from __future__ import annotations

import datetime
from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.enums import ProjectStatus
from multica_py.exceptions import ValidationError
from multica_py.models.projects import ProjectCreateRequest, ProjectUpdateRequest
from multica_py.resources.projects import ProjectResource


def _make_transport() -> MagicMock:
    return MagicMock(spec=CliTransport)


def _result(stdout: bytes = b"", exit_code: int = 0) -> RawCommandResult:
    return RawCommandResult(
        argv=(), exit_code=exit_code, stdout=stdout, stderr=b"", duration=datetime.timedelta()
    )


def _project_json(*, project_id: str = "pr_1", title: str = "Alpha") -> bytes:
    return msgspec.json.encode(
        {"id": project_id, "title": title, "status": ProjectStatus.planned.value}
    )


class TestProjectModels:
    def test_project_status_enum(self):
        assert ProjectStatus.planned.value == "planned"


class TestProjectCommandConstruction:
    def test_create_uses_title_flag(self):
        transport = _make_transport()
        transport.run_bytes.return_value = _result(_project_json())
        resource = ProjectResource(transport, ClientConfig())
        created = resource.create(ProjectCreateRequest(name="Alpha"))
        assert created.name == "Alpha"
        transport.run_bytes.assert_called_once_with(
            ("project", "create", "--title", "Alpha", "--output", "json"),
            stdin=None,
            timeout=None,
        )

    def test_create_includes_description_when_set(self):
        transport = _make_transport()
        transport.run_bytes.return_value = _result(_project_json())
        resource = ProjectResource(transport, ClientConfig())
        resource.create(ProjectCreateRequest(name="Alpha", description="desc"))
        args = transport.run_bytes.call_args[0][0]
        assert "--title" in args
        assert args[args.index("--title") + 1] == "Alpha"
        assert "--description" in args
        assert args[args.index("--description") + 1] == "desc"
        assert "--name" not in args

    def test_update_omits_title_and_description_when_unset(self):
        transport = _make_transport()
        transport.run_bytes.return_value = _result(_project_json())
        resource = ProjectResource(transport, ClientConfig())
        resource.update("pr_1", ProjectUpdateRequest())
        args = transport.run_bytes.call_args[0][0]
        assert args == ("project", "update", "pr_1", "--output", "json")
        assert "--title" not in args
        assert "--description" not in args
        assert "--name" not in args

    def test_update_includes_title_when_name_set(self):
        transport = _make_transport()
        transport.run_bytes.return_value = _result(_project_json(title="New"))
        resource = ProjectResource(transport, ClientConfig())
        updated = resource.update("pr_1", ProjectUpdateRequest(name="only-title"))
        assert updated.name == "New"
        args = transport.run_bytes.call_args[0][0]
        assert "--title" in args
        assert args[args.index("--title") + 1] == "only-title"
        assert "--description" not in args
        assert "--name" not in args

    def test_update_includes_empty_description(self):
        transport = _make_transport()
        transport.run_bytes.return_value = _result(_project_json())
        resource = ProjectResource(transport, ClientConfig())
        resource.update("pr_1", ProjectUpdateRequest(description=""))
        args = transport.run_bytes.call_args[0][0]
        assert "--description" in args
        assert args[args.index("--description") + 1] == ""

    def test_update_includes_non_empty_description(self):
        transport = _make_transport()
        transport.run_bytes.return_value = _result(_project_json())
        resource = ProjectResource(transport, ClientConfig())
        resource.update("pr_1", ProjectUpdateRequest(description="new"))
        args = transport.run_bytes.call_args[0][0]
        assert "--description" in args
        assert args[args.index("--description") + 1] == "new"

    def test_update_description_none_raises_validation_error(self):
        transport = _make_transport()
        resource = ProjectResource(transport, ClientConfig())
        with pytest.raises(ValidationError, match="description=None"):
            resource.update("pr_1", ProjectUpdateRequest(description=None))
        transport.run_bytes.assert_not_called()
