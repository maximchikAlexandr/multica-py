#!/usr/bin/env python3
"""Verify the immutable implementation composition and candidate ancestry."""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Sequence


class CompositionError(ValueError):
    """Raised when a candidate does not preserve the approved composition."""


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], check=False, capture_output=True, text=True)
    if result.returncode:
        raise CompositionError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _ancestor(ancestor: str, descendant: str) -> None:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise CompositionError(f"{ancestor} is not an ancestor of {descendant}")


def verify_composition(
    *,
    composition_sha: str,
    planning_sha: str,
    baseline_sha: str,
    integration_sha: str,
    candidate_sha: str,
    openspec_path: str,
) -> None:
    """Assert exact parents and preservation against the immutable SHA inputs."""
    _git("cat-file", "-e", f"{composition_sha}^{{commit}}")
    parents = _git("rev-list", "--parents", "-n", "1", composition_sha).split()
    if parents != [composition_sha, baseline_sha, planning_sha]:
        raise CompositionError("composition does not have the exact baseline/planning parents")
    _ancestor(integration_sha, planning_sha)
    _ancestor(integration_sha, composition_sha)
    _ancestor(composition_sha, candidate_sha)
    diff = subprocess.run(
        ["git", "diff", "--quiet", planning_sha, candidate_sha, "--", openspec_path],
        check=False,
        capture_output=True,
        text=True,
    )
    if diff.returncode:
        raise CompositionError(
            f"candidate OpenSpec subtree differs from planning SHA ({openspec_path})"
        )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--composition-sha", required=True)
    parser.add_argument("--planning-sha", required=True)
    parser.add_argument("--baseline-sha", required=True)
    parser.add_argument("--integration-sha", required=True)
    parser.add_argument("--candidate-sha", default="HEAD")
    parser.add_argument("--openspec-path", default="openspec/changes/update-multica-0-7-0")
    args = parser.parse_args(argv)
    try:
        verify_composition(
            composition_sha=args.composition_sha,
            planning_sha=args.planning_sha,
            baseline_sha=args.baseline_sha,
            integration_sha=args.integration_sha,
            candidate_sha=args.candidate_sha,
            openspec_path=args.openspec_path,
        )
    except CompositionError as exc:
        print(f"Composition verification failed: {exc}", file=sys.stderr)
        return 1
    print(f"Composition {args.composition_sha} is preserved in {args.candidate_sha}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
