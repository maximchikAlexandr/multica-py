## ADDED Requirements

### Requirement: 0.8.2 commands retain one controlled process boundary
All approved additions and repairs SHALL execute through the existing CLI transport and executor; they SHALL NOT introduce direct HTTP, shell evaluation, a second registry, or command-specific subprocess wrappers.

#### Scenario: Exact argv remains data
- **WHEN** a resource constructs any approved command
- **THEN** each positional value and flag is passed as a literal argv element and metacharacters, spaces, and attachment paths are not interpreted by a shell

#### Scenario: Global options remain inherited
- **WHEN** profile, workspace, server, timeout, cwd, environment, or debug options are scoped on the client or operation
- **THEN** the existing transport applies them with the same precedence and isolation as retained operations

### Requirement: File and stdin channels protect structured and secret input
Workflow step documents, descriptions, comment bodies, attachments, and any secret-bearing supported inputs SHALL use the reviewed file or stdin channel where the CLI provides one; generated diagnostics SHALL redact local paths and secret values.

#### Scenario: Workflow steps use a file channel
- **WHEN** workflow create/update receives structured steps
- **THEN** the SDK writes an owned temporary file with deterministic JSON, passes only its path through the reviewed flag, and removes the file on success or failure

#### Scenario: Secret or local path reaches diagnostics
- **WHEN** execution fails after a file-backed or secret-bearing input is prepared
- **THEN** exception text, argv snapshots, logs, fixtures, and evidence contain only the existing redacted representation

### Requirement: 0.8.2 errors map through reviewed safe boundaries
The transport SHALL classify reviewed 400/401/403/404/409/422 outcomes and malformed or unknown diagnostics without leaking private object existence or unreviewed backend fields.

#### Scenario: Private object is hidden
- **WHEN** the CLI returns the reviewed not-found behavior for a private project relation
- **THEN** the SDK raises `NotFoundError` rather than retrying, probing another endpoint, or exposing authorization metadata

#### Scenario: Unknown diagnostic remains generic
- **WHEN** stderr does not match a reviewed status prefix or structured safe-field schema
- **THEN** the SDK raises the generic command failure with existing redaction and preserves the actual exit code

