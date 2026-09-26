## 1. Bound lifecycle implementation

- [ ] 1.1 Extract one pure exact-ID TaskRun selector from the existing streaming refresh path, preserve `ProtocolError` when a successful issue-runs page omits the target, and keep `TaskRun.stream_events()` behavior unchanged.
- [ ] 1.2 Add `TaskRun.refresh_command(*, options=None)` over `IssueResource.runs_command(issue_id, options=options)` and `TaskRun.refresh(*, options=None)` as its eager wrapper, requiring the bound client and inherited issue context and returning the newly bound selected snapshot.
- [ ] 1.3 Add `TaskRun.cancel_command(*, options=None)` over `IssueResource.cancel_task_command(self.id, issue_id=self.issue_id, options=options)` and `TaskRun.cancel(*, options=None)` as its eager wrapper, preserving task-ID-only addressing when issue context is absent and returning `ActionResult[None]` without refresh or mutation.

## 2. Governed surface and focused verification

- [ ] 2.1 Extend the explicit bound-operation declarations and public method discovery expectations for the four TaskRun methods while leaving the canonical root operation inventory and `contracts/sdk-contract.json` unchanged.
- [ ] 2.2 Add table-driven command/eager cases using existing fixtures for exact default and option-bearing argv, zero construction I/O, result type, exact refreshed run selection, originating-client binding, eager/command parity, and original snapshot immutability.
- [ ] 2.3 Add focused negative cases for detached refresh/cancel, missing refresh issue context, optional cancel issue context, successful refresh without the target, and propagation of root validation/transport failures without retries or extra calls.
- [ ] 2.4 Run focused issue resource, bound entity/relation, operation inventory, signature, and type-check coverage and confirm `Issue.runs`, `TaskRun.messages`, and `TaskRun.stream_events` regress neither behavior nor public shape.

## 3. Documentation and delivery gates

- [ ] 3.1 Update API and service-usage documentation with direct and inspectable refresh/cancel examples, explicit refresh after cancellation, unchanged message access, and the stated lifecycle non-goals.
- [ ] 3.2 Run strict OpenSpec validation, Ruff format/check, mypy for source and tests, the complete non-live pytest suite with live-node exclusion, build/package validation, and the repository-required `make pr` gate; record exact command evidence and leave no transient artifacts.
