from __future__ import annotations

import json
import pathlib
from collections.abc import Callable
from dataclasses import dataclass

import pytest

from multica_py._internal.decoders import decode_json
from multica_py._internal.wire_models import ProjectResourceRecordWire, project_resource_from_wire
from multica_py.models.issue_activity import IssueUsage
from multica_py.models.issues import IssueCreateRequest, IssueUpdateRequest
from multica_py.models.project_resources import (
    LocalDirectoryResourceRef,
    ProjectResourceAddLocalDirectoryRequest,
    ProjectResourceRecord,
)


@dataclass(frozen=True)
class DecodeCase:
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


_DECODE_CASES = (
    DecodeCase(
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
    DecodeCase(
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


@pytest.mark.parametrize("case", _DECODE_CASES, ids=lambda case: case.id)
def test_decode_local_directory_record(case: DecodeCase) -> None:
    record = project_resource_from_wire(
        decode_json(json.dumps(case.payload).encode(), ProjectResourceRecordWire)
    )
    assert record.resource_type == "local_directory"
    assert record.resource_ref.label == case.label
    assert record.resource_ref.local_path == str(pathlib.Path("/tmp/sandbox").resolve())


def test_discriminator_rejects_unknown_resource_type() -> None:
    payload = {
        "id": "res_001",
        "project_id": "pr_001",
        "resource_type": "github_repo",
        "resource_ref": {
            "local_path": "/tmp/sandbox",
            "daemon_id": "daemon-001",
        },
    }
    wire = decode_json(json.dumps(payload).encode(), ProjectResourceRecordWire)
    with pytest.raises(Exception, match="Unsupported resource_type"):
        project_resource_from_wire(wire)


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
        "empty-daemon-id",
        lambda: ProjectResourceAddLocalDirectoryRequest(local_path="/tmp/sandbox", daemon_id=""),
        "daemon_id must be non-empty",
    ),
    RejectCase(
        "issue-create-empty-project-id",
        lambda: IssueCreateRequest(title="Test", project_id=""),
        "project_id must be non-empty",
    ),
    RejectCase(
        "issue-update-empty-project-id",
        lambda: IssueUpdateRequest(project_id=""),
        "project_id must be non-empty",
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
