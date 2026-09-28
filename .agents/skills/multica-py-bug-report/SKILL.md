---
name: multica-py-bug-report
description: Prepare, independently review, and submit a reproducible multica-py bug report without bypassing safeguards.
---

# multica-py bug report

Use this skill when confirmed multica-py behaviour blocks or misleads work and
a reproducible GitHub report is the right next step.

## Workflow

1. Capture the smallest failing scenario and check obvious duplicates in
   `maximchikAlexandr/multica-py`.
2. Run `multica-py bug-report init --title "<one line>" --kind bug`.
3. Fill the returned `report.md`. Mark unknown values as `unknown`; separate
   facts from hypotheses.
4. Run `multica-py bug-report submit <REPORT_ID> --dry-run --json`.
5. Launch an independent sub-agent with `reviewer-prompt.md`, the draft files,
   and the printed payload hash. The reviewer alone writes `reviews/N.json`.
6. If changes are requested, update the report and repeat dry-run plus review.
   Stop after three completed `changes_requested` rounds.
7. Only after approval for the current payload hash run
   `multica-py bug-report submit <REPORT_ID>` and return the issue URL.

## Constraints

- Use the CLI boundary; do not call `gh issue create` directly.
- Never add a review-bypass or force flag.
- Never approve the report in the authoring agent's own session.
- Do not publish guessed facts, credentials, tokens, or private URLs.
- Keep the solution direction to the smallest confirmed change.
- The command always targets `maximchikAlexandr/multica-py` with label `bug`;
  repository and labels are not caller-controlled.

## Reference

- Independent reviewer contract: [reviewer-prompt.md](reviewer-prompt.md)
