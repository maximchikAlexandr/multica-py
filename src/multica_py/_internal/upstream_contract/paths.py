from __future__ import annotations

import pathlib

_MULTICA_PY_ROOT = pathlib.Path(__file__).resolve().parents[2]
GENERATED_DIR = _MULTICA_PY_ROOT / "_generated"
DEFAULT_STATE_PATH = GENERATED_DIR / "upstream_state.json"
SUPPORTED_CONTRACT_PATH = GENERATED_DIR / "upstream_supported_contract.json"
COVERAGE_PATH = GENERATED_DIR / "upstream_coverage.json"
STATE_REL = "src/multica_py/_generated/upstream_state.json"
SUPPORTED_CONTRACT_REL = "src/multica_py/_generated/upstream_supported_contract.json"
CANDIDATE_CONTRACT_REL = "src/multica_py/_generated/upstream_candidate_contract.json"
COVERAGE_REL = "src/multica_py/_generated/upstream_coverage.json"
