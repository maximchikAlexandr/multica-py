## 1. Typed Issue property relation

- [ ] 1.1 Change issue property projection handling so only complete resolved rows initialize `LazyMapping[str, PropertyValue]`; keep UUID-keyed JSON maps in the raw issue projection and route the typed relation through the existing property-list loader.
- [ ] 1.2 Replace the raw-map relation expectation with table-driven list/get/public-relation regressions covering scalar and structured raw values, name-keyed `PropertyValue` results, resolved-row eager snapshots, no per-item issue get, and raw projection serialization compatibility.

## 2. Concurrent synchronous local I/O

- [ ] 2.1 Move initial stdin delivery into the bounded `Popen.communicate` loop so stdin, stdout, and stderr progress concurrently without resubmitting input after a polling timeout, while preserving cancellation, timeout escalation, descendant cleanup, and exact-byte results.
- [ ] 2.2 Extend the real child-process fixture and component process-contract table with above-pipe-capacity three-channel success and bounded-timeout cases, asserting exact output and the existing timeout/cleanup behavior.

## 3. Non-blocking spawned initial stdin

- [ ] 3.1 Make `LocalProcessHandle` own one-time asynchronous initial stdin delivery and concurrent output pumps for spawned requests, preserving buffered/streaming ownership, wait/close behavior, and retryable collection after `ProcessTimeoutError`.
- [ ] 3.2 Change `LocalExecutor.spawn` to return the initialized handle without writing request stdin on the caller thread, and add unit coverage for exact-once delivery, pipe closure, worker cleanup, timeout retry, and error-safe close.
- [ ] 3.3 Add a deterministic real-process component case proving spawn returns while a large stdin reader is gated and later buffered collection preserves the complete stdin-dependent stdout and stderr payloads.

## 4. Verification and delivery

- [ ] 4.1 Run the focused issue resource/relation, local process lifecycle, executor conformance, and component process-contract tests; repair regressions without widening the public API or dependency set.
- [ ] 4.2 Run strict OpenSpec validation, Ruff format/check, mypy for source and tests, the complete non-live pytest suite with live-node exclusion, and the repository-required `make pr` gate; record exact command evidence and leave generated/transient artifacts untracked.
