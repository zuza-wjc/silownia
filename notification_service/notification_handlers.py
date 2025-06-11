from typing import Any, Callable

topic_translators: dict[str, str | Callable[[Any], str]] = {
	"payment-status": lambda msg: f"payment-status-{msg.value['status']}",
	"reservation-status": lambda msg: f"reservation-{msg.value['status']}",
	"class-events": lambda msg: f"class-{msg.value['event']}",
	"send-mail": "send-mail",
}

topic_handlers: dict[str, Callable[[dict], dict]] = {
	"send-mail": lambda data: data,
	"payment-status-created": lambda data: {
		"subject": "Nowe zamówienie",
		"to": data.pop("mail"),
		"template": "new_order",
		"template_values": data
	},
	"payment-status-success": lambda data: {
		"subject": "Potwierdzenie płatności",
		"to": data.pop("mail"),
		"template": "order_completed",
		"template_values": data
	},
	"reservation-created": lambda data: {
		"subject": "Potwierdzenie rezerwacji",
		"to": data.pop("email"),
		"template": "reservation_created",
		"template_values": data
	},
	"reservation-canceled": lambda data: {
		"subject": "Anulowanie rezerwacji",
		"to": data.pop("email"),
		"template": "reservation_canceled",
		"template_values": data
	},
	"class-join": lambda data: {
		"subject": "Dołączono na zjęcia grupowe",
		"to": data.pop("email"),
		"template": "class_joined",
		"template_values": data
	},
	"class-resign": lambda data: {
		"subject": "Opuszczono zajęcia grupowe",
		"to": data.pop("email"),
		"template": "class_left",
		"template_values": data
	},
	"class-cancel_class": lambda data: {
		"subject": "Zajęcia grupowe odwołane",
		"to": data.pop("emails"),
		"template": "class_canceled",
		"template_values": data
	},
}