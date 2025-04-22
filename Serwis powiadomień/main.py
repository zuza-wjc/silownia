from aiokafka import AIOKafkaConsumer
import asyncio
import json

KAFKA_TOPIC = "class-events"
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

async def main():
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="trainer-notifier-group"
    )
    await consumer.start()

    try:
        print("Trainer Notifier Service listening...")
        async for msg in consumer:
            event = json.loads(msg.value)
            if event.get("event") == "client_registered":
                trainer_id = event["trainer_id"]
                client_name = event["client_name"]
                class_title = event["class_title"]
                print(f"[NOTIFY] Trener {trainer_id}: Nowy zapis – {client_name} na {class_title}")

            elif event.get("event") == "client_unregistered":
                trainer_id = event["trainer_id"]
                client_name = event["client_name"]
                class_title = event["class_title"]
                print(f"[NOTIFY] Trener {trainer_id}: Rezygnacja – {client_name} z {class_title}")
    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(main())
