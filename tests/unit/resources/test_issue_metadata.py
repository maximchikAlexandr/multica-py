from __future__ import annotations

import datetime
from unittest.mock import MagicMock

import msgspec

from multica_py._internal.specs import RawCommandResult, TextResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.enums import MetadataValueType
from multica_py.models.common import Page
from multica_py.models.issue_activity import (
    MetadataEntry,
    MetadataListRequest,
    MetadataPredicate,
    MetadataSetRequest,
)
from multica_py.resources.issue_metadata import IssueMetadataResource


def _transport() -> MagicMock:
    return MagicMock(spec=CliTransport)


def _result(stdout: bytes = b"") -> RawCommandResult:
    return RawCommandResult(
        argv=(),
        exit_code=0,
        stdout=stdout,
        stderr=b"",
        duration=datetime.timedelta(),
    )


class TestIssueMetadataResource:
    def test_set_infers_boolean_type_and_format(self) -> None:
        transport = _transport()
        transport.run_bytes.return_value = _result(
            msgspec.json.encode(MetadataEntry(key="flag", value=True))
        )
        resource = IssueMetadataResource(transport, ClientConfig())

        resource.set("iss_1", "flag", True)

        args = transport.run_bytes.call_args[0][0]
        assert "--value" in args
        assert args[args.index("--value") + 1] == "true"
        assert "--type" in args
        assert args[args.index("--type") + 1] == MetadataValueType.boolean.value

    def test_set_typed_honors_explicit_value_type(self) -> None:
        transport = _transport()
        transport.run_bytes.return_value = _result(
            msgspec.json.encode(MetadataEntry(key="answer", value="42"))
        )
        resource = IssueMetadataResource(transport, ClientConfig())

        resource.set_typed(
            MetadataSetRequest(
                issue_id="iss_1",
                key="answer",
                value="42",
                value_type=MetadataValueType.integer,
            )
        )

        args = transport.run_bytes.call_args[0][0]
        assert args[args.index("--type") + 1] == MetadataValueType.integer.value

    def test_query_repeats_predicates_and_returns_page(self) -> None:
        transport = _transport()
        payload = msgspec.json.encode([MetadataEntry(key="priority", value="high")]).decode("utf-8")
        transport.run_text.return_value = TextResult(
            text=payload, stderr="next cursor cur_2", exit_code=0
        )
        resource = IssueMetadataResource(transport, ClientConfig())

        result = resource.query(
            MetadataListRequest(
                issue_id="iss_1",
                predicates=(
                    MetadataPredicate(key="priority", value="high"),
                    MetadataPredicate(key="visible", value=True),
                ),
                cursor="cur_1",
                limit=25,
            )
        )

        args = transport.run_text.call_args[0][0]
        assert args.count("--metadata") == 2
        assert "--cursor" in args
        assert "--limit" in args
        assert isinstance(result, Page)
        assert result.next_cursor == "cur_2"
        assert result.items[0].key == "priority"
