# Copyright 2022 Ben Kehoe
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import itertools
import dataclasses
from typing import List, Optional, Dict, Any
import textwrap

import jsonschema

from .types import SchemaType
from .context import Context
from .utils import ALL_JSON_TYPES
from .prompter import prompt_from_types, prompt_from_schema, PromptText
from .scalar_prompters import prompt_string


@dataclasses.dataclass
class _ObjectSchemaData:
    required_properties: List[str]
    all_properties: List[str]
    additional_properties: Any


def _get_object_schema_data(schema: SchemaType) -> _ObjectSchemaData:
    required_properties = schema.get("required", [])
    all_properties = required_properties + [
        p for p in schema.get("properties", {}) if p not in required_properties
    ]
    additional_properties = schema.get("additionalProperties", True)

    return _ObjectSchemaData(
        required_properties=required_properties,
        all_properties=all_properties,
        additional_properties=additional_properties,
    )


def _prompt_properties(
    *,
    object: Dict,
    schema: SchemaType,
    schema_data: _ObjectSchemaData,
    context: Context,
):
    required_properties = schema_data.required_properties
    other_properties = [
        p for p in schema_data.all_properties if p not in required_properties
    ]

    for property_name in required_properties:
        property_schema = schema.get("properties", {}).get(property_name, {})
        coda = " [REQUIRED]"

        prompt_text = PromptText(
            fixed_type=f"{property_name} [$type]{coda}: ",
            selected_type=f"{property_name}{coda}: ",
        )

        value = prompt_from_schema(
            prompt_text, property_schema, context=context.subcontext(property_name)
        )
        object[property_name] = value

    for property_name in other_properties:
        property_schema = schema.get("properties", {}).get(property_name, {})
        coda = " (CTRL-D to skip)"

        prompt_text = PromptText(
            fixed_type=f"{property_name} [$type]{coda}: ",
            selected_type=f"{property_name}{coda}: ",
        )

        try:
            value = prompt_from_schema(
                prompt_text, property_schema, context=context.subcontext(property_name)
            )
        except EOFError:
            continue
        object[property_name] = value


def _prompt_additional_properties(
    *,
    object: Dict,
    schema: SchemaType,
    schema_data: _ObjectSchemaData,
    context: Context,
):
    if not schema_data.additional_properties:
        return
    while True:
        try:
            property_name = prompt_string(
                "Enter a property name (CTRL+D to finish): ",
                {"type": "string"},
                context=context.with_indent(),
            )
        except EOFError:
            break
        if property_name in object:
            print(
                context.input_handler.with_indent().print(
                    "Property already exists", indent=True
                )
            )
            continue
        value = prompt_from_types(
            "Enter the property value: ",
            ALL_JSON_TYPES,
            context=context.subcontext(property_name),
        )
        object[property_name] = value


def prompt_object(prompt_text: str, schema: SchemaType, *, context: Context):
    validator = context.get_validator(schema)
    if prompt_text:
        context.input_handler.print(prompt_text, indent=True)

    schema_data = _get_object_schema_data(schema)

    while True:
        obj = {}

        _prompt_properties(
            object=obj, schema=schema, schema_data=schema_data, context=context
        )

        _prompt_additional_properties(
            object=obj, schema=schema, schema_data=schema_data, context=context
        )

        errors = [e.message for e in validator.iter_errors(obj)]
        if errors:
            indented_input_handler = context.input_handler.with_indent()
            indented_input_handler.print(
                "\n".join(errors), color="#ff0000", indent=True
            )
            indented_input_handler.print(
                "Object has been reset", color="#ff0000", indent=True
            )
        else:
            return obj
