from __future__ import annotations

import json
import pathlib
from typing import cast

import pytest

from multica_py._internal.upstream_contract import normalize, schema
from multica_py._internal.upstream_contract.paths import SUPPORTED_CONTRACT_PATH

FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures" / "upstream_contract" / "golden"
SCHEMA_DIR = pathlib.Path(__file__).resolve().parents[2] / "contracts" / "schema"


def test_decode_supported_contract() -> None:
    contract = schema.decode_contract(SUPPORTED_CONTRACT_PATH)
    assert contract.schema_version == 2
    assert contract.baseline.version == "0.4.2"
    assert contract.baseline.commit == "48b8dbf43971e5ea974bf827220cd212a1240c72"
    assert len(contract.commands) == 107


def test_decode_state() -> None:
    state = schema.decode_state(FIXTURES / "upstream-state.json")
    assert state.supported is not None
    assert state.supported.version == "0.4.2"


def test_unknown_schema_version_rejected() -> None:
    text = SUPPORTED_CONTRACT_PATH.read_bytes().replace(
        b'"schema_version":2', b'"schema_version":99'
    )
    with pytest.raises(schema.SchemaVersionError):
        schema.decode_contract(text)


def test_canonical_bytes_are_deterministic() -> None:
    obj = {"b": 1, "a": [3, 2, 1], "nested": {"y": 2, "x": 1}}
    a = normalize.canonical_bytes(obj)
    b = normalize.canonical_bytes(obj)
    assert a == b
    assert a == b'{"a":[3,2,1],"b":1,"nested":{"x":1,"y":2}}'


def test_semantic_hash_excludes_observation() -> None:
    contract = schema.decode_contract(SUPPORTED_CONTRACT_PATH)
    base_hash = normalize.semantic_hash(contract)
    same_semantic = contract
    different_observation = contract
    h1 = normalize.semantic_hash(same_semantic)
    h2 = normalize.semantic_hash(different_observation)
    assert h1 == h2 == base_hash


def test_strict_decoder_policy_field_is_preserved() -> None:
    contract_payload: dict[str, object] = {
        "schema_version": 2,
        "baseline": {
            "state": "candidate",
            "version": "0.4.3",
            "tag": "v0.4.3",
            "commit": "0" * 40,
        },
        "artifact": {
            "semantic_hash": "sha256:0",
            "generator_name": "x",
            "generator_version": "0",
            "generator_commit": "0" * 40,
            "collection_method": "binary-exporter",
        },
        "commands": [
            {
                "path": ["auth", "status"],
                "use": "status",
                "output": {"mode": "json", "decoder_policy": "strict"},
            }
        ],
        "observation": {"generated_at": "2026-01-01T00:00:00Z"},
    }
    decoded = schema.decode_contract(contract_payload)  # type: ignore[arg-type]
    assert decoded.commands[0].output.decoder_policy == "strict"


def test_generate_schema_contains_baseline_field() -> None:
    schema_doc = cast("dict[str, object]", schema.generate_contract_schema())
    defs = schema_doc.get("$defs")
    assert isinstance(defs, dict)
    contract = cast("dict[str, object]", defs["SemanticCLIContract"])
    assert contract["title"] == "SemanticCLIContract"
    properties = contract.get("properties", {})
    assert isinstance(properties, dict)
    assert "baseline" in properties


def test_generate_report_schema() -> None:
    report_schema = cast("dict[str, object]", schema.generate_report_schema())
    report_defs = report_schema.get("$defs")
    assert isinstance(report_defs, dict)
    coverage_report = cast("dict[str, object]", report_defs["CoverageReport"])
    assert coverage_report["title"] == "CoverageReport"


def test_encoders_round_trip() -> None:
    contract = schema.decode_contract(SUPPORTED_CONTRACT_PATH)
    encoded = schema.encode_contract(contract)
    decoded = schema.decode_contract(encoded)
    assert decoded.baseline.commit == contract.baseline.commit


def test_generated_contract_schema_is_valid_json_schema() -> None:
    doc = cast("dict[str, object]", schema.generate_contract_schema())
    defs = doc.get("$defs")
    assert isinstance(defs, dict)
    contract = cast("dict[str, object]", defs["SemanticCLIContract"])
    assert contract["title"] == "SemanticCLIContract"
    assert contract["type"] == "object"
    assert "properties" in contract
    ref = doc.get("$ref")
    assert isinstance(ref, str)
    assert ref.endswith("/SemanticCLIContract")


def test_generated_schemas_match_msgspec_models() -> None:
    contract_doc = cast("dict[str, object]", schema.generate_contract_schema())
    report_doc = cast("dict[str, object]", schema.generate_report_schema())
    contract_defs = contract_doc.get("$defs")
    report_defs = report_doc.get("$defs")
    assert isinstance(contract_defs, dict)
    assert isinstance(report_defs, dict)
    contract = cast("dict[str, object]", contract_defs["SemanticCLIContract"])
    report = cast("dict[str, object]", report_defs["CoverageReport"])
    assert contract["title"] == "SemanticCLIContract"
    assert report["title"] == "CoverageReport"
    assert contract["type"] == "object"
    assert "properties" in contract
    contract_ref = contract_doc.get("$ref")
    assert isinstance(contract_ref, str)
    assert contract_ref.endswith("/SemanticCLIContract")


def test_committed_schema_matches_generator() -> None:
    contract_path = SCHEMA_DIR / "upstream-contract-v2.schema.json"
    report_path = SCHEMA_DIR / "upstream-report-v1.schema.json"
    assert contract_path.is_file()
    assert report_path.is_file()
    committed_contract = cast(
        "dict[str, object]",
        json.loads(contract_path.read_text(encoding="utf-8")),
    )
    committed_report = cast(
        "dict[str, object]",
        json.loads(report_path.read_text(encoding="utf-8")),
    )
    assert normalize.canonical_bytes(committed_contract) == normalize.canonical_bytes(
        cast("dict[str, object]", schema.generate_contract_schema())
    )
    assert normalize.canonical_bytes(committed_report) == normalize.canonical_bytes(
        cast("dict[str, object]", schema.generate_report_schema())
    )
