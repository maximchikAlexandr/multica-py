from __future__ import annotations

import pathlib

import msgspec

from .models import (
    CoverageManifest,
    CoverageReport,
    JsonScalar,
    PromotionDecision,
    SemanticCLIContract,
    UpstreamContractDiff,
    UpstreamState,
)

CONTRACT_SCHEMA_VERSION = 2
STATE_SCHEMA_VERSION = 1
DIFF_SCHEMA_VERSION = 1
REPORT_SCHEMA_VERSION = 1
BUNDLE_SCHEMA_VERSION = 1
PROMOTION_SCHEMA_VERSION = 1
COVERAGE_SCHEMA_VERSION = 1

SEVERITIES: tuple[str, ...] = (
    "provenance_only",
    "doc_only",
    "additive",
    "potentially_breaking",
    "breaking",
    "mismatch",
)

SEVERITY_BY_KIND: dict[str, str] = {
    "command_added": "additive",
    "command_removed": "breaking",
    "command_moved_or_renamed": "potentially_breaking",
    "command_hidden": "potentially_breaking",
    "command_visible": "additive",
    "argument_added_required": "breaking",
    "argument_added_optional": "additive",
    "argument_removed": "breaking",
    "argument_changed": "breaking",
    "flag_added_required": "breaking",
    "flag_added_optional": "additive",
    "flag_made_optional": "potentially_breaking",
    "flag_removed": "breaking",
    "flag_renamed": "potentially_breaking",
    "flag_changed_type": "breaking",
    "flag_changed_default": "potentially_breaking",
    "flag_enum_widened": "potentially_breaking",
    "flag_enum_narrowed": "breaking",
    "alias_added": "additive",
    "alias_removed": "potentially_breaking",
    "alias_changed": "potentially_breaking",
    "deprecation_added": "potentially_breaking",
    "deprecation_removed": "additive",
    "execution_mode_changed": "potentially_breaking",
    "output_contract_added": "additive",
    "output_contract_removed": "breaking",
    "output_contract_type_changed": "breaking",
    "doc_only_changed": "doc_only",
    "provenance_only_changed": "provenance_only",
    "source_exporter_help_mismatch": "mismatch",
}


class SchemaError(ValueError):
    pass


class SchemaVersionError(SchemaError):
    pass


DecodeInput = bytes | str | pathlib.Path | dict[str, JsonScalar]


def _expect_int(obj: object, field: str) -> int:
    if not isinstance(obj, int):
        raise SchemaError(f"{field} must be an integer")
    return obj


def _decode[T](
    version: int,
    target: type[T],
    data: DecodeInput,
) -> T:
    payload = _read_json(data)
    actual = _expect_int(payload.get("schema_version"), "schema_version")
    if actual != version:
        raise SchemaVersionError(f"unsupported schema version {actual}")
    return msgspec.convert(payload, type=target, strict=True)


def decode_state(data: DecodeInput) -> UpstreamState:
    return _decode(STATE_SCHEMA_VERSION, UpstreamState, data)


def decode_contract(data: DecodeInput) -> SemanticCLIContract:
    return _decode(CONTRACT_SCHEMA_VERSION, SemanticCLIContract, data)


def decode_diff(data: DecodeInput) -> UpstreamContractDiff:
    return _decode(DIFF_SCHEMA_VERSION, UpstreamContractDiff, data)


def decode_coverage(data: DecodeInput) -> CoverageManifest:
    return _decode(COVERAGE_SCHEMA_VERSION, CoverageManifest, data)


def decode_promotion(data: DecodeInput) -> PromotionDecision:
    return _decode(PROMOTION_SCHEMA_VERSION, PromotionDecision, data)


def _read_json(data: DecodeInput) -> dict[str, JsonScalar]:
    if isinstance(data, dict):
        return data
    if isinstance(data, pathlib.Path):
        return _parse(data.read_bytes())
    if isinstance(data, bytes):
        return _parse(data)
    return _parse(data.encode("utf-8"))


def _parse(blob: bytes) -> dict[str, JsonScalar]:
    obj: object = msgspec.json.decode(blob)
    if not isinstance(obj, dict):
        raise SchemaError("artifact must be a JSON object")
    return obj


def generate_contract_schema() -> dict[str, JsonScalar]:
    schema_doc: dict[str, JsonScalar] = msgspec.json.schema(SemanticCLIContract)
    return schema_doc


def generate_report_schema() -> dict[str, JsonScalar]:
    schema_doc: dict[str, JsonScalar] = msgspec.json.schema(CoverageReport)
    return schema_doc


def encode_contract(contract: SemanticCLIContract) -> bytes:
    return msgspec.json.encode(contract)
