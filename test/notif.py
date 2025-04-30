import json, os
from quixstreams import Application

kafka_app = Application(
	broker_address="localhost:9092",
)

with kafka_app.get_producer() as producer:
	producer.produce(
		topic="send-mail",
		value=json.dumps({
			"to": ["jan.baca@example.pl"],
			"subject": "Testowe powiadomienie",
			"template": "new_order",
			"template_values": {
				"user_name": "Jan Baca",
				"product": "karnet - 3 miesiące",
				"order_id": "1325423hjdfhgr",
				"price": "229.99",
				"payment_url": "https://google.com"
			}
		}).encode("utf-8")
	)

