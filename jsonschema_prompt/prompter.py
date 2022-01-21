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

import string
from typing import List, Union, Optional, Any
import dataclasses

from .types import SchemaType
from .utils import ALL_JSON_TYPES, find_types_in_schema
from .context import Context
from .exceptions import SetValueError


@dataclasses.dataclass(frozen=True)
class PromptText:
    selected_type: str
    fixed_type: str
    type_prompt_text: Optional[str] = None

    @classmethod
    def get_selected_type_prompt_text(
        cls, prompt_text: Optional[Union["PromptText", str]], type: str
    ) -> str:
        if not prompt_text:
            return ""
        if isinstance(prompt_text, cls):
            prompt_text = prompt_text.selected_type
        return prompt_text

    @classmethod
    def get_fixed_type_prompt_text(
        cls, prompt_text: Optional[Union["PromptText", str]], type: str
    ) -> str:
        if not prompt_text:
            return ""
        if isinstance(prompt_text, cls):
            prompt_text = prompt_text.fixed_type
        return string.Template(prompt_text).substitute({"type": type})

    @classmethod
    def get_type_prompt_text(cls, prompt_text: Optional[Union["PromptText", str]]) -> str:
        if isinstance(prompt_text, cls):
            return prompt_text.type_prompt_text or "Enter a type: "
        else:
            return "Enter a type: "


def prompt_from_types(
    prompt_text: Union[str, PromptText], types: List[str], *, context: Context
) -> Any:
    if context.has_value():
        value = context.get_value()
        context.input_handler.print(
            f"At path {context.get_path_str()} using value {value}", indent=True
        )
        return value
    if len(types) == 1:
        type = types[0]
        prompt_text = PromptText.get_fixed_type_prompt_text(prompt_text, type)
    else:
        type_prompter = context.get_type_prompter()
        type_prompt_text = PromptText.get_type_prompt_text(prompt_text)
        type = type_prompter(type_prompt_text, types, context=context)
        prompt_text = PromptText.get_selected_type_prompt_text(prompt_text, type)
    prompter = context.get_prompter(type)
    return prompter(prompt_text, {"type": type}, context=context)


def prompt_from_schema(
    prompt_text: str, schema: SchemaType, *, context: Context
) -> Any:
    if context.has_value():
        value = context.get_value()
        validator = context.get_validator(schema)
        errors = [e.message for e in validator.iter_errors(value)]
        if errors:
            raise SetValueError(context.path, value, "\n".join(errors))
        context.input_handler.print(
            f"At path {context.get_path_str()} using value {value}", indent=True
        )
        return value
    if "$comment" in schema:
        context.input_handler.print_instructions(schema["$comment"])
    types = find_types_in_schema(schema)
    if len(types) == 1:
        type = types[0]
        prompt_text = PromptText.get_fixed_type_prompt_text(prompt_text, type)
    else:
        type_prompter = context.get_type_prompter()
        type_prompt_text = PromptText.get_type_prompt_text(prompt_text)
        type = type_prompter(type_prompt_text, types, context=context)
        prompt_text = PromptText.get_selected_type_prompt_text(prompt_text, type)
    prompter = context.get_prompter(type)
    return prompter(prompt_text, schema, context=context)
