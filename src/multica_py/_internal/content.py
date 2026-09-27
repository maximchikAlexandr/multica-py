"""Safe, execution-time content inputs shared by CLI resources.

The CLI has several spellings for content (inline, file, and stdin).  Keeping
the source as a value object lets command builders choose the reviewed channel
without copying secret handling into every resource.
"""

from __future__ import annotations

import builtins
import io
import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Literal, TextIO, cast

from multica_py.exceptions import ValidationError

ContentKind = Literal["inline", "file", "stream"]


@dataclass(frozen=True, slots=True)
class MaterializedContent:
    """Bytes captured for one command execution.

    ``stream`` is deliberately not retained here: the caller owns it and the
    SDK must never close it.  ``path`` remains available for diagnostics while
    the bytes are used for a stdin or staged file channel.
    """

    data: bytes
    kind: ContentKind
    path: str | None = None
    secret: bool = False

    @property
    def redaction_values(self) -> tuple[str, ...]:
        if not self.secret or not self.data:
            return ()
        return (self.data.decode("utf-8", errors="replace"),)


@dataclass(frozen=True, slots=True)
class SafeContent:
    """A content source that is read only when a command is executed."""

    kind: ContentKind
    value: str | builtins.bytes | os.PathLike[str] | BinaryIO | TextIO
    secret: bool = False

    def __post_init__(self) -> None:
        if self.kind == "inline" and not isinstance(self.value, (str, bytes)):
            raise TypeError("inline content must be text or bytes")
        if self.kind == "file" and not isinstance(self.value, (str, os.PathLike)):
            raise TypeError("file content must be a path")
        if self.kind == "stream" and not isinstance(self.value, io.IOBase):
            raise TypeError("stream content must be a binary or text stream")

    @classmethod
    def inline(cls, value: str | builtins.bytes, *, secret: bool = False) -> SafeContent:
        return cls("inline", value, secret)

    @classmethod
    def text(cls, value: str, *, secret: bool = False) -> SafeContent:
        return cls.inline(value, secret=secret)

    @classmethod
    def bytes(cls, value: builtins.bytes, *, secret: bool = False) -> SafeContent:
        return cls.inline(value, secret=secret)

    @classmethod
    def file(cls, path: str | os.PathLike[str], *, secret: bool = False) -> SafeContent:
        normalized = os.fspath(path)
        if not normalized.strip():
            raise ValueError("content file path must be nonblank")
        return cls("file", normalized, secret)

    @classmethod
    def stream(cls, stream: BinaryIO | TextIO, *, secret: bool = False) -> SafeContent:
        return cls("stream", stream, secret)

    @property
    def path(self) -> str | None:
        value = cast("str | os.PathLike[str]", self.value)
        return os.fspath(value) if self.kind == "file" else None

    @property
    def preview(self) -> str:
        if self.kind == "file":
            return self.path or ""
        if self.secret:
            return "<redacted>"
        return "<content>"

    def read_bytes(self) -> builtins.bytes:
        if self.kind == "inline":
            value = cast("str | builtins.bytes", self.value)
            return value if isinstance(value, builtins.bytes) else value.encode("utf-8")
        if self.kind == "file":
            try:
                return Path(self.path or "").read_bytes()
            except OSError as error:
                raise ValidationError("content file could not be read") from error
        stream = cast("BinaryIO | TextIO", self.value)
        try:
            value = stream.read()
        except (OSError, ValueError) as error:
            raise ValidationError("content stream could not be read") from error
        if isinstance(value, str):
            return value.encode("utf-8")
        if not isinstance(value, builtins.bytes):
            raise TypeError("content stream must return text or bytes")
        return value

    def materialize(self) -> MaterializedContent:
        return MaterializedContent(self.read_bytes(), self.kind, self.path, self.secret)


@contextmanager
def materialize_content(content: SafeContent) -> Iterator[MaterializedContent]:
    """Materialize one source and leave caller-owned streams open."""

    yield content.materialize()


__all__ = ["MaterializedContent", "SafeContent", "materialize_content"]
