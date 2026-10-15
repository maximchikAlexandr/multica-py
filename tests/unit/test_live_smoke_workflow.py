from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

WORKFLOW = Path(__file__).parents[2] / ".github" / "workflows" / "live-smoke.yml"


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _jq_filter(text: str, marker: str) -> str:
    return text.split(marker, 1)[1].split("' >/dev/null", 1)[0]


def _run_jq(filter_text: str, payload: object, **args: str) -> int:
    command = ["jq", "-e"]
    for name, value in args.items():
        command.extend(["--arg", name, value])
    command.append(filter_text)
    return subprocess.run(
        command,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    ).returncode


def test_environment_gate_rejects_wrong_reviewer_and_self_review() -> None:
    text = _workflow_text()
    marker = 'jq -e --arg expected "$EXPECTED_REVIEWER_ID" \''
    filter_text = _jq_filter(text, marker)
    protected = {
        "protection_rules": [
            {
                "type": "required_reviewers",
                "prevent_self_review": True,
                "reviewers": [{"reviewer": {"id": 17, "type": "User"}}],
            }
        ],
        "deployment_branch_policy": {"protected_branches": True},
    }

    assert _run_jq(filter_text, protected, expected="17") == 0
    assert _run_jq(filter_text, protected, expected="18") != 0

    rule_false = json.loads(json.dumps(protected))
    rule_false["protection_rules"][0]["prevent_self_review"] = False
    assert _run_jq(filter_text, rule_false, expected="17") != 0

    rule_missing = json.loads(json.dumps(protected))
    del rule_missing["protection_rules"][0]["prevent_self_review"]
    assert _run_jq(filter_text, rule_missing, expected="17") != 0

    root_true = json.loads(json.dumps(rule_missing))
    root_true["prevent_self_review"] = True
    assert _run_jq(filter_text, root_true, expected="17") != 0

    assert "EXPECTED_REVIEWER_ID: ${{ vars.MULTICA_LIVE_EXPECTED_REVIEWER_ID }}" in text
    assert 'test -n "$EXPECTED_REVIEWER_ID"' in text


def test_ruleset_gate_rejects_unrelated_required_deployment_environment() -> None:
    text = _workflow_text()
    marker = 'jq -e --arg branch "refs/heads/$DEFAULT_BRANCH" \''
    filter_text = _jq_filter(text, marker)
    valid = [
        {
            "enforcement": "active",
            "conditions": {"ref_name": {"include": ["refs/heads/main"]}},
            "rules": [
                {
                    "type": "required_deployments",
                    "parameters": {"required_deployment_environments": ["multica-live"]},
                }
            ],
        }
    ]
    ordered = json.loads(json.dumps(valid))
    ordered[0]["rules"][0]["parameters"]["required_deployment_environments"] = [
        "other-environment",
        "multica-live",
    ]
    object_entries = json.loads(json.dumps(valid))
    object_entries[0]["rules"][0]["parameters"]["required_deployment_environments"] = [
        {"name": "other-environment"},
        {"name": "multica-live"},
    ]
    unrelated = json.loads(json.dumps(valid))
    unrelated[0]["rules"][0]["parameters"]["required_deployment_environments"] = [
        "other-environment"
    ]

    assert _run_jq(filter_text, valid, branch="refs/heads/main") == 0
    assert _run_jq(filter_text, ordered, branch="refs/heads/main") == 0
    assert _run_jq(filter_text, object_entries, branch="refs/heads/main") == 0
    assert _run_jq(filter_text, unrelated, branch="refs/heads/main") != 0
    assert "required_deployment_environments" in text


def test_privileged_job_requires_runner_group_and_expected_labels() -> None:
    text = _workflow_text()
    assert re.search(
        r"runs-on:\n\s+group: multica-live\n\s+labels:\n"
        r"\s+- self-hosted\n\s+- multica-live",
        text,
    )


def test_artifact_action_is_immutably_pinned() -> None:
    text = _workflow_text()
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in text
    assert not re.search(r"actions/upload-artifact@v\d", text)


def test_interrupted_live_step_removes_raw_log_and_keeps_final_cleanup() -> None:
    text = _workflow_text()
    assert "trap cleanup_raw_log EXIT HUP INT TERM" in text
    assert 'rm -f -- "$raw_log"' in text
    assert "name: Remove runner-owned raw log and evidence" in text
    assert "if: always()" in text
