import os
from dotenv import load_dotenv

load_dotenv()
TPAY_CLIENT_ID = os.getenv("TPAY_CLIENT_ID")
TPAY_CLIENT_SECRET = os.getenv("TPAY_CLIENT_SECRET")
TPAY_API_URL = os.getenv("TPAY_API_URL")