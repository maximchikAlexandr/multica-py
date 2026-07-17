# Contract: Machine-Readable Report

Human-readable output is a rendering of this report model.

Required shape:

```json
{
  "schema_version": 1,
  "status": "gaps",
  "supported": {
    "version": "0.4.2",
    "commit": "<full-sha>",
    "semantic_hash": "sha256:<hash>"
  },
  "observed": {
    "version": "0.4.3",
    "release_id": "<id>"
  },
  "candidate": {
    "version": "0.4.3",
    "commit": "<full-sha>",
    "semantic_hash": "sha256:<hash>",
    "trust_level": "verified"
  },
  "upstream_diff": {
    "additive": 3,
    "potentially_breaking": 1,
    "breaking": 2,
    "doc_only": 4
  },
  "coverage": {
    "typed": 105,
    "raw": 2,
    "process": 3,
    "unsupported": 1,
    "legacy": 4,
    "incomplete": 3
  },
  "failures": [
    {
      "code": "REQUIRED_FLAG_ADDED",
      "operation_id": "agents.create",
      "command": "agent create",
      "path": "flags.access-scope",
      "severity": "breaking",
      "resolution": "unresolved"
    }
  ]
}
```

Validation contract:

- Report schema is versioned.
- Human summary and GitHub summaries are derived from this model.
- `check --format human` must render the first four non-empty lines exactly as
  specified in `implementation-oracles.md`.
- Failure entries use machine-readable codes.
- Missing binary, invalid schema, and collector timeout are not represented as clean coverage.
- `--check` never writes this report unless `--output` is explicitly provided.
- `--format json --output PATH` output must validate against
  `contracts/schema/upstream-report-v1.schema.json`.
