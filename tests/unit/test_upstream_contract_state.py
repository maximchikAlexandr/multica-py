from __future__ import annotations

import os
import pathlib
import tempfile

import msgspec

from multica_py._internal.upstream_contract import state as state_module
from multica_py._internal.upstream_contract.models import (
    CandidateBaseline,
    ObservedRelease,
    SupportedBaseline,
    UpstreamState,
)


def test_load_state_when_file_missing_returns_empty() -> None:
    state = state_module.load_state(__missing_path())
    assert state.supported is None


def __missing_path() -> pathlib.Path:
    fd, name = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    os.unlink(name)
    return pathlib.Path(name)


def test_validate_state_rejects_bad_candidate_commit() -> None:
    import pytest

    from multica_py._internal.upstream_contract.provenance import ProvenanceError

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
    import pytest

    from multica_py._internal.upstream_contract.provenance import ProvenanceError

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
