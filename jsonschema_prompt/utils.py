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

import prompt_toolkit

from .input import InputHandler

ALL_JSON_TYPES = [
    "array",
    "boolean",
    "integer",
    "null",
    "number",
    "object",
    "string",
]


def multiline_continuation(width: int, line_number: int, is_soft_wrap: bool):
    return "." * width


def find_types_in_schema(schema):
    if not schema:
        return ()
    if isinstance(schema, (list, tuple)):
        return list(itertools.chain(find_types_in_schema(s) for s in schema))
    if "type" in schema:
        if isinstance(schema["type"], str):
            return [schema["type"]]
        return schema["type"]

    types = set()
    if "allOf" in schema:
        for subschema in schema["allOf"]:
            types.update(find_types_in_schema(subschema))
    # TODO: determine the semantics for types found within oneOf, anyOf, if/then/else
    return list(types)


_ANY_TYPE_COMPLETER = prompt_toolkit.completion.WordCompleter(
    ALL_JSON_TYPES, ignore_case=True
)


def get_type_completer(types):
    if not types:
        return _ANY_TYPE_COMPLETER
    else:
        return prompt_toolkit.completion.WordCompleter(types, ignore_case=True)
