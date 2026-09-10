## ADDED Requirements

### Requirement: Trigger mutation surfaces remain aligned

The direct resource eager and command methods SHALL expose exactly:

```python
def trigger_add(
    self,
    autopilot_id: str,
    *,
    kind: str = "schedule",
    cron_expression: str | None = None,
    timezone: str | None = None,
    label: str | None = None,
    options: OperationOptions | None = None,
) -> AutopilotTrigger: ...

def trigger_add_command(
    self,
    autopilot_id: str,
    *,
    kind: str = "schedule",
    cron_expression: str | None = None,
    timezone: str | None = None,
    label: str | None = None,
    options: OperationOptions | None = None,
) -> Command[AutopilotTrigger]: ...

def trigger_update(
    self,
    autopilot_id: str,
    trigger_id: str,
    *,
    cron_expression: str | UnsetType = Unset,
    timezone: str | UnsetType = Unset,
    label: str | UnsetType = Unset,
    enabled: bool | UnsetType = Unset,
    options: OperationOptions | None = None,
) -> AutopilotTrigger: ...

def trigger_update_command(
    self,
    autopilot_id: str,
    trigger_id: str,
    *,
    cron_expression: str | UnsetType = Unset,
    timezone: str | UnsetType = Unset,
    label: str | UnsetType = Unset,
    enabled: bool | UnsetType = Unset,
    options: OperationOptions | None = None,
) -> Command[AutopilotTrigger]: ...
```

The corresponding bound `Autopilot` methods SHALL expose exactly:

```python
def trigger_add(
    self,
    *,
    kind: str = "schedule",
    cron_expression: str | None = None,
    timezone: str | None = None,
    label: str | None = None,
    options: OperationOptions | None = None,
) -> AutopilotTrigger: ...

def trigger_add_command(
    self,
    *,
    kind: str = "schedule",
    cron_expression: str | None = None,
    timezone: str | None = None,
    label: str | None = None,
    options: OperationOptions | None = None,
) -> Command[AutopilotTrigger]: ...

def trigger_update(
    self,
    trigger_id: str,
    *,
    cron_expression: str | UnsetType = Unset,
    timezone: str | UnsetType = Unset,
    label: str | UnsetType = Unset,
    enabled: bool | UnsetType = Unset,
    options: OperationOptions | None = None,
) -> AutopilotTrigger: ...

def trigger_update_command(
    self,
    trigger_id: str,
    *,
    cron_expression: str | UnsetType = Unset,
    timezone: str | UnsetType = Unset,
    label: str | UnsetType = Unset,
    enabled: bool | UnsetType = Unset,
    options: OperationOptions | None = None,
) -> Command[AutopilotTrigger]: ...
```

The bound forms differ from the matching direct forms only by removal of `autopilot_id`. No trigger mutation SHALL accept a request DTO, public `**kwargs`, or raw CLI string.

#### Scenario: Trigger add signatures match
- **WHEN** direct and bound trigger-add eager/command signatures are inspected
- **THEN** their parameter names, order, keyword-only boundaries, exact annotations, defaults, and `AutopilotTrigger`/`Command[AutopilotTrigger]` returns match the signatures above after removing the bound autopilot identifier

#### Scenario: Trigger update signatures match
- **WHEN** direct and bound trigger-update eager/command signatures are inspected
- **THEN** their parameter names, order, keyword-only boundaries, exact `str | UnsetType`/`bool | UnsetType` annotations, `Unset` defaults, unchanged options annotation/default, and `AutopilotTrigger`/`Command[AutopilotTrigger]` returns match the signatures above after removing the bound autopilot identifier

#### Scenario: Existing supported add kinds remain source-compatible
- **WHEN** a caller passes the existing string literal `kind="schedule"` or `kind="webhook"` to trigger add
- **THEN** runtime validation accepts it and static type checking reports no error

#### Scenario: Obsolete trigger inputs have documented replacements
- **WHEN** migration documentation is checked for the removed trigger `title` input and update `kind` input
- **THEN** it maps `title` to `label` and maps a required kind change to delete-and-add while retaining identifiers, `options`, eager/command forms, and bound method names

### Requirement: Strict compatibility preflight accepts the reviewed CLI envelope

A client configured with `CompatibilityPolicy.strict` SHALL remain I/O-free during construction and SHALL perform compatibility preflight immediately before its first governed transport operation. The preflight command arguments SHALL be `("version", "--output", "json")` with recursive compatibility checking disabled. The transport SHALL form the default full argv `("multica", "version", "--output", "json")` and SHALL preserve the existing global-argument order between the configured executable and the version subcommand. The shared decoder SHALL accept the CLI `0.4.38` JSON keys and values `version="0.4.38"`, `commit="47dc75741"`, `date="2026-09-02T09:52:29Z"`, `go="go1.26.7"`, `os="darwin"`, and `arch="arm64"`, map `date` and `go` to `CliVersion.build_date` and `CliVersion.go_version`, and ignore additive unknown keys. JSON object ordering SHALL NOT affect decoding. It SHALL NOT accept missing, blank, non-semantic, wrong-typed, malformed, or text-only version output as a successful strict check. After success, the original and snapshot transports SHALL share the checked state and SHALL execute the requested operation without another probe.

#### Scenario: Construction is lazy and first operation succeeds
- **WHEN** a strict client using the generated bounds is constructed for CLI `0.4.38` and its first public SDK operation is invoked
- **THEN** construction makes zero executor calls, the exact JSON version probe runs once before the requested operation, all six public `CliVersion` fields match the envelope, and the requested operation proceeds

#### Scenario: Configured global arguments retain their position
- **WHEN** strict preflight uses configured server URL, workspace ID, profile, or debug global arguments
- **THEN** `build_full_argv` places those arguments in its existing fixed order after the executable and before `version --output json`

#### Scenario: Invalid strict envelope fails before the operation
- **WHEN** the version output is text, malformed JSON, or contains a missing, blank, non-semantic, or wrong-typed `version`
- **THEN** strict compatibility raises `UnsupportedCliVersionError`, does not mark the shared state checked, and does not execute the requested operation

#### Scenario: Successful snapshot preflight is cached
- **WHEN** an original transport and any configuration snapshots perform governed operations after one successful strict preflight
- **THEN** the exact version probe appears once across their shared compatibility state
