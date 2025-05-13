import json, os
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

producer.send(
	topic="send-mail",
	value={
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
	}
)

producer.flush()