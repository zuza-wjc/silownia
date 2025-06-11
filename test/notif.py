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
			"userName": "Jan Baca",
			"product": "karnet - 3 miesiące",
			"orderId": "1325423hjdfhgr",
			"price": "229.99",
			"redirect": "https://google.com"
		}
	}
)

producer.flush()