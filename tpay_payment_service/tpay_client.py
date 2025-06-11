import os
import requests
from requests.auth import HTTPBasicAuth

TPAY_CLIENT_ID = os.getenv("TPAY_CLIENT_ID")
TPAY_CLIENT_SECRET = os.getenv("TPAY_CLIENT_SECRET")
TPAY_API_URL = os.getenv("TPAY_API_URL")

class TPayClient:
    def __init__(self):
        self.base_url = TPAY_API_URL
        self.auth = HTTPBasicAuth(TPAY_CLIENT_ID, TPAY_CLIENT_SECRET)
        self.token = self._get_access_token()

    def _get_access_token(self):
        url = f"{self.base_url}/oauth/auth"
        headers = {"Accept": "application/json"}
        response = requests.post(url, auth=self.auth, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data["access_token"]
    
    def create_transaction(self, amount, description, email, webhook_url):
        url = f"{self.base_url}/transactions"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "amount": amount,
            "currency": "PLN",
            "description": description,
            "payer": {
                "email": email
            },
            "notificationUrl": webhook_url
        }

        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()

        if response_data.get("result") != "success":
            raise Exception(f"Błąd tworzenia płatności: {response_data}")

        return (
            response_data["transactionPaymentUrl"],
            response_data["transactionId"],
            response_data["title"]
        )