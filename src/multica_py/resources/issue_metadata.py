from __future__ import annotations

from typing import cast

from multica_py._internal.commands import Command, _Step
from multica_py._internal.decoders import decode_json
from multica_py._internal.specs import TextResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig, OperationOptions
from multica_py.enums import MetadataValueType
from multica_py.models.common import ActionResult
from multica_py.models.issue_activity import (
    MetadataEntry,
    MetadataPage,
    MetadataPredicate,
)
from multica_py.resources._base import BaseResource
from multica_py.types import MetadataValue


class IssueMetadataResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)

    def list_command(
        self, issue_id: str, *, options: OperationOptions | None = None
    ) -> Command[dict[str, MetadataValue]]:
        args = ("issue", "metadata", "list", issue_id, "--output", "json")

        def decode(stdout: bytes, command: str) -> object:
            return decode_json(stdout, dict[str, MetadataValue], command=command)

        return self._plan(
            steps=(_Step(args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("dict[str, MetadataValue]", results[0]),
            options=options,
        )

    def list(
        self, issue_id: str, *, options: OperationOptions | None = None
    ) -> dict[str, MetadataValue]:
        return self.list_command(issue_id, options=options).run()

    def query_command(
        self,
        *,
        issue_id: str,
        predicates: tuple[MetadataPredicate, ...] = (),
        cursor: str | None = None,
        limit: int | None = None,
        options: OperationOptions | None = None,
    ) -> Command[MetadataPage]:
        args = ["issue", "metadata", "list", issue_id]
        for predicate in predicates:
            args.extend(_predicate_args(predicate))
        if cursor is not None:
            args.extend(["--cursor", cursor])
        if limit is not None:
            if limit < 0:
                raise ValueError("limit must be nonnegative")
            args.extend(["--limit", str(limit)])

        def finalize(results: tuple[object, ...]) -> MetadataPage:
            result = cast("TextResult", results[0])
            items = tuple(decode_json(result.text.encode("utf-8"), list[MetadataEntry]))
            return MetadataPage(
                items=items,
                total=len(items),
                next_cursor=_extract_metadata_cursor(result.stderr),
            )

        return self._plan(
            steps=(_Step((*args, "--output", "json"), "run_text"),),
            finalize=finalize,
            options=options,
        )

    def query(
        self,
        *,
        issue_id: str,
        predicates: tuple[MetadataPredicate, ...] = (),
        cursor: str | None = None,
        limit: int | None = None,
        options: OperationOptions | None = None,
    ) -> MetadataPage:
        return self.query_command(
            issue_id=issue_id,
            predicates=predicates,
            cursor=cursor,
            limit=limit,
            options=options,
        ).run()

    def get_command(
        self, issue_id: str, key: str, *, options: OperationOptions | None = None
    ) -> Command[MetadataEntry]:
        return self._decoded_command(
            ("issue", "metadata", "get", issue_id, "--key", key),
            MetadataEntry,
            options=options,
        )

    def get(
        self, issue_id: str, key: str, *, options: OperationOptions | None = None
    ) -> MetadataEntry:
        return self.get_command(issue_id, key, options=options).run()

    def set_command(
        self,
        issue_id: str,
        key: str,
        value: MetadataValue,
        *,
        options: OperationOptions | None = None,
    ) -> Command[MetadataEntry]:
        return self.set_typed_command(issue_id=issue_id, key=key, value=value, options=options)

    def set(
        self,
        issue_id: str,
        key: str,
        value: MetadataValue,
        *,
        options: OperationOptions | None = None,
    ) -> MetadataEntry:
        return self.set_command(issue_id, key, value, options=options).run()

    def set_typed_command(
        self,
        *,
        issue_id: str,
        key: str,
        value: MetadataValue,
        value_type: MetadataValueType | None = None,
        options: OperationOptions | None = None,
    ) -> Command[MetadataEntry]:
        args = [
            "issue",
            "metadata",
            "set",
            issue_id,
            "--key",
            key,
            "--value",
            _format_metadata_value(value),
        ]
        inferred = value_type or _infer_metadata_value_type(value)
        if inferred is not None:
            args.extend(["--type", inferred.value])
        return self._decoded_command(tuple(args), MetadataEntry, options=options)

    def set_typed(
        self,
        *,
        issue_id: str,
        key: str,
        value: MetadataValue,
        value_type: MetadataValueType | None = None,
        options: OperationOptions | None = None,
    ) -> MetadataEntry:
        return self.set_typed_command(
            issue_id=issue_id, key=key, value=value, value_type=value_type, options=options
        ).run()

    def delete_command(
        self, issue_id: str, key: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        return self._action_command(
            ("issue", "metadata", "delete", issue_id, "--key", key), options=options
        )

    def delete(
        self, issue_id: str, key: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.delete_command(issue_id, key, options=options).run()


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
