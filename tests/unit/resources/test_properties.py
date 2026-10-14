from __future__ import annotations

import pytest

from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.exceptions import OutputShapeError
from multica_py.resources.issue_properties import IssuePropertyResource
from multica_py.resources.properties import PropertyResource
from multica_py.sentinels import Unset
from tests.unit.resources._factories import make_transport


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


def test_create_rejects_nonempty_options_for_list_property_types() -> None:
    resource = PropertyResource(CliTransport(ClientConfig()), ClientConfig())
    for property_type in ("multi_text", "multi_url"):
        with pytest.raises(ValueError, match="options_values are not supported"):
            resource.create_command(
                name="Tags",
                property_type=property_type,
                options_values=("ignored",),
            )


def test_issue_property_set_encodes_list_values_stably() -> None:
    resource = IssuePropertyResource(CliTransport(ClientConfig()), ClientConfig())
    command = resource.set_command("iss_001", name="Tags", value=("alpha", "beta", "alpha"))
    assert command._plan.steps[0].argv[-4:] == (
        "--value",
        '["alpha","beta"]',
        "--output",
        "json",
    )


def test_issue_property_list_decodes_multi_values_as_immutable_tuple() -> None:
    transport = make_transport(
        stdout=[
            {
                "property_id": "p1",
                "name": "Tags",
                "type": "multi_text",
                "value": ["alpha", "beta"],
            }
        ]
    )
    result = IssuePropertyResource(transport, ClientConfig()).list("iss_001")
    assert result[0].value == ("alpha", "beta")
    assert isinstance(result[0].value, tuple)


def test_issue_property_list_rejects_malformed_multi_value_shape() -> None:
    transport = make_transport(
        stdout=[
            {
                "property_id": "p1",
                "name": "Tags",
                "type": "multi_text",
                "value": "alpha",
            }
        ]
    )
    with pytest.raises(OutputShapeError, match="list property value"):
        IssuePropertyResource(transport, ClientConfig()).list("iss_001")


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
