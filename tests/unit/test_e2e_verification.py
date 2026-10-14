from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import yaml

from multica_py.exceptions import NotFoundError
from multica_py.models.issues import IssuePropertyAssignment
from scripts.e2e import verify_multica_test as verifier

ROOT = Path(__file__).parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "live-smoke.yml"
SCRIPT = ROOT / "scripts" / "e2e" / "verify_multica_test.py"
_SHA = "a" * 40


@dataclass
class _FakeProject:
    id: str
    description: str = ""


@dataclass
class _FakeProperty:
    id: str
    archived: bool = False


@dataclass
class _FakeValue:
    value: tuple[str, ...]


class _FakeProjects:
    def __init__(self, *, cleanup_failure: bool = False) -> None:
        self.project = _FakeProject("project-1")
        self.deleted = False
        self.cleanup_failure = cleanup_failure

    def create(self, *, name: str) -> _FakeProject:
        return self.project

    def update(self, project_id: str, *, description: str) -> _FakeProject:
        assert project_id == self.project.id
        self.project.description = description
        return self.project

    def delete(self, project_id: str) -> None:
        assert project_id == self.project.id
        if self.cleanup_failure:
            raise RuntimeError("token=cleanup-secret")
        self.deleted = True

    def get(self, project_id: str) -> _FakeProject:
        assert project_id == self.project.id
        if self.deleted:
            raise NotFoundError("gone")
        return self.project


class _FakeProperties:
    def __init__(self, *, fail_create: bool = False) -> None:
        self.fail_create = fail_create
        self.properties: dict[str, _FakeProperty] = {}

    def create(self, *, name: str, property_type: str) -> _FakeProperty:
        if self.fail_create:
            raise RuntimeError('{"token":"property-secret"}')
        prop = _FakeProperty(f"property-{len(self.properties) + 1}")
        self.properties[prop.id] = prop
        return prop

    def archive(self, property_id: str) -> None:
        self.properties[property_id].archived = True

    def get(self, property_id: str) -> _FakeProperty:
        return self.properties[property_id]


class _FakeIssueProperties:
    def __init__(self, issues: _FakeIssues) -> None:
        self.issues = issues

    def set(self, issue_id: str, *, name: str, value: tuple[str, ...], property_type: str) -> None:
        assert property_type in {"multi_text", "multi_url"}
        self.issues.values[name] = _FakeValue(value)

    def list(self, issue_id: str) -> tuple[SimpleNamespace, ...]:
        return tuple(
            SimpleNamespace(name=name, value=value.value)
            for name, value in self.issues.values.items()
        )


class _FakeIssues:
    def __init__(self) -> None:
        self.issue = SimpleNamespace(id="issue-1", properties={})
        self.values: dict[str, _FakeValue] = {}
        self.properties = _FakeIssueProperties(self)

    def create(
        self,
        *,
        title: str,
        project_id: str,
        properties: tuple[IssuePropertyAssignment, ...],
    ) -> SimpleNamespace:
        for assignment in properties:
            self.values[assignment.reference] = _FakeValue(tuple(assignment.value))
        self.issue.properties = self.values
        return self.issue

    def get(self, issue_id: str, *, resolve_properties: bool) -> SimpleNamespace:
        assert issue_id == self.issue.id
        assert resolve_properties is True
        self.issue.properties = self.values
        return self.issue

    def list(
        self, *, project_id: str, property_filters: tuple[str, ...], limit: int
    ) -> SimpleNamespace:
        assert property_filters
        return SimpleNamespace(items=(self.issue,))


class _FakeClient:
    def __init__(
        self,
        *,
        cli_version: str = "0.6.2",
        fail_property_create: bool = False,
        cleanup_failure: bool = False,
    ) -> None:
        self.daemon = SimpleNamespace(status=lambda: SimpleNamespace(cli_version=cli_version))
        self.projects = _FakeProjects(cleanup_failure=cleanup_failure)
        self.properties = _FakeProperties(fail_create=fail_property_create)
        self.issues = _FakeIssues()

    def __enter__(self) -> _FakeClient:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def _patch_run(monkeypatch: pytest.MonkeyPatch, client: _FakeClient) -> None:
    monkeypatch.setattr(verifier, "_build_client", lambda: client)
    monkeypatch.setattr(verifier, "_current_sha", lambda: _SHA)


def _manifest(output: Path) -> dict[str, Any]:
    return json.loads((output / "manifest.json").read_text(encoding="utf-8"))


def _workflow_run(step_id: str) -> str:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    for step in workflow["jobs"]["authorize"]["steps"]:
        if step.get("id") == step_id:
            return step["run"]
    raise AssertionError(f"missing workflow step {step_id}")


def _run_authorization(
    tmp_path: Path,
    *,
    pr_payload: dict[str, Any],
    environment_payload: dict[str, Any] | None = None,
) -> tuple[subprocess.CompletedProcess[str], str]:
    fake_gh = tmp_path / "gh"
    fake_gh.write_text(
        "#!/bin/sh\n"
        'case "$2" in\n'
        "  */environments/multica-live) printf '%s' \"$FAKE_ENV_JSON\" ;;\n"
        "  */rulesets?includes_parents=true) printf '%s' \"$FAKE_RULESETS_JSON\" ;;\n"
        "  */pulls/*) printf '%s' \"$FAKE_PR_JSON\" ;;\n"
        "  *) exit 1 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    fake_gh.chmod(0o700)
    output = tmp_path / "github-output"
    environment = {
        **os.environ,
        "PATH": f"{tmp_path}:{os.environ['PATH']}",
        "GH_TOKEN": "test-token",
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_REPOSITORY": "acme/multica",
        "GITHUB_OUTPUT": str(output),
        "REPOSITORY": "acme/multica",
        "DEFAULT_BRANCH": "main",
        "WORKFLOW_REF": "acme/multica/.github/workflows/live-smoke.yml@refs/heads/main",
        "TRUSTED_WORKFLOW_REF": "refs/heads/main",
        "CANDIDATE_SHA": _SHA,
        "CANDIDATE_PR": "101",
        "FAKE_PR_JSON": json.dumps(pr_payload),
        "FAKE_ENV_JSON": json.dumps(
            environment_payload
            or {
                "protection_rules": [
                    {"type": "required_reviewers", "reviewers": [{"login": "reviewer"}]}
                ],
                "deployment_branch_policy": {"protected_branches": True},
            }
        ),
        "FAKE_RULESETS_JSON": json.dumps(
            [
                {
                    "enforcement": "active",
                    "conditions": {"ref_name": {"include": ["refs/heads/main"]}},
                    "rules": [{"type": "required_deployments"}],
                }
            ]
        ),
    }
    trust = subprocess.run(
        ["bash", "-c", _workflow_run("trust")],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    if trust.returncode != 0:
        return trust, ""
    resolved = subprocess.run(
        ["bash", "-c", _workflow_run("resolve")],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    return resolved, output.read_text(encoding="utf-8") if output.exists() else ""


def test_sanitize_redacts_serialized_and_header_credentials() -> None:
    values = (
        '{"token":"quoted-secret"}',
        '{"Authorization":"Bearer bearer-secret"}',
        "Authorization: Bearer header-secret",
        "https://user:password@example.test/private",
    )
    for value in values:
        redacted = verifier._sanitize(value)
        assert all(
            secret not in redacted
            for secret in ("quoted-secret", "bearer-secret", "header-secret", "password")
        )
        assert "example.test" not in redacted


def test_artifact_output_rejects_git_checkout(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="outside the Git checkout"):
        verifier._prepare_output(ROOT / ".artifacts" / "e2e")
    assert verifier._prepare_output(tmp_path / "e2e").is_dir()


def test_run_success_records_public_scenarios_cleanup_and_hashes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = _FakeClient()
    _patch_run(monkeypatch, client)

    assert verifier.run(tmp_path / "success") == 0

    manifest = _manifest(tmp_path / "success")
    assert manifest["sdk_sha"] == _SHA
    assert manifest["cli_observed_version"] == "0.6.2"
    assert manifest["final_exit_code"] == 0
    assert manifest["commands"]
    assert manifest["resource_ids"] == {
        "project_id": "project-1",
        "text_property_id": "property-1",
        "url_property_id": "property-2",
    }
    assert manifest["cleanup"]["state"] == "passed"
    assert set(manifest["artifact_hashes"]) == {"stdout.txt", "stderr.txt", "cleanup.json"}
    assert all(len(value) == 64 for value in manifest["artifact_hashes"].values())
    assert client.projects.deleted is True
    assert all(prop.archived for prop in client.properties.properties.values())


def test_run_partial_create_failure_cleans_created_project_and_redacts_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = _FakeClient(fail_property_create=True)
    _patch_run(monkeypatch, client)

    assert verifier.run(tmp_path / "partial") == 1

    output = tmp_path / "partial"
    manifest = _manifest(output)
    assert manifest["final_exit_code"] == 1
    assert manifest["resource_ids"] == {"project_id": "project-1"}
    assert client.projects.deleted is True
    assert "property-secret" not in (output / "stderr.txt").read_text(encoding="utf-8")


def test_run_cleanup_failure_is_failed_and_keeps_allowlisted_diagnostics(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = _FakeClient(cleanup_failure=True)
    _patch_run(monkeypatch, client)

    assert verifier.run(tmp_path / "cleanup-failure") == 1

    manifest = _manifest(tmp_path / "cleanup-failure")
    assert manifest["final_exit_code"] == 1
    assert manifest["cleanup"]["state"] == "failed"
    cleanup = json.loads(
        (tmp_path / "cleanup-failure" / "cleanup.json").read_text(encoding="utf-8")
    )
    assert "cleanup-secret" not in json.dumps(cleanup)
    assert cleanup["items"][0]["code"] == "cleanup_failed"


def test_run_wrong_cli_version_is_failed_before_resource_creation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = _FakeClient(cli_version="0.6.1")
    _patch_run(monkeypatch, client)

    assert verifier.run(tmp_path / "wrong-version") == 1

    manifest = _manifest(tmp_path / "wrong-version")
    assert manifest["cli_observed_version"] == "0.6.1"
    assert manifest["final_exit_code"] == 1
    assert manifest["resource_ids"] == {}
    assert '"code": "cli_version_mismatch"' in (
        tmp_path / "wrong-version" / "stderr.txt"
    ).read_text(encoding="utf-8")


def test_run_artifact_write_failure_does_not_print_exception_text(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    client = _FakeClient()
    _patch_run(monkeypatch, client)

    def fail_write(*args: object, **kwargs: object) -> None:
        raise RuntimeError("token=artifact-secret")

    monkeypatch.setattr(verifier, "_write_artifacts", fail_write)
    assert verifier.run(tmp_path / "artifact-failure") == 1
    assert "artifact-secret" not in capsys.readouterr().err


def test_walkthrough_uses_pinned_wrapper_and_strict_target() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert '_WRAPPER_EXECUTABLE = "multica-test"' in source
    assert "resolved_path = Path(wrapper_path).resolve()" in source
    assert "executable=str(resolved_path)" in source
    assert "compatibility=CompatibilityPolicy.strict" in source
    assert "profile=" not in source
    assert "server_url=" not in source
    assert "workspace_id=" not in source
    assert "MULTICA_TOKEN" not in source


def test_live_workflow_authorizes_trusted_exact_head_and_sanitized_graph() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "github.event.repository.default_branch" in workflow
    assert "github.workflow_ref" in workflow
    assert "MULTICA_LIVE_TRUSTED_WORKFLOW_REF" in workflow
    assert "environments/multica-live" in workflow
    assert "required_reviewers" in workflow
    assert "required_deployments" in workflow
    assert "head.repo.full_name" in workflow
    assert 'head_sha" != "$CANDIDATE_SHA"' in workflow
    assert "needs: authorize" in workflow
    assert "persist-credentials: false" in workflow
    assert workflow.index("Revalidate current PR head before candidate setup") < workflow.index(
        "actions/checkout@"
    )
    assert workflow.index("Check immutable checkout before setup") < workflow.index("setup-uv")
    assert "version --output json" in workflow
    assert "observed_version" in workflow
    assert 'test "$observed_version" = "0.6.2"' in workflow
    assert "if: always()" in workflow
    assert "RUNNER_TEMP/multica-live-" in workflow
    assert "Upload sanitized evidence allowlist" in workflow
    assert "manifest.json" in workflow and "cleanup.txt" in workflow
    assert ".artifacts/live-smoke" not in workflow
    assert "persisted-credentials" not in workflow
    assert "secrets." not in workflow


@pytest.mark.parametrize(
    ("state", "head_repo", "head_sha"),
    [
        ("closed", "acme/multica", _SHA),
        ("open", "fork/multica", _SHA),
        ("open", "acme/multica", "b" * 40),
    ],
)
def test_live_workflow_rejects_invalid_pr_head_cases(
    tmp_path: Path, state: str, head_repo: str, head_sha: str
) -> None:
    result, output = _run_authorization(
        tmp_path,
        pr_payload={"state": state, "head": {"repo": {"full_name": head_repo}, "sha": head_sha}},
    )
    assert result.returncode != 0
    assert output == ""


def test_live_workflow_accepts_current_same_repository_pr_head(tmp_path: Path) -> None:
    result, output = _run_authorization(
        tmp_path,
        pr_payload={
            "state": "open",
            "head": {"repo": {"full_name": "acme/multica"}, "sha": _SHA},
        },
    )
    assert result.returncode == 0
    assert "pr_number=101" in output
    assert f"head_sha={_SHA}" in output


def test_live_workflow_fails_closed_without_protected_environment(tmp_path: Path) -> None:
    result, output = _run_authorization(
        tmp_path,
        pr_payload={
            "state": "open",
            "head": {"repo": {"full_name": "acme/multica"}, "sha": _SHA},
        },
        environment_payload={"protection_rules": [], "deployment_branch_policy": None},
    )
    assert result.returncode != 0
    assert output == ""
