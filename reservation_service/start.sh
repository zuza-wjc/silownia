#!/bin/sh
until nc -z broker 29092; do
  sleep 1
done
echo "Kafka dostępna, startuję..."
uvicorn main:app --host 0.0.0.0 --port 8004 --lifespan on