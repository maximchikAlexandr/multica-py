# Merge-conflict webhook setup

The `Notify merge conflicts` workflow runs after every push to `main`. It sends
one event only when at least one open pull request is conflicting with the new
`main` revision.

Add the existing Multica conflict-router URL as the repository Actions secret
`MULTICA_CONFLICT_WEBHOOK_URL`:

1. Open **Settings → Secrets and variables → Actions**.
2. Create a repository secret named `MULTICA_CONFLICT_WEBHOOK_URL`.
3. Paste the complete HTTPS webhook URL as its value.
4. Run the workflow manually by pushing a harmless change to `main`, or wait
   for the next merge.

The URL must remain only in GitHub Actions secrets. Do not put it in workflow
YAML, repository files, logs, issues, or pull-request text.
