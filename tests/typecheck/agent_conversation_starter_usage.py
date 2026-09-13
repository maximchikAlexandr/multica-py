from typing import assert_type, cast

from multica_py._internal.commands import Command
from multica_py.entities.agents import Agent
from multica_py.models.agents import AgentConversationStarter
from multica_py.resources.agents import AgentResource

resource = cast("AgentResource", object())
starter = AgentConversationStarter(label="Review", prompt="Review this")
starters = (starter,)

assert_type(resource.create(name="agent", conversation_starters=starters), Agent)
assert_type(
    resource.create_command(name="agent", conversation_starters=starters),
    Command[Agent],
)
assert_type(resource.update("a1", conversation_starters=starters), Agent)
assert_type(resource.update_command("a1", conversation_starters=starters), Command[Agent])
