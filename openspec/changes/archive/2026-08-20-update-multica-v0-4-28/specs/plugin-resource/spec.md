## ADDED Requirements

### Requirement: Workspace-private Plugin resource is governed

The SDK SHALL expose `MulticaClient.plugins` with eager and `*_command` methods
for the tagged `v0.4.28` `plugin` command family. `list` and `status` SHALL emit
`plugin list` and `plugin status [installation-id|plugin-key]` with
`--output json`. Workspace scope SHALL default to client `--workspace-id`;
canonical argv SHALL list command tokens only and SHALL NOT require a command
`--workspace` flag on `list()`. If tagged CLI source shows a distinct command
`--workspace` flag, the SDK MAY expose it as an optional method kwarg mapped
1:1 after that trace. Bound `Workspace.plugins` SHALL use `with_workspace(self.id)`
like other unpaged workspace relations. List/status rows SHALL decode into one
public frozen `Plugin` type that preserves reviewed JSON keys including
`plugin_key`, `desired_version`, `lifecycle_status`, `trust_tier`, and
`uploader_id`. The SDK SHALL NOT ship a second public name for the same JSON
row. `list`, `status`, `validate`, `pack`, and `init` SHALL emit `--output json`
unless source proves a given command is non-JSON. `validate` and `pack` SHALL
invoke the CLI against a caller path and decode a separate digest type, not
`Plugin`. `init` SHALL invoke `plugin init <dir>` with reviewed flags (`--key`,
`--name`, `--publisher`, `--contribution`, `--endpoint-host`) and SHALL NOT
parse or rewrite `multica.plugin.json` in Python. `install` SHALL emit
`plugin install <dir|archive>`. When upstream `requireHumanLocalCommand` refuses
agent or daemon contexts, the contract SHALL record that human-local constraint
and tests SHALL assert the reviewed refusal rather than inventing a Python HTTP
installer.

#### Scenario: Plugin list returns typed installations
- **WHEN** `client.plugins.list()` runs against a JSON array of private plugin rows
- **THEN** argv is `plugin list --output json` with no required command `--workspace` flag, and each row decodes to frozen `Plugin` preserving key, version, lifecycle, trust, and uploader fields

#### Scenario: Plugin status accepts an optional identifier
- **WHEN** `status()` is called without an id
- **THEN** argv is `plugin status --output json` and the decoder accepts the list envelope used by the CLI

#### Scenario: Plugin status with an id fetches one installation
- **WHEN** `status(plugin_key_or_id)` is called
- **THEN** argv is `plugin status <id> --output json` and the decoder accepts the single-object JSON returned by GET

#### Scenario: Validate and pack stay local CLI operations
- **WHEN** `validate(path)` or `pack(dir, output=zip_path)` is constructed
- **THEN** argv includes `--output json` unless source proves that command is non-JSON, matches `plugin validate <path>` or `plugin pack <dir>` plus the reviewed pack output flag, and digest fields round-trip on a type distinct from `Plugin` without the SDK reading the ZIP itself

#### Scenario: Init does not invent a Python packer
- **WHEN** `init(dir, contribution="skill")` runs
- **THEN** argv contains `plugin init <dir>` and `--contribution skill`, contains no `--output`, and no SDK helper writes a manifest except through that CLI invocation

#### Scenario: Plugin workspace override is explicit
- **WHEN** plugin list or status is called with an explicit workspace override
- **THEN** argv contains `--workspace <value>` while omission continues to use client workspace scope

#### Scenario: Human-local install is recorded
- **WHEN** source shows `plugin install` calls `requireHumanLocalCommand`
- **THEN** the approved operation records that constraint, offline tests cover exact argv, and a reviewed non-human context is expected to fail at the CLI rather than be silently skipped by omitting the public method

### Requirement: Plugin Remote MCP uses secret-safe inputs

`PluginResource` SHALL expose reviewed Remote MCP operations mapping to
`plugin remote-mcp configure|test|approve|revoke <plugin-key> <contribution-key>`.
Configure SHALL require `--endpoint` and SHALL accept a credential only through
`--credential-file` or `--credential-stdin`, which are mutually exclusive. The
SDK SHALL NOT add a plaintext `--credential` string flag. `--credential-file`
path is not a secret; stdin and file **contents** SHALL be collected into
`secret_values`. Credential bytes, auth headers, and related secret values
SHALL be redacted from preview, diagnostics, and exception attributes while
executed argv still receives the file-path flag. Approve SHALL require at least
one `--tool`. Revoke SHALL map to the reviewed DELETE credential path.

#### Scenario: Configure rejects mixed credential channels
- **WHEN** both credential file and stdin are present
- **THEN** construction raises `ValueError` before transport

#### Scenario: Configure carries public configuration by file path
- **WHEN** configure is called with `public_config_file=path`
- **THEN** argv contains `--public-config-file <path>`, SDK construction performs no file IO, and the path is not collected as a secret

#### Scenario: Configure redacts credentials
- **WHEN** configure runs with a credential file
- **THEN** preview, `str(exc)`, and redacted argv omit the credential bytes while the executed subprocess still receives the file path flag

#### Scenario: Approve requires tools
- **WHEN** approve is constructed with an empty tool tuple
- **THEN** construction raises `ValueError` naming the missing tools before transport
