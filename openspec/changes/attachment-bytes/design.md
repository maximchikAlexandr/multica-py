## Context

`AttachmentResource` (src/multica_py/resources/attachments.py:9) exposes three
methods today, all ungoverned (no contract binding/operation; only
`manual:` rows in `tests/cases/operations.py:757-775` and three
`LEGACY_ARGV_MIGRATION` entries `legacy:014/015/016`):

- `list(issue_id) -> tuple[AttachmentResult, ...]`
- `upload(issue_id, file_path) -> AttachmentResult` — builds
  `("attachment","upload",issue_id,"--file",<resolved path>)` and decodes
  JSON via `BaseResource._run_json_decode`.
- `download(attachment_id, output_path) -> None` — builds
  `("attachment","download",attachment_id,"--output",<resolved path>)` and
  calls `transport.run_text`.

The CLI surface is fixed and already covers the need; the gap is purely
Python-side convenience for callers that hold bytes in memory. Reported in
GitHub issue maximchikAlexandr/multica-py#5, which proposes
`upload_bytes()`/`download_bytes()` wrappers over the existing file-based
operations using `tempfile.TemporaryDirectory()`.

The repo has precedent for ungoverned convenience methods that are still
canonical public methods with `manual:` rows: `autopilots.get_run`
(tests/cases/operations.py:862) and `issues.search`
(tests/cases/operations.py:1729). Neither has a contract operation; both are
counted in the discovered canonical method set. This change follows the same
pattern: the byte methods are canonical public methods, get `manual:`
operation rows, but do not enter `contracts/sdk-contract.json` and do not
regenerate `approved_sdk.py`.

`AttachmentResult` (src/multica_py/models/system.py) is the existing decoded
return type of `upload()`; `download()` returns `None` and writes a file.

## Goals / Non-Goals

**Goals:**
- Let consumers upload in-memory bytes and download into memory without
  managing temp files themselves.
- Preserve the exact filename supplied to `upload_bytes` (the upstream
  `--file` path's basename is what the server records).
- Guarantee temp-file cleanup on both success and failure paths.
- Keep the existing file-based `upload()`/`download()` API byte-for-byte
  unchanged.

**Non-Goals:**
- A `download_to_directory()` convenience method. The GitHub issue lists it
  as optional follow-up; not required for the byte-oriented API.
- Streaming/chunked upload or download. The whole payload is materialized in
  memory (it already is in the caller's hands as `bytes`); a streaming API is
  a separate concern.
- Governing `attachment upload/download/list` in the approved contract. They
  stay ungoverned; the byte methods are wrappers, not new CLI operations.
- Changing `AttachmentResult` or adding new models. The byte methods return
  the existing types (`AttachmentResult` / `bytes`).

## Decisions

**1. `upload_bytes` writes `payload` to `<tmpdir>/<filename>` and calls
   `upload(issue_id, <path>)`.**
`upload()` already resolves the path via `pathlib.Path(file_path).resolve()`
and builds `--file <resolved>`. Writing to `<tmpdir>/<filename>` preserves the
user-supplied basename through resolution (the resolved path's final component
is `filename`). Using `filename` as the in-tmpdir leaf — not a random suffix —
is what makes "preserve the exact filename" a structural guarantee rather than
a post-hoc assertion. `tempfile.TemporaryDirectory()` as a context manager
removes the directory on both success and exception exit, satisfying the
cleanup-on-failure requirement with no explicit `try/finally`.

**2. `download_bytes` calls `download(attachment_id, <tmpdir>)` then reads the
   single file in the tmpdir.**
The upstream `attachment download <id> --output <path>` writes the attachment
to `<path>`. Pointing `--output` at the temp directory itself would not work
(`download()` resolves and passes the path verbatim); instead pass
`<tmpdir>/<attachment_id>` as the output path, then read that file. The
attachment id is a safe leaf name in a private tmpdir. If upstream naming
behavior ever changes to write a server-chosen filename into a directory,
`download_bytes` would need to find the single file in the tmpdir; for now the
explicit path is simplest and matches `download()`'s contract. Using a context
manager handles cleanup on both success and failure.

**3. Reuse `upload()`/`download()` verbatim; do not duplicate argv building.**
The byte methods call the existing methods by name, so any future change to
argv building (flag order, resolution, `--output json` injection via
`_run_json_decode`) applies automatically. This is the requirement in the
GitHub issue and keeps the diff minimal.

**4. New `manual:` canonical operation rows, not contract operations.**
Mirroring `autopilots.get_run` / `issues.search`: the byte methods are
ungoverned canonical public methods. Two new
`manual:attachments.upload_bytes:canonical` /
`manual:attachments.download_bytes:canonical` rows go in
`tests/cases/operations.py` next to the existing three attachment rows. They
are canonical (no `:variant:`), so the discovered canonical method set grows
117 → 119 and `test_discovered_public_methods` is updated accordingly. Two
`LEGACY_ARGV_MIGRATION` entries (`legacy:147`, `legacy:148`) and two legacy
fingerprints grow the bijection 146 → 148.

**5. `upload_bytes`/`download_bytes` operation rows assert the transport call
   structurally; a small general harness extension supports dynamic-path
   cases.**
The byte methods create a `tempfile.TemporaryDirectory()` per call, so the
`--file`/`--output` path in the argv they forward to `run_bytes`/`run_text`
is non-deterministic and cannot be pinned with the table's existing exact
`expected_argv` equality. Additionally `download_bytes` reads back the file
the transport writes, so a pure return-value mock (the table's default) cannot
exercise it end-to-end.

To keep the no-allowlist rule intact (every discovered public method has a
canonical row) without special-casing attachment methods, the operation-case
harness gains two small, general fields on `OperationCase`
(tests/cases/operations.py):
- `argv_check: str = "exact"` — `"exact"` (today's behavior) or `"none"` (skip
  the exact `call_args.args == (expected_argv,)` equality and rely on
  `assert_result` to verify the argv structurally). `"none"` is for cases where
  part of the argv is inherently dynamic (temp paths, generated tokens).
- `transport_side_effect: Callable[..., object] | None = None` — when set,
  `_configure_mock` (tests/unit/resources/test_operations.py) configures the
  mock's `run_bytes`/`run_text`/`spawn` with this side effect instead of a
  canned return value, so cases that need the transport to actually do
  something (write a file) can.

In `_assert_transport_call`: when `argv_check == "none"`, still assert the
transport method was called once, then defer argv-shape verification to
`case.assert_result`. When `argv_check == "exact"` (default), behavior is
unchanged.

The two byte-method canonical rows use `argv_check="none"`:
- `manual:attachments.upload_bytes:canonical` — `args=("i1","manifest.json",b'{"x":1}')`,
  `expected_argv=("attachment","upload","i1","--file","<dynamic>","--output","json")`
  (recorded as the prefix `("attachment","upload","i1","--file")` for the
  structural check), `stdout=_AR`, `assert_result` verifies the returned
  object is an `AttachmentResult` with `id=="a1"` and that the `run_bytes`
  call's argv starts with the prefix and ends with `("manifest.json","--output","json")`
  (filename preserved as the `--file` basename).
- `manual:attachments.download_bytes:canonical` — `args=("a1",)`,
  `expected_argv=("attachment","download","a1","--output","<dynamic>")` (prefix
  `("attachment","download","a1","--output")`), `transport_method="run_text"`,
  `transport_side_effect` writes `b'\x00\x01binary'` to the `--output` path
  passed in argv, `assert_result` verifies the returned value is exactly
  `b'\x00\x01binary'` and `run_text` was called once with an argv starting
  with the prefix.

The byte-payload round-trip, filename preservation, and temp-file cleanup
lifecycle (success and failure) are covered by dedicated tests in a new
`tests/unit/resources/test_attachments.py` that uses a fake transport writing
a real file (so the temp-file directory's existence is observable after the
call), keeping the table-driven transport assertions and the lifecycle
assertions in their right layers.

This harness extension is general (not attachment-specific): any future
convenience method with a dynamic argv component or a file-writing transport
reuses `argv_check="none"` / `transport_side_effect`.

## Risks / Trade-offs

- [Temp-file materialization for large payloads] → accepted. The caller
  already holds `bytes` in memory; writing it to a tmpdir and re-reading does
  not change the memory ceiling, only adds a brief disk copy. Streaming is a
  separate non-goal.
- [Filename collision in tmpdir] → not a real risk: each call gets its own
  `TemporaryDirectory`, so the supplied `filename` is the only file in it.
  No need to deduplicate.
- [`download_bytes` output-leaf assumption] → `download()` passes
  `--output <resolved path>` verbatim; the resolved path is
  `<tmpdir>/<attachment_id>`. If the upstream CLI ever changed to write a
  server-named file into a directory when `--output` is a directory, the
  explicit-file assumption would break. This is unlikely (the CLI treats
  `--output` as a file path today) and would surface immediately as a test
  failure in `test_attachments.py::test_download_bytes_round_trip`.
- [Counting the canonical method set] → the two new methods are public and
  canonical, so `discover_public_methods()` grows 117 → 119 and
  `test_discovered_public_methods` exact invariants are updated. Counter
  deltas are computed precisely in tasks.md.