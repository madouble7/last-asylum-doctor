"""Safe parser for the restricted ESM data modules used by the source site."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any


class ModuleParseError(ValueError):
    """Raised when a module does not match the supported data-only structure."""


_IDENTIFIER = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")
_NUMBER = re.compile(r"(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?")
_EXPORT_DEFAULT = re.compile(
    r"(?:^|,)\s*([A-Za-z_$][A-Za-z0-9_$]*)\s+as\s+default\s*(?:,|$)"
)


def parse_research_module(source: str) -> dict[str, Any]:
    """Parse a data-only Vite ESM chunk without executing JavaScript."""
    parser = _LiteralModuleParser(source)
    return parser.parse()


class _LiteralModuleParser:
    """Recursive-descent parser for declarations and JSON-like JS literals."""

    def __init__(self, source: str) -> None:
        self.source = source
        self.position = 0
        self.variables: dict[str, Any] = {}

    def parse(self) -> dict[str, Any]:
        self._skip_space()
        self._expect_word("var")

        while True:
            self._skip_space()
            name = self._parse_identifier()
            if name in self.variables:
                self._fail(f"duplicate variable {name!r}")
            self._skip_space()
            self._expect("=")
            self.variables[name] = self._parse_value(depth=0)
            self._skip_space()
            separator = self._peek()
            if separator == ",":
                self.position += 1
                continue
            if separator == ";":
                self.position += 1
                break
            self._fail("expected ',' or ';' after variable declaration")

        self._skip_space()
        self._expect_word("export")
        self._skip_space()
        self._expect("{")
        export_start = self.position
        export_end = self.source.find("}", export_start)
        if export_end < 0:
            self._fail("unterminated export block")
        export_body = self.source[export_start:export_end]
        self.position = export_end + 1
        self._skip_space()
        if self._peek() == ";":
            self.position += 1
        self._skip_space()
        if self.position != len(self.source):
            self._fail("unexpected executable content after export block")

        match = _EXPORT_DEFAULT.search(export_body)
        if match is None:
            raise ModuleParseError("Module does not export a default data object")
        default_name = match.group(1)
        value = self.variables.get(default_name)
        if not isinstance(value, dict):
            raise ModuleParseError("Default export is not an object literal")
        return deepcopy(value)

    def _parse_value(self, depth: int) -> Any:
        if depth > 100:
            self._fail("literal nesting is too deep")
        self._skip_space()
        character = self._peek()
        if character in {"'", '"', "`"}:
            return self._parse_string()
        if character == "[":
            return self._parse_array(depth + 1)
        if character == "{":
            return self._parse_object(depth + 1)
        if character == "-":
            self.position += 1
            value = self._parse_number()
            return -value
        if character.isdigit():
            return self._parse_number()
        if character and (character.isalpha() or character in {"_", "$"}):
            name = self._parse_identifier()
            if name == "true":
                return True
            if name == "false":
                return False
            if name == "null":
                return None
            if name not in self.variables:
                self._fail(f"unsupported or unknown identifier {name!r}")
            return self.variables[name]
        self._fail(f"unsupported value starting with {character!r}")

    def _parse_array(self, depth: int) -> list[Any]:
        result: list[Any] = []
        self._expect("[")
        self._skip_space()
        if self._peek() == "]":
            self.position += 1
            return result

        while True:
            result.append(self._parse_value(depth))
            self._skip_space()
            separator = self._peek()
            if separator == ",":
                self.position += 1
                self._skip_space()
                if self._peek() == "]":
                    self.position += 1
                    return result
                continue
            if separator == "]":
                self.position += 1
                return result
            self._fail("expected ',' or ']' in array")

    def _parse_object(self, depth: int) -> dict[str, Any]:
        result: dict[str, Any] = {}
        self._expect("{")
        self._skip_space()
        if self._peek() == "}":
            self.position += 1
            return result

        while True:
            self._skip_space()
            if self._peek() in {"'", '"', "`"}:
                key = self._parse_string()
            else:
                key = self._parse_identifier()
            if not isinstance(key, str):
                self._fail("object key must be text")
            if key in result:
                self._fail(f"duplicate object key {key!r}")

            self._skip_space()
            if self._peek() == ":":
                self.position += 1
                value = self._parse_value(depth)
            else:
                if key not in self.variables:
                    self._fail(f"unknown shorthand property {key!r}")
                value = self.variables[key]
            result[key] = value

            self._skip_space()
            separator = self._peek()
            if separator == ",":
                self.position += 1
                self._skip_space()
                if self._peek() == "}":
                    self.position += 1
                    return result
                continue
            if separator == "}":
                self.position += 1
                return result
            self._fail("expected ',' or '}' in object")

    def _parse_string(self) -> str:
        quote = self._peek()
        self.position += 1
        result: list[str] = []
        escapes = {
            "b": "\b",
            "f": "\f",
            "n": "\n",
            "r": "\r",
            "t": "\t",
            "v": "\v",
            "0": "\0",
            "\\": "\\",
            "/": "/",
            "'": "'",
            '"': '"',
            "`": "`",
        }

        while self.position < len(self.source):
            character = self.source[self.position]
            self.position += 1
            if character == quote:
                return "".join(result)
            if quote == "`" and character == "$" and self._peek() == "{":
                self._fail("template interpolation is not allowed")
            if character != "\\":
                result.append(character)
                continue

            if self.position >= len(self.source):
                self._fail("unterminated string escape")
            escaped = self.source[self.position]
            self.position += 1
            if escaped in escapes:
                result.append(escapes[escaped])
            elif escaped in {"u", "x"}:
                width = 4 if escaped == "u" else 2
                digits = self.source[self.position : self.position + width]
                if len(digits) != width or not all(
                    character in "0123456789abcdefABCDEF" for character in digits
                ):
                    self._fail("invalid hexadecimal string escape")
                result.append(chr(int(digits, 16)))
                self.position += width
            elif escaped in {"\n", "\r"}:
                if escaped == "\r" and self._peek() == "\n":
                    self.position += 1
            else:
                self._fail(f"unsupported string escape \\{escaped}")
        self._fail("unterminated string literal")

    def _parse_number(self) -> int | float:
        match = _NUMBER.match(self.source, self.position)
        if match is None:
            self._fail("invalid number")
        token = match.group(0)
        self.position = match.end()
        try:
            if "." in token or "e" in token.lower():
                value = float(token)
                return int(value) if value.is_integer() else value
            return int(token)
        except ValueError as error:
            self._fail(f"invalid number {token!r}", error)

    def _parse_identifier(self) -> str:
        match = _IDENTIFIER.match(self.source, self.position)
        if match is None:
            self._fail("expected identifier")
        self.position = match.end()
        return match.group(0)

    def _expect_word(self, word: str) -> None:
        if not self.source.startswith(word, self.position):
            self._fail(f"expected {word!r}")
        end = self.position + len(word)
        if end < len(self.source) and (
            self.source[end].isalnum() or self.source[end] in {"_", "$"}
        ):
            self._fail(f"expected standalone keyword {word!r}")
        self.position = end

    def _expect(self, expected: str) -> None:
        if self._peek() != expected:
            self._fail(f"expected {expected!r}")
        self.position += 1

    def _skip_space(self) -> None:
        while self.position < len(self.source) and self.source[
            self.position
        ].isspace():
            self.position += 1

    def _peek(self) -> str:
        if self.position >= len(self.source):
            return ""
        return self.source[self.position]

    def _fail(self, message: str, cause: Exception | None = None) -> None:
        error = ModuleParseError(f"{message} at character {self.position}")
        if cause is not None:
            raise error from cause
        raise error
