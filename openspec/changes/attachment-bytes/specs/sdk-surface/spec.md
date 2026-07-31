## ADDED Requirements

### Requirement: Attachment byte-oriented upload and download
The SDK SHALL expose `AttachmentResource.upload_bytes(issue_id, filename, payload) -> AttachmentResult` and `AttachmentResource.download_bytes(attachment_id) -> bytes` as convenience wrappers over the existing file-based `upload()` and `download()` methods. The byte methods SHALL NOT duplicate CLI command-building logic, SHALL accept `bytes` (not base64), SHALL preserve the exact filename supplied to `upload_bytes`, SHALL clean up temporary files automatically on both success and failure, SHALL correctly support empty and binary content, SHALL raise the same SDK exception types as the underlying file-based methods, and SHALL leave the existing `upload()` and `download()` behavior unchanged.

#### Scenario: upload_bytes preserves the supplied filename
- **WHEN** `upload_bytes("i1", "manifest.json", b'{"x":1}')` is called
- **THEN** the underlying `upload()` is called with a path whose final component is exactly `manifest.json`, and the returned `AttachmentResult` is the one decoded by `upload()`.

#### Scenario: download_bytes returns the file content as bytes
- **WHEN** `download_bytes("a1")` is called and the underlying `download()` writes a file containing `b'\x00\x01binary'`
- **THEN** the returned value is exactly `b'\x00\x01binary'`.

#### Scenario: Empty payload uploads and returns the decoded result
- **WHEN** `upload_bytes("i1", "empty.bin", b'')` is called
- **THEN** `upload()` is called with a path to a zero-length file named `empty.bin` and the decoded `AttachmentResult` is returned.

#### Scenario: Empty attachment downloads as empty bytes
- **WHEN** `download_bytes("a1")` is called and the underlying `download()` writes a zero-length file
- **THEN** the returned value is `b''`.

#### Scenario: Temporary files are removed after success
- **WHEN** `upload_bytes` or `download_bytes` completes successfully
- **THEN** the temporary directory created for the operation no longer exists on the filesystem after the call returns.

#### Scenario: Temporary files are removed when the underlying CLI operation fails
- **WHEN** the underlying `upload()` or `download()` raises an exception
- **THEN** the exception propagates to the caller (same SDK exception type) and the temporary directory created for the operation no longer exists on the filesystem.

#### Scenario: Existing upload and download behavior is unchanged
- **WHEN** `upload(issue_id, file_path)` or `download(attachment_id, output_path)` is called
- **THEN** the argv and return behavior are identical to before this change (no regression in the file-based API).

## MODIFIED Requirements

### Requirement: Public resource surface
The SDK MUST retain every public resource method present in the canonical operation table.
#### Scenario: Public methods have canonical rows
- **WHEN** a public resource method exists
- **THEN** one canonical operation row covers it.
<!-- Source IDs: 001:FR-018–FR-031,005:FR-019–FR-025 -->
<!-- Modified by attachment-bytes: `attachments.upload_bytes` and
     `attachments.download_bytes` are added as canonical public methods with
     `manual:attachments.upload_bytes:canonical` and
     `manual:attachments.download_bytes:canonical` rows; the discovered
     canonical method set grows from 117 to 119. The byte methods are
     ungoverned convenience wrappers (no contract operation), mirroring
     `autopilots.get_run` and `issues.search`. -->