from __future__ import annotations

import pathlib

import pytest

from tools.upstream_contract.contract import validate_contract
from tools.upstream_contract.generation import (
    RUNTIME_PATH,
    TRANSIENT_PATHS,
    _ensure_transient_root,
    render_files,
)

APPROVED = pathlib.Path("contracts/sdk-contract.json")


def test_sdk_contract() -> None:
    contract = validate_contract(APPROVED)
    files = render_files(APPROVED)
    assert files[0].path == RUNTIME_PATH
    assert tuple(item.path for item in files[1:]) == TRANSIENT_PATHS
    assert len(contract.binding_descriptors) == 79
    assert (
        tuple((item.operation_id, item.entrypoint_id) for item in contract.binding_descriptors)
        != ()
    )
    assert all("state" not in str(item.path) for item in files)


def test_transient_output_rejects_tracked_paths(tmp_path: pathlib.Path) -> None:
    with pytest.raises(ValueError):
        _ensure_transient_root(pathlib.Path("contracts"))
    outside = _ensure_transient_root(tmp_path)
    assert outside == tmp_path.resolve()


def test_runtime_projection_is_single_authoritative_output() -> None:
    files = render_files(APPROVED)
    runtime = files[0].content
    assert runtime.count(b"TARGET_VERSION") == 3
    assert b"approved_contract" not in runtime
    assert b"source path" not in runtime
    assert b"OPERATION_BINDINGS" in runtime
