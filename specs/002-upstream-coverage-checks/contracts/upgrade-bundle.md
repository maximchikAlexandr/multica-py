# Contract: Upgrade Bundle

Upgrade preparation creates a deterministic local review directory. PR or issue
payload creation belongs only to observer automation and is not part of the
`prepare-upgrade` command.

Required layout:

```text
artifacts/upstream-upgrades/v0.4.2..v0.4.3/
├── summary.md
├── upstream-diff.json
├── impact-map.json
├── candidate-contract.json
├── manifest-suggestions.json
├── implementation-tasks.md
├── changelog-fragment.md
└── test-suggestions/
    ├── argv-contracts.patch
    └── output-fixtures.todo.json
```

For each affected operation, the bundle records:

- Upstream change and severity.
- Operation ID or unresolved mapping state.
- Candidate SDK resource/method suggestion, or the literal value `null` with
  `unresolved_reason` when automation cannot determine one.
- New or changed parameters.
- Source evidence.
- Output contract impact.
- Required tests.
- Documentation and compatibility actions.
- Fields automation could not determine.

Validation contract:

- Bundle generation is deterministic and idempotent for unchanged inputs.
- The layout above is mandatory for local upgrade preparation.
- Generated facts are separated from maintainer decisions.
- Incomplete manifest suggestions never satisfy coverage.
- Re-running preparation does not create duplicate tracking issues or PRs.
- Every non-documentation upstream change appears in the impact map.
- Applying generated manifest suggestions requires an explicit command.
- Applied suggestions remain incomplete until maintainer decisions and tests are supplied.
