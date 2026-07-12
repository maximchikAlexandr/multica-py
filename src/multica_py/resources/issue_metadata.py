from __future__ import annotations

from multica_py._internal.decoders import decode_json
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
from multica_py.resources._base import BaseResource
from multica_py.types import MetadataValue


class IssueMetadataResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)

    def list(self, issue_id: str) -> tuple[MetadataEntry, ...]:
        return self._run_json_decode_list(("issue", "metadata", "list", issue_id), MetadataEntry)

    def query(self, request: MetadataListRequest) -> Page[MetadataEntry]:
        args = ["issue", "metadata", "list", request.issue_id]
        for predicate in request.predicates:
            args.extend(_predicate_args(predicate))
        if request.cursor is not None:
            args.extend(["--cursor", request.cursor])
        if request.limit is not None:
            args.extend(["--limit", str(request.limit)])
        result = self._transport.run_text((*args, "--output", "json"))
        items = tuple(decode_json(result.text.encode("utf-8"), list[MetadataEntry]))
        return Page(items=items, next_cursor=_extract_metadata_cursor(result.stderr))

    def get(self, issue_id: str, key: str) -> MetadataEntry:
        return self._run_json_decode(
            ("issue", "metadata", "get", issue_id, "--key", key), MetadataEntry
        )

    def set(self, issue_id: str, key: str, value: MetadataValue) -> MetadataEntry:
        return self.set_typed(MetadataSetRequest(issue_id=issue_id, key=key, value=value))

    def set_typed(self, request: MetadataSetRequest) -> MetadataEntry:
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
        return self._run_json_decode(tuple(args), MetadataEntry)

    def delete(self, issue_id: str, key: str) -> None:
        self._transport.run_text(("issue", "metadata", "delete", issue_id, "--key", key))


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
