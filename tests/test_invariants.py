"""The two trust guarantees, enforced as tests.

1. envcontract opens no network sockets.
2. Secret values are never rendered in full.
"""

import socket

import pytest

from envcontract.report import render_json
from envcontract.secrets import mask
from envcontract.parser import parse_text
from envcontract.schema import EnvSchema
from envcontract.validators import validate


@pytest.fixture
def no_network(monkeypatch):
    def _blocked(*args, **kwargs):
        raise AssertionError("network access attempted — envcontract must stay 100% local")

    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)


def test_full_check_makes_no_network_calls(no_network):
    schema = EnvSchema.from_text(
        "variables:\n  API_KEY: { type: string, secret: true }\n  PORT: { type: int }\n"
    )
    env = parse_text("API_KEY=sk_live_abcdef123456\nPORT=notanint\n")
    findings = validate(env, schema)
    # Rendering JSON must also stay offline.
    render_json(findings)
    assert any(f.key == "PORT" for f in findings)


def test_mask_hides_the_middle():
    assert mask("sk_live_SUPERSECRET") == "sk******ET"
    assert mask("ab") == "****"
    assert mask("") == "(empty)"
