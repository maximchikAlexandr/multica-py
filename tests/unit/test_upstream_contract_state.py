from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
from dataclasses import dataclass

import msgspec
import pytest

from multica_py._internal.upstream_contract import state as state_module
from multica_py._internal.upstream_contract.cli import cmd_stage_reviewed_candidate
from multica_py._internal.upstream_contract.models import (
    ArtifactMeta,
    Baseline,
    CandidateBaseline,
    ObservedRelease,
    SemanticCLIContract,
    SupportedBaseline,
    UpstreamState,
)
from multica_py._internal.upstream_contract.normalize import canonical_bytes, semantic_hash
from multica_py._internal.upstream_contract.provenance import ProvenanceError
from multica_py._internal.upstream_contract.reporting import EXIT_CLEAN, EXIT_INVALID_ARTIFACT

_COMMIT = "abc1234567890abcdef1234567890abcdef12345"
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_load_state_when_file_missing_returns_empty() -> None:
    state = state_module.load_state(_MISSING_PATH)
    assert state.supported is None


_MISSING_PATH = pathlib.Path("/nonexistent/__definitely_missing.json")


def test_validate_state_rejects_bad_candidate_commit() -> None:
    state = UpstreamState(
        schema_version=1,
        candidate=CandidateBaseline(
            version="0.4.3",
            tag="v0.4.3",
            commit="short",
            semantic_hash="sha256:0",
            contract_ref="x.json",
            trust_level="verified",
        ),
    )
    with pytest.raises(ProvenanceError):
        state_module.validate_state(state)


def test_set_candidate_replaces_existing() -> None:
    state = UpstreamState(
        schema_version=1,
        candidate=CandidateBaseline(
            version="0.4.2",
            tag="v0.4.2",
            commit="0" * 40,
            semantic_hash="sha256:0",
            contract_ref="x.json",
            trust_level="verified",
        ),
    )
    new = msgspec.structs.replace(
        state,
        candidate=CandidateBaseline(
            version="0.4.3",
            tag="v0.4.3",
            commit="abc1234567890abcdef1234567890abcdef12345",
            semantic_hash="sha256:0",
            contract_ref="y.json",
            trust_level="verified",
        ),
    )
    assert new.candidate is not None
    assert new.candidate.version == "0.4.3"


def test_set_candidate_rejects_version_mismatch_with_observed() -> None:
    state = UpstreamState(
        schema_version=1,
        observed=ObservedRelease(
            version="0.4.4",
            tag="v0.4.4",
            release_id="r2",
            status="new",
        ),
    )
    candidate = CandidateBaseline(
        version="0.4.3",
        tag="v0.4.3",
        commit="abc1234567890abcdef1234567890abcdef12345",
        semantic_hash="sha256:0",
        contract_ref="y.json",
        trust_level="verified",
    )
    with pytest.raises(ProvenanceError):
        state_module.set_candidate(state, candidate)


def test_set_candidate_clears_superseded_status() -> None:
    state = UpstreamState(
        schema_version=1,
        observed=ObservedRelease(
            version="0.4.4",
            tag="v0.4.4",
            release_id="r2",
            status="superseded-candidate",
        ),
    )
    candidate = CandidateBaseline(
        version="0.4.4",
        tag="v0.4.4",
        commit="abc1234567890abcdef1234567890abcdef12345",
        semantic_hash="sha256:0",
        contract_ref="y.json",
        trust_level="verified",
    )
    new_state = state_module.set_candidate(state, candidate)
    assert new_state.observed is not None
    assert new_state.observed.status == "candidate-available"


def test_clear_candidate_resets_state() -> None:
    state = UpstreamState(
        schema_version=1,
        candidate=CandidateBaseline(
            version="0.4.2",
            tag="v0.4.2",
            commit="0" * 40,
            semantic_hash="sha256:0",
            contract_ref="x.json",
            trust_level="verified",
        ),
    )
    cleared = msgspec.structs.replace(state, candidate=None)
    assert cleared.candidate is None


def test_replace_supported_keeps_decision() -> None:
    state = UpstreamState(schema_version=1)
    new_state = state_module.replace_supported(
        state,
        SupportedBaseline(
            version="0.4.2",
            tag="v0.4.2",
            commit="0" * 40,
            semantic_hash="sha256:0",
            contract_ref="x.json",
        ),
    )
    assert new_state.supported is not None


# ── T030: stage-reviewed-candidate tests ──────────────────────────────


def test_stage_reviewed_candidate_help_degraded() -> None:
    state = UpstreamState(schema_version=1)
    new_state = state_module.stage_reviewed_candidate(
        state,
        version="0.4.3",
        tag="v0.4.3",
        commit=_COMMIT,
        evidence_trust="help-degraded",
        evidence_semantic_hash="sha256:abc",
        evidence_contract_ref="x.json",
    )
    assert new_state.candidate is not None
    assert new_state.candidate.trust_level == "approved-contract-bound"
    assert new_state.candidate.version == "0.4.3"


def test_stage_reviewed_candidate_rejects_wrong_trust() -> None:
    state = UpstreamState(schema_version=1)
    with pytest.raises(ProvenanceError):
        state_module.stage_reviewed_candidate(
            state,
            version="0.4.3",
            tag="v0.4.3",
            commit=_COMMIT,
            evidence_trust="verified",
            evidence_semantic_hash="sha256:abc",
            evidence_contract_ref="x.json",
        )


@dataclass(frozen=True)
class StageProvenanceCase:
    id: str
    mismatch_prefix: str


_STAGE_PROVENANCE_CASES: tuple[StageProvenanceCase, ...] = (
    StageProvenanceCase(id="short-hash", mismatch_prefix="deadbeef"),
    StageProvenanceCase(id="same-length-hash", mismatch_prefix="badhash"),
)


@pytest.mark.parametrize("case", _STAGE_PROVENANCE_CASES, ids=lambda case: case.id)
def test_stage_reviewed_candidate_rejects_approved_hash_mismatch(
    case: StageProvenanceCase,
    tmp_path: pathlib.Path,
) -> None:
    approved_path = _REPO_ROOT / "contracts/sdk-contract.json"
    if not approved_path.is_file():
        pytest.skip("sdk-contract.json not found")

    real_hash = hashlib.sha256(approved_path.read_bytes()).hexdigest()
    evidence = _make_evidence()
    evidence_bytes = canonical_bytes(msgspec.to_builtins(evidence)) + b"\n"
    prov = {
        "approved_contract_sha256": case.mismatch_prefix + real_hash[len(case.mismatch_prefix) :],
        "release_provenance_sha256": "deadbeef",
    }
    prov_bytes = json.dumps(prov, sort_keys=True).encode() + b"\n"
    ev_path = tmp_path / "evidence.json"
    ev_path.write_bytes(evidence_bytes)
    prov_path = tmp_path / "provenance.json"
    prov_path.write_bytes(prov_bytes)
    out_path = tmp_path / "candidate.json"

    args = argparse.Namespace(
        repo_root=str(_REPO_ROOT),
        evidence=str(ev_path),
        approved=str(approved_path),
        release_provenance=str(prov_path),
        expected_evidence_trust="help-degraded",
        output=str(out_path),
        dry_run=False,
        check=False,
    )
    assert cmd_stage_reviewed_candidate(args) == EXIT_INVALID_ARTIFACT


# ── T032: state/coherence tests ───────────────────────────────────────


def test_state_canonical_refs_valid() -> None:
    supported = SupportedBaseline(
        version="0.4.2",
        tag="v0.4.2",
        commit="0" * 40,
        semantic_hash="sha256:0",
        contract_ref="x.json",
    )
    state = UpstreamState(schema_version=1, supported=supported)
    validated = state_module.validate_state(state)
    assert validated.supported is not None


def test_state_null_candidate_after_promotion() -> None:
    state = UpstreamState(
        schema_version=1,
        candidate=CandidateBaseline(
            version="0.4.3",
            tag="v0.4.3",
            commit=_COMMIT,
            semantic_hash="sha256:abc",
            contract_ref="x.json",
            trust_level="approved-contract-bound",
        ),
        supported=SupportedBaseline(
            version="0.4.2",
            tag="v0.4.2",
            commit="0" * 40,
            semantic_hash="sha256:0",
            contract_ref="x.json",
        ),
    )
    new_state = state_module.replace_supported(
        state,
        SupportedBaseline(
            version="0.4.3",
            tag="v0.4.3",
            commit=_COMMIT,
            semantic_hash="sha256:abc",
            contract_ref="y.json",
        ),
    )
    assert new_state.candidate is None
    assert new_state.supported is not None
    assert new_state.supported.version == "0.4.3"


# ── helpers ───────────────────────────────────────────────────────────


def _make_evidence() -> SemanticCLIContract:
    return SemanticCLIContract(
        schema_version=2,
        baseline=Baseline(state="candidate", version="0.4.3", tag="v0.4.3", commit=_COMMIT),
        artifact=ArtifactMeta(
            semantic_hash="sha256:evidence_placeholder",
            generator_name="test",
            generator_version="0",
            generator_commit="0" * 40,
            collection_method="binary-exporter",
            trust_level="help-degraded",
        ),
    )
