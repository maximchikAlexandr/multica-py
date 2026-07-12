from __future__ import annotations

from multica_py.client import MulticaClient
from multica_py.config import ClientConfig


def test_clone_with_overrides():
    """Prove cloned clients have isolated config."""
    config = ClientConfig(server_url="https://original.com", workspace_id="ws_001")
    client = MulticaClient(config)
    cloned = client.with_workspace("ws_002")
    assert cloned.config.workspace_id == "ws_002"
    assert cloned.config.server_url == "https://original.com"


def test_two_clients_different_workspaces():
    """Prove two clients can have different workspaces without interference."""
    config_a = ClientConfig(workspace_id="ws_a")
    config_b = ClientConfig(workspace_id="ws_b")
    client_a = MulticaClient(config_a)
    client_b = MulticaClient(config_b)
    assert client_a.config.workspace_id == "ws_a"
    assert client_b.config.workspace_id == "ws_b"


def test_client_environment_isolation():
    """Prove clients have independent environment dictionaries."""
    env_a = (("MULTICA_TOKEN", "token_a"),)
    env_b = (("MULTICA_TOKEN", "token_b"),)
    client_a = MulticaClient(ClientConfig(environment=env_a))
    client_b = MulticaClient(ClientConfig(environment=env_b))
    env_a_items = dict(client_a.config.environment)
    env_b_items = dict(client_b.config.environment)
    assert env_a_items["MULTICA_TOKEN"] == "token_a"
    assert env_b_items["MULTICA_TOKEN"] == "token_b"
