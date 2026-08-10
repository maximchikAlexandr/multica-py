from __future__ import annotations

import io
import os
import pathlib
import stat
import tempfile
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


def _read_downloaded_bytes(output_dir: pathlib.Path, returned_path: pathlib.Path) -> bytes:
    if os.name == "nt":
        raise OSError("download_bytes is not supported securely on Windows")
    root = output_dir.resolve(strict=True)
    if any(part == ".." for part in returned_path.parts):
        raise ValueError("downloaded path must stay in the temporary output directory")
    candidate = returned_path if returned_path.is_absolute() else root / returned_path
    try:
        relative_path = candidate.resolve(strict=True).relative_to(root)
    except (OSError, ValueError) as error:
        raise ValueError("downloaded path must stay in the temporary output directory") from error
    if len(relative_path.parts) != 1:
        raise ValueError("downloaded path must be a file in the temporary output directory")

    try:
        root_descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    except OSError as error:
        raise ValueError(
            "downloaded path must be a regular file in the temporary output directory"
        ) from error
    try:
        try:
            descriptor = os.open(
                relative_path,
                os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW,
                dir_fd=root_descriptor,
            )
        except OSError as error:
            raise ValueError(
                "downloaded path must be a regular file in the temporary output directory"
            ) from error
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise ValueError(
                    "downloaded path must be a regular file in the temporary output directory"
                )
            with os.fdopen(descriptor, "rb", closefd=False) as file:
                return file.read()
        finally:
            os.close(descriptor)
    finally:
        os.close(root_descriptor)


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
        temp_provider: _TempPathProvider | None = None
        if isinstance(source, (str, os.PathLike)):
            if filename is not None:
                raise ValueError("filename is only valid for in-memory uploads")
            upload_arg = str(pathlib.Path(os.fspath(source)).resolve())
        elif isinstance(source, Buffer):
            safe_filename = _safe_leaf(filename or "", "filename")
            temp_provider = _TempPathProvider(filename=safe_filename, payload=source)
            upload_arg = ""
        else:
            stream = source
            safe_filename = _stream_filename(stream, filename)
            temp_provider = _TempPathProvider(filename=safe_filename, stream=stream)
            upload_arg = ""
        args = ["attachment", "upload", upload_arg]
        if task_id is not None:
            args.extend(["--task", task_id])
        plan_args, decode = self._plan_decode(tuple(args), AttachmentResult)
        refs = ((2, _StepRef(kind="temp")),) if temp_provider is not None else ()
        return self._plan(
            steps=(_Step(plan_args, "run_bytes", refs=refs, decode=decode),),
            finalize=lambda results: cast("AttachmentResult", results[0]),
            temp_provider=temp_provider,
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
        temp_provider = _TempPathProvider()
        args = ("attachment", "download", attachment_id, "--output-dir", "", "--output", "json")

        def finalize(results: tuple[object, ...]) -> bytes:
            result = cast("RawCommandResult", results[0])
            returned_path = _decode_download_path(result.stdout, command=" ".join(result.argv))
            return _read_downloaded_bytes(temp_provider.path, returned_path)

        return self._plan(
            steps=(_Step(args, "run_bytes", refs=((4, _StepRef(kind="temp")),)),),
            finalize=finalize,
            temp_provider=temp_provider,
            options=options,
        )

    def download_bytes(
        self, attachment_id: str, *, options: OperationOptions | None = None
    ) -> bytes:
        return self.download_bytes_command(attachment_id, options=options).run()


class _TempPathProvider:
    def __init__(
        self,
        filename: str | None = None,
        payload: Buffer | None = None,
        stream: BinaryIO | None = None,
    ) -> None:
        self._filename = filename
        self._payload = payload
        self._stream = stream
        self._directory: tempfile.TemporaryDirectory[str] | None = None

    @property
    def path(self) -> pathlib.Path:
        if self._directory is None:
            raise RuntimeError("temporary attachment directory has not been created")
        return pathlib.Path(self._directory.name)

    def __call__(self) -> str:
        if self._directory is None:
            self._directory = tempfile.TemporaryDirectory()
            if self._filename is not None:
                payload = self._stream.read() if self._stream is not None else self._payload
                if not isinstance(payload, Buffer):
                    raise TypeError("stream must yield bytes")
                (self.path / self._filename).write_bytes(bytes(payload))
        if self._filename is None:
            return str(self.path)
        return str(self.path / self._filename)

    def cleanup(self) -> None:
        if self._directory is not None:
            self._directory.cleanup()
            self._directory = None
