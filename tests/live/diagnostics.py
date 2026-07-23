"""Test-only diagnostics hooks over ``tools.live_support.diagnostics``.

Exports the minimum surface live tests need on top of the canonical scan /
redaction helpers in ``tools.live_support.diagnostics``:

  - ``VERIFICATION_CODE``: canonical canary code (also re-exported by
    ``tools.live_support.diagnostics``; defined here for backward compatibility
    with imports that reach into ``tests.live.diagnostics``).
  - ``DiagnosticCollector``: allowlist-based writer with secret redaction,
    primary-failure / cleanup-failure recording, atomic write, and path-traversal
    safety.
  - ``assert_text_excludes_secrets``: assert no exact secret values appear in text.
  - ``truncate_log``: bounded log truncation with start/end markers.

The full ``LiveDiagnosticsBundle`` failure-bundle writer was sandbox-only and
moves with the agent-sandbox workflow to ``tests/live/sandbox/`` in US5.
"""

from __future__ import annotations

import json
import os
import pathlib
import tempfile
from typing import cast

from tools.live_support.diagnostics import VERIFICATION_CODE

LOG_BYTE_LIMIT = 262144
REDACTED = "***"

FailureRecord = dict[str, str | int | None]
CleanupRecord = dict[str, object]

__all__ = [
    "REDACTED",
    "VERIFICATION_CODE",
    "DiagnosticCollector",
    "assert_text_excludes_secrets",
    "truncate_log",
]


class DiagnosticCollector:
    """Allowlist-based diagnostic bundle writer with secret redaction."""

    def __init__(self, artifact_dir: pathlib.Path, run_id: str) -> None:
        self._artifact_dir = artifact_dir
        self._run_id = run_id
        self._secrets: set[str] = set()
        self._primary_failure: FailureRecord | None = None
        self._cleanup_failure: CleanupRecord | None = None
        self._cleanup_failed = False
        self._artifact_dir.mkdir(parents=True, exist_ok=True)

    @property
    def artifact_dir(self) -> pathlib.Path:
        return self._artifact_dir

    @property
    def cleanup_failed(self) -> bool:
        return self._cleanup_failed

    def register_secret(self, value: str) -> None:
        if value:
            self._secrets.add(value)

    def register_secrets(self, values: list[str]) -> None:
        for value in values:
            self.register_secret(value)

    def redact(self, text: str) -> str:
        redacted = text
        for secret in sorted(self._secrets, key=len, reverse=True):
            redacted = redacted.replace(secret, REDACTED)
        redacted = redacted.replace(VERIFICATION_CODE, REDACTED)
        return redacted

    def write_json(self, filename: str, payload: dict[str, object]) -> None:
        serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        self._atomic_write(filename, self.redact(serialized))

    def write_text(self, filename: str, text: str) -> None:
        self._atomic_write(filename, self.redact(text))

    def write_log(self, filename: str, text: str) -> None:
        self.write_text(filename, truncate_log(text))

    def record_failure(
        self,
        *,
        stage: str,
        exc_type: str,
        message: str,
        operation: str | None = None,
        exit_code: int | None = None,
        resource: str | None = None,
    ) -> None:
        payload: FailureRecord = {
            "stage": stage,
            "exception_type": exc_type,
            "message": self.redact(message),
            "operation": operation,
            "exit_code": exit_code,
            "resource": resource,
        }
        self._primary_failure = payload
        self.write_json("failure.json", cast("dict[str, object]", payload))

    def record_cleanup(self, payload: CleanupRecord) -> None:
        self._cleanup_failure = payload
        self._cleanup_failed = bool(payload.get("failures"))
        self.write_json("cleanup.json", payload)
        self.sync_failure_cleanup_errors(payload.get("failures", []))

    def sync_failure_cleanup_errors(self, cleanup_errors: object) -> None:
        failure_path = self._artifact_dir / "failure.json"
        if not failure_path.is_file():
            return
        payload = json.loads(failure_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return
        payload["cleanup_errors"] = cleanup_errors
        self.write_json("failure.json", payload)

    def has_secret_leak(self, text: str) -> bool:
        for secret in self._secrets:
            if secret and secret in text:
                return True
        return VERIFICATION_CODE in text

    def scan_text(self, text: str) -> int:
        count = sum(1 for secret in self._secrets if secret and secret in text)
        if VERIFICATION_CODE in text:
            count += 1
        return count

    def scan_artifact_dir(self) -> int:
        total = 0
        for path in self._artifact_dir.rglob("*"):
            if not path.is_file():
                continue
            total += self.scan_text(path.read_text(encoding="utf-8", errors="replace"))
        return total

    def assert_no_secret_leak(self, text: str | None = None) -> None:
        if text is not None:
            if self.has_secret_leak(text):
                raise AssertionError("registered secret value leaked")
            return
        if self.scan_artifact_dir() > 0:
            raise AssertionError("registered secret value leaked")

    def write_secret_scan_report(self) -> None:
        finding_count = self.scan_artifact_dir()
        payload = {
            "run_id": self._run_id,
            "finding_count": finding_count,
            "registered_findings": ["registered secret value leaked"] if finding_count else [],
        }
        self.write_json("secret-scan.json", payload)

    @property
    def primary_failure(self) -> FailureRecord | None:
        return self._primary_failure

    @property
    def cleanup_failure(self) -> CleanupRecord | None:
        return self._cleanup_failure

    def _atomic_write(self, filename: str, content: str) -> None:
        target = self._resolve_artifact_path(filename)
        fd, temp_name = tempfile.mkstemp(prefix=f"{filename}.", dir=self._artifact_dir)
        temp_path = pathlib.Path(temp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(content)
            temp_path.replace(target)
        finally:
            if temp_path.exists() and not target.exists():
                temp_path.unlink(missing_ok=True)

    def _resolve_artifact_path(self, filename: str) -> pathlib.Path:
        if (
            not filename
            or "/" in filename
            or os.sep in filename
            or (os.altsep is not None and os.altsep in filename)
            or ".." in pathlib.PurePosixPath(filename).parts
        ):
            raise ValueError(f"invalid artifact filename: {filename!r}")
        target = (self._artifact_dir / filename).resolve()
        if not target.is_relative_to(self._artifact_dir.resolve()):
            raise ValueError(f"artifact filename escapes artifact dir: {filename!r}")
        return target


def assert_text_excludes_secrets(text: str, *secret_values: str | None) -> None:
    for secret in secret_values:
        if secret and secret in text:
            raise AssertionError("text contains a registered secret value")


def truncate_log(text: str, *, limit: int = LOG_BYTE_LIMIT) -> str:
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= limit:
        return text
    marker = "\n... [truncated] ...\n"
    marker_bytes = len(marker.encode("utf-8"))
    keep = max(0, (limit - marker_bytes) // 2)
    start = encoded[:keep].decode("utf-8", errors="replace")
    end = encoded[-keep:].decode("utf-8", errors="replace")
    return f"{start}{marker}{end}"
