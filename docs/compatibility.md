# Compatibility Policy

The generated runtime constants in
`src/multica_py/_generated/approved_sdk.py` define the reviewed CLI interval:

- `MIN_CLI_VERSION` equals `TARGET_VERSION`;
- `MAX_CLI_VERSION` is the exclusive next patch version.

`multica_py._internal.compat` imports these constants. Client configuration
may override the bounds explicitly, while `strict`, `warn`, and `ignore`
retain their documented runtime behaviour.

For an upstream release, use the reviewed flow:

```text
collect → validate --source-checkout → render → check
```

Evidence and transient reports are not runtime inputs. Only a reviewed Git
change to `contracts/sdk-contract.json` and the single generated runtime
projection can promote a new compatibility interval.
