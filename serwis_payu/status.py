from quixstreams import Application

app = Application(
	broker_address="localhost:9092"
)

with app.get_consumer() as consumer:
	consumer.subscribe(["payment-status"])

	while True:
		result = consumer.poll(1)

		if result is not None:
			print("STATUS UPDATE", result.key(), result.value().decode("utf-8"))