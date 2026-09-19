## ADDED Requirements

### Requirement: Bound skill labels relation
A bound `Skill` SHALL always expose `labels` as `LazyCollection[Label]`. The collection SHALL be preloaded from the required labels array for `skills.list` results and SHALL start unloaded when a retained skill-detail response omits labels. An unloaded or invalidated collection SHALL be backed only by the approved `skills.labels.list` operation. Successful add or remove mutations through the bound skill SHALL invalidate the cached relation.

#### Scenario: List-result labels are already loaded
- **WHEN** a bound skill from `skills.list` has empty or populated labels and its labels are read repeatedly without mutation
- **THEN** the preloaded typed labels SHALL be reused and no label-list transport SHALL execute

#### Scenario: Detail-result labels load once until invalidated
- **WHEN** a bound skill from `skills.get` omitted labels and its labels are read repeatedly without mutation
- **THEN** the approved list operation SHALL execute once and the loaded typed labels SHALL be reused

#### Scenario: Add invalidates labels
- **WHEN** a bound skill successfully adds a label
- **THEN** its cached label collection SHALL invalidate and the next read SHALL reload it

#### Scenario: Remove invalidates after detach
- **WHEN** a bound skill successfully detaches a label, including the reviewed refresh-fallback path
- **THEN** its cached label collection SHALL invalidate and SHALL NOT retain the removed label as authoritative

#### Scenario: Unbound access fails without transport
- **WHEN** an unbound skill accesses or mutates its label relation
- **THEN** the established bound-entity error SHALL occur before CLI transport
