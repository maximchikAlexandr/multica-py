"""Unified maintainer CLI for the upstream-contract workflow.

All commands are thin adapters over the upstream_contract modules.
This module never embeds domain behavior itself; it only parses arguments
and delegates.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
from collections.abc import Callable

import msgspec

from multica_py._internal.compat import default_policy, supported_range_text
from multica_py._internal.upstream_contract import (
    coverage,
    files,
    normalize,
    reporting,
    schema,
)
from multica_py._internal.upstream_contract import (
    diff as diff_module,
)
from multica_py._internal.upstream_contract import (
    impact as impact_module,
)
from multica_py._internal.upstream_contract import (
    observer as observer_module,
)
from multica_py._internal.upstream_contract import (
    promotion as promotion_module,
)
from multica_py._internal.upstream_contract import (
    provenance as provenance_module,
)
from multica_py._internal.upstream_contract import (
    state as state_module,
)
from multica_py._internal.upstream_contract import (
    suggestions as suggestions_module,
)
from multica_py._internal.upstream_contract import (
    upgrade as upgrade_module,
)
from multica_py._internal.upstream_contract.collectors import (
    binary as binary_collector,
)
from multica_py._internal.upstream_contract.models import (
    BinaryRef,
    CandidateBaseline,
    CoverageManifest,
    CoverageReport,
    ReportFailure,
    SemanticCLIContract,
    UpstreamContractDiff,
    UpstreamState,
)
from multica_py._internal.upstream_contract.paths import (
    CANDIDATE_CONTRACT_REL,
    COVERAGE_REL,
    STATE_REL,
    SUPPORTED_CONTRACT_REL,
)

ROOT = pathlib.Path(__file__).resolve().parents[4]
_TAG_PATTERN = re.compile(r"^[A-Za-z0-9._/-]+$")


def _arg(args: argparse.Namespace, name: str) -> str:
    value: object = getattr(args, name)
    if not isinstance(value, str):
        raise TypeError(f"arg {name} must be a string, got {type(value).__name__}")
    return value


def _arg_opt(args: argparse.Namespace, name: str) -> str | None:
    value: object = getattr(args, name, None)
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"arg {name} must be a string, got {type(value).__name__}")
    return value


def _flag(args: argparse.Namespace, name: str) -> bool:
    value: object = getattr(args, name, False)
    return bool(value)


def _exit_code_for(report: CoverageReport) -> int:
    status = report.status
    if status == "clean":
        return reporting.EXIT_CLEAN
    if status == "gaps":
        return reporting.EXIT_COVERAGE_GAP
    if status == "invalid":
        return reporting.EXIT_INVALID_ARTIFACT
    if status == "collection-failed":
        return reporting.EXIT_COLLECTOR_FAILURE
    if status == "mismatch":
        return reporting.EXIT_SOURCE_MISMATCH
    if status == "unresolved-breaking":
        return reporting.EXIT_UNRESOLVED_BREAKING
    return reporting.EXIT_INVALID_ARTIFACT


def _report_human(report: CoverageReport) -> str:
    return reporting.format_human_summary(report)


def _default_human(payload: object) -> str:
    if isinstance(payload, CoverageReport):
        return _report_human(payload)
    if isinstance(payload, UpstreamContractDiff):
        lines = [f"Upstream diff: {len(payload.changes)} change(s)"]
        for change in payload.changes:
            lines.append(f"  [{change.severity}] {change.kind}: {' '.join(change.command_path)}")
        return "\n".join(lines) + "\n"
    fallback: dict[str, object] = msgspec.to_builtins(payload)
    return json.dumps(fallback, indent=2, sort_keys=True) + "\n"


def _skip_writes(args: argparse.Namespace) -> bool:
    return not files.writing_ok(
        check=_flag(args, "check"),
        dry_run=_flag(args, "dry_run"),
        output=_arg_opt(args, "output"),
    )


def _write(
    args: argparse.Namespace,
    payload: object,
    *,
    human_fn: Callable[[object], str] | None = None,
) -> None:
    output_path = _arg_opt(args, "output")
    if _arg(args, "format") == "json":
        builtin: object = msgspec.to_builtins(payload)
        text = json.dumps(builtin, indent=2, sort_keys=True) + "\n"
    else:
        text = (human_fn or _default_human)(payload)
    if output_path:
        if files.writing_ok(
            check=_flag(args, "check"),
            dry_run=_flag(args, "dry_run"),
            output=output_path,
        ):
            pathlib.Path(output_path).write_text(text, encoding="utf-8")
    elif not _flag(args, "check"):
        sys.stdout.write(text)


def _emit(
    args: argparse.Namespace,
    report: CoverageReport,
    *,
    human_fn: Callable[[object], str] | None = None,
) -> int:
    _write(args, report, human_fn=human_fn or _default_human)
    return _exit_code_for(report)


def _resolve_supported_path(args: argparse.Namespace) -> pathlib.Path:
    repo_root = pathlib.Path(_arg(args, "repo_root"))
    supported_path = pathlib.Path(_arg(args, "supported"))
    if not supported_path.is_absolute():
        supported_path = repo_root / supported_path
    return supported_path


def _collect_contract_ref(
    repo_root: pathlib.Path,
    output: pathlib.Path,
) -> str:
    resolved_root = repo_root.resolve()
    resolved_output = output.resolve()
    if resolved_output.is_relative_to(resolved_root):
        return str(resolved_output.relative_to(resolved_root))
    return CANDIDATE_CONTRACT_REL


def _persist_collect(
    args: argparse.Namespace,
    repo_root: pathlib.Path,
    output: pathlib.Path,
    contract: SemanticCLIContract,
    contract_bytes: bytes,
) -> None:
    state_path = repo_root / STATE_REL
    state = state_module.load_state(state_path, repo_root=repo_root)
    contract_ref = _collect_contract_ref(repo_root, output)
    new_state = state_module.set_candidate(
        state,
        CandidateBaseline(
            version=_arg(args, "version"),
            tag=_arg(args, "tag"),
            commit=_arg(args, "commit"),
            semantic_hash=contract.artifact.semantic_hash,
            contract_ref=contract_ref,
            trust_level=contract.artifact.trust_level,
            unresolved_items=coverage.collect_contract_review_items(contract),
        ),
    )
    state_builtins: dict[str, object] = msgspec.to_builtins(new_state)
    state_bytes = normalize.canonical_bytes(state_builtins) + b"\n"
    canonical_path = repo_root / CANDIDATE_CONTRACT_REL
    files.atomic_write_files({canonical_path: contract_bytes, state_path: state_bytes})
    if output.resolve() != canonical_path.resolve():
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(contract_bytes)


def _load_supported_contract(
    state: UpstreamState,
    repo_root: pathlib.Path,
) -> SemanticCLIContract:
    if state.supported is None:
        raise FileNotFoundError("state has no supported baseline")
    path = repo_root / state.supported.contract_ref
    if not path.is_file():
        raise FileNotFoundError(f"supported contract missing: {path}")
    return schema.decode_contract(path)


def _require_coverage_manifest(repo_root: pathlib.Path) -> CoverageManifest:
    path = repo_root / COVERAGE_REL
    if not path.is_file():
        raise FileNotFoundError(f"coverage manifest missing: {path}")
    return schema.decode_coverage(path)


def _invalid_report(code: str, message: str) -> CoverageReport:
    report = reporting.empty_report(status="invalid")
    return reporting.add_failure(
        report,
        ReportFailure(code=code, message=message, severity="invalid"),
    )


def cmd_check(args: argparse.Namespace) -> int:
    repo_root = pathlib.Path(_arg(args, "repo_root"))
    state_path = repo_root / STATE_REL
    try:
        state = state_module.load_state(state_path, repo_root=repo_root)
    except (schema.SchemaError, msgspec.DecodeError) as exc:
        return _emit(args, _invalid_report("INVALID_ARTIFACT", f"failed to load state: {exc}"))
    except provenance_module.ProvenanceError as exc:
        return _emit(args, _invalid_report("INVALID_ARTIFACT", f"invalid state: {exc}"))
    try:
        contract = _load_supported_contract(state, repo_root)
    except (schema.SchemaError, msgspec.DecodeError, FileNotFoundError) as exc:
        return _emit(
            args,
            _invalid_report("INVALID_ARTIFACT", f"failed to load supported contract: {exc}"),
        )
    try:
        manifest = _require_coverage_manifest(repo_root)
    except (schema.SchemaError, msgspec.DecodeError, FileNotFoundError) as exc:
        return _emit(
            args,
            _invalid_report("INVALID_ARTIFACT", f"failed to load coverage manifest: {exc}"),
        )
    diff = None
    if _flag(args, "with_candidate"):
        if state.candidate is None:
            return _emit(
                args,
                _invalid_report("INVALID_CANDIDATE", "no candidate present in state"),
            )
        candidate_path = repo_root / state.candidate.contract_ref
        if not candidate_path.is_file():
            return _emit(
                args,
                _invalid_report(
                    "INVALID_CANDIDATE",
                    f"candidate contract missing: {candidate_path}",
                ),
            )
        try:
            candidate_contract = schema.decode_contract(candidate_path)
        except (schema.SchemaError, msgspec.DecodeError) as exc:
            return _emit(
                args,
                _invalid_report("INVALID_CANDIDATE", f"failed to load candidate contract: {exc}"),
            )
        diff = diff_module.diff_contracts(contract, candidate_contract)
        diff = diff_module.resolve_affected_operations(
            diff, coverage.build_bindings_index(manifest)
        )
    report = coverage.build_coverage_report(
        contract=contract,
        manifest=manifest,
        diff=diff,
        state=state,
        repo_root=repo_root,
    )
    return _emit(args, report, human_fn=_default_human)


def cmd_collect(args: argparse.Namespace) -> int:
    repo_root = pathlib.Path(_arg(args, "repo_root"))
    binary = pathlib.Path(_arg(args, "binary"))
    if not binary.exists():
        return reporting.EXIT_COLLECTOR_FAILURE
    local_manual = _flag(args, "local_manual")
    binary_ref = BinaryRef(
        asset_name=_arg(args, "asset_name"),
        sha256=_arg(args, "sha256"),
        os=_arg(args, "os"),
        arch=_arg(args, "arch"),
        version_output=_arg(args, "version_output"),
    )
    release_asset_raw = _arg_opt(args, "release_asset")
    release_asset = pathlib.Path(release_asset_raw) if release_asset_raw else None
    try:
        contract = binary_collector.orchestrate_collect(
            binary,
            release_asset=release_asset,
            version=_arg(args, "version"),
            tag=_arg(args, "tag"),
            commit=_arg(args, "commit"),
            binary_ref=binary_ref,
            local_manual=local_manual,
        )
    except binary_collector.CollectorError as exc:
        if exc.code == "CONTRACT_SOURCE_MISMATCH":
            return reporting.EXIT_SOURCE_MISMATCH
        if exc.code == "CHECKSUM_MISMATCH":
            return reporting.EXIT_INVALID_ARTIFACT
        if exc.code in ("COLLECTOR_TIMEOUT", "COLLECTOR_INCOMPLETE", "COLLECTOR_NONZERO"):
            return reporting.EXIT_COLLECTOR_FAILURE
        if exc.code == "INVALID_COMMIT":
            return reporting.EXIT_INVALID_ARTIFACT
        return reporting.EXIT_COLLECTOR_FAILURE
    output = pathlib.Path(_arg(args, "output"))
    contract_payload: dict[str, object] = msgspec.to_builtins(contract)
    contract_bytes = normalize.canonical_bytes(contract_payload) + b"\n"
    if files.writing_ok(check=_flag(args, "check"), dry_run=_flag(args, "dry_run")):
        try:
            _persist_collect(args, repo_root, output, contract, contract_bytes)
        except provenance_module.ProvenanceError as exc:
            sys.stderr.write(f"collect refused: {exc}\n")
            return reporting.EXIT_INVALID_ARTIFACT
    if _flag(args, "dry_run") or _flag(args, "check"):
        sys.stdout.write(
            f"would write {output} (semantic_hash={contract.artifact.semantic_hash})\n"
        )
    else:
        sys.stdout.write(f"wrote {output} (semantic_hash={contract.artifact.semantic_hash})\n")
    return reporting.EXIT_CLEAN


def cmd_diff(args: argparse.Namespace) -> int:
    repo_root = pathlib.Path(_arg(args, "repo_root"))
    try:
        before = schema.decode_contract(pathlib.Path(_arg(args, "from_path")))
        after = schema.decode_contract(pathlib.Path(_arg(args, "to_path")))
    except (schema.SchemaError, msgspec.DecodeError) as exc:
        sys.stderr.write(f"failed to decode contract: {exc}\n")
        return reporting.EXIT_INVALID_ARTIFACT
    diff = diff_module.diff_contracts(before, after)
    try:
        manifest = _require_coverage_manifest(repo_root)
    except (schema.SchemaError, msgspec.DecodeError, FileNotFoundError) as exc:
        sys.stderr.write(f"failed to load coverage manifest: {exc}\n")
        return reporting.EXIT_INVALID_ARTIFACT
    diff = diff_module.resolve_affected_operations(diff, coverage.build_bindings_index(manifest))
    _write(args, diff, human_fn=_default_human)
    return reporting.exit_code_for_diff_severity(diff)


def cmd_prepare_upgrade(args: argparse.Namespace) -> int:
    supported_path = _resolve_supported_path(args)
    if not supported_path.exists():
        sys.stderr.write(f"supported contract missing: {supported_path}\n")
        return reporting.EXIT_INVALID_ARTIFACT
    try:
        candidate = schema.decode_contract(pathlib.Path(_arg(args, "candidate")))
        supported = schema.decode_contract(supported_path)
    except (schema.SchemaError, msgspec.DecodeError) as exc:
        sys.stderr.write(f"failed to decode contract: {exc}\n")
        return reporting.EXIT_INVALID_ARTIFACT
    repo_root = pathlib.Path(_arg(args, "repo_root"))
    try:
        manifest = _require_coverage_manifest(repo_root)
    except (schema.SchemaError, msgspec.DecodeError, FileNotFoundError) as exc:
        sys.stderr.write(f"failed to load coverage manifest: {exc}\n")
        return reporting.EXIT_INVALID_ARTIFACT
    diff = diff_module.diff_contracts(supported, candidate)
    diff = diff_module.resolve_affected_operations(diff, coverage.build_bindings_index(manifest))
    impact = impact_module.build_impact(diff, manifest)
    bundle = upgrade_module.build_bundle(
        candidate_ref=_arg(args, "candidate"),
        diff=diff,
        impact=impact,
        manifest=manifest,
        generated_at=provenance_module.now_iso(),
    )
    out_dir = pathlib.Path(_arg(args, "output_dir"))
    exit_code = reporting.exit_code_for_diff_severity(diff)
    if files.writing_ok(check=_flag(args, "check"), dry_run=_flag(args, "dry_run")):
        upgrade_module.write_bundle(bundle, output_dir=out_dir, candidate_contract=candidate)
        sys.stdout.write(f"wrote upgrade bundle to {out_dir}\n")
    else:
        sys.stdout.write(f"would write upgrade bundle to {out_dir}\n")
    return exit_code


def cmd_apply_manifest_suggestions(args: argparse.Namespace) -> int:
    repo_root = pathlib.Path(_arg(args, "repo_root"))
    manifest_path = repo_root / COVERAGE_REL
    try:
        manifest = _require_coverage_manifest(repo_root)
    except (schema.SchemaError, msgspec.DecodeError, FileNotFoundError) as exc:
        sys.stderr.write(f"failed to load coverage manifest: {exc}\n")
        return reporting.EXIT_INVALID_ARTIFACT
    diff_path = pathlib.Path(_arg(args, "bundle")) / "upstream-diff.json"
    try:
        diff = schema.decode_diff(diff_path)
    except (schema.SchemaError, msgspec.DecodeError) as exc:
        sys.stderr.write(f"failed to decode diff: {exc}\n")
        return reporting.EXIT_INVALID_ARTIFACT
    suggestions = suggestions_module.generate_manifest_suggestions(diff, manifest)
    new_manifest = suggestions_module.apply_manifest_suggestions(manifest, suggestions)
    new_manifest_payload: dict[str, object] = msgspec.to_builtins(new_manifest)
    if files.writing_ok(check=_flag(args, "check"), dry_run=_flag(args, "dry_run")):
        files.atomic_write_bytes(
            manifest_path, normalize.canonical_bytes(new_manifest_payload) + b"\n"
        )
    sys.stdout.write(f"applied {len(suggestions)} suggestion(s)\n")
    return reporting.EXIT_CLEAN


def _state_path(args: argparse.Namespace) -> pathlib.Path:
    return pathlib.Path(_arg(args, "repo_root")) / STATE_REL


def _write_state(args: argparse.Namespace, new_state: object) -> None:
    if _skip_writes(args):
        return
    payload: dict[str, object] = msgspec.to_builtins(new_state)
    files.atomic_write_bytes(_state_path(args), normalize.canonical_bytes(payload) + b"\n")


def _observe_value(args: argparse.Namespace, arg_name: str, env_name: str) -> str:
    cli_value = _arg_opt(args, arg_name)
    if cli_value is not None:
        return cli_value
    env_value = os.environ.get(env_name, "")
    if not env_value:
        raise ValueError(f"missing {arg_name}: provide CLI flag or {env_name} env var")
    return env_value


def _validate_release_tag(tag: str) -> None:
    if not _TAG_PATTERN.match(tag):
        raise ValueError(f"release tag contains invalid characters: {tag!r}")


def cmd_observe(args: argparse.Namespace) -> int:
    repo_root = pathlib.Path(_arg(args, "repo_root"))
    state_path = _state_path(args)
    try:
        release_id = _observe_value(args, "release_id", "RELEASE_ID")
        version = _observe_value(args, "version", "RELEASE_VERSION")
        tag = _observe_value(args, "tag", "RELEASE_TAG")
        _validate_release_tag(tag)
    except ValueError as exc:
        sys.stderr.write(f"invalid observation: {exc}\n")
        return reporting.EXIT_INVALID_ARTIFACT
    state = state_module.load_state(state_path, repo_root=repo_root)
    observation = observer_module.new_observation(
        release_id=release_id,
        version=version,
        tag=tag,
    )
    new_state = observer_module.merge_observation(state, observation)
    _write_state(args, new_state)
    sys.stdout.write(f"observed release {release_id}\n")
    return reporting.EXIT_CLEAN


def cmd_promote(args: argparse.Namespace) -> int:
    repo_root = pathlib.Path(_arg(args, "repo_root"))
    state_path = _state_path(args)
    try:
        state = state_module.load_state(state_path, repo_root=repo_root)
    except (schema.SchemaError, msgspec.DecodeError) as exc:
        sys.stderr.write(f"failed to load state: {exc}\n")
        return reporting.EXIT_INVALID_ARTIFACT
    candidate = state.candidate
    if candidate is None:
        sys.stderr.write("no candidate present in state\n")
        return reporting.EXIT_INVALID_ARTIFACT
    try:
        decision = schema.decode_promotion(pathlib.Path(_arg(args, "decision")))
    except (schema.SchemaError, msgspec.DecodeError) as exc:
        sys.stderr.write(f"failed to decode promotion decision: {exc}\n")
        return reporting.EXIT_INVALID_ARTIFACT
    try:
        candidate_contract = promotion_module.load_candidate_contract(repo_root, candidate)
    except (schema.SchemaError, msgspec.DecodeError, FileNotFoundError) as exc:
        sys.stderr.write(f"failed to load candidate contract: {exc}\n")
        return reporting.EXIT_INVALID_ARTIFACT
    try:
        new_state = promotion_module.apply_promotion(
            state,
            decision,
            candidate,
            candidate_contract=candidate_contract,
        )
    except promotion_module.PromotionError as exc:
        sys.stderr.write(f"promotion refused: {exc}\n")
        if exc.code in ("trust", "hash_mismatch", "version_mismatch"):
            return reporting.EXIT_INVALID_ARTIFACT
        return reporting.EXIT_UNRESOLVED_BREAKING
    except ValueError as exc:
        sys.stderr.write(f"promotion refused: {exc}\n")
        return reporting.EXIT_UNRESOLVED_BREAKING
    if files.writing_ok(check=_flag(args, "check"), dry_run=_flag(args, "dry_run")):
        promotion_module.write_promoted_artifacts(
            repo_root=repo_root,
            new_state=new_state,
            candidate_contract=candidate_contract,
            state_path=state_path,
        )
        sys.stdout.write(f"promoted {candidate.version} as supported\n")
    else:
        sys.stdout.write(f"would promote {candidate.version} as supported\n")
    return reporting.EXIT_CLEAN


def cmd_reject(args: argparse.Namespace) -> int:
    repo_root = pathlib.Path(_arg(args, "repo_root"))
    try:
        state = state_module.load_state(_state_path(args), repo_root=repo_root)
    except (schema.SchemaError, msgspec.DecodeError) as exc:
        sys.stderr.write(f"failed to load state: {exc}\n")
        return reporting.EXIT_INVALID_ARTIFACT
    try:
        decision = schema.decode_promotion(pathlib.Path(_arg(args, "decision")))
    except (schema.SchemaError, msgspec.DecodeError) as exc:
        sys.stderr.write(f"failed to decode promotion decision: {exc}\n")
        return reporting.EXIT_INVALID_ARTIFACT
    new_state = promotion_module.apply_rejection(state, decision)
    _write_state(args, new_state)
    sys.stdout.write("rejected candidate\n")
    return reporting.EXIT_CLEAN


def cmd_compat(args: argparse.Namespace) -> int:
    sdk_version = _arg_opt(args, "sdk_version")
    if sdk_version is not None:
        policy = default_policy(sdk_version)
        print(supported_range_text(policy))
        return reporting.EXIT_CLEAN
    sys.stderr.write("usage: compat --sdk-version X\n")
    return reporting.EXIT_USAGE


def cmd_upgrade(args: argparse.Namespace) -> int:
    repo_root = pathlib.Path(_arg(args, "repo_root"))
    output_dir = pathlib.Path(_arg(args, "output_dir"))
    candidate = output_dir / "candidate.json"
    supported = repo_root / SUPPORTED_CONTRACT_REL
    observe_args = argparse.Namespace(
        repo_root=str(repo_root),
        release_id=_arg(args, "release_id"),
        version=_arg(args, "version"),
        tag=_arg(args, "tag"),
        dry_run=_flag(args, "dry_run"),
        check=_flag(args, "check"),
    )
    observe_code = cmd_observe(observe_args)
    if observe_code != reporting.EXIT_CLEAN:
        return observe_code
    collect_args = argparse.Namespace(
        repo_root=str(repo_root),
        binary=_arg(args, "binary"),
        version=_arg(args, "version"),
        tag=_arg(args, "tag"),
        commit=_arg(args, "commit"),
        asset_name=_arg(args, "asset_name"),
        sha256=_arg(args, "sha256"),
        os=_arg(args, "os"),
        arch=_arg(args, "arch"),
        version_output=_arg(args, "version_output"),
        output=str(candidate),
        release_asset=_arg_opt(args, "release_asset"),
        dry_run=_flag(args, "dry_run"),
        check=_flag(args, "check"),
        local_manual=_flag(args, "local_manual"),
    )
    collect_code = cmd_collect(collect_args)
    if collect_code != reporting.EXIT_CLEAN:
        return collect_code
    if not supported.is_file():
        sys.stderr.write(f"supported contract missing: {supported}\n")
        return reporting.EXIT_INVALID_ARTIFACT
    diff_args = argparse.Namespace(
        repo_root=str(repo_root),
        from_path=str(supported),
        to_path=str(candidate),
        format="human",
        output=None,
    )
    diff_code = cmd_diff(diff_args)
    if diff_code not in (reporting.EXIT_CLEAN, reporting.EXIT_UNRESOLVED_BREAKING):
        return diff_code
    prep_args = argparse.Namespace(
        repo_root=str(repo_root),
        candidate=str(candidate),
        output_dir=str(output_dir),
        supported=SUPPORTED_CONTRACT_REL,
        dry_run=_flag(args, "dry_run"),
        check=_flag(args, "check"),
    )
    return cmd_prepare_upgrade(prep_args)


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo-root", default=str(ROOT))
    parser = argparse.ArgumentParser(prog="upstream_contract", parents=[common])
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", parents=[common])
    p_check.add_argument("--format", choices=("human", "json"), default="human")
    p_check.add_argument("--output", default=None)
    p_check.add_argument(
        "--with-candidate",
        action="store_true",
        help="include candidate diff and state summaries in the report",
    )
    p_check.add_argument(
        "--check",
        action="store_true",
        help="validate without writing unless --output is set",
    )
    p_check.set_defaults(func=cmd_check)

    p_collect = sub.add_parser("collect", parents=[common])
    p_collect.add_argument("--binary", required=True)
    p_collect.add_argument("--version", required=True)
    p_collect.add_argument("--tag", required=True)
    p_collect.add_argument("--commit", required=True)
    p_collect.add_argument("--asset-name", required=True)
    p_collect.add_argument("--sha256", required=True)
    p_collect.add_argument("--os", required=True)
    p_collect.add_argument("--arch", required=True)
    p_collect.add_argument("--version-output", required=True)
    p_collect.add_argument("--output", required=True)
    p_collect.add_argument("--release-asset", default=None)
    p_collect.add_argument("--dry-run", action="store_true")
    p_collect.add_argument(
        "--local-manual",
        action="store_true",
        help="trust local binary without official checksum verification",
    )
    p_collect.add_argument(
        "--check",
        action="store_true",
        help="validate collection without writing output",
    )
    p_collect.set_defaults(func=cmd_collect)

    p_diff = sub.add_parser("diff", parents=[common])
    p_diff.add_argument("--from", dest="from_path", required=True)
    p_diff.add_argument("--to", dest="to_path", required=True)
    p_diff.add_argument("--format", choices=("human", "json"), default="human")
    p_diff.add_argument("--output", default=None)
    p_diff.set_defaults(func=cmd_diff)

    p_prep = sub.add_parser("prepare-upgrade", parents=[common])
    p_prep.add_argument("--candidate", required=True)
    p_prep.add_argument("--output-dir", required=True)
    p_prep.add_argument(
        "--supported",
        default=SUPPORTED_CONTRACT_REL,
    )
    p_prep.add_argument("--dry-run", action="store_true")
    p_prep.add_argument(
        "--check",
        action="store_true",
        help="validate upgrade bundle without writing output",
    )
    p_prep.set_defaults(func=cmd_prepare_upgrade)

    p_apply = sub.add_parser("apply-manifest-suggestions", parents=[common])
    p_apply.add_argument("--bundle", required=True)
    p_apply.add_argument("--dry-run", action="store_true")
    p_apply.add_argument(
        "--check",
        action="store_true",
        help="validate suggestions without writing manifest",
    )
    p_apply.set_defaults(func=cmd_apply_manifest_suggestions)

    p_obs = sub.add_parser("observe", parents=[common])
    p_obs.add_argument("--release-id", default=None)
    p_obs.add_argument("--version", default=None)
    p_obs.add_argument("--tag", default=None)
    p_obs.add_argument("--dry-run", action="store_true")
    p_obs.set_defaults(func=cmd_observe)

    p_promote = sub.add_parser("promote", parents=[common])
    p_promote.add_argument("--decision", required=True)
    p_promote.add_argument("--dry-run", action="store_true")
    p_promote.add_argument(
        "--check",
        action="store_true",
        help="validate promotion without writing artifacts",
    )
    p_promote.set_defaults(func=cmd_promote)

    p_reject = sub.add_parser("reject", parents=[common])
    p_reject.add_argument("--decision", required=True)
    p_reject.add_argument("--dry-run", action="store_true")
    p_reject.add_argument(
        "--check",
        action="store_true",
        help="validate rejection without writing state",
    )
    p_reject.set_defaults(func=cmd_reject)

    p_compat = sub.add_parser("compat", parents=[common])
    p_compat.add_argument("--sdk-version", default=None)
    p_compat.set_defaults(func=cmd_compat)

    p_upgrade = sub.add_parser("upgrade", parents=[common])
    p_upgrade.add_argument("--tag", required=True)
    p_upgrade.add_argument("--version", required=True)
    p_upgrade.add_argument("--commit", required=True)
    p_upgrade.add_argument("--release-id", required=True)
    p_upgrade.add_argument("--binary", required=True)
    p_upgrade.add_argument("--asset-name", required=True)
    p_upgrade.add_argument("--sha256", required=True)
    p_upgrade.add_argument("--os", required=True)
    p_upgrade.add_argument("--arch", required=True)
    p_upgrade.add_argument("--version-output", required=True)
    p_upgrade.add_argument("--output-dir", required=True)
    p_upgrade.add_argument("--release-asset", default=None)
    p_upgrade.add_argument("--local-manual", action="store_true")
    p_upgrade.add_argument("--dry-run", action="store_true")
    p_upgrade.add_argument(
        "--check",
        action="store_true",
        help="validate upgrade workflow without writing artifacts",
    )
    p_upgrade.set_defaults(func=cmd_upgrade)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    func: object = getattr(args, "func")
    if not callable(func):
        return reporting.EXIT_USAGE
    result: int = func(args)
    return result


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
