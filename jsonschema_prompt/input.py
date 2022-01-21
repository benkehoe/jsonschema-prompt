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

from email.policy import default
import dataclasses
from typing import Callable, Any, Optional
import textwrap

import prompt_toolkit
from prompt_toolkit.validation import Validator

PromptContinuationType = Callable[[int, int, int], str]


def colored_text(color, text):
    return prompt_toolkit.formatted_text.FormattedText([(color, text)])


@dataclasses.dataclass(frozen=True)
class InputHandler:
    str_handler: Callable
    bool_handler: Callable
    print_handler: Callable[[str], Any]
    indent: int = 0
    indent_width: int = 2

    def with_indent(self, amount=1) -> "InputHandler":
        return dataclasses.replace(self, indent=self.indent + amount)

    def get_indented_str(self, s: str) -> str:
        indent_str = " " * self.indent * self.indent_width
        return textwrap.indent(s, indent_str)

    def print_instructions(self, instructions: str) -> str:
        initial_indent_str = " " * self.indent * self.indent_width
        subsequent_indent_str = " " * (self.indent + 1) * self.indent_width
        wrapped_instructions = textwrap.fill(
            instructions,
            initial_indent=initial_indent_str,
            subsequent_indent=subsequent_indent_str,
        )
        self.print_handler(wrapped_instructions)

    def get_string(
        self,
        message: str,
        *,
        validator: Validator,
        completer: Optional[Callable] = None,
        validate_while_typing: Optional[bool] = None,
        multiline: Optional[bool] = None,
        prompt_continuation: Optional[PromptContinuationType] = None,
        default: Optional[Any] = None,
        default_is_none: bool = False,
    ):
        kwargs = {
            "message": self.get_indented_str(message),
            "validator": validator,
        }
        if completer:
            kwargs["completer"] = completer
        if validate_while_typing is not None:
            kwargs["validate_while_typing"] = validate_while_typing
        if multiline is not None:
            kwargs["multiline"] = multiline
        if prompt_continuation:
            kwargs["prompt_continuation"] = prompt_continuation
        if default_is_none:
            kwargs["default"] = None
        elif default is not None:
            kwargs["default"] = str(default)
        return self.str_handler(**kwargs)

    def get_number(
        self,
        message: str,
        *,
        validator: Validator,
        validate_while_typing: Optional[bool] = None,
        default: Optional[Any] = None,
    ):
        return float(
            self.get_string(
                message=message,
                validator=validator,
                validate_while_typing=validate_while_typing,
                default=default,
            )
        )

    def get_boolean(self, message: str):
        return self.bool_handler(message=self.get_indented_str(message))

    def print(self, message: Any, *, indent: bool, color: str = None):
        if indent:
            message = self.get_indented_str(str(message))
        else:
            message = str(message)
        if color:
            message = colored_text(color, message)
        return self.print_handler(message)


DEFAULT_INPUT_HANDLER = InputHandler(
    str_handler=prompt_toolkit.shortcuts.prompt,
    bool_handler=prompt_toolkit.shortcuts.confirm,
    print_handler=prompt_toolkit.shortcuts.print_formatted_text,
)
