from __future__ import annotations

import pathlib
import re
import shutil
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"

# Pinned commit SHAs for known GitHub Actions. Each value MUST be a real,
# resolvable 40-char hex SHA in the upstream repo. We allow either:
# - the canonical pinned SHA below, or
# - the major version tag if the workflow file contains a comment explaining
#   the exception.
PINNED_ACTIONS: dict[str, str] = {
    "actions/checkout": "b4ffde65f46336ab88eb53be808477a3936bae11",
    "astral-sh/setup-uv": "ecd24dd710f2fb0dca1693a67af11fc4a5c5ec84",
}

_SHA_RE = re.compile(r"@[0-9a-f]{40}")
_TAG_RE = re.compile(r"@v\d+(\.\d+)?$")
_HEX40_RE = re.compile(r"^[0-9a-f]{40}$")


def _iter_uses() -> list[tuple[pathlib.Path, str, str]]:
    found: list[tuple[pathlib.Path, str, str]] = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if "uses:" not in line:
                continue
            _, _, value = line.partition("uses:")
            value = value.strip()
            if not value:
                continue
            found.append((path, line, value))
    return found


def test_actions_pinned_to_sha_or_tag_with_explanation() -> None:
    for path, line, value in _iter_uses():
        if "@" not in value:
            continue
        action, _, ref = value.partition("@")
        if action not in PINNED_ACTIONS:
            continue
        expected_sha = PINNED_ACTIONS[action]
        if _SHA_RE.match(f"@{ref}"):
            assert ref == expected_sha, (
                f"{path.name}: {action} pinned to {ref!r} but whitelist expects {expected_sha!r}"
            )
            continue
        if _TAG_RE.match(f"@{ref}"):
            # Major-version tag is allowed for first-party actions when a
            # repository policy comment is present anywhere in the workflow
            # file. The observer workflow (the new file) must pin SHAs.
            if path.name == "upstream-contract-observer.yml":
                raise AssertionError(
                    f"{path.name}: observer workflow must pin actions by full SHA, got {ref!r}"
                )
            if "major-version-tag-allowed" in path.read_text(encoding="utf-8"):
                continue
            raise AssertionError(
                f"{path.name}: major-version tag {ref!r} used without repository policy comment"
            )
        raise AssertionError(f"{path.name}: unexpected action ref {ref!r}")


def test_pinned_action_shas_are_well_formed() -> None:
    for action, sha in PINNED_ACTIONS.items():
        assert _HEX40_RE.match(sha), f"{action}: SHA {sha!r} is not 40 lowercase hex chars"
        assert set(sha) != {"0"}, f"{action}: SHA {sha!r} is all zeros"
        # Reject obvious repeating-pattern placeholders (e.g. "0bf2e9c0bf2e9c...").
        assert len(set(sha)) >= 8, f"{action}: SHA {sha!r} looks like a placeholder"


def test_pinned_action_shas_resolve_upstream() -> None:
    if shutil.which("gh") is None:
        return
    for action, sha in PINNED_ACTIONS.items():
        result = subprocess.run(
            ["gh", "api", f"repos/{action}/commits/{sha}", "--jq", ".sha"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            continue
        resolved = result.stdout.strip()
        assert resolved == sha, (
            f"{action}: SHA {sha!r} does not resolve to itself (got {resolved!r})"
        )


def test_workflow_files_exist() -> None:
    expected = {
        "ci.yml",
        "upstream-contract-observer.yml",
    }
    actual = {path.name for path in WORKFLOWS.glob("*.yml")}
    assert expected.issubset(actual)
