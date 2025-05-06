from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from database import SessionLocal
import crud
from models import MembershipType
from kafka import KafkaProducer, KafkaConsumer
import json
import threading
from contextlib import asynccontextmanager
from enum import Enum

@asynccontextmanager
async def lifespan(app: FastAPI):
    def run_consumer():
        consume_payment_events()

    thread = threading.Thread(target=run_consumer, daemon=True)
    thread.start()
    yield

app = FastAPI(lifespan=lifespan)

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

MEMBERSHIP_PRICES = {
    "1m": 1.0,
    "3m": 3.0,
    "12m": 12.0
}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "dziala"}


class PaymentMethod(str, Enum):
    tpay = "TPay"
    payu = "PayU"

@app.post("/buy-membership/")
def buy_membership(
    email: str, 
    type: MembershipType, 
    payment_method: PaymentMethod,
    db: Session = Depends(get_db)
):
    existing = crud.get_membership_by_email(db, email)
    if existing:
        raise HTTPException(status_code=400, detail="Klient już ma karnet.")
    
    membership = crud.create_membership(db, email, type.value, date.today())
    
    try:
        event_type = f"MembershipCreated{payment_method.value}"

        producer.send("membership-events", {
            "event_type": event_type,
            "email": email,
            "type": type.value,
            "price": MEMBERSHIP_PRICES[type.value],
            "description": "Zakup karnetu",
            "payment_method": payment_method.value
        })

        # producer.send("membership-events",
        #     key="??",
        #     value={
        #         "event_type": event_type,
        #         "email": email,
        #         "type": type.value,
        #         "price": MEMBERSHIP_PRICES[type.value],
        #         "description": "Zakup karnetu",
        #         "payment_method": payment_method.value
        # })
    except Exception as e:
        crud.delete_membership_by_email(db, email)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Błąd przy tworzeniu płatności: {e}")

    return {
        "message": "Karnet kupiony. Przejdź do płatności.",
        "membership": membership
    }


@app.get("/get-membership/")
def get_membership(email: str, db: Session = Depends(get_db)):
    membership = crud.get_membership_by_email(db, email)
    if not membership:
        raise HTTPException(status_code=404, detail="Nie znaleziono karnetu dla podanego emaila.")
    
    return {
        "email": membership.email,
        "status": membership.status,
    }


@app.post("/verify-membership/")
def verify_membership(email: str, db: Session = Depends(get_db)):
    membership = crud.get_membership_by_email(db, email)
    if not membership:
        raise HTTPException(status_code=404, detail="Nie znaleziono karnetu dla podanego emaila.")
    
    if membership.status != "active":
        membership.status = "active"
        db.commit()
        db.refresh(membership)
        return {"message": f"Status zmieniony na 'active' dla {email}"}
    
    return {"message": f"Karnet już jest aktywny dla {email}"}


@app.delete("/cancel-membership")
def cancel_membership(email: str = Query(...), db: Session = Depends(get_db)):
    deleted = crud.delete_membership_by_email(db, email)
    if not deleted:
        raise HTTPException(status_code=404, detail="Nie znaleziono karnetu do usunięcia.")
    return {"message": f"Karnet dla {email} został anulowany."}


consumer = KafkaConsumer(
    'payment-events',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    group_id='membership-group'
)

def consume_payment_events():
    for msg in consumer:
        event = msg.value
        with SessionLocal() as db:
            if event.get("event_type") == "PaymentFailed":
                crud.delete_membership_by_email(db, event.get("email"))
                db.commit()
            elif event.get("event_type") == "PaymentSuccessful":
                crud.update_membership_status(db, event.get("email"), "paid")
                db.commit()