import copy, os

class Order:
	body = None

	def __init__(self, order_id, description):
		self.body = {
			"merchantPosId": os.getenv("PAYU_POS_ID"),
			"description": str( description ),
			"extOrderId": str( order_id ),
			"currencyCode": "PLN",
			"totalAmount": 0,
			"continueUrl": os.getenv("PAYU_CONTINUE_URL"),
			"notifyUrl": os.getenv("PAYU_NOTIFY_URL"),
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