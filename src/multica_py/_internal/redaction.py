from __future__ import annotations

import re

REDACTED = "***"

_token_pattern = re.compile(r"--token(?:[= ])(\S+)", re.IGNORECASE)
_token_text_pattern = re.compile(
    r"(?i)(--token(?:=|\s+)|token(?:=|:\s+)|bearer\s+|authorization:\s*)(\S+)"
)
_url_secret_pattern = re.compile(
    r"(?i)([?&#](?:access_token|api_key|key|password|secret|token)=)([^&#\s]+)"
)


def collect_secret_values(argv: tuple[str, ...]) -> tuple[str, ...]:
    secrets: list[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--token" and i + 1 < len(argv):
            secrets.append(argv[i + 1])
            i += 2
            continue
        match = _token_pattern.search(arg)
        if match is not None:
            secrets.append(match.group(1))
        secrets.extend(match.group(2) for match in _url_secret_pattern.finditer(arg))
        i += 1
    return tuple(secret for secret in secrets if secret)


def redact_argv(argv: tuple[str, ...]) -> tuple[str, ...]:
    redacted: list[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--token" and i + 1 < len(argv):
            redacted.extend((arg, REDACTED))
            i += 2
            continue
        redacted.append(_redact_url_secret_arg(_redact_token_arg(arg)))
        i += 1
    return tuple(redacted)


def redact_text(text: str, *, secret_values: tuple[str, ...] = ()) -> str:
    redacted = _token_text_pattern.sub(_redact_token_match, text)
    for secret in secret_values:
        if secret:
            redacted = re.sub(re.escape(secret), REDACTED, redacted, flags=re.IGNORECASE)
    return redacted


def _redact_token_match(match: re.Match[str]) -> str:
    return f"{match.group(1)}{REDACTED}"


def _redact_token_arg(arg: str) -> str:
    return _token_pattern.sub(lambda m: m.group(0).replace(m.group(1), REDACTED), arg)  # type: ignore[misc]


def _redact_url_secret_arg(arg: str) -> str:
    return _url_secret_pattern.sub(_redact_url_secret_match, arg)


def _redact_url_secret_match(match: re.Match[str]) -> str:
    return f"{match.group(1)}{REDACTED}"
