from __future__ import annotations

from multica_py.config import ClientConfig


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
