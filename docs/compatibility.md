# Compatibility Policy

- SDK `1.x` targets the pinned CLI baseline at `multica-ai/multica@48b8dbf`
- `CompatibilityPolicy.STRICT` — requires configured min/max CLI version
- `CompatibilityPolicy.WARN` — allows newer versions, emits warning
- `CompatibilityPolicy.IGNORE` — skips version validation (default)

## Public API

`multica_py.compatibility` exposes `CliVersion` only: a frozen struct holding
parsed CLI version/build metadata (`version`, `commit`, `build_date`,
`go_version`, `os`, `arch`, `raw_output`).

## Runtime Compatibility

Runtime version checks live in `src/multica_py/_internal/compat.py`:

- `parse_cli_version` — decode JSON from `multica version --format json`
- `check_version` / `check_version_from_config` — enforce `ClientConfig.compatibility`
- `_load_supported_bounds` — read min/max CLI range from
  `src/multica_py/_generated/upstream_state.json` (`supported.version` and
  patch-bumped upper bound)
- `_warn_newer_untested_once` — emit at most one `UserWarning` per process when
  the detected CLI is newer than the SDK-tested range under `WARN` policy

`ClientConfig.min_cli_version` and `ClientConfig.max_cli_version` override the
generated defaults when set. Transport and resource code call
`check_version_from_config`; there is no diagnostics singleton on the public
module.

## Maintainer SSOT

Supported CLI bounds and maintainer-facing policy text also come from
`src/multica_py/_internal/compat.py`:

- `default_policy(sdk_version)` — build a `CliCompatMatrix` from
  `upstream_state.json`
- `supported_range_text(policy)` — human-readable range for reports and CLI
  output

The maintainer subcommand `scripts/upstream_contract.py compat --sdk-version X`
imports these helpers directly from `_internal.compat`.
