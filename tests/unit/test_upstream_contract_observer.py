from __future__ import annotations

import msgspec

from multica_py._internal.upstream_contract import observer as observer_module
from multica_py._internal.upstream_contract import state as state_module
from multica_py._internal.upstream_contract.models import (
    CandidateBaseline,
    ObservedRelease,
    SupportedBaseline,
    UpstreamState,
)


def _state() -> UpstreamState:
    return UpstreamState(schema_version=1)


def test_merge_observation_is_idempotent() -> None:
    state = _state()
    observation = observer_module.new_observation(release_id="123", version="0.4.3", tag="v0.4.3")
    state = observer_module.merge_observation(state, observation)
    state_again = observer_module.merge_observation(state, observation)
    assert state.observed is not None
    assert state_again.observed is not None
    assert state.observed.release_id == state_again.observed.release_id


def test_merge_observation_keeps_supported_unchanged() -> None:
    state = UpstreamState(
        schema_version=1,
        supported=SupportedBaseline(
            version="0.4.2",
            tag="v0.4.2",
            commit="0" * 40,
            semantic_hash="sha256:0",
            contract_ref="x.json",
        ),
    )
    state = observer_module.merge_observation(
        state,
        observer_module.new_observation(release_id="123", version="0.4.3", tag="v0.4.3"),
    )
    assert state.supported is not None
    assert state.supported.version == "0.4.2"


def test_record_failed_write_inline() -> None:
    state = UpstreamState(
        schema_version=1,
        supported=SupportedBaseline(
            version="0.4.2",
            tag="v0.4.2",
            commit="0" * 40,
            semantic_hash="sha256:0",
            contract_ref="x.json",
        ),
        observed=ObservedRelease(version="0.4.3", tag="v0.4.3", release_id="r", status="new"),
    )
    observed = state.observed
    assert observed is not None
    new_state = msgspec.structs.replace(
        state,
        observed=msgspec.structs.replace(observed, status="failed:checksum-mismatch"),
    )
    assert new_state.supported == state.supported
    assert "failed" in (new_state.observed.status if new_state.observed else "")


def test_superseded_candidate_state() -> None:
    state = UpstreamState(
        schema_version=1,
        observed=ObservedRelease(version="0.4.2", tag="v0.4.2", release_id="r1", status="new"),
        candidate=CandidateBaseline(
            version="0.4.2",
            tag="v0.4.2",
            commit="0" * 40,
            semantic_hash="sha256:0",
            contract_ref="x.json",
            trust_level="verified",
        ),
    )
    new_state = observer_module.superseded_candidate_state(state, newer_release_id="r2")
    assert new_state.candidate is None
    assert new_state.observed is not None
    assert new_state.observed.status == "superseded-candidate"


def test_record_failed_write() -> None:
    state = UpstreamState(
        schema_version=1,
        observed=ObservedRelease(version="0.4.3", tag="v0.4.3", release_id="r", status="new"),
    )
    new_state = observer_module.record_failed_write(state, reason="checksum-mismatch")
    assert new_state.observed is not None
    assert "failed:checksum-mismatch" in new_state.observed.status


def test_record_failed_write_marks_rerun_needed() -> None:
    state = UpstreamState(
        schema_version=1,
        observed=ObservedRelease(version="0.4.3", tag="v0.4.3", release_id="r"),
    )
    new_state = observer_module.record_failed_write(state, reason="rerun-needed")
    assert new_state.observed is not None
    assert "rerun" in new_state.observed.status


def test_observe_supersede_then_set_candidate_allows_promote() -> None:
    state = UpstreamState(
        schema_version=1,
        supported=SupportedBaseline(
            version="0.4.2",
            tag="v0.4.2",
            commit="0" * 40,
            semantic_hash="sha256:0",
            contract_ref="x.json",
        ),
        observed=ObservedRelease(version="0.4.2", tag="v0.4.2", release_id="r1", status="new"),
        candidate=CandidateBaseline(
            version="0.4.2",
            tag="v0.4.2",
            commit="0" * 40,
            semantic_hash="sha256:0",
            contract_ref="x.json",
            trust_level="verified",
        ),
    )
    state = observer_module.merge_observation(
        state,
        observer_module.new_observation(release_id="r2", version="0.4.4", tag="v0.4.4"),
    )
    assert state.candidate is None
    assert state.observed is not None
    assert state.observed.status == "superseded-candidate"
    new_candidate = CandidateBaseline(
        version="0.4.4",
        tag="v0.4.4",
        commit="abc1234567890abcdef1234567890abcdef12345",
        semantic_hash="sha256:abc",
        contract_ref="y.json",
        trust_level="verified",
    )
    state = state_module.set_candidate(state, new_candidate)
    assert state.observed is not None
    assert state.observed.status == "candidate-available"
    assert state.candidate == new_candidate
