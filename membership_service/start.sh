#!/bin/sh
echo "Czekam na Kafka..."
until nc -z broker 29092; do
  sleep 1
done
echo "Kafka dostępna, startuję..."
uvicorn main:app --host 0.0.0.0 --port 8005 --lifespan on