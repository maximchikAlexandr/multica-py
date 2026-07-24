# Historical Handoff Index

This file is non-normative historical context. Implementers MUST NOT infer or
choose behavior from it.

Binding authorities, in order:

1. `contracts/sdk-contract-v2.seed.json` — complete reviewed machine input.
2. `contracts/approved-sdk-contract-v2.md` — closed schema and invariants.
3. `contracts/operation-decisions.md` — the 16 public operation decisions.
4. `contracts/source-authority.json` and `.md` — machine authority and readable pinned-source view.
5. `contracts/upstream-family-disposition.md` — all 11 family boundaries.
6. `contracts/generated-output-formats.json` — exact nine output formats.
7. `contracts/generation-and-provenance.md` — generation and promotion protocol.
8. `contracts/live-acceptance.md` — live, mutation, stability, and aggregation.
9. `contracts/requirement-traceability.md` — exact 65 requirement IDs.
10. `tasks.md` and `quickstart.md` — execution order and commands.

Target identity:

- tag/version: `v0.4.9` / `0.4.9`;
- commit: `ecbdbda09e7b2be56cd9ccc55cee1ee360222d18`;
- release ID: `358605496`;
- upstream checkout: `.devlocal/upstream/multica-v0.4.9`;
- artifact root: `.test-artifacts/upstream-v0.4.9/`.

Historical evidence remains under
`.devlocal/artifacts/upstream-upgrades/v0.3.10..v0.4.9/`. Its CLI contract is
`help-degraded`; it is evidence, not a public SDK decision and not `verified`.

Promotion has an external maintainer gate:
`contracts/upstream-v0.4.9-promotion-decision.json` must be created by a real
maintainer. An implementation agent must never create it, modify it, or invent
a reviewer identity.

The former long-form handoff was retired because it duplicated binding
decisions and contained stale absolute paths. Git history remains the only
archive of that research narrative.
