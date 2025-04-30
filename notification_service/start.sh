#!/bin/sh
echo "Czekam na Kafka..."
until nc -z broker 29092; do
  sleep 1
done
echo "Kafka dostępna, startuję..."
python notification_service.py