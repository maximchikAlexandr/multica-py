from __future__ import annotations


class MulticaError(Exception):
    pass


class ExecutableNotFoundError(MulticaError):
    pass


class ExecutableNotRunnableError(MulticaError):
    pass


class UnsupportedCliVersionError(MulticaError):
    pass


class CommandTimeoutError(MulticaError):
    pass


class CommandCancelledError(MulticaError):
    pass


class CommandExecutionError(MulticaError):
    def __init__(
        self,
        message: str,
        exit_code: int | None = None,
        stdout: str = "",
        stderr: str = "",
        argv: tuple[str, ...] = (),
    ) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.argv = argv


class AuthenticationError(CommandExecutionError):
    pass


class AuthorizationError(CommandExecutionError):
    pass


class NotFoundError(CommandExecutionError):
    pass


class ConflictError(CommandExecutionError):
    pass


class ValidationError(CommandExecutionError):
    pass


class NetworkError(CommandExecutionError):
    pass


class UnknownCommandError(CommandExecutionError):
    pass


class ProtocolError(MulticaError):
    pass


class JsonOutputError(ProtocolError):
    pass


class OutputShapeError(ProtocolError):
    pass


class EncodingError(ProtocolError):
    pass
