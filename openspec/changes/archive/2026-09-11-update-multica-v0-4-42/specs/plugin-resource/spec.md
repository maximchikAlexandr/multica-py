## REMOVED Requirements

### Requirement: Workspace-private Plugin resource is governed

**Reason**: Multica `0.4.42` removes the complete public `plugin` Cobra hierarchy, so these methods cannot satisfy the target compatibility contract.

**Migration**: Remove Plugin SDK calls and do not substitute an unreviewed app, raw CLI path, or remote-MCP mechanism; pin an older SDK/CLI pair only as an explicit temporary consumer decision.

### Requirement: Plugin Remote MCP uses secret-safe inputs

**Reason**: The target CLI exposes no Plugin Remote MCP commands.

**Migration**: Remove these calls; there is no approved in-SDK replacement in this change.
