from datetime import date
from requests import Session
from models import Membership

def get_membership_by_email(db: Session, email: str):
    return db.query(Membership).filter(Membership.email == email).first()

def get_membership_by_id(db: Session, membership_id: int):
    return db.query(Membership).filter(Membership.id == membership_id).first()

def create_membership(db: Session, email: str, type: str, purchase_date: date):
    membership = Membership(
        email=email,
        type=type,
        purchase_date=purchase_date,
        expiration_date=None,
        status="created",
        redirect_url=None
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


def update_membership_status(db: Session, membership_id: int, status: str):
    membership = db.query(Membership).filter(Membership.id == membership_id).first()
    if membership:
        membership.status = status
        db.commit()
        db.refresh(membership)
        return membership
    return None

def update_membership_redirect_url(db: Session, membership_id: int, redirect_url: str):
    membership = db.query(Membership).filter(Membership.id == membership_id).first()
    if membership:
        membership.redirect_url = redirect_url
        db.commit()
        db.refresh(membership)
        return membership
    print(f"Nie znaleziono karnetu o ID {membership_id}")
    return None


def delete_membership_by_email(db: Session, email: str):
    membership = get_membership_by_email(db, email)
    if membership:
        db.delete(membership)
        db.commit()
        return True
    return False

def delete_membership_by_id(db: Session, membership_id: int):
    membership = db.query(Membership).filter(Membership.id == membership_id).first()
    if membership:
        db.delete(membership)
        db.commit()
        return True
    return False