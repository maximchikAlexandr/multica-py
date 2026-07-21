from __future__ import annotations


def assert_manifest_coverage(
    eligible: frozenset[str],
    covered: frozenset[str],
    gaps: frozenset[str],
    *,
    missing_label: str = "Missing coverage for",
    stale_label: str = "Stale gap entries (have coverage)",
) -> None:
    """Assert eligible manifest operations are covered or explicitly allowlisted."""
    uncovered = eligible - covered - gaps
    stale = covered & gaps
    errors: list[str] = []
    if uncovered:
        errors.append(f"{missing_label}: {sorted(uncovered)}")
    if stale:
        errors.append(f"{stale_label}: {sorted(stale)}")
    assert not errors, "; ".join(errors)
