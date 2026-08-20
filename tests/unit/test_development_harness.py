from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
RUN_CHANGE = ROOT / "tools" / "zeroshot" / "run-change"
WORKFLOW = ROOT / "tools" / "zeroshot" / "workflow.json"
SETTINGS = ROOT / ".zeroshot" / "settings.json"


@pytest.mark.parametrize("change", ["../escape", "bad/change", "missing-change"])
def test_run_change_rejects_invalid_or_missing_change(change: str) -> None:
    result = subprocess.run(
        [RUN_CHANGE, "--dry-run", change],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0


def test_run_change_dry_run_validates_with_pinned_cli(tmp_path: Path) -> None:
    zeroshot = tmp_path / "zeroshot"
    zeroshot.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = --version ]; then echo 6.40.0; exit 0; fi\n'
        "if [ \"$1 $2\" = 'config validate' ]; then exit 0; fi\n"
        "exit 99\n",
        encoding="utf-8",
    )
    zeroshot.chmod(0o755)
    openspec = tmp_path / "openspec"
    openspec.write_text('#!/bin/sh\n[ "$1" = validate ]\n', encoding="utf-8")
    openspec.chmod(0o755)
    codex = tmp_path / "codex"
    codex.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    codex.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}{os.pathsep}{env['PATH']}"
    env["ZEROSHOT_BIN"] = str(zeroshot)

    result = subprocess.run(
        [RUN_CHANGE, "--dry-run", "unify-sdk-operation-contracts"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "zeroshot=6.40.0 provider=codex isolation=--worktree input_git_hash=" in result.stdout


def test_worker_continues_before_validation_when_not_ready() -> None:
    workflow = json.loads(WORKFLOW.read_text(encoding="utf-8"))
    worker = next(agent for agent in workflow["agents"] if agent["id"] == "worker")

    assert workflow["defaultProvider"] == "codex"
    assert any(trigger["topic"] == "WORKER_PROGRESS" for trigger in worker["triggers"])
    assert any(
        source["topic"] == "WORKER_PROGRESS" for source in worker["contextStrategy"]["sources"]
    )
    assert "WORKER_PROGRESS" in worker["hooks"]["onComplete"]["logic"]["script"]


def test_repository_settings_pin_delivery_and_command_proof() -> None:
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))

    assert settings["github"]["prBase"] == "main"
    assert settings["worktree"]["baseRef"] == "HEAD"
    assert settings["commandProofs"] == [
        {
            "id": "project-pr",
            "profile": "pr",
            "scope": "repo",
            "description": "Full repository pull-request verification",
            "command": "make pr",
        }
    ]


def test_makefile_owns_repository_verification_commands() -> None:
    expected_commands = {
        "lint": "uv run ruff format --check .\nuv run ruff check .",
        "types": "uv run mypy --namespace-packages --explicit-package-bases -p multica_py",
        "mutation": "NO_COLOR=1 uv run mutmut run",
        "contract": "uv run python scripts/upstream_contract.py check",
        "package": "uv build",
        "live": 'uv run pytest -o addopts="" -q -m live_smoke',
    }

    for target, expected in expected_commands.items():
        result = subprocess.run(
            ["make", "--no-print-directory", "--dry-run", target],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
        assert expected in result.stdout


@pytest.mark.parametrize(
    ("profile", "target"),
    [
        ("lint", "lint"),
        ("types", "types"),
        ("offline", "test"),
        ("mutation", "mutation"),
        ("compat", "compat"),
        ("contract", "contract"),
        ("packaging", "package"),
        ("live", "live"),
        ("pr", "pr"),
    ],
)
def test_verify_delegates_profiles_to_make(profile: str, target: str, tmp_path: Path) -> None:
    make = tmp_path / "make"
    make.write_text('#!/bin/sh\nprintf "%s\\n" "$*"\n', encoding="utf-8")
    make.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}{os.pathsep}{env['PATH']}"

    result = subprocess.run(
        [ROOT / "tools" / "verify", profile],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"--no-print-directory -C {ROOT} {target}"


def test_verify_delegates_targeted_arguments_to_make(tmp_path: Path) -> None:
    make = tmp_path / "make"
    make.write_text('#!/bin/sh\nprintf "%s\\n" "$*"\n', encoding="utf-8")
    make.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}{os.pathsep}{env['PATH']}"

    result = subprocess.run(
        [ROOT / "tools" / "verify", "targeted", "tests/unit/test_client.py", "-x"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == (
        f"--no-print-directory -C {ROOT} targeted PYTEST_ARGS=tests/unit/test_client.py -x"
    )
