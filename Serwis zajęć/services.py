from fastapi import HTTPException
from models import ClassGroup
import httpx
import json

USER_SERVICE_URL = "http://localhost:8001"

async def join_class(db, req, producer):
    class_group = db.query(ClassGroup).filter(ClassGroup.id == req.class_id).first()
    email = req.client_email

    try:
        # response = httpx.get(f"{USER_SERVICE_URL}/get-pass/{req.client_id}", timeout=5.0)
        response = httpx.get(f"{USER_SERVICE_URL}/get-membership/?email={email}", timeout=5.0)
        response.raise_for_status()
        data = response.json()
        status = data["status"]
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Serwis karnetów jest niedostępny")
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=400, detail="Nie znaleziono użytkownika")

    if not class_group:
        raise HTTPException(status_code=404, detail="Nie znaleziono zajęć")

    if not status:
        return {"success": False, "message": "Brak ważnego karnetu"}

    subject = ""
    body = ""

    current_ids = class_group.user_ids.split(",") if class_group.user_ids else []
    if str(email) in current_ids:
        subject = "Potwierdzenie rezygnacji z zajęć"
        body = "<h1>Otrzymaliśmy informację o Twojej rezygnacji z zajęć</h1><p>Do zobaczenia!</p>"
        updated_ids = [uid for uid in current_ids if uid != str(email)]
        class_group.user_ids = ",".join(updated_ids)
    else:
        if (len(class_group.user_ids.split(",")) if class_group.user_ids else 0) >= class_group.capacity:
            return {"success": False, "message": "Brak wolnych miejsc"}
        
        subject = "Potwierdzenie zapisu na zajęcia"
        body = "<h1>Dziękujemy za zapis</h1><p>Do zobaczenia!</p>"
        current_ids.append(str(email))
        class_group.user_ids = ",".join(current_ids)
    
    db.commit()

    mail_payload = {
        "event": "send-mail",
        "to": [email],
        "subject": subject,
        "body": body
    }

    message = json.dumps(mail_payload, ensure_ascii=False).encode("utf-8")
    await producer.send("class-events", message)

    return {"success": True, "message": f"{subject} Klient {email}: {class_group.title}"}

async def create_class(db, req, producer):
    new_class = ClassGroup(
        trainer_id = req.trainer_id,
        title = req.title,
        capacity = req.capacity,
        user_ids = ""
    )

    db.add(new_class)
    db.commit()
    db.refresh(new_class)

    event = {
        "event": "create_class",
        "id": new_class.id,
        "trainer_id": new_class.trainer_id,
        "title": new_class.title,
        "capacity": new_class.capacity
    }
    await producer.send_and_wait("class-events", json.dumps(event).encode("utf-8"))

    return new_class

async def cancel_class(db, req, producer):
    class_group = db.query(ClassGroup).filter(ClassGroup.id == req.class_id).first()

    if class_group:
        db.delete(class_group)
        db.commit()

        emials = class_group.user_ids.split(",") if class_group.user_ids else []

        subject = "Odwołanie zajęć"
        body = f"<h1>Informujemy o odwołaniu zajęć {class_group.title}</h1><p>Twoje najbliższe zajęcia zostały odwołane. Przepraszamy za niedogodności i zapraszamy do zapisu na inny termin.</p>"


        mail_payload = {
            "event": "send-mail",
            "to": [emials],
            "subject": subject,
            "body": body
        }

        await producer.send_and_wait("class-events", json.dumps(mail_payload).encode("utf-8"))
        return True
    
    return False

def get_class_list(db):
    return [{
        "id": c.id,
        "title": c.title,
        "capacity": c.capacity,
        "enrolled": len(c.user_ids.split(",")) if c.user_ids else 0
    } for c in db.query(ClassGroup).all()]

def get_class_participants(db, class_id):
    class_group = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
    if not class_group:
        return {"message": "Zajęcia nie istnieją"}
    return {
        "class": class_group.title,
        "participants": class_group.user_ids
    }