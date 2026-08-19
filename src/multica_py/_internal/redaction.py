from __future__ import annotations

import json
import os
import re
from collections.abc import Iterable, Mapping
from typing import cast
from urllib.parse import unquote, unquote_plus, urlsplit

REDACTED = "***"

_token_pattern = re.compile(r"--token(?:[= ])(\S+)", re.IGNORECASE)
_token_text_pattern = re.compile(
    r"(?i)(--token(?:=|\s+)|token(?:=|:\s+)|bearer\s+|authorization:\s*)(\S+)"
)
_SECRET_KEY_PATTERNS = (
    ("access", "key"),
    ("access", "token"),
    ("api", "key"),
    ("auth", "token"),
    ("authorization",),
    ("client", "secret"),
    ("credential",),
    ("key",),
    ("password",),
    ("passwd",),
    ("private", "key"),
    ("secret",),
    ("token",),
)
_SECRET_OPTION_EXCLUSIONS = frozenset({"credential"})
_FILE_CONTENT_SECRET_OPTIONS = frozenset(
    {"credential-file", "server-config-file"},
)
_STDIN_CONTENT_SECRET_OPTIONS = frozenset(
    {"credential-stdin", "server-config-stdin"},
)
_INLINE_SECRET_OPTIONS = frozenset({"auth-header", "server-config"})
_SECRET_KEY_COMPACT_ALIASES = frozenset(
    {"apikey", "accesskey", "accesstoken", "authtoken", "clientsecret", "privatekey"}
)
_SECRET_KEY_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
_SECRET_KEY_SEPARATOR = re.compile(r"[^A-Za-z0-9]+")


def _is_secret_config_key(key: str) -> bool:
    return _is_secret_key(key) or any(separator in key for separator in (".", ":", "/"))


def _is_secret_option(arg: str) -> bool:
    """Return whether an option name conventionally carries a secret value."""
    if not arg.startswith("--"):
        return False
    name = arg[2:].partition("=")[0]
    if name in _SECRET_OPTION_EXCLUSIONS:
        return False
    return name in _INLINE_SECRET_OPTIONS or _is_secret_key(name)


def _collectible_secret_option(arg: str) -> bool:
    if not arg.startswith("--"):
        return False
    name = arg[2:].partition("=")[0]
    if name in _SECRET_OPTION_EXCLUSIONS:
        return False
    return (
        name in _INLINE_SECRET_OPTIONS
        or name in _FILE_CONTENT_SECRET_OPTIONS
        or name in _STDIN_CONTENT_SECRET_OPTIONS
        or _is_secret_key(name)
    )


def _secret_key_segments(key: str) -> tuple[str, ...]:
    separated = _SECRET_KEY_BOUNDARY.sub(" ", key)
    parts = cast("list[str]", _SECRET_KEY_SEPARATOR.split(separated))
    return tuple(part.casefold() for part in parts if part)


def _is_secret_key(key: str) -> bool:
    return _is_secret_key_with_policy(key, include_bare_key=False)


def _is_secret_key_with_policy(key: str, *, include_bare_key: bool) -> bool:
    segments = _secret_key_segments(key)
    if any(segment in _SECRET_KEY_COMPACT_ALIASES for segment in segments):
        return True
    return any(
        segments[index : index + len(pattern)] == pattern
        for pattern in _SECRET_KEY_PATTERNS
        if include_bare_key or pattern != ("key",)
        for index in range(len(segments) - len(pattern) + 1)
    )


def collect_secret_values(argv: tuple[str, ...], *, stdin: bytes | None = None) -> tuple[str, ...]:
    secrets: list[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if (
            arg == "config"
            and i + 3 < len(argv)
            and argv[i + 1] == "set"
            and _is_secret_config_key(argv[i + 2])
        ):
            secrets.append(argv[i + 3])
            i += 4
            continue
        if arg.removeprefix("--") in _FILE_CONTENT_SECRET_OPTIONS and i + 1 < len(argv):
            secrets.extend(_read_file_secrets(argv[i + 1]))
            i += 2
            continue
        if arg == "--credential-stdin" and stdin:
            secrets.extend(_collect_content_secret_values(stdin.decode("utf-8", errors="replace")))
            i += 1
            continue
        if arg == "--server-config-stdin" and stdin:
            secrets.extend(_collect_content_secret_values(stdin.decode("utf-8", errors="replace")))
            i += 1
            continue
        if _collectible_secret_option(arg) and "=" not in arg and i + 1 < len(argv):
            secrets.extend(_collect_option_secret_values(arg[2:], argv[i + 1]))
            i += 2
            continue
        if _collectible_secret_option(arg) and "=" in arg:
            _, _, value = arg.partition("=")
            if value:
                secrets.extend(_collect_option_secret_values(arg[2:].partition("=")[0], value))
        secrets.extend(_collect_url_secret_values(arg))
        i += 1
    return normalize_secret_values(secrets)


def _read_file_secrets(path: str) -> tuple[str, ...]:
    content = _read_file_bytes(path)
    if not content:
        return ()
    decoded = content.decode("utf-8", errors="replace")
    return _collect_content_secret_values(decoded)


def _read_file_bytes(path: str) -> bytes:
    try:
        with open(os.fspath(path), "rb") as handle:
            return handle.read()
    except OSError:
        return b""


def _collect_option_secret_values(name: str, value: str) -> tuple[str, ...]:
    if name == "auth-header":
        return (value, *_collect_auth_header_secret_values(value))
    if name in {"credential-file", "credential-stdin", "server-config-file", "server-config-stdin"}:
        return _collect_content_secret_values(value)
    if name == "server-config":
        return _collect_content_secret_values(value)
    return (value,)


def _collect_content_secret_values(value: str) -> tuple[str, ...]:
    content = value.strip()
    if not content:
        return ()
    secrets = [content]
    try:
        parsed = cast("object", json.loads(content))
    except (json.JSONDecodeError, TypeError):
        return (content,)
    _collect_json_secret_values(parsed, secrets)
    return tuple(secrets)


def _collect_json_secret_values(value: object, secrets: list[str], *, secret: bool = False) -> None:
    if isinstance(value, Mapping):
        mapping = cast("Mapping[object, object]", value)
        for key, child in mapping.items():
            _collect_json_secret_values(
                child,
                secrets,
                secret=secret or _is_secret_config_key(str(key)),
            )
        return
    if isinstance(value, (list, tuple)):
        for child in value:
            _collect_json_secret_values(child, secrets, secret=secret)
        return
    if secret and value is not None:
        secrets.append(str(value).lower() if isinstance(value, bool) else str(value))


def _collect_auth_header_secret_values(value: str) -> tuple[str, ...]:
    _name, separator, remainder = value.partition(":")
    payload = remainder.strip() if separator else value.strip()
    if not payload:
        return ()
    _scheme, separator, token = payload.partition(" ")
    if separator and token.strip():
        return (payload, token.strip())
    return (payload,)


def _collect_url_secret_values(arg: str) -> tuple[str, ...]:
    """Collect raw and decoded values from sensitive URL query/fragment keys."""
    try:
        parts = urlsplit(arg)
    except ValueError:
        return ()

    secrets: list[str] = []
    for component in _url_query_components(parts.query, parts.fragment):
        for pair in component.split("&"):
            raw_key, separator, raw_value = pair.partition("=")
            if not separator:
                continue
            if not _is_secret_key_with_policy(unquote_plus(raw_key), include_bare_key=True):
                continue
            secrets.extend((raw_value, unquote_plus(raw_value)))
    authority, at, _host = parts.netloc.rpartition("@")
    if at:
        _user, separator, raw_password = authority.partition(":")
        if separator and raw_password:
            secrets.extend((raw_password, unquote(raw_password)))
    return tuple(secrets)


def _url_query_components(query: str, fragment: str) -> tuple[str, ...]:
    """Return query pairs from both URL query and hash-router query forms."""
    components = [query]
    if fragment.startswith("?"):
        components.append(fragment[1:])
    elif "?" in fragment:
        components.append(fragment.split("?", 1)[1])
    else:
        components.append(fragment)
    return tuple(component for component in components if component)


def collect_secret_values_from_environment(env: Mapping[str, str]) -> tuple[str, ...]:
    """Collect values from environment keys that conventionally carry secrets."""
    return normalize_secret_values(
        value for key, value in env.items() if value and _is_secret_key(key)
    )


def normalize_secret_values(values: Iterable[str]) -> tuple[str, ...]:
    """Return unique, non-empty secrets ordered from longest to shortest."""
    return tuple(sorted({value for value in values if value}, key=_secret_sort_key))


def collect_diagnostic_secret_values(
    argv: tuple[str, ...], environment: Mapping[str, str], *, stdin: bytes | None = None
) -> tuple[str, ...]:
    """Collect all secret values that may appear in command diagnostics."""
    return normalize_secret_values(
        (
            *collect_secret_values(argv, stdin=stdin),
            *collect_secret_values_from_environment(environment),
        )
    )


def collect_diagnostic_secret_bytes(
    argv: tuple[str, ...], *, stdin: bytes | None = None
) -> tuple[bytes, ...]:
    """Collect opaque file/stdin payloads for byte-preserving diagnostics."""
    secrets: list[bytes] = []
    if stdin and any(f"--{option}" in argv for option in _STDIN_CONTENT_SECRET_OPTIONS):
        secrets.append(stdin)
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg.removeprefix("--") in _FILE_CONTENT_SECRET_OPTIONS and i + 1 < len(argv):
            content = _read_file_bytes(argv[i + 1])
            if content:
                secrets.append(content)
            i += 2
            continue
        i += 1
    unique: list[bytes] = []
    for secret in secrets:
        if secret not in unique:
            unique.append(secret)
    return tuple(unique)


def _secret_sort_key(value: str) -> tuple[int, str]:
    return -len(value), value


def redact_argv(argv: tuple[str, ...]) -> tuple[str, ...]:
    redacted: list[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--credential-file" and i + 1 < len(argv):
            redacted.extend((arg, argv[i + 1]))
            i += 2
            continue
        if arg == "--server-config-file" and i + 1 < len(argv):
            redacted.extend((arg, argv[i + 1]))
            i += 2
            continue
        if _is_secret_option(arg) and "=" not in arg and i + 1 < len(argv):
            redacted.extend((arg, REDACTED))
            i += 2
            continue
        if _is_secret_option(arg) and "=" in arg:
            name, _, _value = arg.partition("=")
            redacted.append(f"{name}={REDACTED}")
            i += 1
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


def redact_bytes(
    data: bytes,
    *,
    secret_values: tuple[str, ...] = (),
    secret_bytes: tuple[bytes, ...] = (),
) -> bytes:
    redacted = data
    replacement = REDACTED.encode("utf-8")
    for secret in secret_bytes:
        if secret:
            redacted = redacted.replace(secret, replacement)
    for secret_text in normalize_secret_values(secret_values):
        encoded = secret_text.encode("utf-8")
        if encoded:
            redacted = redacted.replace(encoded, replacement)
    return redacted


def _redact_token_match(match: re.Match[str]) -> str:
    return f"{match.group(1)}{REDACTED}"


def _redact_token_arg(arg: str) -> str:
    return _token_pattern.sub(lambda m: m.group(0).replace(m.group(1), REDACTED), arg)  # type: ignore[misc]


def _redact_url_secret_arg(arg: str) -> str:
    try:
        parts = urlsplit(arg)
    except ValueError:
        return arg

    redacted = arg
    if parts.query:
        redacted = redacted.replace(parts.query, _redact_url_query_component(parts.query), 1)
    if parts.fragment:
        redacted = redacted.replace(parts.fragment, _redact_url_query_component(parts.fragment), 1)

    authority, at, host = parts.netloc.rpartition("@")
    if at:
        user, separator, _raw_password = authority.partition(":")
        if separator:
            redacted_netloc = f"{user}:{REDACTED}@{host}"
            redacted = redacted.replace(parts.netloc, redacted_netloc, 1)
    return redacted


def _redact_url_query_component(component: str) -> str:
    prefix = ""
    query = component
    if "?" in component:
        route, query = component.split("?", 1)
        prefix = f"{route}?"
    pairs: list[str] = []
    for pair in query.split("&"):
        raw_key, separator, _raw_value = pair.partition("=")
        if separator and _is_secret_key_with_policy(unquote_plus(raw_key), include_bare_key=True):
            pairs.append(f"{raw_key}={REDACTED}")
        else:
            pairs.append(pair)
    return prefix + "&".join(pairs)
