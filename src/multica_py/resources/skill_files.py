from __future__ import annotations

import os
from typing import cast

from multica_py._generated.approved_sdk import (
    SKILL_FILES_DELETE_BINDING,
    SKILL_FILES_LIST_BINDING,
    SKILL_FILES_UPSERT_BINDING,
    validate_nonblank,
)
from multica_py._internal.commands import Command, _Step
from multica_py._internal.decoders import decode_json
from multica_py.config import OperationOptions
from multica_py.models.common import ActionResult, Page
from multica_py.models.skills import SkillFile
from multica_py.resources._base import BaseResource


class SkillFileResource(BaseResource):
    def list_command(
        self,
        skill_id: str,
        *,
        with_content: bool = False,
        options: OperationOptions | None = None,
    ) -> Command[Page[SkillFile]]:
        _ = cast("object", SKILL_FILES_LIST_BINDING)
        validate_nonblank(skill_id)
        if type(with_content) is not bool:
            raise TypeError("with_content must be a bool")
        args = ["skill", "files", "list", skill_id]
        if with_content:
            args.append("--with-content")
        return self._decoded_page_command(tuple(args), SkillFile, options=options)

    def list(
        self,
        skill_id: str,
        *,
        with_content: bool = False,
        options: OperationOptions | None = None,
    ) -> Page[SkillFile]:
        return self.list_command(skill_id, with_content=with_content, options=options).run()

    def upsert_command(
        self,
        skill_id: str,
        path: str,
        content: str | None = None,
        *,
        content_file: str | os.PathLike[str] | None = None,
        content_stdin: bytes | None = None,
        options: OperationOptions | None = None,
    ) -> Command[SkillFile]:
        _ = cast("object", SKILL_FILES_UPSERT_BINDING)
        validate_nonblank(skill_id)
        validate_nonblank(path)
        if sum(value is not None for value in (content, content_file, content_stdin)) != 1:
            raise TypeError("exactly one of content, content_file, or content_stdin is required")
        args = ["skill", "files", "upsert", skill_id, "--path", path]
        stdin = None
        if content is not None:
            if not isinstance(content, str):
                raise TypeError("content must be a string")
            args.extend(("--content", content))
        elif content_file is not None:
            args.extend(("--content-file", os.fspath(content_file)))
        else:
            if not isinstance(content_stdin, bytes):
                raise TypeError("content_stdin must be bytes")
            args.append("--content-stdin")
            stdin = content_stdin
        return self._plan(
            steps=(
                _Step(
                    (*args, "--output", "json"),
                    "run_bytes",
                    stdin=stdin,
                    decode=lambda stdout, command: decode_json(stdout, SkillFile, command=command),
                ),
            ),
            finalize=lambda results: cast("SkillFile", results[0]),
            options=options,
        )

    def upsert(
        self,
        skill_id: str,
        path: str,
        content: str | None = None,
        *,
        content_file: str | os.PathLike[str] | None = None,
        content_stdin: bytes | None = None,
        options: OperationOptions | None = None,
    ) -> SkillFile:
        return self.upsert_command(
            skill_id,
            path,
            content,
            content_file=content_file,
            content_stdin=content_stdin,
            options=options,
        ).run()

    def delete_command(
        self, skill_id: str, file_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        _ = cast("object", SKILL_FILES_DELETE_BINDING)
        validate_nonblank(skill_id)
        validate_nonblank(file_id)
        return self._action_command(
            ("skill", "files", "delete", skill_id, file_id), options=options
        )

    def delete(
        self, skill_id: str, file_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.delete_command(skill_id, file_id, options=options).run()
