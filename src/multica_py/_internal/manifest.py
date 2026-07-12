from __future__ import annotations

import pathlib
from typing import cast

import msgspec

CLI_MANIFEST_PATH = pathlib.Path(__file__).parent.parent / "_generated" / "cli_manifest.json"


class ManifestMeta(msgspec.Struct, frozen=True):
    pinned_sha: str
    source_base: str
    generated_at: str


class ManifestEntry(msgspec.Struct, frozen=True, kw_only=True):
    command: str
    sdk_method: str
    output_mode: str
    aliases: tuple[str, ...] = ()
    status: str = ""
    reason: str | None = None
    source_file: str | None = None


class ManifestDocument(msgspec.Struct, frozen=True):
    meta: ManifestMeta = msgspec.field(name="_meta")
    commands: tuple[ManifestEntry, ...]


def load_manifest_document(path: pathlib.Path = CLI_MANIFEST_PATH) -> ManifestDocument:
    return msgspec.json.decode(path.read_bytes(), type=ManifestDocument, strict=False)


def load_manifest(path: pathlib.Path = CLI_MANIFEST_PATH) -> tuple[ManifestEntry, ...]:
    return load_manifest_document(path).commands


def resolve_dotted_path(obj: object, dotted_path: str) -> object:
    current: object = obj
    for part in dotted_path.split("."):
        current = cast("object", getattr(current, part, None))
        if current is None:
            return None
    return current


def validate_manifest_sdk_mapping(manifest: tuple[ManifestEntry, ...]) -> list[str]:
    errors: list[str] = []
    seen_sdk: set[str] = set()
    for entry in manifest:
        if entry.status == "unsupported":
            continue
        if entry.sdk_method and entry.sdk_method in seen_sdk:
            errors.append(f"Duplicate SDK mapping: {entry.sdk_method} for command {entry.command}")
        if entry.sdk_method:
            seen_sdk.add(entry.sdk_method)
        if not entry.command:
            errors.append(f"Entry missing command field: {entry!r}")
        if not entry.sdk_method:
            errors.append(f"Entry missing sdk_method for command: {entry.command}")
    return errors
