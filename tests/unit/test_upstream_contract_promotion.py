"""Unit tests for `multica_py._internal.upstream_contract.promotion`.

These were moved from `tests/contract/test_upstream_contract_promotion.py`
in T044: the contract layer no longer duplicates pure logic that is
exercised here.
"""

from __future__ import annotations

import hashlib
import pathlib

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


# ---------------------------------------------------------------------------
# PromotionTransaction tests (T034)
# ---------------------------------------------------------------------------


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _prepare_repo(tmp_path: pathlib.Path) -> tuple[pathlib.Path, list[bytes]]:
    repo_root = tmp_path / "repo"
    dests = [repo_root / d for d in promotion_module.PROMOTION_DESTINATIONS]
    contents = [f"content{i}".encode() for i in range(5)]
    for d, c in zip(dests, contents):
        d.parent.mkdir(parents=True, exist_ok=True)
        d.write_bytes(c)
    return repo_root, contents


def test_promotion_successful_transaction(tmp_path: pathlib.Path) -> None:
    repo_root, _contents = _prepare_repo(tmp_path)
    new_bytes = [f"new{i}".encode() for i in range(5)]
    txn = promotion_module.PromotionTransaction(repo_root)
    txn.run(*new_bytes)
    dests = [repo_root / d for d in promotion_module.PROMOTION_DESTINATIONS]
    assert all(d.is_file() for d in dests)
    for d, nb in zip(dests, new_bytes):
        assert d.read_bytes() == nb
    lock = tmp_path / "repo" / ".devlocal" / "upstream-promotion.lock"
    journal = tmp_path / "repo" / ".devlocal" / "upstream-promotion-journal.json"
    assert not lock.exists()
    assert not journal.exists()
    for d in dests:
        assert not d.with_name(d.name + ".promote-backup").exists()


@pytest.mark.parametrize("ordinal", [1, 3, 4, 5])
def test_promotion_injected_failure_before_ordinal(tmp_path: pathlib.Path, ordinal: int) -> None:
    repo_root, contents = _prepare_repo(tmp_path)
    orig_hashes = [_sha256(c) for c in contents]
    new_bytes = [f"new{i}".encode() for i in range(5)]
    txn = promotion_module.PromotionTransaction(repo_root, _failure_before=ordinal)
    with pytest.raises(promotion_module.PromotionTransactionError):
        txn.run(*new_bytes)
    dests = [repo_root / d for d in promotion_module.PROMOTION_DESTINATIONS]
    for d, oh in zip(dests, orig_hashes):
        assert d.is_file()
        assert _sha256(d.read_bytes()) == oh, f"{d} was modified"
    lock = tmp_path / "repo" / ".devlocal" / "upstream-promotion.lock"
    assert not lock.exists()


def test_promotion_journal_recovery(tmp_path: pathlib.Path) -> None:
    repo_root, contents = _prepare_repo(tmp_path)
    orig_hashes = [_sha256(c) for c in contents]
    new_bytes = [b"incomplete" for _ in range(5)]
    txn = promotion_module.PromotionTransaction(repo_root, _failure_before=2)
    with pytest.raises(promotion_module.PromotionTransactionError):
        txn.run(*new_bytes)
    journal = repo_root / ".devlocal" / "upstream-promotion-journal.json"
    assert journal.is_file()
    promotion_module.PromotionTransaction.recover_prepared(repo_root)
    assert not journal.exists()
    dests = [repo_root / d for d in promotion_module.PROMOTION_DESTINATIONS]
    for d, oh in zip(dests, orig_hashes):
        assert d.is_file()
        assert _sha256(d.read_bytes()) == oh


def test_promotion_approved_contract_bound_allowed() -> None:
    state = _state_with_supported()
    candidate, decision, contract = _aligned_promotion_inputs()
    contract = msgspec.structs.replace(
        contract,
        artifact=msgspec.structs.replace(contract.artifact, trust_level="approved-contract-bound"),
    )
    digest = semantic_hash(contract)
    contract = msgspec.structs.replace(
        contract,
        artifact=msgspec.structs.replace(contract.artifact, semantic_hash=digest),
    )
    candidate = msgspec.structs.replace(
        candidate, trust_level="approved-contract-bound", semantic_hash=digest
    )
    decision = msgspec.structs.replace(decision, candidate_semantic_hash=digest)
    new_state = promotion_module.apply_promotion(
        state, decision, candidate, candidate_contract=contract
    )
    assert new_state.supported is not None
    assert new_state.supported.version == "0.4.3"
