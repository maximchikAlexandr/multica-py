from __future__ import annotations

import datetime
from unittest.mock import MagicMock

import msgspec

from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.skills import Skill, SkillCreateRequest, SkillUpdateRequest
from multica_py.resources.skills import SkillResource


def _t() -> MagicMock:
    return MagicMock(spec=CliTransport)


def _r(stdout: bytes = b"") -> RawCommandResult:
    return RawCommandResult(
        argv=(), exit_code=0, stdout=stdout, stderr=b"", duration=datetime.timedelta()
    )


_S = msgspec.json.encode(Skill(id="s1", name="sk"))


class TestSkillCommands:
    def test_list_sends_skill_list(self):
        t = _t()
        t.run_bytes.return_value = _r(stdout=b"[]")
        SkillResource(t, ClientConfig()).list()
        t.run_bytes.assert_called_once_with(
            ("skill", "list", "--output", "json"), stdin=None, timeout=None
        )

    def test_get_sends_skill_get(self):
        t = _t()
        t.run_bytes.return_value = _r(stdout=_S)
        SkillResource(t, ClientConfig()).get("s1")
        t.run_bytes.assert_called_once_with(
            ("skill", "get", "s1", "--output", "json"), stdin=None, timeout=None
        )

    def test_create_includes_name(self):
        t = _t()
        t.run_bytes.return_value = _r(stdout=_S)
        SkillResource(t, ClientConfig()).create(SkillCreateRequest(name="my-sk"))
        t.run_bytes.assert_called_once_with(
            ("skill", "create", "--name", "my-sk", "--output", "json"), stdin=None, timeout=None
        )

    def test_create_omits_description_when_none(self):
        t = _t()
        t.run_bytes.return_value = _r(stdout=_S)
        SkillResource(t, ClientConfig()).create(SkillCreateRequest(name="my-sk"))
        args = t.run_bytes.call_args[0][0]
        assert "--description" not in args

    def test_create_includes_description_when_set(self):
        t = _t()
        t.run_bytes.return_value = _r(stdout=_S)
        SkillResource(t, ClientConfig()).create(
            SkillCreateRequest(name="my-sk", description="desc")
        )
        args = t.run_bytes.call_args[0][0]
        assert "--description" in args and args[args.index("--description") + 1] == "desc"

    def test_update_omits_name_when_none(self):
        t = _t()
        t.run_bytes.return_value = _r(stdout=_S)
        SkillResource(t, ClientConfig()).update("s1", SkillUpdateRequest())
        args = t.run_bytes.call_args[0][0]
        assert "--name" not in args

    def test_update_includes_name_when_set(self):
        t = _t()
        t.run_bytes.return_value = _r(stdout=_S)
        SkillResource(t, ClientConfig()).update("s1", SkillUpdateRequest(name="new"))
        args = t.run_bytes.call_args[0][0]
        assert "--name" in args

    def test_delete_uses_text(self):
        t = _t()
        SkillResource(t, ClientConfig()).delete("s1")
        t.run_text.assert_called_once_with(("skill", "delete", "s1"))

    def test_import_from_url(self):
        t = _t()
        t.run_bytes.return_value = _r(stdout=_S)
        SkillResource(t, ClientConfig()).import_from_url("https://x.com")
        t.run_bytes.assert_called_once_with(
            ("skill", "import", "--url", "https://x.com", "--output", "json"),
            stdin=None,
            timeout=None,
        )


class TestSkillDecode:
    def test_list_decodes(self):
        t = _t()
        t.run_bytes.return_value = _r(
            msgspec.json.encode([Skill(id="s1", name="S1"), Skill(id="s2", name="S2")])
        )
        result = SkillResource(t, ClientConfig()).list()
        assert len(result) == 2
        assert result[0].name == "S1"
