from sqlalchemy.orm import Session
from models import UserProfile
from datetime import date

def create_user_profile(db: Session, email: str, first_name: str, last_name: str, birth_date: date, address: str):
    user = UserProfile(
        email=email,
        first_name=first_name,
        last_name=last_name,
        birth_date=birth_date,
        address=address
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user