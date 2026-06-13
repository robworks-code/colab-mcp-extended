from colab_mcp.tools.secrets import _gen_inject_code, _gen_get_secret_code
from colab_mcp.tools.secrets import _validate_env_var


def test_validate_env_var_blocks_loaders():
    assert _validate_env_var("LD_PRELOAD")
    assert _validate_env_var("PATH")
    assert _validate_env_var("")
    assert _validate_env_var("HF_TOKEN") is None


def test_inject_code_sets_env_without_printing_value():
    code = _gen_inject_code("HF_TOKEN", "HF_TOKEN")
    compile(code, "<gen>", "exec")
    assert "userdata.get" in code
    assert "os.environ" in code
    assert "'set': True" in code or '"set": True' in code


def test_inject_code_quotes_names():
    code = _gen_inject_code("My Secret", "MY_ENV")
    assert "'My Secret'" in code
    assert "'MY_ENV'" in code


def test_get_secret_code_returns_value():
    code = _gen_get_secret_code("API_KEY")
    compile(code, "<gen>", "exec")
    assert "userdata.get" in code
    assert "'API_KEY'" in code
