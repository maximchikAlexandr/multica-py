from __future__ import annotations

import msgspec
import pytest

from multica_py._internal.upstream_contract import promotion as promotion_module
from multica_py._internal.upstream_contract import state as state_module
from multica_py._internal.upstream_contract.models import (
    ArtifactMeta,
    Baseline,
    CandidateBaseline,
    CommandContract,
    ExecutionContract,
    ObservedRelease,
    OutputContract,
    PromotionDecision,
    SemanticCLIContract,
    SupportedBaseline,
    UpstreamState,
)
from multica_py._internal.upstream_contract.normalize import semantic_hash
from multica_py._internal.upstream_contract.paths import SUPPORTED_CONTRACT_REL

_COMMIT = "abc1234567890abcdef1234567890abcdef12345"


def test_validate_promotion_requires_full_commit() -> None:
    decision = PromotionDecision(
        schema_version=1,
        candidate_version="0.4.3",
        candidate_tag="v0.4.3",
        candidate_commit="short",
        candidate_semantic_hash="sha256:abc",
        previous_supported_version="0.4.2",
        previous_supported_commit="0" * 40,
        clean_gate_ref="ci/check",
        reviewer="alice",
    )
    with pytest.raises(ValueError):
        promotion_module.validate_promotion(decision)


def test_apply_promotion_refuses_unverified_trust_level() -> None:
    state = _state_with_supported()
    candidate, decision, contract = _aligned_promotion_inputs()
    with pytest.raises(promotion_module.PromotionError):
        promotion_module.apply_promotion(
            state,
            decision,
            msgspec.structs.replace(candidate, trust_level="release-binary"),
            candidate_contract=contract,
        )


def test_apply_promotion_refuses_contract_trust_mismatch() -> None:
    state = _state_with_supported()
    candidate, decision, contract = _aligned_promotion_inputs()
    tampered = msgspec.structs.replace(
        contract,
        artifact=msgspec.structs.replace(contract.artifact, trust_level="release-binary"),
    )
    with pytest.raises(promotion_module.PromotionError) as exc_info:
        promotion_module.apply_promotion(state, decision, candidate, candidate_contract=tampered)
    assert exc_info.value.code == "trust"


def test_apply_promotion_replaces_supported() -> None:
    state = _state_with_supported()
    candidate, decision, contract = _aligned_promotion_inputs()
    new_state = promotion_module.apply_promotion(
        state, decision, candidate, candidate_contract=contract
    )
    assert new_state.supported is not None
    assert new_state.supported.version == "0.4.3"
    assert new_state.supported.contract_ref == SUPPORTED_CONTRACT_REL
    assert new_state.candidate is None


def test_apply_promotion_refuses_version_mismatch_with_observed() -> None:
    state = _state_with_supported()
    state = msgspec.structs.replace(
        state,
        observed=ObservedRelease(
            version="0.4.4",
            tag="v0.4.4",
            release_id="r-new",
            status="new",
        ),
    )
    candidate, decision, contract = _aligned_promotion_inputs()
    with pytest.raises(promotion_module.PromotionError) as exc_info:
        promotion_module.apply_promotion(state, decision, candidate, candidate_contract=contract)
    assert exc_info.value.code == "version_mismatch"


def test_apply_promotion_refuses_hash_mismatch() -> None:
    state = _state_with_supported()
    candidate, decision, contract = _aligned_promotion_inputs()
    tampered = msgspec.structs.replace(
        contract,
        artifact=msgspec.structs.replace(contract.artifact, semantic_hash="sha256:deadbeef"),
    )
    with pytest.raises(promotion_module.PromotionError) as exc_info:
        promotion_module.apply_promotion(state, decision, candidate, candidate_contract=tampered)
    assert exc_info.value.code == "hash_mismatch"


def test_set_candidate_clears_superseded_and_allows_promote() -> None:
    state = UpstreamState(
        schema_version=1,
        supported=SupportedBaseline(
            version="0.4.2",
            tag="v0.4.2",
            commit="0" * 40,
            semantic_hash="sha256:0",
            contract_ref="x.json",
        ),
        observed=ObservedRelease(
            version="0.4.4",
            tag="v0.4.4",
            release_id="r-newer",
            status="superseded-candidate",
        ),
    )
    candidate, decision, contract = _aligned_promotion_inputs(
        version="0.4.4",
        tag="v0.4.4",
        commit=_COMMIT,
    )
    state = state_module.set_candidate(state, candidate)
    assert state.observed is not None
    assert state.observed.status == "candidate-available"
    new_state = promotion_module.apply_promotion(
        state,
        decision,
        candidate,
        candidate_contract=contract,
    )
    assert new_state.supported is not None
    assert new_state.supported.version == "0.4.4"


def test_apply_rejection_clears_candidate() -> None:
    candidate, decision, _contract = _aligned_promotion_inputs()
    state = UpstreamState(
        schema_version=1,
        supported=SupportedBaseline(
            version="0.4.2",
            tag="v0.4.2",
            commit="0" * 40,
            semantic_hash="sha256:0",
            contract_ref="x.json",
        ),
        candidate=candidate,
    )
    new_state = promotion_module.apply_rejection(state, decision)
    assert new_state.candidate is None


def _state_with_supported() -> UpstreamState:
    return UpstreamState(
        schema_version=1,
        supported=SupportedBaseline(
            version="0.4.2",
            tag="v0.4.2",
            commit="0" * 40,
            semantic_hash="sha256:0",
            contract_ref="x.json",
        ),
    )


def _aligned_promotion_inputs(
    *,
    version: str = "0.4.3",
    tag: str = "v0.4.3",
    commit: str = _COMMIT,
) -> tuple[CandidateBaseline, PromotionDecision, SemanticCLIContract]:
    contract = _base_contract(version=version, tag=tag, commit=commit)
    digest = semantic_hash(contract)
    contract = msgspec.structs.replace(
        contract,
        artifact=msgspec.structs.replace(contract.artifact, semantic_hash=digest),
    )
    candidate = CandidateBaseline(
        version=version,
        tag=tag,
        commit=commit,
        semantic_hash=digest,
        contract_ref="x.json",
        trust_level="verified",
    )
    decision = PromotionDecision(
        schema_version=1,
        candidate_version=version,
        candidate_tag=tag,
        candidate_commit=commit,
        candidate_semantic_hash=digest,
        previous_supported_version="0.4.2",
        previous_supported_commit="0" * 40,
        clean_gate_ref="ci/check",
        reviewer="alice",
    )
    return candidate, decision, contract


def _base_contract(*, version: str, tag: str, commit: str) -> SemanticCLIContract:
    return SemanticCLIContract(
        schema_version=2,
        baseline=Baseline(state="candidate", version=version, tag=tag, commit=commit),
        artifact=ArtifactMeta(
            semantic_hash="",
            generator_name="test",
            generator_version="0",
            generator_commit="0" * 40,
            collection_method="binary-exporter",
            trust_level="verified",
        ),
        commands=(
            CommandContract(
                path=("agent",),
                use="list",
                execution=ExecutionContract(),
                output=OutputContract(),
            ),
        ),
    )
