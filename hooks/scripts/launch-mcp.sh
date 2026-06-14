#!/bin/sh
# colab-mcp-extended plugin launcher.
#
# Runs the bundled FastMCP server (colab_mcp:main, console script `colab-mcp`)
# via `uv`, resolving/creating the project virtualenv inside this plugin's clone
# directory from pyproject.toml. The server speaks stdio JSON-RPC to the MCP host
# and drives a Colab notebook through a browser backend (webbrowser by default,
# optional Playwright via the [headless] extra).
#
# All diagnostics go to stderr so they never corrupt the stdout JSON-RPC channel.

set -u

# CLAUDE_PLUGIN_ROOT is set by Claude Code when invoking plugin scripts.
# Fall back to this script's own location for manual / alt-host invocation.
: "${CLAUDE_PLUGIN_ROOT:=$(cd "$(dirname "$0")/../.." 2>/dev/null && pwd)}"

if ! command -v uv >/dev/null 2>&1; then
    echo "[colab] 'uv' not found on PATH. Install it: https://docs.astral.sh/uv/" 1>&2
    exit 127
fi

# `uv run` creates/syncs the venv on first launch from pyproject.toml.
# Pass through any args (e.g. --browser-profile, --mlx-python) supplied by the host.
exec uv run --directory "$CLAUDE_PLUGIN_ROOT" colab-mcp "$@"
