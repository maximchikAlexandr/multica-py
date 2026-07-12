from __future__ import annotations

import datetime
from unittest.mock import MagicMock

import msgspec

from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.system import Repository, RepositoryCheckoutResult
from multica_py.resources.repositories import RepositoryResource


def _t() -> MagicMock:
    return MagicMock(spec=CliTransport)


def _r(stdout: bytes = b"") -> RawCommandResult:
    return RawCommandResult(
        argv=(), exit_code=0, stdout=stdout, stderr=b"", duration=datetime.timedelta()
    )


_R = msgspec.json.encode(Repository(id="r1", name="repo1"))


class TestRepoCommands:
    def test_list_sends_repo_list(self):
        t = _t()
        t.run_bytes.return_value = _r(stdout=b"[]")
        RepositoryResource(t, ClientConfig()).list()
        t.run_bytes.assert_called_once_with(
            ("repo", "list", "--output", "json"), stdin=None, timeout=None
        )

    def test_get_sends_repo_get(self):
        t = _t()
        t.run_bytes.return_value = _r(stdout=_R)
        RepositoryResource(t, ClientConfig()).get("r1")
        t.run_bytes.assert_called_once_with(
            ("repo", "get", "r1", "--output", "json"), stdin=None, timeout=None
        )

    def test_checkout_sends_branch(self):
        t = _t()
        t.run_bytes.return_value = _r(
            msgspec.json.encode(RepositoryCheckoutResult(path="/p", branch="main", success=True))
        )
        RepositoryResource(t, ClientConfig()).checkout("r1", "main")
        t.run_bytes.assert_called_once_with(
            ("repo", "checkout", "r1", "--branch", "main", "--output", "json"),
            stdin=None,
            timeout=None,
        )


class TestRepoDecode:
    def test_list_decodes(self):
        t = _t()
        t.run_bytes.return_value = _r(
            msgspec.json.encode([Repository(id="r1", name="R1"), Repository(id="r2", name="R2")])
        )
        result = RepositoryResource(t, ClientConfig()).list()
        assert len(result) == 2

    def test_checkout_decodes(self):
        t = _t()
        data = msgspec.json.encode(RepositoryCheckoutResult(path="/p", branch="main", success=True))
        t.run_bytes.return_value = _r(stdout=data)
        result = RepositoryResource(t, ClientConfig()).checkout("r1", "main")
        assert result.success is True
