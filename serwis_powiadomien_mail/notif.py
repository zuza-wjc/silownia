import smtplib, ssl, json
from quixstreams import Application
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

smtp_server = "smtp.ethereal.email"
port = "587"
username = "abigayle.keeling@ethereal.email"
password = "BVRcXekVfe6quEqrFa"

message = """\
Subject: Test

Testowa wiadomosc
"""

app = Application(
	broker_address="localhost:9092",
)

context = ssl.create_default_context()

server = smtplib.SMTP(smtp_server, port)
server.starttls(context=context)
server.login(username, password)

def sned_mail(data):
	message = MIMEMultipart()
	message["Subject"] = data["subject"]
	message["From"] = username
	message["To"] = data["to"]

	html = f"""\
<html>
<body>
{data["message"]}
</body>
</html>
"""

	message.attach(MIMEText(html, "html", "utf-8"))
	server.sendmail(username, data["to"], message.as_string())

with app.get_consumer() as consumer:
	consumer.subscribe(["send-mail"])

	while True:
		result = consumer.poll(1)
		if result is not None:
			sned_mail(json.loads(result.value().decode("utf-8")))