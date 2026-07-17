# Contract: Observer and Collector Security

## Offline Blocking Gate

Runs on pull requests and normal pushes:

- Validates schemas and canonical artifacts.
- Compares supported contract to SDK coverage decisions.
- Runs contract/unit tests.
- Does not download Multica releases.
- Does not require live Multica account, server, network, or credentials.

## Scheduled Observer

Runs on schedule or manual dispatch:

- Reads upstream release metadata.
- Compares observed release identity to supported and candidate state.
- Downloads official release assets only when preparing a candidate.
- Verifies checksums before execution.
- Builds candidate contract and upgrade bundle.
- Creates or updates one idempotent tracking issue/PR per release.
- Never changes supported baseline or auto-merges coverage decisions.
- Uses a concurrency group keyed by upstream release tag or release ID.
- Labels generated tracking work with `upstream-update`.
- Marks generated tracking work as `needs-maintainer-decision`.
- Uses a deterministic issue/PR identity derived from upstream tag or release ID.
- Applies a superseded-candidate policy when a newer release replaces an older candidate.
- Pins every third-party GitHub Action by full commit SHA; first-party
  `actions/*` actions may use a major version only when a repository policy
  comment explains the exception in the workflow file.

## Collector Security Policy

Required controls:

- Verify official `checksums.txt` and selected release asset digest before extraction.
- Verify binary digest after extraction; if the extracted binary digest cannot
  be computed, collection fails with exit code `3`.
- Run collection without repository secrets.
- Use temporary `HOME` and config directories.
- Clear `MULTICA_*`, cloud provider, GitHub, and other token-like environment variables.
- Use stable `LANG=C`, `NO_COLOR=1`, and terminal width.
- Enforce per-node timeout, total timeout, stdout/stderr limits, and artifact size limits.
- Disable network during introspection when runner capabilities allow it.
- Record platform and collection method.
- Return collector failure for timeout, oversized output, or incomplete traversal.
- Treat explicit local binary collection as manual evidence unless it can be
  reproduced from a verified release asset or full source commit; local
  executable paths are not stored in checked-in artifacts.

Validation contract:

- Binary with checksum mismatch is never executed.
- Partial inventory cannot be promoted to complete contract.
- Observer repeated for the same release is idempotent.
- Failed observer or upgrade writes leave previous supported/candidate state
  intact or create a clearly invalid temporary artifact that cannot be promoted.
- Superseded candidates are marked with the newer release identity and never
  silently replace supported state.
- Collection job has no write token; separate job performs PR/issue updates when needed.
