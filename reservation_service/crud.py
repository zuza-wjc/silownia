from sqlalchemy.orm import Session
from models import Reservation
from schemas import ReservationCreate
from datetime import datetime, timedelta
from sqlalchemy import and_


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
