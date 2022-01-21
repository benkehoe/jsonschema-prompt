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

from typing import Optional, List

from .types import SchemaType
from .context import Context
from .utils import get_type_completer, multiline_continuation
from .validators import (
    get_type_validator,
    JSONSchemaValidator,
    StringJSONSchemaValidator,
)


def _check_const(schema):
    if "const" in schema:
        return True, schema["const"]
    if "enum" in schema and len(schema["enum"] == 1):
        return True, schema["enum"][0]
    return False, None


def prompt_type(
    prompt_text: str, types: Optional[List[str]], *, context: Context
) -> str:
    type = context.input_handler.get_string(
        message=prompt_text,
        validator=get_type_validator(types),
        completer=get_type_completer(types),
    )
    return type


def prompt_string(prompt_text: str, schema: SchemaType, *, context: Context) -> str:
    has_const, const_value = _check_const(schema)
    if has_const:
        return const_value
    validator = StringJSONSchemaValidator(
        schema, validator_factory=context.get_validator_factory()
    )
    kwargs = {}
    if schema.get("multiline", False) is True:
        kwargs["multiline"] = True
        kwargs["prompt_continuation"] = multiline_continuation
    if "default" in schema:
        if schema["default"] is None:
            kwargs["default_is_none"] = True
        else:
            kwargs["default"] = schema["default"]
    return context.input_handler.get_string(
        message=prompt_text, validator=validator, validate_while_typing=False, **kwargs
    )


def prompt_number(prompt_text: str, schema: SchemaType, *, context: Context) -> float:
    has_const, const_value = _check_const(schema)
    if has_const:
        return const_value
    validator = JSONSchemaValidator(
        schema, validator_factory=context.get_validator_factory()
    )
    kwargs = {}
    if isinstance(schema.get("default"), float):
        kwargs["default"] = schema["default"]
    return context.input_handler.get_number(
        message=prompt_text, validator=validator, validate_while_typing=False, **kwargs
    )


def prompt_boolean(prompt_text: str, schema: SchemaType, *, context: Context) -> bool:
    has_const, const_value = _check_const(schema)
    if has_const:
        return const_value
    kwargs = {}
    return context.input_handler.get_boolean(message=prompt_text, **kwargs)


def prompt_null(prompt_text: str, schema: SchemaType, *, context: Context) -> None:
    return None
