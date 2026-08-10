from __future__ import annotations

import datetime
import inspect
import io
import os
import pathlib
from dataclasses import dataclass
from typing import BinaryIO, cast
from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig, OperationOptions
from multica_py.models.system import AttachmentResult
from multica_py.resources import attachments
from multica_py.resources.attachments import AttachmentResource, UploadSource


@dataclass(frozen=True)
class AttachmentCase:
    method: str
    args: tuple[object, ...]
    kwargs: tuple[tuple[str, pathlib.Path | str | None], ...]
    expected_argv: tuple[str, ...]
    stdout: bytes


_PAYLOAD = msgspec.json.encode(AttachmentResult(id="a1", filename="file.txt"))
_UPLOAD_PATH = pathlib.Path("/tmp/attachment.txt").resolve()
_OUTPUT_DIR = pathlib.Path("/tmp/downloads").resolve()

ATTACHMENT_CASES = (
    AttachmentCase(
        "upload",
        (_UPLOAD_PATH,),
        (),
        ("attachment", "upload", str(_UPLOAD_PATH), "--output", "json"),
        _PAYLOAD,
    ),
    AttachmentCase(
        "upload",
        (_UPLOAD_PATH,),
        (("task_id", "task_1"),),
        ("attachment", "upload", str(_UPLOAD_PATH), "--task", "task_1", "--output", "json"),
        _PAYLOAD,
    ),
    AttachmentCase(
        "download",
        ("a1",),
        (("output_dir", _OUTPUT_DIR),),
        ("attachment", "download", "a1", "--output-dir", str(_OUTPUT_DIR), "--output", "json"),
        msgspec.json.encode(str(_OUTPUT_DIR / "file.txt")),
    ),
)


@dataclass(frozen=True)
class AttachmentValidationCase:
    method: str
    args: tuple[object, ...]
    kwargs: tuple[tuple[str, pathlib.Path | str | None], ...]


@dataclass(frozen=True)
class AttachmentSignatureCase:
    method: str
    parameters: tuple[tuple[str, inspect._ParameterKind, object], ...]
    return_annotation: object


@dataclass(frozen=True)
class AttachmentBytesCase:
    method: str
    name: str
    payload: bytes


@dataclass(frozen=True)
class AttachmentUnsafeCase:
    method: str
    value: str


ATTACHMENT_VALIDATION_CASES = (
    AttachmentValidationCase("upload", (_UPLOAD_PATH,), (("task_id", ""),)),
    AttachmentValidationCase("download", ("",), (("output_dir", _OUTPUT_DIR),)),
)

ATTACHMENT_SIGNATURE_CASES = (
    AttachmentSignatureCase(
        "upload",
        (
            ("source", inspect.Parameter.POSITIONAL_OR_KEYWORD, UploadSource),
            ("filename", inspect.Parameter.KEYWORD_ONLY, str | None),
            ("task_id", inspect.Parameter.KEYWORD_ONLY, str | None),
            ("options", inspect.Parameter.KEYWORD_ONLY, OperationOptions | None),
        ),
        AttachmentResult,
    ),
    AttachmentSignatureCase(
        "download",
        (
            ("attachment_id", inspect.Parameter.POSITIONAL_OR_KEYWORD, str),
            ("output_dir", inspect.Parameter.KEYWORD_ONLY, pathlib.Path),
            ("options", inspect.Parameter.KEYWORD_ONLY, OperationOptions | None),
        ),
        pathlib.Path,
    ),
)

ATTACHMENT_BYTES_CASES = (
    AttachmentBytesCase("upload", "manifest.json", b"\x00\x01binary"),
    AttachmentBytesCase("upload", "empty.bin", b""),
    AttachmentBytesCase("download", "a1", b"\x00\x01binary"),
    AttachmentBytesCase("download", "a1", b""),
)

ATTACHMENT_UNSAFE_CASES = tuple(
    AttachmentUnsafeCase(method, value)
    for method in ("upload", "download")
    for value in ("../escape", "/absolute", "..", "nested/file", "nested\\file", "")
)


@pytest.mark.parametrize("case", ATTACHMENT_CASES)
def test_attachment_surface_uses_governed_argv(case: AttachmentCase) -> None:
    transport = MagicMock(spec=CliTransport)
    transport.run_bytes.return_value = RawCommandResult(
        argv=case.expected_argv,
        exit_code=0,
        stdout=case.stdout,
        stderr=b"",
        duration=datetime.timedelta(),
    )
    resource = AttachmentResource(transport, ClientConfig())

    result = getattr(resource, case.method)(*case.args, **dict(case.kwargs))

    if case.method == "upload":
        assert isinstance(result, AttachmentResult)
    else:
        assert result == _OUTPUT_DIR / "file.txt"
    transport.run_bytes.assert_called_once_with(case.expected_argv, stdin=None, timeout=None)
    transport.run_text.assert_not_called()


@pytest.mark.parametrize("case", ATTACHMENT_VALIDATION_CASES)
def test_attachment_surface_rejects_invalid_context_before_transport(
    case: AttachmentValidationCase,
) -> None:
    transport = MagicMock(spec=CliTransport)
    resource = AttachmentResource(transport, ClientConfig())

    with pytest.raises(ValueError):
        getattr(resource, case.method)(*case.args, **dict(case.kwargs))

    transport.run_bytes.assert_not_called()
    transport.run_text.assert_not_called()


def test_unsupported_attachment_list_is_absent() -> None:
    assert not hasattr(AttachmentResource, "list")


@pytest.mark.parametrize("case", ATTACHMENT_SIGNATURE_CASES)
def test_attachment_public_signatures(case: AttachmentSignatureCase) -> None:
    signature = inspect.signature(getattr(AttachmentResource, case.method), eval_str=True)
    parameters = tuple(signature.parameters.values())[1:]

    assert tuple((item.name, item.kind, item.annotation) for item in parameters) == case.parameters
    assert signature.return_annotation == case.return_annotation


class _NamedBytesIO(io.BytesIO):
    name = "stream.bin"


class _CountingBytesIO(io.BytesIO):
    def __init__(self, payload: bytes) -> None:
        super().__init__(payload)
        self.read_calls = 0

    def read(self, size: int | None = -1) -> bytes:
        self.read_calls += 1
        return super().read(size)


class _UnreadableBytesIO(io.BytesIO):
    def readable(self) -> bool:
        return False


def test_unified_upload_accepts_bytes_and_binary_streams_lazily() -> None:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    stream = _CountingBytesIO(b"stream-payload")
    seen: list[pathlib.Path] = []

    def complete(argv: tuple[str, ...], **_kwargs: object) -> RawCommandResult:
        path = pathlib.Path(argv[2])
        seen.append(path)
        assert path.read_bytes() == b"stream-payload"
        return RawCommandResult(argv, 0, _PAYLOAD, b"", datetime.timedelta())

    transport.run_bytes.side_effect = complete
    resource = AttachmentResource(transport, ClientConfig())
    command = resource.upload_command(stream, filename="stream.bin", task_id="task_1")

    assert stream.read_calls == 0
    assert not stream.closed
    assert command.commands == (
        "multica attachment upload '${temp.path}' --task task_1 --output json",
    )
    assert transport.run_bytes.call_count == 0

    result = command.run()

    assert result == AttachmentResult(id="a1", filename="file.txt")
    assert stream.read_calls == 1
    assert stream.tell() == len(b"stream-payload")
    assert not stream.closed
    assert len(seen) == 1
    assert not seen[0].exists()


def test_unified_upload_derives_safe_stream_name_and_preserves_path_sources() -> None:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    transport.run_bytes.return_value = RawCommandResult(
        argv=(), exit_code=0, stdout=_PAYLOAD, stderr=b"", duration=datetime.timedelta()
    )
    resource = AttachmentResource(transport, ClientConfig())
    stream = _NamedBytesIO(b"payload")
    stream_command = resource.upload_command(stream)
    path_command = resource.upload_command("relative/file.txt")

    assert stream_command.commands == ("multica attachment upload '${temp.path}' --output json",)
    assert stream.tell() == 0
    assert path_command.commands == (
        f"multica attachment upload {pathlib.Path('relative/file.txt').resolve()} --output json",
    )
    assert path_command._plan._temp_provider is None
    assert transport.run_bytes.call_count == 0


def test_upload_bytes_alias_matches_unified_upload_preview_and_result() -> None:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    payload = b"alias-payload"
    transport.run_bytes.return_value = RawCommandResult(
        argv=(), exit_code=0, stdout=_PAYLOAD, stderr=b"", duration=datetime.timedelta()
    )
    resource = AttachmentResource(transport, ClientConfig())

    unified = resource.upload_command(payload, filename="alias.bin")
    alias = resource.upload_bytes_command("alias.bin", payload)

    assert alias.commands == unified.commands
    assert alias.run() == unified.run()
    assert transport.run_bytes.call_count == 2


@pytest.mark.parametrize(
    "source",
    (
        b"payload",
        bytearray(b"payload"),
        memoryview(b"payload"),
        io.BytesIO(b"payload"),
    ),
)
def test_in_memory_upload_requires_filename_before_filesystem_or_transport(
    source: object,
) -> None:
    transport = MagicMock(spec=CliTransport)
    resource = AttachmentResource(transport, ClientConfig())

    with pytest.raises(ValueError, match="filename"):
        resource.upload_command(cast("BinaryIO", source))

    transport.run_bytes.assert_not_called()


@pytest.mark.parametrize(
    "source",
    (
        io.StringIO("text"),
        io.BytesIO(b"closed"),
        _UnreadableBytesIO(b"unreadable"),
    ),
)
def test_upload_rejects_text_or_closed_stream_before_execution(source: object) -> None:
    if isinstance(source, io.BytesIO):
        source.close()
    transport = MagicMock(spec=CliTransport)
    resource = AttachmentResource(transport, ClientConfig())

    with pytest.raises(ValueError, match="stream"):
        resource.upload_command(cast("BinaryIO", source), filename="payload.bin")

    transport.run_bytes.assert_not_called()


@pytest.mark.parametrize(
    "filename",
    ("", "   ", ".", "..", "../payload.bin", "/absolute", "nested/file.bin", "nested\\file.bin"),
)
def test_unified_upload_rejects_unsafe_filenames_before_filesystem_access(filename: str) -> None:
    transport = MagicMock(spec=CliTransport)
    resource = AttachmentResource(transport, ClientConfig())

    with pytest.raises(ValueError, match="filename"):
        resource.upload_command(b"payload", filename=filename)

    transport.run_bytes.assert_not_called()


def test_unified_upload_accepts_double_dot_basename() -> None:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    resource = AttachmentResource(transport, ClientConfig())

    command = resource.upload_command(b"payload", filename="report..txt")

    assert command.commands == ("multica attachment upload '${temp.path}' --output json",)


def test_unified_upload_failure_cleans_stream_temp_directory() -> None:
    transport = MagicMock(spec=CliTransport)
    paths: list[pathlib.Path] = []

    def fail(argv: tuple[str, ...], **_kwargs: object) -> RawCommandResult:
        path = pathlib.Path(argv[2])
        paths.append(path.parent)
        assert path.read_bytes() == b"payload"
        raise RuntimeError("upload failed")

    transport.run_bytes.side_effect = fail
    resource = AttachmentResource(transport, ClientConfig())

    with pytest.raises(RuntimeError, match="upload failed"):
        resource.upload_command(io.BytesIO(b"payload"), filename="payload.bin").run()

    assert len(paths) == 1
    assert not paths[0].exists()


@pytest.mark.parametrize("case", ATTACHMENT_BYTES_CASES)
def test_attachment_byte_helpers_preserve_content_and_clean_temporary_files(
    case: AttachmentBytesCase,
) -> None:
    transport = MagicMock(spec=CliTransport)
    temporary_directories: list[pathlib.Path] = []

    def complete(argv: tuple[str, ...], **_kwargs: object) -> RawCommandResult:
        if case.method == "upload":
            path = pathlib.Path(argv[2])
            assert path.name == case.name
            assert path.read_bytes() == case.payload
            temporary_directories.append(path.parent)
            stdout = _PAYLOAD
        else:
            directory = pathlib.Path(argv[argv.index("--output-dir") + 1])
            path = directory / case.name
            path.write_bytes(case.payload)
            temporary_directories.append(directory)
            stdout = msgspec.json.encode(str(path))
        return RawCommandResult(argv, 0, stdout, b"", datetime.timedelta())

    transport.run_bytes.side_effect = complete
    resource = AttachmentResource(transport, ClientConfig())
    result = (
        resource.upload_bytes(case.name, case.payload)
        if case.method == "upload"
        else resource.download_bytes(case.name)
    )

    if case.method == "upload":
        assert isinstance(result, AttachmentResult)
    else:
        assert result == case.payload
    transport.run_bytes.assert_called_once()
    transport.run_text.assert_not_called()
    assert not temporary_directories[0].exists()


@pytest.mark.parametrize("case", ATTACHMENT_BYTES_CASES)
def test_attachment_byte_helpers_propagate_failures_and_clean_temporary_files(
    case: AttachmentBytesCase,
) -> None:
    transport = MagicMock(spec=CliTransport)
    temporary_directories: list[pathlib.Path] = []

    def fail(argv: tuple[str, ...], **_kwargs: object) -> RawCommandResult:
        path = (
            pathlib.Path(argv[2])
            if case.method == "upload"
            else pathlib.Path(argv[argv.index("--output-dir") + 1])
        )
        temporary_directories.append(path.parent if case.method == "upload" else path)
        raise RuntimeError("cli failed")

    transport.run_bytes.side_effect = fail
    resource = AttachmentResource(transport, ClientConfig())

    with pytest.raises(RuntimeError, match="cli failed"):
        if case.method == "upload":
            resource.upload_bytes(case.name, case.payload)
        else:
            resource.download_bytes(case.name)

    assert not temporary_directories[0].exists()


@pytest.mark.parametrize("case", ATTACHMENT_UNSAFE_CASES)
def test_attachment_byte_helpers_reject_unsafe_names_before_transport(
    case: AttachmentUnsafeCase,
) -> None:
    transport = MagicMock(spec=CliTransport)
    resource = AttachmentResource(transport, ClientConfig())

    with pytest.raises(ValueError):
        if case.method == "upload":
            resource.upload_bytes(case.value, b"x")
        else:
            resource.download_bytes(case.value)

    transport.run_bytes.assert_not_called()
    transport.run_text.assert_not_called()


@pytest.mark.parametrize("kind", ("outside", "parent", "symlink"))
def test_download_bytes_rejects_untrusted_cli_paths(kind: str, tmp_path: pathlib.Path) -> None:
    transport = MagicMock(spec=CliTransport)
    external = tmp_path / "external.bin"
    external.write_bytes(b"secret")

    def complete(argv: tuple[str, ...], **_kwargs: object) -> RawCommandResult:
        output_dir = pathlib.Path(argv[argv.index("--output-dir") + 1])
        if kind == "outside":
            returned = external
        elif kind == "parent":
            returned = pathlib.Path("../external.bin")
        else:
            link = output_dir / "attachment.bin"
            link.symlink_to(external)
            returned = link
        return RawCommandResult(
            argv, 0, msgspec.json.encode(str(returned)), b"", datetime.timedelta()
        )

    transport.run_bytes.side_effect = complete
    resource = AttachmentResource(transport, ClientConfig())

    with pytest.raises(ValueError, match="temporary output directory"):
        resource.download_bytes("a1")

    transport.run_bytes.assert_called_once()


@pytest.mark.skipif(os.name == "nt", reason="POSIX FIFO semantics required")
def test_download_bytes_rejects_fifo_without_blocking(tmp_path: pathlib.Path) -> None:
    fifo = tmp_path / "attachment.bin"
    os.mkfifo(fifo)

    with pytest.raises(ValueError, match="regular file"):
        attachments._read_downloaded_bytes(tmp_path, fifo)


def test_download_bytes_fails_closed_on_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("multica_py.resources.attachments.os.name", "nt")

    with pytest.raises(OSError, match="not supported securely on Windows"):
        attachments._read_downloaded_bytes(pathlib.Path("unused"), pathlib.Path("unused"))
