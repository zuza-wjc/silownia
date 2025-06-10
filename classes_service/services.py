from fastapi import HTTPException
from models import ClassGroup, Membership, Trainers

def join_class(db, req, producer):
    class_group = db.query(ClassGroup).filter(ClassGroup.id == req.class_id).first()
    membership = db.query(Membership).filter(Membership.id == req.client_id).first()
    email = membership.email
    status = membership.status

    if not membership:
        raise HTTPException(status_code=404, detail="Nie znaleziono użytkownika")

    if not class_group:
        raise HTTPException(status_code=404, detail="Nie znaleziono zajęć")

    if status != "active":
        return {"success": False, "message": "Brak ważnego karnetu"}
    
    subject = ""

    current_ids = class_group.user_ids.split(",") if class_group.user_ids else []
    if req.client_id in current_ids:
        event = "resign"
        subject = "Potwierdzenie rezygnacji z zajęć"
        updated_ids = [uid for uid in current_ids if uid != req.client_id]
        class_group.user_ids = ",".join(updated_ids)
    else:
        if (len(class_group.user_ids.split(",")) if class_group.user_ids else 0) >= class_group.capacity:
            return {"success": False, "message": "Brak wolnych miejsc"}
        event = "join"
        subject = "Potwierdzenie zapisu na zajęcia"
        current_ids.append(req.client_id)
        class_group.user_ids = ",".join(current_ids)
    
    db.commit()

    producer.send("class-evnets", value={
        "event": event,
        "class_id": req.class_id,
        "trainer_id": class_group.trainer_id,
        "title": class_group.title,
        "capacity": class_group.capacity,
        "email": email
    })

    return {"success": True, "message": f"{subject} Klient {email}: {class_group.title}"}

def create_class(db, req, producer):
    new_class = ClassGroup(
        trainer_id = req.trainer_id,
        title = req.title,
        capacity = req.capacity,
        user_ids = ""
    )

    db.add(new_class)
    db.commit()
    db.refresh(new_class)

    producer.send("class-evnets", value={
        "event": "create_class",
        "id": new_class.id,
        "trainer_id": new_class.trainer_id,
        "title": new_class.title,
        "capacity": new_class.capacity
    })

    return new_class

def cancel_class(db, req, producer):
    class_group = db.query(ClassGroup).filter(ClassGroup.id == req.class_id).first()

    if class_group:
        db.delete(class_group)
        db.commit()

        emails = class_group.user_ids.split(",") if class_group.user_ids else []

        producer.send("class-evnets", value={
            "event": "cancel_class",
            "id": class_group.id,
            "trainer_id": class_group.trainer_id,
            "title": class_group.title,
            "capacity": class_group.capacity,
            "emails": emails
        })

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

def update_status(db, email, status, expiration_date):
    membership = db.query(Membership).filter(Membership.email == email).first()

    if membership:
        membership.status = status
    else:
        membership = Membership(email=email, status=status, expiration_date=expiration_date)
        db.add(membership)

    db.commit()
    db.refresh(membership)
    return membership

def get_membership_list(db):
    return [{
        "id": c.id,
        "email": c.email
    } for c in db.query(Membership).all()]