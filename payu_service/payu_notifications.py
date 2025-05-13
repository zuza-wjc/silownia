import json, os

from jsonschema import validate
from kafka import KafkaConsumer
from observer import Subject
from payu_schemas import notification_schema

notification_subject = Subject()

def payment_notifications_loop():
	consumer = KafkaConsumer(
		"payu-notification",
		bootstrap_servers=os.getenv("KAFKA_BROKER"),
		auto_offset_reset="latest",
		enable_auto_commit=True,
		value_deserializer=lambda v: json.loads(v.decode("utf-8")),
		key_deserializer=lambda k: k.decode("utf-8") if k else None,
		group_id="payu-notification-group"
	)

	for message in consumer:
		try:
			validate(message.value, notification_schema)
			notification_subject.notify({
				"orderId": message.value["extOrderId"],
				"payuId": message.value["orderId"],
				"status": message.value["status"]
			})
		except Exception as error:
			print("JSON Schema validation failed", error)