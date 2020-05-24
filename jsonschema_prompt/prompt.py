import json
import sys
import collections
import itertools
import string

import jsonschema

import prompt_toolkit
from prompt_toolkit.validation import Validator, ValidationError

Prompters = collections.namedtuple('Prompters', ['str', 'bool', 'print'])

DEFAULT_PROMPTERS = Prompters(
    str=prompt_toolkit.shortcuts.prompt,
    bool=prompt_toolkit.shortcuts.confirm,
    print=prompt_toolkit.shortcuts.print_formatted_text,
)

INDENT_WIDTH=2
def get_indent(indent):
    return ' ' * indent * INDENT_WIDTH

def colored_text(color, text):
    return prompt_toolkit.formatted_text.FormattedText([
        (color, text)
    ])

class JSONSchemaValidator(Validator):
    def __init__(self, schema):
        self.schema = schema
        self.validator = jsonschema.Draft7Validator(self.schema, format_checker=jsonschema.draft7_format_checker)

    def get_json(self, document):
        try:
            return json.loads(document.text)
        except json.JSONDecodeError as e:
            raise ValidationError(message=str(e))

    def validate(self, document):
        obj = self.get_json(document)
        errors = [e.message for e in self.validator.iter_errors(obj)]
        if errors:
            raise ValidationError(message='\n'.join(errors))

class StringJSONSchemaValidator(JSONSchemaValidator):
    def get_json(self, document):
        return document.text

def prompt_continuation(width, line_number, is_soft_wrap):
    return '.' * width

def prompt_string(prompt_text, schema, indent=0, prompters=None):
    prompters = prompters or DEFAULT_PROMPTERS
    validator = StringJSONSchemaValidator(schema)
    prompt_args = {
        "message": get_indent(indent) + prompt_text,
        "validator": validator,
        "validate_while_typing": False,
    }
    if schema.get("multiline", False) is True:
        prompt_args["multiline"] = True
        prompt_args["prompt_continuation"] = prompt_continuation
    if schema.get("default"):
        prompt_args["default"] = str(schema["default"])
    return prompters.str(**prompt_args)

def prompt_number(prompt_text, schema, indent=0, prompters=None):
    prompters = prompters or DEFAULT_PROMPTERS
    validator = JSONSchemaValidator(schema)
    prompt_args = {
        "message": get_indent(indent) + prompt_text,
        "validator": validator,
        "validate_while_typing": False,
    }
    if schema.get("default"):
        prompt_args["default"] = str(schema["default"])
    return float(prompters.str(**prompt_args))

def prompt_boolean(prompt_text, schema, indent=0, prompters=None):
    prompters = prompters or DEFAULT_PROMPTERS
    prompt_args = {
        "message": get_indent(indent) + prompt_text,
    }
    # prompt_args["key_bindings"] = kb
    return prompters.bool(**prompt_args)

def prompt_null(prompt_text, schema, indent=0, prompters=None):
    return None

def prompt_array(prompt_text, schema, indent=0, prompters=None):
    prompters = prompters or DEFAULT_PROMPTERS
    validator = jsonschema.Draft7Validator(schema, format_checker=jsonschema.draft7_format_checker)
    min_items = schema.get("minItems")
    max_items = schema.get("maxItems")

    prompters.print(schema)

    if "items" in schema:
        items = schema["items"]
        if isinstance(items, (list, tuple)):
            # print('items is a list')
            # items is a list
            indexed_items = items
            if "additionalItems" in schema:
                additional_items = schema["additionalItems"]
                if isinstance(additional_items, dict):
                    # print("add'l items is a schema")
                    # add'l items is a schema
                    additional_items_allowed = True
                    additional_items_schema = additional_items
                    additional_items_types = _find_types(additional_items)
                else:
                    # print("add'l items bool")
                    # add'l items set to a boolean
                    additional_items_allowed = additional_items
                    additional_items_schema = {}
                    additional_items_types = ALL_TYPES
            else:
                # print("items is list, no addl items prop")
                # items is a list but no add'l items property is set
                additional_items_allowed = False
                additional_items_schema = {}
                additional_items_types = ALL_TYPES
        else:
            # print("items is a schema")
            # items is a single schema, becomes add'l items
            indexed_items = []
            additional_items_allowed = True
            additional_items_schema = items
            additional_items_types = _find_types(items)
    else:
        # print("no items prop")
        # no items set, add'l items all allowed
        indexed_items = []
        additional_items_allowed = True
        additional_items_schema = {}
        additional_items_types = ALL_TYPES

    prompters.print(get_indent(indent) + prompt_text)

    while True:
        array = []
        for i in itertools.count():
            over_min_length = min_items is None or i >= min_items
            over_max_length = max_items is not None and i >= max_items
            if i < len(indexed_items):
                item_schema = indexed_items[i]
                prompt_text_tuple = (f"Enter a value [$type]: ", f"Enter a value: ")
                value = prompt_from_schema(prompt_text_tuple, item_schema, indent=indent+1, prompters=prompters)
            elif over_max_length or not additional_items_allowed:
                break
            else:
                item_schema = additional_items_schema
                end_text = " (CTRL+D to finish)" if over_min_length else  ""
                prompt_text_tuple = (f"Enter a value [$type]{end_text}: ", f"Enter a value{end_text}: ")
                try:
                    value = prompt_from_types(prompt_text_tuple, additional_items_types, indent=indent+1, prompters=prompters)
                except EOFError:
                    break

            array.append(value)

        errors = [e.message for e in validator.iter_errors(array)]
        if errors:
            prompters.print(colored_text("#ff0000", "\n".join(get_indent(indent+1) + e for e in errors)))
            prompters.print(colored_text("#ff0000", get_indent(indent+1) + "Array has been reset"))
        else:
            return array

def prompt_object(prompt_text, schema, indent=0, prompters=None):
    prompters = prompters or DEFAULT_PROMPTERS
    validator = jsonschema.Draft7Validator(schema, format_checker=jsonschema.draft7_format_checker)
    prompters.print(get_indent(indent) + prompt_text)
    while True:
        obj = {}
        required_properties = schema.get("required", [])
        properties = required_properties + [p for p in schema.get("properties", {}) if p not in required_properties]
        additional_properties = schema.get("additionalProperties", True)

        for property_name in properties:
            property_required = property_name in required_properties
            property_schema = schema.get("properties", {}).get(property_name, {})
            req_str = " [REQUIRED]" if property_required else ""

            prompt_text_tuple = (f"{property_name} [$type]{req_str}: ", f"{property_name} {req_str}: ")

            value = prompt_from_schema(prompt_text_tuple, property_schema, indent=indent+1, prompters=prompters)
            obj[property_name] = value

        if additional_properties:
            while True:
                try:
                    property_name = prompt_string("Enter a property name (CTRL+D to finish): ", {"type": "string"}, indent=indent+1, prompters=prompters)
                except EOFError:
                    break
                if property_name in obj:
                    print(get_indent(indent+1) + "Property already exists")
                    continue
                value = prompt_from_types("Enter the property value: ", ALL_TYPES, indent=indent+1, prompters=prompters)
                obj[property_name] = value

        errors = [e.message for e in validator.iter_errors(obj)]
        if errors:
            prompters.print(colored_text("#ff0000", "\n".join(get_indent(indent+1) + e for e in errors)))
            prompters.print(colored_text("#ff0000", get_indent(indent+1) + "Object has been reset"))
        else:
            return obj

PROMPT_FUNCS = {
    "array": prompt_array,
    "boolean": prompt_boolean,
    "integer": prompt_number,
    "null": prompt_null,
    "number": prompt_number,
    "object": prompt_object,
    "string": prompt_string,
}

ALL_TYPES = list(PROMPT_FUNCS.keys())

_ALL_ALL_TYPES_COMPLETER = prompt_toolkit.completion.WordCompleter(ALL_TYPES, ignore_case=True)

def get_type_completer(types):
    if not types:
        return _ALL_ALL_TYPES_COMPLETER
    else:
        return prompt_toolkit.completion.WordCompleter(ALL_TYPES, ignore_case=True)

_ALL_ALL_TYPES_VALIDATOR = prompt_toolkit.validation.Validator.from_callable(
    lambda text: text in ALL_TYPES,
    error_message="Invalid type",
    move_cursor_to_end=True,
)

def get_type_validator(types):
    if not types:
        return _ALL_ALL_TYPES_VALIDATOR
    else:
        return prompt_toolkit.validation.Validator.from_callable(
        lambda text: text in types and text in ALL_TYPES,
        error_message="Invalid type",
        move_cursor_to_end=True,
    )

def _find_types(schema):
    if isinstance(schema, (list, tuple)):
        return itertools.chain(_find_types(s) for s in schema)
    type = schema.get("type")
    if type:
        return [type]
    types = []
    for key in ['allOf', 'anyOf', 'oneOf']:
        for subschema in schema.get(key, []):
            types.extend(_find_types(subschema))
    for key in ['not', 'if', 'then', 'else']:
        subschema = schema.get(key, {})
        types.extend(_find_types(subschema))
    return types

def prompt_type(prompt_text, types, indent=0, prompters=None):
    prompters = prompters or DEFAULT_PROMPTERS
    prompt_args = {
        "message": get_indent(indent) + prompt_text,
        "completer": get_type_completer(types),
        "validator": get_type_validator(types),
    }
    type = prompters.str(**prompt_args)
    return type

# def get_prompt_func(types, indent=0, prompters=None):
#     type = schema.get("type")
#     if not type:
#         types = _find_types(schema)
#         if len(types) == 1:
#             type = types[0]
#         else:
#             if not types:
#                 types = ALL_TYPES
#             type = prompt_type("Enter a type: ", types, indent=indent, prompters=prompters)

#     return type, PROMPT_FUNCS[type]

def prompt_from_types(prompt_text, types, indent=0, prompters=None):
    if isinstance(prompt_text, str):
        prompt_text = (prompt_text, prompt_text)
    if len(types) == 1:
        type = types[0]
        prompt_text = string.Template(prompt_text[0]).substitute({"type": type})
    else:
        type = prompt_type("Enter a type: ", ALL_TYPES, indent=indent, prompters=prompters)
        prompt_text = prompt_text[1]
    prompt_func = PROMPT_FUNCS[type]
    return prompt_func(prompt_text, {"type": type}, indent=indent, prompters=prompters)

def prompt_from_schema(prompt_text, schema, indent=0, prompters=None):
    if isinstance(prompt_text, str):
        prompt_text = (prompt_text, prompt_text)
    types = _find_types(schema)
    if len(types) == 1:
        type = types[0]
        prompt_text = string.Template(prompt_text[0]).substitute({"type": type})
    else:
        type = prompt_type("Enter a type: ", ALL_TYPES, indent=indent, prompters=prompters)
        prompt_text = prompt_text[1]
    prompt_func = PROMPT_FUNCS[type]
    return prompt_func(prompt_text, schema, indent=indent, prompters=prompters)
