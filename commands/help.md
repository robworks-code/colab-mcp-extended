---
description: Overview of the colab MCP server — what it does and the full set of tools it exposes, grouped by category.
---

# colab: help

Give the user a concise overview of the **colab** MCP server and its tools. The server
drives a Google Colab notebook from Claude Code over stdio, with multi-session support
and an optional headless/Playwright backend.

If the user asked a specific question ("how do I run code?", "can it use a GPU?"), answer
that directly using the categories below rather than dumping the whole list. Otherwise,
present the grouped tool list.

## Tools by category

**Connection**
- `open_session` — open a new Colab browser session and connect to its kernel (pass a Drive
  `notebook_id` to open a specific notebook, and `authuser` to pick the Google account)
- `list_sessions`, `close_session`, `switch_session`

**Execution**
- `execute_code` (supports `capture_plots` for inline images), `interrupt_kernel`,
  `restart_kernel`
- Background jobs: `run_async`, `poll_execution`, `stop_async`, `list_jobs`

**Files**
- `install_package`, `get_runtime_info`
- VM filesystem: `upload_file`, `download_file`, `list_vm_files`, `read_vm_file`,
  `write_vm_file`, `delete_vm_file`

**Runtime**
- `get_resource_usage` (CPU/RAM/GPU/disk)

**Drive**
- `mount_drive`, `unmount_drive`, `list_drive_files`

**Secrets**
- `inject_secret_to_env`, `get_secret`

**Inspection**
- `list_variables`, `inspect_variable`

**Notebook cells**
- `list_cells`, `get_cell`, `add_cell`, `edit_cell`, `delete_cell`

**Notebook lifecycle (Playwright/headless only)**
- `change_runtime_type`, `connect_runtime`, `factory_reset_runtime`, `save_notebook`,
  `complete_drive_mount_consent`

**Round-trip (Colab-side fine-tuning)**
- `save_and_push_merged` — merge an Unsloth/PEFT model and push to a private HF repo
- `ensure_repo_readme` — seed an HF repo README so `mlx_lm.convert` doesn't 404

**Local MLX (host-side)**
- `normalize_tokenizer_config`, `download_from_hf`, `convert_to_mlx` — run on the host via the
  `--mlx-python` interpreter

## Setup

If the server isn't connected yet, point the user to `/colab:setup`.
