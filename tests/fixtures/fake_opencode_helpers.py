from __future__ import annotations

import json
import pathlib
import sys
import textwrap
from dataclasses import dataclass

_FAKE_OPENCODE = pathlib.Path(__file__).resolve().parent / "fake_opencode.py"


@dataclass(frozen=True)
class InstructionPayload:
    """Deterministic fake OpenCode instruction payload."""

    run_id: str
    path: str = "target.txt"
    schema: int = 1

    @property
    def before(self) -> str:
        return f"before:{self.run_id}\n"

    @property
    def after(self) -> str:
        return f"after:{self.run_id}\n"

    def compact_json(self) -> str:
        payload: dict[str, int | str] = {
            "schema": self.schema,
            "path": self.path,
            "before": self.before,
            "after": self.after,
        }
        return json.dumps(payload, separators=(",", ":"))

    def prompt(self) -> str:
        return textwrap.dedent(
            f"""\
            Edit target.txt in the attached local directory.
            MULTICA_TEST_ACTION={self.compact_json()}
            """
        ).strip()


def fake_opencode_path() -> pathlib.Path:
    """Return the fake OpenCode executable path."""
    return _FAKE_OPENCODE


def canonical_argv(
    work_dir: pathlib.Path, prompt: str, *, executable: str | None = None
) -> list[str]:
    """Build canonical fake OpenCode argv for subprocess tests."""
    tail = [
        "run",
        "--format",
        "json",
        "--dangerously-skip-permissions",
        "--dir",
        str(work_dir.resolve()),
        "--model",
        "multica-test/fake",
        prompt,
    ]
    if executable is not None:
        return [executable, *tail]
    return [sys.executable, str(_FAKE_OPENCODE), *tail]


def prepare_instruction_workspace(tmp_path: pathlib.Path, run_id: str) -> InstructionPayload:
    """Write the default instruction workspace files."""
    payload = InstructionPayload(run_id=run_id)
    (tmp_path / payload.path).write_text(payload.before, encoding="utf-8")
    (tmp_path / "control.txt").write_text("control\n", encoding="utf-8")
    return payload
