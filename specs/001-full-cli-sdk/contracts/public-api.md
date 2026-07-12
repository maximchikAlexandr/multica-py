# Public API Contract

```python
from multica_py import MulticaClient, ClientConfig
```

The client exposes stable resource attributes. Methods accept typed request models for operations with more than two optional parameters. Simple reads/actions accept explicit keyword-only parameters.

Rules:

- All optional parameters after identifiers are keyword-only.
- All collection returns are tuples.
- All models are frozen.
- Every public method has an exact return type.
- No public signature contains `Any`, `object`, or unbounded `Mapping[str, object]`.
- Raw passthrough is available only through `client.transport.run_raw(...)` as a deliberately advanced, non-resource API and is not imported from package root.
- The console `multica-py exec` uses raw transport but does not weaken typed resource contracts.
