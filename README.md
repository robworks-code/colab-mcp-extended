# colab-mcp-extended

Extended version of Google's [colab-mcp](https://github.com/googlecolab/colab-mcp) that supports opening specific Drive notebooks instead of always opening the scratchpad.

## Changes from upstream

- `notebook_id` parameter on `open_colab_browser_connection` - pass a Google Drive file ID to open that notebook
- `authuser` parameter - specify which Google account to use (default: 1)
- Multi-session support - manage multiple Colab sessions concurrently
- Headless/Playwright browser backend (optional, via `[headless]` extra)
- Expanded tool set covering execution, files, Drive, secrets, inspection, and notebook cells
- Fine-tune round-trip helpers (Colab-side merge/push) and host-side MLX conversion tools

## Installation

### As a Claude Code plugin (recommended)

This repo doubles as the `colab` Claude Code plugin, published via the
[robworks-claude-code-plugins](https://github.com/ringo380/robworks-claude-code-plugins)
marketplace:

```
/plugin marketplace add ringo380/robworks-claude-code-plugins
/plugin install colab@robworks-claude-code-plugins
```

The bundled MCP server launches via [`uv`](https://docs.astral.sh/uv/) (required on PATH);
the project virtualenv is created from `pyproject.toml` on first launch. Run `/colab:setup`
for guided first-run setup and `/colab:help` for the full tool list.

### Standalone (pip)

```bash
git clone https://github.com/robworks-code/colab-mcp-extended.git
cd colab-mcp-extended
pip install -e .            # or: pip install -e '.[headless]' for Playwright support
```

## Tools

### Connection

- `open_session` - Open a new Colab browser session and connect to its kernel
- `list_sessions` - List all active sessions and their status
- `close_session` - Close a session and release its browser/kernel resources
- `switch_session` - Switch the active session used by subsequent tool calls

### Execution

- `execute_code` - Execute Python code in the Colab kernel; supports `capture_plots` to return inline images
- `interrupt_kernel` - Send a kernel interrupt (equivalent to Ctrl+C)
- `restart_kernel` - Restart the Colab kernel, clearing all in-memory state
- `run_async` - Start a long-running code execution in the background and return a job ID
- `poll_execution` - Poll the status and partial output of a background job
- `stop_async` - Cancel a running background job
- `list_jobs` - List all active and recently completed background jobs

### Files

- `install_package` - Install a Python package in the Colab runtime via pip
- `get_runtime_info` - Return Python version, installed packages, and environment details
- `upload_file` - Upload a local file to the Colab VM filesystem
- `download_file` - Download a file from the Colab VM to the local machine
- `list_vm_files` - List files and directories on the Colab VM
- `read_vm_file` - Read the contents of a file on the Colab VM
- `write_vm_file` - Write or overwrite a file on the Colab VM
- `delete_vm_file` - Delete a file or directory from the Colab VM

### Runtime

- `get_resource_usage` - Return current CPU, RAM, GPU, and disk usage for the Colab runtime

### Drive

- `mount_drive` - Mount Google Drive in the Colab runtime at `/content/drive`
- `unmount_drive` - Unmount Google Drive from the Colab runtime
- `list_drive_files` - List files in a Google Drive folder (requires Drive mounted)

### Secrets

- `inject_secret_to_env` - Read a Colab secret and inject it as an environment variable
- `get_secret` - Return the value of a Colab secret

### Inspection

- `list_variables` - List all variables currently defined in the kernel namespace
- `inspect_variable` - Return the type, shape, and value summary of a named variable

### Notebook cells

- `list_cells` - List all cells in the open notebook with their types and truncated content
- `get_cell` - Return the full source of a specific notebook cell
- `add_cell` - Insert a new code or markdown cell at a given position
- `edit_cell` - Replace the source of an existing notebook cell
- `delete_cell` - Delete a notebook cell by index

### Notebook lifecycle (Playwright/headless only)

- `change_runtime_type` - Change the Colab runtime hardware accelerator (CPU/GPU/TPU)
- `connect_runtime` - Connect to the Colab runtime if disconnected
- `factory_reset_runtime` - Factory-reset the Colab runtime, deleting all VM files
- `save_notebook` - Save the current notebook to Google Drive
- `complete_drive_mount_consent` - Click through the Google Drive mount authorization dialog

### Round-trip (Colab-side)

Helpers for the fine-tune round-trip, run inside the Colab kernel:

- `save_and_push_merged` - Merge an Unsloth/PEFT model and push it to a private HF repo (verifies safetensors, clears stale files)
- `ensure_repo_readme` - Ensure an HF repo has a `README.md` (prevents `mlx_lm.convert` 404)

### Local MLX (host-side)

These run on the machine hosting the MCP server, not in a Colab session. They use
the interpreter selected by `--mlx-python` / `COLAB_MCP_MLX_PYTHON` (defaults to the
server's own interpreter):

- `normalize_tokenizer_config` - Normalize a local model's `tokenizer_config.json` for MLX/transformers load
- `download_from_hf` - Download an HF repo to a local directory via the configured interpreter
- `convert_to_mlx` - Convert an HF model (local dir or repo id) to MLX format locally
