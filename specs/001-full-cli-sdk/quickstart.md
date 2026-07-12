# Quickstart and Validation Scenarios

## Consumer installation

```bash
uv tool install multica-py
multica-py doctor
```

Ephemeral:

```bash
uvx multica-py version
```

Library:

```bash
uv add multica-py
```

The upstream `multica` executable must be installed separately.

## Contributor workflow

```bash
uv sync --frozen --all-groups
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests scripts
uv run pytest
uv build
```

## Required validation scenarios

1. Fake binary receives global flags in exact order and command flags exactly as source requires.
2. Missing binary raises `ExecutableNotFoundError` without importing or initializing external state.
3. Issue JSON decodes into immutable models and ignores additive unknown fields.
4. Missing required issue field raises `OutputShapeError`.
5. Repeated metadata/attachment flags preserve caller order.
6. Mutually exclusive description inputs cannot be constructed as a valid request.
7. Timeout terminates a spawned child process tree.
8. Token arguments are redacted from exception text and logs.
9. `uv tool install` of the local wheel exposes `multica-py`.
10. `uvx --from <wheel> multica-py version` works.
11. Standard pip can install the wheel and import `multica_py`.
12. Coverage audit fails when a Cobra command is added to the pinned manifest without an SDK row.

## Verified Validation Results

Validation status: ✅ fully verified, ⚡ partially evidenced, ⚠️ defined but not directly tested.

1. ✅ `build_global_args` in `argv.py` produces flags in `--server-url`, `--workspace-id`, `--profile`, `--debug` order. Test: `test_global_args_with_server_and_workspace`, `test_global_args_with_debug` in `tests/unit/resources/test_issues.py`.
2. ✅ `find_executable` in `executable.py` raises `ExecutableNotFoundError`. Test: `test_exec_missing_multica` in `tests/unit/test_console_cli.py`.
3. ✅ `decode_json` in `decoders.py` uses `msgspec` decoding for strict typed models, and additive unknown fields are still tolerated where the target struct shape allows them. Tests: `test_decode_additive_unknown_fields` in `tests/unit/test_decoders.py`, `test_issue_additive_fields_ignored` in `tests/contract/test_issue_models.py`.
4. ✅ Missing required fields raise `OutputShapeError` via `msgspec.ValidationError`. Test: `test_decode_missing_required_field` in `tests/unit/test_decoders.py`.
5. ✅ `IssueCreateRequest.label` is `tuple[str, ...]` preserving order. Test: `test_issue_create_request_with_labels` in `tests/unit/resources/test_issues.py`.
6. ✅ `IssueCreateRequest.description_input` is a tagged union (`InlineDescription | FileDescription | StdinDescription | NoDescription`). Invalid values raise `TypeError` at construction via `__post_init__`. Test: `test_issue_create_request_with_description`, `test_issue_create_request_no_description` in `tests/unit/resources/test_issues.py`. Rejection tested in `test_invalid_value_rejected` in `test_mutually_exclusive.py`.
7. ✅ `run_with_timeout` raises `CommandTimeoutError` on timeout and `CommandCancelledError` on explicit cancellation, including escalation after ignored `SIGTERM`. Tests: `test_timeout_terminates_process` in `tests/integration/test_streaming_commands.py`, `test_run_with_timeout_raises_cancelled_for_real_process`, `test_precancelled_token_raises_immediately`, and `test_cancelled_process_escalates_after_sigterm_is_ignored` in `tests/integration/test_cancellation.py`.
8. ✅ `redact_argv` replaces `--token` values with `***`. Test: `test_transport_redacts_token` in `tests/unit/test_transport.py`.
9. ⚡ `pyproject.toml` defines `multica-py` console script entry point (verified via metadata). CLI dispatch tested via local `main()` call. Full installed-tool execution not tested in unit suite. Test: `test_console_script_defined` in `tests/packaging/test_build.py`, `test_cli_version_command` in `tests/unit/test_console_cli.py`.
10. ✅ `package-test.yml` tests `uv tool install`, `uvx --from`, `pip install`, and `uv pip install`. Release workflow validates wheel before publishing.
11. ✅ CI covers Linux and macOS, Python 3.12 and 3.13, for test, lint, types, and build.
12. ✅ `validate_manifest_sdk_mapping` detects missing SDK mappings. Test: `test_every_command_has_sdk_mapping` in `tests/contract/test_full_cli_coverage.py`.
