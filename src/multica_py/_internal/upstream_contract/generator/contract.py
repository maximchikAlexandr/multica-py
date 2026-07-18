"""Approved SDK contract loader for deterministic generator input.

The approved SDK contract is the only valid production generator input.
Raw source evidence, candidate diffs, and generated upgrade bundles are
never generator input.
"""

from __future__ import annotations

import pathlib

import msgspec

ENUM_POLICIES: tuple[str, ...] = ("strict", "open")
CONSTRAINT_CATEGORIES: tuple[str, ...] = (
    "requires",
    "conflicts_with",
    "exactly_one",
    "at_least_one",
    "required_together",
    "conditional_enum",
    "conditional_range",
    "custom",
)
PRESENCE_SEMANTICS: tuple[str, ...] = (
    "omitted",
    "null",
    "empty",
    "zero",
    "false",
    "true",
)


class ApprovedOperation(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    operation_id: str
    binding_command_path: tuple[str, ...]
    python_parameter: str
    cli_argument: str
    required: bool = False
    presence_semantics: str = "omitted"
    enum_policy: str = "strict"
    approved_enum: tuple[str, ...] = ()
    constraints: tuple[dict[str, str], ...] = ()
    test_refs: tuple[str, ...] = ()


class ApprovedContract(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    schema_version: int
    operations: tuple[ApprovedOperation, ...] = ()


def load_approved_contract(path: pathlib.Path) -> ApprovedContract:
    contract = msgspec.json.decode(path.read_bytes(), type=ApprovedContract, strict=True)
    if contract.schema_version != 1:
        raise ValueError("unsupported approved contract schema_version")
    return contract


def validate_approved(contract: ApprovedContract) -> ApprovedContract:
    seen: set[str] = set()
    for op in contract.operations:
        if op.operation_id in seen:
            raise ValueError(f"duplicate operation_id: {op.operation_id}")
        seen.add(op.operation_id)
        if op.presence_semantics not in PRESENCE_SEMANTICS:
            raise ValueError(
                f"operation {op.operation_id}: presence_semantics {op.presence_semantics!r} not in {PRESENCE_SEMANTICS}"
            )
        if op.enum_policy not in ENUM_POLICIES:
            raise ValueError(
                f"operation {op.operation_id}: enum_policy {op.enum_policy!r} not in {ENUM_POLICIES}"
            )
        for constraint in op.constraints:
            category = constraint.get("category", "")
            if category not in CONSTRAINT_CATEGORIES:
                raise ValueError(
                    f"operation {op.operation_id}: constraint category {category!r} not in {CONSTRAINT_CATEGORIES}"
                )
    return contract
