import json
import pytest
from colab_mcp.tools._runner import (
    OUTPUT_START, OUTPUT_END, extract_delimited, wrap_output, run_python,
)


def test_wrap_output_surrounds_body_with_delimiters():
    code = wrap_output('print(json.dumps({"a": 1}))')
    assert OUTPUT_START in code
    assert OUTPUT_END in code
    compile(code, "<gen>", "exec")  # must be valid Python


def test_extract_delimited_pulls_inner_payload():
    raw = f"noise\n{OUTPUT_START}\n{{\"a\": 1}}\n{OUTPUT_END}\nmore noise"
    assert json.loads(extract_delimited(raw)) == {"a": 1}


def test_extract_delimited_fallback_on_missing_markers():
    assert extract_delimited("  bare  ") == "bare"


@pytest.mark.anyio
async def test_run_python_returns_parsed_payload(fake_session):
    session = fake_session(canned=f"{OUTPUT_START}\n{{\"ok\": true}}\n{OUTPUT_END}")
    result = await run_python(session, 'print("x")')
    assert result == {"ok": True}
    assert session.client.calls[0][0] == "execute_code"


@pytest.fixture
def anyio_backend():
    return "asyncio"
