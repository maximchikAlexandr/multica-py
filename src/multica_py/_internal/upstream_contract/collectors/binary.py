from __future__ import annotations

import pathlib
import subprocess
import tempfile

import msgspec

from ..models import (
    ArgumentContract,
    ArtifactMeta,
    Baseline,
    BinaryRef,
    CommandContract,
    ExecutionContract,
    FlagContract,
    ObservationMeta,
    OutputContract,
    SemanticCLIContract,
    SourceRef,
)
from ..normalize import semantic_hash
from ..provenance import is_full_commit, now_iso
from . import source as source_collector
from ._raw_payloads import (
    RawArgument,
    RawCommand,
    RawExecution,
    RawExporterPayload,
    RawFlag,
    RawOutput,
    RawSource,
)
from .security import (
    DEFAULT_OUTPUT_LIMIT,
    is_safe_output_size,
    sanitized_environment,
    verify_checksum,
)

COLLECTOR_METHOD_ORDER: tuple[str, ...] = (
    "release-asset",
    "binary-exporter",
    "help-parser",
)

DEFAULT_TIMEOUT_SECONDS = 25


class CollectorError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def orchestrate_collect(
    binary: pathlib.Path,
    *,
    release_asset: pathlib.Path | None,
    version: str,
    tag: str,
    commit: str,
    binary_ref: BinaryRef,
    local_manual: bool = False,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    tmp_dir: pathlib.Path | None = None,
) -> SemanticCLIContract:
    """Collect a candidate contract using the fixed collector method order."""
    errors: list[CollectorError] = []
    contract: SemanticCLIContract | None = None
    if release_asset is not None and release_asset.is_file():
        try:
            contract = collect_from_release_asset(
                release_asset,
                expected_sha256=binary_ref.sha256,
                version=version,
                tag=tag,
                commit=commit,
                asset_name=binary_ref.asset_name,
                os_name=binary_ref.os,
                arch=binary_ref.arch,
                version_output=binary_ref.version_output,
            )
        except CollectorError as exc:
            errors.append(exc)
    if contract is None:
        try:
            contract = collect_from_binary(
                binary,
                version=version,
                tag=tag,
                commit=commit,
                binary_ref=binary_ref,
                timeout_seconds=timeout_seconds,
                tmp_dir=tmp_dir,
                local_manual=local_manual,
            )
        except CollectorError as exc:
            errors.append(exc)
            if not local_manual:
                try:
                    contract = collect_from_help_parser(
                        binary,
                        version=version,
                        tag=tag,
                        commit=commit,
                        asset_name=binary_ref.asset_name,
                        sha256=binary_ref.sha256,
                        os_name=binary_ref.os,
                        arch=binary_ref.arch,
                        version_output=binary_ref.version_output,
                        timeout_seconds=timeout_seconds,
                        tmp_dir=tmp_dir,
                    )
                except CollectorError as help_exc:
                    errors.append(help_exc)
    if contract is None:
        raise (
            errors[-1]
            if errors
            else CollectorError("COLLECTOR_INCOMPLETE", "no collection method succeeded")
        )
    if contract.artifact.collection_method != "help-parser" and not local_manual:
        cross_check_exporter_help(
            binary,
            contract,
            version=version,
            tag=tag,
            commit=commit,
            asset_name=binary_ref.asset_name,
            sha256=binary_ref.sha256,
            os_name=binary_ref.os,
            arch=binary_ref.arch,
            version_output=binary_ref.version_output,
            timeout_seconds=timeout_seconds,
            tmp_dir=tmp_dir,
        )
        contract = _with_verified_trust(contract)
    return contract


def collect_from_binary(
    binary: pathlib.Path,
    *,
    version: str,
    tag: str,
    commit: str,
    binary_ref: BinaryRef,
    collection_method: str = "binary-exporter",
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    generator_name: str = "multica-py-upstream-contract",
    generator_version: str = "0.1.0",
    generator_commit: str = "0" * 40,
    tmp_dir: pathlib.Path | None = None,
    local_manual: bool = False,
) -> SemanticCLIContract:
    """Collect a candidate contract from a real multica binary."""
    if not is_full_commit(commit):
        raise CollectorError("INVALID_COMMIT", f"commit must be 40-character hex, got {commit!r}")
    if collection_method not in COLLECTOR_METHOD_ORDER:
        raise CollectorError(
            "INVALID_METHOD",
            f"collection_method {collection_method!r} is not in {COLLECTOR_METHOD_ORDER}",
        )
    artifact_tmp = tmp_dir or pathlib.Path(tempfile.mkdtemp(prefix="multica-collect-"))
    env = sanitized_environment()
    env["TMPDIR"] = str(artifact_tmp)
    env["HOME"] = str(artifact_tmp)
    if not local_manual and not verify_checksum(binary, binary_ref.sha256):
        raise CollectorError(
            "CHECKSUM_MISMATCH", f"binary checksum does not match {binary_ref.sha256}"
        )
    try:
        result = subprocess.run(
            [str(binary), "__contract", "--format", "json"],
            capture_output=True,
            env=env,
            cwd=artifact_tmp,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise CollectorError("COLLECTOR_TIMEOUT", f"timeout after {timeout_seconds}s") from exc
    if result.returncode != 0:
        raise CollectorError("COLLECTOR_NONZERO", f"exporter exited {result.returncode}")
    _assert_safe_stream_sizes(result.stdout, result.stderr, label="exporter")
    try:
        payload = msgspec.json.decode(result.stdout, type=RawExporterPayload)
    except msgspec.DecodeError as exc:
        raise CollectorError("COLLECTOR_INVALID_JSON", str(exc)) from exc
    commands = _commands_from_exporter(payload)
    trust_level = (
        "local-manual"
        if local_manual
        else _trust_level_for(collection_method, has_source_cross_check=False)
    )
    artifact = ArtifactMeta(
        semantic_hash="",
        generator_name=generator_name,
        generator_version=generator_version,
        generator_commit=generator_commit,
        collection_method=collection_method,
        trust_level=trust_level,
    )
    baseline = Baseline(state="candidate", version=version, tag=tag, commit=commit)
    observation = ObservationMeta(generated_at=now_iso())
    contract = SemanticCLIContract(
        schema_version=2,
        baseline=baseline,
        artifact=artifact,
        binary=binary_ref,
        commands=commands,
        observation=observation,
    )
    return _with_hash(contract)


def collect_from_help_parser(
    binary: pathlib.Path,
    *,
    version: str,
    tag: str,
    commit: str,
    asset_name: str,
    sha256: str,
    os_name: str,
    arch: str,
    version_output: str,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    tmp_dir: pathlib.Path | None = None,
) -> SemanticCLIContract:
    """Help-parser fallback. Always degraded; never promotable without cross-check."""
    if not is_full_commit(commit):
        raise CollectorError("INVALID_COMMIT", f"commit must be 40-character hex, got {commit!r}")
    artifact_tmp = tmp_dir or pathlib.Path(tempfile.mkdtemp(prefix="multica-help-"))
    env = sanitized_environment()
    env["TMPDIR"] = str(artifact_tmp)
    env["HOME"] = str(artifact_tmp)
    if not verify_checksum(binary, sha256):
        raise CollectorError("CHECKSUM_MISMATCH", f"binary checksum does not match {sha256}")
    try:
        result = subprocess.run(
            [str(binary), "--help"],
            capture_output=True,
            env=env,
            cwd=artifact_tmp,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise CollectorError("COLLECTOR_TIMEOUT", f"timeout after {timeout_seconds}s") from exc
    if result.returncode not in (0, 2):
        raise CollectorError("COLLECTOR_NONZERO", f"help exited {result.returncode}")
    _assert_safe_stream_sizes(result.stdout, result.stderr, label="help")
    commands = _commands_from_help(result.stdout.decode("utf-8", errors="replace"))
    binary_ref = BinaryRef(
        asset_name=asset_name,
        sha256=sha256,
        os=os_name,
        arch=arch,
        version_output=version_output,
    )
    artifact = ArtifactMeta(
        semantic_hash="",
        generator_name="multica-py-upstream-contract",
        generator_version="0.1.0",
        generator_commit="0" * 40,
        collection_method="help-parser",
        trust_level="help-degraded",
    )
    baseline = Baseline(state="candidate", version=version, tag=tag, commit=commit)
    observation = ObservationMeta(generated_at=now_iso())
    contract = SemanticCLIContract(
        schema_version=2,
        baseline=baseline,
        artifact=artifact,
        binary=binary_ref,
        commands=commands,
        observation=observation,
    )
    return _with_hash(contract)


def collect_from_release_asset(
    asset_path: pathlib.Path,
    *,
    expected_sha256: str,
    version: str,
    tag: str,
    commit: str,
    asset_name: str,
    os_name: str,
    arch: str,
    version_output: str,
) -> SemanticCLIContract:
    """Read a ``multica-cli-contract.json`` release asset and wrap it as a contract."""
    if not is_full_commit(commit):
        raise CollectorError("INVALID_COMMIT", f"commit must be 40-character hex, got {commit!r}")
    if not is_safe_output_size(asset_path.stat().st_size):
        raise CollectorError(
            "COLLECTOR_OUTPUT_LIMIT",
            f"release asset exceeded {DEFAULT_OUTPUT_LIMIT} bytes",
        )
    if not verify_checksum(asset_path, expected_sha256):
        raise CollectorError(
            "CHECKSUM_MISMATCH", f"asset checksum does not match {expected_sha256}"
        )
    raw_payload = asset_path.read_bytes()
    try:
        payload = msgspec.json.decode(raw_payload, type=RawExporterPayload)
    except msgspec.DecodeError as exc:
        raise CollectorError("COLLECTOR_INVALID_JSON", str(exc)) from exc
    commands = _commands_from_exporter(payload)
    binary_ref = BinaryRef(
        asset_name=asset_name,
        sha256=expected_sha256,
        os=os_name,
        arch=arch,
        version_output=version_output,
    )
    artifact = ArtifactMeta(
        semantic_hash="",
        generator_name="multica-py-upstream-contract",
        generator_version="0.1.0",
        generator_commit="0" * 40,
        collection_method="release-asset",
        trust_level=_trust_level_for("release-asset", has_source_cross_check=False),
    )
    baseline = Baseline(state="candidate", version=version, tag=tag, commit=commit)
    observation = ObservationMeta(generated_at=now_iso())
    contract = SemanticCLIContract(
        schema_version=2,
        baseline=baseline,
        artifact=artifact,
        binary=binary_ref,
        commands=commands,
        observation=observation,
    )
    return _with_hash(contract)


def cross_check_exporter_help(
    binary: pathlib.Path,
    exporter_contract: SemanticCLIContract,
    *,
    version: str,
    tag: str,
    commit: str,
    asset_name: str,
    sha256: str,
    os_name: str,
    arch: str,
    version_output: str,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    tmp_dir: pathlib.Path | None = None,
) -> None:
    """Cross-check exporter command inventory against help-parser fallback."""
    help_contract = collect_from_help_parser(
        binary,
        version=version,
        tag=tag,
        commit=commit,
        asset_name=asset_name,
        sha256=sha256,
        os_name=os_name,
        arch=arch,
        version_output=version_output,
        timeout_seconds=timeout_seconds,
        tmp_dir=tmp_dir,
    )
    if source_collector.exporter_help_agree(exporter_contract, help_contract):
        return
    diff = source_collector.classify_exporter_help_mismatch(exporter_contract, help_contract)
    details = "; ".join(f"{change.kind}:{change.severity}" for change in diff.changes[:3])
    raise CollectorError(
        "CONTRACT_SOURCE_MISMATCH",
        f"exporter and help-parser disagree ({details or 'no shared semantics'})",
    )


def _with_verified_trust(contract: SemanticCLIContract) -> SemanticCLIContract:
    updated = msgspec.structs.replace(
        contract,
        artifact=msgspec.structs.replace(
            contract.artifact,
            trust_level=_trust_level_for(
                contract.artifact.collection_method,
                has_source_cross_check=True,
            ),
        ),
    )
    return _with_hash(updated)


def _assert_safe_stream_sizes(stdout: bytes, stderr: bytes, *, label: str) -> None:
    if not is_safe_output_size(len(stdout)):
        raise CollectorError(
            "COLLECTOR_OUTPUT_LIMIT",
            f"{label} stdout exceeded {DEFAULT_OUTPUT_LIMIT} bytes",
        )
    if not is_safe_output_size(len(stderr)):
        raise CollectorError(
            "COLLECTOR_OUTPUT_LIMIT",
            f"{label} stderr exceeded {DEFAULT_OUTPUT_LIMIT} bytes",
        )


def _with_hash(contract: SemanticCLIContract) -> SemanticCLIContract:
    digest = semantic_hash(contract)
    return msgspec.structs.replace(
        contract,
        artifact=msgspec.structs.replace(contract.artifact, semantic_hash=digest),
    )


def _trust_level_for(method: str, *, has_source_cross_check: bool) -> str:
    if method == "release-asset" and has_source_cross_check:
        return "verified"
    if method == "release-asset":
        return "release-binary"
    if method == "binary-exporter" and has_source_cross_check:
        return "verified"
    if method == "binary-exporter":
        return "release-binary"
    return "help-degraded"


def _commands_from_exporter(payload: RawExporterPayload) -> tuple[CommandContract, ...]:
    if not payload.commands:
        raise CollectorError("COLLECTOR_INCOMPLETE", "exporter returned no commands")
    return tuple(_command_from_raw(c) for c in payload.commands)


def _command_from_raw(raw: RawCommand) -> CommandContract:
    path = raw.path
    return CommandContract(
        path=path,
        use=raw.use or " ".join(path),
        aliases=raw.aliases,
        hidden=raw.hidden,
        deprecated=raw.deprecated,
        args=_argument_from_raw(raw.args),
        flags=tuple(_flag_from_raw(f) for f in raw.flags),
        execution=_execution_from_raw(raw.execution),
        output=_output_from_raw(raw.output),
        source=_source_from_raw(raw.source),
    )


def _commands_from_help(help_text: str) -> tuple[CommandContract, ...]:
    commands: list[CommandContract] = []
    current: list[str] | None = None
    for line in help_text.splitlines():
        stripped = line.strip()
        if not stripped:
            current = None
            continue
        if stripped == "Available Commands:":
            continue
        if line.startswith(" ") and current is not None:
            continue
        if " " not in stripped and stripped.isalpha():
            current = [stripped]
            commands.append(
                CommandContract(
                    path=tuple(current),
                    use=stripped,
                    args=ArgumentContract(),
                    execution=ExecutionContract(),
                    output=OutputContract(
                        mode="none", decoder_policy="text-only", confidence="low"
                    ),
                )
            )
        else:
            current = None
    if not commands:
        raise CollectorError("COLLECTOR_INCOMPLETE", "help parser found no commands")
    return tuple(commands)


def _argument_from_raw(raw: RawArgument | None) -> ArgumentContract:
    if raw is None:
        return ArgumentContract()
    return ArgumentContract(
        min=raw.min,
        max=raw.max,
        grammar=raw.grammar,
        validators=raw.validators,
        review_items=raw.review_items,
    )


def _flag_from_raw(raw: RawFlag) -> FlagContract:
    return FlagContract(
        name=raw.name,
        shorthand=raw.shorthand,
        type=raw.type,
        required=raw.required,
        repeatable=raw.repeatable,
        default=raw.default,
        enum=raw.enum,
        inherited=raw.inherited,
        deprecated=raw.deprecated,
        source=_source_from_raw(raw.source),
    )


def _execution_from_raw(raw: RawExecution | None) -> ExecutionContract:
    if raw is None:
        return ExecutionContract()
    return ExecutionContract(
        interactive=raw.interactive,
        streaming=raw.streaming,
        managed_process=raw.managed_process,
        requires_server=raw.requires_server,
        exit_behavior=raw.exit_behavior,
    )


def _output_from_raw(raw: RawOutput | None) -> OutputContract:
    if raw is None:
        return OutputContract()
    return OutputContract(
        mode=raw.mode,
        schema_ref=raw.schema_ref,
        model=raw.model,
        fixture_ref=raw.fixture_ref,
        decoder_policy=raw.decoder_policy,
        confidence=raw.confidence,
        negative_fixture_ref=raw.negative_fixture_ref,
        field_change_policy=raw.field_change_policy,
    )


def _source_from_raw(raw: RawSource | None) -> SourceRef | None:
    if raw is None:
        return None
    return SourceRef(
        path=raw.path,
        symbol=raw.symbol,
        line_start=raw.line_start,
        line_end=raw.line_end,
        commit=raw.commit,
        repository=raw.repository,
    )
