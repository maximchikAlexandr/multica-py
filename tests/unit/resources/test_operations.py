from __future__ import annotations

import pathlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import cast
from unittest.mock import MagicMock

import pytest

from multica_py._internal.specs import TextResult
from multica_py._internal.transport import CliTransport
from multica_py._internal.upstream_contract.generator.renderer import render_outputs
from multica_py._internal.upstream_contract.generator.validation import load_approved_contract_v2
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

_ROOT = pathlib.Path(__file__).resolve().parents[3]
_GENERATED_CASES_PATH = "tests/cases/generated/approved_sdk_cases.py"
_GENERATED_VALIDATORS_PATH = "src/multica_py/_generated/approved_sdk_validators.py"
_GENERATED_CONTRACT = load_approved_contract_v2(_ROOT / "contracts/sdk-contract.json")
_GENERATED_OUTPUTS = {
    str(output.path): output.content for output in render_outputs(_GENERATED_CONTRACT)
}
_GENERATED_VALIDATOR_NAMESPACE: dict[str, object] = {
    "__name__": "multica_py._generated.approved_sdk_validators"
}
exec(
    compile(
        _GENERATED_OUTPUTS[_GENERATED_VALIDATORS_PATH],
        "<generated approved_sdk_validators>",
        "exec",
    ),
    _GENERATED_VALIDATOR_NAMESPACE,
)

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


@dataclass(frozen=True)
class ValidationProbe:
    valid_value: str
    invalid_value: str
    valid_raises: bool = False
    invalid_raises: bool = True


@dataclass(frozen=True)
class GeneratedValidationCase:
    validator_id: str
    case_id: str
    function_name: str
    value: str
    raises_value_error: bool


_VALIDATOR_PROBES: dict[str, ValidationProbe] = {
    "normalize_optional_label": ValidationProbe("hello", "", invalid_raises=False),
    "validate_comment_cursor": ValidationProbe("cur_before", ""),
    "validate_description_input": ValidationProbe("hello", "", valid_raises=True),
    "validate_issue_sort": ValidationProbe("title", "invalid"),
    "validate_issue_status": ValidationProbe("todo", "invalid"),
    "validate_nonblank": ValidationProbe("hello", ""),
    "validate_nonnegative_limit": ValidationProbe("0", "-1"),
    "validate_positive_limit": ValidationProbe("1", "0"),
    "validate_project_description": ValidationProbe("hello", "", valid_raises=True),
    "validate_project_status": ValidationProbe("planned", "invalid"),
    "validate_project_update": ValidationProbe("hello", "", valid_raises=True),
    "validate_resource_update": ValidationProbe("hello", "", valid_raises=True),
    "validate_thread_cursor_limit": ValidationProbe("1", "0"),
}


def _generated_validation_cases() -> tuple[GeneratedValidationCase, ...]:
    namespace: dict[str, object] = {}
    exec(
        compile(
            _GENERATED_OUTPUTS[_GENERATED_CASES_PATH],
            "<generated approved_sdk_cases>",
            "exec",
        ),
        namespace,
    )
    raw_cases = namespace["CONSTRAINT_CASES"]
    assert isinstance(raw_cases, tuple)

    cases: list[GeneratedValidationCase] = []
    seen_case_ids: set[str] = set()
    for raw_case in raw_cases:
        validator_id = getattr(raw_case, "validator_id", None)
        case_id = getattr(raw_case, "case_id", None)
        valid = getattr(raw_case, "valid", None)
        assert isinstance(validator_id, str)
        assert isinstance(case_id, str)
        assert isinstance(valid, bool)
        if case_id in seen_case_ids:
            continue
        seen_case_ids.add(case_id)
        function_name = _GENERATED_CONTRACT.catalogs.validators[validator_id].rpartition(".")[-1]
        probe = _VALIDATOR_PROBES[function_name]
        cases.append(
            GeneratedValidationCase(
                validator_id=validator_id,
                case_id=case_id,
                function_name=function_name,
                value=probe.valid_value if valid else probe.invalid_value,
                raises_value_error=probe.valid_raises if valid else probe.invalid_raises,
            )
        )

    expected_ids = {
        evidence.positive_case_id
        for evidence in _GENERATED_CONTRACT.catalogs.validator_evidence.values()
    } | {
        evidence.negative_case_id
        for evidence in _GENERATED_CONTRACT.catalogs.validator_evidence.values()
    }
    assert {case.case_id for case in cases} == expected_ids
    return tuple(cases)


_GENERATED_VALIDATION_CASES = _generated_validation_cases()


@pytest.mark.parametrize(
    "case",
    _GENERATED_VALIDATION_CASES,
    ids=lambda case: case.case_id,
)
def test_generated_constraint(case: GeneratedValidationCase) -> None:
    validator = cast(
        "Callable[[str], None]",
        _GENERATED_VALIDATOR_NAMESPACE[case.function_name],
    )
    if case.raises_value_error:
        with pytest.raises(ValueError):
            validator(case.value)
    else:
        validator(case.value)
