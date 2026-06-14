# tests/test_roundtrip.py
from colab_mcp.tools.roundtrip import _gen_save_push_code, _gen_ensure_readme_code


def test_save_push_code_is_valid_and_uses_safe_patterns():
    code = _gen_save_push_code("model", "tok", "user/repo", "merged_16bit", True)
    compile(code, "<gen>", "exec")
    # uses save_pretrained_merged (not the silent push_to_hub_merged)
    assert "save_pretrained_merged" in code
    assert "push_to_hub_merged" not in code
    # token via get_token() fallback, never userdata in a subprocess
    assert "get_token" in code
    assert "userdata" not in code
    # verifies a safetensors was produced
    assert ".safetensors" in code
    # clears stale files when clear_repo
    assert "delete_patterns" in code
    assert "['*']" in code
    # interpolates the variable names and repo id literally
    assert "user/repo" in code
    assert "'merged_16bit'" in code


def test_save_push_code_no_clear_omits_glob_delete():
    code = _gen_save_push_code("m", "t", "u/r", "merged_4bit", False)
    compile(code, "<gen>", "exec")
    assert "_dp = ['*'] if False else None" in code


def test_ensure_readme_code_is_valid_and_uploads_when_missing():
    code = _gen_ensure_readme_code("user/repo", None)
    compile(code, "<gen>", "exec")
    assert "get_token" in code
    assert "upload_file" in code
    assert "README.md" in code
    assert "user/repo" in code


def test_ensure_readme_custom_content_is_embedded():
    code = _gen_ensure_readme_code("u/r", "# Custom\n")
    compile(code, "<gen>", "exec")
    assert "# Custom" in code
