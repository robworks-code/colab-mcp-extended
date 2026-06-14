# tests/test_roundtrip.py
import asyncio
import json

from colab_mcp.session_manager import SessionManager
from colab_mcp.tools.roundtrip import _gen_save_push_code, _gen_ensure_readme_code, get_roundtrip_tools


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


def _tool(group, name):
    return next(t for t in group if t.name == name)


def test_save_push_code_includes_var_names():
    code = _gen_save_push_code("mymodel", "mytok", "u/r", "merged_16bit", True)
    assert "mymodel.save_pretrained_merged" in code
    assert "mytok," in code


def test_save_push_no_safetensors_branch_present():
    code = _gen_save_push_code("m", "t", "u/r", "merged_16bit", True)
    assert "no .safetensors produced" in code


def test_ensure_readme_uses_file_exists():
    code = _gen_ensure_readme_code("u/r", None)
    compile(code, "<gen>", "exec")
    assert "file_exists" in code
    assert "hf_hub_download" not in code


def test_save_and_push_rejects_bad_var_name():
    sm = SessionManager(default_browser_profile=None)
    fn = _tool(get_roundtrip_tools(sm), "save_and_push_merged").fn
    out = json.loads(asyncio.run(fn(model_var="x; import os", tokenizer_var="t", repo_id="u/r")))
    assert "error" in out and "invalid kernel variable name" in out["error"]
