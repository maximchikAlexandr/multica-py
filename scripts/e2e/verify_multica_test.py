#!/usr/bin/env python3
"""Run an isolated, artifact-producing SDK walkthrough through ``multica-test``."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.enums import CompatibilityPolicy
from multica_py.exceptions import NotFoundError
from multica_py.models.issues import IssuePropertyAssignment

_WRAPPER_EXECUTABLE = "multica-test"
_EXPECTED_CLI_VERSION = "0.6.2"
_SECRET_PATTERNS = (
    re.compile(r"(?i)(?:token|password|secret|api[_-]?key|authorization)(?:[=:]|\s+)[^\s,;]+"),
    re.compile(r"(?i)https?://[^\s]+"),
    re.compile(r"(?i)(?:profile|server[_-]?url|workspace[_-]?id)(?:[=:]|\s+)[^\s,;]+"),
)


def _sanitize(value: object) -> str:
    text = str(value)
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("<redacted>", text)
    return text


def _repo_root() -> Path | None:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip()).resolve()


def _prepare_output(path: Path) -> Path:
    output = path.expanduser().resolve()
    root = _repo_root()
    if root is not None and (output == root or root in output.parents):
        raise ValueError("output must be outside the Git checkout")
    if output.exists():
        if not output.is_dir() or any(output.iterdir()):
            raise ValueError("output must be a new or empty directory")
    else:
        output.mkdir(parents=True)
    return output


def _current_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    )
    sha = result.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise RuntimeError("tested checkout did not report a full commit SHA")
    return sha


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_artifacts(
    output: Path,
    *,
    sdk_sha: str | None,
    events: list[dict[str, Any]],
    errors: list[dict[str, str]],
    cleanup: list[dict[str, str]],
) -> None:
    stdout_path = output / "stdout.txt"
    stderr_path = output / "stderr.txt"
    cleanup_path = output / "cleanup.json"
    stdout_path.write_text(
        "\n".join(json.dumps(event, ensure_ascii=False, sort_keys=True) for event in events) + "\n",
        encoding="utf-8",
    )
    stderr_path.write_text(
        "\n".join(json.dumps(error, ensure_ascii=False, sort_keys=True) for error in errors)
        + ("\n" if errors else ""),
        encoding="utf-8",
    )
    _write_json(
        cleanup_path,
        {"items": cleanup, "all_succeeded": all(item["status"] == "ok" for item in cleanup)},
    )
    manifest = {
        "schema": "multica-py-e2e-v1",
        "sdk_sha": sdk_sha,
        "cli_executable": _WRAPPER_EXECUTABLE,
        "cli_expected_version": _EXPECTED_CLI_VERSION,
        "credentials": "not collected",
        "artifacts": {
            name: _hash(output / name) for name in ("stdout.txt", "stderr.txt", "cleanup.json")
        },
    }
    _write_json(output / "manifest.json", manifest)


def _walkthrough(
    client: MulticaClient,
    events: list[dict[str, Any]],
    resources: dict[str, str],
) -> None:
    suffix = uuid4().hex[:12]
    project = client.projects.create(name=f"multica-py-e2e-{suffix}")
    resources["project_id"] = project.id
    text_name = f"e2e-text-{suffix}"
    url_name = f"e2e-url-{suffix}"
    text_definition = client.properties.create(name=text_name, property_type="multi_text")
    resources["text_property_id"] = text_definition.id
    url_definition = client.properties.create(name=url_name, property_type="multi_url")
    resources["url_property_id"] = url_definition.id
    create_text = ("alpha,comma", "[literal]")
    create_urls = ("https://example.com/a?x=1", "https://example.com/b")
    issue = client.issues.create(
        title=f"multica-py-e2e-{suffix}",
        project_id=project.id,
        properties=(
            IssuePropertyAssignment(
                reference=text_name, value=create_text, property_type="multi_text"
            ),
            IssuePropertyAssignment(
                reference=url_name, value=create_urls, property_type="multi_url"
            ),
        ),
    )
    events.append(
        {"step": "create", "status": "ok", "issue_id": issue.id, "project_id": project.id}
    )

    direct_text = ("direct,comma", "direct-second")
    direct_urls = ("https://example.com/direct",)
    client.issues.properties.set(
        issue.id, name=text_name, value=direct_text, property_type="multi_text"
    )
    client.issues.properties.set(
        issue.id, name=url_name, value=direct_urls, property_type="multi_url"
    )
    values = {row.name: row.value for row in client.issues.properties.list(issue.id)}
    if values.get(text_name) != direct_text or values.get(url_name) != direct_urls:
        raise AssertionError("direct list-property read-back did not preserve tuples")
    resolved = client.issues.get(issue.id, resolve_properties=True)
    if resolved.id != issue.id:
        raise AssertionError("issue read-back returned the wrong resource")
    resolved_values = resolved.properties
    if (
        resolved_values[text_name].value != direct_text
        or resolved_values[url_name].value != direct_urls
    ):
        raise AssertionError("resolved property read-back did not preserve tuples")
    filtered = client.issues.list(
        project_id=project.id,
        property_filters=(f"{text_name}=direct,comma",),
        limit=20,
    )
    if issue.id not in {item.id for item in filtered.items}:
        raise AssertionError("exact-element property filter did not find the issue")
    updated = client.projects.update(project.id, description="e2e-updated")
    if updated.description != "e2e-updated":
        raise AssertionError("project update read-back did not preserve description")
    events.append(
        {
            "step": "read-back",
            "status": "ok",
            "issue_id": issue.id,
            "property_ids": [text_definition.id, url_definition.id],
            "filtered_issue_ids": [item.id for item in filtered.items],
        }
    )


def _cleanup(
    client: MulticaClient, resources: dict[str, str], cleanup: list[dict[str, str]]
) -> None:
    for key in ("project_id", "text_property_id", "url_property_id"):
        resource_id = resources.get(key)
        if resource_id is None:
            continue
        try:
            if key == "project_id":
                client.projects.delete(resource_id)
                try:
                    client.projects.get(resource_id)
                except NotFoundError:
                    pass
                else:
                    raise AssertionError("deleted project was still readable")
            else:
                client.properties.archive(resource_id)
                _require_archived_property(client, resource_id)
        except Exception as error:  # pragma: no cover - exercised by isolated stand
            cleanup.append({"resource": key, "status": "error", "error": _sanitize(error)})
        else:
            cleanup.append({"resource": key, "status": "ok"})


def _require_archived_property(client: MulticaClient, property_id: str) -> None:
    if not client.properties.get(property_id).archived:
        raise AssertionError("archived property remained active")


def _build_client() -> MulticaClient:
    if shutil.which(_WRAPPER_EXECUTABLE) is None:
        raise RuntimeError("wrapper-owned multica-test is not installed")
    config = ClientConfig(
        executable=_WRAPPER_EXECUTABLE,
        compatibility=CompatibilityPolicy.strict,
    )
    if (
        config.profile is not None
        or config.server_url is not None
        or config.workspace_id is not None
    ):
        raise AssertionError("wrapper-owned walkthrough must not set target overrides")
    return MulticaClient(config)


def _require_cli_version(client: MulticaClient) -> None:
    status = client.daemon.status()
    if status.cli_version != _EXPECTED_CLI_VERSION:
        raise RuntimeError("CLI version gate failed")


def run(output: Path) -> int:
    events: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    cleanup: list[dict[str, str]] = []
    sdk_sha: str | None = None
    resources: dict[str, str] = {}
    prepared_output: Path | None = None
    failure: Exception | None = None
    try:
        prepared_output = _prepare_output(output)
        sdk_sha = _current_sha()
        with _build_client() as client:
            try:
                _require_cli_version(client)
                events.append(
                    {"step": "preflight", "status": "ok", "cli_version": _EXPECTED_CLI_VERSION}
                )
                _walkthrough(client, events, resources)
            except Exception as error:
                failure = error
                errors.append({"type": type(error).__name__, "detail": _sanitize(error)})
            finally:
                if resources:
                    _cleanup(client, resources, cleanup)
    except Exception as error:
        if failure is None:
            failure = error
            errors.append({"type": type(error).__name__, "detail": _sanitize(error)})
    finally:
        if resources and not cleanup:
            errors.append({"type": "CleanupError", "detail": "cleanup did not run"})
        if prepared_output is not None:
            try:
                _write_artifacts(
                    prepared_output,
                    sdk_sha=sdk_sha,
                    events=events,
                    errors=errors,
                    cleanup=cleanup,
                )
            except Exception as error:
                failure = failure or error
                print(f"artifact write failed: {_sanitize(error)}", file=sys.stderr)
    if failure is not None:
        print(
            f"walkthrough failed: {type(failure).__name__}: {_sanitize(failure)}", file=sys.stderr
        )
        return 1
    if any(item["status"] != "ok" for item in cleanup):
        print("walkthrough cleanup failed", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    namespace = parser.parse_args(argv)
    return run(namespace.output)


if __name__ == "__main__":
    raise SystemExit(main())
