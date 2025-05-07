docker build -t payu_service ./payu_service
docker build -t notification_service ./notification_service
docker build -t membership_service ./membership_service
docker-compose up -d --build
pause