# src/colab_mcp/tools/roundtrip.py
"""Colab-side fine-tune round-trip tools (save / merge / push to HF)."""
from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

from fastmcp.tools.tool import Tool

from colab_mcp.tools._runner import run_python, wrap_output

if TYPE_CHECKING:
    from colab_mcp.session_manager import SessionManager

_DEFAULT_README = "# Merged model\n\nUploaded by colab-mcp-extended.\n"

_IDENT_RE = re.compile(r"^[A-Za-z_]\w*$")


def _validate_var_name(name: str) -> str | None:
    """Return an error message if name is not a bare Python identifier, else None."""
    if not _IDENT_RE.match(name or ""):
        return f"invalid kernel variable name: {name!r}"
    return None


def _gen_save_push_code(model_var: str, tokenizer_var: str, repo_id: str,
                        save_method: str, clear_repo: bool) -> str:
    body = (
        "import json, os, glob, tempfile\n"
        "from huggingface_hub import HfApi, get_token\n"
        "_tmp = tempfile.mkdtemp(prefix='colab_mcp_merged_')\n"
        "try:\n"
        f"    {model_var}.save_pretrained_merged(_tmp, {tokenizer_var}, save_method={save_method!r})\n"
        "    _st = glob.glob(os.path.join(_tmp, '*.safetensors'))\n"
        "    if not _st:\n"
        "        print(json.dumps({'error': 'no .safetensors produced by save_pretrained_merged'}))\n"
        "    else:\n"
        "        _rp = os.path.join(_tmp, 'README.md')\n"
        "        if not os.path.exists(_rp):\n"
        "            with open(_rp, 'w') as _f:\n"
        f"                _f.write({_DEFAULT_README!r})\n"
        "        _api = HfApi(token=get_token())\n"
        f"        _api.create_repo({repo_id!r}, private=True, exist_ok=True)\n"
        f"        _dp = ['*'] if {bool(clear_repo)!r} else None\n"
        f"        _api.upload_folder(folder_path=_tmp, repo_id={repo_id!r}, delete_patterns=_dp)\n"
        "        _files = sorted(os.path.basename(p) for p in glob.glob(os.path.join(_tmp, '*')))\n"
        f"        print(json.dumps({{'repo_id': {repo_id!r}, 'url': 'https://huggingface.co/' + {repo_id!r}, 'files': _files}}))\n"
        "except Exception as e:\n"
        "    print(json.dumps({'error': str(e)}))\n"
    )
    return wrap_output(body)


def _gen_ensure_readme_code(repo_id: str, content: str | None) -> str:
    text = content if content is not None else _DEFAULT_README
    body = (
        "import io, json\n"
        "from huggingface_hub import HfApi, get_token\n"
        "try:\n"
        "    _api = HfApi(token=get_token())\n"
        f"    _api.create_repo({repo_id!r}, private=True, exist_ok=True)\n"
        f"    _existed = _api.file_exists({repo_id!r}, 'README.md')\n"
        "    if not _existed:\n"
        f"        _api.upload_file(path_or_fileobj=io.BytesIO({text!r}.encode()), path_in_repo='README.md', repo_id={repo_id!r})\n"
        f"    print(json.dumps({{'repo_id': {repo_id!r}, 'readme_existed': _existed}}))\n"
        "except Exception as e:\n"
        "    print(json.dumps({'error': str(e)}))\n"
    )
    return wrap_output(body)


def get_roundtrip_tools(session_manager: SessionManager) -> list[Tool]:
    async def save_and_push_merged(model_var: str, tokenizer_var: str, repo_id: str,
                                   save_method: str = "merged_16bit",
                                   clear_repo: bool = True,
                                   session_id: str | None = None) -> str:
        """Merge an Unsloth/PEFT model and push it to a private HF repo.

        Runs `<model_var>.save_pretrained_merged(...)` in the kernel (reliable, unlike
        push_to_hub_merged which can silently no-op), verifies a .safetensors was
        produced, ensures a README exists (so later mlx_lm.convert won't 404), and
        uploads via HfApi using the cached token from get_token(). With clear_repo,
        passes delete_patterns=['*'] so stale files from a prior different-arch push
        are removed.

        Args:
            model_var: Name of the model object in the kernel namespace.
            tokenizer_var: Name of the tokenizer object in the kernel namespace.
            repo_id: Target HF repo id, e.g. "user/model".
            save_method: Unsloth save method (default "merged_16bit").
            clear_repo: Clear existing repo files on upload (default True).
            session_id: Target session. Uses active session if not specified.

        Returns:
            JSON {repo_id, url, files[]} or {error}.
        """
        err = _validate_var_name(model_var) or _validate_var_name(tokenizer_var)
        if err:
            return json.dumps({"error": err})
        session = session_manager.resolve_session(session_id)
        code = _gen_save_push_code(model_var, tokenizer_var, repo_id, save_method, clear_repo)
        return json.dumps(await run_python(session, code))

    async def ensure_repo_readme(repo_id: str, content: str | None = None,
                                 session_id: str | None = None) -> str:
        """Ensure a HF repo has a README.md (prevents mlx_lm.convert 404).

        Creates the private repo if needed and uploads a minimal README only when one
        is not already present.

        Args:
            repo_id: Target HF repo id.
            content: Optional README body; a minimal default is used if omitted.
            session_id: Target session. Uses active session if not specified.

        Returns:
            JSON {repo_id, readme_existed} or {error}.
        """
        session = session_manager.resolve_session(session_id)
        return json.dumps(await run_python(session, _gen_ensure_readme_code(repo_id, content)))

    return [
        Tool.from_function(fn=save_and_push_merged, name="save_and_push_merged",
                           description="Merge an Unsloth/PEFT model and push it to a private HF repo (verifies safetensors, clears stale files)."),
        Tool.from_function(fn=ensure_repo_readme, name="ensure_repo_readme",
                           description="Ensure a HF repo has a README.md (prevents mlx_lm.convert 404)."),
    ]
