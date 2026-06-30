from envcontract.parser import parse_text


def test_basic_key_value():
    env = parse_text("FOO=bar\nBAZ=qux\n")
    assert env.as_dict() == {"FOO": "bar", "BAZ": "qux"}
    assert env.entries[0].line_no == 1
    assert env.entries[1].line_no == 2


def test_export_prefix_and_comments():
    env = parse_text("# a comment\nexport TOKEN=abc123\n\n  # indented comment\n")
    assert env.as_dict() == {"TOKEN": "abc123"}


def test_quotes_and_inline_comments():
    env = parse_text(
        'NAME="hello world"  \n'
        "PATH='/usr/local/bin'\n"
        "PORT=3000 # the dev port\n"
        'MSG="quoted # not a comment"\n'
    )
    d = env.as_dict()
    assert d["NAME"] == "hello world"
    assert d["PATH"] == "/usr/local/bin"
    assert d["PORT"] == "3000"
    assert d["MSG"] == "quoted # not a comment"


def test_escaped_newlines_in_double_quotes():
    env = parse_text('CERT="line1\\nline2"\n')
    assert env.as_dict()["CERT"] == "line1\nline2"


def test_duplicate_keys_last_wins_and_flagged():
    env = parse_text("A=1\nA=2\n")
    assert env.as_dict()["A"] == "2"
    assert env.duplicate_keys == ["A"]


def test_malformed_lines_recorded():
    env = parse_text("VALID=1\nNOPE\n=novalue\nbad key=1\n")
    assert env.as_dict() == {"VALID": "1"}
    assert len(env.errors) == 3
    messages = " ".join(e.message for e in env.errors)
    assert "missing '='" in messages
    assert "empty key" in messages
    assert "invalid key" in messages
