FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential
RUN apt-get install -y netcat-openbsd iputils-ping \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt


COPY . .

RUN chmod +x start.sh
ENV PYTHONUNBUFFERED=1

#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
ENTRYPOINT ["./start.sh"]