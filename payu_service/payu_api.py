import json, os
from flask import Flask, Response, request
from kafka import KafkaProducer


def run_api():
	producer = KafkaProducer(
		bootstrap_servers=os.getenv("KAFKA_BROKER"),
		value_serializer=lambda v: json.dumps(v).encode("utf-8"),
		key_serializer=lambda k: k.encode("utf-8") if k else None
	)

	app = Flask(__name__)

	@app.route("/notification", methods=['POST'])
	def payment_callback():
		order = json.loads(request.data.decode("utf-8"))["order"]

		print("[API] Got PayU notification:", order)
		producer.send(
			topic="payu-notification",
			value=order
		)

		return Response("", status=200)

	app.run('0.0.0.0', port=8007)