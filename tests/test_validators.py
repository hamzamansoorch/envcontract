from envcontract.parser import parse_text
from envcontract.schema import EnvSchema
from envcontract.validators import Severity, has_errors, validate

SCHEMA = EnvSchema.from_text(
    """
    variables:
      DATABASE_URL: { type: url, required: true, secret: true }
      PORT: { type: int, min: 1, max: 65535, default: "3000" }
      LOG_LEVEL: { type: enum, values: [debug, info, warn, error] }
      STRIPE_KEY: { type: string, secret: true, pattern: "^sk_(test|live)_" }
      DEBUG: { type: bool, required: false }
    """
)


def _keys_with_errors(findings):
    return {f.key for f in findings if f.severity is Severity.ERROR}


def test_all_valid():
    env = parse_text(
        "DATABASE_URL=postgres://localhost:5432/db\n"
        "PORT=8080\n"
        "LOG_LEVEL=info\n"
        "STRIPE_KEY=sk_test_abc\n"
        "DEBUG=true\n"
    )
    findings = validate(env, SCHEMA)
    assert not has_errors(findings)


def test_missing_required():
    env = parse_text("PORT=8080\nLOG_LEVEL=info\nSTRIPE_KEY=sk_test_x\n")
    assert "DATABASE_URL" in _keys_with_errors(validate(env, SCHEMA))


def test_required_with_default_not_flagged():
    # PORT has a default, so its absence is not an error.
    env = parse_text("DATABASE_URL=https://x.io\nLOG_LEVEL=info\nSTRIPE_KEY=sk_live_y\n")
    assert "PORT" not in _keys_with_errors(validate(env, SCHEMA))


def test_type_and_range_and_enum_and_pattern():
    env = parse_text(
        "DATABASE_URL=not-a-url\n"
        "PORT=99999\n"
        "LOG_LEVEL=verbose\n"
        "STRIPE_KEY=pk_live_wrong\n"
    )
    errs = _keys_with_errors(validate(env, SCHEMA))
    assert {"DATABASE_URL", "PORT", "LOG_LEVEL", "STRIPE_KEY"} <= errs


def test_unknown_key_is_warning_not_error():
    env = parse_text(
        "DATABASE_URL=https://x.io\nLOG_LEVEL=info\nSTRIPE_KEY=sk_test_z\nEXTRA=1\n"
    )
    findings = validate(env, SCHEMA)
    extra = [f for f in findings if f.key == "EXTRA"]
    assert extra and extra[0].severity is Severity.WARNING
    assert not has_errors([f for f in findings if f.key == "EXTRA"])


def test_secret_value_never_in_findings():
    secret = "sk_live_SUPERSECRETVALUE123"
    env = parse_text(f"DATABASE_URL=bad\nLOG_LEVEL=info\nSTRIPE_KEY={secret}\n")
    # STRIPE_KEY is valid here; ensure no finding message leaks any raw secret.
    for f in validate(env, SCHEMA):
        assert secret not in f.message
