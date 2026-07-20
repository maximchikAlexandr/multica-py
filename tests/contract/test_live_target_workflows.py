from __future__ import annotations

import pathlib

from scripts.resolve_multica_target import load_pinned_target, workflow_backend_digest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TARGET_FILE = ROOT / "contracts" / "multica-live-target.toml"
PINNED_WORKFLOWS = (
    ROOT / ".github" / "workflows" / "ci.yml",
    ROOT / ".github" / "workflows" / "live-extended.yml",
    ROOT / ".github" / "workflows" / "live-opencode-canary.yml",
)


def test_live_workflows_resolve_target_from_contract() -> None:
    target = load_pinned_target(TARGET_FILE)
    digest = workflow_backend_digest(target)
    for workflow_path in PINNED_WORKFLOWS:
        text = workflow_path.read_text(encoding="utf-8")
        assert "load_pinned_target(Path('contracts/multica-live-target.toml'))" in text
        assert "workflow_backend_digest" in text
        assert target.upstream_commit not in text
        assert digest not in text


def test_live_workflows_do_not_pin_stale_multica_refs() -> None:
    target = load_pinned_target(TARGET_FILE)
    stale_commit = "4416313f8f7f801df8b7f5072087da8a6502a89c"
    stale_digest = "sha256:d8a50acac1eb674093b0e9de4afc656328ac6b37fc641f1fb4b256547f1ffe3b"
    for workflow_path in PINNED_WORKFLOWS:
        text = workflow_path.read_text(encoding="utf-8")
        assert stale_commit not in text
        assert stale_digest not in text
        assert (
            target.upstream_commit not in text or "multica_target.outputs.upstream_commit" in text
        )
