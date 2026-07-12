from __future__ import annotations

from multica_py.client import MulticaClient
from multica_py.config import ClientConfig


def test_client_construction():
    config = ClientConfig()
    client = MulticaClient(config)
    assert client.config is config
    assert hasattr(client, "issues")
    assert hasattr(client, "auth")


def test_client_context_manager():
    with MulticaClient(ClientConfig()) as client:
        assert client is not None
