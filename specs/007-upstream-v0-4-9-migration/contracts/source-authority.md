# Contract: Pinned Upstream Source Authority

The only accepted checkout is `.devlocal/upstream/multica-v0.4.9` at commit
`ecbdbda09e7b2be56cd9ccc55cee1ee360222d18`. Materialize and verify it:

```bash
test -d .devlocal/upstream/multica-v0.4.9/.git ||
  git clone --filter=blob:none https://github.com/multica-ai/multica.git \
    .devlocal/upstream/multica-v0.4.9
git -C .devlocal/upstream/multica-v0.4.9 checkout --detach \
  ecbdbda09e7b2be56cd9ccc55cee1ee360222d18
test "$(git -C .devlocal/upstream/multica-v0.4.9 rev-parse HEAD)" = \
  ecbdbda09e7b2be56cd9ccc55cee1ee360222d18
```

Every row uses repository `multica-ai/multica` and that full commit.

| ID | Path | Symbol | Lines |
| --- | --- | --- | --- |
| F-CHAT-HISTORY | `server/cmd/multica/cmd_chat.go` | `chatHistoryCmd` | 20-35 |
| F-CHAT-THREAD | `server/cmd/multica/cmd_chat.go` | `chatThreadCmd` | 37-48 |
| F-CHAT-READ | `server/cmd/multica/cmd_chat.go` | `fetchChatRead` | 80-112 |
| F-PROPERTY-DECL | `server/cmd/multica/cmd_property.go` | `propertyCmd/issuePropertyCmd` | 49-174 |
| F-PROPERTY-RUN | `server/cmd/multica/cmd_property.go` | `runPropertyCreate/runPropertyUpdate` | 306-393 |
| F-ISSUE-PROPERTY | `server/cmd/multica/cmd_property.go` | `runIssuePropertySet/runIssuePropertyUnset` | 608-695 |
| F-ISSUE-NEW-DECL | `server/cmd/multica/cmd_issue.go` | `issuePullRequestsCmd/issueChildrenCmd/issueReorderCmd` | 183-242 |
| F-ISSUE-REORDER | `server/cmd/multica/cmd_issue.go` | `registerIssueReorderFlags/runIssueReorder` | 1463-1633 |
| F-ISSUE-NEW-RUN | `server/cmd/multica/cmd_issue.go` | `runIssueCommentResolution/runIssueUsage` | 2011-2143 |
| F-ISSUE-DECL | `server/cmd/multica/cmd_issue.go` | `issueListCmd` | 436-448 |
| F-ISSUE-CREATE | `server/cmd/multica/cmd_issue.go` | `runIssueCreate` | 1052-1192 |
| F-ISSUE-UPDATE | `server/cmd/multica/cmd_issue.go` | `runIssueUpdate` | 1229-1343 |
| F-AGENT-SKILL | `server/cmd/multica/cmd_agent.go` | `agentSkillsAddCmd` | 120-130 |
| F-AGENT-PERM | `server/cmd/multica/cmd_agent.go` | `applyAgentPermissionFlags` | 501-531 |
| F-AGENT-RUN | `server/cmd/multica/cmd_agent.go` | `runAgentCreate/runAgentUpdate` | 533-709 |
| F-AGENT-SKILL-RUN | `server/cmd/multica/cmd_agent.go` | `runAgentSkillsSet/runAgentSkillsAdd` | 884-966 |
| F-ATTACHMENT | `server/cmd/multica/cmd_attachment.go` | `attachmentUploadCmd/runAttachmentUpload` | 34-110 |
| F-UPLOAD | `server/internal/cli/client.go` | `UploadChatAttachment` | 469-540 |
| F-REPO-DECL | `server/cmd/multica/cmd_repo.go` | `repoListCmd/repoAddCmd/repoRemoveCmd` | 18-74 |
| F-REPO-RUN | `server/cmd/multica/cmd_repo.go` | `runRepoList/runRepoAdd/runRepoRemove` | 155-285 |
| F-WORKSPACE-DECL | `server/cmd/multica/cmd_workspace.go` | `workspaceCreateCmd/workspaceMemberInviteCmd` | 27-76 |
| F-RUNTIME | `server/cmd/multica/cmd_runtime.go` | `runRuntimeDelete/runRuntimeRename` | 214-287 |
| F-RUNTIME-PROFILE | `server/cmd/multica/cmd_runtime_profile.go` | `runtimeProfileCmd/runRuntimeProfileList/runRuntimeProfileCreate/runRuntimeProfileUpdate/runRuntimeProfileDelete/runRuntimeProfileSetPath/runRuntimeProfileUnsetPath` | 35-339 |
| F-DAEMON | `server/cmd/multica/cmd_daemon.go` | `daemonProbeRuntimesCmd` | 53-58 |
| F-SKILL | `server/cmd/multica/cmd_skill.go` | `skillSearchCmd` | 66-71 |
| F-SKILL-RUN | `server/cmd/multica/cmd_skill.go` | `runSkillSearch` | 559-590 |
| F-SQUAD | `server/cmd/multica/cmd_squad.go` | `squadMemberSetRoleCmd/runSquadMemberSetRole` | 346-393 |
| F-AUTOPILOT | `server/cmd/multica/cmd_autopilot.go` | `runAutopilotCreate/runAutopilotUpdate` | 264-427 |
| F-PROJECT-FLAGS | `server/cmd/multica/cmd_project.go` | `projectCreateCmd/projectUpdateCmd` | 133-184 |
| F-PROJECT-RUN | `server/cmd/multica/cmd_project.go` | `runProjectCreate/runProjectUpdate` | 304-450 |
| F-ROOT | `server/cmd/multica/main.go` | `rootCmd` | 27-85 |
| F-CLIENT-ERROR | `server/internal/cli/client.go` | `httpTimeout/APIContext/newHTTPError` | 72-180 |
| F-CLIENT-UPLOAD | `server/internal/cli/client.go` | `DeleteJSONResponse/UploadChatAttachment` | 258-540 |
| F-ERRORS | `server/internal/cli/errors.go` | `ErrorKind/NetworkError/UserMessageError/HTTPError/classifyNetworkError/wrapTransport` | 1-492 |

Operation mappings use the smaller symbol-specific ranges in
`operation-decisions.md`; family refs prove family classification only.
Slash-separated symbols are an ordered set: validation requires every literal
identifier to occur within the inclusive line range. Wildcards are forbidden.
