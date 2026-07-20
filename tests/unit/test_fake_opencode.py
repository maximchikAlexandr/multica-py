"""Unit tests for the deterministic fake OpenCode executable."""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass

import pytest

from tests.fixtures import fake_opencode
from tests.fixtures.fake_opencode_helpers import InstructionPayload, canonical_argv

pytestmark = pytest.mark.unit

_RUN_ID = "a" * 32


@dataclass(frozen=True)
class InstructionRejectCase:
    """One instruction validation rejection scenario."""

    id: str
    prompt: str
    match: str
    write_target: bool = True
    before: str | None = None


def _payload(**kwargs: object) -> InstructionPayload:
    return InstructionPayload(run_id=_RUN_ID, **kwargs)  # type: ignore[arg-type]


def _argv(work_dir: pathlib.Path, prompt: str) -> list[str]:
    return canonical_argv(work_dir, prompt, executable="fake_opencode.py")


def _write_target(work_dir: pathlib.Path, before: str) -> pathlib.Path:
    target = work_dir / "target.txt"
    target.write_text(before, encoding="utf-8")
    return target


def test_parse_canonical_argv_accepts_supported_command(tmp_path: pathlib.Path) -> None:
    """Canonical argv parsing accepts the supported OpenCode command."""
    prompt = _payload().prompt()
    parsed = fake_opencode.parse_canonical_argv(_argv(tmp_path, prompt))
    assert parsed.work_dir == tmp_path.resolve()
    assert parsed.prompt == prompt


def test_parse_canonical_argv_rejects_unsupported_option(tmp_path: pathlib.Path) -> None:
    """Unsupported argv options raise ArgvError."""
    argv = _argv(tmp_path, _payload().prompt())
    argv[2:2] = ["--verbose"]
    with pytest.raises(fake_opencode.ArgvError):
        fake_opencode.parse_canonical_argv(argv)


def test_success_replaces_file_atomically(tmp_path: pathlib.Path) -> None:
    """Success mode performs an exact atomic replacement."""
    payload = _payload()
    _write_target(tmp_path, payload.before)
    instruction = fake_opencode.parse_and_validate_instruction(payload.prompt(), tmp_path)
    exit_code = fake_opencode.run_instruction(tmp_path, instruction, mode="success")
    assert exit_code == 0
    assert (tmp_path / "target.txt").read_text(encoding="utf-8") == payload.after
    assert not (tmp_path / "target.txt.tmp").exists()


_INSTRUCTION_REJECT_CASES = (
    InstructionRejectCase(
        "malformed-json",
        "MULTICA_TEST_ACTION={not-json",
        "invalid instruction JSON",
    ),
    InstructionRejectCase(
        "unknown-schema",
        InstructionPayload(run_id=_RUN_ID, schema=2).prompt(),
        "unsupported schema",
    ),
    InstructionRejectCase(
        "absolute-path",
        _payload(path="/target.txt").prompt(),
        "relative POSIX path",
    ),
    InstructionRejectCase(
        "path-traversal",
        _payload(path="../target.txt").prompt(),
        "relative POSIX path",
    ),
    InstructionRejectCase(
        "missing-file",
        _payload().prompt(),
        "regular file",
        write_target=False,
    ),
    InstructionRejectCase(
        "before-mismatch",
        _payload().prompt(),
        "before content mismatch",
        before="different-content\n",
    ),
)


@pytest.mark.parametrize("case", _INSTRUCTION_REJECT_CASES, ids=lambda case: case.id)
def test_instruction_validation_rejects(
    tmp_path: pathlib.Path, case: InstructionRejectCase
) -> None:
    """Instruction validation rejects unsafe or invalid payloads before mutation."""
    before = case.before if case.before is not None else f"before:{_RUN_ID}\n"
    if case.write_target:
        _write_target(tmp_path, before)
    with pytest.raises(fake_opencode.InstructionError, match=case.match):
        fake_opencode.parse_and_validate_instruction(case.prompt, tmp_path)
    if case.write_target:
        assert (tmp_path / "target.txt").read_text(encoding="utf-8") == before
    else:
        assert not (tmp_path / "target.txt").exists()


def test_atomic_replace_uses_sibling_temporary_file(tmp_path: pathlib.Path) -> None:
    """Atomic replacement writes through a sibling temporary file."""
    target = _write_target(tmp_path, f"before:{_RUN_ID}\n")
    fake_opencode.atomic_replace_file(target, f"after:{_RUN_ID}\n")
    assert target.read_text(encoding="utf-8") == f"after:{_RUN_ID}\n"
    assert not target.with_name("target.txt.tmp").exists()


def test_success_event_lines_are_exact_jsonl_payload() -> None:
    """Success mode emits the exact three-line JSONL contract."""
    assert fake_opencode.success_event_lines() == (
        '{"type":"step_start","sessionID":"multica-test","part":{}}',
        '{"type":"text","sessionID":"multica-test","part":{"text":"Applied MULTICA_TEST_ACTION"}}',
        '{"type":"step_finish","sessionID":"multica-test","part":{"reason":"stop","tokens":{"input":0,"output":0}}}',
    )


def test_error_event_line_is_sanitized_json() -> None:
    """Instruction errors serialize to the required JSONL error envelope."""
    line = fake_opencode.error_event_line("before content mismatch")
    payload = json.loads(line)
    assert payload == {
        "type": "error",
        "sessionID": "multica-test",
        "error": {
            "name": "MulticaTestInstructionError",
            "message": "before content mismatch",
        },
    }
