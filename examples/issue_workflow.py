"""Idempotent issue metadata/comments and a guarded status transition."""

from multica_py import ClientConfig, IssueStatus, MulticaClient


class UnexpectedIssueStateError(RuntimeError):
    """The issue changed since the caller chose its transition."""


def record_result_once(
    client: MulticaClient,
    issue_id: str,
    operation_key: str,
    message: str,
) -> None:
    issue = client.issues.get(issue_id)

    if issue.metadata.all().get("automation.operation") != operation_key:
        issue.set_metadata("automation.operation", operation_key)

    marker = f"[automation:{operation_key}]"
    if not any(comment.body.startswith(marker) for comment in issue.comments.all()):
        issue.add_comment(f"{marker} {message}")


def move_if_current(
    client: MulticaClient,
    issue_id: str,
    expected: IssueStatus,
    target: IssueStatus,
) -> None:
    issue = client.issues.get(issue_id)
    if issue.status is not expected:
        raise UnexpectedIssueStateError(
            f"issue {issue_id} changed: expected {expected.value}, got {issue.status.value}"
        )
    client.issues.set_status(issue_id, target)


if __name__ == "__main__":
    sdk = MulticaClient(ClientConfig())
    record_result_once(sdk, "issue_456", "run_789", "processing completed")
    move_if_current(sdk, "issue_456", IssueStatus.in_progress, IssueStatus.in_review)
