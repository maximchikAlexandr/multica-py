"""Deterministic projections for the approved v3 contract."""

from __future__ import annotations

import hashlib
import json
import pathlib
import py_compile
import tempfile
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from types import ModuleType
from typing import cast

from .contract import (
    BindingDescriptor,
    ContractCatalog,
    ContractError,
    EnumDefinition,
    ValidatorDefinition,
    validate_contract,
)

RUNTIME_PATH = pathlib.PurePosixPath("src/multica_py/_generated/approved_sdk.py")
TRANSIENT_PATHS = (
    pathlib.PurePosixPath("docs/approved-sdk.md"),
    pathlib.PurePosixPath("reports/compatibility.json"),
    pathlib.PurePosixPath("reports/provenance.json"),
)


_ONE_OF_VALUES = {
    "IssueStatus": frozenset(
        {"backlog", "todo", "in_progress", "in_review", "done", "blocked", "cancelled"}
    ),
    "ProjectStatus": frozenset({"planned", "in_progress", "paused", "completed", "cancelled"}),
    "AutopilotExecutionMode": frozenset({"create_issue", "run_only"}),
}


@dataclass(frozen=True)
class RenderedFile:
    path: pathlib.PurePosixPath
    content: bytes


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _next_patch(version: str) -> str:
    parts = version.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ContractError(f"target.version is not a semantic version: {version!r}")
    return f"{parts[0]}.{parts[1]}.{int(parts[2]) + 1}"


def _runtime(catalog: ContractCatalog) -> bytes:
    enum_definitions: tuple[EnumDefinition, ...] = catalog.enum_definitions
    binding_descriptors: tuple[BindingDescriptor, ...] = catalog.binding_descriptors
    validator_definitions: tuple[ValidatorDefinition, ...] = catalog.validator_definitions
    enum_key: Callable[[EnumDefinition], str] = lambda item: item.public_name  # noqa: E731
    binding_operation_key: Callable[[BindingDescriptor], tuple[str, str]] = lambda item: (  # noqa: E731
        item.operation_id,
        item.entrypoint_id,
    )
    binding_descriptor_key: Callable[[BindingDescriptor], str] = lambda item: item.descriptor_id  # noqa: E731
    validator_id_key: Callable[[ValidatorDefinition], str] = lambda item: item.validator_id  # noqa: E731
    validator_name_key: Callable[[ValidatorDefinition], str] = lambda item: item.name  # noqa: E731
    lines = [
        "from __future__ import annotations",
        "",
        "from dataclasses import dataclass",
        "from enum import StrEnum",
        "",
        f"TARGET_VERSION = {catalog.target.version!r}",
        "MIN_CLI_VERSION = TARGET_VERSION",
        f"MAX_CLI_VERSION = {_next_patch(catalog.target.version)!r}",
        "",
    ]
    for definition in sorted(enum_definitions, key=enum_key):
        lines.extend([f"class {definition.public_name}(StrEnum):"])
        for member in definition.members:
            lines.append(f"    {member.name} = {member.value!r}")
        lines.append("")
    binding_names: dict[str, str] = {}
    for descriptor in catalog.binding_descriptors:
        binding_names[descriptor.descriptor_id] = (
            descriptor.descriptor_id.upper().replace(".", "_") + "_BINDING"
        )
    lines.extend(
        [
            "@dataclass(frozen=True)",
            "class GeneratedMapping:",
            "    python_path: str",
            "    cli_binding: str",
            "    destination: str",
            "",
            "@dataclass(frozen=True)",
            "class GeneratedBinding:",
            "    operation_id: str",
            "    entrypoint_id: str",
            "    command: tuple[str, ...]",
            "    mappings: tuple[GeneratedMapping, ...]",
            "    validator_ids: tuple[str, ...]",
            "",
        ]
    )
    for descriptor in sorted(binding_descriptors, key=binding_operation_key):
        mappings = ", ".join(
            f"GeneratedMapping({source!r}, {binding!r}, {destination!r})"
            for source, binding, destination in descriptor.mappings
        )
        mappings_tup = f"({mappings},)" if mappings else "()"
        lines.extend(
            [
                f"{binding_names[descriptor.descriptor_id]} = GeneratedBinding(",
                f"    {descriptor.operation_id!r}, {descriptor.entrypoint_id!r}, {descriptor.command!r},",
                f"    {mappings_tup}, {descriptor.validator_ids!r},",
                ")",
                "",
            ]
        )
    lines.append("OPERATION_BINDINGS: tuple[GeneratedBinding, ...] = (")
    for descriptor in sorted(binding_descriptors, key=binding_operation_key):
        lines.append(f"    {binding_names[descriptor.descriptor_id]},")
    lines.extend((")", ""))
    validators_by_name = {
        validator.name: validator
        for validator in sorted(validator_definitions, key=validator_id_key)
    }
    for validator in sorted(validators_by_name.values(), key=validator_name_key):
        parameter = validator.parameter_name
        body = _validator_body(validator.body_kind, parameter)
        lines.extend([f"def {validator.name}({parameter}: object) -> None:", body, ""])
    exports = ["TARGET_VERSION", "MIN_CLI_VERSION", "MAX_CLI_VERSION"]
    exports.extend(item.public_name for item in sorted(enum_definitions, key=enum_key))
    exports.extend(["GeneratedMapping", "GeneratedBinding"])
    exports.extend(
        binding_names[descriptor.descriptor_id]
        for descriptor in sorted(binding_descriptors, key=binding_descriptor_key)
    )
    exports.append("OPERATION_BINDINGS")
    exports.extend(
        item.name for item in sorted(validators_by_name.values(), key=validator_name_key)
    )
    lines.append(f"__all__ = {tuple(exports)!r}")
    lines.append("")
    return "\n".join(lines).encode()


def _validator_body(body_kind: str, parameter: str) -> str:
    if body_kind == "nonblank":
        return f"    if not isinstance({parameter}, str) or not {parameter}.strip():\n        raise ValueError('value must be nonblank')"
    if body_kind == "nonnegative_int":
        return f"    if not isinstance({parameter}, int) or isinstance({parameter}, bool) or {parameter} < 0:\n        raise ValueError('value must be a nonnegative integer')"
    if body_kind == "positive_int":
        return f"    if not isinstance({parameter}, int) or isinstance({parameter}, bool) or {parameter} <= 0:\n        raise ValueError('value must be a positive integer')"
    if body_kind.startswith("one_of:"):
        enum_id = body_kind.removeprefix("one_of:")
        values = _ONE_OF_VALUES.get(enum_id)
        if values is None:
            raise ContractError(f"unsupported validator enum ID: {enum_id}")
        return (
            f"    if not isinstance({parameter}, str) or {parameter} not in {tuple(sorted(values))!r}:\n"
            "        raise ValueError('value is not a supported enum member')"
        )
    if body_kind == "project_update":
        return f"    if {parameter} is None:\n        raise ValueError('project update value cannot be None')"
    if body_kind == "resource_update":
        return f"    if not isinstance({parameter}, str) or not {parameter}.strip():\n        raise ValueError('resource update path must be nonblank')"
    raise ContractError(f"unsupported validator body kind: {body_kind}")


def _transient(catalog: ContractCatalog) -> tuple[RenderedFile, ...]:
    operation_ids = sorted(catalog.operation_ids)
    markdown = (
        "# Approved SDK\n\n"
        + "\n".join(f"- `{operation_id}`" for operation_id in operation_ids)
        + "\n"
    )
    compatibility = {
        "max_cli_version": _next_patch(catalog.target.version),
        "min_cli_version": catalog.target.version,
        "target_version": catalog.target.version,
    }
    provenance = {
        "approved_contract_sha256": hashlib.sha256(_json_bytes(catalog.raw)).hexdigest(),
        "source_refs": [
            [source_ref_id, commit]
            for source_ref_id, commit in sorted(
                (item.source_ref_id, item.commit) for item in catalog.source_refs
            )
        ],
        "target": {
            "commit": catalog.target.commit,
            "tag": catalog.target.tag,
            "version": catalog.target.version,
        },
    }
    return (
        RenderedFile(TRANSIENT_PATHS[0], markdown.encode()),
        RenderedFile(TRANSIENT_PATHS[1], _json_bytes(compatibility)),
        RenderedFile(TRANSIENT_PATHS[2], _json_bytes(provenance)),
    )


def render_files(contract_path: pathlib.Path) -> tuple[RenderedFile, ...]:
    catalog = validate_contract(contract_path)
    return (RenderedFile(RUNTIME_PATH, _runtime(catalog)), *_transient(catalog))


def _ensure_transient_root(root: pathlib.Path) -> pathlib.Path:
    resolved = root.resolve()
    repository = pathlib.Path.cwd().resolve()
    forbidden = ("contracts", "src", "tests", "docs", "openspec")
    if resolved == repository or any(
        resolved == repository / name or repository / name in resolved.parents for name in forbidden
    ):
        raise ContractError(f"transient output is inside a tracked directory: {root}")
    return resolved


def write_rendered(
    files: Iterable[RenderedFile],
    repository: pathlib.Path,
    transient_root: pathlib.Path,
    *,
    write_runtime: bool = True,
) -> None:
    root = _ensure_transient_root(transient_root)
    for rendered in files:
        if rendered.path == RUNTIME_PATH:
            if write_runtime:
                destination = repository / pathlib.Path(rendered.path)
            else:
                continue
        else:
            destination = root / pathlib.Path(rendered.path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(rendered.content)


def _relative_files(files: Iterable[RenderedFile]) -> dict[str, bytes]:
    return {str(item.path): item.content for item in files}


def _validate_transient_projection(catalog: ContractCatalog, rendered: RenderedFile) -> None:
    text = rendered.content.decode("utf-8")
    if rendered.path == TRANSIENT_PATHS[0]:
        if not text.startswith("# Approved SDK\n"):
            raise ContractError("generated Markdown has an invalid heading")
        missing = [
            operation_id
            for operation_id in catalog.operation_ids
            if f"- `{operation_id}`\n" not in text
        ]
        if missing:
            raise ContractError(
                f"generated Markdown is missing operation IDs: {', '.join(sorted(missing))}"
            )
        return
    value = cast("object", json.loads(text))
    if not isinstance(value, dict):
        raise ContractError(f"generated {rendered.path} must be a JSON object")
    if rendered.path == TRANSIENT_PATHS[1]:
        expected = {
            "max_cli_version": _next_patch(catalog.target.version),
            "min_cli_version": catalog.target.version,
            "target_version": catalog.target.version,
        }
        if value != expected:
            raise ContractError("generated compatibility projection is invalid")
        return
    expected_provenance = {
        "approved_contract_sha256": hashlib.sha256(_json_bytes(catalog.raw)).hexdigest(),
        "source_refs": [
            [source_ref_id, commit]
            for source_ref_id, commit in sorted(
                (item.source_ref_id, item.commit) for item in catalog.source_refs
            )
        ],
        "target": {
            "commit": catalog.target.commit,
            "tag": catalog.target.tag,
            "version": catalog.target.version,
        },
    }
    if value != expected_provenance:
        raise ContractError("generated provenance projection is invalid")


def check_repository(contract_path: pathlib.Path, repository: pathlib.Path) -> None:
    first_root = pathlib.Path(tempfile.mkdtemp(prefix="upstream-contract-1-"))
    second_root = pathlib.Path(tempfile.mkdtemp(prefix="upstream-contract-2-"))
    first = render_files(contract_path)
    second = render_files(contract_path)
    if _relative_files(first) != _relative_files(second):
        raise ContractError("two clean renders differ")
    runtime_path = repository / pathlib.Path(RUNTIME_PATH)
    if not runtime_path.is_file():
        raise ContractError(f"committed runtime projection is missing: {runtime_path}")
    if runtime_path.read_bytes() != first[0].content:
        raise ContractError("committed runtime projection differs from approved contract")
    try:
        py_compile.compile(str(runtime_path), doraise=True)
        for root, files in ((first_root, first), (second_root, second)):
            write_rendered(files, repository, root, write_runtime=False)
            for rendered in files:
                if rendered.path == RUNTIME_PATH:
                    continue
                if rendered.path.suffix == ".py":
                    py_compile.compile(str(root / pathlib.Path(rendered.path)), doraise=True)
                if rendered.path.suffix in {".json", ".md"}:
                    _validate_transient_projection(
                        validate_contract(contract_path),
                        RenderedFile(
                            rendered.path, (root / pathlib.Path(rendered.path)).read_bytes()
                        ),
                    )
    finally:
        for root in (first_root, second_root):
            for path in sorted(root.rglob("*"), reverse=True):
                if path.is_file() or path.is_symlink():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()
            root.rmdir()
    _import_generated_runtime(repository)


def _import_generated_runtime(repository: pathlib.Path) -> ModuleType:
    import importlib
    import sys

    source = repository / "src"
    old = list(sys.path)
    try:
        sys.path.insert(0, str(source))
        module = importlib.import_module("multica_py._generated.approved_sdk")
        required = {"TARGET_VERSION", "MIN_CLI_VERSION", "MAX_CLI_VERSION", "OPERATION_BINDINGS"}
        exports = cast("tuple[str, ...]", getattr(module, "__all__", ()))
        if not required.issubset(set(exports)):
            raise ContractError("generated runtime exports are incomplete")
        return module
    finally:
        sys.path[:] = old
