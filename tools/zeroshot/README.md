# Zeroshot development harness

OpenSpec defines what and why; Zeroshot 6.40.0 orchestrates implementation and independent evidence; GitHub CI remains the merge authority. Zeroshot is development tooling, not a `multica-py` dependency.

## Run a change

Requires Node.js 22+ and an authenticated supported agent CLI.

```bash
./tools/zeroshot/bootstrap
./tools/zeroshot/run-change add-zeroshot-development-harness
```

The repository workflow uses Codex by default and a Zeroshot-managed Git worktree based on the current `HEAD`. The worker continues privately while it reports `canValidate=false`; validators start only after it reports implementation ready. The requirements validator checks every MUST against observable evidence. The engineering validator receives the repository-owned `project-pr` command proof (`make pr`), which is also a required delivery gate. A mandatory `FAIL`, `CANNOT_VALIDATE`, `SKIPPED`, `UNKNOWN`, evidence-free result, or stale command proof rejects the run.

Delivery and provider controls stay explicit:

```bash
./tools/zeroshot/run-change --pr <change-id>
./tools/zeroshot/run-change --ship <change-id>
./tools/zeroshot/run-change --background <change-id>
./tools/zeroshot/run-change --provider codex <change-id>
```

`--pr` targets `main`; `--ship` additionally merges after all validators and the command-proof gate approve. Use `zeroshot resume <run-id>` for a stopped or failed run. The fixed OpenSpec workflow intentionally does not use Zeroshot's conductor: the approved change already supplies scope, architecture, and acceptance criteria.

Monitor and export native evidence:

```bash
zeroshot list
zeroshot logs <run-id> -f
zeroshot export <run-id> --format trace --output /tmp/<run-id>.trace.jsonl
zeroshot export <run-id> --format semantic --output /tmp/<run-id>.semantic.jsonl
```

Zeroshot stores resumable ledgers under `~/.zeroshot`; worktree paths appear in run status/logs. Keep exported traces outside the repository or upload them as CI/PR artifacts. Project checks are exposed through the root `Makefile`; live checks are explicit (`make live`) and missing required live evidence remains unverified.

Zeroshot refuses to create a worktree below its hard-coded 10 GB free-space guard. This is a conservative safety reserve against a run exhausting the disk while creating worktrees, dependency environments, logs, and SQLite ledgers; it is not the measured size of this repository.
