"""Local two-phase bug-report drafts for the multica-py GitHub repository."""

from __future__ import annotations

import fcntl
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import subprocess
import uuid
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal, cast

Repository = "maximchikAlexandr/multica-py"
Labels = ("bug",)
ReportKind = Literal["bug", "enhancement", "tech-debt"]
Verdict = Literal["approved", "changes_requested"]

_MAX_REPORT_BYTES = 256 * 1024
_MAX_REVIEW_ROUNDS = 3
_REPORT_ID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_REQUIRED_SECTIONS = (
    "## Context",
    "## Reproduction or scenario",
    "## Actual vs expected behaviour",
    "## Evidence",
    "## Minimal sufficient solution direction",
    "## Acceptance criteria and regression scenario",
    "## Project constraints and change consequences",
)
_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"(?i)\b(?:password|token|secret)\s*[:=]\s*\S+"),
    re.compile(r"(?i)\bauthorization:\s*(?:bearer|basic)\s+\S+"),
)


class BugReportError(RuntimeError):
    """Raised when a draft is invalid or cannot be published safely."""


@dataclass(frozen=True, slots=True)
class Draft:
    report_id: str
    title: str
    kind: ReportKind
    directory: str


@dataclass(frozen=True, slots=True)
class Review:
    round: int
    reviewed_payload_sha256: str
    reviewer_session_ref: str | None
    verdict: Verdict
    findings: str


@dataclass(frozen=True, slots=True)
class Preview:
    report_id: str
    title: str
    repository: str
    labels: tuple[str, ...]
    payload_sha256: str
    next_review_path: str | None
    approved: bool
    blockers: tuple[str, ...]
    issue_url: str | None


def reports_root(*, create: bool = False) -> Path:
    user_root = Path(os.environ.get("MULTICA_PY_HOME", "~/.multica-py")).expanduser()
    root = user_root / "bug-reports"
    if root.is_symlink():
        raise BugReportError("bug-reports root must not be a symlink")
    if create:
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(root, 0o700)
    return root


def _draft_directory(report_id: str) -> Path:
    if not _REPORT_ID.fullmatch(report_id):
        raise BugReportError("report_id must be a complete UUID")
    directory = reports_root() / report_id
    if directory.is_symlink():
        raise BugReportError("bug-report draft must not be a symlink")
    return directory


def _write_private(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    os.chmod(path, 0o600)


def _package_version() -> str:
    try:
        return importlib.metadata.version("multica-py")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def _template(title: str, kind: ReportKind) -> str:
    return f"""# {title}

Kind: {kind}

## Context

- multica-py version: {_package_version()}
- OS: {platform.platform()}
- Python: {platform.python_version()}

## Reproduction or scenario

<describe the minimal steps that trigger the problem>

## Actual vs expected behaviour

Actual:

<what happens>

Expected:

<what should happen, and the basis for that expectation>

## Evidence

Facts:

<observable facts: commands, outputs, file paths, exit codes>

Hypotheses:

<separate guesses from facts>

## Minimal sufficient solution direction

<the smallest change that addresses the root cause, with explicit bounds>

## Acceptance criteria and regression scenario

- <verifiable criterion>
- Regression: <the smallest test that fails if the fix regresses>

## Project constraints and change consequences

<applicable SDK rules, contracts, or consequences of the proposed change>
"""


def init_report(title: str, kind: ReportKind = "bug") -> Draft:
    title = title.strip()
    if not title or "\n" in title or "\r" in title:
        raise BugReportError("title must be one non-empty line")
    if kind not in ("bug", "enhancement", "tech-debt"):
        raise BugReportError("kind must be bug, enhancement, or tech-debt")

    report_id = str(uuid.uuid4())
    directory = reports_root(create=True) / report_id
    directory.mkdir(mode=0o700)
    (directory / "reviews").mkdir(mode=0o700)
    metadata = {
        "report_id": report_id,
        "title": title,
        "kind": kind,
        "repository": Repository,
        "labels": list(Labels),
    }
    _write_private(
        directory / "metadata.json",
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _write_private(directory / "report.md", _template(title, kind))
    return Draft(report_id, title, kind, str(directory))


def _read_metadata(directory: Path) -> dict[str, object]:
    path = directory / "metadata.json"
    try:
        value = cast("object", json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as error:
        raise BugReportError(f"metadata.json is unreadable: {error}") from error
    if not isinstance(value, dict):
        raise BugReportError("metadata.json must contain a JSON object")
    return cast("dict[str, object]", value)


def _read_reviews(directory: Path) -> list[Review]:
    reviews: list[Review] = []
    for round_number in range(1, _MAX_REVIEW_ROUNDS + 1):
        path = directory / "reviews" / f"{round_number}.json"
        if not path.exists():
            continue
        if round_number != len(reviews) + 1:
            raise BugReportError("review rounds must be contiguous")
        try:
            value = cast("object", json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as error:
            raise BugReportError(f"reviews/{round_number}.json is unreadable: {error}") from error
        if not isinstance(value, dict):
            raise BugReportError(f"reviews/{round_number}.json must be a JSON object")
        verdict = value.get("verdict")
        if verdict not in ("approved", "changes_requested"):
            raise BugReportError(
                f"reviews/{round_number}.json verdict must be approved or changes_requested"
            )
        review = Review(
            round=int(value.get("round", 0)),
            reviewed_payload_sha256=str(value.get("reviewed_payload_sha256", "")),
            reviewer_session_ref=(
                str(value["reviewer_session_ref"])
                if value.get("reviewer_session_ref") is not None
                else None
            ),
            verdict=cast("Verdict", verdict),
            findings=str(value.get("findings", "")),
        )
        if review.round != round_number or not review.reviewed_payload_sha256:
            raise BugReportError(f"reviews/{round_number}.json has invalid fields")
        reviews.append(review)
    return reviews


def _read_report(directory: Path) -> str:
    path = directory / "report.md"
    try:
        data = path.read_bytes()
    except OSError as error:
        raise BugReportError(f"report.md is unreadable: {error}") from error
    if len(data) > _MAX_REPORT_BYTES:
        raise BugReportError(f"report.md exceeds {_MAX_REPORT_BYTES} bytes")
    return data.decode("utf-8")


def _body(report_id: str, report: str) -> str:
    marker = f"REPORT_ID: {report_id}\n\n"
    return report if report.startswith(marker) else marker + report


def _payload_hash(title: str, body: str) -> str:
    material = "\n".join((title, body, Repository, ",".join(Labels))).encode()
    return hashlib.sha256(material).hexdigest()


def preview_report(report_id: str) -> Preview:
    directory = _draft_directory(report_id)
    if not directory.is_dir():
        raise BugReportError(f"bug-report draft not found: {report_id}")
    metadata = _read_metadata(directory)
    title = metadata.get("title")
    if not isinstance(title, str) or not title.strip():
        raise BugReportError("metadata.json title is required")
    if metadata.get("repository") != Repository or metadata.get("labels") != list(Labels):
        raise BugReportError("metadata.json repository and labels are immutable")

    report = _read_report(directory)
    blockers = [
        f"report.md is missing required section: {section}"
        for section in _REQUIRED_SECTIONS
        if section not in report
    ]
    if re.search(r"<[^>\n]{3,}>", report):
        blockers.append("report.md has unfilled template placeholders")
    if any(pattern.search(report) for pattern in _SECRET_PATTERNS):
        blockers.append("report.md contains a secret-like pattern")

    body = _body(report_id, report)
    payload_hash = _payload_hash(title, body)
    reviews = _read_reviews(directory)
    latest = reviews[-1] if reviews else None
    refusals = sum(review.verdict == "changes_requested" for review in reviews)
    approved = bool(
        latest and latest.verdict == "approved" and latest.reviewed_payload_sha256 == payload_hash
    )
    if latest and latest.verdict == "approved" and not approved:
        blockers.append("latest approval is stale for the current payload")
    if refusals >= _MAX_REVIEW_ROUNDS and not approved:
        blockers.append("maximum review rounds reached")

    next_review_path = None
    if not approved and len(reviews) < _MAX_REVIEW_ROUNDS:
        next_review_path = str(directory / "reviews" / f"{len(reviews) + 1}.json")
    issue_url = metadata.get("issue_url")
    return Preview(
        report_id=report_id,
        title=title,
        repository=Repository,
        labels=Labels,
        payload_sha256=payload_hash,
        next_review_path=next_review_path,
        approved=approved,
        blockers=tuple(blockers),
        issue_url=issue_url if isinstance(issue_url, str) else None,
    )


def _run_gh(arguments: Sequence[str], *, stdin: str | None = None) -> str:
    result = subprocess.run(
        ["gh", *arguments],
        input=stdin,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _find_existing(report_id: str) -> str | None:
    output = _run_gh(
        (
            "issue",
            "list",
            "--repo",
            Repository,
            "--search",
            f'"REPORT_ID: {report_id}" in:body',
            "--json",
            "url",
            "--limit",
            "1",
        )
    )
    try:
        values = cast("object", json.loads(output))
    except json.JSONDecodeError as error:
        raise BugReportError("gh returned invalid JSON while checking duplicates") from error
    if not isinstance(values, list) or not values:
        return None
    value = values[0]
    if not isinstance(value, dict) or not isinstance(value.get("url"), str):
        raise BugReportError("gh returned an invalid duplicate search result")
    return cast("str", value["url"])


def _save_issue_url(directory: Path, metadata: Mapping[str, object], issue_url: str) -> None:
    updated = dict(metadata)
    updated["issue_url"] = issue_url
    _write_private(
        directory / "metadata.json",
        json.dumps(updated, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


@contextmanager
def _submit_lock(directory: Path) -> Iterator[None]:
    lock = directory / ".submit.lock"
    with lock.open("w", encoding="utf-8") as handle:
        os.chmod(lock, 0o600)
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def submit_report(report_id: str) -> str:
    directory = _draft_directory(report_id)
    if not directory.is_dir():
        raise BugReportError(f"bug-report draft not found: {report_id}")
    with _submit_lock(directory):
        preview = preview_report(report_id)
        if preview.issue_url:
            return preview.issue_url
        if preview.blockers:
            raise BugReportError("; ".join(preview.blockers))
        if not preview.approved:
            raise BugReportError("an independent approval for the current payload is required")

        metadata = _read_metadata(directory)
        existing = _find_existing(report_id)
        if existing:
            _save_issue_url(directory, metadata, existing)
            return existing

        report = _read_report(directory)
        output = _run_gh(
            (
                "issue",
                "create",
                "--repo",
                Repository,
                "--title",
                preview.title,
                "--label",
                Labels[0],
                "--body-file",
                "-",
            ),
            stdin=_body(report_id, report),
        )
        match = re.search(r"https://github\.com/[^\s]+/issues/\d+", output)
        if not match:
            existing = _find_existing(report_id)
            if not existing:
                raise BugReportError("GitHub issue may exist, but its URL could not be recovered")
            issue_url = existing
        else:
            issue_url = match.group(0)
        _save_issue_url(directory, metadata, issue_url)
        return issue_url


def as_json(value: Draft | Preview) -> str:
    """Serialize command results deterministically for automation."""

    return json.dumps(
        cast("dict[str, object]", asdict(value)),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )


__all__ = [
    "BugReportError",
    "Draft",
    "Preview",
    "ReportKind",
    "as_json",
    "init_report",
    "preview_report",
    "reports_root",
    "submit_report",
]
