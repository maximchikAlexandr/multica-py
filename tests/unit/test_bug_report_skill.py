from pathlib import Path


def test_skill_preserves_two_phase_review_contract() -> None:
    root = Path(__file__).resolve().parents[2] / ".agents" / "skills" / "multica-py-bug-report"
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    reviewer = (root / "reviewer-prompt.md").read_text(encoding="utf-8")

    assert "independent sub-agent" in skill
    assert "--skip-review" not in skill
    assert "--force" not in skill
    assert "reviewed_payload_sha256" in reviewer
    assert "changes_requested" in reviewer
