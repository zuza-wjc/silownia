import json
from quixstreams import Application

app = Application(
	broker_address="localhost:9092"
)

with app.get_producer() as producer:
	producer.produce(
		topic="create-payment",
		key="PayU",
		value=json.dumps({
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
		}).encode("utf-8")
	)