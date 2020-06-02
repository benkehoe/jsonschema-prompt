# jsonschema-prompt

```python
import json

from jsonschema_prompt.prompt import *

schema1 = {
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
value = prompt_from_schema("test obj: ", schema1)
print(json.dumps(value, indent=2))

schema2 = {
    "type": "array",
    "items": {
        "type": "string",
    },
    "minItems": 3
}
value = prompt_from_schema("test array: ", schema2)
print(json.dumps(value, indent=2))
```
