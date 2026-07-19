from __future__ import annotations

import hashlib
import os
import pathlib
import shutil
import tempfile

import msgspec

from . import suggestions as suggestions_module
from .models import (
    CoverageManifest,
    ImpactMap,
    SemanticCLIContract,
    TestSuggestions,
    UpgradeBundle,
    UpstreamContractDiff,
)
from .normalize import canonical_bytes
from .schema import BUNDLE_SCHEMA_VERSION


def build_bundle(
    *,
    candidate_ref: str,
    diff: UpstreamContractDiff,
    impact: ImpactMap,
    manifest: CoverageManifest,
    generated_at: str,
) -> UpgradeBundle:
    suggestions = suggestions_module.generate_manifest_suggestions(diff, manifest)
    tasks = suggestions_module.generate_implementation_tasks(diff)
    test_suggestions = _test_suggestions(diff, impact)
    changelog = suggestions_module.generate_changelog_fragment(diff)
    summary = _summary(diff, impact, suggestions)
    return UpgradeBundle(
        schema_version=BUNDLE_SCHEMA_VERSION,
        summary=summary,
        upstream_diff=diff,
        impact_map=impact,
        candidate_contract_ref=candidate_ref,
        manifest_suggestions=suggestions,
        implementation_tasks=tasks,
        test_suggestions=test_suggestions,
        changelog_fragment=changelog,
        generated_at=generated_at,
    )


def _test_suggestions(
    diff: UpstreamContractDiff,
    impact: ImpactMap,
) -> TestSuggestions:
    argv_targets = tuple(
        sorted(
            {
                " ".join(entry.command_path)
                for entry in impact.entries
                if entry.severity in ("breaking", "potentially_breaking", "additive")
            }
        )
    )
    output_fixture_targets = tuple(
        " ".join(entry.command_path)
        for entry in impact.entries
        if entry.change_kind.startswith("output_")
    )
    return TestSuggestions(
        argv_targets=argv_targets,
        output_fixture_targets=output_fixture_targets,
    )


def _summary(
    diff: UpstreamContractDiff,
    impact: ImpactMap,
    suggestions: tuple[object, ...],
) -> str:
    return (
        f"Upstream diff: {len(diff.changes)} change(s); "
        f"impact: {len(impact.entries)} entry(ies); "
        f"manifest suggestions: {len(suggestions)} (incomplete until maintainer decisions)."
    )


def write_canonical_json(path: pathlib.Path, struct: object) -> None:
    payload: dict[str, object] = msgspec.to_builtins(struct)
    path.write_bytes(canonical_bytes(payload) + b"\n")


def write_bundle(
    bundle: UpgradeBundle,
    *,
    output_dir: pathlib.Path,
    candidate_contract: SemanticCLIContract,
    write: bool = True,
) -> pathlib.Path:
    if not write:
        return output_dir
    parent = output_dir.parent
    parent.mkdir(parents=True, exist_ok=True)
    staging = pathlib.Path(tempfile.mkdtemp(prefix=f"{output_dir.name}.new.", dir=str(parent)))
    try:
        _write_bundle_contents(staging, bundle, candidate_contract)
        if output_dir.exists():
            previous = pathlib.Path(
                tempfile.mkdtemp(prefix=f"{output_dir.name}.prev.", dir=str(parent))
            )
            os.replace(output_dir, previous)
            try:
                os.replace(staging, output_dir)
            except Exception:
                if output_dir.exists():
                    shutil.rmtree(output_dir, ignore_errors=True)
                os.replace(previous, output_dir)
                raise
            shutil.rmtree(previous, ignore_errors=True)
        else:
            os.replace(staging, output_dir)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return output_dir


def _write_bundle_contents(
    output_dir: pathlib.Path,
    bundle: UpgradeBundle,
    candidate_contract: SemanticCLIContract,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.md").write_text(bundle.summary + "\n", encoding="utf-8")
    write_canonical_json(output_dir / "upstream-diff.json", bundle.upstream_diff)
    write_canonical_json(output_dir / "impact-map.json", bundle.impact_map)
    write_canonical_json(output_dir / "candidate-contract.json", candidate_contract)
    write_canonical_json(
        output_dir / "manifest-suggestions.json", list(bundle.manifest_suggestions)
    )
    (output_dir / "implementation-tasks.md").write_text(
        "\n".join(bundle.implementation_tasks) + "\n", encoding="utf-8"
    )
    (output_dir / "changelog-fragment.md").write_text(bundle.changelog_fragment, encoding="utf-8")
    test_dir = output_dir / "test-suggestions"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "argv-contracts.patch").write_text(
        _argv_patch(bundle.test_suggestions.argv_targets),
        encoding="utf-8",
    )
    write_canonical_json(
        test_dir / "output-fixtures.todo.json",
        list(bundle.test_suggestions.output_fixture_targets),
    )
    digest_struct: UpgradeBundle = msgspec.structs.replace(bundle, bundle_hash="", generated_at="")
    digest_payload: dict[str, object] = msgspec.to_builtins(digest_struct)
    digest = hashlib.sha256(canonical_bytes(digest_payload)).hexdigest()
    (output_dir / "bundle.hash").write_text(f"sha256:{digest}\n", encoding="utf-8")


def _argv_patch(targets: tuple[str, ...]) -> str:
    if not targets:
        return "# No argv contract test suggestions.\n"
    lines = ["# Suggested argv contract tests:", ""]
    for target in targets:
        lines.append(f"# - {target}")
    return "\n".join(lines) + "\n"
