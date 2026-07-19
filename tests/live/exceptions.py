from __future__ import annotations


class LiveSetupError(RuntimeError):
    """Raised when live test environment setup fails."""

    def __init__(self, stage: str, message: str) -> None:
        super().__init__(message)
        self.stage = stage
