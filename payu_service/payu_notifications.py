import json, os

from quixstreams import Application
from jsonschema import validate

from observer import Subject
from payu_schemas import notification_schema

notification_subject = Subject()

def payment_notifications_loop():
	app = Application(
		broker_address=os.getenv("KAFKA_BROKER"),
		consumer_group="payu-notification-group"
	)

	with app.get_consumer() as consumer:
		consumer.subscribe(["payu-notification"])

		while True:
			result = consumer.poll(1)
			if result is not None:
				jsonObject = json.loads(result.value().decode("utf-8"))
				try:
					validate(jsonObject, notification_schema)
					notification_subject.notify({
						"orderId": jsonObject["extOrderId"],
						"payuId": jsonObject["orderId"],
						"status": jsonObject["status"]
					})
				except Exception as error:
					print("JSON Schema validation failed", error)