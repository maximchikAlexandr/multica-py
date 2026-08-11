# Pre-archive validation proof

The change was validated before archival at commit `b81631bf5af81bab45e34ee1d61182bd0d0b8b6b`, the parent of the archive commit `73fa219`.

The following commands passed at that pre-archive tip:

```text
uv run openspec validate complete-public-sdk-ergonomics-bound-issues --type change --strict --json
summary: 1 item, 1 passed, 0 failed

uv run openspec validate --specs --strict --json
summary: 8 items, 8 passed, 0 failed
```

The archived change directory has no active delta, so release revalidation on
the archived tip uses the strict main-spec command above. The change-specific
validation is a pre-archive proof and is not rerun against the archived path.
