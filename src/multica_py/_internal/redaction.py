from __future__ import annotations

import re
from collections.abc import Iterable, Mapping

REDACTED = "***"

_token_pattern = re.compile(r"--token(?:[= ])(\S+)", re.IGNORECASE)
_token_text_pattern = re.compile(
    r"(?i)(--token(?:=|\s+)|token(?:=|:\s+)|bearer\s+|authorization:\s*)(\S+)"
)
_url_secret_pattern = re.compile(
    r"(?i)([?&#](?:access_token|api_key|key|password|secret|token)=)([^&#\s]+)"
)
_secret_env_key_pattern = re.compile(
    r"(?i)(?:^|_)(?:access[_-]?key|api[_-]?key|auth[_-]?token|"
    r"client[_-]?secret|credential|password|passwd|private[_-]?key|secret|token)(?:$|_)"
)


def collect_secret_values(argv: tuple[str, ...]) -> tuple[str, ...]:
    secrets: list[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if (
            arg == "config"
            and i + 3 < len(argv)
            and argv[i + 1] == "set"
            and _secret_env_key_pattern.search(argv[i + 2]) is not None
        ):
            secrets.append(argv[i + 3])
            i += 4
            continue
        if arg == "--token" and i + 1 < len(argv):
            secrets.append(argv[i + 1])
            i += 2
            continue
        match = _token_pattern.search(arg)
        if match is not None:
            secrets.append(match.group(1))
        secrets.extend(match.group(2) for match in _url_secret_pattern.finditer(arg))
        i += 1
    return normalize_secret_values(secrets)


def collect_secret_values_from_environment(env: Mapping[str, str]) -> tuple[str, ...]:
    """Collect values from environment keys that conventionally carry secrets."""
    return normalize_secret_values(
        value
        for key, value in env.items()
        if value and _secret_env_key_pattern.search(key) is not None
    )


def normalize_secret_values(values: Iterable[str]) -> tuple[str, ...]:
    """Return unique, non-empty secrets ordered from longest to shortest."""
    return tuple(sorted({value for value in values if value}, key=_secret_sort_key))


def collect_diagnostic_secret_values(
    argv: tuple[str, ...], environment: Mapping[str, str]
) -> tuple[str, ...]:
    """Collect all secret values that may appear in command diagnostics."""
    return normalize_secret_values(
        (
            *collect_secret_values(argv),
            *collect_secret_values_from_environment(environment),
        )
    )


def _secret_sort_key(value: str) -> tuple[int, str]:
    return -len(value), value


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


def redact_diagnostic_argv(
    argv: tuple[str, ...], *, secret_values: tuple[str, ...]
) -> tuple[str, ...]:
    """Redact structured arguments, then remove collected secret values from each one."""
    return tuple(redact_text(arg, secret_values=secret_values) for arg in redact_argv(argv))


def redact_text(text: str, *, secret_values: tuple[str, ...] = ()) -> str:
    redacted = _token_text_pattern.sub(_redact_token_match, text)
    for secret in normalize_secret_values(secret_values):
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
