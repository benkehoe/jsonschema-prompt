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

import typing

import jsonpointer

from . import prompter, context, utils, input, types
from .exceptions import SetValueError


def prompt(
    schema: types.SchemaType, *, prompt_text: typing.Optional[str]=None, set_values: typing.Mapping = None
) -> typing.Any:
    default_context = context.Context(
        input_handler=input.DEFAULT_INPUT_HANDLER, values=set_values
    )
    result = prompter.prompt_from_schema(prompt_text, schema, context=default_context)
    for path, value in default_context.values.items():
        try:
            result_value = path.get(result)
            if isinstance(result_value, jsonpointer.EndOfList):
                path.set(result, value)
            elif result_value != value:
                raise SetValueError(
                    path, value, f"Mismatch with existing value {result_value!r}"
                )
        except jsonpointer.JsonPointerException:
            try:
                path.set(result, value)
            except jsonpointer.JsonPointerException as e:
                raise SetValueError(path, value, str(e))
    return result
