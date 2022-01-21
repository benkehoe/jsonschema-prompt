# jsonschema-prompt

```python
import json

from jsonschema_prompt import prompt

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
value = prompt("test obj: ", schema1)
print(json.dumps(value, indent=2))

schema2 = {
    "type": "array",
    "items": {
        "type": "string",
    },
    "minItems": 3
}
value = prompt("test array: ", schema2)
print(json.dumps(value, indent=2))
```

```bash
python -m jsonschema_prompt --schema '{"type": "array", "items": {"type": "schema"}}'

echo '{"type": "array", "minItems": 3}' > schema.json
python -m jsonschema_prompt --schema-file schema.json
# loads yaml files if pyyaml is installed
```
