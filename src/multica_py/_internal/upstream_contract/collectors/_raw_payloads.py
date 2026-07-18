from __future__ import annotations

import msgspec


class RawArgument(msgspec.Struct, frozen=True, kw_only=True):
    min: int = 0
    max: int = 0
    grammar: str | None = None
    validators: tuple[str, ...] = ()
    review_items: tuple[str, ...] = ()


class RawSource(msgspec.Struct, frozen=True, kw_only=True):
    path: str | None = None
    symbol: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    commit: str | None = None
    repository: str | None = None


class RawFlag(msgspec.Struct, frozen=True, kw_only=True):
    name: str
    shorthand: str | None = None
    type: str = "string"
    required: bool = False
    repeatable: bool = False
    default: str | None = None
    enum: tuple[str, ...] = ()
    inherited: bool = False
    deprecated: str | None = None
    source: RawSource | None = None


class RawExecution(msgspec.Struct, frozen=True, kw_only=True):
    interactive: bool = False
    streaming: bool = False
    managed_process: bool = False
    requires_server: bool = True
    exit_behavior: str | None = None


class RawOutput(msgspec.Struct, frozen=True, kw_only=True):
    mode: str = "none"
    schema_ref: str | None = None
    model: str | None = None
    fixture_ref: str | None = None
    decoder_policy: str = "text-only"
    confidence: str = "low"
    negative_fixture_ref: str | None = None
    field_change_policy: str = "permissive-extra-fields"


class RawCommand(msgspec.Struct, frozen=True, kw_only=True):
    path: tuple[str, ...]
    use: str = ""
    aliases: tuple[str, ...] = ()
    hidden: bool = False
    deprecated: str | None = None
    args: RawArgument | None = None
    flags: tuple[RawFlag, ...] = ()
    execution: RawExecution | None = None
    output: RawOutput | None = None
    source: RawSource | None = None


class RawExporterPayload(msgspec.Struct, frozen=True, kw_only=True):
    commands: tuple[RawCommand, ...] = ()
