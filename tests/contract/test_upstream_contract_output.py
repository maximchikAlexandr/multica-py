from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
FAKE_BINARY = ROOT / "tests" / "fixtures" / "fake_multica.py"


def _run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(FAKE_BINARY), *argv],
        check=False,
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin"},
    )


def test_typed_output_fixture_is_valid_json() -> None:
    result = _run(["auth", "status"])
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert "authenticated" in payload
    assert isinstance(payload["authenticated"], bool)


def test_strict_decoder_rejects_unknown_field() -> None:
    from multica_py._internal.upstream_contract.schema import decode_contract

    decoded = decode_contract(
        {
            "schema_version": 2,
            "baseline": {
                "state": "candidate",
                "version": "0.4.3",
                "tag": "v0.4.3",
                "commit": "0" * 40,
            },
            "artifact": {
                "semantic_hash": "sha256:0",
                "generator_name": "x",
                "generator_version": "0",
                "generator_commit": "0" * 40,
                "collection_method": "binary-exporter",
            },
            "commands": [
                {
                    "path": ["auth", "status"],
                    "use": "status",
                    "output": {"mode": "json", "decoder_policy": "strict"},
                }
            ],
            "observation": {"generated_at": "2026-01-01T00:00:00Z"},
        }
    )
    assert decoded.commands[0].output.decoder_policy == "strict"
