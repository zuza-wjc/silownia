import httpx
from fastapi import HTTPException
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FIREBASE_API_KEY")
FIREBASE_AUTH_URL = os.getenv("FIREBASE_AUTH_URL")

async def register_user(email: str, password: str):
    url = f"{FIREBASE_AUTH_URL}/accounts:signUp?key={API_KEY}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload)
        if resp.status_code != 200:
            error_message = resp.json().get("error", {}).get("message", "Nieznany błąd Firebase")
            raise HTTPException(status_code=400, detail=f"Błąd rejestracji: {error_message}")
        return resp.json()

async def login_user(email: str, password: str):
    url = f"{FIREBASE_AUTH_URL}/accounts:signInWithPassword?key={API_KEY}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload)
        if resp.status_code != 200:
            error_message = resp.json().get("error", {}).get("message", "Nieznany błąd Firebase")
            raise HTTPException(status_code=401, detail=f"Błąd logowania: {error_message}")
        return resp.json()