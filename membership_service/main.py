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
import os, asyncio
from schemas import PaymentMethod, BuyMembershipResponse, CreatePaymentRequest, MembershipResponse
from dateutil.relativedelta import relativedelta

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

        with SessionLocal() as db:
            if event.get("status") == "created":
                internal_id = event.get("internalId")
                redirect_url = event.get("redirect")
                if not redirect_url:
                    print(f"Brak'redirect' URL: {event}")
                    continue
                    
                print(f"Płatność utworzona dla: {internal_id}, redirect: {redirect_url}")
                updated_mem = crud.update_membership_redirect_url(db, internal_id, redirect_url)
                if not updated_mem:
                        print(f"Nie udało się zaktualizować redirect url dla {internal_id}")
                    
                fut = pending.get(internal_id)
                if fut and not fut.done() and loop:
                    loop.call_soon_threadsafe(fut.set_result, event)
                elif fut and fut.done():
                    print(f"Future for {internal_id} was already done.")
                elif not fut:
                    print(f"No pending future found for {internal_id} (event: 'created'). Might have timed out in API.")

            elif event.get("status") == "success":
                membership = crud.update_membership_status(db, int(event.get("internalId")), "paid")
                db.commit()
                print(f"Płatność zakończona pomyślnie dla karnetu: {event.get('internalId')}")
                if membership:
                    send_membership_status(membership.email, "paid", membership.expiration_date)

                
            elif event.get("status") == "failed":
                crud.delete_membership_by_id(db, int(event.get("internalId")))
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


@app.post("/buy-membership/", response_model=BuyMembershipResponse)
async def buy_membership(
    email: str, 
    type: MembershipType, 
    payment_method: PaymentMethod,
    db: Session = Depends(get_db)
):
    existing_membership = crud.get_membership_by_email(db, email)

    if existing_membership:
        if existing_membership.status in ["paid", "active"]:
            raise HTTPException(status_code=400, detail="Klient już ma aktywny lub opłacony karnet.")
        
        if existing_membership.status == "created":
            if existing_membership.redirect_url:
                print(f"Istnieje karnet dla {email} z redirect URL")
                return BuyMembershipResponse(
                    message="Płatność dla tego karnetu została już utworzona. Przekierowuję do płatności.",
                    membership=MembershipResponse(email=email, status="created"),
                    redirect=existing_membership.redirect_url
                )
            else:
                print(f"Istnieje karnet dla {email} bez redirect URL. Czekaj na link.")
                raise HTTPException(
                    status_code=202,
                    detail="Oczekujemy na link do płatności dla Twojego karnetu. Spróbuj ponownie za chwilę."
                )
        print(f"Istnieje karnet dla {email} ze statusem: {existing_membership.status}.")
        raise HTTPException(
            status_code=409, # Conflict
            detail=f"Istnieje już karnet dla tego emaila ze statusem '{existing_membership.status}', który uniemożliwia nową transakcję. Skontaktuj się z obsługą."
        )
    
    print(f"Tworze nowy karnet dla {email}, typ: {type.value}")
    new_membership = crud.create_membership(db, email, type.value, date.today())
    internal_id = str(new_membership.id)
    send_membership_status(email, "created", None)

    try:
        payment_request = CreatePaymentRequest(
            internalId=internal_id,
            description=f"Zakup karnetu - {type.value}",
            customer={
                "id": "abcdefg123",
                "ip": "172.0.0.1",
                "email": email,
                "firstName": "Janusz",
                "lastName": "Kowalski"
            },
            products=[
                {
                    "name": f"Karnet - {type.value}",
                    "price": MEMBERSHIP_PRICES[type.value]
                }
            ]
        )
        producer.send("create-payment",
            key=payment_method.value.encode("utf-8"),
            value=payment_request.dict()
        )
    except Exception as e:
        crud.delete_membership_by_email(db, email)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Błąd przy tworzeniu płatności: {e}")

    fut = loop.create_future()
    pending[internal_id] = fut

    try:
        payment_event_data = await asyncio.wait_for(fut, timeout=10.0)
        
        redirect_url_from_event = payment_event_data.get("redirect")
        if not redirect_url_from_event:
            print(f"Płatność otrzymana dla {internal_id} brak redirect URL. Event: {payment_event_data}")
            crud.delete_membership_by_id(db, new_membership.id)
            raise HTTPException(status_code=500, detail="Nie otrzymano linku do płatności od systemu płatności po utworzeniu.")

        print(f"Redirect URL {redirect_url_from_event} otrzymany z kafki {internal_id}.")
        return BuyMembershipResponse(
            message="Karnet utworzony. Przejdź do płatności.",
            membership=MembershipResponse(email=email, status="created"),
            redirect=redirect_url_from_event
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=202,
            detail=f"Płatność dla karnetu {internal_id} jest przetwarzana. Link do płatności zostanie udostępniony wkrótce. Spróbuj ponownie za chwilę."
        )
    finally:
        pending.pop(internal_id, None)

@app.post("/verify-membership/")
def verify_membership(email: str, db: Session = Depends(get_db)):
    membership = crud.get_membership_by_email(db, email)
    if not membership:
        raise HTTPException(status_code=404, detail="Nie znaleziono karnetu dla podanego emaila.")
    
    if membership.status == "paid":
        membership.status = "active"

        if isinstance(membership.purchase_date, date) and membership.type in ["1m", "3m", "12m"]:
            if membership.type == "1m":
                membership.expiration_date = membership.purchase_date + relativedelta(months=1)
            elif membership.type == "3m":
                membership.expiration_date = membership.purchase_date + relativedelta(months=3)
            elif membership.type == "12m":
                membership.expiration_date = membership.purchase_date + relativedelta(months=12)
            else:
                db.rollback()
                raise HTTPException(status_code=500, detail="Nie można obliczyć daty ważności: nieprawidłowy typ karnetu.")
        else:
            db.rollback()
            raise HTTPException(status_code=500, detail="Nie można obliczyć daty ważności: brak daty zakupu lub nieprawidłowy typ.")
        
        db.commit()
        db.refresh(membership)
        send_membership_status(email, "active", membership.expiration_date)
        return {"message": f"Status zmieniony na 'active' dla {email}"}
    
    return {"message": f"Karnet już jest aktywny dla {email}"}


@app.delete("/cancel-membership")
def cancel_membership(email: str = Query(...), db: Session = Depends(get_db)):
    deleted = crud.delete_membership_by_email(db, email)
    send_membership_status(email, "cancelled", None)
    if not deleted:
        raise HTTPException(status_code=404, detail="Nie znaleziono karnetu do usunięcia.")
    return {"message": f"Karnet dla {email} został anulowany."}


def send_membership_status(email: str, status: str, expiration_date: date | None):
    producer.send("membership-status", value={
        "email": email,
        "status": status,
        "expiration_date": expiration_date.isoformat() if expiration_date else None
    })
