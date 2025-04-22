from datetime import date
from requests import Session
from models import Membership

def get_membership_by_email(db: Session, email: str):
    return db.query(Membership).filter(Membership.email == email).first()

def create_membership(db: Session, email: str, type: str, purchase_date: date):
    membership = Membership(email=email, type=type, purchase_date=purchase_date, active="inactive")
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership

def update_membership_status(db: Session, email: str, status: str):
    membership = get_membership_by_email(db, email)
    if membership:
        membership.active = status
        db.commit()
        db.refresh(membership)
        return membership
    return None