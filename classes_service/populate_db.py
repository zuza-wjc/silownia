from database import SessionLocal, engine
from models import ClassGroup, Membership, Trainers, Base
from datetime import date, timedelta

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

memberships = [
    Membership(
        id=1, 
        email="jan.kowalski@example.com", 
        expiration_date=date.today() + timedelta(days=30), 
        status="active"
    ),
    Membership(
        id=2, 
        email="anna.nowak@example.com", 
        expiration_date=date.today() + timedelta(days=75), 
        status="paid"
    ),
    Membership(
        id=3, 
        email="piotr.zielinski@example.com", 
        expiration_date=date.today() + timedelta(days=265), 
        status="active"
    ),
    Membership(
        id=4, 
        email="kasia.kwiatkowska@example.com", 
        expiration_date=date.today() - timedelta(days=10), 
        status="inactive"
    ),
]

classes = [
    ClassGroup(
        id=100,
        trainer_id=30,
        title="Yoga",
        capacity=2,
        user_ids=""),
    ClassGroup(
        id=200,
        trainer_id=31,
        title="Crossfit",
        capacity=1,
        user_ids=""
    ),
]

trainers = [
    Trainers(
        id=1,
        email="jan.nowak@example.com"
    ),
    Trainers(
        id=2,
        email="krzysztof.stefan@example.com"
    ),
]

db.add_all(memberships)
db.add_all(classes)
db.add_all(trainers)
db.commit()
db.close()
