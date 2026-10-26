from __future__ import annotations

import json
import pathlib
from collections.abc import Callable
from dataclasses import dataclass

import pytest

from multica_py._internal.decoders import decode_json
from multica_py._internal.wire_models import (
    _project_from_wire,
    _ProjectResourceRecordWire,
    _ProjectWire,
    project_resource_from_wire,
)
from multica_py.exceptions import OutputShapeError
from multica_py.models.issue_activity import IssueUsage
from multica_py.models.project_resources import (
    GithubRepoResourceRef,
    LocalDirectoryResourceRef,
    ProjectResourceRecord,
)


@dataclass(frozen=True)
class ProjectResourceDecodeCase:
    """One project resource wire decode scenario."""

    id: str
    payload: dict[str, object]
    label: str | None


@dataclass(frozen=True)
class RejectCase:
    """One model validation rejection scenario."""

    id: str
    factory: Callable[[], object]
    match: str


_PROJECT_RESOURCE_DECODE_CASES = (
    ProjectResourceDecodeCase(
        "with-label",
        {
            "id": "res_001",
            "project_id": "pr_001",
            "resource_type": "local_directory",
            "resource_ref": {
                "local_path": "/tmp/sandbox",
                "daemon_id": "daemon-001",
                "label": "main",
            },
        },
        "main",
    ),
    ProjectResourceDecodeCase(
        "without-label",
        {
            "id": "res_001",
            "project_id": "pr_001",
            "resource_type": "local_directory",
            "resource_ref": {
                "local_path": "/tmp/sandbox",
                "daemon_id": "daemon-001",
            },
        },
        None,
    ),
)


@pytest.mark.parametrize("case", _PROJECT_RESOURCE_DECODE_CASES, ids=lambda case: case.id)
def test_decode_local_directory_record(case: ProjectResourceDecodeCase) -> None:
    record = project_resource_from_wire(
        decode_json(json.dumps(case.payload).encode(), _ProjectResourceRecordWire)
    )
    assert record.resource_type == "local_directory"
    assert isinstance(record.resource_ref, LocalDirectoryResourceRef)
    assert record.resource_ref.label == case.label
    assert record.resource_ref.local_path == str(pathlib.Path("/tmp/sandbox").resolve())


def test_discriminator_preserves_github_resource_type() -> None:
    payload = {
        "id": "res_001",
        "project_id": "pr_001",
        "resource_type": "github_repo",
        "resource_ref": {
            "url": "https://github.com/acme/repo",
            "ref": "main",
        },
    }
    wire = decode_json(json.dumps(payload).encode(), _ProjectResourceRecordWire)
    record = project_resource_from_wire(wire)
    assert record.resource_ref == GithubRepoResourceRef(
        url="https://github.com/acme/repo", ref="main"
    )


_REJECT_CASES = (
    RejectCase(
        "empty-record-id",
        lambda: ProjectResourceRecord(
            id="",
            project_id="pr_001",
            resource_type="local_directory",
            resource_ref=LocalDirectoryResourceRef(
                local_path="/tmp/sandbox",
                daemon_id="daemon-001",
            ),
        ),
        "id must be non-empty",
    ),
    RejectCase(
        "empty-project-id",
        lambda: ProjectResourceRecord(
            id="res_001",
            project_id="",
            resource_type="local_directory",
            resource_ref=LocalDirectoryResourceRef(
                local_path="/tmp/sandbox",
                daemon_id="daemon-001",
            ),
        ),
        "project_id must be non-empty",
    ),
    RejectCase(
        "relative-local-path",
        lambda: LocalDirectoryResourceRef(local_path="relative/path", daemon_id="daemon-001"),
        "local_path must be an absolute path",
    ),
    RejectCase(
        "empty-reference-daemon-id",
        lambda: LocalDirectoryResourceRef(local_path="/tmp/sandbox", daemon_id=" "),
        "daemon_id must be non-empty",
    ),
)


@pytest.mark.parametrize("case", _REJECT_CASES, ids=lambda case: case.id)
def test_model_validation_rejects(case: RejectCase) -> None:
    with pytest.raises(ValueError, match=case.match):
        case.factory()


@pytest.mark.parametrize(
    ("payload", "cost_usd"),
    [
        (b'{"total_runs": 1, "cost_usd": 0.05}', 0.05),
        (b'{"total_runs": 1}', None),
    ],
    ids=("with-cost", "without-cost"),
)
def test_issue_usage_decodes_cost_usd(payload: bytes, cost_usd: float | None) -> None:
    usage = decode_json(payload, IssueUsage)
    assert usage.cost_usd == cost_usd


@pytest.mark.parametrize(
    ("workflow_field", "expected"),
    (
        (None, None),
        (('"workflow_id":null',), None),
        (
            ('"workflow_id":"123e4567-e89b-12d3-a456-426614174000"',),
            "123e4567-e89b-12d3-a456-426614174000",
        ),
    ),
    ids=("legacy-omitted", "explicit-null", "uuid"),
)
def test_project_workflow_id_decodes_legacy_null_and_uuid(
    workflow_field: tuple[str] | None, expected: str | None
) -> None:
    suffix = "" if workflow_field is None else "," + workflow_field[0]
    wire = decode_json(
        f'{{"id":"p1","title":"Project","status":"planned"{suffix}}}'.encode(),
        _ProjectWire,
    )

    assert _project_from_wire(wire).workflow_id == expected


@pytest.mark.parametrize("workflow_id", ("bad", ""), ids=("malformed", "empty"))
def test_project_workflow_id_rejects_malformed_uuid(workflow_id: str) -> None:
    payload = (
        '{"id":"p1","title":"Project","status":"planned",'
        f'"workflow_id":{json.dumps(workflow_id)}}}'
    ).encode()
    with pytest.raises(OutputShapeError, match="workflow_id"):
        decode_json(
            payload,
            _ProjectWire,
        )
