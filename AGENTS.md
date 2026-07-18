<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
`specs/002-upstream-coverage-checks/plan.md`
<!-- SPECKIT END -->

## Multica Upstream Contract Review Rules

When updating the SDK from upstream `multica-ai/multica`, treat the pinned
upstream CLI source and verified release binary as evidence, not as automatic
approval for public SDK changes.

Extractor scripts may automatically record only declarative facts from known,
versioned patterns:

- Cobra command literals such as `cobra.Command{Use, Aliases, Hidden, Deprecated}`.
- `AddCommand(...)` command-tree relationships.
- Known `Flags()` and `PersistentFlags()` registration calls.
- Known Cobra argument validators and declarative flag constraints.
- Source file, symbol, and line-range provenance.

Everything else must fail closed into a review item. Unknown source patterns,
unresolved helpers, dynamic enum construction, imperative validation, or
presence-sensitive code must never change the public SDK automatically.

For every new or changed command, the reviewer must trace each positional
argument and flag through `RunE` and called helpers, then record where each
value lands: path, query, JSON body, header, multipart body, or local process
control. Do not treat matching names as proof of mapping; `--project` and
`project_id` still require source evidence.

For update/patch-style parameters, explicitly document presence semantics:

- omitted value;
- `null` / `None`;
- empty string;
- zero or `false` when accepted by the type.

Use an explicit unset sentinel in the SDK when `None` has a meaning different
from "not provided".

Enum values found by scripts are candidates only. A reviewer must approve the
public enum name, strict/open policy, aliases, deprecated values, and operation
scope before they enter the approved SDK contract.

Declarative Cobra constraints may be extracted automatically. Imperative
constraints found in conditionals, `Flags().Changed(...)`, helper calls, or
custom validation must be normalized by review as `requires`, `conflicts_with`,
`exactly_one`, `at_least_one`, `required_together`, conditional enum/range, or
a named custom validator. Each approved constraint needs positive and negative
tests.

Generated evidence, manifest suggestions, and upgrade bundles are not coverage
decisions. Only an approved SDK contract with operation IDs, source references,
input/output contracts, coverage level, and test references can promote a
candidate upstream contract to supported SDK coverage.

Keep the upstream-update pipeline split into two active layers in feature 002:

- `sdk-contract.json`: the human/agent-approved SDK contract with operation
  IDs, mappings, overrides, policy decisions, and source references.
- `generator/`: deterministic generation of Python signatures, enums,
  validators, docs, fixtures, and tests from the approved contract.

`source_evidence/` extractors were removed in the 002 cleanup and return in
feature 003 when wired to landing zones. Do not treat source evidence as an
active layer until 003 lands.

The approved SDK contract is the only valid production generator input.
Evidence files, heuristic rename suggestions, and generated upgrade bundles
must never directly generate or modify public SDK behavior.

Maintainer upgrade entrypoint:

```bash
uv run python scripts/upstream_contract.py upgrade --tag ... --version ... \
  --commit ... --release-id ... --binary ... --asset-name ... --sha256 ... \
  --os ... --arch ... --version-output ... --output-dir ...
```

Or `./scripts/upstream_upgrade.sh` with `TAG`, `COMMIT`, `RELEASE_ID`, `BINARY`,
`ASSET_NAME`, `SHA256`, and `VERSION_OUTPUT` set. Verified collect/export paths:
`tools/upstream-cli-contract/README.md` and `upstream_contract.py collect`.

## Commit Messages

Use Conventional Commits for all repository commits:

```text
<type>[optional scope]: <description>
```

Allowed types: `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `build`, `ci`,
`chore`, `style`, `revert`.

The repository enforces this with `.githooks/commit-msg`. Enable it locally with:

```sh
git config core.hooksPath .githooks
```
