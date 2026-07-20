#!/usr/bin/env python3
"""Remove live test processes and Docker resources matching the run prefix."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import signal
import subprocess
import sys
from typing import cast

RUN_PREFIX_ROOT = "multica-py-live-"
RUN_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
PREFIX_PATTERN = re.compile(rf"^{re.escape(RUN_PREFIX_ROOT)}[0-9a-f]{{32}}$")


def _compose_prefix(run_id: str) -> str:
    return f"{RUN_PREFIX_ROOT}{run_id}"


def _resolve_prefix(
    run_id: str | None,
    prefix: str | None,
    *,
    allow_all: bool,
) -> str:
    if run_id:
        if not RUN_ID_PATTERN.match(run_id):
            msg = "run_id must be 32 lowercase hex characters"
            raise SystemExit(msg)
        return _compose_prefix(run_id)
    if prefix:
        if not PREFIX_PATTERN.match(prefix):
            msg = "prefix must match multica-py-live-<32 hex chars>"
            raise SystemExit(msg)
        return prefix
    if allow_all:
        return RUN_PREFIX_ROOT
    msg = "run_id or validated prefix required; use --all for broad cleanup"
    raise SystemExit(msg)


def _docker_lines(command: list[str]) -> list[str]:
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def _remove_docker_containers(prefix: str) -> tuple[list[str], list[str]]:
    filters = [f"name={prefix}"]
    if PREFIX_PATTERN.match(prefix):
        filters.append(f"label=com.docker.compose.project={prefix}")
    names: list[str] = []
    for docker_filter in filters:
        names.extend(
            _docker_lines(
                [
                    "docker",
                    "ps",
                    "-a",
                    "--filter",
                    docker_filter,
                    "--format",
                    "{{.Names}}",
                ]
            )
        )
    unique_names = sorted(set(names))
    removed: list[str] = []
    errors: list[str] = []
    for name in unique_names:
        completed = subprocess.run(
            ["docker", "rm", "-f", name],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if completed.returncode == 0:
            removed.append(name)
        else:
            errors.append(
                f"container {name}: {completed.stderr.strip() or completed.stdout.strip()}"
            )
    return removed, errors


def _remove_docker_networks(prefix: str) -> tuple[list[str], list[str]]:
    names = _docker_lines(
        ["docker", "network", "ls", "--filter", f"name={prefix}", "--format", "{{.Name}}"]
    )
    removed: list[str] = []
    errors: list[str] = []
    for name in names:
        completed = subprocess.run(
            ["docker", "network", "rm", name],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if completed.returncode == 0:
            removed.append(name)
        else:
            errors.append(f"network {name}: {completed.stderr.strip() or completed.stdout.strip()}")
    return removed, errors


def _remove_docker_volumes(prefix: str) -> tuple[list[str], list[str]]:
    names = _docker_lines(
        ["docker", "volume", "ls", "--filter", f"name={prefix}", "--format", "{{.Name}}"]
    )
    removed: list[str] = []
    errors: list[str] = []
    for name in names:
        completed = subprocess.run(
            ["docker", "volume", "rm", name],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if completed.returncode == 0:
            removed.append(name)
        else:
            errors.append(f"volume {name}: {completed.stderr.strip() or completed.stdout.strip()}")
    return removed, errors


def _docker_container_pids(compose_project: str) -> list[int]:
    container_ids = _docker_lines(
        [
            "docker",
            "ps",
            "-a",
            "--filter",
            f"label=com.docker.compose.project={compose_project}",
            "--format",
            "{{.ID}}",
        ]
    )
    pids: list[int] = []
    for container_id in container_ids:
        completed = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Pid}}", container_id],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if completed.returncode != 0 or not completed.stdout.strip().isdigit():
            continue
        pid = int(completed.stdout.strip())
        if pid > 0:
            pids.append(pid)
    return pids


def _terminate_processes(prefix: str) -> tuple[list[int], list[str]]:
    if prefix == RUN_PREFIX_ROOT:
        return [], []
    if not PREFIX_PATTERN.match(prefix):
        return [], []
    own_pid = os.getpid()
    candidate_pids = set(_docker_container_pids(prefix))
    completed = subprocess.run(
        ["pgrep", "-f", prefix],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if completed.returncode == 0:
        for line in completed.stdout.splitlines():
            if not line.strip().isdigit():
                continue
            candidate_pids.add(int(line.strip()))
    candidate_pids.discard(own_pid)
    terminated: list[int] = []
    errors: list[str] = []
    for pid in sorted(candidate_pids):
        try:
            os.kill(pid, signal.SIGTERM)
            terminated.append(pid)
        except OSError as exc:
            errors.append(f"process {pid}: {exc}")
    return terminated, errors


def cleanup_live_resources(
    *,
    run_id: str | None = None,
    prefix: str | None = None,
    allow_all: bool = False,
) -> dict[str, object]:
    """Remove Docker resources and processes matching a live run prefix.

    Args:
        run_id: Optional 32-character lowercase hex run identifier.
        prefix: Optional explicit prefix matching ``multica-py-live-<run_id>``.
        allow_all: When true, allow cleanup of all ``multica-py-live-*`` resources.

    Returns:
        Machine-readable cleanup audit payload.
    """
    resolved_prefix = _resolve_prefix(run_id, prefix, allow_all=allow_all)
    containers, container_errors = _remove_docker_containers(resolved_prefix)
    networks, network_errors = _remove_docker_networks(resolved_prefix)
    volumes, volume_errors = _remove_docker_volumes(resolved_prefix)
    processes, process_errors = _terminate_processes(resolved_prefix)
    errors = container_errors + network_errors + volume_errors + process_errors
    return {
        "prefix": resolved_prefix,
        "containers_removed": containers,
        "networks_removed": networks,
        "volumes_removed": volumes,
        "processes_terminated": processes,
        "errors": errors,
    }


def write_audit(audit_path: pathlib.Path, payload: dict[str, object]) -> None:
    """Write cleanup audit JSON atomically."""
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    """Build the cleanup script argument parser."""
    parser = argparse.ArgumentParser(
        description="Remove live test Docker resources and processes for a run prefix.",
    )
    parser.add_argument("--run-id", help="32-character lowercase hex live run identifier")
    parser.add_argument(
        "--prefix",
        help="Explicit live run prefix matching multica-py-live-<32 hex chars>",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Clean all multica-py-live-* resources (requires explicit opt-in)",
    )
    parser.add_argument(
        "--audit",
        type=pathlib.Path,
        help="Write machine-readable cleanup audit JSON to this path",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run external live resource cleanup."""
    args = build_parser().parse_args(argv)
    run_id = cast("str | None", args.run_id)
    prefix = cast("str | None", args.prefix)
    allow_all = bool(args.all)
    audit_path = cast("pathlib.Path | None", args.audit)
    payload = cleanup_live_resources(run_id=run_id, prefix=prefix, allow_all=allow_all)
    if audit_path is not None:
        write_audit(audit_path, payload)
    if payload["errors"]:
        print(json.dumps(payload, indent=2), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
