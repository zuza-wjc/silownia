from fastapi import FastAPI
from models import Base, RegistrationRequest, CreateClassRequest, CancelClassRequest
from database import engine, SessionLocal
from services import join_class, create_class, get_class_list, get_class_participants, cancel_class
from aiokafka import AIOKafkaProducer

Base.metadata.create_all(bind=engine)
app = FastAPI()

producer = None

@app.on_event("startup")
async def startup_event():
    global producer
    producer = AIOKafkaProducer(bootstrap_servers="localhost:9092")
    await producer.start()

@app.on_event("shutdown")
async def shutdown_event():
    await producer.stop()


@app.post("/join-class")
async def join_clas(req: RegistrationRequest):
    with SessionLocal() as db:
        return await join_class(db, req, producer)
    
@app.post("/create-class")  
async def create_clas(req: CreateClassRequest):
    with SessionLocal() as db:
        return await create_class(db, req, producer)
    
@app.delete("/cancel-class")
async def cancel_clas(req: CancelClassRequest):
    with SessionLocal() as db:
        return await cancel_class(db, req, producer)

@app.get("/classes")
def list_classes():
    with SessionLocal() as db:
        return get_class_list(db)

@app.get("/classes/{class_id}")
def class_participants(class_id: int):
    with SessionLocal() as db:
        return get_class_participants(db, class_id)
    
