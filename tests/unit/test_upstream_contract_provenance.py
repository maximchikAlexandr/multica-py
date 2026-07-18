from __future__ import annotations

import pytest

from multica_py._internal.upstream_contract import provenance
from multica_py._internal.upstream_contract.models import (
    ObservedRelease,
    SupportedBaseline,
)


def test_is_full_commit_accepts_40_hex() -> None:
    assert provenance.is_full_commit("0" * 40)
    assert provenance.is_full_commit("48b8dbf43971e5ea974bf827220cd212a1240c72")


def test_is_full_commit_rejects_short_or_non_hex() -> None:
    assert not provenance.is_full_commit("abc")
    assert not provenance.is_full_commit("z" * 40)


def test_assert_full_commit_raises() -> None:
    with pytest.raises(provenance.ProvenanceError):
        provenance.assert_full_commit("short", what="test")


def test_assert_no_absolute_path() -> None:
    with pytest.raises(provenance.ProvenanceError):
        provenance.assert_no_absolute_path("/usr/local/bin/multica", what="path")
    with pytest.raises(provenance.ProvenanceError):
        provenance.assert_no_absolute_path("C:\\bin\\multica", what="path")
    provenance.assert_no_absolute_path("relative/path", what="path")


def test_validate_supported_requires_commit() -> None:
    baseline = SupportedBaseline(
        version="0.4.2",
        tag="v0.4.2",
        commit="0" * 40,
        semantic_hash="sha256:abc",
        contract_ref="contract.json",
    )
    out = provenance.validate_supported(baseline)
    assert out is baseline


def test_validate_supported_rejects_invalid_hash() -> None:
    with pytest.raises(provenance.ProvenanceError):
        provenance.validate_supported(
            SupportedBaseline(
                version="0.4.2",
                tag="v0.4.2",
                commit="0" * 40,
                semantic_hash="md5:abc",
                contract_ref="contract.json",
            )
        )


def test_validate_observed_requires_version() -> None:
    out = provenance.validate_observed(
        ObservedRelease(version="0.4.3", tag="v0.4.3", release_id="r1")
    )
    assert out.version == "0.4.3"
