# Contract: Process Harness

`tests/fixtures/child_process.py` поддерживает ровно эти capabilities:

- emit stdout/stderr and exit;
- write ready file;
- wait for release file;
- ignore SIGTERM;
- spawn one descendant;
- write parent and descendant PID files.

`tests/fixtures/process_state.py` определяет `running`, `zombie`, `absent` и adapters:

- Linux: `/proc/<pid>/stat`;
- macOS: `ps -o stat= -p <pid>`.

Zombie считается execution-ended. После этого helper ждёт `absent` максимум 2.0 seconds с interval 0.02 seconds.

`tests/component/test_process_contract.py` содержит ровно четыре parameter IDs:

- `cancellation`
- `timeout`
- `sigterm-escalation`
- `descendant-cleanup`

Module имеет markers `process` и `serial`; test имеет timeout 20 seconds. Finalizer всегда закрывает pipes, завершает process group и повторно проверяет отсутствие running parent/descendant.
