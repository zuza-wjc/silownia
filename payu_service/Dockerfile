FROM python:3.10

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update \
 && apt-get install -y netcat-openbsd iputils-ping \
 && rm -rf /var/lib/apt/lists/*

RUN chmod +x start.sh

#CMD ["python", "notification_service.py"]
ENTRYPOINT ["./start.sh"]