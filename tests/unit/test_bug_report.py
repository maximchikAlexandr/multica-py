from __future__ import annotations

import json
from pathlib import Path

import pytest

from multica_py import bug_report


def _filled_report(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    replacements = {
        "<describe the minimal steps that trigger the problem>": "Run `python example.py`.",
        "<what happens>": "The command exits with code 1.",
        "<what should happen, and the basis for that expectation>": (
            "It exits with code 0, as documented in docs/api.md."
        ),
        "<observable facts: commands, outputs, file paths, exit codes>": (
            "`python example.py` exits 1 with `invalid response`."
        ),
        "<separate guesses from facts>": "The decoder may reject an optional field.",
        "<the smallest change that addresses the root cause, with explicit bounds>": (
            "Accept the documented optional field in the existing decoder."
        ),
        "<verifiable criterion>": "The documented payload decodes successfully.",
        "<the smallest test that fails if the fix regresses>": (
            "a decoder unit test with the documented payload"
        ),
        "<applicable SDK rules, contracts, or consequences of the proposed change>": (
            "Preserve strict typing and the current public API."
        ),
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
    return text


@pytest.fixture(autouse=True)
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MULTICA_PY_HOME", str(tmp_path / ".multica-py"))


def test_init_creates_private_two_phase_draft() -> None:
    draft = bug_report.init_report("Decoder rejects valid payload")
    directory = Path(draft.directory)

    assert directory.stat().st_mode & 0o777 == 0o700
    assert (directory / "report.md").stat().st_mode & 0o777 == 0o600
    assert (directory / "metadata.json").stat().st_mode & 0o777 == 0o600
    assert (directory / "reviews").is_dir()
    metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["repository"] == "maximchikAlexandr/multica-py"
    assert metadata["labels"] == ["bug"]


def test_preview_requires_filled_template_then_exposes_review_hash() -> None:
    draft = bug_report.init_report("Decoder rejects valid payload")
    report_path = Path(draft.directory) / "report.md"

    assert (
        "report.md has unfilled template placeholders"
        in bug_report.preview_report(draft.report_id).blockers
    )

    _filled_report(report_path)
    preview = bug_report.preview_report(draft.report_id)
    assert preview.blockers == ()
    assert preview.approved is False
    assert preview.next_review_path and preview.next_review_path.endswith("reviews/1.json")


def test_submit_requires_current_independent_approval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    draft = bug_report.init_report("Decoder rejects valid payload")
    directory = Path(draft.directory)
    _filled_report(directory / "report.md")
    preview = bug_report.preview_report(draft.report_id)

    with pytest.raises(bug_report.BugReportError, match="approval"):
        bug_report.submit_report(draft.report_id)

    review = {
        "round": 1,
        "reviewed_payload_sha256": preview.payload_sha256,
        "reviewer_session_ref": "review-session",
        "verdict": "approved",
        "findings": "Reproduction and regression scenario are actionable.",
    }
    (directory / "reviews" / "1.json").write_text(json.dumps(review), encoding="utf-8")

    calls: list[tuple[tuple[str, ...], str | None]] = []

    def run_gh(arguments: tuple[str, ...], *, stdin: str | None = None) -> str:
        calls.append((arguments, stdin))
        if arguments[:2] == ("issue", "list"):
            return "[]"
        return "https://github.com/maximchikAlexandr/multica-py/issues/42\n"

    monkeypatch.setattr(bug_report, "_run_gh", run_gh)
    assert bug_report.submit_report(draft.report_id).endswith("/issues/42")
    assert calls[1][0][-2:] == ("--body-file", "-")
    assert calls[1][1] and calls[1][1].startswith(f"REPORT_ID: {draft.report_id}")


def test_report_edit_invalidates_approval() -> None:
    draft = bug_report.init_report("Decoder rejects valid payload")
    directory = Path(draft.directory)
    _filled_report(directory / "report.md")
    preview = bug_report.preview_report(draft.report_id)
    review = {
        "round": 1,
        "reviewed_payload_sha256": preview.payload_sha256,
        "reviewer_session_ref": "review-session",
        "verdict": "approved",
        "findings": "Approved.",
    }
    (directory / "reviews" / "1.json").write_text(json.dumps(review), encoding="utf-8")
    (directory / "report.md").write_text(
        (directory / "report.md").read_text(encoding="utf-8") + "\nNew fact.\n",
        encoding="utf-8",
    )

    preview = bug_report.preview_report(draft.report_id)
    assert preview.approved is False
    assert "latest approval is stale for the current payload" in preview.blockers


def test_preview_rejects_non_contiguous_review_rounds() -> None:
    draft = bug_report.init_report("Decoder rejects valid payload")
    directory = Path(draft.directory)
    _filled_report(directory / "report.md")
    review = {
        "round": 2,
        "reviewed_payload_sha256": "a" * 64,
        "reviewer_session_ref": "review-session",
        "verdict": "changes_requested",
        "findings": "Missing first round.",
    }
    (directory / "reviews" / "2.json").write_text(json.dumps(review), encoding="utf-8")

    with pytest.raises(bug_report.BugReportError, match="contiguous"):
        bug_report.preview_report(draft.report_id)


def test_submit_reports_missing_draft_cleanly() -> None:
    with pytest.raises(bug_report.BugReportError, match="not found"):
        bug_report.submit_report("00000000-0000-0000-0000-000000000000")


@pytest.mark.parametrize(
    "secret",
    [
        "token=super-secret-value",
        "ghp_abcdefghijklmnopqrstuvwxyz123456",
        "-----BEGIN PRIVATE KEY-----",
    ],
)
def test_preview_rejects_secret_like_content(secret: str) -> None:
    draft = bug_report.init_report("Secret leak")
    report_path = Path(draft.directory) / "report.md"
    _filled_report(report_path)
    report_path.write_text(report_path.read_text(encoding="utf-8") + secret, encoding="utf-8")

    assert (
        "report.md contains a secret-like pattern"
        in bug_report.preview_report(draft.report_id).blockers
    )
