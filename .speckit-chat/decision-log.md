# Decision Log

## Feature: 001-full-cli-sdk

### 2026-07-12 — Implementation decisions

- **Import package**: `multica_py` — per plan.md §1
- **PyPI distribution**: `multica-py` — per plan.md §1
- **Console entry point**: `multica-py` with subcommands doctor/version/coverage/exec — per plan.md §11
- **Build backend**: hatchling — per plan.md §1
- **Runtime dependency**: msgspec only — per plan.md §1
- **Python support**: 3.12/3.13 — per plan.md §1
- **Platform support**: Linux/macOS — per plan.md §1
- **Client sync-only v1**: No async — per research.md R-004
- **Models frozen**: All msgspec.Struct with frozen=True, kw_only=True — per plan.md §8
- **Error classification**: Exact domain errors only when source supports it — per research.md R-005
- **Compatibility**: STRICT/WARN/IGNORE policies — per plan.md §16
- **Secret redaction**: Token flags, env secrets, exception text — per plan.md §18
