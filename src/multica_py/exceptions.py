from __future__ import annotations


class MulticaError(Exception):
    pass


class ProcessOutputModeError(MulticaError):
    def __init__(self, current_mode: str, requested_consumer: str) -> None:
        self.current_mode = current_mode
        self.requested_consumer = requested_consumer
        super().__init__(
            f"Cannot use {requested_consumer}: process output is already claimed by {current_mode}."
        )


class MissingPermalinkContextError(MulticaError):
    def __init__(
        self,
        entity_type: str,
        entity_id: str,
        missing_fields: tuple[str, ...],
    ) -> None:
        fields = ", ".join(missing_fields)
        super().__init__(
            f"Cannot build {entity_type} '{entity_id}' permalink: "
            f"missing web-routing context ({fields})."
        )
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.missing_fields = missing_fields


class ExecutableNotFoundError(MulticaError):
    pass


class ExecutableNotRunnableError(MulticaError):
    pass


class UnsupportedCliVersionError(MulticaError):
    pass


class CommandTimeoutError(MulticaError):
    pass


class ProcessTimeoutError(CommandTimeoutError):
    pass


class ProcessOutputCaptureError(MulticaError):
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


class RelationError(MulticaError):
    pass


class DetachedEntityError(RelationError):
    def __init__(self, entity_type: str, entity_id: str, relation_name: str) -> None:
        super().__init__(
            f"Cannot access {entity_type}.{relation_name}: "
            f"{entity_type} '{entity_id}' is detached. "
            f"Fetch a fresh bound entity through MulticaClient."
        )
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.relation_name = relation_name


class MissingRelationContextError(RelationError):
    def __init__(
        self, entity_type: str, entity_id: str, relation_name: str, missing_field: str
    ) -> None:
        super().__init__(
            f"Cannot access {entity_type}.{relation_name}: "
            f"'{missing_field}' is required but not available "
            f"on {entity_type} '{entity_id}'."
        )
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.relation_name = relation_name
        self.missing_field = missing_field


class RelationPaginationError(RelationError):
    def __init__(self, relation_name: str, reason: str) -> None:
        super().__init__(f"Pagination error on {relation_name}: {reason}")
        self.relation_name = relation_name
        self.reason = reason
