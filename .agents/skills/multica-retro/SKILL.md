---
name: multica-retro
description: Review recent Multica coding-agent runs in selected projects using a deterministic evidence bundle and propose numbered improvements without changing code or process.
---

# Multica retro

Use `scripts/retro_collect.py` from the repository root to collect completed runs
and their Multica messages. It uses the current `multica-py` SDK and the
authenticated `multica` CLI; it does not create or update issues.

```sh
uv run python scripts/retro_collect.py \
  --project-id be21ace8-af16-4e39-a10a-dbec46d6b2ad \
  --project-id 89afff1c-d2f9-43d1-a50d-c6930f3491e3 \
  --days 3 --output ./retro-evidence.json
```

The output file must be new and is created with mode `0600`. It may contain
secrets in tool transcripts: never attach or publish it. Delete it after the
review according to the runtime's retention policy. Use `--until` for a fixed
exclusive UTC boundary and `--issue MYL-N` for a focused check. Selection is by
`completed_at` in a half-open interval; failed runs with a completion timestamp
are included. Do not filter by issue `updated_at` or `last_activity_at`.

For each run, the bundle contains exact Multica run messages and a verified
path to the primary local Codex rollout when it still exists beside the run's
workdir. One Codex session can span multiple Multica runs. Do not treat the
whole rollout as evidence for one run without checking timestamps and run
boundaries. A missing local file is not a reason to invent its contents; use
the Multica messages and state the coverage limit. Child-agent sessions are
not guaranteed to be linked by the primary session ID.

Apply the categories in [Matt Pocock's retro skill](https://github.com/mattpocock/skills/blob/b0618bc436ad893b3c5e84e55fba86586d34a404/skills/engineering/retro/SKILL.md):
navigation, existing automated checks, coding standards, steering instructions,
tool economy, inert instructions, and information access. Inspect the repo's
current checks before recommending a new one. Prefer a deterministic check
over another prose rule for mechanical failures. Report only evidence-backed
improvements in Russian, in severity order. Number findings stably and include
project, issue key, run ID, observation, impact, and proposed change. Mark
uncertain inferences explicitly.

This skill is read-only. Do not repair findings or create follow-up issues
without the human's separate selection of numbered findings.
