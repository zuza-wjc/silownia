"""
payment-status:
	key: PayU
	value: (utf-8 encoded json) {
		internalId: <internalId>
		orderId: "<orderId>",
		payuId: "<payuOrderId>",
		status: "CREATED" | "PENDING" | "WAITING_FOR_CONFIRMATION" | "COMPLETED" | "CANCELED",
		redirect?: "https://link.to/redirect/user"
	}
"""
status_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["internalId", "orderId", "payuId", "status"],
    "properties": {
		"internalId": {
            "type": "string"
        },
        "orderId": {
            "type": "string"
        },
        "payuId": {
            "type": "string"
        },
        "status": {
            "type": "string",
            "enum": [
                "created",
                "success",
                "failed"
            ]
        },
        "redirect": {
            "type": "string",
            "format": "uri"
        }
    },
    "additionalProperties": False
}

"""
create-payment:
	key: PayU
	value: (utf-8 encoded json) {
		key: internalId
		description: "Payment description"
		customer: {
			id: "customerId",
			ip: "123.456.789.000"
			email: "email@example.com",
			firstName: "Jan",
			lastName: "Kowalski",
		},
		products: [
			{
				name: "Product name",
				price: 100.29
			},
			...
		],
	}
"""
payment_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["internalId", "description", "customer", "products"],
    "properties": {
		"internalId": {
            "type": "string"
        },
        "description": {
            "type": "string"
        },
        "customer": {
            "type": "object",
            "required": ["id", "ip", "email", "firstName", "lastName"],
            "properties": {
                "id": {
                    "type": "string"
                },
                "ip": {
                    "type": "string",
                    "format": "ipv4"
                },
                "email": {
                    "type": "string",
                    "format": "email"
                },
                "firstName": {
                    "type": "string"
                },
                "lastName": {
                    "type": "string"
                }
            },
            "additionalProperties": False
        },
        "products": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["name", "price"],
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "price": {
                        "type": "number",
                        "minimum": 0
                    }
                },
                "additionalProperties": False
            }
        }
    },
    "additionalProperties": False
}

"""
payu-notification:
	value: (utf-8 encoded json) {
		orderId: <orderId>,
		extOrderId: <payuOrderId>,
		status: <paymentStatus>
	}
"""
notification_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["orderId", "extOrderId", "status"],
    "properties": {
        "orderId": {
            "type": "string"
        },
        "extOrderId": {
            "type": "string"
        },
        "status": {
            "type": "string",
            "enum": [
                "CREATED",
                "PENDING",
                "WAITING_FOR_CONFIRMATION",
                "COMPLETED",
                "CANCELED"
            ]
        },
    },
    "additionalProperties": True
}

response_schema = {
	"$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["orderId", "extOrderId", "redirectUri"],
    "properties": {
        "orderId": {
            "type": "string"
        },
        "extOrderId": {
            "type": "string"
        },
        "redirectUri": {
			"type": "string",
            "format": "uri"
		}
    },
    "additionalProperties": True
}