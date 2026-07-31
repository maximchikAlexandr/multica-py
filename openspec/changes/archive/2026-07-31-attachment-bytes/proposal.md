## Why

`AttachmentResource` (src/multica_py/resources/attachments.py:13,19) only
exposes file-path based `upload(issue_id, file_path)` and
`download(attachment_id, output_path)`. Consumers that already hold bytes in
memory (generated manifests, downloaded documents) must spill to a temp file,
call the SDK, then clean up — logic that is easy to duplicate across
integrations and reported in GitHub issue maximchikAlexandr/multica-py#5. The
SDK should encapsulate the temp-file dance once.

## What Changes

- Add `AttachmentResource.upload_bytes(issue_id, filename, payload) -> AttachmentResult`
  that writes `payload: bytes` to a `tempfile.TemporaryDirectory`, preserves
  the supplied `filename`, calls the existing `upload()` (which builds the
  `attachment upload <issue_id> --file <path>` argv unchanged), and returns the
  decoded `AttachmentResult`. Cleanup is automatic via the context manager.
- Add `AttachmentResource.download_bytes(attachment_id) -> bytes` that calls
  the existing `download()` into a `tempfile.TemporaryDirectory`, reads the
  single downloaded file back as `bytes`, and returns it. Cleanup is automatic.
- No new Multica CLI flags or commands; no new contract bindings or
  operations. The byte methods are pure Python-side wrappers over the existing
  file-based `upload()`/`download()` and reuse their argv-building, so no CLI
  command-building logic is duplicated.
- Add `manual:attachments.upload_bytes:canonical` and
  `manual:attachments.download_bytes:canonical` operation rows (ungoverned,
  mirroring the existing `manual:attachments.list/upload/download:canonical`
  rows) plus two `LEGACY_ARGV_MIGRATION` entries and two legacy fingerprints,
  growing the bijection 146 → 148. The two new public methods are canonical,
  so the discovered canonical method set grows 117 → 119.
- Tests: extend the existing table-driven `tests/cases/operations.py` row set
  and add focused tests in `tests/unit/resources/test_attachments.py` for the
  temp-file lifecycle (success cleanup, failure cleanup, empty payload, binary
  content, filename preservation, bytes round-trip). No new test files beyond
  the one new `test_attachments.py` unit module.

## Capabilities

### New Capabilities
<!-- None: this change widens the existing attachment surface; it does not
     introduce a new capability boundary. -->

### Modified Capabilities
- `sdk-surface`: adds the requirement "Attachment byte-oriented upload and
  download" covering `upload_bytes` and `download_bytes` as convenience
  wrappers that preserve the existing file-based API, reuse `upload()`/`
  download()`, accept `bytes`, preserve the supplied filename, clean up
  temp files automatically (success and failure), and raise the same SDK
  exception types as the underlying methods.

## Impact

- `src/multica_py/resources/attachments.py`: two new methods, `tempfile` and
  `pathlib` imports.
- `tests/cases/operations.py`: two new `manual:` canonical rows; two new
  `LEGACY_ARGV_MIGRATION` entries; two small general fields on `OperationCase`
  (`argv_check`, `transport_side_effect`) to support dynamic-path / file-
  writing cases.
- `tests/cases/legacy_payloads.py`: two new fingerprints.
- `tests/unit/resources/test_operations.py`: `_configure_mock` and
  `_assert_transport_call` honor the two new fields; counter assertions
  updated (canonical 117 → 119, total 149 → 151, manual 112 → 114,
  noncanonical and generated unchanged).
- `tests/unit/resources/test_operations.py::test_legacy_payload_bijection`:
  `range(1, 147)` → `range(1, 149)` and fingerprint count 146 → 148.
- New `tests/unit/resources/test_attachments.py` for the temp-file lifecycle.
- No contract (`contracts/sdk-contract.json`) changes: the byte methods are
  ungoverned convenience wrappers, like `autopilots.get_run` and
  `issues.search`.
- No generated output (`approved_sdk.py`) changes.