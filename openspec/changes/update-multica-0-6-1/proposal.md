## Why

Reviewed SDK baseline `0.6.0` уже соответствует 205 CLI nodes и 196 response
entrypoints, но stable Multica `0.6.1` добавляет presence-sensitive duplicate
transition к существующим issue mutations и уточняет несколько совместимых
response/error semantics. Нужен один source-pinned direct upgrade от exact SDK
commit `48745d2fe9e80ee9c027293ef22971ff5723f5f5`, не расширяющий public API из
collector evidence автоматически.

## What Changes

- Перевести approved contract, generated compatibility projection и release/docs
  claims с target `0.6.0` на stable `0.6.1` commit
  `2ea01ae4ef55de4310b99af192d2dbd367832883`, сохранив archive, executable и
  version-output digests как разные provenance facts.
- Сохранить полный inventory 205/205 CLI nodes: 203 unchanged и два adapted
  (`issue status`, `issue update`), без новых или удалённых command nodes.
- Добавить optional Python input `duplicate_of` к direct и bound
  `set_status[_command]`/`update[_command]`, используя существующий
  `Issue.duplicate_of`; обеспечить omission, nonblank validation, cancelled-only
  status policy, update content/attachment conflicts и отсутствие partial upload.
- Пересогласовать все 196 supported response entrypoints: девять изменившихся
  semantics получают pinned provenance/fixtures, остальные 187 доказываются как
  unchanged; open strings и integer tick precision не сужаются.
- Обновить существующие table-driven contract/unit/component/live gates,
  deterministic render, source-link audit, package/docs/release checks и единый
  rollback. Новые dependencies, competing models/adapters и tracked evidence не
  добавляются.

## Capabilities

### New Capabilities

Нет.

### Modified Capabilities

- `upstream-contract`: exact provenance, 205-node inventory, двухкомандный input
  delta и полный 196-entrypoint response audit переходят с `0.6.0` на `0.6.1`.
- `sdk-surface`: четыре существующих direct/bound issue mutation entrypoints
  получают `duplicate_of`, а quota, usage и repository-checkout semantics остаются
  совместимыми и presence/open-value safe.
- `verification-and-release`: table-driven positive/negative coverage, docs,
  compatibility interval, deterministic generation, packaging и rollback должны
  доказать coherent direct upgrade без tracked evidence и transient artifacts.

## Impact

Изменение затрагивает `contracts/sdk-contract.json`, единственную generated
runtime projection, существующие issue resource/bound methods, table-driven
operation/response fixtures, compatibility and repository-checkout error tests,
README/docs и package/release evidence. Production dependencies и отдельные SDK
operations не добавляются. `.devlocal` evidence, upstream source checkout,
archives, binaries и visual report остаются вне Git; implementation начинается
только после независимой проверки и human gate.
