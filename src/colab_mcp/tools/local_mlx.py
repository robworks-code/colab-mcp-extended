# src/colab_mcp/tools/local_mlx.py
"""Local-host MLX round-trip tools (run where the server runs, not in Colab)."""
from __future__ import annotations

import json
import os
from typing import Any

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
