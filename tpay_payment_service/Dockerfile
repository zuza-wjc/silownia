FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update \
 && apt-get install -y netcat-openbsd iputils-ping \
 && rm -rf /var/lib/apt/lists/*

RUN chmod +x start.sh

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["./start.sh"]
