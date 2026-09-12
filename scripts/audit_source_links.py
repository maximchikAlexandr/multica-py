#!/usr/bin/env python3
"""Verify approved source links use the pinned upstream contract target."""

from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
import tarfile
from collections.abc import Iterator
from functools import cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.upstream_contract.contract import (
    ContractCatalog,
    ContractError,
    _response_source_url,
    validate_contract,
)

APPROVED_FILE = Path("contracts/sdk-contract.json")
DEFAULT_SOURCE_CHECKOUT = Path(
    ".devlocal/upstream-contract/v0.4.42..v0.4.43/source-repo/"
    ".devlocal/upstream-contract/v0.4.42..v0.4.43/source-0.4.43"
)
BASELINE_FILES = (
    "openspec/specs/sdk-surface/spec.md",
    "openspec/specs/subprocess-transport/spec.md",
    "openspec/specs/upstream-contract/spec.md",
    "openspec/specs/verification-and-release/spec.md",
)


def check_baseline_sources() -> list[str]:
    """Check embedded baseline links without treating them as contract input."""
    errors: list[str] = []
    for baseline_file in BASELINE_FILES:
        try:
            content = Path(baseline_file).read_text(encoding="utf-8")
        except FileNotFoundError:
            errors.append(f"Baseline file not found: {baseline_file}")
            continue

        refs = re.findall(r"blob/([a-f0-9]+)/", content)
        if refs:
            errors.append(f"Baseline source URLs require an approved target audit: {baseline_file}")
        else:
            print(f"[OK] Baseline has no embedded source URLs: {baseline_file}")
    return errors


def _source_ids(value: object) -> Iterator[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "source_ref_id" and isinstance(item, str):
                yield item
            elif key == "source_ref_ids" and isinstance(item, list):
                yield from (source_id for source_id in item if isinstance(source_id, str))
            else:
                yield from _source_ids(item)
    elif isinstance(value, list):
        for item in value:
            yield from _source_ids(item)


@cache
def _git_sources(checkout: str, commit: str) -> dict[str, list[str]]:
    try:
        result = subprocess.run(
            ["git", "-C", checkout, "archive", "--format=tar", commit, "--", "*.go"],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return {}
    sources: dict[str, list[str]] = {}
    with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r:") as archive:
        for member in archive.getmembers():
            if not member.isfile() or not member.name.endswith(".go"):
                continue
            content = archive.extractfile(member)
            if content is not None:
                sources[member.name] = content.read().decode("utf-8", errors="replace").splitlines()
    return sources


def _git_source(checkout: str, commit: str, path: str) -> list[str] | None:
    return _git_sources(checkout, commit).get(path)


def check_registry_source_links(catalog: ContractCatalog, source_checkout: Path) -> list[str]:
    """Check every response registry URL against both pinned repository trees."""
    errors: list[str] = []
    registry = catalog.compatibility.response_registry
    for item in registry:
        for url in item.source_urls:
            commit, path, start, end = _response_source_url(url, "response registry source URL")
            lines = _git_source(str(source_checkout), commit, path)
            if lines is None:
                errors.append(
                    f"Response registry {item.work_item_id} references missing {commit}:{path}"
                )
                continue
            if end > len(lines):
                errors.append(
                    f"Response registry {item.work_item_id} range exceeds {commit}:{path} ({end}>{len(lines)})"
                )
                continue
            selected = [line.strip() for line in lines[start - 1 : end] if line.strip()]
            if not selected or all(line == "package main" for line in selected):
                errors.append(
                    f"Response registry {item.work_item_id} has a non-substantive source range: {url}"
                )
    return errors


def check_contract_source_links(
    approved: Path = APPROVED_FILE, source_checkout: Path | None = None
) -> list[str]:
    """Check contract source IDs and every pinned registry range."""
    try:
        catalog = validate_contract(approved)
    except (ContractError, OSError) as exc:
        return [f"Approved contract is not valid: {exc}"]

    errors: list[str] = []
    source_ids = {item.source_ref_id for item in catalog.source_refs}
    if any(item.repository != "multica-ai/multica" for item in catalog.source_refs):
        errors.append("Every approved source reference must target multica-ai/multica")
    if any(item.commit != catalog.target.commit for item in catalog.source_refs):
        errors.append("Every approved source reference must use target.commit")

    raw = catalog.raw
    referenced_ids = set(_source_ids(raw.get("operations")))
    catalogs = raw.get("catalogs")
    if isinstance(catalogs, dict):
        referenced_ids.update(_source_ids(catalogs.get("binding_source_refs")))
        referenced_ids.update(_source_ids(catalogs.get("update_field_policies")))
    unknown_ids = referenced_ids - source_ids
    if unknown_ids:
        errors.append(f"Approved source references are unknown: {', '.join(sorted(unknown_ids))}")

    if not errors:
        print(
            f"[OK] {len(catalog.source_refs)} contract source links target "
            f"multica-ai/multica@{catalog.target.commit}"
        )
        if source_checkout is not None:
            errors.extend(check_registry_source_links(catalog, source_checkout))
        print(
            f"[OK] {len(catalog.compatibility.response_registry)} response registry items are pinned"
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-checkout", type=Path, default=DEFAULT_SOURCE_CHECKOUT)
    args = parser.parse_args()
    source_checkout = args.source_checkout if args.source_checkout.exists() else None
    errors = [
        *check_baseline_sources(),
        *check_contract_source_links(source_checkout=source_checkout),
    ]
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
