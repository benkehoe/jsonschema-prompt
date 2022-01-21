import json

from jsonschema_prompt import prompt

if False:
    value = prompt_string("test: ", {
        "type": "string",
        # "format": "date",
        # "minLength": 3,
    })
    print(value)

if False:
    value = prompt_boolean("test bool: ", {
        "type": "boolean"
    })
    print(value)

if False:
    schema = {
        "type": "object",
        "properties": {
            "a": {
                "type": "number",
            },
            "bar": {
                "type": "null",
            },
            "foo": {
                "type": "string"
            },
            "z": {
                "type": "boolean",
            }
        },
        "required": [ "foo" ],
        "additionalProperties": True,
    }
    value = prompt_from_schema("test obj: ", schema)
    print(json.dumps(value, indent=2))

if True:
    schema = {
        "type": "array",
        "items": {
            "type": "string",
        },
        "minItems": 3
    }
    value = prompt("test array: ", schema)
    print(json.dumps(value, indent=2))
