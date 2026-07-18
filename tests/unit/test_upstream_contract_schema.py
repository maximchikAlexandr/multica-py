from __future__ import annotations

import json
import pathlib

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
    text = SUPPORTED_CONTRACT_PATH.read_bytes().replace(b'"schema_version":2', b'"schema_version":99')
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


def test_generate_schema_contains_baseline_field() -> None:
    schema_doc = schema.generate_contract_schema()
    contract = schema_doc["$defs"]["SemanticCLIContract"]
    assert contract["title"] == "SemanticCLIContract"
    properties = contract.get("properties", {})
    assert isinstance(properties, dict)
    assert "baseline" in properties


def test_generate_report_schema() -> None:
    report_schema = schema.generate_report_schema()
    assert report_schema["$defs"]["CoverageReport"]["title"] == "CoverageReport"


def test_encoders_round_trip() -> None:
    contract = schema.decode_contract(SUPPORTED_CONTRACT_PATH)
    encoded = schema.encode_contract(contract)
    decoded = schema.decode_contract(encoded)
    assert decoded.baseline.commit == contract.baseline.commit


def test_generated_contract_schema_is_valid_json_schema() -> None:
    doc = schema.generate_contract_schema()
    contract = doc["$defs"]["SemanticCLIContract"]
    assert contract["title"] == "SemanticCLIContract"
    assert contract["type"] == "object"
    assert "properties" in contract
    assert "$ref" in doc
    assert doc["$ref"].endswith("/SemanticCLIContract")


def test_generated_schemas_match_msgspec_models() -> None:
    contract_doc = schema.generate_contract_schema()
    report_doc = schema.generate_report_schema()
    contract = contract_doc["$defs"]["SemanticCLIContract"]
    report = report_doc["$defs"]["CoverageReport"]
    assert contract["title"] == "SemanticCLIContract"
    assert report["title"] == "CoverageReport"
    assert contract["type"] == "object"
    assert "properties" in contract
    assert "$ref" in contract_doc
    assert contract_doc["$ref"].endswith("/SemanticCLIContract")


def test_committed_schema_matches_generator() -> None:
    contract_path = SCHEMA_DIR / "upstream-contract-v2.schema.json"
    report_path = SCHEMA_DIR / "upstream-report-v1.schema.json"
    assert contract_path.is_file()
    assert report_path.is_file()
    committed_contract = json.loads(contract_path.read_text(encoding="utf-8"))
    committed_report = json.loads(report_path.read_text(encoding="utf-8"))
    assert normalize.canonical_bytes(committed_contract) == normalize.canonical_bytes(
        schema.generate_contract_schema()
    )
    assert normalize.canonical_bytes(committed_report) == normalize.canonical_bytes(
        schema.generate_report_schema()
    )
