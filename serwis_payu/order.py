import copy, json
from quixstreams import Application

pos_id = "490010"

class Order:
	body = None

	def __init__(self, order_id, description):
		self.body = {
			"merchantPosId": pos_id,
			"description": str( description ),
			"extOrderId": str( order_id ),
			"currencyCode": "PLN",
			"totalAmount": 0,
			"continueUrl": "http://35.211.136.14/continue",
			"notifyUrl": "http://35.211.136.14/notification",
			"products": []
		}

	def set_customer(self, id, mail, first_name, last_name, ip):
		self.body["customerIp"] = str(ip)
		self.body["buyer"] = {
			"extCustomerId": str(id),
			"email": str(mail),
			"firstName": str(first_name),
			"lastName": str(last_name),
		}

	def add_product(self, name, price, quantity):
		self.body["products"].append({
			"name": str(name),
			"unitPrice": str(int(price * 100)),
			"quantity": str(quantity),
		})

		self.body["totalAmount"] += price * 100

	def get_body(self):
		body = copy.deepcopy(self.body)
		body["totalAmount"] = str(int(body["totalAmount"]))
		return body

app = Application(
	broker_address="localhost:9092"
)

mail = input("Mail: ")
product = input("Produkt: ")
order = Order(input("orderId: "), "Opłata karnetu")
order.set_customer("420", mail, input("Imie: "), input("Nazwisko: "), "127.0.0.1")
order.add_product(product, float(input("Kwota: ")), 1)

with app.get_producer() as producer:
	producer.produce(
		topic="create-payment",
		value=json.dumps(order.get_body()).encode("utf-8")
	)