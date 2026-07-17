# Contract: Semantic CLI Contract

## Command Contract

Each command is represented as structured semantic data, not a string-only
command path.

Required shape:

```json
{
  "path": ["agent", "list"],
  "use": "list",
  "aliases": [],
  "hidden": false,
  "deprecated": null,
  "args": {
    "min": 0,
    "max": 0,
    "grammar": null
  },
  "flags": [
    {
      "name": "status",
      "shorthand": null,
      "type": "string",
      "required": false,
      "repeatable": false,
      "default": null,
      "enum": [],
      "inherited": false,
      "deprecated": null
    }
  ],
  "execution": {
    "interactive": false,
    "streaming": false,
    "managed_process": false,
    "requires_server": true
  },
  "output": {
    "mode": "json",
    "schema_ref": "contracts/output/agent-list-v1.json"
  },
  "source": {
    "path": "server/cmd/multica/cmd_agent.go",
    "symbol": "agentListCmd"
  }
}
```

Validation contract:

- Command paths and flags are normalized into stable order.
- Help descriptions are documentation-only unless attached to deprecation or validation semantics.
- Inherited flags must identify inherited effective presence.
- Hidden/deprecated state participates in semantic diff.

## Diff Categories

Semantic diff entries use these change kinds:

- `command_added`
- `command_removed`
- `command_moved_or_renamed`
- `argument_added`
- `argument_removed`
- `argument_changed`
- `flag_added`
- `flag_removed`
- `flag_renamed`
- `flag_changed`
- `default_changed`
- `alias_changed`
- `deprecation_changed`
- `execution_mode_changed`
- `output_contract_changed`
- `doc_only_changed`
- `provenance_only_changed`

Severity values:

- `provenance_only`
- `doc_only`
- `additive`
- `potentially_breaking`
- `breaking`

Default severity policy:

- The complete change-kind oracle is `contracts/implementation-oracles.md`.
- New command: additive.
- New optional flag: additive.
- New required argument or flag: breaking.
- Removed command or flag: breaking.
- Type or enum narrowing: breaking.
- Enum widening: potentially breaking.
- Default value change: potentially breaking.
- Alias removal while the canonical command remains: potentially breaking.
- Visible command becoming hidden: potentially breaking.
- Deprecation added: potentially breaking.
- Output field removed or type-changed: breaking.
- Help text only: documentation-only.
- Same semantic hash with new build provenance: provenance-only.

## Source Evidence Boundary

Source extraction may automatically record only declarative facts from known,
versioned patterns:

- Cobra command literals with `Use`, `Aliases`, `Short`, `Long`, `Hidden`, and `Deprecated`.
- `AddCommand` relationships.
- Known `Flags()` and `PersistentFlags()` registration calls.
- Known Cobra argument validators.
- Known declarative flag constraints.
- Source file, symbol, and line range.

Everything else becomes evidence with `review_required: true`.

The following require maintainer approval before entering the ApprovedSDKContract:

- Python parameter to CLI flag to API field mapping.
- Omitted/null/empty/zero/false semantics.
- Dynamic enum policy.
- Imperative validation and custom constraints.
- Public operation names and unsupported decisions.

## Preferred Upstream Exporter

Collection uses this fixed order unless the user explicitly requests one method
for diagnostic collection:

1. Release asset such as `multica-cli-contract.json`.
2. Hidden CLI command such as `multica __contract --format json`.
3. Go helper/exporter that walks Cobra `rootCmd` at a pinned full source commit.
4. Help parser fallback.

Fallback policy:

- Help parsing is allowed only as fallback or degraded mode.
- Fallback results must record collection method and trust level.
- Hidden/deprecated metadata missing from fallback output creates review items.
- Source/binary/exporter/help mismatch is reported separately from SDK coverage
  gaps with exit code `5` and failure code `CONTRACT_SOURCE_MISMATCH`.
- Promotion eligibility follows `contracts/implementation-oracles.md`.
