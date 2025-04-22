from fastapi import HTTPException
from models import Client, ClassGroup
from datetime import date
from models import ClassEnrollmentRequest
import httpx
import json

async def register_client(db, req, producer):
    client = db.query(Client).filter(Client.id == req.client_id).first()
    class_group = db.query(ClassGroup).filter(ClassGroup.id == req.class_id).first()

    if not client:
        raise HTTPException(status_code=404, detail="Nie znaleziono klienta")

    if not class_group:
        raise HTTPException(status_code=404, detail="Nie znaleziono zajęć")

    current_date = date.today()

    if client.valid_until < current_date:
        return {"success": False, "message": "Brak ważnego karnetu"}

    if len(class_group.participants) >= class_group.capacity:
        return {"success": False, "message": "Brak wolnych miejsc"}

    if client in class_group.participants:
        return {"success": False, "message": "Klient już zapisany na te zajęcia"}

    class_group.participants.append(client)
    db.commit()

    class_group = db.query(ClassGroup).filter(ClassGroup.id == req.class_id).first()

    event = {
        "event": "client_registered",
        "client_id": req.client_id,
        "client_name": client.name,
        "class_id": req.class_id,
        "class_title": class_group.title,
        "trainer_id": class_group.trainer_id
    }
    await producer.send_and_wait("class-events", json.dumps(event).encode("utf-8"))

    return {"success": True, "message": f"Klient {client.name} zapisany na zajęcia: {class_group.title}"}

async def unregister_client(db, req, producer):
    client = db.query(Client).filter(Client.id == req.client_id).first()
    class_group = db.query(ClassGroup).filter(ClassGroup.id == req.class_id).first()

    if not client:
        raise HTTPException(status_code=404, detail="Nie znaleziono klienta")

    if not class_group:
        raise HTTPException(status_code=404, detail="Nie znaleziono zajęć")

    if client not in class_group.participants:
        return {"success": False, "message": "Klient nie jest zapisany na te zajęcia"}

    class_group.participants.remove(client)
    db.commit()

    event = {
        "event": "client_unregistered",
        "client_id": req.client_id,
        "client_name": client.name,
        "class_id": req.class_id,
        "class_title": class_group.title,
        "trainer_id": class_group.trainer_id
    }
    await producer.send_and_wait("class-events", json.dumps(event).encode("utf-8"))

    return {"success": True, "message": f"Klient {client.name} wypisał się z zajęć: {class_group.title}"}


async def send_email(trainer_id: int, new_user_id: int):
    url = "http://127.0.0.1:8001/sign_up/"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json={"trainer_id": trainer_id, "new_user_id": new_user_id})
        return response.json()

def get_class_list(db):
    return [{
        "id": c.id,
        "title": c.title,
        "capacity": c.capacity,
        "enrolled": len(c.participants)
    } for c in db.query(ClassGroup).all()]

def get_class_participants(db, class_id):
    class_group = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
    if not class_group:
        return {"message": "Zajęcia nie istnieją"}
    return {
        "class": class_group.title,
        "participants": [{c.name, c.id} for c in class_group.participants]
    }