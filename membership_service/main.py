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
import os, asyncio

pending: dict[str, asyncio.Future] = {}
loop: asyncio.AbstractEventLoop | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    def run_consumer():
        consume_payment_events()

    global loop
    loop = asyncio.get_running_loop()
    thread = threading.Thread(target=run_consumer, daemon=True)
    thread.start()
    yield

app = FastAPI(lifespan=lifespan)

producer = KafkaProducer(
    bootstrap_servers=os.getenv("KAFKA_BROKER"),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

consumer = KafkaConsumer(
    'payment-status',
    bootstrap_servers=os.getenv("KAFKA_BROKER"),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    key_deserializer=lambda k: k.decode('utf-8') if k else None,
    group_id='membership-group'
)

def consume_payment_events():
    for msg in consumer:
        event = msg.value
        key = msg.key

        with SessionLocal() as db:
            if event.get("status") == "created":
                print(f"Płatność utworzona dla karnetu: {event.get('internalId')}, link do płatności: {event.get('redirect')}")
                internal_id = event.get("internalId")
                if not internal_id:
                    continue

                fut = pending.get(internal_id)
                if fut and not fut.done():
                    loop.call_soon_threadsafe(fut.set_result, event)

            elif event.get("status") == "success":
                crud.update_membership_status(db, event.get("internalId"), "paid")
                db.commit()
                print(f"Płatność zakończona pomyślnie dla karnetu: {event.get('internalId')}")
                
            elif event.get("status") == "failed":
                crud.delete_membership_by_email(db, event.get("internalId"))
                db.commit()
                print(f"Płatność nieudana dla karnetu: {event.get('internalId')}")


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
async def buy_membership(
    email: str, 
    type: MembershipType, 
    payment_method: PaymentMethod,
    db: Session = Depends(get_db)
):
    existing = crud.get_membership_by_email(db, email)
    if existing:
        raise HTTPException(status_code=400, detail="Klient już ma karnet.")
    
    membership = crud.create_membership(db, email, type.value, date.today())
    internal_id = str(membership.id)

    try:
        producer.send("create-payment",
            key=payment_method.value.encode("utf-8"),
            value={
                "internalId": internal_id,
                "description": f"Zakup karnetu - {type.value}",
                "customer": {
                    "id": "abcdefg123",
                    "ip": "172.0.0.1",
                    "email": email,
                    "firstName": "Janusz",
                    "lastName": "Kowalski"
                },
                "products": [
                    {
                        "name": f"Karnet - {type.value}",
                        "price": MEMBERSHIP_PRICES[type.value]
                    }
                ]
            }
        )
    except Exception as e:
        crud.delete_membership_by_email(db, email)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Błąd przy tworzeniu płatności: {e}")

    fut = loop.create_future()
    pending[internal_id] = fut

    try:
        result = await asyncio.wait_for(fut, timeout=10)
        return {
            "message": "Karnet kupiony. Przejdź do płatności.",
            "membership": membership,
            "redirect": result.get("redirect")
        }
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=202,
            detail=f"Płatność {internal_id} w toku - sprawdź później.",
        )
    finally:
        pending.pop(internal_id, None)

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