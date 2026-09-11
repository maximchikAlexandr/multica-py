from typing import assert_type, cast

from multica_py._internal.commands import Command
from multica_py.entities.autopilots import Autopilot
from multica_py.models.autopilots import AutopilotTrigger
from multica_py.resources.autopilots import AutopilotResource

resource = cast("AutopilotResource", object())
bound = cast("Autopilot", object())

assert_type(
    resource.trigger_add(
        "a1", cron_expression="*/30 * * * *", timezone="Europe/Minsk", label="half-hour"
    ),
    AutopilotTrigger,
)
assert_type(
    resource.trigger_add_command(
        "a1", cron_expression="*/30 * * * *", timezone="Europe/Minsk", label="half-hour"
    ),
    Command[AutopilotTrigger],
)
assert_type(
    resource.trigger_update("a1", "tr1", cron_expression="0 */3 * * *", enabled=False),
    AutopilotTrigger,
)
assert_type(
    resource.trigger_update_command("a1", "tr1", cron_expression="0 */3 * * *", enabled=True),
    Command[AutopilotTrigger],
)
assert_type(
    bound.trigger_add(cron_expression="*/30 * * * *", timezone="Europe/Minsk", label="half-hour"),
    AutopilotTrigger,
)
assert_type(
    bound.trigger_add_command(
        cron_expression="*/30 * * * *", timezone="Europe/Minsk", label="half-hour"
    ),
    Command[AutopilotTrigger],
)
assert_type(
    bound.trigger_update("tr1", cron_expression="0 */3 * * *", enabled=False), AutopilotTrigger
)
assert_type(
    bound.trigger_update_command("tr1", cron_expression="0 */3 * * *", enabled=True),
    Command[AutopilotTrigger],
)
