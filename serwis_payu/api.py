import json
from flask import Flask, Response, request
from quixstreams import Application

app = Flask(__name__)
# app.debug = True

kafka = Application(
	broker_address="localhost:9092"
)

@app.route("/notification", methods=['POST'])
def payment_callback():
	#print(dict(request.headers))
	#print(request.data)
	order = json.loads(request.data.decode("utf-8"))["order"]

	producer = kafka.get_producer()
	producer.produce(
		topic="payment-status",
		key=order["extOrderId"].encode("utf-8"),
		value=json.dumps({
			"status": order["status"],
		}).encode("utf-8"),
	)

	if order["status"] == "COMPLETED":
		producer.produce(
			topic="send-mail",
			value=json.dumps({
				"to": order["buyer"]["email"],
				"subject": "Potwierdzenie otrzymania płatności",
				"message": f"Otrzymaliśmy potwierdzenie płatności za produkt: {order['products'][0]['name']}"
			}).encode("utf-8"),
		)

	producer.flush()

	return Response("", status=200)

@app.route("/continue")
def pos_payment():
	print(dict(request.headers))
	print(request.data)
	return Response("Dziekuje za zakup. Twoja platnosc jest teraz przetwazana.")

app.run('0.0.0.0', port=80)
