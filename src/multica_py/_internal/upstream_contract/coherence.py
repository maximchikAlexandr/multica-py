from __future__ import annotations

import pathlib

from multica_py._internal.upstream_contract.generator.renderer import GeneratedOutput

from .normalize import semantic_hash
from .paths import STATE_REL
from .schema import decode_contract, decode_state


class InvalidArtifactError(Exception):
    pass


def validate_supported_target(repo_root: pathlib.Path) -> None:
    state_path = repo_root / STATE_REL
    if not state_path.exists():
        raise InvalidArtifactError(f"state file not found: {state_path}")
    try:
        state = decode_state(state_path)
    except Exception as exc:
        raise InvalidArtifactError(f"failed to decode state: {exc}") from exc

    if state.supported is None:
        raise InvalidArtifactError("state has no supported baseline")

    contract_path = repo_root / state.supported.contract_ref
    if not contract_path.exists():
        raise InvalidArtifactError(f"supported contract not found: {contract_path}")

    try:
        contract = decode_contract(contract_path)
    except Exception as exc:
        raise InvalidArtifactError(f"failed to decode supported contract: {exc}") from exc

    computed_hash = semantic_hash(contract)
    if computed_hash != state.supported.semantic_hash:
        raise InvalidArtifactError(
            f"supported semantic_hash mismatch: state says "
            f"{state.supported.semantic_hash!r}, "
            f"computed {computed_hash!r}"
        )


def validate_promotion_projection(
    repo_root: pathlib.Path,
    projected_outputs: tuple[GeneratedOutput, ...],
) -> None:
    for out in projected_outputs:
        dest = repo_root / out.path
        if not dest.is_file():
            raise InvalidArtifactError(f"projected output missing: {out.path}")
