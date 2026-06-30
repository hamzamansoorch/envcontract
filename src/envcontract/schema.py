"""Load and validate the .env.schema contract itself.

The schema is YAML. It describes variables and their rules — never values.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

VarType = Literal["string", "int", "float", "bool", "url", "email", "enum"]


class SchemaError(Exception):
    """Raised when a .env.schema file is missing or malformed."""


class VariableRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: VarType = "string"
    required: bool = True
    secret: bool = False
    default: Optional[str] = None
    pattern: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None
    values: Optional[list[str]] = None
    description: Optional[str] = None

    @model_validator(mode="after")
    def _check_enum(self) -> "VariableRule":
        if self.type == "enum" and not self.values:
            raise ValueError("enum type requires a non-empty 'values' list")
        return self


class EnvSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = 1
    variables: dict[str, VariableRule] = Field(default_factory=dict)

    @classmethod
    def from_text(cls, text: str) -> "EnvSchema":
        try:
            data = yaml.safe_load(text) or {}
        except yaml.YAMLError as exc:
            raise SchemaError(f"invalid YAML in schema: {exc}") from exc
        if not isinstance(data, dict):
            raise SchemaError("schema root must be a mapping with a 'variables' key")
        try:
            return cls.model_validate(data)
        except ValidationError as exc:
            raise SchemaError(_format_validation_error(exc)) from exc

    @classmethod
    def from_file(cls, path: str | Path) -> "EnvSchema":
        p = Path(path)
        if not p.exists():
            raise SchemaError(
                f"schema file not found: {p}. Run `envcontract init` to create one from your .env."
            )
        return cls.from_text(p.read_text(encoding="utf-8"))


def _format_validation_error(exc: ValidationError) -> str:
    lines = ["schema is invalid:"]
    for err in exc.errors():
        loc = ".".join(str(p) for p in err["loc"])
        lines.append(f"  - {loc}: {err['msg']}")
    return "\n".join(lines)
