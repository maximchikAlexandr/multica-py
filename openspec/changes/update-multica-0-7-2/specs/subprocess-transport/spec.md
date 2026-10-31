## ADDED Requirements

### Requirement: Forced daemon stop preserves target lifecycle safety
Daemon stop eager and command forms SHALL accept exact boolean `force=False`, append `--force` only when true, use the existing non-JSON action/lifecycle transport, and delegate graceful wait, profile/PID identity, forced termination, and cleanup confirmation to the pinned target CLI. The SDK SHALL NOT kill by executable name, signal an unresolved PID, fabricate structured status, retry, or report success before cleanup is confirmed.

#### Scenario: Ordinary stop remains unchanged
- **WHEN** daemon stop uses the default
- **THEN** exact argv SHALL omit `--force`, success SHALL retain `ActionResult[None]`, and no JSON decoder SHALL be selected

#### Scenario: Force stop terminates only the confirmed daemon
- **WHEN** force is true, graceful shutdown times out, and target confirms the selected profile and owned PID
- **THEN** exact argv SHALL include one `--force`, target SHALL terminate only the confirmed daemon process after the graceful timeout, and success SHALL be returned only after cleanup confirmation

#### Scenario: Identity or cleanup uncertainty fails closed
- **WHEN** PID/profile identity mismatches, the PID is unresolved, forced termination fails, or cleanup cannot be confirmed
- **THEN** the existing process/error boundary SHALL raise a failure, perform no SDK-side fallback kill, and SHALL not claim the daemon stopped
