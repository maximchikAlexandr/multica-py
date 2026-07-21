#!/usr/bin/env python3
"""Deterministic OpenCode-compatible executable for agent sandbox tests."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import cast

_EXIT_USAGE = 64
_EXIT_INSTRUCTION = 2
_EXIT_AGENT_ERROR = 1
_FAKE_VERSION = "1.0.0"
_REQUIRED_MODEL = "multica-test/fake"
_ACTION_PREFIX = "MULTICA_TEST_ACTION="
_INSTRUCTION_KEYS = frozenset({"schema", "path", "before", "after"})
_ALLOWED_MODES = frozenset({"success", "error", "timeout", "wrong-edit"})
_STEP_START = '{"type":"step_start","sessionID":"multica-test","part":{}}'
_TEXT_EVENT = (
    '{"type":"text","sessionID":"multica-test","part":{"text":"Applied MULTICA_TEST_ACTION"}}'
)
_STEP_FINISH = '{"type":"step_finish","sessionID":"multica-test","part":{"reason":"stop","tokens":{"input":0,"output":0}}}'
_ERROR_NAME = "MulticaTestInstructionError"
_UUID = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
_ISSUE_ID_RE = re.compile(rf"Your assigned issue ID is:\s*({_UUID})")
_ISSUE_GET_RE = re.compile(rf"multica issue get\s+({_UUID})")


@dataclass(frozen=True)
class ParsedArgv:
    """Canonical OpenCode argv values."""

    work_dir: Path
    prompt: str


@dataclass(frozen=True)
class AgentSandboxInstruction:
    """Validated sandbox file-replacement instruction."""

    schema: int
    path: str
    before: str
    after: str


class ArgvError(Exception):
    """Raised when argv does not match the single supported command."""


class InstructionError(Exception):
    """Raised when MULTICA_TEST_ACTION validation fails."""


def parse_canonical_argv(argv: list[str]) -> ParsedArgv:
    """Parse and validate the single supported OpenCode argv shape.

    Args:
        argv: Process argv including the executable path at index zero.

    Returns:
        Parsed work directory and prompt.

    Raises:
        ArgvError: When argv is not the supported canonical command.
    """
    if len(argv) < 2 or argv[1] != "run":
        raise ArgvError("unsupported command")

    work_dir: str | None = None
    model: str | None = None
    format_value: str | None = None
    skip_permissions = False
    prompt: str | None = None
    index = 2
    while index < len(argv):
        token = argv[index]
        if token == "--dangerously-skip-permissions":
            skip_permissions = True
            index += 1
            continue
        if not token.startswith("--"):
            if prompt is not None:
                raise ArgvError("unexpected positional argument")
            prompt = token
            index += 1
            continue
        if index + 1 >= len(argv):
            raise ArgvError("missing option value")
        value = argv[index + 1]
        if token == "--format":
            format_value = value
        elif token == "--dir":
            work_dir = value
        elif token == "--model":
            model = value
        else:
            raise ArgvError("unsupported option")
        index += 2

    if (
        format_value != "json"
        or not skip_permissions
        or work_dir is None
        or model != _REQUIRED_MODEL
        or prompt is None
    ):
        raise ArgvError("invalid canonical argv")

    resolved_dir = Path(work_dir)
    if not resolved_dir.is_absolute() or not resolved_dir.is_dir():
        raise ArgvError("invalid work directory")

    return ParsedArgv(work_dir=resolved_dir, prompt=prompt)


def extract_action_line(text: str) -> str:
    """Return the compact JSON payload from a MULTICA_TEST_ACTION line.

    Args:
        text: Prompt or issue description text.

    Returns:
        Compact JSON object text following MULTICA_TEST_ACTION=.

    Raises:
        InstructionError: When the text does not contain exactly one action line.
    """
    matches = [
        line[len(_ACTION_PREFIX) :] for line in text.splitlines() if line.startswith(_ACTION_PREFIX)
    ]
    if len(matches) != 1:
        raise InstructionError("prompt must contain exactly one MULTICA_TEST_ACTION line")
    return matches[0]


def extract_issue_id(prompt: str) -> str:
    """Return the assigned issue ID from a Multica daemon bootstrap prompt.

    Args:
        prompt: Final OpenCode prompt text from Multica ``BuildPrompt``.

    Returns:
        Issue UUID embedded in the bootstrap prompt.

    Raises:
        InstructionError: When no assigned issue ID can be parsed.
    """
    match = _ISSUE_ID_RE.search(prompt) or _ISSUE_GET_RE.search(prompt)
    if match is None:
        raise InstructionError("prompt must contain an assigned issue ID")
    return match.group(1)


def fetch_issue_description(issue_id: str) -> str:
    """Fetch issue description via the Multica CLI in the agent environment.

    Args:
        issue_id: Issue UUID to fetch.

    Returns:
        Issue description text.

    Raises:
        InstructionError: When the CLI call fails or description is missing.
    """
    try:
        completed = subprocess.run(
            ["multica", "issue", "get", issue_id, "--output", "json"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise InstructionError("failed to fetch issue description") from exc
    if completed.returncode != 0:
        raise InstructionError(f"failed to fetch issue description (exit {completed.returncode})")
    try:
        payload: object = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise InstructionError("invalid issue get JSON") from exc
    if not isinstance(payload, dict):
        raise InstructionError("invalid issue get JSON")
    description = payload.get("description")
    if not isinstance(description, str):
        raise InstructionError("issue description missing")
    return description


def resolve_action_payload(prompt: str) -> str:
    """Resolve MULTICA_TEST_ACTION from the prompt or issue description.

    Multica's daemon bootstrap prompt tells the agent to run ``issue get`` and
    does not embed the issue body. Prefer an inline action line when present
    (unit/component fixtures); otherwise fetch the description via Multica CLI.

    Args:
        prompt: Final OpenCode prompt text.

    Returns:
        Compact JSON object text following MULTICA_TEST_ACTION=.

    Raises:
        InstructionError: When the action cannot be resolved.
    """
    matches = [
        line[len(_ACTION_PREFIX) :]
        for line in prompt.splitlines()
        if line.startswith(_ACTION_PREFIX)
    ]
    if len(matches) > 1:
        raise InstructionError("prompt must contain exactly one MULTICA_TEST_ACTION line")
    if len(matches) == 1:
        return matches[0]
    return extract_action_line(fetch_issue_description(extract_issue_id(prompt)))


def parse_instruction_json(payload: str) -> dict[str, object]:
    """Parse compact JSON for a sandbox instruction.

    Args:
        payload: Compact JSON object text.

    Returns:
        Parsed JSON object.

    Raises:
        InstructionError: When JSON is malformed or not an object.
    """
    try:
        parsed_object: object = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise InstructionError("invalid instruction JSON") from exc
    if not isinstance(parsed_object, dict):
        raise InstructionError("invalid instruction JSON")
    return cast("dict[str, object]", parsed_object)


def validate_instruction(data: dict[str, object], work_dir: Path) -> AgentSandboxInstruction:
    """Validate instruction schema, path containment, and exact-before semantics.

    Args:
        data: Parsed instruction object.
        work_dir: Absolute workspace directory from --dir.

    Returns:
        Validated instruction.

    Raises:
        InstructionError: When validation fails.
    """
    if set(data.keys()) != _INSTRUCTION_KEYS:
        raise InstructionError("instruction must contain exactly four keys")

    schema = data["schema"]
    path_value = data["path"]
    before_value = data["before"]
    after_value = data["after"]
    if not isinstance(schema, int):
        raise InstructionError("unsupported schema")
    if schema != 1:
        raise InstructionError("unsupported schema")
    if not isinstance(path_value, str):
        raise InstructionError("path must be a relative POSIX path")
    if not isinstance(before_value, str) or not isinstance(after_value, str):
        raise InstructionError("before and after must be strings")

    relative_path = _validate_relative_path(path_value)
    target = _resolve_contained_path(work_dir, relative_path)
    if not target.is_file():
        raise InstructionError("target must be a regular file")

    current = target.read_text(encoding="utf-8")
    if current != before_value:
        raise InstructionError("before content mismatch")

    return AgentSandboxInstruction(
        schema=schema,
        path=relative_path,
        before=before_value,
        after=after_value,
    )


def _validate_relative_path(path_value: str) -> str:
    pure = PurePosixPath(path_value)
    if pure.is_absolute():
        raise InstructionError("path must be a relative POSIX path")
    parts = pure.parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise InstructionError("path must be a relative POSIX path")
    return pure.as_posix()


def _resolve_contained_path(work_dir: Path, relative_path: str) -> Path:
    root = work_dir.resolve()
    target = (root / relative_path).resolve()
    if not target.is_relative_to(root):
        raise InstructionError("path must stay inside work directory")
    return target


def atomic_replace_file(target: Path, content: str) -> None:
    """Write content to a sibling temporary file and atomically replace target.

    Args:
        target: Existing regular file to replace.
        content: UTF-8 text to write.
    """
    temp_path = target.with_name(f"{target.name}.tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp_path, target)


def success_event_lines() -> tuple[str, str, str]:
    """Return the required success JSONL event lines."""
    return (_STEP_START, _TEXT_EVENT, _STEP_FINISH)


def error_event_line(message: str) -> str:
    """Return one sanitized JSONL error event line."""
    payload = {
        "type": "error",
        "sessionID": "multica-test",
        "error": {"name": _ERROR_NAME, "message": message},
    }
    return json.dumps(payload, separators=(",", ":"))


def emit_error(message: str) -> None:
    """Write one JSONL error event to stdout."""
    sys.stdout.write(error_event_line(message) + "\n")
    sys.stdout.flush()


def emit_success_stream() -> None:
    """Write the required three-line success JSONL stream."""
    for line in success_event_lines():
        sys.stdout.write(line + "\n")
    sys.stdout.flush()


def emit_step_start() -> None:
    """Write the step_start JSONL event."""
    sys.stdout.write(_STEP_START + "\n")
    sys.stdout.flush()


def extract_run_id(before: str) -> str:
    """Extract run_id from a before:<run_id> instruction prefix."""
    prefix = "before:"
    if not before.startswith(prefix):
        raise InstructionError("before content mismatch")
    suffix = before[len(prefix) :]
    if not suffix.endswith("\n"):
        raise InstructionError("before content mismatch")
    return suffix[:-1]


def parse_and_validate_instruction(prompt: str, work_dir: Path) -> AgentSandboxInstruction:
    """Extract, parse, and validate MULTICA_TEST_ACTION from a prompt or issue."""
    data = parse_instruction_json(resolve_action_payload(prompt))
    return validate_instruction(data, work_dir)


def resolve_agent_mode() -> str:
    """Return normalized agent mode from the environment."""
    raw = os.environ.get("MULTICA_TEST_AGENT_MODE")
    if raw is None or raw == "success":
        return "success"
    return raw


def run_instruction(
    work_dir: Path,
    instruction: AgentSandboxInstruction,
    *,
    mode: str,
) -> int:
    """Execute the requested agent mode for a validated instruction."""
    target = _resolve_contained_path(work_dir, instruction.path)
    if mode == "timeout":
        emit_step_start()
        while True:
            time.sleep(3600)
    if mode == "wrong-edit":
        run_id = extract_run_id(instruction.before)
        target.write_text(f"unexpected:{run_id}\n", encoding="utf-8")
        emit_success_stream()
        return 0
    atomic_replace_file(target, instruction.after)
    emit_success_stream()
    return 0


def print_version() -> None:
    """Write the semver line expected by multica daemon version detection."""
    sys.stdout.write(f"{_FAKE_VERSION}\n")
    sys.stdout.flush()


def is_version_probe(argv: list[str]) -> bool:
    """Return whether argv is the daemon's ``--version`` probe."""
    return len(argv) == 2 and argv[1] == "--version"


def main() -> int:
    """Run the deterministic OpenCode-compatible executable."""
    if is_version_probe(sys.argv):
        print_version()
        return 0

    try:
        parsed = parse_canonical_argv(sys.argv)
    except ArgvError:
        return _EXIT_USAGE

    mode = resolve_agent_mode()
    if mode not in _ALLOWED_MODES:
        return _EXIT_USAGE

    if mode == "error":
        emit_error("agent mode error")
        return _EXIT_AGENT_ERROR

    try:
        instruction = parse_and_validate_instruction(parsed.prompt, parsed.work_dir)
    except InstructionError as exc:
        emit_error(str(exc))
        return _EXIT_INSTRUCTION

    return run_instruction(parsed.work_dir, instruction, mode=mode)


if __name__ == "__main__":
    raise SystemExit(main())
