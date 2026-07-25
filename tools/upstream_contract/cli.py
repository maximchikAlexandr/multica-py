"""Command-line entrypoint for the four approved-contract operations."""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import subprocess
import sys

from .contract import ContractError, validate_contract
from .evidence import ReleaseIdentity, collect
from .generation import RUNTIME_PATH, check_repository, render_files, write_rendered


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="upstream_contract.py")
    commands = parser.add_subparsers(dest="command", required=True)
    validate_parser = commands.add_parser("validate")
    validate_parser.add_argument("--approved", required=True, type=pathlib.Path)
    validate_parser.add_argument("--source-checkout", type=pathlib.Path)
    collect_parser = commands.add_parser("collect")
    for name in ("source-checkout", "binary", "version-output", "output-dir"):
        collect_parser.add_argument(f"--{name}", required=True, type=pathlib.Path)
    for name in ("tag", "version", "commit", "release-id", "asset-name", "sha256", "os", "arch"):
        collect_parser.add_argument(f"--{name}", required=True)
    render_parser = commands.add_parser("render")
    render_parser.add_argument("--approved", required=True, type=pathlib.Path)
    render_parser.add_argument("--runtime-output", required=True, type=pathlib.Path)
    render_parser.add_argument("--transient-output", required=True, type=pathlib.Path)
    check_parser = commands.add_parser("check")
    check_parser.add_argument("--approved", required=True, type=pathlib.Path)
    return parser


def _source_validate(approved: pathlib.Path, source_checkout: pathlib.Path) -> None:
    catalog = validate_contract(approved)
    checkout_root = source_checkout.resolve()
    if not checkout_root.is_dir():
        raise ContractError(f"source checkout does not exist: {source_checkout}")
    actual = subprocess.run(
        ["git", "-C", str(source_checkout), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if actual != catalog.target.commit:
        raise ContractError("source checkout HEAD does not match approved target commit")
    for source_ref in catalog.source_refs:
        path = (checkout_root / source_ref.path).resolve()
        try:
            path.relative_to(checkout_root)
        except ValueError as exc:
            raise ContractError(
                f"approved source reference escapes source checkout: {source_ref.path}"
            ) from exc
        try:
            blob = subprocess.run(
                [
                    "git",
                    "-C",
                    str(source_checkout),
                    "show",
                    f"{catalog.target.commit}:{source_ref.path}",
                ],
                check=True,
                capture_output=True,
            ).stdout
        except subprocess.CalledProcessError as exc:
            raise ContractError(
                f"approved source reference is missing from target commit: {path}"
            ) from exc
        lines = blob.decode("utf-8", errors="replace").splitlines()
        start = source_ref.line_start
        end = source_ref.line_end
        symbol = source_ref.symbol
        if start < 1 or end < start or end > len(lines):
            raise ContractError(f"source line range is invalid for {path}")
        text = "\n".join(lines[start - 1 : end])
        for part in symbol.split("/"):
            if part not in text:
                raise ContractError(f"source symbol {part!r} not found in {path}:{start}-{end}")


def _require_runtime_output(path: pathlib.Path) -> None:
    expected = (pathlib.Path.cwd() / RUNTIME_PATH).resolve()
    if path.resolve() != expected:
        raise ContractError(f"--runtime-output must be {RUNTIME_PATH}")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate":
            if args.source_checkout is None:
                validate_contract(args.approved)
            else:
                _source_validate(args.approved, args.source_checkout)
            return 0
        if args.command == "collect":
            identity = ReleaseIdentity(
                tag=args.tag,
                version=args.version,
                commit=args.commit,
                release_id=args.release_id,
                asset_name=args.asset_name,
                sha256=args.sha256,
                os=args.os,
                arch=args.arch,
                version_output_sha256=hashlib.sha256(args.version_output.read_bytes()).hexdigest(),
            )
            collect(
                source_checkout=args.source_checkout,
                binary=args.binary,
                identity=identity,
                version_output=args.version_output,
                output_dir=args.output_dir,
            )
            return 0
        if args.command == "render":
            files = render_files(args.approved)
            _require_runtime_output(args.runtime_output)
            write_rendered(files, pathlib.Path.cwd(), args.transient_output)
            return 0
        if args.command == "check":
            try:
                validate_contract(args.approved)
            except ContractError as exc:
                print(str(exc), file=sys.stderr)
                return 2
            check_repository(args.approved, pathlib.Path.cwd())
            return 0
    except (ContractError, OSError, ValueError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 2 if args.command == "validate" else 1
    return 2
