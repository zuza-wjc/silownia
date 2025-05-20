from fastapi import FastAPI
from models import Base, RegistrationRequest, CreateClassRequest, CancelClassRequest
from database import engine, SessionLocal
from services import join_class, create_class, get_class_list, get_class_participants, cancel_class, update_status
from kafka import KafkaProducer, KafkaConsumer
import os, asyncio
import json
from contextlib import asynccontextmanager
import threading

pending: dict[str, asyncio.Future] = {}
loop: asyncio.AbstractEventLoop | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    def run_consumer():
        consume_events()

    global loop
    loop = asyncio.get_running_loop()
    thread = threading.Thread(target=run_consumer, daemon=True)
    thread.start()
    yield

app = FastAPI(lifespan=lifespan)

producer = KafkaProducer(
    bootstrap_servers=os.getenv("KAFKA_BROKER"),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

consumer = KafkaConsumer(
    'membership-status',
    bootstrap_servers=os.getenv("KAFKA_BROKER"),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    key_deserializer=lambda k: k.decode('utf-8') if k else None,
    group_id='membership-group'
)

def consume_events():
    for msg in consumer:
        event = msg.value
        with SessionLocal() as db:
            if event.get("status") == "active":
                email = event["email"]
                update_status(db, email, "active")
            # elif event.get("status") == "inactive":
            # elif event.get("status") == "paid":

@app.post("/join-class")
def join_clas(req: RegistrationRequest):
    with SessionLocal() as db:
        return join_class(db, req, producer)
    
@app.post("/create-class")  
def create_clas(req: CreateClassRequest):
    with SessionLocal() as db:
        return create_class(db, req, producer)
    
@app.delete("/cancel-class")
def cancel_clas(req: CancelClassRequest):
    with SessionLocal() as db:
        return cancel_class(db, req, producer)

@app.get("/classes")
def list_classes():
    with SessionLocal() as db:
        return get_class_list(db)

@app.get("/classes/{class_id}")
def class_participants(class_id: int):
    with SessionLocal() as db:
        return get_class_participants(db, class_id)
    
