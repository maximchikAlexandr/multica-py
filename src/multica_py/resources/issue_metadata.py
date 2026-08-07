from __future__ import annotations

from typing import cast, overload

from multica_py._internal.commands import Command, _Step
from multica_py._internal.decoders import decode_json
from multica_py._internal.specs import TextResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.enums import MetadataValueType
from multica_py.models.issue_activity import (
    MetadataEntry,
    MetadataListRequest,
    MetadataPage,
    MetadataPredicate,
    MetadataSetRequest,
)
from multica_py.resources._base import BaseResource, _resolve_request
from multica_py.types import MetadataValue


class IssueMetadataResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)

    def list_command(self, issue_id: str) -> Command[dict[str, MetadataValue]]:
        args = ("issue", "metadata", "list", issue_id, "--output", "json")

        def decode(stdout: bytes, command: str) -> object:
            return decode_json(stdout, dict[str, MetadataValue], command=command)

        return self._plan(
            steps=(_Step(args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("dict[str, MetadataValue]", results[0]),
        )

    def list(self, issue_id: str) -> dict[str, MetadataValue]:
        return self.list_command(issue_id).run()

    @overload
    def query_command(self, request: MetadataListRequest, /) -> Command[MetadataPage]: ...

    @overload
    def query_command(
        self,
        *,
        issue_id: str,
        predicates: tuple[MetadataPredicate, ...] = (),
        cursor: str | None = None,
        limit: int | None = None,
    ) -> Command[MetadataPage]: ...

    def query_command(  # type: ignore[misc]
        self, request: MetadataListRequest | None = None, /, **kwargs: object
    ) -> Command[MetadataPage]:
        request = _resolve_request(request, kwargs, MetadataListRequest)
        args = ["issue", "metadata", "list", request.issue_id]
        for predicate in request.predicates:
            args.extend(_predicate_args(predicate))
        if request.cursor is not None:
            args.extend(["--cursor", request.cursor])
        if request.limit is not None:
            args.extend(["--limit", str(request.limit)])

        def finalize(results: tuple[object, ...]) -> MetadataPage:
            result = cast("TextResult", results[0])
            items = tuple(decode_json(result.text.encode("utf-8"), list[MetadataEntry]))
            return MetadataPage(items=items, next_cursor=_extract_metadata_cursor(result.stderr))

        return self._plan(
            steps=(_Step((*args, "--output", "json"), "run_text"),), finalize=finalize
        )

    @overload
    def query(self, request: MetadataListRequest, /) -> MetadataPage: ...

    @overload
    def query(
        self,
        *,
        issue_id: str,
        predicates: tuple[MetadataPredicate, ...] = (),
        cursor: str | None = None,
        limit: int | None = None,
    ) -> MetadataPage: ...

    def query(  # type: ignore[misc]
        self, request: MetadataListRequest | None = None, /, **kwargs: object
    ) -> MetadataPage:
        return self.query_command(cast("MetadataListRequest", request), **kwargs).run()

    def get_command(self, issue_id: str, key: str) -> Command[MetadataEntry]:
        return self._decoded_command(
            ("issue", "metadata", "get", issue_id, "--key", key), MetadataEntry
        )

    def get(self, issue_id: str, key: str) -> MetadataEntry:
        return self.get_command(issue_id, key).run()

    def set_command(self, issue_id: str, key: str, value: MetadataValue) -> Command[MetadataEntry]:
        return self.set_typed_command(MetadataSetRequest(issue_id=issue_id, key=key, value=value))

    def set(self, issue_id: str, key: str, value: MetadataValue) -> MetadataEntry:
        return self.set_command(issue_id, key, value).run()

    @overload
    def set_typed_command(self, request: MetadataSetRequest, /) -> Command[MetadataEntry]: ...

    @overload
    def set_typed_command(
        self,
        *,
        issue_id: str,
        key: str,
        value: MetadataValue,
        value_type: MetadataValueType | None = None,
    ) -> Command[MetadataEntry]: ...

    def set_typed_command(  # type: ignore[misc]
        self, request: MetadataSetRequest | None = None, /, **kwargs: object
    ) -> Command[MetadataEntry]:
        request = _resolve_request(request, kwargs, MetadataSetRequest)
        args = [
            "issue",
            "metadata",
            "set",
            request.issue_id,
            "--key",
            request.key,
            "--value",
            _format_metadata_value(request.value),
        ]
        inferred = request.value_type or _infer_metadata_value_type(request.value)
        if inferred is not None:
            args.extend(["--type", inferred.value])
        return self._decoded_command(tuple(args), MetadataEntry)

    @overload
    def set_typed(self, request: MetadataSetRequest, /) -> MetadataEntry: ...

    @overload
    def set_typed(
        self,
        *,
        issue_id: str,
        key: str,
        value: MetadataValue,
        value_type: MetadataValueType | None = None,
    ) -> MetadataEntry: ...

    def set_typed(  # type: ignore[misc]
        self, request: MetadataSetRequest | None = None, /, **kwargs: object
    ) -> MetadataEntry:
        return self.set_typed_command(cast("MetadataSetRequest", request), **kwargs).run()

    def delete_command(self, issue_id: str, key: str) -> Command[None]:
        return self._none_command(("issue", "metadata", "delete", issue_id, "--key", key))

    def delete(self, issue_id: str, key: str) -> None:
        self.delete_command(issue_id, key).run()


def _infer_metadata_value_type(value: MetadataValue) -> MetadataValueType | None:
    if value is None:
        return MetadataValueType.null
    if isinstance(value, bool):
        return MetadataValueType.boolean
    if isinstance(value, int) and not isinstance(value, bool):
        return MetadataValueType.integer
    if isinstance(value, float):
        return MetadataValueType.number
    if isinstance(value, str):
        return MetadataValueType.string
    return None


def _format_metadata_value(value: MetadataValue) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _predicate_args(predicate: MetadataPredicate) -> list[str]:
    args = ["--metadata", f"{predicate.key}={_format_metadata_value(predicate.value)}"]
    value_type = predicate.value_type or _infer_metadata_value_type(predicate.value)
    if value_type is not None:
        args.extend(["--metadata-type", value_type.value])
    return args


def _extract_metadata_cursor(stderr: str) -> str | None:
    for line in stderr.splitlines():
        if "cursor" in line.lower():
            return line.split()[-1]
    return None
