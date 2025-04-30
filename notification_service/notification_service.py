import smtplib, ssl, json, os, traceback
from quixstreams import Application
from jsonschema import validate
from email.message import EmailMessage
from dotenv import load_dotenv

from notification_schemas import message_schema
from notification_templates import templates

load_dotenv()

smtp_server = os.getenv("SMTP_SERVER")
port = os.getenv("SMTP_PORT")
username = os.getenv("SMTP_USERNAME")
password = os.getenv("SMTP_PASSWORD")

# Get body from message
def get_body(data: dict) -> str | None:
	template: str = data.get("template")
	if template:
		body = templates.get(template)
		if not body:
			return

		values: dict = data.get("template_values")
		return values and body.format(**values) or body
	else:
		return data["body"]

# Build base message
def build_message(to: str, subject: str, single = True) -> EmailMessage:
	message = EmailMessage()
	message["From"] = username
	message["Subject"] = subject

	if single:
		message["To"] = to
	else:
		message["Bcc"] = to

	message.set_content("Twoja przeglądarka poczty nie obsługuje HTML.")

	return message

def send_mail(data: dict):
	subject = data["subject"]
	to = data["to"]
	to_str = ", ".join(to)
	body = get_body(data)

	if not body:
		print("Failed to send message - no body", data.get("body"), data.get("template"))

	message = build_message(to_str, subject, len(to) == 1)
	message.add_alternative(body, subtype="html")

	send_message(message, to)


def send_message(message: EmailMessage, to: list[str]):
	try:
		server = smtplib.SMTP(smtp_server, port)
		server.starttls(context=ssl.create_default_context())
		server.login(username, password)

		server.send_message(message, to_addrs=to)
		print(f"Message(s) sent to: {to}")
	except Exception as error:
		print("An error occured while attempting to send mail:", error, traceback.format_exc())

# Listen to kafka events
app = Application(
	broker_address=os.getenv("KAFKA_BROKER"),
	consumer_group="send-mail-group"
)

with app.get_consumer() as consumer:
	consumer.subscribe(["send-mail"])

	while True:
		result = consumer.poll(1)
		if result is not None:
			jsonObject = json.loads(result.value().decode("utf-8"))
			try:
				validate(jsonObject, message_schema)
				send_mail(jsonObject)
			except Exception as error:
				print("JSON Schema validation failed", error)