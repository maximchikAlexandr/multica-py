from __future__ import annotations

import json
from typing import cast
from unittest.mock import MagicMock

import pytest

from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.exceptions import OutputShapeError
from multica_py.resources.issue_properties import IssuePropertyResource
from multica_py.resources.properties import PropertyResource
from multica_py.sentinels import Unset
from tests.unit.resources._factories import command_result
from tests.unit.resources.property_cases import (
    PROPERTY_ACCEPTED_CASES,
    PROPERTY_INVALID_CASES,
    AcceptedPropertyInputCase,
    PropertyInputCase,
)


def test_create_rejects_options_for_actor_types() -> None:
    resource = PropertyResource(CliTransport(ClientConfig()), ClientConfig())
    with pytest.raises(ValueError, match="options_values are not supported"):
        resource.create_command(
            name="Owner",
            property_type="actor",
            options_values=("member:abc",),
        )
    with pytest.raises(ValueError, match="options_values are not supported"):
        resource.create_command(
            name="Reviewers",
            property_type="multi_actor",
            options_values=("member:abc",),
        )


def test_create_emits_repeatable_option_flags_for_select() -> None:
    resource = PropertyResource(CliTransport(ClientConfig()), ClientConfig())
    command = resource.create_command(
        name="Status",
        property_type="select",
        options_values=("Ready", "Blocked:#ff0000"),
    )
    assert command._plan.steps[0].argv == (
        "property",
        "create",
        "--name",
        "Status",
        "--type",
        "select",
        "--option",
        "Ready",
        "--option",
        "Blocked:#ff0000",
        "--output",
        "json",
    )


def test_update_icon_presence_emits_clear_flag() -> None:
    resource = PropertyResource(CliTransport(ClientConfig()), ClientConfig())
    omitted = resource.update_command("prop_001")
    cleared = resource.update_command("prop_001", icon="")
    assert "--icon" not in omitted._plan.steps[0].argv
    assert cleared._plan.steps[0].argv == (
        "property",
        "update",
        "prop_001",
        "--icon",
        "",
        "--output",
        "json",
    )


def test_issue_property_set_passes_actor_value_through_argv() -> None:
    resource = IssuePropertyResource(CliTransport(ClientConfig()), ClientConfig())
    command = resource.set_command(
        "iss_001",
        name="Reviewer",
        value="member:019f0000-0000-7000-8000-000000000001",
    )
    assert command._plan.steps[0].argv == (
        "issue",
        "property",
        "set",
        "iss_001",
        "--name",
        "Reviewer",
        "--value",
        "member:019f0000-0000-7000-8000-000000000001",
        "--output",
        "json",
    )


def test_issue_property_set_encodes_discriminated_list_values(mock_transport: MagicMock) -> None:
    resource = IssuePropertyResource(mock_transport, ClientConfig())
    command = resource.set_command(
        "iss_001",
        name="Tags",
        value=("alpha", "beta", "alpha"),
        property_type="multi_text",
    )
    assert command._plan.steps[0].argv == (
        "issue",
        "property",
        "set",
        "iss_001",
        "--name",
        "Tags",
        "--value",
        '["alpha","beta"]',
        "--output",
        "json",
    )


@pytest.mark.parametrize("case", PROPERTY_ACCEPTED_CASES, ids=lambda case: case.id)
def test_issue_property_set_accepts_property_boundaries(
    case: AcceptedPropertyInputCase, mock_transport: MagicMock
) -> None:
    resource = IssuePropertyResource(mock_transport, ClientConfig())
    command = resource.set_command(
        "iss_001",
        name="Tags",
        value=cast("str | tuple[str, ...]", case.value),
        property_type=case.property_type,  # type: ignore[arg-type]
    )
    assert command._plan.steps[0].argv == (
        "issue",
        "property",
        "set",
        "iss_001",
        "--name",
        "Tags",
        "--value",
        case.encoded,
        "--output",
        "json",
    )


@pytest.mark.parametrize("case", PROPERTY_INVALID_CASES, ids=lambda case: case.id)
def test_issue_property_set_rejects_invalid_values_before_io(
    case: PropertyInputCase, mock_transport: MagicMock
) -> None:
    resource = IssuePropertyResource(mock_transport, ClientConfig())
    with pytest.raises(case.error_type, match=case.message):
        resource.set(
            "iss_001",
            name="Tags",
            value=cast("str | tuple[str, ...]", case.value),
            property_type=case.property_type,  # type: ignore[arg-type]
        )
    mock_transport.run_bytes.assert_not_called()


def test_issue_property_set_accepts_discriminated_string_forms(mock_transport: MagicMock) -> None:
    resource = IssuePropertyResource(mock_transport, ClientConfig())
    comma = resource.set_command(
        "iss_001", name="Tags", value="alpha,beta,alpha", property_type="multi_text"
    )
    json_array = resource.set_command(
        "iss_001",
        name="Tags",
        value='["alpha,beta","[beta]"]',
        property_type="multi_text",
    )
    assert comma._plan.steps[0].argv == (
        "issue",
        "property",
        "set",
        "iss_001",
        "--name",
        "Tags",
        "--value",
        '["alpha","beta"]',
        "--output",
        "json",
    )
    assert json_array._plan.steps[0].argv == (
        "issue",
        "property",
        "set",
        "iss_001",
        "--name",
        "Tags",
        "--value",
        '["alpha,beta","[beta]"]',
        "--output",
        "json",
    )


@pytest.mark.parametrize(
    "value",
    ("scalar", {"nested": "value"}, None, ["ok", 1]),
    ids=("scalar", "object", "null", "non-string-item"),
)
def test_issue_property_list_rejects_malformed_list_values(
    value: object, mock_transport: MagicMock
) -> None:
    mock_transport.run_bytes.return_value = command_result(
        json.dumps(
            [
                {
                    "property_id": "prop_001",
                    "name": "Tags",
                    "type": "multi_text",
                    "value": value,
                }
            ]
        ).encode()
    )
    resource = IssuePropertyResource(mock_transport, ClientConfig())
    with pytest.raises(OutputShapeError, match="array of strings"):
        resource.list("iss_001")


def test_issue_property_unset_omits_value_flag() -> None:
    resource = IssuePropertyResource(CliTransport(ClientConfig()), ClientConfig())
    command = resource.unset_command("iss_001", name="Reviewer")
    argv = command._plan.steps[0].argv
    assert "--name" in argv
    assert "--value" not in argv


def test_issue_property_create_update_do_not_accept_unset_options() -> None:
    resource = PropertyResource(CliTransport(ClientConfig()), ClientConfig())
    command = resource.create_command(name="Title", property_type="text", description=Unset)
    assert "--description" not in command._plan.steps[0].argv
