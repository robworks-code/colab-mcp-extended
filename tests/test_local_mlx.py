# tests/test_local_mlx.py
import asyncio
import json
import os
import subprocess

import colab_mcp.tools.local_mlx as lm
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
    with open(os.path.join(d, "tokenizer_config.json"), encoding="utf-8") as f:
        cfg = json.load(f)
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


class _Proc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _tool(group, name):
    return next(t for t in group if t.name == name)


def test_get_local_mlx_tools_yields_three():
    names = {t.name for t in lm.get_local_mlx_tools("/usr/bin/python3")}
    assert names == {"normalize_tokenizer_config", "download_from_hf", "convert_to_mlx"}


def test_convert_builds_argv_and_clears_dir(tmp_path, monkeypatch):
    captured = {}

    def fake_run(argv, capture_output, text):
        captured["argv"] = argv
        return _Proc(returncode=0, stdout="done")

    monkeypatch.setattr(subprocess, "run", fake_run)
    src = tmp_path / "src"
    src.mkdir()
    (src / "tokenizer_config.json").write_text('{"tokenizer_class": "TokenizersBackend"}')
    mlx = tmp_path / "mlx"
    mlx.mkdir()
    (mlx / "stale").write_text("x")

    fn = _tool(lm.get_local_mlx_tools("/PY"), "convert_to_mlx").fn
    out = json.loads(asyncio.run(fn(source=str(src), mlx_path=str(mlx), quantize=True, q_bits=8)))

    assert out["status"] == "ok"
    assert out["normalized"]["changed"] == ["tokenizer_class"]
    assert not (mlx / "stale").exists()  # cleared
    argv = captured["argv"]
    assert argv[0] == "/PY"
    assert argv[1:5] == ["-m", "mlx_lm.convert", "--hf-path", str(src)]
    assert "--mlx-path" in argv and str(mlx) in argv
    assert "-q" in argv and "--q-bits" in argv and "8" in argv


def test_convert_surfaces_sentencepiece_hint(tmp_path, monkeypatch):
    def fake_run(argv, capture_output, text):
        return _Proc(returncode=1, stderr="ModuleNotFoundError: No module named 'sentencepiece'")

    monkeypatch.setattr(subprocess, "run", fake_run)
    fn = _tool(lm.get_local_mlx_tools("/PY"), "convert_to_mlx").fn
    out = json.loads(asyncio.run(fn(source="org/repo", mlx_path=str(tmp_path / "out"))))
    assert "error" in out
    assert "sentencepiece" in out["hint"]


def test_download_parses_last_json_line(monkeypatch):
    def fake_run(argv, capture_output, text):
        assert argv[0] == "/PY" and argv[1] == "-c"
        return _Proc(returncode=0, stdout='noise\n{"path": "/d", "files": ["a"]}')

    monkeypatch.setattr(subprocess, "run", fake_run)
    fn = _tool(lm.get_local_mlx_tools("/PY"), "download_from_hf").fn
    out = json.loads(asyncio.run(fn(repo_id="org/repo", local_dir="/d")))
    assert out["path"] == "/d" and out["files"] == ["a"]


def test_parse_last_json_falls_back_to_raw():
    assert lm._parse_last_json("just noise\nmore noise") == {"raw": "just noise\nmore noise"}
