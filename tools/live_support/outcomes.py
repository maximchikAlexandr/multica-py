"""Outcome models and helpers for live test tooling.

Exports:
  - OutcomeCategory: passed, failed, timeout, unrunnable, infrastructure_error, auth_error
  - OutcomeStage: smoke, extended, stability, mutation, aggregate
  - TargetFingerprint: frozen msgspec Struct with version, tag, commit, sha256
  - JUnitCounts: frozen msgspec Struct with tests, failures, errors, skipped
  - LiveOutcome: frozen msgspec Struct for a single live test outcome
  - MutationOutcome: frozen msgspec Struct for mutation-test outcomes
  - parse_junit: parse a JUnit XML file into JUnitCounts
  - normalize_message: redact paths, timestamps, durations, and secrets
  - compare_candidate_to_control: regresson check between JUnitCounts
"""

from __future__ import annotations

import pathlib
import re
import xml.etree.ElementTree as ET
from enum import StrEnum

import msgspec

from tools.live_support.diagnostics import redact


class OutcomeCategory(StrEnum):
    passed = "passed"
    failed = "failed"
    timeout = "timeout"
    unrunnable = "unrunnable"
    infrastructure_error = "infrastructure_error"
    auth_error = "auth_error"


class OutcomeStage(StrEnum):
    smoke = "smoke"
    extended = "extended"
    stability = "stability"
    mutation = "mutation"
    aggregate = "aggregate"


class TargetFingerprint(msgspec.Struct, frozen=True):
    version: str
    tag: str
    commit: str
    sha256: str


class JUnitCounts(msgspec.Struct, frozen=True):
    tests: int
    failures: int
    errors: int
    skipped: int


class LiveOutcome(msgspec.Struct, frozen=True):
    operation_id: str
    category: OutcomeCategory
    stage: OutcomeStage
    duration_ms: int
    message: str
    fingerprint: TargetFingerprint


class MutationOutcome(msgspec.Struct, frozen=True):
    target: str
    control_fingerprint: TargetFingerprint
    mutated_fingerprint: TargetFingerprint
    killed: bool
    control_path: str
    mutated_path: str


_PATH_PATTERN = re.compile(r"(/[A-Za-z0-9._-]+)+")
_TIMESTAMP_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}")
_DURATION_PATTERN = re.compile(r"\d+\.\d+s")


def normalize_message(msg: str) -> str:
    """Redact paths, timestamps, durations, and known secrets from a message."""
    result = _PATH_PATTERN.sub("<path>", msg)
    result = _TIMESTAMP_PATTERN.sub("<timestamp>", result)
    result = _DURATION_PATTERN.sub("<duration>", result)
    result = redact(result)
    return result


def parse_junit(junit_path: pathlib.Path) -> JUnitCounts:
    """Parse a JUnit XML file and return aggregated test counts."""
    tree = ET.parse(junit_path)
    root = tree.getroot()
    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_skipped = 0
    for suite in root.iter("testsuite"):
        total_tests += int(suite.get("tests", 0))
        total_failures += int(suite.get("failures", 0))
        total_errors += int(suite.get("errors", 0))
        total_skipped += int(suite.get("skipped", 0))
    return JUnitCounts(
        tests=total_tests,
        failures=total_failures,
        errors=total_errors,
        skipped=total_skipped,
    )


def compare_candidate_to_control(control: JUnitCounts, candidate: JUnitCounts) -> bool:
    """Return True if candidate has not regressed relative to control."""
    if candidate.failures > control.failures:
        return False
    return candidate.errors <= control.errors


__all__ = [
    "JUnitCounts",
    "LiveOutcome",
    "MutationOutcome",
    "OutcomeCategory",
    "OutcomeStage",
    "TargetFingerprint",
    "compare_candidate_to_control",
    "normalize_message",
    "parse_junit",
]
