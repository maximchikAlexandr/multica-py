# entity-permalinks Specification

## Purpose
TBD - created by archiving change simplify-public-sdk-experience. Update Purpose after archive.
## Requirements
### Requirement: Explicit web routing context
`ClientConfig` SHALL accept independent `app_url` and `workspace_slug` settings for web permalinks. `app_url` SHALL be an absolute HTTPS URL, except HTTP SHALL be allowed for localhost/loopback self-hosting; credentials, query, and fragment SHALL be rejected and trailing slashes normalized. `workspace_slug` SHALL be one nonblank URL path segment. The SDK SHALL NOT infer the frontend origin from `server_url`, infer a slug from workspace ID/name, or perform I/O to discover either value.

#### Scenario: Hosted context is explicit
- **WHEN** a hosted client is configured with `app_url="https://multica.ai"` and its workspace slug
- **THEN** permalink construction uses exactly that origin and slug

#### Scenario: Self-hosted context is independent from API URL
- **WHEN** a self-hosted client supplies different `server_url` and `app_url` values
- **THEN** CLI execution uses `server_url` while permalinks use only `app_url`

#### Scenario: Unsafe routing context is rejected
- **WHEN** app URL contains credentials/query/fragment or an unsafe remote HTTP origin, or the slug is blank/contains a slash
- **THEN** configuration raises `ValueError`

### Requirement: Stable Issue and Project permalinks
Bound `Issue` and `Project` SHALL expose pure `permalink() -> str` methods using the reviewed web routes `/{workspace_slug}/issues/{url-encoded-id}` and `/{workspace_slug}/projects/{url-encoded-id}`. The method SHALL preserve the entity's originating client context, perform no subprocess/network I/O, and raise a typed missing-context error when either required configuration value is absent.

#### Scenario: Issue permalink uses the reviewed route
- **WHEN** a bound issue with ID `issue_123` has complete web context
- **THEN** `issue.permalink()` returns `<app_url>/<workspace_slug>/issues/issue_123`

#### Scenario: Project permalink uses the reviewed route
- **WHEN** a bound project with ID `project_123` has complete web context
- **THEN** `project.permalink()` returns `<app_url>/<workspace_slug>/projects/project_123`

#### Scenario: Missing context fails clearly
- **WHEN** a detached entity or bound entity without app URL/workspace slug requests a permalink
- **THEN** a typed SDK error names the missing web-routing context and no guessed URL is returned

#### Scenario: Permalink access is passive
- **WHEN** `permalink()` is called repeatedly
- **THEN** no CLI, filesystem, or network operation occurs

