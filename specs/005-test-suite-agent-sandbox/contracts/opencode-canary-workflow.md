# Contract: Real OpenCode Canary Workflow

## Profile

- pytest marker: `live_opencode_canary`
- test name: `test_real_opencode_executes_issue_in_local_directory`
- one attempt, 15-minute workflow timeout, USD 0.10 usage ceiling

## Issue content

Title:

```text
Agent canary edit <run_id>
```

Description MUST contain these verbatim lines (with `<run_id>` substituted):

```text
Replace the entire contents of target.txt with exactly:
after:<run_id>
(with trailing newline)
Do not modify control.txt or any other file.
Initial content of target.txt is exactly:
before:<run_id>
(with trailing newline)
```

Rules:

1. Do not include `MULTICA_TEST_ACTION`.
2. Do not reference any other file path.
3. Canary reuses the same sandbox helper, cleanup order, file assertions, and diagnostic bundle as the deterministic workflow.

## Usage and cost

After terminal run:

1. Call `client.issues.usage(issue_id)`.
2. If the call raises or returns no decodable payload, canary MUST fail with diagnostic (not skip).
3. If `cost_usd` is absent from the decoded payload, canary MUST fail with diagnostic naming the missing field.
4. If `cost_usd > 0.10`, canary MUST fail.

## Environment

Required variables and skip behavior are defined in `spec.md` FR-056 and FR-057. Invalid configuration MUST skip before Docker, daemon, or backend startup.

Before daemon start, map validated canary variables to daemon variables:

| Canary variable | Daemon variable |
|---|---|
| `MULTICA_CANARY_OPENCODE_PATH` | `MULTICA_OPENCODE_PATH` |
| `MULTICA_CANARY_MODEL` | `MULTICA_OPENCODE_MODEL` |

Deterministic workflow MUST keep `MULTICA_OPENCODE_MODEL=multica-test/fake`; canary MUST use the mapped real model value only.
