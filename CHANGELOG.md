# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.1] - 2026-06-13

### Security

- Bump `fastmcp` 2.14.5 -> 3.2.0, resolving three advisories in unused fastmcp
  features (OpenAPI provider SSRF/path traversal, OAuth proxy confused-deputy,
  Gemini CLI command injection). None were reachable in this codebase.

### Changed

- Use the non-deprecated `fastmcp.server.providers.proxy` import path for
  `FastMCPProxy`.

### Added

- `Installation` section in the README with clone and dev-install instructions.
- `.gitignore` covering Python build artifacts, virtual environments, and macOS files.

## [1.1.0] - 2026-06-13

### Added

- Runtime: `get_resource_usage` (live GPU utilization/memory, RAM, disk).
- Drive: `mount_drive`, `unmount_drive`, `list_drive_files`.
- Secrets: `inject_secret_to_env` (sets an environment variable without returning the
  value; refuses loader-sensitive variables such as PATH and LD_PRELOAD) and `get_secret`.
- VM filesystem: `list_vm_files`, `read_vm_file`, `write_vm_file`, `delete_vm_file`.
- Inspection: `list_variables` and `inspect_variable` (type, shape/dtype, DataFrame head).
- Async execution: `run_async`, `poll_execution` (incremental output via a cursor),
  `stop_async` (cooperative), and `list_jobs` - a background in-kernel thread for
  long-running jobs.
- Browser/UI control (Playwright sessions): `change_runtime_type`, `connect_runtime`,
  `factory_reset_runtime`, `save_notebook`, `complete_drive_mount_consent`.
- Optional `capture_plots` on `execute_code` returns matplotlib figures as image blocks.
- pytest suite (37 tests); Playwright-dependent tests skip cleanly when the `headless`
  extra is not installed.

### Changed

- `execute_code` extracts result text via `extract_text` so `capture_plots` image
  parsing works and output is clean.
- Blocking browser tools report progress while they wait.

## [1.0.0] - 2026

### Added

- Multi-session architecture with headless browser support.
- Initial fork of colab-mcp with `notebook_id` and `authuser` support.

[Unreleased]: https://github.com/robworks-code/colab-mcp-extended/compare/v1.1.1...HEAD
[1.1.1]: https://github.com/robworks-code/colab-mcp-extended/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/robworks-code/colab-mcp-extended/releases/tag/v1.1.0
[1.0.0]: https://github.com/robworks-code/colab-mcp-extended/commits/main
