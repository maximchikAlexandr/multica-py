from __future__ import annotations

import msgspec

from multica_py.models.agents import Agent
from multica_py.models.autopilots import Autopilot, AutopilotRun
from multica_py.models.issue_activity import MetadataEntry
from multica_py.models.skills import Skill
from multica_py.models.system import AttachmentResult, Repository, RuntimeDefinition

AG = msgspec.json.encode(Agent(id="a1", name="n"))
AP = msgspec.json.encode(Autopilot(id="a1", name="AP"))
APRUN = msgspec.json.encode(AutopilotRun(id="r1", status="running"))
AR = msgspec.json.encode(AttachmentResult(id="a1", filename="f.txt"))
CMT_FLAT = msgspec.json.encode([{"id": "c1", "content": "hello"}])
CMT_THREAD = msgspec.json.encode([{"id": "c1", "content": "reply", "parent_id": "th_1"}])
CMT_RECENT = msgspec.json.encode(
    [{"id": "th_1", "comments": [{"id": "c1", "content": "root comment"}], "resolved": False}]
)
LBL = msgspec.json.encode([{"id": "lbl_1", "name": "bug", "color": "#ff0000"}])
META = msgspec.json.encode([MetadataEntry(key="priority", value="high")])
REPO = msgspec.json.encode(Repository(id="r1", name="repo1"))
RT = msgspec.json.encode(RuntimeDefinition(id="r1", name="py3"))
SK = msgspec.json.encode(Skill(id="s1", name="sk"))
