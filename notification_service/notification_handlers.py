from typing import Any, Callable

topic_translators: dict[str, str | Callable[[Any], str]] = {
	"payment-status": lambda msg: f"payment-status-{msg.value["status"]}"
}

topic_handlers: dict[str, Callable[[dict], dict]] = {
	"send-mail": lambda data: data,
	"payment-status-created": lambda data: {
		"subject": "Nowe zamówienie",
		"to": data.pop("mail"),
		"template": "new_order",
		"template_values": data
	},
	"payment-status-completed": lambda data: {
		"subject": "Potwierdzenie płatności",
		"to": data.pop("mail"),
		"template": "order_completed",
		"template_values": data
	},
}