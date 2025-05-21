import smtplib, ssl, json, os, traceback
from kafka import KafkaConsumer
from jsonschema import validate
from email.message import EmailMessage
from dotenv import load_dotenv

from notification_schemas import topic_schemas
from notification_handlers import topic_translators, topic_handlers

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
		return

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
consumer = KafkaConsumer(
    bootstrap_servers=os.getenv("KAFKA_BROKER"),
    auto_offset_reset="latest",
    enable_auto_commit=True,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    group_id="send-mail-group"
)

consumer.subscribe([""])

for message in consumer:
	try:
		topic = message.topic
		translator = topic_translators.get(topic)
		if translator:
			if translator is str:
				topic = translator
			elif translator is function:
				topic = translator(message)

		if not topic:
			continue

		validator = topic_schemas.get(topic)
		if validator:
			validate(message.value, validator)

		handler = topic_handlers.get(topic)
		if not handler:
			print(f"Topic '{topic}' has no handler!")
		else:
			data = handler(message.value)
			if data:
				send_mail(data)
		
	except Exception as error:
		print("Error", error)