from __future__ import annotations

import contextlib
import datetime
import os
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

import msgspec
import pytest

from multica_py._internal.transport import CliTransport
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.execution import CommandExecutor, ExecutionRequest, ExecutionResult, ProcessHandle
from multica_py.models.system import AttachmentResult


@dataclass
class _Executor:
    requests: list[ExecutionRequest] = field(default_factory=list)
    staged: list[tuple[str, bytes, Path]] = field(default_factory=list)
    close_count: int = 0

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        self.requests.append(request)
        return ExecutionResult(
            exit_code=0,
            stdout=msgspec.json.encode(AttachmentResult(id="a1", filename="file.txt")),
            stderr=b"",
        )

    def spawn(self, request: ExecutionRequest) -> ProcessHandle:
        raise AssertionError(f"unexpected spawn: {request!r}")

    @contextlib.contextmanager
    def stage(self, label: str, content: bytes) -> Iterator[str]:
        directory = Path.cwd() / f".test-stage-{len(self.staged)}"
        directory.mkdir()
        path = directory / label
        path.write_bytes(content)
        self.staged.append((label, content, path))
        try:
            yield str(path)
        finally:
            path.unlink()
            directory.rmdir()

    def close(self) -> None:
        self.close_count += 1

    def __enter__(self) -> CommandExecutor:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


@pytest.mark.parametrize(
    "view",
    (
        lambda client: client.with_profile("dev"),
        lambda client: client.with_workspace("workspace"),
        lambda client: client.with_timeout(datetime.timedelta(seconds=3)),
        lambda client: client.with_cwd("/target/workspace"),
        lambda client: client.with_environment({"TARGET_TOKEN": "token"}),
    ),
)
def test_scoped_clients_share_executor_and_semaphore_without_owning_executor(
    view: Callable[[MulticaClient], MulticaClient],
) -> None:
    executor = _Executor()
    client = MulticaClient(executor=executor)

    scoped = view(client)
    scoped.close()

    assert scoped._executor is client._executor is executor
    assert scoped._semaphore is client._semaphore
    assert executor.close_count == 0


def test_default_client_closes_only_its_own_executor(monkeypatch: pytest.MonkeyPatch) -> None:
    executor = _Executor()
    monkeypatch.setattr("multica_py.client.LocalExecutor", lambda: executor)

    client = MulticaClient()
    client.close()

    assert executor.close_count == 1


def test_supplied_executor_outlives_root_client() -> None:
    executor = _Executor()

    with MulticaClient(executor=executor):
        pass

    assert executor.close_count == 0


def test_preview_redacts_controller_environment_without_sending_it_to_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "controller-secret")
    executor = _Executor()
    client = MulticaClient(
        ClientConfig(environment=(("TARGET_TOKEN", "target-secret"),)), executor=executor
    )
    transport = client._transport

    result = transport.run_bytes(("version",))

    assert "controller-secret" not in result.argv
    assert executor.requests[0].environment == (("TARGET_TOKEN", "target-secret"),)


def test_path_upload_stages_exact_bytes_on_target_and_preview_stays_filesystem_passive(
    tmp_path: Path,
) -> None:
    source = tmp_path / "payload.bin"
    source.write_bytes(b"exact\\x00payload")
    executor = _Executor()
    client = MulticaClient(executor=executor)
    command = client.attachments.upload_command(source)

    assert command.commands == ("multica attachment upload '${temp.path}' --output json",)
    assert executor.staged == []

    assert command.run() == AttachmentResult(id="a1", filename="file.txt")
    label, content, path = executor.staged[0]
    assert label == "payload.bin"
    assert content == b"exact\\x00payload"
    assert not path.exists()
    assert executor.requests[0].argv[3].endswith("payload.bin")


def test_staging_is_cleaned_when_execution_fails(tmp_path: Path) -> None:
    source = tmp_path / "payload.bin"
    source.write_bytes(b"payload")
    executor = _Executor()

    def fail(request: ExecutionRequest) -> ExecutionResult:
        executor.requests.append(request)
        raise RuntimeError("execution failed")

    executor.run = fail  # type: ignore[method-assign]
    client = MulticaClient(executor=executor)

    with pytest.raises(RuntimeError, match="execution failed"):
        client.attachments.upload(source)

    assert not executor.staged[0][2].exists()
