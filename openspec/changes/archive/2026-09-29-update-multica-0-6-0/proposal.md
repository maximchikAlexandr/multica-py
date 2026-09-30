## Why

После merge PR #95 approved SDK baseline вырос до 193 operations и 196 response
entrypoints, поэтому прежний план от старого main повторно создавал уже
реализованные surfaces. Нужна новая ревизия прямого upgrade с exact baseline
`c1842ae2dfcd0cc5e739b7785d3209d5e72d01ed` на Multica `0.6.0`, сохраняющая
merged работу и принимающая только source-pinned target delta.

## What Changes

- Перевести approved contract, generated compatibility projection, документацию
  и release claims с target/max-tested `0.5.3` на `0.6.0` по pinned commit
  `ea94c7cd5bbce9c8e1f28c5fa049c47ee7651d02`.
- Сопоставить все 205 target CLI nodes: четыре added, zero removed, шесть changed;
  сохранить 23 новых baseline operations из PR #95 как retained, а не реализовать
  их повторно.
- Расширить существующий `IssueWakeupResource`: адаптировать create/update/list/
  get/disable/events к v2 и добавить typed trigger/delete/checkin/runs.
- Добавить agent-task cursor, issue-update attachments и совместимые projections
  для 18 changed entrypoints из полного registry 196/196; доказать 178 unchanged.
- Расширить текущие table-driven gates, source links, fixtures и consumer/release
  guidance без второго registry или fixture framework; live status оставить
  отдельным явным gate.
- Не продвигать `steer_task_ids`, extractor hardening, UI/mobile/desktop/search/
  channel/WeCom/internal scheduler behavior либо collector evidence в runtime API.

## Capabilities

### New Capabilities

- `issue-wakeup-resource`: Target-only trigger/delete/checkin/runs и v2 semantics
  уже существующего wakeup resource, включая deadline, conditions, fire limits и
  response evolution.

### Modified Capabilities

- `upstream-contract`: Provenance, complete command/response reconciliation,
  mappings и compatibility interval переходят с approved `0.5.3` на `0.6.0` от
  refreshed SDK baseline 193/196.
- `sdk-surface`: Существующие agent, issue, comment, pull-request, timeline и MCP
  surfaces получают approved inputs, pagination и additive typed fields.
- `verification-and-release`: Offline contract/model/resource/docs/package gates
  должны доказать один coherent direct upgrade без повторной реализации merged
  baseline operations.

## Impact

Изменение затрагивает `contracts/sdk-contract.json`, единственную generated runtime
projection, существующие wakeup/agent/issue/comment/PR/MCP models и adapters,
table-driven fixtures/tests, source-link audit, public inventories, documentation и
package checks. Dependencies не добавляются. Collector output, release binaries,
source checkouts и transient reports остаются untracked evidence; implementation
начинается только после новой независимой READY и human approval.
