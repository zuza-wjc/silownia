from database import SessionLocal
from models import ClassGroup, Base
from database import engine

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

classes = [
    ClassGroup(id=100, trainer_id=30, title="Yoga", capacity=2, user_ids=""),
    ClassGroup(id=200, trainer_id=31, title="Crossfit", capacity=1, user_ids=""),
]

db.add_all(classes)
db.commit()
db.close()
