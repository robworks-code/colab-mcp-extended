import sys

from colab_mcp.session_manager import SessionManager
from colab_mcp.tools.runtime import get_runtime_tools
from colab_mcp.tools.drive import get_drive_tools
from colab_mcp.tools.secrets import get_secret_tools
from colab_mcp.tools.inspect import get_inspect_tools
from colab_mcp.tools.roundtrip import get_roundtrip_tools
from colab_mcp.tools.local_mlx import get_local_mlx_tools
from colab_mcp import parse_args


def test_all_new_tool_groups_yield_tools():
    sm = SessionManager(default_browser_profile=None)
    names = set()
    for grp in (get_runtime_tools(sm), get_drive_tools(sm),
                get_secret_tools(sm), get_inspect_tools(sm),
                get_roundtrip_tools(sm)):
        for t in grp:
            names.add(t.name)
    for t in get_local_mlx_tools(sys.executable):
        names.add(t.name)
    assert {"get_resource_usage", "mount_drive", "unmount_drive",
            "list_drive_files", "inject_secret_to_env", "get_secret",
            "list_variables", "inspect_variable",
            "save_and_push_merged", "ensure_repo_readme",
            "normalize_tokenizer_config", "download_from_hf",
            "convert_to_mlx"} <= names


def test_mlx_python_defaults_to_sys_executable():
    args = parse_args([])
    assert args.mlx_python == sys.executable


def test_mlx_python_env_override(monkeypatch):
    monkeypatch.setenv("COLAB_MCP_MLX_PYTHON", "/custom/python")
    args = parse_args([])
    assert args.mlx_python == "/custom/python"


def test_mlx_python_flag_wins_over_env(monkeypatch):
    monkeypatch.setenv("COLAB_MCP_MLX_PYTHON", "/env/python")
    args = parse_args(["--mlx-python", "/flag/python"])
    assert args.mlx_python == "/flag/python"
