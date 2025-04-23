import requests, json, time, copy
from quixstreams import Application


pos_id = "490010"
client_id = "490010"
client_secret = "50f2ba5aa3c4caafe7c7244831104a54"

access_token = None
token_expires = None

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

def authorize_token():
	global access_token, token_expires

	res = requests.post("https://secure.snd.payu.com/pl/standard/user/oauth/authorize", headers={
		"Content-Type": "application/x-www-form-urlencoded"
	}, data={
		"grant_type": "client_credentials",
		"client_id": client_id,
		"client_secret": client_secret,
	})

	data = res.json()

	access_token = data["access_token"]
	token_expires = time.time() + int(data["expires_in"])
	print("Got new toke: " + access_token)
	print("Expires: " + str(token_expires))

def get_token():
	global access_token, token_expires

	if not access_token or token_expires >= time.time():
		authorize_token()

	return access_token

def make_order(order: Order = None, body = None):
	res = requests.post("https://secure.snd.payu.com/api/v2_1/orders", headers = {
		"Content-Type": "application/json",
		"Authorization": "Bearer " + get_token()
	}, json = body or order.get_body(), allow_redirects=False)

	print(res.status_code, res.headers)
	data = res.json()
	status = None
	statusCode = None

	if res.status_code == 200:
		status = data["status"]
		statusCode = status["statusCode"]
	elif res.status_code == 302:
		status = data
		statusCode = data["status"]["statusCode"]

	if statusCode != "SUCCESS":
		print(status)
		return {
			"status": "err",
			"details": status,
		}
	
	print("REDIRECT: " + status["redirectUri"])
	return {
		"status": "ok",
		"redirect": status["redirectUri"],
		"orderId": status["extOrderId"],
		"payuId": status["orderId"],
	}

#order = Order("ABC125", "Opłata karnetu")
#order.set_customer("420", "janusz@kowalski.example", "Janusz", "Kowalski", "127.0.0.1")
#order.add_product("Karnet (1 miesiąc)", 59.99, 1)
#make_order(order)

app = Application(
	broker_address="localhost:9092"
)

producer = app.get_producer()

with app.get_consumer() as consumer:
	consumer.subscribe(["create-payment"])

	while True:
		result = consumer.poll(1)

		if result is not None:
			print("NEW PAYMENT")
			body = json.loads(result.value().decode("utf-8"))
			r = make_order(body=body)
			if(r["status"] == "ok"):
				producer.produce(
					topic="payment-status",
					key=r["orderId"].encode("utf-8"),
					value=json.dumps({
						"status": "CREATED",
						"redirect": r["redirect"],
						"payuId": r["payuId"],
					}).encode("utf-8")
				)

				mail = body["buyer"]["email"]
				product = body["products"][0]["name"]

				producer.produce(
					topic="send-mail",
					value=json.dumps({
						"to": mail,
						"subject": "Nowe zamówienie - " + product,
						"message": f'Zarejestrowano nowe zamówienie.\nW kolejnym mailu otrzymasz potwierdzenie płatności.\nAby opłacić zamówienie wejdź w <a href="{r["redirect"]}" target="_blank">link</a>'
					}).encode("utf-8")
	)