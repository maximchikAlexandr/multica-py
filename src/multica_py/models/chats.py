from __future__ import annotations

import datetime

import msgspec

from multica_py.models.common import Page
from multica_py.types import JsonValue

__all__ = ["ChatMessage", "ChatPage"]


class ChatMessage(msgspec.Struct, frozen=True, kw_only=True):
    ts: datetime.datetime | None = None
    role: str = ""
    author: str = ""
    text: str = ""
    thread_id: str | None = None
    reply_count: int | None = None
    latest_reply: datetime.datetime | None = None
    metadata: JsonValue | None = None


ChatPage = Page[ChatMessage]
