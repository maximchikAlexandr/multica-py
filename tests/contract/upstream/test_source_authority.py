"""Source authority validation tests.

Every test validates source refs from the approved seed and source-authority
against the pinned upstream checkout at .devlocal/upstream/multica-v0.4.9.
"""

from __future__ import annotations

import pathlib
from collections.abc import Callable

import pytest

from multica_py._internal.upstream_contract.generator.validation import (
    load_approved_contract_v2,
)
from multica_py._internal.upstream_contract.source_validation import (
    validate_commit,
    validate_source_authority,
)

ROOT = pathlib.Path(__file__).resolve().parents[3]
SEED = ROOT / "contracts/sdk-contract.json"
SOURCE_AUTHORITY_JSON = ROOT / "specs/007-upstream-v0-4-9-migration/contracts/source-authority.json"
SOURCE_AUTHORITY_MD = ROOT / "specs/007-upstream-v0-4-9-migration/contracts/source-authority.md"
SOURCE_ROOT = ROOT / ".devlocal/upstream/multica-v0.4.9"
EXPECTED_COMMIT = "ecbdbda09e7b2be56cd9ccc55cee1ee360222d18"

_SOURCE_ROOT_REASON: str | None = None
if not (SOURCE_ROOT / ".git").is_dir():
    _SOURCE_ROOT_REASON = f"pinned checkout missing: {SOURCE_ROOT}"


def test_source_authority_commit_verified() -> None:
    if _SOURCE_ROOT_REASON is not None:
        pytest.skip(_SOURCE_ROOT_REASON)
    contract = load_approved_contract_v2(SEED)
    validate_source_authority(SOURCE_ROOT, contract, SOURCE_AUTHORITY_JSON)


def test_source_authority_rejects_wrong_commit(
    repo_factory: Callable[..., pathlib.Path],
) -> None:
    repo = repo_factory(initial_commits=1)
    with pytest.raises(ValueError, match="commit mismatch"):
        validate_commit(repo, EXPECTED_COMMIT)
