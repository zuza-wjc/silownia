from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import crud
import schemas
from uuid import UUID
from datetime import date

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/reservations", response_model=schemas.ReservationOut)
def create_reservation(reservation: schemas.ReservationCreate, db: Session = Depends(get_db)):
    conflict = crud.get_conflicting_reservation(
        db, reservation.resource_id, reservation.start_time, reservation.end_time
    )
    if conflict:
        raise HTTPException(status_code=409, detail="Time slot already booked.")
    return crud.create_reservation(db, reservation)

@app.get("/reservations", response_model=list[schemas.ReservationOut])
def list_reservations(resource_id: UUID, date: date, db: Session = Depends(get_db)):
    return crud.get_reservations_by_resource(db, resource_id, date)

@app.delete("/reservations/{reservation_id}")
def cancel_reservation(reservation_id: UUID, db: Session = Depends(get_db)):
    res = crud.cancel_reservation(db, reservation_id)
    if not res:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return {"message": "Reservation cancelled"}
