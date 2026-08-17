from __future__ import annotations

import pathlib
import subprocess
import sys
from dataclasses import dataclass, field

from multica_py import MulticaClient
from multica_py.config import ClientConfig
from multica_py.enums import CompatibilityPolicy
from multica_py.execution import ExecutionRequest, ExecutionResult, LocalExecutor


@dataclass
class _ThirdPartyExecutor(LocalExecutor):
    requests: list[ExecutionRequest] = field(default_factory=list)

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        self.requests.append(request)
        return ExecutionResult(exit_code=0, stdout=b"provider output", stderr=b"")


def test_common_and_provider_imports_do_not_load_optional_packages() -> None:
    source = """
import importlib.abc
import sys

class OptionalPackageBlocker(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in {\"microsandbox\", \"paramiko\"}:
            raise AssertionError(f\"optional package imported: {fullname}\")
        return None

for package in (\"microsandbox\", \"paramiko\"):
    sys.modules.pop(package, None)
sys.meta_path.insert(0, OptionalPackageBlocker())

import multica_py
from multica_py.execution import CommandExecutor, LocalExecutor
import multica_py.execution.microsandbox
import multica_py.execution.ssh

assert CommandExecutor.__module__ == \"multica_py.execution.base\"
assert LocalExecutor.__module__ == \"multica_py.execution.local\"
assert \"microsandbox\" not in sys.modules
assert \"paramiko\" not in sys.modules
"""
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    subprocess.run([sys.executable, "-c", source], cwd=repo_root, check=True)


def test_optional_provider_classes_are_not_common_or_root_exports() -> None:
    import multica_py
    import multica_py.execution as execution

    assert "MicrosandboxExecutor" not in multica_py.__all__
    assert "SshExecutor" not in multica_py.__all__
    assert "MicrosandboxExecutor" not in execution.__all__
    assert "SshExecutor" not in execution.__all__


def test_third_party_executor_is_injected_without_registration() -> None:
    executor = _ThirdPartyExecutor()
    client = MulticaClient(
        ClientConfig(compatibility=CompatibilityPolicy.ignore), executor=executor
    )
    try:
        assert client._executor is executor
        command = client.cli.command("version")
        assert command.commands == ("multica version",)
        assert command.run().stdout == b"provider output"
        assert executor.requests == [ExecutionRequest(argv=("multica", "version"))]
    finally:
        client.close()
