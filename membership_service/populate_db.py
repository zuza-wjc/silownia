from database import SessionLocal, engine
from models import Membership, Base, MembershipType
from datetime import date, timedelta

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

memberships = [
    Membership(
        id=1, 
        email="jan.kowalski@example.com", 
        type=MembershipType.one_month, 
        purchase_date=date.today(), 
        expiration_date=date.today() + timedelta(days=30), 
        status="active"
    ),
    Membership(
        id=2, 
        email="anna.nowak@example.com", 
        type=MembershipType.three_months, 
        purchase_date=date.today() - timedelta(days=15), 
        expiration_date=date.today() + timedelta(days=75), 
        status="paid"
    ),
    Membership(
        id=3, 
        email="piotr.zielinski@example.com", 
        type=MembershipType.twelve_months, 
        purchase_date=date.today() - timedelta(days=100), 
        expiration_date=date.today() + timedelta(days=265), 
        status="active"
    ),
    Membership(
        id=4, 
        email="kasia.kwiatkowska@example.com", 
        type=MembershipType.one_month, 
        purchase_date=date.today() - timedelta(days=40), 
        expiration_date=date.today() - timedelta(days=10), 
        status="created"
    ),
]

db.add_all(memberships)
db.commit()
db.close()
