from __future__ import annotations

import datetime
from unittest.mock import MagicMock

import msgspec

from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.agents import Agent, AgentCreateRequest, AgentTask, AgentUpdateRequest
from multica_py.resources.agents import AgentResource


def _make_transport() -> MagicMock:
    return MagicMock(spec=CliTransport)


def _result(stdout: bytes = b"", exit_code: int = 0) -> RawCommandResult:
    return RawCommandResult(
        argv=(), exit_code=exit_code, stdout=stdout, stderr=b"", duration=datetime.timedelta()
    )


class TestAgentCommandConstruction:
    def test_list_sends_agent_list_json(self):
        transport = _make_transport()
        transport.run_bytes.return_value = _result(stdout=b"[]")
        agent = AgentResource(transport, ClientConfig())
        agent.list()
        transport.run_bytes.assert_called_once_with(
            ("agent", "list", "--output", "json"), stdin=None, timeout=None
        )

    def test_get_sends_agent_get(self):
        transport = _make_transport()
        transport.run_bytes.return_value = _result(msgspec.json.encode(Agent(id="a1", name="n")))
        agent = AgentResource(transport, ClientConfig())
        agent.get("a1")
        transport.run_bytes.assert_called_once_with(
            ("agent", "get", "a1", "--output", "json"), stdin=None, timeout=None
        )

    def test_create_includes_name(self):
        transport = _make_transport()
        transport.run_bytes.return_value = _result(msgspec.json.encode(Agent(id="a1", name="n")))
        agent = AgentResource(transport, ClientConfig())
        agent.create(AgentCreateRequest(name="my-agent"))
        transport.run_bytes.assert_called_once_with(
            ("agent", "create", "--name", "my-agent", "--output", "json"), stdin=None, timeout=None
        )

    def test_create_includes_description_when_set(self):
        transport = _make_transport()
        transport.run_bytes.return_value = _result(msgspec.json.encode(Agent(id="a1", name="n")))
        agent = AgentResource(transport, ClientConfig())
        agent.create(AgentCreateRequest(name="my-agent", description="desc"))
        args = transport.run_bytes.call_args[0][0]
        assert "--description" in args
        assert args[args.index("--description") + 1] == "desc"

    def test_update_omits_name_when_none(self):
        transport = _make_transport()
        transport.run_bytes.return_value = _result(msgspec.json.encode(Agent(id="a1", name="n")))
        agent = AgentResource(transport, ClientConfig())
        agent.update("a1", AgentUpdateRequest())
        args = transport.run_bytes.call_args[0][0]
        assert "--name" not in args

    def test_update_includes_name_when_set(self):
        transport = _make_transport()
        transport.run_bytes.return_value = _result(msgspec.json.encode(Agent(id="a1", name="n")))
        agent = AgentResource(transport, ClientConfig())
        agent.update("a1", AgentUpdateRequest(name="new"))
        args = transport.run_bytes.call_args[0][0]
        assert "--name" in args
        assert args[args.index("--name") + 1] == "new"

    def test_archive_uses_text_transport(self):
        transport = _make_transport()
        agent = AgentResource(transport, ClientConfig())
        agent.archive("a1")
        transport.run_text.assert_called_once_with(("agent", "archive", "a1"))

    def test_restore_uses_text_transport(self):
        transport = _make_transport()
        agent = AgentResource(transport, ClientConfig())
        agent.restore("a1")
        transport.run_text.assert_called_once_with(("agent", "restore", "a1"))

    def test_tasks_sends_agent_tasks_json(self):
        transport = _make_transport()
        transport.run_bytes.return_value = _result(stdout=b"[]")
        agent = AgentResource(transport, ClientConfig())
        agent.tasks("a1")
        transport.run_bytes.assert_called_once_with(
            ("agent", "tasks", "a1", "--output", "json"), stdin=None, timeout=None
        )

    def test_upload_avatar_uses_text_transport(self):
        transport = _make_transport()
        agent = AgentResource(transport, ClientConfig())
        agent.upload_avatar("a1", "/path/image.png")
        transport.run_text.assert_called_once_with(
            ("agent", "avatar", "upload", "a1", "--image", "/path/image.png")
        )


class TestAgentDecode:
    def test_list_decodes_agents(self):
        transport = _make_transport()
        data = msgspec.json.encode([Agent(id="a1", name="Alice"), Agent(id="a2", name="Bob")])
        transport.run_bytes.return_value = _result(stdout=data)
        agent = AgentResource(transport, ClientConfig())
        result = agent.list()
        assert len(result) == 2
        assert result[0].id == "a1"
        assert result[1].name == "Bob"

    def test_get_decodes_agent(self):
        transport = _make_transport()
        data = msgspec.json.encode(Agent(id="a1", name="Alice", description="desc"))
        transport.run_bytes.return_value = _result(stdout=data)
        agent = AgentResource(transport, ClientConfig())
        result = agent.get("a1")
        assert result.id == "a1"
        assert result.description == "desc"

    def test_tasks_decodes_agent_tasks(self):
        transport = _make_transport()
        data = msgspec.json.encode([AgentTask(id="t1", status="running", issue_id="i1")])
        transport.run_bytes.return_value = _result(stdout=data)
        agent = AgentResource(transport, ClientConfig())
        result = agent.tasks("a1")
        assert len(result) == 1
        assert result[0].id == "t1"
