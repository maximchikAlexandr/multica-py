from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SanitizerCase:
    name: str
    value: str
    secrets: tuple[str, ...]


SANITIZER_CASES: tuple[SanitizerCase, ...] = (
    SanitizerCase("serialized token", '{"token":"quoted-secret"}', ("quoted-secret",)),
    SanitizerCase(
        "serialized authorization",
        '{"Authorization":"Bearer bearer-secret"}',
        ("bearer-secret",),
    ),
    SanitizerCase(
        "header authorization", "Authorization: Bearer header-secret", ("header-secret",)
    ),
    SanitizerCase(
        "URL credentials",
        "https://user:password@example.test/private",
        ("password", "example.test"),
    ),
)
