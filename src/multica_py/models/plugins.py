from __future__ import annotations

import msgspec

__all__ = ["Plugin", "PluginDigest"]


class Plugin(msgspec.Struct, frozen=True, kw_only=True):
    plugin_key: str
    desired_version: str
    lifecycle_status: str
    trust_tier: str
    uploader_id: str = ""


class PluginDigest(msgspec.Struct, frozen=True, kw_only=True):
    plugin_key: str
    version: str
    manifest_digest: str
    archive_digest: str
    artifact_digest: str
    size_bytes: int
    file_count: int
