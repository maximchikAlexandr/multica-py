from __future__ import annotations

import json
import os
import pathlib
import tempfile

LOG_BYTE_LIMIT = 262144
REDACTED = "***"
VERIFICATION_CODE = "888888"

FailureRecord = dict[str, str | int | None]
CleanupRecord = dict[str, object]


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
        """Return the artifact directory root."""
        return self._artifact_dir

    @property
    def cleanup_failed(self) -> bool:
        """Return whether session cleanup failed."""
        return self._cleanup_failed

    def register_secret(self, value: str) -> None:
        """Register an exact secret value for redaction."""
        if value:
            self._secrets.add(value)

    def register_secrets(self, values: list[str]) -> None:
        """Register multiple exact secret values for redaction."""
        for value in values:
            self.register_secret(value)

    def redact(self, text: str) -> str:
        """Redact registered secrets from text."""
        redacted = text
        for secret in sorted(self._secrets, key=len, reverse=True):
            redacted = redacted.replace(secret, REDACTED)
        redacted = redacted.replace(f'"token":"{VERIFICATION_CODE}"', '"token":"***"')
        return redacted

    def write_json(self, filename: str, payload: dict[str, object]) -> None:
        """Write one redacted JSON artifact atomically."""
        serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        self._atomic_write(filename, self.redact(serialized))

    def write_text(self, filename: str, text: str) -> None:
        """Write one redacted text artifact atomically."""
        self._atomic_write(filename, self.redact(text))

    def write_log(self, filename: str, text: str) -> None:
        """Write one bounded, redacted log artifact atomically."""
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
        """Record the primary failure metadata."""
        payload: FailureRecord = {
            "stage": stage,
            "exception_type": exc_type,
            "message": self.redact(message),
            "operation": operation,
            "exit_code": exit_code,
            "resource": resource,
        }
        self._primary_failure = payload
        self.write_json("failure.json", payload)

    def record_cleanup(self, payload: CleanupRecord) -> None:
        """Record cleanup metadata separately from the primary failure."""
        self._cleanup_failure = payload
        self._cleanup_failed = bool(payload.get("failures"))
        self.write_json("cleanup.json", payload)

    def has_secret_leak(self, text: str) -> bool:
        """Return whether text contains a registered secret value."""
        for secret in self._secrets:
            if secret and secret in text:
                return True
        return VERIFICATION_CODE in text

    def scan_text(self, text: str) -> int:
        """Return the number of registered secret matches found in text."""
        count = sum(1 for secret in self._secrets if secret and secret in text)
        if VERIFICATION_CODE in text:
            count += 1
        return count

    def scan_artifact_dir(self) -> int:
        """Return the number of registered secret matches found in artifacts."""
        total = 0
        for path in self._artifact_dir.rglob("*"):
            if not path.is_file():
                continue
            total += self.scan_text(path.read_text(encoding="utf-8", errors="replace"))
        return total

    def assert_no_secret_leak(self, text: str | None = None) -> None:
        """Raise when registered secrets leak into text or the artifact directory."""
        if text is not None:
            if self.has_secret_leak(text):
                raise AssertionError("registered secret value leaked")
            return
        if self.scan_artifact_dir() > 0:
            raise AssertionError("registered secret value leaked")

    def write_secret_scan_report(self) -> None:
        """Write a redaction-safe secret scan report for CI follow-up."""
        finding_count = self.scan_artifact_dir()
        payload = {
            "run_id": self._run_id,
            "finding_count": finding_count,
            "registered_findings": ["registered secret value leaked"] if finding_count else [],
        }
        self.write_json("secret-scan.json", payload)

    @property
    def primary_failure(self) -> FailureRecord | None:
        """Return recorded primary failure metadata."""
        return self._primary_failure

    @property
    def cleanup_failure(self) -> CleanupRecord | None:
        """Return recorded cleanup failure metadata."""
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
            msg = f"invalid artifact filename: {filename!r}"
            raise ValueError(msg)
        target = (self._artifact_dir / filename).resolve()
        if not target.is_relative_to(self._artifact_dir.resolve()):
            msg = f"artifact filename escapes artifact dir: {filename!r}"
            raise ValueError(msg)
        return target


def assert_text_excludes_secrets(text: str, *secret_values: str | None) -> None:
    """Raise AssertionError when text contains a secret without echoing the value.

    Args:
        text: Text that must not contain registered secret values.
        secret_values: Exact secret strings to search for.

    Raises:
        AssertionError: When any secret value appears in ``text``.
    """
    for secret in secret_values:
        if secret and secret in text:
            raise AssertionError("text contains a registered secret value")


def truncate_log(text: str, *, limit: int = LOG_BYTE_LIMIT) -> str:
    """Truncate a log to the configured byte limit with markers."""
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= limit:
        return text
    marker = "\n... [truncated] ...\n"
    marker_bytes = len(marker.encode("utf-8"))
    keep = max(0, (limit - marker_bytes) // 2)
    start = encoded[:keep].decode("utf-8", errors="replace")
    end = encoded[-keep:].decode("utf-8", errors="replace")
    return f"{start}{marker}{end}"
