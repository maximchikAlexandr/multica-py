# Service Usage Patterns

## FastAPI

```python
from datetime import timedelta

from fastapi import FastAPI
from multica_py import MulticaClient, ClientConfig

app = FastAPI()
config = ClientConfig(timeout=timedelta(seconds=30))
client = MulticaClient(config)

@app.get("/issues")
def list_issues():
    return [i.title for i in client.issues.list()]
```

## Temporal Activity

```python
from datetime import timedelta

from temporalio import activity
from multica_py import ClientConfig, MulticaClient
from multica_py.models.issues import IssueCreateRequest

@activity.defn
async def create_issue(title: str) -> dict:
    client = MulticaClient(ClientConfig(timeout=timedelta(seconds=60)))
    issue = client.issues.create(IssueCreateRequest(title=title))
    return {"id": issue.id, "title": issue.title}
```

## Local Self-Hosted Deployment

```python
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

status = client.auth.status()
print(status.authenticated)

for project in client.projects.list():
    print(project.name)
```

Interactive first-time local setup is still a process-backed CLI flow:

```python
process = client.setup.self_host("http://localhost:8080")
process.wait()
```
