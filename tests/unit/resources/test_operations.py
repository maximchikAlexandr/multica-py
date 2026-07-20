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

from .cases import ARGV_CASES, DECODE_CASES, ArgvCase, DecodeCase

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
    "projects": ProjectResource,
    "project_resources": ProjectResourceCollection,
    "repositories": RepositoryResource,
    "runtimes": RuntimeResource,
    "setup": SetupResource,
    "skills": SkillResource,
    "skill_files": SkillFileResource,
    "squads": SquadResource,
    "users": UserResource,
    "workspaces": WorkspaceResource,
}


@pytest.mark.parametrize("case", ARGV_CASES, ids=lambda c: c.id or c.sdk_method)
def test_command_argv(
    case: ArgvCase,
    mock_transport: MagicMock,
    raw_result: MagicMock,
) -> None:
    transport = cast("CliTransport", mock_transport)
    config = ClientConfig()
    cls = _RESOURCE_CLASSES[case.resource_attr]
    resource = cls(transport, config)

    if case.transport_method == "run_bytes":
        mock_transport.run_bytes.return_value = raw_result(stdout=case.stdout)
    elif case.transport_method == "run_text":
        mock_transport.run_text.return_value = TextResult(
            text=case.stdout.decode("utf-8", errors="replace"),
            stderr="",
            exit_code=0,
        )
    else:
        mock_transport.spawn.return_value = MagicMock()

    method = getattr(resource, case.method)
    method(*case.args, **case.kwargs)

    if case.transport_method == "run_bytes":
        mock_transport.run_bytes.assert_called_once()
        call = mock_transport.run_bytes.call_args
        assert call.args == (case.expected_argv,)
        assert call.kwargs.get("stdin") == case.stdin
        assert call.kwargs.get("timeout") == case.timeout
    elif case.transport_method == "run_text":
        mock_transport.run_text.assert_called_once_with(case.expected_argv)
    else:
        mock_transport.spawn.assert_called_once_with(case.expected_argv)


@pytest.mark.parametrize("case", DECODE_CASES, ids=lambda c: c.id)
def test_decode(
    case: DecodeCase,
    mock_transport: MagicMock,
    raw_result: MagicMock,
) -> None:
    transport = cast("CliTransport", mock_transport)
    config = ClientConfig()
    cls = _RESOURCE_CLASSES[case.resource_attr]
    resource = cls(transport, config)

    mock_transport.run_bytes.return_value = raw_result(stdout=case.stdout)
    method = getattr(resource, case.method)
    result = method(*case.args)
    case.check(result)


KNOWN_ARGV_GAPS: frozenset[str] = frozenset()


def test_every_guard_eligible_operation_has_argv_case() -> None:
    covered = frozenset(c.sdk_method for c in ARGV_CASES)
    assert_manifest_coverage(
        guard_eligible_operations(),
        covered,
        KNOWN_ARGV_GAPS,
        missing_label="Missing argv cases for",
        stale_label="Stale KNOWN_ARGV_GAPS entries (have rows)",
    )
