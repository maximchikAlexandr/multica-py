from __future__ import annotations

import datetime as _dt
import pathlib
import re

from .models import (
    ObservedRelease,
    SupportedBaseline,
)

_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_ABS_PATH_RE = re.compile(r"^/|^[A-Za-z]:[\\/]")


class ProvenanceError(ValueError):
    pass


def is_full_commit(value: str) -> bool:
    return bool(_COMMIT_RE.match(value))


def assert_full_commit(value: str, *, what: str) -> str:
    if not is_full_commit(value):
        raise ProvenanceError(f"{what} must be a 40-character hex commit, got {value!r}")
    return value


def assert_no_absolute_path(value: str, *, what: str) -> str:
    if _ABS_PATH_RE.match(value):
        raise ProvenanceError(f"{what} must not be an absolute path, got {value!r}")
    return value


def assert_contract_ref_contained(ref: str, repo_root: pathlib.Path, *, what: str) -> str:
    """Ensure ``ref`` resolves inside ``repo_root`` without path traversal."""
    assert_no_absolute_path(ref, what=what)
    ref_path = pathlib.Path(ref)
    if ".." in ref_path.parts:
        raise ProvenanceError(f"{what} must not contain .. components, got {ref!r}")
    resolved = (repo_root / ref_path).resolve()
    root = repo_root.resolve()
    if not resolved.is_relative_to(root):
        raise ProvenanceError(f"{what} must resolve inside repo root, got {ref!r}")
    return ref


def now_iso() -> str:
    return _dt.datetime.now(tz=_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_supported(
    baseline: SupportedBaseline,
    *,
    repo_root: pathlib.Path | None = None,
) -> SupportedBaseline:
    assert_full_commit(baseline.commit, what="supported.commit")
    if not baseline.semantic_hash.startswith("sha256:"):
        raise ProvenanceError("supported.semantic_hash must use the sha256: prefix")
    if not baseline.contract_ref:
        raise ProvenanceError("supported.contract_ref is required")
    if repo_root is not None:
        assert_contract_ref_contained(
            baseline.contract_ref,
            repo_root,
            what="supported.contract_ref",
        )
    else:
        assert_no_absolute_path(baseline.contract_ref, what="supported.contract_ref")
    return baseline


def validate_observed(observed: ObservedRelease) -> ObservedRelease:
    if not observed.version:
        raise ProvenanceError("observed.version is required")
    return observed
