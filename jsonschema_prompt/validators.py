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

import json
import sys
import collections
import itertools
import string
from dataclasses import dataclass
from typing import Callable

import jsonschema

from prompt_toolkit.validation import Validator, ValidationError

from .utils import ALL_JSON_TYPES


class JSONSchemaValidator(Validator):
    def __init__(self, schema, *, validator_factory):
        self.schema = schema
        self.validator = validator_factory(self.schema)

    def get_json(self, document):
        try:
            return json.loads(document.text)
        except json.JSONDecodeError as e:
            raise ValidationError(message=str(e))

    def validate(self, document):
        obj = self.get_json(document)
        errors = [e.message for e in self.validator.iter_errors(obj)]
        if errors:
            raise ValidationError(message="\n".join(errors))


class StringJSONSchemaValidator(JSONSchemaValidator):
    def get_json(self, document):
        return document.text


_ANY_TYPE_VALIDATOR = Validator.from_callable(
    lambda text: text in ALL_JSON_TYPES,
    error_message="Invalid type",
    move_cursor_to_end=True,
)


def get_type_validator(types) -> Validator:
    if not types:
        return _ANY_TYPE_VALIDATOR
    else:
        return Validator.from_callable(
            lambda text: text in types and text in ALL_JSON_TYPES,
            error_message=f"Type must be one of: {', '.join(types)}",
            move_cursor_to_end=True,
        )
