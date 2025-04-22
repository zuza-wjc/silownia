from fastapi import FastAPI, HTTPException
from models import Base, RegistrationRequest
from database import engine, SessionLocal
from services import register_client, unregister_client, get_class_list, get_class_participants
from aiokafka import AIOKafkaProducer
import asyncio

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


@app.post("/register")
async def register(req: RegistrationRequest):
    with SessionLocal() as db:
        return await register_client(db, req, producer)
    
@app.post("/unregister")
async def unregister(req: RegistrationRequest):
    with SessionLocal() as db:
        return await unregister_client(db, req, producer)

@app.get("/classes")
def list_classes():
    with SessionLocal() as db:
        return get_class_list(db)

@app.get("/classes/{class_id}")
def class_participants(class_id: int):
    with SessionLocal() as db:
        return get_class_participants(db, class_id)
    
