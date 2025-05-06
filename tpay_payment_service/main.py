import json
from fastapi import FastAPI, HTTPException, Depends, Request
from tpay_client import TPayClient
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Transaction, CreatePaymentRequest
from kafka import KafkaConsumer, KafkaProducer
from contextlib import asynccontextmanager
import threading

WEBHOOK_URL = "https://65c1-2a00-f41-70ef-71a6-9dbe-a9ae-bcd9-3c64.ngrok-free.app/webhook"

@asynccontextmanager
async def lifespan(app: FastAPI):
    def run_consumer():
        with SessionLocal() as db:
            consume_membership_events(db)
    thread = threading.Thread(target=run_consumer, daemon=True)
    thread.start()
    yield

app = FastAPI(lifespan=lifespan)
tpay_client = TPayClient()

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

consumer = KafkaConsumer(
    'create-payment',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    key_deserializer=lambda k: k.decode('utf-8') if k else None,
    group_id='payment-group'
)

def consume_membership_events(db: Session):
    for msg in consumer:
        event = msg.value
        key = msg.key

        if key == "TPay":
            try:
                internal_id = event["internalId"]
                email = event["customer"]["email"]
                price = event["products"][0]["price"]
                description = event["description"]

                payment_url, transaction_id, transaction_title = tpay_client.create_transaction(
                    amount=price,
                    description=description,
                    email=email,
                    webhook_url=WEBHOOK_URL
                )

                transaction = Transaction(
                    internal_id=internal_id,
                    email=email,
                    amount=price,
                    description=description,
                    tpay_transaction_id=transaction_id,
                    tpay_title=transaction_title
                )
                db.add(transaction)
                db.commit()
                db.refresh(transaction)

                # Wysłanie statusu 'created' do Kafki
                producer.send("payment-status", key="TPay".encode("utf-8"), value={
                    "internalId": internal_id,      # wziete z serwisu karnetow
                    "orderId": str(transaction.id), # wziete z bazy transactions.db
                    "paymentId": transaction_id,    # wziete z TPay API
                    "status": "created",
                    "redirect": payment_url
                })

                print(f"Payment created for {email}, payment URL: {payment_url}")

            except Exception as e:
                print(f"Błąd: {e}")

                # Wysłanie statusu 'failed' do Kafki
                producer.send("payment-status", key="TPay".encode("utf-8"), value={
                    "internalId": event.get("internalId", "unknown"),
                    "orderId": None,
                    "paymentId": None,
                    "status": "failed",
                    "redirect": None
                })


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "dziala"}


@app.post("/make-payment/")
async def make_payment(
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
    
    if status == "TRUE":
        transaction.status = "paid"
        db.commit()

        # Wysłanie statusu 'success' do Kafki
        producer.send("payment-status", key="TPay".encode("utf-8"), value={
            "internalId": transaction.internal_id,
            "orderId": str(transaction.id),
            "paymentId": transaction.tpay_transaction_id,
            "status": "success",
            "redirect": None
        })
    
    elif status == "FALSE":
        transaction.status = "failed"
        db.commit()

        # Wysłanie statusu 'failed' do Kafki
        producer.send("payment-status", key="TPay".encode("utf-8"), value={
            "internalId": transaction.internal_id,
            "orderId": str(transaction.id),
            "paymentId": transaction.tpay_transaction_id,
            "status": "failed",
            "redirect": None
        })

    return {"message": "Status zaktualizowany"}