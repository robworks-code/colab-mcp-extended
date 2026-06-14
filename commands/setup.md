---
description: Guided first-run setup for the colab MCP server — check prerequisites (uv, optional Playwright), explain Google sign-in, and verify the server launches.
disable-model-invocation: true
---

# colab: setup

Walk the user through getting the bundled **colab** MCP server running. Be concise and
do the checks for them where you can; only ask the user to act when a step needs a human
(browser sign-in, installing a tool).

## Steps

1. **Confirm `uv` is installed** (the launcher requires it):

   ```bash
   command -v uv && uv --version
   ```

   If missing, tell the user to install it: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   (or `brew install uv`), then restart the session.

2. **Confirm the plugin's MCP server is wired up.** The server is named `colab` and is
   launched by `${CLAUDE_PLUGIN_ROOT}/hooks/scripts/launch-mcp.sh` via `.mcp.json`. Ask the
   user to run `/mcp` and confirm a `colab` server is listed. If it is not, suggest
   `/reload-plugins` (or restarting Claude Code), since plugin MCP servers load at session
   start.

3. **First launch builds the venv.** On the very first connection, `uv run` creates and syncs
   the project virtualenv from `pyproject.toml` inside the plugin clone. This can take a
   minute; subsequent launches are fast. The default backend is `webbrowser` — no extra
   install needed.

4. **Optional: headless / Playwright backend.** The notebook-lifecycle tools
   (`change_runtime_type`, `connect_runtime`, `factory_reset_runtime`, `save_notebook`,
   `complete_drive_mount_consent`) require the `[headless]` extra. To enable it, the user can
   install Playwright into the plugin's environment:

   ```bash
   uv run --directory "$CLAUDE_PLUGIN_ROOT" python -m pip install '.[headless]'
   uv run --directory "$CLAUDE_PLUGIN_ROOT" python -m playwright install chromium
   ```

5. **Google sign-in.** The server drives Colab through a real browser session, so the user
   must be signed in to the Google account that owns the target notebooks. To reuse a
   persistent browser profile across runs, the server accepts `--browser-profile /path/to/profile`
   and `authuser` selects the account index. Auth happens in the browser, out-of-band — there
   is no token to paste here.

6. **Optional: local MLX tools.** `normalize_tokenizer_config`, `download_from_hf`, and
   `convert_to_mlx` run on the host using the interpreter set by `--mlx-python` /
   `COLAB_MCP_MLX_PYTHON` (defaults to the server's own interpreter). Mention this only if the
   user is doing fine-tune round-trips.

7. **Verify.** Ask the user to try `open_session` (optionally with a Drive `notebook_id`), then
   `execute_code` with something trivial like `print(1 + 1)`. If that returns output, setup is
   complete. Point them to `/colab:help` for the full tool list.
