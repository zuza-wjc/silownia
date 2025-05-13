import json
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
	key_serializer=lambda k: k.encode("utf-8") if k else None
)

producer.send(
	topic="create-payment",
	key="PayU",
	value={
		"internalId": "1764362",
		"description": "Zakup karnetu - 3 miesiące",
		"customer": {
			"id": "abcde5fg123",
			"ip": "172.0.0.1",
			"email": "janusz.kowalski@mail.pl",
			"firstName": "Janusz",
			"lastName": "Kowalski"
		},
		"products": [
			{
				"name": "Karnet - 3 miesiące",
				"price": 139.99,
			}
		]
	}
)

producer.flush()