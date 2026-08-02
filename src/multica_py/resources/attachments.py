from __future__ import annotations

import os
import pathlib
import stat
import tempfile

from multica_py._generated.approved_sdk import (
    ATTACHMENT_DOWNLOAD_BINDING,
    ATTACHMENT_UPLOAD_BINDING,
    validate_nonblank,
)
from multica_py._internal.decoders import decode_json
from multica_py.models.system import AttachmentResult
from multica_py.resources._base import BaseResource


def _safe_leaf(name: str, param: str) -> str:
    if not name:
        raise ValueError(f"{param} must not be empty")
    if name in (".", "..") or pathlib.PurePath(name).name != name or "/" in name or "\\" in name:
        raise ValueError(f"{param} must be a bare filename, not a path: {name!r}")
    return name


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
    def upload(self, path: pathlib.Path, *, task_id: str | None = None) -> AttachmentResult:
        _ = ATTACHMENT_UPLOAD_BINDING
        resolved = path.resolve()
        args = ["attachment", "upload", str(resolved)]
        if task_id is not None:
            validate_nonblank(task_id)
            args.extend(["--task", task_id])
        return self._run_json_decode(
            tuple(args),
            AttachmentResult,
        )

    def upload_bytes(
        self, filename: str, payload: bytes, *, task_id: str | None = None
    ) -> AttachmentResult:
        _safe_leaf(filename, "filename")
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / filename
            path.write_bytes(payload)
            return self.upload(path, task_id=task_id)

    def download(self, attachment_id: str, *, output_dir: pathlib.Path) -> pathlib.Path:
        _ = ATTACHMENT_DOWNLOAD_BINDING
        validate_nonblank(attachment_id)
        args = ("attachment", "download", attachment_id, "--output-dir", str(output_dir.resolve()))
        result = self._transport.run_bytes((*args, "--output", "json"), stdin=None, timeout=None)
        return _decode_download_path(result.stdout, command=" ".join(result.argv))

    def download_bytes(self, attachment_id: str) -> bytes:
        _safe_leaf(attachment_id, "attachment_id")
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = pathlib.Path(tmp)
            path = self.download(attachment_id, output_dir=output_dir)
            return _read_downloaded_bytes(output_dir, path)
