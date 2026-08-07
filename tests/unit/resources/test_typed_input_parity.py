from __future__ import annotations

import inspect
import typing
from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.enums import AutopilotExecutionMode, MetadataValueType
from multica_py.models.autopilots import (
    AutopilotTriggerCreate,
    AutopilotTriggerUpdate,
    AutopilotUpdateRequest,
)
from multica_py.models.issue_activity import (
    MetadataListRequest,
    MetadataPredicate,
    MetadataSetRequest,
)
from multica_py.models.labels import LabelUpdateRequest
from multica_py.resources.autopilots import Autopilot, AutopilotResource
from multica_py.resources.issue_metadata import IssueMetadataResource
from multica_py.resources.labels import LabelResource


def _transport() -> MagicMock:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    return transport


def _autopilot(client: object | None = None) -> Autopilot:
    return Autopilot(
        id="a1",
        workspace_id="w1",
        title="AP",
        assignee_type="member",
        assignee_id="u1",
        status="active",
        execution_mode="create_issue",
        created_by_type="member",
        created_by_id="u1",
        _client=client,
    )


def test_metadata_query_object_and_direct_commands_have_identical_plans() -> None:
    resource = IssueMetadataResource(_transport(), ClientConfig())
    request = MetadataListRequest(
        issue_id="i1",
        predicates=(MetadataPredicate(key="priority", value=3),),
        cursor="next",
        limit=5,
    )

    assert (
        resource.query_command(request).commands
        == resource.query_command(
            issue_id="i1",
            predicates=(MetadataPredicate(key="priority", value=3),),
            cursor="next",
            limit=5,
        ).commands
    )


def test_metadata_set_typed_object_and_direct_commands_have_identical_plans() -> None:
    resource = IssueMetadataResource(_transport(), ClientConfig())
    request = MetadataSetRequest(
        issue_id="i1", key="enabled", value=True, value_type=MetadataValueType.boolean
    )

    assert (
        resource.set_typed_command(request).commands
        == resource.set_typed_command(
            issue_id="i1", key="enabled", value=True, value_type=MetadataValueType.boolean
        ).commands
    )


@pytest.mark.parametrize(
    ("method", "request_value", "kwargs"),
    (
        (
            "query_command",
            MetadataListRequest(issue_id="i1"),
            {"issue_id": "i1"},
        ),
        (
            "set_typed_command",
            MetadataSetRequest(issue_id="i1", key="k", value="v"),
            {"issue_id": "i1", "key": "k", "value": "v"},
        ),
    ),
)
def test_metadata_mixed_input_is_rejected_before_transport(
    method: str, request_value: object, kwargs: dict[str, object]
) -> None:
    transport = _transport()
    resource = IssueMetadataResource(transport, ClientConfig())

    with pytest.raises(
        TypeError, match=r"Pass either a request object or keyword arguments, not both\."
    ):
        getattr(resource, method)(request_value, **kwargs)
    transport.run_bytes.assert_not_called()
    transport.run_text.assert_not_called()


def test_top_level_trigger_object_and_direct_commands_have_identical_plans() -> None:
    resource = AutopilotResource(_transport(), ClientConfig())
    add = AutopilotTriggerCreate(title="Webhook", kind="webhook")
    update = AutopilotTriggerUpdate(title="Changed")

    assert (
        resource.trigger_add_command("a1", add).commands
        == resource.trigger_add_command("a1", title="Webhook", kind="webhook").commands
    )
    assert (
        resource.trigger_update_command("a1", "tr1", update).commands
        == resource.trigger_update_command("a1", "tr1", title="Changed").commands
    )


def test_bound_trigger_object_and_direct_commands_share_cache_plan() -> None:
    transport = _transport()
    resource = AutopilotResource(transport, ClientConfig())
    client = MagicMock()
    client.autopilots = resource
    entity = _autopilot(client)

    assert entity.trigger_add_command(AutopilotTriggerCreate(title="T", kind="k")).commands == (
        entity.trigger_add_command(title="T", kind="k").commands
    )
    assert entity.trigger_update_command("tr1", AutopilotTriggerUpdate(title="T")).commands == (
        entity.trigger_update_command("tr1", title="T").commands
    )
    transport.run_bytes.assert_not_called()


def test_autopilot_update_object_and_direct_commands_have_identical_plans() -> None:
    resource = AutopilotResource(_transport(), ClientConfig())
    request = AutopilotUpdateRequest(
        title="New",
        execution_mode=AutopilotExecutionMode.create_issue,
        subscribers=("u1", "u2"),
    )

    assert (
        resource.update_command("a1", request).commands
        == resource.update_command(
            "a1",
            title="New",
            execution_mode=AutopilotExecutionMode.create_issue,
            subscribers=("u1", "u2"),
        ).commands
    )


def test_label_update_object_and_direct_commands_have_identical_plans() -> None:
    resource = LabelResource(_transport(), ClientConfig())
    request = LabelUpdateRequest(name="feature", color="blue")

    assert (
        resource.update_command("label1", request).commands
        == resource.update_command("label1", name="feature", color="blue").commands
    )


@pytest.mark.parametrize(
    ("resource_cls", "method", "request_cls"),
    (
        (IssueMetadataResource, "query", MetadataListRequest),
        (IssueMetadataResource, "set_typed", MetadataSetRequest),
        (AutopilotResource, "trigger_add", AutopilotTriggerCreate),
        (AutopilotResource, "trigger_update", AutopilotTriggerUpdate),
        (AutopilotResource, "update", AutopilotUpdateRequest),
        (LabelResource, "update", LabelUpdateRequest),
    ),
)
def test_direct_overloads_list_exact_request_fields(
    resource_cls: type, method: str, request_cls: type
) -> None:
    overloads = typing.get_overloads(getattr(resource_cls, method))
    direct = next(
        overload
        for overload in overloads
        if any(
            parameter.kind == inspect.Parameter.KEYWORD_ONLY
            for parameter in inspect.signature(overload).parameters.values()
        )
    )
    params = inspect.signature(direct).parameters.values()
    keyword_names = {
        parameter.name for parameter in params if parameter.kind == inspect.Parameter.KEYWORD_ONLY
    }
    assert keyword_names == {field.name for field in msgspec.structs.fields(request_cls)}
