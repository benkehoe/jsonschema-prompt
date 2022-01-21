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

import dataclasses
import itertools
from typing import Callable, Mapping, Union, Any

import jsonschema

from .input import InputHandler
from jsonpointer import JsonPointer


def _validator_factory(schema):
    return jsonschema.Draft7Validator(
        schema, format_checker=jsonschema.draft7_format_checker
    )


@dataclasses.dataclass(frozen=True)
class Context:
    input_handler: InputHandler
    values: Mapping[JsonPointer, Any] = None
    path: JsonPointer = JsonPointer("")

    def __post_init__(self):
        values = {}
        if self.values:
            for key, value in self.values.items():
                if not isinstance(key, JsonPointer):
                    key = JsonPointer(key)
                values[key] = value
        object.__setattr__(self, "values", values)

    def subcontext(self, element: Union[str, int], *, indent: bool = True) -> "Context":
        new_parts = self.path.get_parts() + [element]
        subcontext = dataclasses.replace(self, path=JsonPointer.from_parts(new_parts))
        if indent:
            subcontext = dataclasses.replace(
                subcontext, input_handler=self.input_handler.with_indent()
            )
        return subcontext

    def with_indent(self) -> "Context":
        return dataclasses.replace(self, input_handler=self.input_handler.with_indent())

    def get_path_str(self) -> str:
        return repr(self.path.path)

    def has_value(self) -> bool:
        return self.path in self.values

    def get_value(self) -> Any:
        return self.values[self.path]

    def get_prompter(self, type: str) -> Callable:
        from . import scalar_prompters, array_prompter, object_prompter

        PROMPT_FUNCS = {
            "array": array_prompter.prompt_array,
            "boolean": scalar_prompters.prompt_boolean,
            "integer": scalar_prompters.prompt_number,
            "null": scalar_prompters.prompt_null,
            "number": scalar_prompters.prompt_number,
            "object": object_prompter.prompt_object,
            "string": scalar_prompters.prompt_string,
        }
        return PROMPT_FUNCS[type]

    def get_type_prompter(self):
        from . import scalar_prompters

        return scalar_prompters.prompt_type

    def get_validator_factory(self):
        return _validator_factory

    def get_validator(self, schema):
        return jsonschema.Draft7Validator(
            schema, format_checker=jsonschema.draft7_format_checker
        )

    def validate(self, schema, data):
        return self.get_validator(schema).validate(data)
