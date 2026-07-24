# Contract: Upstream Family Disposition

Every source-delta family has one primary disposition. A mixed family names its
required subset. Classification is not approval of an operation ID.
`deferred_owner_decision` means “excluded from Feature 007”; the implementer
does not request or make that future decision.

| Family | Disposition | Required operation IDs | Source refs |
| --- | --- | --- | --- |
| `issue-existing-changes` | `required_compatibility` | `["issues.comments.add","issues.comments.list","issues.create","issues.list"]` | `F-ISSUE-DECL`, `F-ISSUE-CREATE`, `F-ISSUE-UPDATE` |
| `issue-new-commands` | `required_subset_plus_extension_candidates` | `["issues.set_status"]` | `F-ISSUE-NEW-DECL`, `F-ISSUE-REORDER`, `F-ISSUE-NEW-RUN` |
| `project-and-root-registration` | `required_subset_plus_cli_only` | `["projects.create","projects.resources.add_local_directory","projects.resources.list","projects.resources.remove","projects.resources.update_local_directory","projects.set_status","projects.update"]` | `F-PROJECT-FLAGS`, `F-PROJECT-RUN`, `F-ROOT` |
| `attachments-and-client-transport` | `required_subset_plus_deferred_extension` | `["issues.comments.add","issues.create"]` | `F-ATTACHMENT`, `F-UPLOAD` |
| `transport-error-contract` | `required_compatibility` | `["issues.comments.add","issues.comments.delete","issues.comments.list","issues.create","issues.labels.add","issues.labels.list","issues.labels.remove","issues.list","issues.set_status","projects.create","projects.resources.add_local_directory","projects.resources.list","projects.resources.remove","projects.resources.update_local_directory","projects.set_status","projects.update"]` | `F-CLIENT-ERROR`, `F-CLIENT-UPLOAD`, `F-ERRORS` |
| `chat-read` | `separate_extension_candidate` | `[]` | `F-CHAT-HISTORY`, `F-CHAT-THREAD`, `F-CHAT-READ` |
| `workspace-properties` | `separate_extension_candidate` | `[]` | `F-PROPERTY-DECL`, `F-PROPERTY-RUN`, `F-ISSUE-PROPERTY` |
| `workspace-repository-management` | `deferred_owner_decision` | `[]` | `F-REPO-DECL`, `F-REPO-RUN`, `F-WORKSPACE-DECL` |
| `runtime-and-local-control` | `cli_only_plus_deferred_extension` | `[]` | `F-RUNTIME`, `F-RUNTIME-PROFILE`, `F-DAEMON` |
| `agent-settings-and-skills` | `deferred_owner_decision` | `[]` | `F-AGENT-SKILL`, `F-AGENT-PERM`, `F-AGENT-RUN`, `F-AGENT-SKILL-RUN` |
| `skills-squads-and-autopilots` | `deferred_owner_decision` | `[]` | `F-SKILL`, `F-SKILL-RUN`, `F-SQUAD`, `F-AUTOPILOT` |

Source-ref definitions are binding in `source-authority.md`.

Rules:

- The help-degraded 107 `command_removed` rows are not removal evidence.
- Existing raw/process wrappers outside the 16 governed IDs remain unchanged.
- The 35 target additions do not enter the approved contract, generated
  compatibility projection, or public signature solely because source or
  evidence contains them.
- Workspace repositories and project resources are semantically distinct.
- A future public addition requires a separate explicit scope and contract
  approval.
