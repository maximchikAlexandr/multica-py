from __future__ import annotations

import datetime


class RawCommandResult:
    def __init__(
        self,
        argv: tuple[str, ...],
        exit_code: int,
        stdout: bytes,
        stderr: bytes,
        duration: datetime.timedelta,
        secret_values: tuple[str, ...] = (),
    ) -> None:
        self.argv = argv
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.duration = duration
        self.secret_values = secret_values


class TextResult:
    def __init__(self, text: str, stderr: str, exit_code: int) -> None:
        self.text = text
        self.stderr = stderr
        self.exit_code = exit_code
