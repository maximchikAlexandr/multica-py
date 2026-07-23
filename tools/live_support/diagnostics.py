"""Canonical scan/redaction functions and verification code for live diagnostics.

This module is the shared canonical home for live diagnostic helpers that
scripts and live tests rely on. ``tests.live.diagnostics`` re-exports
``VERIFICATION_CODE`` from here for backward compatibility.

Exports:
  - VERIFICATION_CODE: synthetic canary string used to verify live runs.
  - redact(s: str) -> str: redact common secret patterns from a string.
  - scan_for_secrets(content: str) -> list[str]: detect common secret types.
  - is_canary_response(content: str) -> bool: True if content embeds the
    canary verification code.
"""

from __future__ import annotations

import re

VERIFICATION_CODE = "888888"

__all__ = [
    "VERIFICATION_CODE",
    "is_canary_response",
    "redact",
    "scan_for_secrets",
]

_REDACT_API_KEY = re.compile(r"(MULTICA_API_KEY=)[^\s&]+")
_REDACT_BEARER = re.compile(r"(Authorization:\s*Bearer\s+)[A-Za-z0-9._-]+")
_REDACT_GENERIC_KEY = re.compile(
    r"(api[_-]?key[\"':\s=]+)[A-Za-z0-9._-]+",
    re.IGNORECASE,
)

_SCAN_API_KEY = re.compile(r"MULTICA_API_KEY=[A-Za-z0-9]{16,}")
_SCAN_BEARER_TOKEN = re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}")
_SCAN_OPENAI_KEY = re.compile(r"sk-[A-Za-z0-9]{20,}")


def redact(s: str) -> str:
    """Redact common secret patterns in a string.

    Recognized patterns:
      - ``MULTICA_API_KEY=<value>`` in URL-encoded or shell form.
      - ``Authorization: Bearer <token>`` headers.
      - Generic ``api_key=<value>`` / ``api-key: <value>`` / ``"apiKey":"<value>"``.
    """
    redacted = _REDACT_API_KEY.sub(r"\1***", s)
    redacted = _REDACT_BEARER.sub(r"\1***", redacted)
    redacted = _REDACT_GENERIC_KEY.sub(r"\1***", redacted)
    return redacted


def scan_for_secrets(content: str) -> list[str]:
    """Return a list of detected secret type names in ``content``.

    Each returned name corresponds to a class of secrets that can be safely
    reported without leaking the secret value itself.
    """
    findings: list[str] = []
    if _SCAN_API_KEY.search(content):
        findings.append("api-key")
    if _SCAN_BEARER_TOKEN.search(content):
        findings.append("bearer-token")
    if _SCAN_OPENAI_KEY.search(content):
        findings.append("openai-key")
    return findings


def is_canary_response(content: str) -> bool:
    """Return True if ``content`` embeds the live verification canary."""
    return VERIFICATION_CODE in content
