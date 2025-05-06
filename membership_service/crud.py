from datetime import date
from requests import Session
from models import Membership
from dateutil.relativedelta import relativedelta

def get_membership_by_email(db: Session, email: str):
    return db.query(Membership).filter(Membership.email == email).first()


def create_membership(db: Session, email: str, type: str, purchase_date: date):
    if type == "1m":
        expiration = purchase_date + relativedelta(months=1)
    elif type == "3m":
        expiration = purchase_date + relativedelta(months=3)
    elif type == "12m":
        expiration = purchase_date + relativedelta(months=12)
    else:
        raise ValueError("Nieprawidłowy typ karnetu")

    membership = Membership(
        email=email,
        type=type,
        purchase_date=purchase_date,
        expiration_date=expiration,
        status="inactive"
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


def update_membership_status(db: Session, email: str, status: str):
    membership = get_membership_by_email(db, email)
    if membership:
        membership.status = status
        db.commit()
        db.refresh(membership)
        return membership
    return None


def delete_membership_by_email(db: Session, email: str):
    membership = get_membership_by_email(db, email)
    if membership:
        db.delete(membership)
        db.commit()
        return True
    return False
