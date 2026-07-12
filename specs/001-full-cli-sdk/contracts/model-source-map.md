# Model Source Map

Exact Python fields must be traced from the JSON-producing branch of each command and the referenced structs under `server/internal/cli`.

Primary upstream source directories:

- Command registration and presentation: [`server/cmd/multica`](https://github.com/multica-ai/multica/tree/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica)
- CLI HTTP client and transport structs: [`server/internal/cli`](https://github.com/multica-ai/multica/tree/48b8dbf43971e5ea974bf827220cd212a1240c72/server/internal/cli)
- Root/global flags: [`server/cmd/multica/main.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/main.go)

Rules:

1. Prefer explicit Go structs with `json` tags.
2. If a command builds an anonymous JSON object/map, reproduce exactly that stable object as a dedicated Python model.
3. Never model table-only columns as API fields unless the JSON branch contains them.
4. Preserve optionality from pointers/omitempty and actual response behavior.
5. Convert RFC3339 timestamps to aware `datetime` only when source guarantees RFC3339; otherwise retain `str` with a named alias.
6. Record fixture provenance as `source file + function + baseline SHA`.
