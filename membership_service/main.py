from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from database import SessionLocal
import requests
import crud
from models import MembershipType

app = FastAPI()

PAYMENT_API_URL = "https://73c7-37-248-220-226.ngrok-free.app/create_payment/"
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


@app.post("/buy-membership/")
def buy_membership(email: str, type: MembershipType, db: Session = Depends(get_db)):
    existing = crud.get_membership_by_email(db, email)
    if existing:
        raise HTTPException(status_code=400, detail="Klient już ma karnet.")
    
    membership = crud.create_membership(db, email, type.value, date.today())
    
    try:
        response = requests.post(PAYMENT_API_URL, json={
            "amount": MEMBERSHIP_PRICES[type.value],
            "description": "Zakup karnetu",
            "email": email
        })
        response.raise_for_status()
        payment_data = response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd przy tworzeniu płatności: {e}")

    return {
        "message": "Karnet kupiony. Przejdź do płatności.",
        "membership": membership,
        "payment": payment_data
    }
    

@app.post("/update_membership")
async def update_membership(data: dict, db: Session = Depends(get_db)):
    email = data.get("email")
    status = data.get("status")

    updated = crud.update_membership_status(db, email, status)

    if not updated:
        return {"error": "Nie znaleziono karnetu dla podanego emaila."}

    return {"message": f"Status zaktualizowany na {status} dla {email}"}
