from __future__ import annotations

import os
import pathlib
import shutil
import tempfile

import msgspec

from .coverage import collect_contract_review_items
from .models import (
    CandidateBaseline,
    PromotionDecision,
    SemanticCLIContract,
    SupportedBaseline,
    UpstreamState,
)
from .normalize import canonical_bytes, semantic_hash
from .paths import SUPPORTED_CONTRACT_REL
from .provenance import is_full_commit
from .schema import decode_contract
from .state import replace_supported

PROMOTION_SCHEMA_VERSION = 1

ALLOWED_TRUST_LEVELS: tuple[str, ...] = ("verified",)


class PromotionError(ValueError):
    """Promotion refused with an explicit failure category."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def validate_promotion(decision: PromotionDecision) -> PromotionDecision:
    if not is_full_commit(decision.candidate_commit):
        raise ValueError(f"candidate_commit must be 40-char hex, got {decision.candidate_commit!r}")
    if not is_full_commit(decision.previous_supported_commit):
        raise ValueError(
            f"previous_supported_commit must be 40-char hex, got {decision.previous_supported_commit!r}"
        )
    if not decision.candidate_semantic_hash.startswith("sha256:"):
        raise ValueError("candidate_semantic_hash must be sha256: prefix")
    if not decision.clean_gate_ref:
        raise ValueError("clean_gate_ref is required")
    if not decision.reviewer:
        raise ValueError("reviewer is required")
    return decision


def apply_promotion(
    state: UpstreamState,
    decision: PromotionDecision,
    candidate: CandidateBaseline,
    *,
    candidate_contract: SemanticCLIContract,
) -> UpstreamState:
    validate_promotion(decision)
    contract_trust = candidate_contract.artifact.trust_level
    if contract_trust not in ALLOWED_TRUST_LEVELS:
        raise PromotionError(
            "trust",
            f"candidate contract trust_level {contract_trust!r} not in {ALLOWED_TRUST_LEVELS}; "
            "refusing to promote",
        )
    if candidate.trust_level not in ALLOWED_TRUST_LEVELS:
        raise PromotionError(
            "trust",
            f"candidate trust_level {candidate.trust_level!r} not in {ALLOWED_TRUST_LEVELS}; "
            "refusing to promote",
        )
    if contract_trust != candidate.trust_level:
        raise PromotionError(
            "trust",
            f"candidate contract trust_level {contract_trust!r} does not match "
            f"state candidate trust_level {candidate.trust_level!r}",
        )
    if candidate.unresolved_items:
        raise PromotionError(
            "unresolved",
            f"candidate has unresolved_items: {', '.join(candidate.unresolved_items)}",
        )
    if state.observed is not None and candidate.version != state.observed.version:
        raise PromotionError(
            "version_mismatch",
            f"candidate.version {candidate.version!r} does not match "
            f"observed.version {state.observed.version!r}",
        )
    _verify_candidate_contract_hash(candidate, decision, candidate_contract)
    review_items = collect_contract_review_items(candidate_contract)
    if review_items:
        raise PromotionError(
            "unresolved",
            f"candidate contract has review_items: {', '.join(review_items)}",
        )
    if candidate.commit != decision.candidate_commit:
        raise ValueError("candidate.commit does not match decision.candidate_commit")
    if candidate.semantic_hash != decision.candidate_semantic_hash:
        raise ValueError("candidate.semantic_hash does not match decision.candidate_semantic_hash")
    if state.supported and state.supported.commit != decision.previous_supported_commit:
        raise ValueError("decision.previous_supported_commit does not match current supported")
    new_supported = SupportedBaseline(
        version=decision.candidate_version,
        tag=decision.candidate_tag,
        commit=decision.candidate_commit,
        semantic_hash=decision.candidate_semantic_hash,
        contract_ref=SUPPORTED_CONTRACT_REL,
    )
    return replace_supported(state, new_supported)


def _verify_candidate_contract_hash(
    candidate: CandidateBaseline,
    decision: PromotionDecision,
    candidate_contract: SemanticCLIContract,
) -> None:
    on_disk_hash = candidate_contract.artifact.semantic_hash
    recomputed_hash = semantic_hash(candidate_contract)
    if on_disk_hash and on_disk_hash != recomputed_hash:
        raise PromotionError(
            "hash_mismatch",
            "on-disk candidate artifact.semantic_hash does not match recomputed digest",
        )
    effective_hash = on_disk_hash if on_disk_hash.startswith("sha256:") else recomputed_hash
    if effective_hash != decision.candidate_semantic_hash:
        raise PromotionError(
            "hash_mismatch",
            "candidate contract semantic_hash does not match promotion decision",
        )
    if effective_hash != candidate.semantic_hash:
        raise PromotionError(
            "hash_mismatch",
            "candidate contract semantic_hash does not match state.candidate.semantic_hash",
        )


def write_promoted_artifacts(
    *,
    repo_root: pathlib.Path,
    new_state: UpstreamState,
    candidate_contract: SemanticCLIContract,
    state_path: pathlib.Path,
) -> None:
    if new_state.supported is None:
        raise ValueError("promoted state must include supported baseline")
    contract_path = repo_root / SUPPORTED_CONTRACT_REL
    contract_payload: dict[str, object] = msgspec.to_builtins(candidate_contract)
    contract_bytes = canonical_bytes(contract_payload) + b"\n"
    state_payload: dict[str, object] = msgspec.to_builtins(new_state)
    state_bytes = canonical_bytes(state_payload) + b"\n"
    parent = contract_path.parent
    parent.mkdir(parents=True, exist_ok=True)
    staging = pathlib.Path(tempfile.mkdtemp(prefix="promote.", dir=str(parent)))
    try:
        staging_contract = staging / contract_path.name
        staging_state = staging / state_path.name
        staging_contract.write_bytes(contract_bytes)
        staging_state.write_bytes(state_bytes)
        os.replace(staging_contract, contract_path)
        os.replace(staging_state, state_path)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def load_candidate_contract(
    repo_root: pathlib.Path,
    candidate: CandidateBaseline,
) -> SemanticCLIContract:
    return decode_contract(repo_root / candidate.contract_ref)


def apply_rejection(
    state: UpstreamState,
    decision: PromotionDecision,
) -> UpstreamState:
    if not decision.reviewer:
        raise ValueError("rejection requires a reviewer")
    if state.candidate is None:
        return state
    return msgspec.structs.replace(state, candidate=None)
