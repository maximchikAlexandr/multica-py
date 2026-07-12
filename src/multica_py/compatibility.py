from __future__ import annotations

import msgspec


class CliVersion(msgspec.Struct, frozen=True, kw_only=True):
    version: str
    commit: str
    build_date: str
    go_version: str
    os: str
    arch: str
    raw_output: str
