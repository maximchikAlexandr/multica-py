# Contract: Deterministic OpenCode-Compatible Executable

## File

`tests/fixtures/fake_opencode.py`

Executable with Python shebang and executable permission on POSIX. CI invokes it through its absolute path.

## Accepted argv

The executable accepts one command only:

```text
fake_opencode.py run --format json --dangerously-skip-permissions --dir <absolute-dir> --model multica-test/fake <final-prompt>
```

Rules:

1. First positional token must be `run`.
2. `--format` must equal `json`.
3. `--dir` is required and must be absolute existing directory.
4. `--dangerously-skip-permissions` is required.
5. `--model` is required and must equal `multica-test/fake`.
6. Final positional argument is the prompt.
7. No other option is accepted; any additional option exits 64.
8. The prompt must contain exactly one line beginning `MULTICA_TEST_ACTION=`.

## Environment

`MULTICA_TEST_AGENT_MODE` values:

- absent or `success` — normal behavior;
- `error` — emit JSONL error and exit 1 without file mutation;
- `timeout` — emit step_start, then wait until killed; no file mutation;
- `wrong-edit` — write `unexpected:<run_id>\n` to target, emit success stream, exit 0.

Any other value exits 64 without touching files.

## Success algorithm

1. Parse compact JSON after `MULTICA_TEST_ACTION=`.
2. Validate `AgentSandboxInstruction` schema.
3. Resolve `<dir>/<path>` and verify containment.
4. Read UTF-8 file and compare exact `before`.
5. Write `after` to sibling temporary file.
6. Flush and atomically replace target via `os.replace`.
7. Emit one JSON object per line in this order:

```json
{"type":"step_start","sessionID":"multica-test","part":{}}
{"type":"text","sessionID":"multica-test","part":{"text":"Applied MULTICA_TEST_ACTION"}}
{"type":"step_finish","sessionID":"multica-test","part":{"reason":"stop","tokens":{"input":0,"output":0}}}
```

8. Flush stdout and exit 0.

## Validation/error behavior

For schema/path/file/before errors:

1. do not mutate any file;
2. emit one JSONL object:

```json
{"type":"error","sessionID":"multica-test","error":{"name":"MulticaTestInstructionError","message":"<sanitized reason>"}}
```

3. exit 2.

No secrets, full environment, token or absolute path outside `<dir>` may be printed.

## Required tests

- success exact replacement;
- malformed JSON;
- unknown schema;
- absolute path;
- path traversal;
- missing file;
- before mismatch;
- error mode;
- timeout kill;
- wrong-edit mode;
- unknown mode;
- canonical argv acceptance.
