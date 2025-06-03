from kafka import KafkaConsumer
import json
from sqlalchemy.orm import Session
from database import SessionLocal
import crud
from datetime import datetime

TOPIC = "pass-events"
KAFKA_BROKER = "localhost:9092"

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    group_id="reservation-service"
)

consumer.subscribe(['passes'])

print("Listening for pass events...")

for msg in consumer:
    event = msg.value
    print("Received:", event)
    db: Session = SessionLocal()

    try:
        if event["event"] == "pass_purchased":
            crud.upsert_pass(
                db,
                user_id=event["data"]["user_id"],
                valid_until=datetime.fromisoformat(event["data"]["valid_until"])
            )
        elif event["event"] == "pass_cancelled":
            crud.remove_pass(
                db,
                user_id=event["data"]["user_id"]
            )
    except Exception as e:
        print("Error processing message:", e)
    finally:
        db.close()
