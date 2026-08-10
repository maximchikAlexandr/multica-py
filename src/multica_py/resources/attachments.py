from __future__ import annotations

import os
import pathlib
import stat
import tempfile
from typing import cast

import msgspec

from multica_py._generated.approved_sdk import (
    ATTACHMENT_DOWNLOAD_BINDING,
    ATTACHMENT_UPLOAD_BINDING,
    validate_nonblank,
)
from multica_py._internal.commands import Command, _Step, _StepRef
from multica_py._internal.decoders import decode_json
from multica_py._internal.specs import RawCommandResult
from multica_py.models.system import AttachmentResult
from multica_py.resources._base import BaseResource


def _safe_leaf(name: str, param: str) -> str:
    if not name:
        raise ValueError(f"{param} must not be empty")
    if name in (".", "..") or pathlib.PurePath(name).name != name or "/" in name or "\\" in name:
        raise ValueError(f"{param} must be a bare filename, not a path: {name!r}")
    return name


class _AttachmentDownloadResult(msgspec.Struct, frozen=True, kw_only=True):
    path: str


def _decode_download_path(data: bytes, *, command: str) -> pathlib.Path:
    result = decode_json(data, _AttachmentDownloadResult, command=command)
    return pathlib.Path(result.path)


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
    def upload_command(
        self, path: pathlib.Path, *, task_id: str | None = None
    ) -> Command[AttachmentResult]:
        _ = cast("object", ATTACHMENT_UPLOAD_BINDING)
        resolved = path.resolve()
        args = ["attachment", "upload", str(resolved)]
        if task_id is not None:
            validate_nonblank(task_id)
            args.extend(["--task", task_id])
        plan_args, decode = self._plan_decode(tuple(args), AttachmentResult)
        return self._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("AttachmentResult", results[0]),
        )

    def upload(self, path: pathlib.Path, *, task_id: str | None = None) -> AttachmentResult:
        return self.upload_command(path, task_id=task_id).run()

    def upload_bytes_command(
        self, filename: str, payload: bytes, *, task_id: str | None = None
    ) -> Command[AttachmentResult]:
        _safe_leaf(filename, "filename")
        if task_id is not None:
            validate_nonblank(task_id)
        temp_provider = _TempPathProvider(filename=filename, payload=payload)
        args = [
            "attachment",
            "upload",
            "",
        ]
        if task_id is not None:
            args.extend(["--task", task_id])
        plan_args, decode = self._plan_decode(tuple(args), AttachmentResult)
        return self._plan(
            steps=(
                _Step(
                    plan_args,
                    "run_bytes",
                    refs=((2, _StepRef(kind="temp")),),
                    decode=decode,
                ),
            ),
            finalize=lambda results: cast("AttachmentResult", results[0]),
            temp_provider=temp_provider,
        )

    def upload_bytes(
        self, filename: str, payload: bytes, *, task_id: str | None = None
    ) -> AttachmentResult:
        return self.upload_bytes_command(filename, payload, task_id=task_id).run()

    def download_command(
        self, attachment_id: str, *, output_dir: pathlib.Path
    ) -> Command[pathlib.Path]:
        _ = cast("object", ATTACHMENT_DOWNLOAD_BINDING)
        validate_nonblank(attachment_id)
        args = ("attachment", "download", attachment_id, "--output-dir", str(output_dir.resolve()))

        def finalize(results: tuple[object, ...]) -> pathlib.Path:
            result = cast("RawCommandResult", results[0])
            return _decode_download_path(result.stdout, command=" ".join(result.argv))

        return self._plan(
            steps=(_Step(args, "run_bytes"),),
            finalize=finalize,
        )

    def download(self, attachment_id: str, *, output_dir: pathlib.Path) -> pathlib.Path:
        return self.download_command(attachment_id, output_dir=output_dir).run()

    def download_bytes_command(self, attachment_id: str) -> Command[bytes]:
        _safe_leaf(attachment_id, "attachment_id")
        temp_provider = _TempPathProvider()
        args = ("attachment", "download", attachment_id, "--output-dir", "")

        def finalize(results: tuple[object, ...]) -> bytes:
            result = cast("RawCommandResult", results[0])
            returned_path = _decode_download_path(result.stdout, command=" ".join(result.argv))
            return _read_downloaded_bytes(temp_provider.path, returned_path)

        return self._plan(
            steps=(_Step(args, "run_bytes", refs=((4, _StepRef(kind="temp")),)),),
            finalize=finalize,
            temp_provider=temp_provider,
        )

    def download_bytes(self, attachment_id: str) -> bytes:
        return self.download_bytes_command(attachment_id).run()


class _TempPathProvider:
    def __init__(self, filename: str | None = None, payload: bytes | None = None) -> None:
        self._filename = filename
        self._payload = payload
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
                assert self._payload is not None
                (self.path / self._filename).write_bytes(self._payload)
        if self._filename is None:
            return str(self.path)
        return str(self.path / self._filename)

    def cleanup(self) -> None:
        if self._directory is not None:
            self._directory.cleanup()
            self._directory = None
