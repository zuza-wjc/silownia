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
                client_id = event["client_id"]
                class_title = event["class_title"]
                print(f"[NOTIFY] Trener {trainer_id}: Nowy zapis – {client_id} na {class_title}")

            elif event.get("event") == "client_unregistered":
                trainer_id = event["trainer_id"]
                client_id = event["client_id"]
                class_title = event["class_title"]
                print(f"[NOTIFY] Trener {trainer_id}: Rezygnacja – {client_id} z {class_title}")

            elif event.get("event") == "create_class":
                id = event["id"]
                trainer_id = event["trainer_id"]
                title = event["title"]
                capacity = event["capacity"]
                print(f"[NOTIFY] Trenet {trainer_id}: Utworzono nowe zajęcia {title} o id: {id}, z ilością miejsc {capacity}")

            elif event.get("event") == "cancle_class":
                to = event["to"]
                subject = event["subject"]
                body = event["body"]
                print(f"[NOTIFY] {subject} \n {body}")

            elif event.get("event") == "send-mail":
                to = event["to"]
                subject = event["subject"]
                body = event["body"]
                print(f"[NOTIFY] {subject} \n {body}")

                         
    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(main())
