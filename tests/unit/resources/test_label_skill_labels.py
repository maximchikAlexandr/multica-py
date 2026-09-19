from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast, get_type_hints

import pytest

from multica_py import Command
from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.entities.labels import Label
from multica_py.entities.skills import Skill
from multica_py.enums import CompatibilityPolicy, LabelResourceType
from multica_py.exceptions import DetachedEntityError, OutputShapeError
from multica_py.models.common import ActionResult, Page
from multica_py.models.relations import LazyCollection
from multica_py.resources.labels import LabelResource
from multica_py.resources.skill_labels import SkillLabelResource
from multica_py.resources.skills import SkillResource
from multica_py.sentinels import Unset, UnsetType


@dataclass(frozen=True)
class LabelListCase:
    id: str
    resource_type: LabelResourceType | str | None
    command: str


@dataclass(frozen=True)
class LabelUpdateCase:
    id: str
    description: str | UnsetType | None
    command: str


@dataclass(frozen=True)
class LabelCreateCase:
    id: str
    resource_type: LabelResourceType | str
    description: str | None
    command: str


@dataclass(frozen=True)
class SkillLabelIdentifierCase:
    id: str
    invoke: Callable[[SkillLabelResource], object]


@dataclass(frozen=True)
class SkillLabelCommandCase:
    id: str
    invoke: Callable[[SkillLabelResource], object]
    command: str


@dataclass(frozen=True)
class SkillLabelPayloadCase:
    id: str
    payload: object
    expected_ids: tuple[str, ...]


@dataclass(frozen=True)
class SkillLabelMalformedCase:
    id: str
    payload: object
    invoke: Callable[[SkillLabelResource], object]


@dataclass(frozen=True)
class SkillListPreloadCase:
    id: str
    labels: list[dict[str, object]]
    expected_ids: tuple[str, ...]
    expected_names: tuple[str, ...]
    expected_colors: tuple[str, ...]
    expected_descriptions: tuple[str, ...]
    expected_resource_types: tuple[str, ...]


def _reject_issue_skill_labels(resource: SkillLabelResource) -> object:
    return resource.list("sk_1")


def _reject_issue_skill_label_add(resource: SkillLabelResource) -> object:
    return resource.add("sk_1", "lb_1")


def _reject_issue_skill_label_remove(resource: SkillLabelResource) -> object:
    return resource.remove("sk_1", "lb_1")


_SKILL_LABEL_ISSUE_SCOPE_CASES = (
    SkillLabelIdentifierCase("list", _reject_issue_skill_labels),
    SkillLabelIdentifierCase("add", _reject_issue_skill_label_add),
    SkillLabelIdentifierCase("remove", _reject_issue_skill_label_remove),
)


def _reject_malformed_skill_label_add(resource: SkillLabelResource) -> object:
    return resource.add("sk_1", "lb_1")


def _reject_malformed_skill_label_remove(resource: SkillLabelResource) -> object:
    return resource.remove("sk_1", "lb_1")


_SKILL_LABEL_MALFORMED_CASES = (
    SkillLabelMalformedCase("add", [{"id": "lb_1"}], _reject_malformed_skill_label_add),
    SkillLabelMalformedCase("remove", {"detached": "yes"}, _reject_malformed_skill_label_remove),
)


@pytest.mark.parametrize(
    "case",
    (
        LabelListCase("omitted", None, "multica label list --output json"),
        LabelListCase(
            "issue",
            LabelResourceType.issue,
            "multica label list --resource-type issue --output json",
        ),
        LabelListCase("skill", "skill", "multica label list --resource-type skill --output json"),
    ),
    ids=lambda case: case.id,
)
def test_label_list_resource_type_argv_matrix(
    case: LabelListCase,
) -> None:
    resource = LabelResource(CliTransport(ClientConfig()), ClientConfig())
    assert resource.list_command(case.resource_type).commands == (case.command,)


@pytest.mark.parametrize(
    "case",
    (
        LabelUpdateCase("omit", Unset, "multica label get lb_1 --output json"),
        LabelUpdateCase(
            "set",
            "new description",
            "multica label update lb_1 --description 'new description' --output json",
        ),
        LabelUpdateCase(
            "clear-none", None, "multica label update lb_1 --description '' --output json"
        ),
        LabelUpdateCase(
            "clear-empty", "", "multica label update lb_1 --description '' --output json"
        ),
    ),
    ids=lambda case: case.id,
)
def test_label_update_description_argv_matrix(
    case: LabelUpdateCase,
) -> None:
    resource = LabelResource(CliTransport(ClientConfig()), ClientConfig())
    assert resource.update_command("lb_1", description=case.description).commands == (case.command,)


@pytest.mark.parametrize(
    "case",
    (
        LabelCreateCase(
            "default-issue-omitted",
            LabelResourceType.issue,
            None,
            "multica label create --name build --resource-type issue --output json",
        ),
        LabelCreateCase(
            "skill-described",
            "skill",
            "for builds",
            "multica label create --name build --color blue --resource-type skill "
            "--description 'for builds' --output json",
        ),
    ),
    ids=lambda case: case.id,
)
def test_label_create_scope_and_description_argv(
    case: LabelCreateCase,
) -> None:
    resource = LabelResource(CliTransport(ClientConfig()), ClientConfig())
    assert resource.create_command(
        "build",
        "blue" if case.resource_type == "skill" else None,
        resource_type=case.resource_type,
        description=case.description,
    ).commands == (case.command,)


def test_label_create_rejects_unsupported_scope_and_empty_description_before_transport(
    mock_transport: Any,
) -> None:
    resource = LabelResource(mock_transport, ClientConfig())
    with pytest.raises(ValueError, match="resource_type"):
        resource.create("build", resource_type="workspace")
    with pytest.raises(ValueError, match="description"):
        resource.create("build", description="")
    mock_transport.run_bytes.assert_not_called()


def test_label_decoding_preserves_description_and_resource_type(
    mock_transport: Any, raw_result: Callable[..., Any]
) -> None:
    mock_transport.run_bytes.return_value = raw_result(
        stdout=json.dumps(
            {
                "id": "lb_1",
                "name": "Build",
                "color": "blue",
                "description": "for builds",
                "resource_type": "skill",
            }
        ).encode()
    )
    label = LabelResource(mock_transport, ClientConfig()).get("lb_1")
    assert label.description == "for builds"
    assert label.resource_type == "skill"


def _invalid_list_identifier(resource: SkillLabelResource) -> object:
    return resource.list("")


def _invalid_add_skill_identifier(resource: SkillLabelResource) -> object:
    return resource.add("", "lb_1")


def _invalid_add_label_identifier(resource: SkillLabelResource) -> object:
    return resource.add("sk_1", "")


def _invalid_remove_skill_identifier(resource: SkillLabelResource) -> object:
    return resource.remove("", "lb_1")


def _invalid_remove_label_identifier(resource: SkillLabelResource) -> object:
    return resource.remove("sk_1", "")


_SKILL_LABEL_IDENTIFIER_CASES = (
    SkillLabelIdentifierCase("list-skill-blank", _invalid_list_identifier),
    SkillLabelIdentifierCase("add-skill-blank", _invalid_add_skill_identifier),
    SkillLabelIdentifierCase("add-label-blank", _invalid_add_label_identifier),
    SkillLabelIdentifierCase("remove-skill-blank", _invalid_remove_skill_identifier),
    SkillLabelIdentifierCase("remove-label-blank", _invalid_remove_label_identifier),
)


@pytest.mark.parametrize("case", _SKILL_LABEL_IDENTIFIER_CASES, ids=lambda case: case.id)
def test_skill_label_identifiers_fail_before_transport(
    case: SkillLabelIdentifierCase, mock_transport: Any
) -> None:
    resource = SkillLabelResource(mock_transport, ClientConfig())
    with pytest.raises(ValueError):
        case.invoke(resource)
    mock_transport.run_bytes.assert_not_called()


def _list_skill_labels(resource: SkillLabelResource) -> object:
    return resource.list_command("sk_1")


def _add_skill_label(resource: SkillLabelResource) -> object:
    return resource.add_command("sk_1", "lb_1")


def _remove_skill_label(resource: SkillLabelResource) -> object:
    return resource.remove_command("sk_1", "lb_1")


_SKILL_LABEL_COMMAND_CASES = (
    SkillLabelCommandCase(
        "list", _list_skill_labels, "multica skill label list sk_1 --output json"
    ),
    SkillLabelCommandCase(
        "add", _add_skill_label, "multica skill label add sk_1 lb_1 --output json"
    ),
    SkillLabelCommandCase(
        "remove", _remove_skill_label, "multica skill label remove sk_1 lb_1 --output json"
    ),
)


@pytest.mark.parametrize("case", _SKILL_LABEL_COMMAND_CASES, ids=lambda case: case.id)
def test_skill_label_commands_have_exact_argv(case: SkillLabelCommandCase) -> None:
    resource = SkillLabelResource(CliTransport(ClientConfig()), ClientConfig())
    command = cast("Command[object]", case.invoke(resource))
    assert command.commands == (case.command,)


@pytest.mark.parametrize(
    "case",
    (
        SkillLabelPayloadCase("empty", [], ()),
        SkillLabelPayloadCase(
            "populated", [{"id": "lb_1", "name": "Build", "resource_type": "skill"}], ("lb_1",)
        ),
        SkillLabelPayloadCase(
            "future-scope", [{"id": "lb_1", "name": "Build", "resource_type": "future"}], ("lb_1",)
        ),
    ),
    ids=lambda case: case.id,
)
def test_skill_label_list_decodes_empty_populated_and_open_scope(
    case: SkillLabelPayloadCase, mock_transport: Any, raw_result: Callable[..., Any]
) -> None:
    mock_transport.run_bytes.return_value = raw_result(stdout=json.dumps(case.payload).encode())
    page = SkillLabelResource(mock_transport, ClientConfig()).list("sk_1")
    assert tuple(label.id for label in page.items) == case.expected_ids


def test_skill_label_responses_reject_issue_scope_and_malformed_rows(
    mock_transport: Any, raw_result: Callable[..., Any]
) -> None:
    resource = SkillLabelResource(mock_transport, ClientConfig())
    mock_transport.run_bytes.return_value = raw_result(
        stdout=json.dumps([{"id": "lb_1", "name": "Issue", "resource_type": "issue"}]).encode()
    )
    with pytest.raises(OutputShapeError, match="issue-scoped"):
        resource.list("sk_1")

    mock_transport.run_bytes.return_value = raw_result(stdout=json.dumps([{"id": "lb_1"}]).encode())
    with pytest.raises(OutputShapeError):
        resource.list("sk_1")


@pytest.mark.parametrize("case", _SKILL_LABEL_ISSUE_SCOPE_CASES, ids=lambda case: case.id)
def test_skill_label_mutations_reject_issue_scope(
    case: SkillLabelIdentifierCase, mock_transport: Any, raw_result: Callable[..., Any]
) -> None:
    mock_transport.run_bytes.return_value = raw_result(
        stdout=json.dumps([{"id": "lb_1", "name": "Issue", "resource_type": "issue"}]).encode()
    )
    resource = SkillLabelResource(mock_transport, ClientConfig())
    with pytest.raises(OutputShapeError, match="issue-scoped"):
        case.invoke(resource)


def test_skill_label_remove_accepts_detached_fallback(
    mock_transport: Any, raw_result: Callable[..., Any]
) -> None:
    mock_transport.run_bytes.return_value = raw_result(
        stdout=json.dumps({"detached": True}).encode()
    )
    result = SkillLabelResource(mock_transport, ClientConfig()).remove("sk_1", "lb_1")
    assert isinstance(result, ActionResult)
    assert result.success is True


def test_skill_label_add_and_remove_decode_refreshed_pages(
    mock_transport: Any, raw_result: Callable[..., Any]
) -> None:
    mock_transport.run_bytes.side_effect = [
        raw_result(
            stdout=json.dumps([{"id": "lb_1", "name": "Skill", "resource_type": "skill"}]).encode()
        ),
        raw_result(
            stdout=json.dumps(
                [{"id": "lb_2", "name": "Refreshed", "resource_type": "skill"}]
            ).encode()
        ),
    ]
    resource = SkillLabelResource(mock_transport, ClientConfig())
    added = resource.add("sk_1", "lb_1")
    removed = resource.remove("sk_1", "lb_1")
    assert isinstance(removed, Page)
    assert tuple(label.id for label in added.items) == ("lb_1",)
    assert tuple(label.id for label in removed.items) == ("lb_2",)


@pytest.mark.parametrize("case", _SKILL_LABEL_MALFORMED_CASES, ids=lambda case: case.id)
def test_skill_label_mutations_reject_malformed_responses(
    case: SkillLabelMalformedCase, mock_transport: Any, raw_result: Callable[..., Any]
) -> None:
    mock_transport.run_bytes.return_value = raw_result(stdout=json.dumps(case.payload).encode())
    resource = SkillLabelResource(mock_transport, ClientConfig())
    with pytest.raises(OutputShapeError):
        case.invoke(resource)


@pytest.mark.parametrize(
    "case",
    (
        SkillListPreloadCase("empty", [], (), (), (), (), ()),
        SkillListPreloadCase(
            "populated",
            [
                {
                    "id": "lb_1",
                    "name": "Skill",
                    "color": "blue",
                    "description": "for builds",
                    "resource_type": "skill",
                }
            ],
            ("lb_1",),
            ("Skill",),
            ("blue",),
            ("for builds",),
            ("skill",),
        ),
    ),
    ids=lambda case: case.id,
)
def test_skill_list_preloads_labels_without_relation_transport_call(
    case: SkillListPreloadCase, mock_transport: Any, raw_result: Callable[..., Any]
) -> None:
    mock_transport.run_bytes.return_value = raw_result(
        stdout=json.dumps(
            [
                {
                    "id": "sk_1",
                    "name": "Build",
                    "description": "Build things",
                    "file_count": 2,
                    "labels": case.labels,
                }
            ]
        ).encode()
    )
    resource = SkillResource(mock_transport, ClientConfig())
    skill = resource.list().items[0]
    assert bool(skill.labels.loaded)
    assert skill.description == "Build things"
    assert skill.file_count == 2
    labels = skill.labels.all()
    assert tuple(label.id for label in labels) == case.expected_ids
    assert tuple(label.name for label in labels) == case.expected_names
    assert tuple(label.color for label in labels) == case.expected_colors
    assert tuple(label.description for label in labels) == case.expected_descriptions
    assert tuple(label.resource_type for label in labels) == case.expected_resource_types
    assert mock_transport.run_bytes.call_count == 1


@pytest.mark.parametrize(
    "payload",
    (
        [{"id": "sk_1", "name": "Build", "labels": None}],
        [{"id": "sk_1", "name": "Build", "labels": [{"name": "Missing id"}]}],
        [{"id": "sk_1", "name": "Build", "labels": [{"id": "lb_1"}]}],
    ),
    ids=("labels-null", "nested-id-missing", "nested-name-missing"),
)
def test_skill_list_rejects_malformed_required_fields(
    payload: object, mock_transport: Any, raw_result: Callable[..., Any]
) -> None:
    mock_transport.run_bytes.return_value = raw_result(stdout=json.dumps(payload).encode())
    with pytest.raises(OutputShapeError):
        SkillResource(mock_transport, ClientConfig()).list()


def test_skill_list_projection_rejects_issue_scoped_labels(
    mock_transport: Any, raw_result: Callable[..., Any]
) -> None:
    mock_transport.run_bytes.return_value = raw_result(
        stdout=json.dumps(
            [
                {
                    "id": "sk_1",
                    "name": "Build",
                    "labels": [{"id": "lb_1", "name": "Issue", "resource_type": "issue"}],
                }
            ]
        ).encode()
    )
    with pytest.raises(OutputShapeError, match="issue-scoped"):
        SkillResource(mock_transport, ClientConfig()).list()


def test_eager_skill_labels_add_and_remove_invalidate_and_reload(
    raw_result: Callable[..., Any],
) -> None:
    config = ClientConfig(compatibility=CompatibilityPolicy.ignore)
    transport = CliTransport(config)
    responses = iter(
        (
            [
                {
                    "id": "sk_1",
                    "name": "Build",
                    "labels": [{"id": "lb_1", "name": "Initial", "resource_type": "skill"}],
                }
            ],
            [{"id": "lb_2", "name": "Added", "resource_type": "skill"}],
            [{"id": "lb_3", "name": "After add", "resource_type": "skill"}],
            [{"id": "lb_4", "name": "Removed", "resource_type": "skill"}],
            [{"id": "lb_5", "name": "After remove", "resource_type": "skill"}],
        )
    )
    calls: list[tuple[str, ...]] = []

    def execute(argv: tuple[str, ...], **_: Any) -> RawCommandResult:
        calls.append(argv)
        return raw_result(stdout=json.dumps(next(responses)).encode())

    setattr(transport, "_execute", execute)
    client = MulticaClient(config)
    client.skills._transport = transport
    client.skills.labels._transport = transport
    skill = client.skills.list().items[0]

    assert skill.labels.loaded
    assert tuple(label.id for label in skill.labels.all()) == ("lb_1",)
    assert len(calls) == 1

    added = skill.add_label("lb_2")
    assert tuple(label.id for label in added.items) == ("lb_2",)
    assert not bool(skill.labels.loaded)
    assert tuple(label.id for label in skill.labels.all()) == ("lb_3",)
    assert len(calls) == 3

    removed = skill.remove_label("lb_2")
    assert isinstance(removed, Page)
    assert tuple(label.id for label in removed.items) == ("lb_4",)
    assert not bool(skill.labels.loaded)
    assert tuple(label.id for label in skill.labels.all()) == ("lb_5",)
    assert len(calls) == 5


def test_skill_detail_labels_load_once_and_mutation_invalidates_cache(
    raw_result: Callable[..., Any],
) -> None:
    config = ClientConfig(compatibility=CompatibilityPolicy.ignore)
    transport = CliTransport(config)
    responses = iter(
        (
            [{"id": "lb_1", "name": "First", "resource_type": "skill"}],
            [{"id": "lb_2", "name": "Second", "resource_type": "skill"}],
            [{"id": "lb_3", "name": "Reloaded", "resource_type": "skill"}],
            [{"id": "lb_4", "name": "After remove", "resource_type": "skill"}],
            [{"id": "lb_5", "name": "Reloaded again", "resource_type": "skill"}],
            {"detached": True},
            [{"id": "lb_6", "name": "After detach", "resource_type": "skill"}],
        )
    )
    calls: list[tuple[str, ...]] = []

    def execute(argv: tuple[str, ...], **_: Any) -> RawCommandResult:
        calls.append(argv)
        return raw_result(stdout=json.dumps(next(responses)).encode())

    setattr(transport, "_execute", execute)
    client = MulticaClient(config)
    client.skills._transport = transport
    client.skills.labels._transport = transport
    skill = Skill(id="sk_1", name="Build", _client=client)

    assert not skill.labels.loaded
    assert tuple(label.id for label in skill.labels.all()) == ("lb_1",)
    assert tuple(label.id for label in skill.labels.all()) == ("lb_1",)
    assert len(calls) == 1

    skill.add_label_command("lb_4").run()
    assert not skill.labels.loaded
    assert tuple(label.id for label in skill.labels.all()) == ("lb_3",)
    assert len(calls) == 3

    removed = skill.remove_label_command("lb_4").run()
    assert isinstance(removed, Page)
    assert tuple(label.id for label in removed.items) == ("lb_4",)
    assert not skill.labels.loaded
    assert tuple(label.id for label in skill.labels.all()) == ("lb_5",)
    assert len(calls) == 5

    detached = skill.remove_label_command("lb_5").run()
    assert isinstance(detached, ActionResult)
    assert not skill.labels.loaded
    assert tuple(label.id for label in skill.labels.all()) == ("lb_6",)
    assert len(calls) == 7


def test_skill_labels_type_and_unbound_failures() -> None:
    getter = cast("property", Skill.__dict__["labels"]).fget
    assert getter is not None
    annotation = get_type_hints(getter)["return"]
    assert annotation == LazyCollection[Label]

    skill = Skill(id="sk_1", name="Build")
    with pytest.raises(DetachedEntityError):
        skill.labels
    with pytest.raises(DetachedEntityError):
        skill.add_label("lb_1")
    with pytest.raises(DetachedEntityError):
        skill.add_label_command("lb_1")
    with pytest.raises(DetachedEntityError):
        skill.remove_label("lb_1")
    with pytest.raises(DetachedEntityError):
        skill.remove_label_command("lb_1")
