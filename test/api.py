import json, os
from flask import Flask, Response, request
from quixstreams import Application

app = Flask(__name__)

kafka_app = Application(
	broker_address="localhost:9092",
)

@app.route("/payu-payment-notification", methods=['POST'])
def payment_callback():
	order = json.loads(request.data.decode("utf-8"))["order"]

	with kafka_app.get_producer() as producer:
		producer.produce(
			topic="payu-notification",
			value=json.dumps(order).encode("utf-8")
		)

	return Response("", status=200)

app.run('0.0.0.0', port=80)