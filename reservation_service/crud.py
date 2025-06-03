from sqlalchemy.orm import Session
from models import Reservation
from schemas import ReservationCreate
from datetime import datetime, timedelta
from sqlalchemy import and_
from models import Pass


def get_conflicting_reservation(db: Session, resource_id, start_time, end_time):
    return db.query(Reservation).filter(
        Reservation.resource_id == resource_id,
        Reservation.start_time < end_time,
        Reservation.end_time > start_time,
        Reservation.status == "active"
    ).first()


def create_reservation(db: Session, reservation: ReservationCreate):
    db_res = Reservation(**reservation.dict())
    db.add(db_res)
    db.commit()
    db.refresh(db_res)
    return db_res


def get_reservations_by_resource(db: Session, resource_id, date):
    # zamiana date (czyli np. 2025-04-18) na datetime z godziną 00:00
    start_of_day = datetime.combine(date, datetime.min.time())
    # koniec dnia – dzień później o 00:00 (czyli przed północą)
    end_of_day = start_of_day + timedelta(days=1)

    return db.query(Reservation).filter(
        Reservation.resource_id == resource_id,
        Reservation.start_time >= start_of_day,
        Reservation.start_time < end_of_day,
    ).all()


def cancel_reservation(db: Session, reservation_id):
    res = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if res:
        res.status = "cancelled"
        db.commit()
    return res


def upsert_pass(db: Session, user_id: str, valid_until: datetime):
    existing = db.query(Pass).filter_by(user_id=user_id).first()
    if existing:
        existing.valid_until = valid_until
    else:
        new_pass = Pass(user_id=user_id, valid_until=valid_until)
        db.add(new_pass)
    db.commit()


def remove_pass(db: Session, user_id: str):
    db.query(Pass).filter_by(user_id=user_id).delete()
    db.commit()


def has_valid_pass(db: Session, user_id: str) -> bool:
    p = db.query(Pass).filter_by(user_id=user_id).first()
    return p is not None and p.valid_until >= datetime.utcnow()
