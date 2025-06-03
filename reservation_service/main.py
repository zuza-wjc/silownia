from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import crud
import schemas
from uuid import UUID
from datetime import date, datetime
from kafka import KafkaProducer
import json
import os

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Kafka Producer init
KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "localhost:9092")
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER_URL,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

NOTIFICATION_TOPIC = "send-mail"


def send_notification(event_type: str, data: dict):
    payload = {"event": event_type, "data": data}
    producer.send(NOTIFICATION_TOPIC, payload)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/reservations", response_model=schemas.ReservationOut)
def create_reservation(reservation: schemas.ReservationCreate, db: Session = Depends(get_db)):
    if reservation.start_time >= reservation.end_time:
        raise HTTPException(status_code=400, detail="Start time must be before end time.")
    if reservation.start_time < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Cannot reserve in the past.")

    if not crud.has_valid_pass(db, str(reservation.user_id)):
        raise HTTPException(status_code=403, detail="User does not have a valid pass.")

    conflict = crud.get_conflicting_reservation(
        db, reservation.resource_id, reservation.start_time, reservation.end_time
    )
    if conflict:
        raise HTTPException(status_code=409, detail="Time slot already booked.")

    res = crud.create_reservation(db, reservation)
    send_notification("reservation_created", {"reservation_id": str(res.id), "user_id": str(res.user_id)})
    return res



@app.get("/reservations", response_model=list[schemas.ReservationOut])
def list_reservations(resource_id: UUID, date: date, db: Session = Depends(get_db)):
    return crud.get_reservations_by_resource(db, resource_id, date)


@app.delete("/reservations/{reservation_id}")
def cancel_reservation(reservation_id: UUID, db: Session = Depends(get_db)):
    res = crud.cancel_reservation(db, reservation_id)
    if not res:
        raise HTTPException(status_code=404, detail="Reservation not found")
    send_notification("reservation_cancelled", {"reservation_id": str(res.id), "user_id": str(res.user_id)})
    return {"message": "Reservation cancelled"}


@app.post("/report-fault")
def report_fault(user_id: UUID, class_id: UUID):
    send_notification("fault_reported", {"user_id": str(user_id), "class_id": str(class_id)})
    return {"message": "Fault reported"}


@app.post("/confirm-fault")
def confirm_fault(class_id: UUID):
    send_notification("fault_confirmed", {"class_id": str(class_id)})
    return {"message": "Fault confirmed"}


@app.post("/clear-fault")
def clear_fault(class_id: UUID):
    send_notification("fault_cleared", {"class_id": str(class_id)})
    return {"message": "Fault cleared"}


@app.post("/reserve-equipment-or-room")
def reserve_equipment_or_room(reservation: schemas.ReservationCreate, db: Session = Depends(get_db)):
    if reservation.start_time >= reservation.end_time:
        raise HTTPException(status_code=400, detail="Start time must be before end time.")
    conflict = crud.get_conflicting_reservation(
        db, reservation.resource_id, reservation.start_time, reservation.end_time
    )
    if conflict:
        raise HTTPException(status_code=409, detail="Time slot already booked.")

    # walidacja karnetu
    res = crud.create_reservation(db, reservation)
    send_notification("equipment_reserved", {"reservation_id": str(res.id), "user_id": str(res.user_id)})
    return res