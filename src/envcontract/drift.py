"""Compute drift between a local .env and the committed schema.

Answers the "a teammate added a var and didn't tell anyone" problem.
"""

from __future__ import annotations

from dataclasses import dataclass

from .parser import ParsedEnv
from .schema import EnvSchema


@dataclass
class Drift:
    missing_locally: list[str]   # declared in schema, absent from local .env
    not_in_schema: list[str]     # present locally, not declared in schema
    in_sync: list[str]           # present in both

    @property
    def has_drift(self) -> bool:
        return bool(self.missing_locally or self.not_in_schema)


def compute_drift(parsed: ParsedEnv, schema: EnvSchema) -> Drift:
    env_keys = list(parsed.as_dict().keys())
    schema_keys = list(schema.variables.keys())
    env_set, schema_set = set(env_keys), set(schema_keys)

    missing_locally = [k for k in schema_keys if k not in env_set]
    not_in_schema = [k for k in env_keys if k not in schema_set]
    in_sync = [k for k in schema_keys if k in env_set]
    return Drift(missing_locally, not_in_schema, in_sync)
