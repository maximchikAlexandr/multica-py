from __future__ import annotations

import io
import os
import pathlib
from collections.abc import Buffer, Callable
from typing import BinaryIO, cast, overload

from multica_py._generated.approved_sdk import (
    ATTACHMENT_DOWNLOAD_BINDING,
    ATTACHMENT_UPLOAD_BINDING,
    validate_nonblank,
)
from multica_py._internal.commands import Command, _Step, _StepRef
from multica_py._internal.decoders import decode_json
from multica_py._internal.specs import RawCommandResult
from multica_py.config import OperationOptions
from multica_py.execution import OutputArtifact
from multica_py.models.system import AttachmentResult
from multica_py.resources._base import BaseResource

UploadSource = str | os.PathLike[str] | Buffer | BinaryIO


def _safe_leaf(name: str, param: str) -> str:
    if not name or not name.strip():
        raise ValueError(f"{param} must not be empty")
    if name in (".", "..") or pathlib.PurePath(name).name != name or "/" in name or "\\" in name:
        raise ValueError(f"{param} must be a bare filename, not a path: {name!r}")
    return name


def _stream_filename(stream: BinaryIO, filename: str | None) -> str:
    stream_object = cast("object", stream)
    if cast("bool", getattr(stream_object, "closed", False)):
        raise ValueError("stream must be open")
    if isinstance(stream_object, io.TextIOBase):
        raise ValueError("stream must be binary")
    read = cast("object", getattr(stream_object, "read", None))
    if not callable(read):
        raise TypeError("stream must provide a read() method")
    readable = cast("object", getattr(stream_object, "readable", None))
    if callable(readable):
        readable_fn = cast("Callable[[], bool]", readable)
        try:
            is_readable = readable_fn()
        except Exception as error:
            raise ValueError("stream must be readable") from error
        if not is_readable:
            raise ValueError("stream must be readable")
    if filename is None:
        stream_name = cast("object", getattr(stream_object, "name", None))
        if isinstance(stream_name, os.PathLike):
            stream_name = os.fspath(stream_name)
        if not isinstance(stream_name, str) or not stream_name:
            raise ValueError("filename is required for an unnamed stream")
        filename = pathlib.PurePath(stream_name).name
    return _safe_leaf(filename, "filename")


def _decode_download_path(data: bytes, *, command: str) -> pathlib.Path:
    return pathlib.Path(decode_json(data, str, command=command))


class AttachmentResource(BaseResource):
    @overload
    def upload_command(
        self,
        source: str | os.PathLike[str],
        *,
        filename: None = None,
        task_id: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[AttachmentResult]: ...

    @overload
    def upload_command(
        self,
        source: Buffer,
        *,
        filename: str,
        task_id: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[AttachmentResult]: ...

    @overload
    def upload_command(
        self,
        source: BinaryIO,
        *,
        filename: str | None = None,
        task_id: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[AttachmentResult]: ...

    def upload_command(
        self,
        source: UploadSource,
        *,
        filename: str | None = None,
        task_id: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[AttachmentResult]:
        return self._build_upload_plan(source, filename=filename, task_id=task_id, options=options)

    def _build_upload_plan(
        self,
        source: UploadSource,
        *,
        filename: str | None = None,
        task_id: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[AttachmentResult]:
        _ = cast("object", ATTACHMENT_UPLOAD_BINDING)
        if task_id is not None:
            validate_nonblank(task_id)
        stage_provider: _UploadSourceProvider
        if isinstance(source, (str, os.PathLike)):
            if filename is not None:
                raise ValueError("filename is only valid for in-memory uploads")
            source_path = pathlib.Path(os.fspath(source))
            stage_provider = _UploadSourceProvider(source_path.name, path=source_path)
        elif isinstance(source, Buffer):
            safe_filename = _safe_leaf(filename or "", "filename")
            stage_provider = _UploadSourceProvider(safe_filename, payload=bytes(source))
        else:
            stream = source
            safe_filename = _stream_filename(stream, filename)
            stage_provider = _UploadSourceProvider(safe_filename, stream=stream)
        args = ["attachment", "upload", ""]
        if task_id is not None:
            args.extend(["--task", task_id])
        plan_args, decode = self._plan_decode(tuple(args), AttachmentResult)
        return self._plan(
            steps=(
                _Step(plan_args, "run_bytes", refs=((2, _StepRef(kind="temp")),), decode=decode),
            ),
            finalize=lambda results: cast("AttachmentResult", results[0]),
            stage_provider=stage_provider,
            options=options,
        )

    @overload
    def upload(
        self,
        source: str | os.PathLike[str],
        *,
        filename: None = None,
        task_id: str | None = None,
        options: OperationOptions | None = None,
    ) -> AttachmentResult: ...

    @overload
    def upload(
        self,
        source: Buffer,
        *,
        filename: str,
        task_id: str | None = None,
        options: OperationOptions | None = None,
    ) -> AttachmentResult: ...

    @overload
    def upload(
        self,
        source: BinaryIO,
        *,
        filename: str | None = None,
        task_id: str | None = None,
        options: OperationOptions | None = None,
    ) -> AttachmentResult: ...

    def upload(
        self,
        source: UploadSource,
        *,
        filename: str | None = None,
        task_id: str | None = None,
        options: OperationOptions | None = None,
    ) -> AttachmentResult:
        return self._build_upload_plan(
            source, filename=filename, task_id=task_id, options=options
        ).run()

    def upload_bytes_command(
        self,
        filename: str,
        payload: Buffer,
        *,
        task_id: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[AttachmentResult]:
        return self.upload_command(payload, filename=filename, task_id=task_id, options=options)

    def upload_bytes(
        self,
        filename: str,
        payload: Buffer,
        *,
        task_id: str | None = None,
        options: OperationOptions | None = None,
    ) -> AttachmentResult:
        return self.upload(payload, filename=filename, task_id=task_id, options=options)

    def download_command(
        self,
        attachment_id: str,
        *,
        output_dir: pathlib.Path,
        options: OperationOptions | None = None,
    ) -> Command[pathlib.Path]:
        _ = cast("object", ATTACHMENT_DOWNLOAD_BINDING)
        validate_nonblank(attachment_id)
        args = ("attachment", "download", attachment_id, "--output-dir", str(output_dir.resolve()))

        def finalize(results: tuple[object, ...]) -> pathlib.Path:
            result = cast("RawCommandResult", results[0])
            return _decode_download_path(result.stdout, command=" ".join(result.argv))

        return self._plan(
            steps=(_Step((*args, "--output", "json"), "run_bytes"),),
            finalize=finalize,
            options=options,
        )

    def download(
        self,
        attachment_id: str,
        *,
        output_dir: pathlib.Path,
        options: OperationOptions | None = None,
    ) -> pathlib.Path:
        return self.download_command(attachment_id, output_dir=output_dir, options=options).run()

    def download_bytes_command(
        self, attachment_id: str, *, options: OperationOptions | None = None
    ) -> Command[bytes]:
        _safe_leaf(attachment_id, "attachment_id")
        args = ("attachment", "download", attachment_id, "--output-dir", "", "--output", "json")

        def finalize(results: tuple[object, ...]) -> bytes:
            result = cast("RawCommandResult", results[0])
            returned_path = _decode_download_path(result.stdout, command=" ".join(result.argv))
            artifact = cast("OutputArtifact", results[1])
            return artifact.read(str(returned_path))

        return self._plan(
            steps=(_Step(args, "run_bytes", refs=((4, _StepRef(kind="output")),)),),
            finalize=finalize,
            capture_output_label="download",
            options=options,
        )

    def download_bytes(
        self, attachment_id: str, *, options: OperationOptions | None = None
    ) -> bytes:
        return self.download_bytes_command(attachment_id, options=options).run()


class _UploadSourceProvider:
    def __init__(
        self,
        filename: str,
        *,
        path: pathlib.Path | None = None,
        payload: bytes | None = None,
        stream: BinaryIO | None = None,
    ) -> None:
        self._filename = _safe_leaf(filename, "filename")
        self._path = path
        self._payload = payload
        self._stream = stream
        self._content: bytes | None = None

    def __call__(self) -> tuple[str, bytes]:
        if self._content is None:
            if self._path is not None:
                self._content = self._path.read_bytes()
            elif self._stream is not None:
                payload = self._stream.read()
                if not isinstance(payload, Buffer):
                    raise TypeError("stream must yield bytes")
                self._content = bytes(payload)
            elif self._payload is not None:
                self._content = self._payload
            else:
                raise RuntimeError("upload source has no content")
        return self._filename, self._content
