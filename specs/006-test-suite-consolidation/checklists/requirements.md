# Checklist качества требований

**Feature:** `006-test-suite-consolidation`  
**Результат:** PASS  
**Unresolved clarification markers:** 0

- [x] Scope ограничен tests, tooling, CI и packaging.
- [x] Public SDK behavior явно неизменен.
- [x] Пять user stories имеют priority и independent test.
- [x] Уменьшение test count разрешено, уменьшение coverage запрещено.
- [x] Baseline снимается после process repair и до deduplication.
- [x] Единственный case type зафиксирован как `OperationCase`.
- [x] `ERROR_CASES`, fake CLI protocol и fixture retention rule определены однозначно.
- [x] Offline network check является hard prohibition.
- [x] `CrudDescriptor` полностью декларативен; resource-specific branch запрещён.
- [x] `tools/live_support/`, четыре live contexts и один `LiveApiClient` зафиксированы.
- [x] Contract modules, package build/install paths и artifact contents определены.
- [x] LOC, file-size, coverage, mutation и duration gates измеримы.
- [x] Edge cases включают zombie, malformed output, cleanup failure и unrunnable live policy.
- [x] Альтернативных решений для implementer не осталось.
- [x] Маркеры `[NEEDS CLARIFICATION]` отсутствуют.
