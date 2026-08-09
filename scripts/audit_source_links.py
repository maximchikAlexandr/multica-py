#!/usr/bin/env python3
"""Verify approved source links use the pinned upstream contract target."""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.upstream_contract.contract import ContractError, validate_contract

APPROVED_FILE = Path("contracts/sdk-contract.json")
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


def check_contract_source_links(approved: Path = APPROVED_FILE) -> list[str]:
    """Check contract source IDs, repository identity, and pinned commits."""
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
    return errors


def main() -> int:
    errors = [*check_baseline_sources(), *check_contract_source_links()]
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
