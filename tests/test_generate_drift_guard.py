from envcontract.drift import compute_drift
from envcontract.generate import infer_type, render_schema_yaml
from envcontract.guard import scan_files
from envcontract.parser import parse_text
from envcontract.schema import EnvSchema


# ---- generate / init ----

def test_infer_type():
    assert infer_type("8080") == "int"
    assert infer_type("3.14") == "float"
    assert infer_type("true") == "bool"
    assert infer_type("https://x.io/y") == "url"
    assert infer_type("a@b.com") == "email"
    assert infer_type("hello world") == "string"


def test_render_schema_strips_values_and_flags_secrets():
    env = parse_text(
        "DATABASE_URL=postgres://localhost/db\n"
        "PORT=8080\n"
        "STRIPE_SECRET_KEY=sk_live_REALSECRET\n"
    )
    yaml_text = render_schema_yaml(env)
    # No real values leak into the schema.
    assert "sk_live_REALSECRET" not in yaml_text
    assert "postgres://localhost/db" not in yaml_text
    assert "8080" not in yaml_text
    # Secret key auto-flagged; types inferred.
    assert "STRIPE_SECRET_KEY:" in yaml_text
    assert "secret: true" in yaml_text
    schema = EnvSchema.from_text(yaml_text)  # round-trips into a valid schema
    assert schema.variables["PORT"].type == "int"
    assert schema.variables["STRIPE_SECRET_KEY"].secret is True


# ---- drift / diff ----

def test_compute_drift():
    schema = EnvSchema.from_text("variables:\n  A: {}\n  B: {}\n  C: {}\n")
    env = parse_text("A=1\nB=2\nZ=9\n")
    d = compute_drift(env, schema)
    assert d.missing_locally == ["C"]
    assert d.not_in_schema == ["Z"]
    assert set(d.in_sync) == {"A", "B"}
    assert d.has_drift is True


def test_no_drift():
    schema = EnvSchema.from_text("variables:\n  A: {}\n")
    assert compute_drift(parse_text("A=1\n"), schema).has_drift is False


# ---- guard ----

def test_guard_blocks_real_secret(tmp_path):
    schema = EnvSchema.from_text("variables:\n  API_KEY: { secret: true }\n")
    f = tmp_path / ".env"
    f.write_text("API_KEY=sk_live_abcdef123456\nPORT=8080\n")
    violations = scan_files([str(f)], schema)
    assert len(violations) == 1
    assert violations[0].key == "API_KEY"


def test_guard_ignores_placeholders(tmp_path):
    schema = EnvSchema.from_text("variables:\n  API_KEY: { secret: true }\n")
    f = tmp_path / ".env.example"
    f.write_text("API_KEY=changeme\n")
    assert scan_files([str(f)], schema) == []


def test_guard_catches_secretish_key_without_schema(tmp_path):
    # Even with no schema, a key that looks secret + real value is flagged.
    f = tmp_path / ".env"
    f.write_text("AWS_SECRET_ACCESS_KEY=AKIAREALLOOKINGSECRET123\n")
    violations = scan_files([str(f)], None)
    assert len(violations) == 1


def test_guard_never_exposes_value(tmp_path):
    schema = EnvSchema.from_text("variables:\n  TOKEN: { secret: true }\n")
    secret = "ghp_SUPERSECRETTOKENVALUE"
    f = tmp_path / ".env"
    f.write_text(f"TOKEN={secret}\n")
    for v in scan_files([str(f)], schema):
        assert secret not in (v.key + (str(v.line_no) or "") + v.file)
