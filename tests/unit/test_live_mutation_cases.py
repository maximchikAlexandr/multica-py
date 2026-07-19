"""Ensure SC-002 mutation patch strings still match current sources."""

from __future__ import annotations

from scripts.run_live_tests import MUTATION_CASES, REPO_ROOT


def test_mutation_case_originals_exist_in_pinned_sources() -> None:
    """Each mutation original fragment must remain present for --mutation-check."""
    for case in MUTATION_CASES:
        source = (REPO_ROOT / case.path).read_text(encoding="utf-8")
        assert case.original in source, f"{case.name}: original fragment missing in {case.path}"
