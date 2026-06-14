# tests/test_local_mlx.py
import json
import os

from colab_mcp.tools.local_mlx import _normalize_tokenizer_config


def _write_cfg(tmp_path, data):
    p = tmp_path / "tokenizer_config.json"
    p.write_text(json.dumps(data))
    return str(tmp_path)


def test_normalize_rewrites_backend_and_drops_keys(tmp_path):
    d = _write_cfg(tmp_path, {
        "tokenizer_class": "TokenizersBackend",
        "backend": "x", "is_local": True, "from_slow": False, "keep": 1,
    })
    res = _normalize_tokenizer_config(d)
    assert res["changed"] == ["tokenizer_class", "backend", "is_local", "from_slow"]
    cfg = json.loads(open(os.path.join(d, "tokenizer_config.json")).read())
    assert cfg["tokenizer_class"] == "PreTrainedTokenizerFast"
    assert "backend" not in cfg and "is_local" not in cfg and "from_slow" not in cfg
    assert cfg["keep"] == 1


def test_normalize_is_idempotent_and_noops_when_clean(tmp_path):
    d = _write_cfg(tmp_path, {"tokenizer_class": "PreTrainedTokenizerFast"})
    res = _normalize_tokenizer_config(d)
    assert res["changed"] == []


def test_normalize_missing_file_returns_error(tmp_path):
    res = _normalize_tokenizer_config(str(tmp_path))
    assert "error" in res
