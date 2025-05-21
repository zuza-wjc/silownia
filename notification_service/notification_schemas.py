import copy
from typing import TypedDict

"""
send-mail:
	value: (utf-8 encoded json) {
		"to": ["list", "of", "mails"],
		"subject": "mail subject"
		"body"?: "html body",			//Must include either body or template
		"template"?: "template_name",
		"template_values"?: {
			"template_key1": "value2",
			"template_key2": "value2",
			...
		}
	}
"""

blank_shema = {
	"$schema": "http://json-schema.org/draft-07/schema#",
	"type": "object",
	"required": [],
	"properties": {},
	"additionalProperties": True
}

raw_send_schema = {
	"$schema": "http://json-schema.org/draft-07/schema#",
	"type": "object",
	"required": ["to", "subject"],
	"properties": {
		"to": {
			"type": "array",
			"items": {
				"type": "string",
				"format": "email"
			},
			"minItems": 1
		},
		"subject": {
			"type": "string"
		},
		"body": {
			"type": "string"
		},
		"template": {
			"type": "string"
		},
		"template_values": {
			"type": "object",
			"additionalProperties": {
				"type": "string"
			}
		}
	},
	"oneOf": [
		{
			"required": ["body"]
		},
		{
			"required": ["template"]
		}
	]
}

class SchemaDict(TypedDict):
	required: list
	properties: dict

class Schema:
	schema: SchemaDict

	def __init__(self):
		self.schema = copy.deepcopy(blank_shema)

	def addProperty(self, name, type, required = False):
		schema_entry = {
			"type": type
		}

		self.schema["properties"][name] = schema_entry

		if required:
			self.schema["required"].append(name)

		return self

topic_schemas: dict[str, dict] = {
	"send-mail": raw_send_schema,
	"payment-status-created": Schema()
		.addProperty("mail", ["string", "array"], True)
		.addProperty("userName", "string", True)
		.addProperty("product", "string", True)
		.addProperty("price", "string", True)
		.addProperty("orderId", "string", True)
		.addProperty("redirect", "string", True)
		.schema,
	"payment-status-created": Schema()
		.addProperty("mail", ["string", "array"], True)
		.addProperty("userName", "string", True)
		.addProperty("price", "string", True)
		.schema,
}