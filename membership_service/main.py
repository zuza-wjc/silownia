from fastapi import FastAPI, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta
from database import SessionLocal
import crud
from models import MembershipType
from kafka import KafkaProducer, KafkaConsumer
import json
import threading
from contextlib import asynccontextmanager
import os, asyncio
from schemas import PaymentMethod, BuyMembershipResponse, MembershipDateResponse, CreatePaymentRequest, MembershipResponse
from dateutil.relativedelta import relativedelta
import redis
import uuid

pending: dict[str, asyncio.Future] = {}
loop: asyncio.AbstractEventLoop | None = None

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

EXTENSION_INTENT_KEY_PREFIX = "extension_intent:"
EXTENSION_INTENT_TTL_SECONDS = 900

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
        payment_internal_id = event.get("internalId")

        with SessionLocal() as db:
            if event.get("status") == "created":
                redirect_url = event.get("redirect")
                if not redirect_url:
                    print(f"Brak'redirect' URL: {event}")
                    continue
                    
                print(f"Płatność utworzona dla: {payment_internal_id}, redirect: {redirect_url}")

                is_extension_payment = redis_client.exists(f"{EXTENSION_INTENT_KEY_PREFIX}{payment_internal_id}")
                if not is_extension_payment:
                    updated_mem = crud.update_membership_redirect_url(db, payment_internal_id, redirect_url)
                    if not updated_mem:
                        print(f"Nie udało się zaktualizować redirect url dla {payment_internal_id}")
                else:
                    print(f"Otrzymano redirect URL dla przedłużenia płatności: {payment_internal_id}")
                    
                fut = pending.get(payment_internal_id)
                if fut and not fut.done() and loop:
                    loop.call_soon_threadsafe(fut.set_result, event)
                elif fut and fut.done():
                    print(f"Future for {payment_internal_id} was already done.")
                elif not fut:
                    print(f"No pending future found for {payment_internal_id} (event: 'created'). Might have timed out in API.")

            elif event.get("status") == "success":
                extension_intent_json = redis_client.get(f"{EXTENSION_INTENT_KEY_PREFIX}{payment_internal_id}")
                if extension_intent_json:
                    redis_client.delete(f"{EXTENSION_INTENT_KEY_PREFIX}{payment_internal_id}")
                    extension_data = json.loads(extension_intent_json)
                    original_membership_id = extension_data['original_membership_id']
                    extension_type = extension_data['extension_type']
                    email = extension_data['email']

                    membership = crud.get_membership_by_id(db, original_membership_id)
                    if membership and membership.status == "active" and membership.expiration_date:
                        current_expiration_date = membership.expiration_date
                        if extension_type == "1m":
                            membership.expiration_date = current_expiration_date + relativedelta(months=1)
                        elif extension_type == "3m":
                            membership.expiration_date = current_expiration_date + relativedelta(months=3)
                        elif extension_type == "12m":
                            membership.expiration_date = current_expiration_date + relativedelta(months=12)
                        
                        db.commit()
                        db.refresh(membership)
                        print(f"Karnet dla {email} (ID: {original_membership_id}) został pomyślnie przedłużony. Nowa data ważności: {membership.expiration_date}")
                        send_membership_status(email, "extended", membership.expiration_date)
                    else:
                        print(f"Nie można przedłużyć karnetu. ID: {original_membership_id}, Status: {membership.status if membership else 'Nie znaleziono'}")
                else:
                    membership = crud.update_membership_status(db, int(payment_internal_id), "paid")
                    db.commit()
                    print(f"Płatność zakończona pomyślnie dla nowego karnetu: {payment_internal_id}")
                    if membership:
                        send_membership_status(membership.email, "paid", membership.expiration_date)

            elif event.get("status") == "failed":
                is_extension_payment = redis_client.exists(f"{EXTENSION_INTENT_KEY_PREFIX}{payment_internal_id}")
                if is_extension_payment:
                    redis_client.delete(f"{EXTENSION_INTENT_KEY_PREFIX}{payment_internal_id}")
                    extension_data = json.loads(extension_intent_json) if (extension_intent_json := redis_client.get(f"{EXTENSION_INTENT_KEY_PREFIX}{payment_internal_id}")) else {}
                    email = extension_data.get('email', 'N/A')
                    print(f"Płatność za przedłużenie nieudana dla {email} (ID płatności: {payment_internal_id}). Karnet nie został zmieniony.")
                else:
                    crud.delete_membership_by_id(db, int(payment_internal_id))
                    db.commit()
                    print(f"Płatność nieudana dla nowego karnetu: {payment_internal_id}. Karnet usunięty.")



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
            status_code=409,
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

    elif membership.status == "created":
        return {"message": f"Karnet nie opłacony dla {email}"}
    elif membership.status == "active":
         return {"message": f"Karnet już jest aktywny dla {email}"}
    
    return {"message": f"Status karnetu dla {email}: {membership.status}"}



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



@app.post("/extend-membership/", response_model=BuyMembershipResponse)
async def extend_membership(
    email: str,
    type: MembershipType,
    payment_method: PaymentMethod,
    db: Session = Depends(get_db)
):
    existing_membership = crud.get_membership_by_email(db, email)

    if not existing_membership:
        raise HTTPException(status_code=404, detail="Nie znaleziono aktywnego karnetu dla podanego emaila.")

    if existing_membership.status != "active":
        raise HTTPException(status_code=400, detail=f"Karnet dla {email} nie jest aktywny. Aktualny status: {existing_membership.status}.")

    if not existing_membership.expiration_date:
         raise HTTPException(status_code=400, detail=f"Karnet dla {email} nie ma daty ważności.")

    if (existing_membership.expiration_date - date.today()) >= timedelta(weeks=2):
        raise HTTPException(status_code=400, detail="Karnet można przedłużyć dopiero, gdy pozostało mniej niż 2 tygodnie do jego wygaśnięcia.")

    internal_id_for_payment = uuid.uuid4().hex
    
    extension_details = {
        "original_membership_id": existing_membership.id,
        "extension_type": type.value,
        "email": email 
    }
    redis_client.set(
        f"{EXTENSION_INTENT_KEY_PREFIX}{internal_id_for_payment}",
        json.dumps(extension_details),
        ex=EXTENSION_INTENT_TTL_SECONDS
    )
    
    try:
        payment_request = CreatePaymentRequest(
            internalId=internal_id_for_payment,
            description=f"Przedłużenie karnetu - {type.value}",
            customer={
                "id": "abcdefg123",
                "ip": "172.0.0.1",
                "email": email,
                "firstName": "Janusz",
                "lastName": "Kowalski"
            },
            products=[
                {
                    "name": f"Przedłużenie karnetu - {type.value}",
                    "price": MEMBERSHIP_PRICES[type.value]
                }
            ]
        )
        producer.send("create-payment",
            key=payment_method.value.encode("utf-8"),
            value=payment_request.dict()
        )
    except Exception as e:
        redis_client.delete(f"{EXTENSION_INTENT_KEY_PREFIX}{internal_id_for_payment}")
        raise HTTPException(status_code=500, detail=f"Błąd przy inicjowaniu płatności za przedłużenie: {e}")

    fut = loop.create_future()
    pending[internal_id_for_payment] = fut

    try:
        payment_event_data = await asyncio.wait_for(fut, timeout=10.0)
        
        redirect_url_from_event = payment_event_data.get("redirect")
        if not redirect_url_from_event:
            print(f"Otrzymano zdarzenie utworzenia płatności dla przedłużenia {internal_id_for_payment}, ale brak redirect URL. Event: {payment_event_data}")
            raise HTTPException(status_code=500, detail="Nie otrzymano linku do płatności od systemu płatności po utworzeniu żądania przedłużenia.")

        print(f"Redirect URL {redirect_url_from_event} otrzymany z Kafki dla przedłużenia {internal_id_for_payment}.")
        return BuyMembershipResponse(
            message="Proces przedłużania karnetu rozpoczęty. Przejdź do płatności.",
            membership=MembershipResponse(email=email, status=existing_membership.status),
            redirect=redirect_url_from_event
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=202,
            detail=f"Płatność za przedłużenie karnetu (ID: {internal_id_for_payment}) jest przetwarzana. Link do płatności zostanie udostępniony wkrótce. Spróbuj ponownie sprawdzić status lub odświeżyć stronę."
        )
    finally:
        pending.pop(internal_id_for_payment, None)




@app.get("/membership/{email}", response_model=MembershipDateResponse)
def get_membership_details(email: str = Path(...), db: Session = Depends(get_db)):
    print(f"Zapytanie o karnet dla email: {email}")
    membership = crud.get_membership_by_email(db, email)
    if not membership:
        raise HTTPException(status_code=404, detail=f"Nie znaleziono karnetu dla emaila: {email}")
    
    print(f"Znaleziono karnet: {membership.status}, typ: {membership.type}, wygasa: {membership.expiration_date}")
    return membership