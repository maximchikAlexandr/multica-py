"""Fail-closed declarative evidence collection for pinned upstream releases."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import subprocess
from dataclasses import dataclass
from typing import cast

REVIEW_CODES = (
    "UNKNOWN_PATTERN",
    "UNRESOLVED_HELPER",
    "DYNAMIC_ENUM",
    "IMPERATIVE_VALIDATION",
    "PRESENCE_SENSITIVE",
    "UNRESOLVED_MAPPING",
)
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_LITERAL_STRING = r'"(?:[^"\\]|\\.)*"'
_LITERAL_STRING_RE: re.Pattern[str] = re.compile(_LITERAL_STRING)
_FIELD_MARKERS = {
    "Use": re.compile(r"\bUse\s*:"),
    "Aliases": re.compile(r"\bAliases\s*:"),
    "Hidden": re.compile(r"\bHidden\s*:"),
    "Deprecated": re.compile(r"\bDeprecated\s*:"),
}
_USE = re.compile(rf"\bUse\s*:\s*({_LITERAL_STRING})\s*(?=,|}})")
_ALIAS = re.compile(
    rf"\bAliases\s*:\s*\[\s*((?:{_LITERAL_STRING}\s*(?:,\s*{_LITERAL_STRING}\s*)*)?)\]\s*(?=,|}})"
)
_HIDDEN = re.compile(r"\bHidden\s*:\s*(true|false)\s*(?=,|})")
_DEPRECATED = re.compile(rf"\bDeprecated\s*:\s*({_LITERAL_STRING})\s*(?=,|}})")
_ADD_COMMAND = re.compile(r"\bAddCommand\(([^\n]*)\)")
_KNOWN_ADD_COMMAND = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\s*,\s*[A-Za-z_][A-Za-z0-9_]*)*")
_KNOWN_FLAG = re.compile(
    rf"\b(?:Flags|PersistentFlags)\(\)\.(String|Bool|Int|Float|Duration|StringSlice)\("
    rf"(?P<arguments>{_LITERAL_STRING}\s*,\s*(?:{_LITERAL_STRING}|true|false|[-+]?[0-9]+(?:\.[0-9]+)?|\[\]string\{{[^{{}}]*\}})\s*,\s*{_LITERAL_STRING})\)"
)
_FLAG_MARKER = re.compile(r"\b(?:Flags|PersistentFlags)\(\)\.[A-Za-z_][A-Za-z0-9_]*\s*\(")
_KNOWN_ARGS = re.compile(
    r"\bArgs\s*:\s*cobra\.(?P<validator>NoArgs\(\)|(?:ExactArgs|MaximumNArgs|MinimumNArgs)\([0-9]+\)|RangeArgs\([0-9]+\s*,\s*[0-9]+\))\s*(?=,|})"
)
_ARGS_MARKER = re.compile(r"\bArgs\s*:")
_PRESENCE = re.compile(r"\b(?:Flags|PersistentFlags)\(\)\.Changed\s*\(")
_IMPERATIVE = re.compile(r"\b(?:if|switch)\b|\b(?:ValidateFunc|MarkFlag\w+)\b")
_DYNAMIC_ENUM = re.compile(r"\b(?:append|make)\s*\(|\b(?:Choices|Enum|Values)\s*[:=]")


@dataclass(frozen=True)
class ReleaseIdentity:
    tag: str
    version: str
    commit: str
    release_id: str
    asset_name: str
    sha256: str
    os: str
    arch: str
    version_output_sha256: str


def _sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_forbidden_output(output: pathlib.Path) -> bool:
    root = pathlib.Path.cwd().resolve()
    resolved = output.resolve()
    return any(
        resolved == root / name or root / name in resolved.parents
        for name in ("contracts", "src", "tests", "docs", "openspec")
    )


def _source_location(path: str, line_number: int, symbol: str) -> dict[str, object]:
    return {
        "line_end": line_number,
        "line_start": line_number,
        "path": path,
        "symbol": symbol,
    }


def _without_go_comments(content: str) -> tuple[str, ...]:
    """Return source lines with comments blanked while preserving literals and lines."""

    lines: list[str] = []
    block_comment = False
    for raw_line in content.splitlines():
        result: list[str] = []
        index = 0
        quoted = False
        escaped = False
        while index < len(raw_line):
            pair = raw_line[index : index + 2]
            if block_comment:
                if pair == "*/":
                    block_comment = False
                    result.extend("  ")
                    index += 2
                else:
                    result.append(" ")
                    index += 1
            elif quoted:
                character = raw_line[index]
                result.append(character)
                if character == '"' and not escaped:
                    quoted = False
                escaped = character == "\\" and not escaped
                if character != "\\":
                    escaped = False
                index += 1
            elif pair == "//":
                result.extend(" " * (len(raw_line) - index))
                break
            elif pair == "/*":
                block_comment = True
                result.extend("  ")
                index += 2
            else:
                character = raw_line[index]
                result.append(character)
                quoted = character == '"'
                index += 1
        lines.append("".join(result))
    return tuple(lines)


def _git_go_sources(source_checkout: pathlib.Path, commit: str) -> tuple[tuple[str, str], ...]:
    """Read only tracked Go blobs from the pinned commit, never worktree files."""

    listing = subprocess.run(
        ["git", "-C", str(source_checkout), "ls-tree", "-r", "-z", commit, "--"],
        check=True,
        capture_output=True,
    ).stdout
    sources: list[tuple[str, str]] = []
    for entry in listing.split(b"\0"):
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        mode, kind, _object_id = metadata.decode("ascii").split()
        path = raw_path.decode("utf-8", errors="surrogateescape")
        if kind != "blob" or mode not in {"100644", "100755"} or not path.endswith(".go"):
            continue
        content = subprocess.run(
            ["git", "-C", str(source_checkout), "show", f"{commit}:{path}"],
            check=True,
            capture_output=True,
        ).stdout.decode("utf-8", errors="replace")
        sources.append((path, content))
    return tuple(sources)


def _collect_facts(
    source_root: pathlib.Path,
    *,
    commit: str | None = None,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    facts: list[dict[str, object]] = []
    review_items: list[dict[str, object]] = []
    if commit is None:
        sources = tuple(
            (
                path.relative_to(source_root).as_posix(),
                path.read_text(encoding="utf-8", errors="replace"),
            )
            for path in sorted(source_root.rglob("*.go"))
        )
    else:
        sources = _git_go_sources(source_root, commit)
    for relative, content in sources:
        lines = _without_go_comments(content)
        for number, line in enumerate(lines, start=1):
            use_match = _USE.search(line)
            if use_match:
                use_value = cast("str", use_match.group(1)).strip('"')
                facts.append(
                    {
                        "command_path": use_value.split(),
                        "kind": "cobra_use",
                        "source": _source_location(relative, number, "cobra.Command"),
                        "value": {"use": use_value},
                    }
                )
            alias_match = _ALIAS.search(line)
            if alias_match:
                literal_matches = cast(
                    "list[str]",
                    _LITERAL_STRING_RE.findall(cast("str", alias_match.group(1))),
                )
                aliases = [item.strip('"') for item in literal_matches]
                facts.append(
                    {
                        "command_path": [],
                        "kind": "cobra_aliases",
                        "source": _source_location(relative, number, "cobra.Command"),
                        "value": {"aliases": aliases},
                    }
                )
            for regex, kind, key in (
                (_HIDDEN, "cobra_hidden", "hidden"),
                (_DEPRECATED, "cobra_deprecated", "deprecated"),
            ):
                match = regex.search(line)
                if match:
                    match_value = cast("str", match.group(1))
                    value: object = (
                        match_value == "true" if key == "hidden" else match_value.strip('"')
                    )
                    facts.append(
                        {
                            "command_path": [],
                            "kind": kind,
                            "source": _source_location(relative, number, "cobra.Command"),
                            "value": {key: value},
                        }
                    )
            for field, marker in _FIELD_MARKERS.items():
                if (
                    marker.search(line)
                    and not {
                        "Use": use_match,
                        "Aliases": alias_match,
                        "Hidden": _HIDDEN.search(line),
                        "Deprecated": _DEPRECATED.search(line),
                    }[field]
                ):
                    review_items.append(
                        {
                            "code": "UNKNOWN_PATTERN",
                            "message": f"{field} is not a closed Cobra literal",
                            "source": _source_location(relative, number, "cobra.Command"),
                        }
                    )
            add_match = _ADD_COMMAND.search(line)
            if add_match:
                arguments = cast("str", add_match.group(1)).strip()
                if _KNOWN_ADD_COMMAND.fullmatch(arguments):
                    facts.append(
                        {
                            "command_path": [],
                            "kind": "add_command",
                            "source": _source_location(relative, number, "AddCommand"),
                            "value": {"arguments": arguments},
                        }
                    )
                else:
                    review_items.append(
                        {
                            "code": "UNRESOLVED_HELPER",
                            "message": "AddCommand arguments are not a closed declarative pattern",
                            "source": _source_location(relative, number, "AddCommand"),
                        }
                    )
            flag_match = _KNOWN_FLAG.search(line)
            if flag_match:
                facts.append(
                    {
                        "command_path": [],
                        "kind": "flag_registration",
                        "source": _source_location(relative, number, f"{flag_match.group(1)}Flag"),
                        "value": {"name": flag_match.group(2), "type": flag_match.group(1)},
                    }
                )
            elif _FLAG_MARKER.search(line):
                review_items.append(
                    {
                        "code": "UNKNOWN_PATTERN",
                        "message": "flag registration is not a closed declarative pattern",
                        "source": _source_location(relative, number, "flag-registration"),
                    }
                )
            args_match = _KNOWN_ARGS.search(line)
            if args_match:
                validator = cast("str", args_match.group("validator"))
                facts.append(
                    {
                        "command_path": [],
                        "kind": "cobra_args",
                        "source": _source_location(relative, number, "cobra.Args"),
                        "value": {"validator": validator.split("(", 1)[0]},
                    }
                )
            elif _ARGS_MARKER.search(line):
                review_items.append(
                    {
                        "code": "UNKNOWN_PATTERN",
                        "message": "Args is not a closed Cobra validator pattern",
                        "source": _source_location(relative, number, "cobra.Args"),
                    }
                )
            if _PRESENCE.search(line):
                code = "PRESENCE_SENSITIVE"
            elif _DYNAMIC_ENUM.search(line):
                code = "DYNAMIC_ENUM"
            elif _IMPERATIVE.search(line):
                code = "IMPERATIVE_VALIDATION"
            elif "RunE:" in line or "Flags().Lookup" in line:
                code = "UNRESOLVED_HELPER"
            else:
                code = ""
            if code:
                review_items.append(
                    {
                        "code": code,
                        "message": "relevant imperative or helper logic requires human review",
                        "source": _source_location(relative, number, "unknown-source-pattern"),
                    }
                )
    facts.sort(
        key=lambda item: (
            str(item["kind"]),
            str(item["command_path"]),
            str(item["source"]),
            json.dumps(item["value"], sort_keys=True),
        )
    )
    review_items.sort(key=lambda item: (str(item["code"]), str(item["source"])))
    return facts, review_items


def collect(
    *,
    source_checkout: pathlib.Path,
    binary: pathlib.Path,
    identity: ReleaseIdentity,
    version_output: pathlib.Path,
    output_dir: pathlib.Path,
) -> None:
    if not _COMMIT.fullmatch(identity.commit):
        raise ValueError("commit must be a full 40-character hexadecimal value")
    if _is_forbidden_output(output_dir):
        raise ValueError("collect output must be outside contracts, src, tests, docs, and openspec")
    if not source_checkout.is_dir():
        raise ValueError(f"source checkout does not exist: {source_checkout}")
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise ValueError(f"verified binary is not executable: {binary}")
    if not version_output.is_file():
        raise ValueError(f"version output does not exist: {version_output}")
    if _sha256(binary) != identity.sha256:
        raise ValueError("verified binary checksum does not match --sha256")
    actual_commit = subprocess.run(
        ["git", "-C", str(source_checkout), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if actual_commit != identity.commit:
        raise ValueError("source checkout HEAD does not match --commit")
    facts, review_items = _collect_facts(source_checkout, commit=identity.commit)
    evidence = {
        "binary": {
            "arch": identity.arch,
            "asset_name": identity.asset_name,
            "os": identity.os,
            "sha256": identity.sha256,
            "version_output_sha256": _sha256(version_output),
        },
        "facts": facts,
        "schema_version": 1,
        "target": {
            "commit": identity.commit,
            "release_id": identity.release_id,
            "tag": identity.tag,
            "version": identity.version,
        },
    }
    review = {"items": review_items, "schema_version": 1}
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "evidence.json").write_bytes(
        (json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    )
    (output_dir / "review-items.json").write_bytes(
        (json.dumps(review, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    )
