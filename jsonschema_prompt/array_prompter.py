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
from typing import List, Optional
import textwrap

import jsonschema

from .types import SchemaType
from .context import Context
from .utils import find_types_in_schema, ALL_JSON_TYPES
from .prompter import prompt_from_types, prompt_from_schema, PromptText


@dataclasses.dataclass
class _AdditionalItemsData:
    allowed: bool
    schema: SchemaType
    types: List[str]


@dataclasses.dataclass(frozen=True)
class _ArraySchemaData:
    min_items: Optional[int]
    max_items: Optional[int]
    indexed_items: Optional[List[SchemaType]]
    additional_items: _AdditionalItemsData


def _get_additional_items_data(schema: SchemaType, default_allowed: bool):
    if "additionalItems" not in schema:
        return _AdditionalItemsData(
            allowed=default_allowed, schema={}, types=ALL_JSON_TYPES
        )
    additional_items = schema["additionalItems"]
    if isinstance(additional_items, dict):
        # print("add'l items is a schema")
        # add'l items is a schema
        return _AdditionalItemsData(
            allowed=True,
            schema=additional_items,
            types=find_types_in_schema(additional_items),
        )
    else:
        # print("add'l items bool")
        # add'l items set to a boolean
        assert isinstance(additional_items, bool)
        return _AdditionalItemsData(
            allowed=additional_items, schema={}, types=ALL_JSON_TYPES
        )


def _get_array_schema_data(schema):
    min_items = schema.get("minItems")
    max_items = schema.get("maxItems")
    if "items" not in schema:
        return _ArraySchemaData(
            min_items=min_items,
            max_items=max_items,
            indexed_items=[],
            additional_items=_get_additional_items_data(schema, default_allowed=True),
        )
    items = schema["items"]
    if not isinstance(items, list):
        # print("items is a schema")
        # items is a single schema, becomes add'l items
        return _ArraySchemaData(
            min_items=min_items,
            max_items=max_items,
            indexed_items=[],
            additional_items=_AdditionalItemsData(
                allowed=True, schema=items, types=find_types_in_schema(items)
            ),
        )

    return _ArraySchemaData(
        min_items=min_items,
        max_items=max_items,
        indexed_items=items,
        additional_items=_get_additional_items_data(schema, default_allowed=False),
    )


class _BreakLoop(Exception):
    pass


def _do_loop(*, index: int, data: _ArraySchemaData, context: Context):
    over_min_length = data.min_items is None or index >= data.min_items
    over_max_length = data.max_items is not None and index >= data.max_items
    if index < len(data.indexed_items):
        item_schema = data.indexed_items[index]
        prompt_text = PromptText(
            fixed_type=f"Enter a value [$type]: ",
            selected_type=f"Enter a value: ",
        )
        return prompt_from_schema(
            prompt_text, item_schema, context=context.subcontext(index)
        )
    elif over_max_length or not data.additional_items.allowed:
        raise _BreakLoop
    else:
        item_schema = data.additional_items.schema
        end_text = " (CTRL+D to finish)" if over_min_length else ""
        prompt_text = PromptText(
            fixed_type=f"Enter a value [$type]{end_text}: ",
            selected_type=f"Enter a value: ",
            type_prompt_text=f"Enter a type{end_text}: ",
        )
        try:
            return prompt_from_schema(
                prompt_text,
                schema=item_schema,
                context=context.subcontext(index),
            )
        except EOFError:
            raise _BreakLoop


def prompt_array(prompt_text, schema: SchemaType, *, context: Context):
    validator = context.get_validator(schema)

    array_schema_data = _get_array_schema_data(schema)

    if prompt_text:
        context.input_handler.print(prompt_text, indent=True)

    while True:
        array = []
        for index in itertools.count():
            try:
                value = _do_loop(index=index, data=array_schema_data, context=context)
                array.append(value)
            except _BreakLoop:
                break

        errors = [e.message for e in validator.iter_errors(array)]
        if errors:
            indented_input_handler = context.input_handler.with_indent()
            indented_input_handler.print(
                "\n".join(errors), color="#ff0000", indent=True
            )
            indented_input_handler.print(
                "Array has been reset", color="#ff0000", indent=True
            )
        else:
            return array
