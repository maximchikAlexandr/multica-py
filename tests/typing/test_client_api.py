from __future__ import annotations

from multica_py import ClientConfig, MulticaClient


def test_client_creation_typed():
    config: ClientConfig = ClientConfig()
    client: MulticaClient = MulticaClient(config)
    assert isinstance(client, MulticaClient)


def test_client_has_resources():
    config = ClientConfig()
    client = MulticaClient(config)
    assert hasattr(client, "issues")
    assert hasattr(client, "auth")
    assert hasattr(client, "workspaces")
