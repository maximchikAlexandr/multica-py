from __future__ import annotations

import pathlib
from collections.abc import Callable
from typing import cast
from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py._internal.specs import RawCommandResult, TextResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.system import AttachmentResult
from multica_py.resources.attachments import AttachmentResource

_AR = msgspec.json.encode(AttachmentResult(id="a1", filename="f.txt"))


def test_upload_bytes_round_trip(
    mock_transport: MagicMock, raw_result: Callable[[bytes, int], RawCommandResult]
) -> None:
    mock_transport.run_bytes.return_value = raw_result(_AR, 0)
    resource = AttachmentResource(cast("CliTransport", mock_transport), ClientConfig())
    result = resource.upload_bytes("i1", "manifest.json", b'{"x":1}')
    assert isinstance(result, AttachmentResult)
    assert result.id == "a1"
    mock_transport.run_bytes.assert_called_once()
    args = mock_transport.run_bytes.call_args
    file_arg = args.args[0][4]
    assert pathlib.PurePath(file_arg).name == "manifest.json"
    assert not pathlib.Path(file_arg).parent.exists()


def test_upload_bytes_empty_payload(
    mock_transport: MagicMock, raw_result: Callable[[bytes, int], RawCommandResult]
) -> None:
    st_size: list[int] = []
    tmpdirs: list[pathlib.Path] = []

    def side_effect(argv: tuple[str, ...], **kwargs: object) -> RawCommandResult:
        path = pathlib.Path(argv[4])
        st_size.append(path.stat().st_size)
        tmpdirs.append(path.parent)
        return raw_result(_AR, 0)

    mock_transport.run_bytes.side_effect = side_effect
    resource = AttachmentResource(cast("CliTransport", mock_transport), ClientConfig())
    result = resource.upload_bytes("i1", "empty.bin", b"")
    assert isinstance(result, AttachmentResult)
    assert result.id == "a1"
    assert st_size[0] == 0
    assert not tmpdirs[0].exists()


def test_upload_bytes_preserves_filename(
    mock_transport: MagicMock, raw_result: Callable[[bytes, int], RawCommandResult]
) -> None:
    mock_transport.run_bytes.return_value = raw_result(_AR, 0)
    resource = AttachmentResource(cast("CliTransport", mock_transport), ClientConfig())
    resource.upload_bytes("i1", "ai-factory-result.json", b"...")
    args = mock_transport.run_bytes.call_args
    file_arg = args.args[0][4]
    assert file_arg.endswith("ai-factory-result.json")
    assert pathlib.PurePath(file_arg).name == "ai-factory-result.json"


def test_upload_bytes_cleans_up_on_failure(mock_transport: MagicMock) -> None:
    tmpdirs: list[str] = []

    def side_effect(argv: tuple[str, ...], **kwargs: object) -> RawCommandResult:
        tmpdirs.append(str(pathlib.Path(argv[4]).parent))
        raise RuntimeError("cli failed")

    mock_transport.run_bytes.side_effect = side_effect
    resource = AttachmentResource(cast("CliTransport", mock_transport), ClientConfig())
    with pytest.raises(RuntimeError, match="cli failed"):
        resource.upload_bytes("i1", "f.txt", b"x")
    assert not pathlib.Path(tmpdirs[0]).exists()


@pytest.mark.parametrize("bad_leaf", ["../escape.txt", "/abs/path", "..", "foo\\bar", ""])
def test_upload_bytes_rejects_unsafe_filename(mock_transport: MagicMock, bad_leaf: str) -> None:
    resource = AttachmentResource(cast("CliTransport", mock_transport), ClientConfig())
    with pytest.raises(ValueError):
        resource.upload_bytes("i1", bad_leaf, b"x")


def test_download_bytes_round_trip(mock_transport: MagicMock) -> None:
    def side_effect(argv: tuple[str, ...], **kwargs: object) -> TextResult:
        out = argv[argv.index("--output") + 1]
        pathlib.Path(out).write_bytes(b"\x00\x01binary")
        return TextResult(text="", stderr="", exit_code=0)

    mock_transport.run_text.side_effect = side_effect
    resource = AttachmentResource(cast("CliTransport", mock_transport), ClientConfig())
    result = resource.download_bytes("a1")
    assert result == b"\x00\x01binary"
    mock_transport.run_text.assert_called_once()
    args = mock_transport.run_text.call_args
    out_arg = args.args[0][args.args[0].index("--output") + 1]
    assert not pathlib.Path(out_arg).parent.exists()


def test_download_bytes_empty_attachment(mock_transport: MagicMock) -> None:
    def side_effect(argv: tuple[str, ...], **kwargs: object) -> TextResult:
        out = argv[argv.index("--output") + 1]
        pathlib.Path(out).write_bytes(b"")
        return TextResult(text="", stderr="", exit_code=0)

    mock_transport.run_text.side_effect = side_effect
    resource = AttachmentResource(cast("CliTransport", mock_transport), ClientConfig())
    assert resource.download_bytes("a1") == b""


def test_download_bytes_cleans_up_on_failure(mock_transport: MagicMock) -> None:
    tmpdirs: list[str] = []

    def side_effect(argv: tuple[str, ...], **kwargs: object) -> TextResult:
        tmpdirs.append(str(pathlib.Path(argv[argv.index("--output") + 1]).parent))
        raise RuntimeError("cli failed")

    mock_transport.run_text.side_effect = side_effect
    resource = AttachmentResource(cast("CliTransport", mock_transport), ClientConfig())
    with pytest.raises(RuntimeError, match="cli failed"):
        resource.download_bytes("a1")
    assert not pathlib.Path(tmpdirs[0]).exists()


@pytest.mark.parametrize("bad_leaf", ["../escape", "/abs/path", "..", "foo\\bar", ""])
def test_download_bytes_rejects_unsafe_attachment_id(
    mock_transport: MagicMock, bad_leaf: str
) -> None:
    resource = AttachmentResource(cast("CliTransport", mock_transport), ClientConfig())
    with pytest.raises(ValueError):
        resource.download_bytes(bad_leaf)


def test_existing_upload_unchanged(
    mock_transport: MagicMock, raw_result: Callable[[bytes, int], RawCommandResult]
) -> None:
    mock_transport.run_bytes.return_value = raw_result(_AR, 0)
    resource = AttachmentResource(cast("CliTransport", mock_transport), ClientConfig())
    result = resource.upload("i1", "/p/f.txt")
    assert isinstance(result, AttachmentResult)
    mock_transport.run_bytes.assert_called_once_with(
        (
            "attachment",
            "upload",
            "i1",
            "--file",
            str(pathlib.Path("/p/f.txt").resolve()),
            "--output",
            "json",
        ),
        stdin=None,
        timeout=None,
    )


def test_existing_download_unchanged(mock_transport: MagicMock) -> None:
    mock_transport.run_text.return_value = TextResult(text="", stderr="", exit_code=0)
    resource = AttachmentResource(cast("CliTransport", mock_transport), ClientConfig())
    resource.download("a1", "/out")
    mock_transport.run_text.assert_called_once()
    args = mock_transport.run_text.call_args
    assert args.args[0] == (
        "attachment",
        "download",
        "a1",
        "--output",
        str(pathlib.Path("/out").resolve()),
    )
