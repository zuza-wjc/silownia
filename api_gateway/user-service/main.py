from flask import Flask, request, jsonify
import os
import threading
from kafka import KafkaConsumer

app = Flask(__name__)

@app.route('/')
def get_user():
    print("kahfkahfh")
    return 'App user-service success'

@app.route('/users')
def get_all_users():
    return 'Return all users from user-service'

@app.route('/membership', methods=['POST'])
def post_membership():
    data = request.get_json()
    payment_method = data.get('payment_method') + ' - pass_service'
    type_ = data.get('type') + ' - pass_service'
    email = data.get('email') + ' - pass_service'
    data = {
        'email': email,
        'payment_method': payment_method,
        'type': type_
    }
    return jsonify({"data": data})


# Konfiguracja Kafka
KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC_NAME = "my-topic"

def kafka_consumer_job():
    print(">>> Kafka consumer wystartował", flush=True)
    try:
        consumer = KafkaConsumer(
            TOPIC_NAME,
            bootstrap_servers=KAFKA_SERVERS,
            group_id="flask-consumer-group",
            auto_offset_reset='earliest',
            enable_auto_commit=True
        )

        for message in consumer:
            print(f">>> Otrzymano wiadomość: {message.value.decode()}", flush=True)
    except Exception as e:
        print(f">>> Błąd Kafka consumer: {e}", flush=True)


# Uruchomienie konsumenta Kafka w osobnym wątku
def start_kafka_consumer():
    print("cokolwiek")
    thread = threading.Thread(target=kafka_consumer_job, daemon=True)
    thread.start()

# Startujemy konsumenta przed uruchomieniem Flask
start_kafka_consumer()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)