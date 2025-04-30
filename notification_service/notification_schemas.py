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

message_schema = {
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