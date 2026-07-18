from __future__ import annotations

import msgspec

from .models import ObservedRelease, ReleaseObservation, UpstreamState
from .provenance import now_iso


def new_observation(
    *,
    release_id: str,
    version: str,
    tag: str,
) -> ReleaseObservation:
    if not release_id or not version or not tag:
        raise ValueError(
            f"new_observation requires non-empty release_id, version, tag (got "
            f"release_id={release_id!r}, version={version!r}, tag={tag!r})"
        )
    return ReleaseObservation(
        release_id=release_id,
        version=version,
        tag=tag,
        status="new",
    )


def merge_observation(
    state: UpstreamState,
    observation: ReleaseObservation,
) -> UpstreamState:
    if state.observed and state.observed.release_id == observation.release_id:
        return state
    observed = ObservedRelease(
        version=observation.version,
        tag=observation.tag,
        release_id=observation.release_id,
        published_at=now_iso(),
        status="candidate-available" if observation.status == "new" else observation.status,
    )
    new_state = msgspec.structs.replace(state, observed=observed)
    if state.candidate and state.candidate.version != observation.version:
        return superseded_candidate_state(new_state, newer_release_id=observation.release_id)
    return new_state


def superseded_candidate_state(
    state: UpstreamState,
    *,
    newer_release_id: str,
) -> UpstreamState:
    if state.candidate is None:
        return state
    observed = state.observed or ObservedRelease(version="", tag=None, release_id="")
    return msgspec.structs.replace(
        state,
        candidate=None,
        observed=msgspec.structs.replace(
            observed,
            release_id=newer_release_id,
            status="superseded-candidate",
        ),
    )


def record_failed_write(
    state: UpstreamState,
    *,
    reason: str,
) -> UpstreamState:
    if state.observed is None:
        return state
    return msgspec.structs.replace(
        state,
        observed=msgspec.structs.replace(state.observed, status=f"failed:{reason}"),
    )
