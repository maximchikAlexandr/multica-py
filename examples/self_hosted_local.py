"""Local self-hosted Multica example using multica-py."""

from datetime import timedelta

from multica_py import ClientConfig, MulticaClient

config = ClientConfig(
    executable="/usr/local/bin/multica",
    server_url="http://localhost:8080",
    workspace_id="ws_local",
    profile="self-hosted",
    timeout=timedelta(seconds=30),
)
client = MulticaClient(config)


def list_projects() -> None:
    for project in client.projects.list():
        print(project.name)


def check_auth() -> None:
    status = client.auth.status()
    print(status.authenticated)


def connect_local_instance() -> None:
    process = client.setup.self_host("http://localhost:8080")
    process.wait()


def main() -> None:
    check_auth()
    list_projects()


if __name__ == "__main__":
    main()
