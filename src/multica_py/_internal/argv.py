from __future__ import annotations

from multica_py.config import ClientConfig

_GLOBAL_OPTIONS_WITH_VALUES = frozenset({"--server-url", "--workspace-id", "--profile"})
_GLOBAL_BOOLEAN_OPTIONS = frozenset({"--debug"})


def normalize_global_args(argv: tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    index = 0
    while index < len(argv):
        argument = argv[index]
        option, separator, _value = argument.partition("=")
        if option in _GLOBAL_BOOLEAN_OPTIONS:
            index += 1
            continue
        if option in _GLOBAL_OPTIONS_WITH_VALUES:
            index += 1
            if not separator and index < len(argv):
                index += 1
            continue
        normalized.append(argument)
        index += 1
    return tuple(normalized)


def build_global_args(config: ClientConfig) -> tuple[str, ...]:
    args: list[str] = []
    if config.server_url is not None:
        args.extend(["--server-url", config.server_url])
    if config.workspace_id is not None:
        args.extend(["--workspace-id", config.workspace_id])
    if config.profile is not None:
        args.extend(["--profile", config.profile])
    if config.debug:
        args.append("--debug")
    return tuple(args)
