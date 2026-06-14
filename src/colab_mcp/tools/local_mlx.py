# src/colab_mcp/tools/local_mlx.py
"""Local-host MLX round-trip tools (run where the server runs, not in Colab)."""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
from typing import Any

from fastmcp.tools.tool import Tool

_DROP_KEYS = ("backend", "is_local", "from_slow")


def _normalize_tokenizer_config(path: str) -> dict[str, Any]:
    """Rewrite tokenizer_config.json so a different local transformers can load it.

    Colab transformers writes tokenizer_class 'TokenizersBackend', which other
    versions cannot import. Normalize it to 'PreTrainedTokenizerFast' and drop the
    backend/is_local/from_slow keys. Idempotent. `path` may be the model dir or the
    json file itself.
    """
    cfg_path = (
        os.path.join(path, "tokenizer_config.json") if os.path.isdir(path) else path
    )
    if not os.path.isfile(cfg_path):
        return {"error": f"tokenizer_config.json not found at {cfg_path}"}
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)
    changed: list[str] = []
    if cfg.get("tokenizer_class") == "TokenizersBackend":
        cfg["tokenizer_class"] = "PreTrainedTokenizerFast"
        changed.append("tokenizer_class")
    for k in _DROP_KEYS:
        if k in cfg:
            del cfg[k]
            changed.append(k)
    if changed:
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    return {"path": cfg_path, "changed": changed}


def _download_script(repo_id: str, local_dir: str) -> str:
    return (
        "import json, os\n"
        "from huggingface_hub import snapshot_download\n"
        f"p = snapshot_download(repo_id={repo_id!r}, local_dir={local_dir!r})\n"
        "print(json.dumps({'path': p, 'files': sorted(os.listdir(p))}))\n"
    )


def _parse_last_json(stdout: str) -> dict[str, Any]:
    for line in reversed(stdout.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return {"raw": stdout.strip()}


def get_local_mlx_tools(mlx_python: str) -> list[Tool]:
    async def normalize_tokenizer_config(path: str) -> str:
        """Normalize a downloaded model's tokenizer_config.json for local load.

        Rewrites tokenizer_class 'TokenizersBackend' (written by Colab transformers)
        to 'PreTrainedTokenizerFast' and drops backend/is_local/from_slow so a
        different local transformers / mlx_lm can load the tokenizer. Idempotent.

        Args:
            path: Local model directory (or the tokenizer_config.json file).

        Returns:
            JSON {path, changed[]} or {error}.
        """
        return json.dumps(_normalize_tokenizer_config(path))

    async def download_from_hf(repo_id: str, local_dir: str) -> str:
        """Download an HF repo to a local directory via the configured interpreter.

        Runs snapshot_download in the --mlx-python environment so the model can be
        normalized before conversion. Returns the local path and file list.

        Args:
            repo_id: HF repo id, e.g. "user/model".
            local_dir: Destination directory on the local host.

        Returns:
            JSON {path, files[]} or {error}.
        """
        proc = await asyncio.to_thread(
            subprocess.run,
            [mlx_python, "-c", _download_script(repo_id, local_dir)],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            return json.dumps({"error": proc.stderr.strip() or "download failed"})
        return json.dumps(_parse_last_json(proc.stdout))

    async def convert_to_mlx(source: str, mlx_path: str, quantize: bool = False,
                             q_bits: int = 4, clear_existing: bool = True,
                             normalize: bool = True) -> str:
        """Convert an HF model (local dir or repo id) to MLX format locally.

        When `source` is a local directory and `normalize` is set, runs the
        tokenizer-config normalization first. When `clear_existing` is set and
        `mlx_path` exists, it is moved aside before conversion and restored if the
        conversion fails (mlx_lm.convert refuses to write into an existing dir). If
        stderr mentions sentencepiece, returns an install hint.

        Args:
            source: Local model dir or HF repo id (passed as --hf-path).
            mlx_path: Output directory for the MLX model.
            quantize: If true, pass -q with --q-bits.
            q_bits: Quantization bit width (default 4).
            clear_existing: Move mlx_path aside before converting (restored on failure).
            normalize: Normalize tokenizer_config when source is a local dir.

        Returns:
            JSON {mlx_path, status, normalized?} or {error, argv, hint?, normalized?}.
        """
        mlx_path = os.path.normpath(mlx_path)
        norm = None
        if normalize and os.path.isdir(source):
            norm = _normalize_tokenizer_config(source)
        backup = None
        if clear_existing and os.path.isdir(mlx_path):
            backup = mlx_path + ".bak"
            if os.path.isdir(backup):
                shutil.rmtree(backup)
            os.rename(mlx_path, backup)
        argv = [mlx_python, "-m", "mlx_lm.convert",
                "--hf-path", source, "--mlx-path", mlx_path]
        if quantize:
            argv += ["-q", "--q-bits", str(q_bits)]
        proc = await asyncio.to_thread(subprocess.run, argv,
                                       capture_output=True, text=True)
        if proc.returncode != 0:
            if os.path.isdir(mlx_path):
                shutil.rmtree(mlx_path)  # drop the partial/corrupt output
            if backup is not None:
                os.rename(backup, mlx_path)  # restore the prior output
            err: dict[str, Any] = {
                "error": proc.stderr.strip() or "convert failed", "argv": argv,
            }
            if "sentencepiece" in (proc.stderr or "").lower():
                err["hint"] = f"pip install sentencepiece in {mlx_python}'s environment"
            if norm is not None:
                err["normalized"] = norm
            return json.dumps(err)
        if backup is not None:
            shutil.rmtree(backup)
        result: dict[str, Any] = {"mlx_path": mlx_path, "status": "ok"}
        if norm is not None:
            result["normalized"] = norm
        return json.dumps(result)

    return [
        Tool.from_function(fn=normalize_tokenizer_config, name="normalize_tokenizer_config",
                           description="Normalize a local model's tokenizer_config.json for MLX/transformers load."),
        Tool.from_function(fn=download_from_hf, name="download_from_hf",
                           description="Download an HF repo to a local directory via the configured interpreter."),
        Tool.from_function(fn=convert_to_mlx, name="convert_to_mlx",
                           description="Convert an HF model (local dir or repo id) to MLX format locally."),
    ]
