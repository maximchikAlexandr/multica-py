## 1. Resource methods

- [x] 1.1 In `src/multica_py/resources/attachments.py`, add `import tempfile` after `import pathlib` (line 3). Keep the existing imports.
- [x] 1.2 In `src/multica_py/resources/attachments.py`, add `upload_bytes` after `upload` (after line 17):
  ```python
  def upload_bytes(self, issue_id: str, filename: str, payload: bytes) -> AttachmentResult:
      _safe_leaf(filename, "filename")
      with tempfile.TemporaryDirectory() as tmp:
          path = pathlib.Path(tmp) / filename
          path.write_bytes(payload)
          return self.upload(issue_id, str(path))
  ```
  Validate `filename` is a bare leaf (no path separators, non-empty) via `_safe_leaf` before building the path; raises `ValueError` otherwise. This preserves the exact `filename` as the `--file` basename (the existing `upload` resolves the path, whose final component is `filename`), writes `payload` verbatim (empty `bytes` produces a zero-length file), and the `with` block removes the temp directory on both success and exception exit. No CLI command-building logic is duplicated: it delegates to `self.upload`.
- [x] 1.3 In `src/multica_py/resources/attachments.py`, add `download_bytes` after `download` (after line 27):
  ```python
  def download_bytes(self, attachment_id: str) -> bytes:
      _safe_leaf(attachment_id, "attachment_id")
      with tempfile.TemporaryDirectory() as tmp:
          path = pathlib.Path(tmp) / attachment_id
          self.download(attachment_id, str(path))
          return path.read_bytes()
      # ponytail: assumes upstream `--output <file>` writes to that exact file path;
      # if upstream ever writes a server-named file into a directory, read the single
      # file in tmp instead. Covered by test_attachments.py::test_download_bytes_round_trip.
  ```
  Validate `attachment_id` is a bare leaf (no path separators, non-empty) via `_safe_leaf` before building the path; raises `ValueError` otherwise. Delegates to `self.download` (no argv duplication), reads the file back as `bytes` (empty attachment → `b''`), and the `with` block cleans up on success and failure. The exception from `download()` propagates unchanged (same SDK exception type) and the `with` exits cleanup the directory before the exception reaches the caller.

- [x] 1.4 Add a private `_safe_leaf` validator at module scope in `attachments.py` before `AttachmentResource`:
  ```python
  def _safe_leaf(name: str, param: str) -> str:
      if not name:
          raise ValueError(f"{param} must not be empty")
      if name in (".", "..") or pathlib.PurePath(name).name != name or "/" in name or "\\" in name:
          raise ValueError(f"{param} must be a bare filename, not a path: {name!r}")
      return name
  ```
  Also rejects `name` equal to `"."` or `".."` (defence-in-depth: `Path(tmp) / ".."` raises `IsADirectoryError` instead of the spec-required `ValueError`). Applied by tasks 1.2 and 1.3 at the trust boundary before building `pathlib.Path(tmp) / <param>`. Path-traversal defence (ASVS 12.8.1/12.8.2): rejects empty, absolute, and `..`-bearing values. Same `ValueError` family the rest of the resource uses for bad input.

## 2. Operation-case harness: general dynamic-path support

- [x] 2.1 In `tests/cases/operations.py`, add two fields to the `OperationCase` dataclass (after line 57, the `source_ref` field):
  ```python
  argv_check: str = "exact"
  transport_side_effect: Callable[..., object] | None = None
  ```
  `argv_check` is `"exact"` (today's behavior) or `"none"` (skip exact argv equality in `_assert_transport_call`; rely on `assert_result` to verify argv structurally). `transport_side_effect`, when set, is applied by `_configure_mock` as the mock's side effect for the transport method instead of a canned return value. `Callable` is already imported (line 5). These fields are general (not attachment-specific): any future convenience method with a dynamic argv component or a file-writing transport reuses them.
- [x] 2.2 In `tests/unit/resources/test_operations.py`, extend `_configure_mock` (lines 25-42) to honor `transport_side_effect`: before the existing `if case.transport_method == "spawn":` branch, add
  ```python
  if case.transport_side_effect is not None:
      if case.transport_method == "run_bytes":
          mock_transport.run_bytes.side_effect = case.transport_side_effect
      elif case.transport_method == "run_text":
          mock_transport.run_text.side_effect = case.transport_side_effect
      elif case.transport_method == "spawn":
          mock_transport.spawn.side_effect = case.transport_side_effect
      return
  ```
  When no side effect is set, the existing return-value configuration runs unchanged.
- [x] 2.3 In `tests/unit/resources/test_operations.py`, extend `_assert_transport_call` (lines 45-70) to honor `argv_check == "none"`: in the `run_bytes` branch (lines 57-64), wrap the exact argv equality in `if case.argv_check == "exact":`; when `"none"`, only assert `mock_transport.run_bytes.assert_called_once()` (the structural argv check is delegated to `case.assert_result`). Do the same in the `run_text` branch (lines 65-68): wrap `call_args.args == (tuple(case.expected_argv),)` in `if case.argv_check == "exact":`. The `spawn` branch stays exact (no dynamic-path spawn cases). `assert_result` (line 54-55) already runs before the transport-method branches, so structural argv verification inside `assert_result` has access to `mock_transport` via closure — pass `mock_transport` into `assert_result` by changing the call to `case.assert_result(result, mock_transport)` (see task 2.4).
- [x] 2.4 In `tests/unit/resources/test_operations.py`, change the `assert_result` call (line 55) from `case.assert_result(result)` to `case.assert_result(result, mock_transport)`. Update the `assert_result` type on `OperationCase` (tests/cases/operations.py line 55) from `Callable[[object], None] | None` to `Callable[[object, MagicMock], None] | None`. `MagicMock` is already imported in test_operations.py (line 6); in operations.py add `from unittest.mock import MagicMock` (or use `typing.Any`/`object` — prefer importing `MagicMock` for the type hint; add the import after line 8). Existing `assert_result` callables (the generated `assert_type`/`assert_page`/`_assert_none` in `generated_operation_cases`) take only `result`; update their signatures to accept a second `mock_transport: MagicMock` parameter and ignore it, so they keep working through the same call site.

## 3. Operation-case rows

- [x] 3.1 In `tests/cases/operations.py`, add two `LEGACY_ARGV_MIGRATION` entries after `legacy:146` (line 444):
  ```python
  "legacy:147": "manual:attachments.upload_bytes:canonical",
  "legacy:148": "manual:attachments.download_bytes:canonical",
  ```
- [x] 3.2 In `tests/cases/operations.py`, add two canonical rows in `_build_operation_cases` immediately after the existing `attachments.download` row (after line 776). Import nothing new (`AttachmentResult` is already imported via `multica_py.models.system` at line 500; `pathlib` is imported locally at line 450). Use a local helper to build the structural `assert_result`:
  ```python
  def _assert_upload_bytes(result: object, mt: MagicMock) -> None:
      assert isinstance(result, AttachmentResult)
      assert result.id == "a1"
      mt.run_bytes.assert_called_once()
      argv = mt.run_bytes.call_args.args[0]
      assert argv[:4] == ("attachment", "upload", "i1", "--file")
      assert argv[-2:] == ("--output", "json")
      assert argv[4].endswith("manifest.json")
      # the --file basename is the preserved filename
      assert pathlib.PurePath(argv[4]).name == "manifest.json"

  def _assert_download_bytes(result: object, mt: MagicMock) -> None:
      assert result == b"\x00\x01binary"
      mt.run_text.assert_called_once()
      argv = mt.run_text.call_args.args[0]
      assert argv[:4] == ("attachment", "download", "a1", "--output")

  def _write_download(_argv: tuple[str, ...], **_kw: object) -> TextResult:
      pathlib.Path(_argv[_argv.index("--output") + 1]).write_bytes(b"\x00\x01binary")
      return TextResult(text="", stderr="", exit_code=0)

  cases.append(_c(
      "attachments.upload_bytes",
      ("attachment", "upload", "i1", "--file", "<dynamic>", "--output", "json"),
      args=("i1", "manifest.json", b'{"x":1}'),
      stdout=_AR,
      id="manual:attachments.upload_bytes:canonical",
      argv_check="none",
      assert_result=_assert_upload_bytes,
  ))
  cases.append(_c(
      "attachments.download_bytes",
      ("attachment", "download", "a1", "--output", "<dynamic>"),
      args=("a1",),
      transport="run_text",
      id="manual:attachments.download_bytes:canonical",
      argv_check="none",
      transport_side_effect=_write_download,
      assert_result=_assert_download_bytes,
  ))
  ```
  `TextResult` is already imported in `tests/unit/resources/test_operations.py` (line 10) but NOT in `tests/cases/operations.py`; add `from multica_py._internal.specs import TextResult` to the local imports inside `_build_operation_cases` (after line 452, near the other local imports). `MagicMock` import added in task 2.4 covers the type hints. The `expected_argv` tuples carry a `"<dynamic>"` placeholder purely for documentation/fingerprint stability (see task 4.3); the structural assertion ignores it.
- [x] 3.3 Confirm `_c` passes through the new fields: `_c` (lines 602-654) constructs `OperationCase(...)` with named fields and does not pass `argv_check`/`transport_side_effect` today. Add `argv_check=argv_check` and `transport_side_effect=transport_side_effect` to the `_c` signature (defaulting `argv_check: str = "exact"` and `transport_side_effect: Callable[..., object] | None = None`) and to the `OperationCase(...)` constructor call (lines 635-654). No other call sites need changes (defaults preserve existing behavior).

## 4. Legacy payload fingerprints

- [x] 4.1 In `tests/cases/legacy_payloads.py`, append two fingerprints for `legacy:147` and `legacy:148` computed with the existing formula used by `test_legacy_payload_bijection` (tests/unit/resources/test_operations.py:103-114):
  ```python
  payload(case) = (
      case.resource_attr, case.method, case.args,
      tuple(sorted(dict(case.kwargs).items())),
      case.transport_method, case.expected_argv,
      case.stdin, case.timeout, case.stdout,
  )
  ```
  Compute each as `hashlib.sha256(repr(payload(case)).encode()).hexdigest()` against the final `OperationCase` rows from task 3.2 (after the fields are finalized). The fingerprint list grows 146 → 148.
- [x] 4.2 Recompute the two fingerprints AFTER tasks 3.1–3.3 are done so the `OperationCase` rows are in their final shape (the `expected_argv` with `"<dynamic>"`, the `args`, `transport_method`, `stdout` all feed the fingerprint). Use:
  ```sh
  uv run python -c "
  import hashlib
  from tests.cases.operations import OPERATION_CASES as OC
  for cid in ('manual:attachments.upload_bytes:canonical','manual:attachments.download_bytes:canonical'):
      c = next(x for x in OC if x.id == cid)
      p = (c.resource_attr, c.method, c.args, tuple(sorted(dict(c.kwargs).items())), c.transport_method, c.expected_argv, c.stdin, c.timeout, c.stdout)
      print(cid, hashlib.sha256(repr(p).encode()).hexdigest())
  "
  ```

## 5. Counter invariants

- [x] 5.1 In `tests/unit/resources/test_operations.py::test_discovered_public_methods` (lines 79-95), update the counter assertions. After adding `attachments.upload_bytes` and `attachments.download_bytes` as canonical public methods:
  - `len(discovered) == 119` (was 117)
  - `len(OPERATION_CASES) == 151` (was 149)
  - `sum(1 for c in OPERATION_CASES if c.is_canonical) == 119` (was 117)
  - `sum(1 for c in OPERATION_CASES if not c.is_canonical) == 32` (unchanged: the two new rows are canonical, not `:variant:`)
  - `len(generated) == 37` (unchanged: the two new rows are `manual:`)
  - `len(manual) == 114` (was 112)
  Recompute every counter against the actual edited `OPERATION_CASES` before committing — these are exact invariants, not estimates. The `assert all(...)` invariants (lines 91-95) still hold: generated rows have `source_ref is None`, manual rows have `source_ref is not None` (the two new rows get `legacy:147`/`legacy:148` as their `source_ref` via the `LEGACY_ARGV_MIGRATION` lookup in `_c`).
- [x] 5.2 In `tests/unit/resources/test_operations.py::test_legacy_payload_bijection` (lines 98-128), update: `range(1, 147)` → `range(1, 149)` (line 116), `len(LEGACY_PAYLOAD_FINGERPRINTS) == 148` (line 118, was 146), and the bijection length `== 148` (line 119, was 146).

## 6. Lifecycle tests

- [x] 6.1 Create `tests/unit/resources/test_attachments.py` with a fake transport that writes real files, so the temp-file lifecycle is observable. Use a minimal fake implementing the `CliTransport` surface used by `AttachmentResource` (`run_bytes` returning `RawCommandResult`, `run_text` writing a file to `--output` and returning `TextResult`), or reuse `mock_transport` + `side_effect` where the side_effect writes the file. Reuse the `mock_transport` fixture from `tests/unit/resources/conftest.py` and `ClientConfig()`.
- [x] 6.2 Add `test_upload_bytes_round_trip`: build `AttachmentResource(mock_transport, ClientConfig())`, configure `mock_transport.run_bytes` to return `RawCommandResult(argv=(), stdout=_AR, exit_code=0, stderr=b"", duration=datetime.timedelta())` (reuse the `_AR = msgspec.json.encode(AttachmentResult(id="a1", filename="manifest.json"))` fixture inline). Call `upload_bytes("i1", "manifest.json", b'{"x":1}')`. Assert the result is `AttachmentResult(id="a1")`. Assert `run_bytes` was called once and the `--file` path's basename is `manifest.json`. Use `tmp_path`-independent observation: after the call, assert no `tempfile`-managed directory leaks (the `with` cleaned up) by checking that the `--file` path's parent no longer exists (`pathlib.Path(file_arg).parent.exists() is False`).
- [x] 6.3 Add `test_upload_bytes_empty_payload`: call `upload_bytes("i1", "empty.bin", b'')`. Configure the fake transport to capture the `--file` path and assert `pathlib.Path(file_arg).stat().st_size == 0` (empty file written). Assert the decoded `AttachmentResult` is returned. Assert the temp dir is cleaned up.
- [x] 6.4 Add `test_upload_bytes_preserves_filename`: call `upload_bytes("i1", "ai-factory-result.json", b'...')`. Assert the `--file` argv value ends with `ai-factory-result.json` and `PurePath(...).name == "ai-factory-result.json"`.
- [x] 6.5 Add `test_download_bytes_round_trip`: configure `mock_transport.run_text` side effect to write `b'\x00\x01binary'` to the `--output` path in argv. Call `download_bytes("a1")`. Assert the return is exactly `b'\x00\x01binary'`. Assert the temp dir is cleaned up (the `--output` path's parent no longer exists).
- [x] 6.6 Add `test_download_bytes_empty_attachment`: side effect writes `b''`. Assert `download_bytes("a1") == b''`.
- [x] 6.7 Add `test_upload_bytes_cleans_up_on_failure`: configure `mock_transport.run_bytes` to raise `RuntimeError("cli failed")`. Assert `upload_bytes("i1","f.txt",b'x')` raises `RuntimeError` (same exception type propagates). Assert the temp directory created for the upload no longer exists — capture the `--file` path is not possible because `run_bytes` raised before returning, so instead monkeypatch `tempfile.TemporaryDirectory` to record the created directory, or check that `pathlib.Path(tempfile.gettempdir())` contains no leftover `tmp*` directory owned by this call. Prefer: wrap `tempfile.TemporaryDirectory` via `monkeypatch.setattr` to record the path, then assert `not recorded_path.exists()` after the raised call is caught. Reuse the same pattern for `download_bytes` cleanup-on-failure (`test_download_bytes_cleans_up_on_failure`).
- [x] 6.8 Add `test_existing_upload_and_download_unchanged`: assert `upload("i1","/p/f.txt")` still emits `("attachment","upload","i1","--file",<resolved>,"--output","json")` via `run_bytes`, and `download("a1","/out")` still emits `("attachment","download","a1","--output",<resolved>)` via `run_text`, with the same return behavior as before (regression guard). This mirrors the existing `manual:attachments.upload:canonical` / `manual:attachments.download:canonical` rows but lives here as an explicit lifecycle regression test.

## 7. Verification

- [ ] 7.1 `uv run pytest -m "not live"` green.
- [x] 7.2 `uv run mypy src` and `uv run mypy tests` green (the new `OperationCase` fields and `assert_result` signature change are typed; `transport_side_effect` is `Callable[..., object] | None`).
- [x] 7.3 `uv run ruff check` and `uv run ruff format --check` green.
- [x] 7.4 `uv run pytest tests/unit/resources/test_operations.py::test_discovered_public_methods` asserts the canonical method set grew to 119 and the updated counters (151 total / 119 canonical / 32 noncanonical / 37 generated / 114 manual) — no allowlist, exact invariants.
- [x] 7.5 `uv run pytest tests/unit/resources/test_operations.py::test_legacy_payload_bijection` green with 148 legacy fingerprints.
- [x] 7.6 `uv run openspec change validate attachment-bytes --strict` green.
