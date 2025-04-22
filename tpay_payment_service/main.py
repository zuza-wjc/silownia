from fastapi import FastAPI, HTTPException, Depends, Request
from tpay_client import TPayClient
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Transaction, CreatePaymentRequest
import requests

app = FastAPI()
tpay_client = TPayClient()

WEBHOOK_URL = "https://73c7-37-248-220-226.ngrok-free.app/webhook"
MEMBERSHIP_WEBHOOK_URL = "https://53ee-37-248-220-226.ngrok-free.app/update_membership"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "dziala"}


@app.post("/create_payment/")
async def create_payment(
    payment_data: CreatePaymentRequest,
    db: Session = Depends(get_db)
):
    try:
        payment_url, transaction_id, transaction_title = tpay_client.create_transaction(
            payment_data.amount,
            payment_data.description,
            payment_data.email,
            webhook_url=WEBHOOK_URL
        )


        db.add(Transaction(
            email=payment_data.email,
            amount=payment_data.amount,
            description=payment_data.description,
            tpay_transaction_id=transaction_id,
            tpay_title=transaction_title
        ))
        db.commit()

        return {"payment_url": payment_url, "transaction_id": transaction_id, "transaction_title": transaction_title}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Błąd przy tworzeniu transakcji: {e}")


@app.post("/webhook")
async def tpay_webhook(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    title = form.get("tr_id")
    status = form.get("tr_status")

    if not title:
        return {"error": "Brak tr_id"}

    transaction = db.query(Transaction).filter(Transaction.tpay_title == title).first()
    if not transaction:
        return {"error": "Transakcja nie znaleziona"}
    
    if status != "TRUE":
        return {"message": "Status nie jest TRUE – brak zmian."}

    transaction.status = "paid"
    db.commit()

    try:
        response = requests.post(
            MEMBERSHIP_WEBHOOK_URL,
            json={"email": transaction.email, "status": transaction.status}
        )
        response.raise_for_status()
        print(f"Wysłano update statusu do membership: {response.status_code}")
    except Exception as e:
        print(f"Błąd przy wysyłaniu do membership service: {e}")

    return {"message": f"Status zaktualizowany"}