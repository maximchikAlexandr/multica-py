from __future__ import annotations

from typing import cast
from unittest.mock import MagicMock

import pytest

from multica_py._internal.specs import TextResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.resources.agent_skills import AgentSkillResource
from multica_py.resources.agents import AgentResource
from multica_py.resources.attachments import AttachmentResource
from multica_py.resources.auth import AuthResource
from multica_py.resources.autopilot_triggers import AutopilotTriggerResource
from multica_py.resources.autopilots import AutopilotResource
from multica_py.resources.configuration import ConfigurationResource
from multica_py.resources.daemon import DaemonResource
from multica_py.resources.issue_comments import IssueCommentResource
from multica_py.resources.issue_labels import IssueLabelResource
from multica_py.resources.issue_metadata import IssueMetadataResource
from multica_py.resources.issue_subscribers import IssueSubscriberResource
from multica_py.resources.issues import IssueResource
from multica_py.resources.labels import LabelResource
from multica_py.resources.maintenance import MaintenanceResource
from multica_py.resources.project_resources import ProjectResourceCollection
from multica_py.resources.projects import ProjectResource
from multica_py.resources.repositories import RepositoryResource
from multica_py.resources.runtimes import RuntimeResource
from multica_py.resources.setup import SetupResource
from multica_py.resources.skill_files import SkillFileResource
from multica_py.resources.skills import SkillResource
from multica_py.resources.squads import SquadResource
from multica_py.resources.users import UserResource
from multica_py.resources.workspaces import WorkspaceResource
from tests._manifest_coverage import assert_manifest_coverage
from tests._manifest_support import guard_eligible_operations
from tests.cases.argv_data import _NESTED_RESOURCE_ATTRS
from tests.cases.models import OperationCase
from tests.cases.operations import OPERATION_CASES

_RESOURCE_CLASSES = {
    "agent_skills": AgentSkillResource,
    "agents": AgentResource,
    "attachments": AttachmentResource,
    "auth": AuthResource,
    "autopilot_triggers": AutopilotTriggerResource,
    "autopilots": AutopilotResource,
    "configuration": ConfigurationResource,
    "daemon": DaemonResource,
    "issue_comments": IssueCommentResource,
    "issue_labels": IssueLabelResource,
    "issue_metadata": IssueMetadataResource,
    "issue_subscribers": IssueSubscriberResource,
    "issues": IssueResource,
    "labels": LabelResource,
    "maintenance": MaintenanceResource,
    "project_resources": ProjectResourceCollection,
    "projects": ProjectResource,
    "repositories": RepositoryResource,
    "runtimes": RuntimeResource,
    "setup": SetupResource,
    "skill_files": SkillFileResource,
    "skills": SkillResource,
    "squads": SquadResource,
    "users": UserResource,
    "workspaces": WorkspaceResource,
}


def _resource_attr(sdk_method: str) -> str:
    parts = sdk_method.split(".")
    if len(parts) >= 3:
        nested = _NESTED_RESOURCE_ATTRS.get((parts[0], parts[1]))
        if nested is not None:
            return nested
    return parts[0]


def _invoke_argv(mock_transport: MagicMock, case: object) -> None:
    import datetime

    from multica_py._internal.specs import RawCommandResult

    assert isinstance(case, OperationCase)
    if case.expected_call is None:
        pytest.skip(f"{case.operation_id}: no expected_call case")
    call = case.expected_call
    method_name = case.sdk_method.rsplit(".", 1)[-1]
    if call.method == "spawn":
        mock_transport.spawn.return_value = MagicMock()
    elif call.method == "run_bytes":
        mock_transport.run_bytes.return_value = RawCommandResult(
            argv=tuple(call.args),
            exit_code=0,
            stdout=case.response.stdout if case.response is not None else b"{}",
            stderr=b"",
            duration=datetime.timedelta(),
        )
    elif call.method == "run_text":
        mock_transport.run_text.return_value = TextResult(
            text=(case.response.stdout if case.response is not None else b"{}").decode(
                "utf-8", errors="replace"
            ),
            stderr="",
            exit_code=0,
        )

    transport = cast("CliTransport", mock_transport)
    config = ClientConfig()
    resource_attr = _resource_attr(case.sdk_method)
    cls = _RESOURCE_CLASSES[resource_attr]
    resource = cls(transport, config)

    method = getattr(resource, method_name)
    if not all(isinstance(a, (str, int, float, bool, type(None))) for a in case.args):
        pytest.skip(f"{case.operation_id}: args contain non-scalar public types")
    method(*case.args, **dict(case.kwargs))

    if call.method == "run_bytes":
        mock_transport.run_bytes.assert_called_once()
        called = mock_transport.run_bytes.call_args
        assert called.args == (tuple(call.args),)
        assert called.kwargs.get("stdin") == call.stdin
        assert called.kwargs.get("timeout") == call.timeout
    elif call.method == "run_text":
        mock_transport.run_text.assert_called_once_with(tuple(call.args))
    else:
        mock_transport.spawn.assert_called_once_with(tuple(call.args))


KNOWN_ARGV_GAPS: frozenset[str] = frozenset()


@pytest.mark.parametrize("case", list(OPERATION_CASES), ids=lambda c: c.operation_id)
def test_operation_argv(case: object, mock_transport: MagicMock) -> None:
    _invoke_argv(mock_transport, case)


def test_every_guard_eligible_operation_has_argv_case() -> None:
    covered = frozenset(c.operation_id for c in OPERATION_CASES if c.expected_call is not None)
    assert_manifest_coverage(
        guard_eligible_operations(),
        covered,
        KNOWN_ARGV_GAPS,
        missing_label="Missing argv cases for",
        stale_label="Stale KNOWN_ARGV_GAPS entries (have rows)",
    )
