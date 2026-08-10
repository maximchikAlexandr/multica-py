from __future__ import annotations

from urllib.parse import quote

from multica_py.exceptions import MissingPermalinkContextError


def build_permalink(
    *,
    entity_type: str,
    entity_id: str,
    collection: str,
    app_url: str | None,
    workspace_slug: str | None,
) -> str:
    missing = tuple(
        field
        for field, value in (
            ("app_url", app_url),
            ("workspace_slug", workspace_slug),
        )
        if value is None
    )
    if missing:
        raise MissingPermalinkContextError(entity_type, entity_id, missing)
    assert app_url is not None
    assert workspace_slug is not None
    return "/".join(
        (
            app_url,
            quote(workspace_slug, safe=""),
            collection,
            quote(entity_id, safe=""),
        )
    )
