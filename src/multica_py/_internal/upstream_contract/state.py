from __future__ import annotations

import pathlib

import msgspec

from .models import (
    CandidateBaseline,
    SupportedBaseline,
    UpstreamState,
)
from .paths import DEFAULT_STATE_PATH
from .provenance import (
    ProvenanceError,
    assert_contract_ref_contained,
    is_full_commit,
    validate_observed,
    validate_supported,
)
from .schema import decode_state


def load_state(
    path: pathlib.Path | None = None,
    *,
    repo_root: pathlib.Path | None = None,
) -> UpstreamState:
    target = path or DEFAULT_STATE_PATH
    if not target.exists():
        return UpstreamState.empty()
    state = decode_state(target)
    root = repo_root or target.resolve().parents[3]
    return validate_state(state, repo_root=root)


def set_candidate(state: UpstreamState, candidate: CandidateBaseline) -> UpstreamState:
    if not is_full_commit(candidate.commit):
        raise ProvenanceError(f"candidate.commit must be 40-char hex, got {candidate.commit!r}")
    if state.observed is not None and candidate.version != state.observed.version:
        raise ProvenanceError(
            f"candidate.version {candidate.version!r} does not match "
            f"observed.version {state.observed.version!r}"
        )
    new_state = msgspec.structs.replace(state, candidate=candidate)
    if new_state.observed is not None and new_state.observed.status == "superseded-candidate":
        new_state = msgspec.structs.replace(
            new_state,
            observed=msgspec.structs.replace(
                new_state.observed,
                status="candidate-available",
            ),
        )
    return new_state


def validate_state(state: UpstreamState, *, repo_root: pathlib.Path | None = None) -> UpstreamState:
    if state.supported is not None:
        validate_supported(state.supported, repo_root=repo_root)
    if state.observed is not None:
        validate_observed(state.observed)
    if state.candidate is not None:
        candidate = state.candidate
        if not is_full_commit(candidate.commit):
            raise ProvenanceError(f"candidate.commit must be 40-char hex, got {candidate.commit!r}")
        if repo_root is not None:
            assert_contract_ref_contained(
                candidate.contract_ref,
                repo_root,
                what="candidate.contract_ref",
            )
    return state


def replace_supported(
    state: UpstreamState,
    supported: SupportedBaseline,
) -> UpstreamState:
    validate_supported(supported)
    return msgspec.structs.replace(state, supported=supported, candidate=None)
