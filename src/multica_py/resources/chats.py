from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import cast

from multica_py._generated.approved_sdk import CHAT_HISTORY_BINDING, CHAT_THREAD_BINDING
from multica_py._internal.commands import Command, _Step
from multica_py._internal.decoders import decode_json
from multica_py._internal.json_values import _coerce_json_value
from multica_py.config import OperationOptions
from multica_py.models.chats import ChatMessage, ChatPage
from multica_py.resources._base import BaseResource, _operation_minimum_cli_version

__all__ = ["ChatMessage", "ChatPage", "ChatResource"]


def _message(value: Mapping[str, object]) -> ChatMessage:
    def timestamp(raw: object) -> datetime.datetime | None:
        if isinstance(raw, datetime.datetime):
            return raw
        if isinstance(raw, str):
            try:
                return datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    return ChatMessage(
        ts=timestamp(value.get("ts", value.get("timestamp"))),
        role=str(value.get("role", "")),
        author=str(value.get("author", "")),
        text=str(value.get("text", value.get("content", ""))),
        thread_id=cast("str | None", value.get("thread_id")),
        reply_count=cast("int | None", value.get("reply_count")),
        latest_reply=timestamp(value.get("latest_reply")),
        metadata=_coerce_json_value(value.get("metadata"), field_name="chat.metadata")
        if value.get("metadata") is not None
        else None,
    )


def _decode_chat(stdout: bytes, command: str) -> ChatPage:
    raw = decode_json(stdout, dict[str, object], command=command)
    messages = raw.get("messages", ())
    if not isinstance(messages, list | tuple):
        raise TypeError("chat response messages must be an array")
    items = tuple(_message(cast("Mapping[str, object]", item)) for item in messages)
    next_cursor = raw.get("next_cursor")
    raw_total = raw.get("total")
    raw_limit = raw.get("limit")
    return ChatPage(
        items=items,
        total=raw_total if isinstance(raw_total, int) else None,
        limit=raw_limit if isinstance(raw_limit, int) else None,
        next_cursor=next_cursor if isinstance(next_cursor, str) else None,
    )


class ChatResource(BaseResource):
    def history_command(
        self,
        *,
        limit: int | None = None,
        before: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[ChatPage]:
        return self._read_command("history", limit=limit, before=before, options=options)

    def history(
        self,
        *,
        limit: int | None = None,
        before: str | None = None,
        options: OperationOptions | None = None,
    ) -> ChatPage:
        return self.history_command(limit=limit, before=before, options=options).run()

    def thread_command(
        self,
        thread_id: str | None = None,
        *,
        limit: int | None = None,
        before: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[ChatPage]:
        return self._read_command(
            "thread", thread_id=thread_id, limit=limit, before=before, options=options
        )

    def thread(
        self,
        thread_id: str | None = None,
        *,
        limit: int | None = None,
        before: str | None = None,
        options: OperationOptions | None = None,
    ) -> ChatPage:
        return self.thread_command(thread_id, limit=limit, before=before, options=options).run()

    def _read_command(
        self,
        kind: str,
        *,
        thread_id: str | None = None,
        limit: int | None,
        before: str | None,
        options: OperationOptions | None,
    ) -> Command[ChatPage]:
        if limit is not None and (type(limit) is not int or limit < 0):
            raise ValueError("limit must be nonnegative")
        if before is not None and not isinstance(before, str):
            raise TypeError("before must be a string or None")
        args = ["chat", kind]
        if kind == "thread" and thread_id is not None:
            if not thread_id.strip():
                raise ValueError("thread_id must be nonblank")
            args.append(thread_id)
        if limit:
            args.extend(("--limit", str(limit)))
        if before:
            args.extend(("--before", before))
        binding = CHAT_HISTORY_BINDING if kind == "history" else CHAT_THREAD_BINDING
        return self._plan(
            steps=(_Step((*args, "--output", "json"), "run_bytes", decode=_decode_chat),),
            finalize=lambda results: cast("ChatPage", results[0]),
            options=options,
            minimum_cli_version=_operation_minimum_cli_version(cast("object", binding)),
        )
