import json, uuid, threading, traceback, os

from observer import Subject, Observer
from jsonschema import validate
from payu_schemas import payment_schema
from payu_requests import make_order
from dotenv import load_dotenv
from kafka import KafkaConsumer, KafkaProducer

import payu_database
from payu_notifications import notification_subject, payment_notifications_loop
from payu_api import run_api
from order import Order

load_dotenv()

class NotificationObserver(Observer):
	def update(self, subject: Subject, data) -> None:
		print("Payment status update", data)

		status = translate_status(data["status"])
		payu_database.update_payment(data["orderId"], status)

		dbData = payu_database.get_payment_by_order_id(data["orderId"])

		args = {}

		if status == "success":
			args["mail"] = dbData["mail"]
			args["userName"] = dbData["userName"]
			args["price"] = dbData["amount"]

		produce_udpate(
			dbData["internalId"],
			dbData["orderId"],
			dbData["payuId"],
			status,
			**args
		)

notification_observer = NotificationObserver()
notification_subject.attach(notification_observer)

payu_database.initialize_database()

producer = KafkaProducer(
    bootstrap_servers=os.getenv("KAFKA_BROKER"),
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
	key_serializer=lambda k: k.encode("utf-8") if k else None
)

def create_payment(data: dict):
	orderId = str(uuid.uuid4())
	order = Order(orderId, data["description"])
	customer = data["customer"]
	userName = customer["firstName"] + " " + customer["lastName"]

	print("New payment", data["internalId"], orderId)

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
		"created",
		redirect=orderData["redirect"],
		mail=customer["email"],
		userName=userName,
		product=productName,
		price=str(order.body["totalAmount"] / 100)
	)

	print("Payment created")

def translate_status(status: str) -> str:
	if status == "PENDING":
		return "pending"
	elif status == "WAITING_FOR_CONFIRMATION":
		return "waiting"
	elif status == "COMPLETED":
		return "success"
	elif status == "CANCELED":
		return "failed"

def produce_udpate(internalId, orderId, payuId, status, **kwargs):
	print("[KAFKA] Producing update message")
	producer.send(
		topic="payment-status",
		key="PayU",
		value={
			"internalId": internalId,
			"orderId": orderId,
			"paymentId": payuId,
			"status": status,
			**kwargs
		}
	)

# Start everything
kafka_thread = threading.Thread(target=payment_notifications_loop, daemon=True)
kafka_thread.start()

api_thread = threading.Thread(target=run_api, daemon=True)
api_thread.start()

consumer = KafkaConsumer(
    "create-payment",
    bootstrap_servers=os.getenv("KAFKA_BROKER"),
    auto_offset_reset="latest",
    enable_auto_commit=True,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
	key_deserializer=lambda k: k.decode("utf-8") if k else None,
    group_id="create-payment-payu-group"
)

for message in consumer:
	if message.key == "PayU":
		print("[KAFKA] Got new payment request")
		try:
			validate(message.value, payment_schema)
			create_payment(message.value)
		except Exception as error:
			print("Error", error, traceback.format_exc())