from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

event = {
    "event": "pass_purchased",
    "data": {
        "user_id": "11111111-1111-1111-1111-111111111111",
        "valid_until": "2025-12-31T23:59:59"
    }
}

producer.send("passes", event).get(timeout=10)
print("Sent event")
producer.flush()
