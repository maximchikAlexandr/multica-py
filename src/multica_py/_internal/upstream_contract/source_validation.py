"""Validate source refs in an ApprovedContractV2 against a pinned checkout."""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from typing import cast

from .generator.schema import ApprovedContractV2, SourceRef
from .generator.validation import load_approved_contract_v2
from .reporting import EXIT_CLEAN, EXIT_INVALID_ARTIFACT


def validate_commit(source_root: pathlib.Path, expected_commit: str) -> None:
    result = subprocess.run(
        ["git", "-C", str(source_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    actual = result.stdout.strip()
    if actual != expected_commit:
        raise ValueError(f"commit mismatch: expected {expected_commit}, got {actual}")


def validate_source_ref(source_root: pathlib.Path, ref: SourceRef) -> None:
    file_path = source_root / ref.path
    if not file_path.is_file():
        raise FileNotFoundError(f"source file not found: {file_path}")

    lines = file_path.read_text().splitlines()
    if ref.line_start < 1 or ref.line_start > len(lines):
        raise ValueError(f"line_start {ref.line_start} out of bounds (file has {len(lines)} lines)")

    end = ref.line_end if ref.line_end <= len(lines) else len(lines)
    symbols = ref.symbol.split("/")
    range_text = "\n".join(lines[ref.line_start - 1 : end])
    for sym in symbols:
        if sym not in range_text:
            raise ValueError(
                f"symbol {sym!r} not found in {ref.path}:{ref.line_start}-{ref.line_end}"
            )


def validate_source_authority(
    source_root: pathlib.Path,
    contract: ApprovedContractV2,
    source_authority_path: pathlib.Path,
) -> None:
    validate_commit(source_root, contract.target.commit)

    raw: object = json.loads(source_authority_path.read_text())
    assert isinstance(raw, dict)
    refs_raw: object = raw.get("refs", [])
    assert isinstance(refs_raw, list)

    family_refs: list[dict[str, object]] = []
    for item in refs_raw:
        assert isinstance(item, dict)
        family_refs.append(cast("dict[str, object]", item))

    repository = cast("str", raw.get("repository", ""))
    commit = cast("str", raw.get("commit", ""))

    for fr in family_refs:
        ref = SourceRef(
            source_ref_id=cast("str", fr["id"]),
            repository=repository,
            commit=commit,
            path=cast("str", fr["path"]),
            symbol=cast("str", fr["symbol"]),
            line_start=cast("int", fr["line_start"]),
            line_end=cast("int", fr["line_end"]),
        )
        validate_source_ref(source_root, ref)

    for ref in contract.source_refs:
        validate_source_ref(source_root, ref)


def validate_source_cli(args: argparse.Namespace) -> int:
    source_root = pathlib.Path(cast("str", args.source_root))
    contract_path = pathlib.Path(cast("str", args.approved))

    try:
        contract = load_approved_contract_v2(contract_path)
    except (ValueError, FileNotFoundError) as exc:
        sys.stderr.write(f"failed to load approved contract: {exc}\n")
        return EXIT_INVALID_ARTIFACT

    source_authority_path = pathlib.Path(contract.scope.source_authority_ref)
    if not source_authority_path.is_absolute():
        source_authority_path = (
            pathlib.Path(cast("str", args.repo_root)) / source_authority_path
        ).resolve()

    try:
        validate_source_authority(source_root, contract, source_authority_path)
    except (ValueError, FileNotFoundError) as exc:
        sys.stderr.write(f"source validation failed: {exc}\n")
        return EXIT_INVALID_ARTIFACT

    sys.stdout.write("source validation passed\n")
    return EXIT_CLEAN
