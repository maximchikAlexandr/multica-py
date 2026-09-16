## ADDED Requirements

### Requirement: Comment deletion uses target keep-replies semantics
For `issues.comments.delete`, the SDK SHALL retain the existing public method
and CLI argv while approving Multica `0.4.44` transport semantics: target CLI
SHALL call `DELETE /api/comments/<id>/keep-replies`, preserve descendants as
tombstones, and treat a pre-support server's plain-text 404 as failure. The SDK
SHALL use the centralized diagnostic classifier and SHALL perform no fallback,
retry, or direct request to the old destructive endpoint.

#### Scenario: Target deletion preserves replies
- **WHEN** CLI `0.4.44` deletes a comment with descendants
- **THEN** the action succeeds through the keep-replies route and subsequent thread decoding retains the tombstone and every reply

#### Scenario: Pre-support server fails closed
- **WHEN** CLI `0.4.44` receives the reviewed plain-text 404 because the keep-replies route is unavailable
- **THEN** the SDK raises the centralized approved command error and issues no destructive fallback request

#### Scenario: Delete signature and argv remain stable
- **WHEN** a caller constructs eager or command-form comment deletion
- **THEN** the Python signature and complete argv remain `comment_id` and `issue comment delete <comment-id>` with no SDK-level route argument

#### Scenario: Malformed successful output remains a decode failure
- **WHEN** a nominally successful delete command returns output that violates the approved action-result shape
- **THEN** decoding raises `OutputShapeError` and does not classify or retry it as the reviewed 404 path
