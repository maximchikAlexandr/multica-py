from __future__ import annotations

import msgspec


class CliCompatMatrix(msgspec.Struct, frozen=True, kw_only=True):
    schema_version: int
    sdk_version: str
    min_cli_version: str
    max_cli_version: str
    contract_hashes: dict[str, str] = msgspec.field(default_factory=dict)
    runtime_policy: str = "warn-once"
    override_policy: str = "explicit"
    detection_policy: str = "lazy"
    documentation_ref: str | None = None
