from database import SessionLocal
from models import Client, ClassGroup, Base
from database import engine
from datetime import date

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

clients = [
    Client(id=1, name="Anna",   email="123@gmail.com", valid_until=date(2025, 4, 22)),
    Client(id=2, name="Bartek", email="313@gmail.com", valid_until=date(2025, 2, 12)),
    Client(id=3, name="Celina", email="151@gmail.com", valid_until=date(2025, 5, 15)),
]

classes = [
    ClassGroup(id=100, trainer_id=30, title="Yoga", capacity=2),
    ClassGroup(id=200, trainer_id=31, title="Crossfit", capacity=1),
]

db.add_all(clients + classes)
db.commit()
db.close()