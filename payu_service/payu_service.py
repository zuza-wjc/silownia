import json, uuid, threading, traceback, os

from quixstreams import Application
from observer import Subject, Observer
from jsonschema import validate
from payu_schemas import payment_schema
from payu_requests import make_order
from dotenv import load_dotenv

import payu_database
from payu_notifications import notification_subject, payment_notifications_loop
from order import Order

load_dotenv()

class NotificationObserver(Observer):
	def update(self, subject: Subject, data) -> None:
		print("UPDATE", data)

		payu_database.update_payment(data["orderId"], data["status"])

		dbData = payu_database.get_payment_by_order_id(data["orderId"])
		produce_udpate(
			dbData["internalId"],
			dbData["orderId"],
			dbData["payuId"],
			dbData["status"]
		)

		if data["status"] == "COMPLETED":
			produce_mail_completed(
				dbData["mail"],
				dbData["orderId"],
				dbData["userName"],
				str(dbData["amount"]),
			)

notification_observer = NotificationObserver()
notification_subject.attach(notification_observer)

app = Application(
	broker_address=os.getenv("KAFKA_BROKER"),
	consumer_group="create-payment-payu-group"
)

producer = app.get_producer()

payu_database.initialize_database()

def create_payment(data: dict):
	orderId = str(uuid.uuid4())
	print("PAYMENT", orderId)

	order = Order(orderId, data["description"])

	customer = data["customer"]
	userName = customer["firstName"] + " " + customer["lastName"]

	order.set_customer(
		customer["id"],
		customer["email"],
		customer["firstName"],
		customer["lastName"],
		customer["ip"]
	)

	productName = None
	for product in data["products"]:
		order.add_product(
			product["name"],
			product["price"],
			1
		)

		if productName is None:
			productName = product["name"]
		else:
			productName += ", " + product["name"]

	orderData = make_order(order)

	if not orderData:
		print("Failed to create order!")
		return
	
	payu_database.insert_payment(
		orderId,
		orderData["payuId"],
		customer["id"],
		data["internalId"],
		str(order.body["totalAmount"] / 100),
		customer["email"],
		userName
	)

	produce_udpate(
		data["internalId"],
		orderId,
		orderData["payuId"],
		"CREATED",
		orderData["redirect"]
	)

	produce_mail_order(
		customer["email"],
		orderId,
		userName,
		productName,
		str(order.body["totalAmount"] / 100),
		orderData["redirect"]
	)
	print("DONE")

def produce_udpate(internalId, orderId, payuId, status, redirect = None):
	producer.produce(
		topic="payment-status",
		key="PayU",
		value=json.dumps({
			"internalId": internalId,
			"orderId": orderId,
			"payuId": payuId,
			"status": status,
			"redirect": redirect,
		}).encode("utf-8")
	)

def produce_mail_order(mail, orderId, userName, product, amount, redirect):
	producer.produce(
		topic="send-mail",
		value=json.dumps({
			"to": [mail],
			"subject": "Nowe zamówienie",
			"template": "new_order",
			"template_values": {
				"user_name": userName,
				"order_id": orderId,
				"product": product,
				"price": amount,
				"payment_url": redirect,
			}
		}).encode("utf-8")
	)

def produce_mail_completed(mail, orderId, userName, amount):
	producer.produce(
		topic="send-mail",
		value=json.dumps({
			"to": [mail],
			"subject": "Potwierdzenie zakupu",
			"template": "order_completed",
			"template_values": {
				"user_name": userName,
				"order_id": orderId,
				"price": amount,
			}
		}).encode("utf-8")
	)

# Start everything
kafka_thread = threading.Thread(target=payment_notifications_loop, daemon=True)
kafka_thread.start()

with app.get_consumer() as consumer:
	consumer.subscribe(["create-payment"])

	while True:
		result = consumer.poll(1)
		if result is not None and result.key().decode() == "PayU":
			print("GOT PAYMENT REQUEST")
			jsonObject = json.loads(result.value().decode("utf-8"))
			try:
				validate(jsonObject, payment_schema)
				create_payment(jsonObject)
			except Exception as error:
				print("JSON Schema validation failed", error, traceback.format_exc())