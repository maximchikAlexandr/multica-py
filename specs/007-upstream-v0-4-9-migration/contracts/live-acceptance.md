# Contract: Prepared Live Acceptance

The SDK repository does not own backend provisioning, direct HTTP access,
agent-sandbox lifecycle, or an extended live acceptance state machine.

Prepared-target acceptance is the five-scenario smoke suite in
`tests/live/test_smoke.py`. It verifies CLI release identity, project CRUD,
comment list decoding, not-found mapping, and project-update presence
semantics. The runner supplies the CLI, server URL, workspace, expected
version, and preauthenticated profile through the environment contract in
`tests/live/README.md`.

The default verification suite remains offline. Live acceptance is a manual
workflow outcome and does not copy credentials into the repository, pytest
environment, artifacts, or command line.
