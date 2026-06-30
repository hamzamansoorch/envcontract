import pytest

from envcontract.schema import EnvSchema, SchemaError

VALID = """
version: 1
variables:
  DATABASE_URL:
    type: url
    required: true
    secret: true
  PORT:
    type: int
    default: "3000"
    min: 1
    max: 65535
  LOG_LEVEL:
    type: enum
    values: [debug, info, warn, error]
    default: info
"""


def test_loads_valid_schema():
    schema = EnvSchema.from_text(VALID)
    assert schema.version == 1
    assert schema.variables["DATABASE_URL"].secret is True
    assert schema.variables["PORT"].type == "int"
    assert schema.variables["LOG_LEVEL"].values == ["debug", "info", "warn", "error"]


def test_enum_without_values_is_rejected():
    bad = "variables:\n  X:\n    type: enum\n"
    with pytest.raises(SchemaError):
        EnvSchema.from_text(bad)


def test_unknown_field_is_rejected():
    bad = "variables:\n  X:\n    typ: string\n"  # typo: 'typ'
    with pytest.raises(SchemaError):
        EnvSchema.from_text(bad)


def test_missing_file_gives_helpful_error():
    with pytest.raises(SchemaError) as exc:
        EnvSchema.from_file("/nonexistent/.env.schema")
    assert "envcontract init" in str(exc.value)


def test_invalid_yaml():
    with pytest.raises(SchemaError):
        EnvSchema.from_text("variables: [unclosed\n")
