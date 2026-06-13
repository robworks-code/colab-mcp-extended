from colab_mcp.session_manager import SessionManager
from colab_mcp.tools.runtime import get_runtime_tools
from colab_mcp.tools.drive import get_drive_tools
from colab_mcp.tools.secrets import get_secret_tools
from colab_mcp.tools.inspect import get_inspect_tools


def test_all_new_tool_groups_yield_tools():
    sm = SessionManager(default_browser_profile=None)
    names = set()
    for grp in (get_runtime_tools(sm), get_drive_tools(sm),
                get_secret_tools(sm), get_inspect_tools(sm)):
        for t in grp:
            names.add(t.name)
    assert {"get_resource_usage", "mount_drive", "unmount_drive",
            "list_drive_files", "inject_secret_to_env", "get_secret",
            "list_variables", "inspect_variable"} <= names
