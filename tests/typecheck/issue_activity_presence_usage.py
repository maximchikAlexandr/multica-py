from typing import assert_type

from multica_py.entities.issues import TaskRun
from multica_py.models.agents import AgentTask
from multica_py.models.issue_activity import IssueUsage, RunMessage, TaskCancellationActor

actor = TaskCancellationActor(type="system", id="actor-1")
run = TaskRun(id="run-1", status="cancelled", cancelled_by=actor)
task = AgentTask(id="run-1", status="cancelled", issue_id="issue-1", cancelled_by=actor)
message = RunMessage(task_id="run-1", seq=1, type="tool_result", output_truncated=True)
usage = IssueUsage(
    task_count=1,
    terminal_task_count=2,
    metered_task_count=1,
    unreported_task_count=0,
)

assert_type(run.cancelled_by, TaskCancellationActor | None)
assert_type(task.cancelled_by, TaskCancellationActor | None)
assert_type(message.output_truncated, bool | None)
assert_type(usage.terminal_task_count, int | None)
