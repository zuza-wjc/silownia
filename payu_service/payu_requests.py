import requests, time, os

from order import Order
from jsonschema import validate
from payu_schemas import response_schema

access_token = None
token_expires = None

def authorize_token():
	global access_token, token_expires

	res = requests.post("https://secure.snd.payu.com/pl/standard/user/oauth/authorize", headers={
		"Content-Type": "application/x-www-form-urlencoded"
	}, data={
		"grant_type": "client_credentials",
		"client_id": os.getenv("PAYU_CLIENT_ID"),
		"client_secret": os.getenv("PAYU_SECRET"),
	})

	data = res.json()

	access_token = data["access_token"]
	token_expires = time.time() + int(data["expires_in"])

def get_token():
	global access_token, token_expires

	if not access_token or token_expires >= time.time():
		authorize_token()

	return access_token

def process_response(status_code: str, status: dict, ):
	if status_code != "SUCCESS":
		print("Error occured while creating order", status)
		return
	
	try:
		validate(status, response_schema)
	except Exception as error:
		print("Response is invalid", error)
		return

	return {
		"orderId": status["extOrderId"],
		"payuId": status["orderId"],
		"redirect": status["redirectUri"]
	}
		

def make_order(order: Order):
	res = requests.post("https://secure.snd.payu.com/api/v2_1/orders", headers = {
		"Content-Type": "application/json",
		"Authorization": "Bearer " + get_token()
	}, json = order.get_body(), allow_redirects=False)

	data = res.json()
	status = None
	status_code = None

	if res.status_code == 200:
		status = data["status"]
		status_code = status["statusCode"]
	elif res.status_code == 302:
		status = data
		status_code = data["status"]["statusCode"]

	return process_response(status_code, status)
	