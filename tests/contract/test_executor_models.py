from __future__ import annotations

import datetime

import pytest

from multica_py._internal.decoders import decode_json
from multica_py.models.agents import Agent, AgentSkill
from multica_py.models.system import Squad, SquadMember


@pytest.mark.parametrize(
    ("model_type", "json_bytes", "expected_field", "expected_value"),
    [
        (
            Agent,
            b'{"id":"a1","name":"n","skills":[{"id":"sk_1","name":"openspec-propose","enabled":true}]}',
            "skills",
            (AgentSkill(id="sk_1", name="openspec-propose", enabled=True),),
        ),
        (
            Agent,
            b'{"id":"a1","name":"n","skills":[],"archived_at":null}',
            "archived_at",
            None,
        ),
        (
            Agent,
            b'{"id":"a1","name":"n","archived_at":"2026-07-28T11:47:17Z"}',
            "archived_at",
            datetime.datetime(2026, 7, 28, 11, 47, 17, tzinfo=datetime.UTC),
        ),
        (
            Agent,
            b'{"id":"a1","name":"n"}',
            "skills",
            (),
        ),
        (
            Squad,
            b'{"id":"s1","name":"S","leader_id":"leader-1"}',
            "leader_id",
            "leader-1",
        ),
        (
            Squad,
            b'{"id":"s1","name":"S","leader_id":null}',
            "leader_id",
            None,
        ),
        (
            Squad,
            b'{"id":"s1","name":"S","archived_at":null}',
            "archived_at",
            None,
        ),
        (
            Squad,
            b'{"id":"s1","name":"S","archived_at":"2026-07-28T11:47:17Z"}',
            "archived_at",
            datetime.datetime(2026, 7, 28, 11, 47, 17, tzinfo=datetime.UTC),
        ),
        (
            Squad,
            b'{"id":"s1","name":"S","member_count":0}',
            "leader_id",
            None,
        ),
    ],
)
def test_executor_field_decoding(
    model_type: type,
    json_bytes: bytes,
    expected_field: str,
    expected_value: object,
) -> None:
    result: object = decode_json(json_bytes, model_type, command="test")
    val = getattr(result, expected_field)
    assert val == expected_value


_SKILLS_JSON = b'[{"id":"sk_1","name":"openspec-propose","enabled":true}]'
_SQUAD_MEMBERS_JSON = (
    b'[{"member_id":"a1","member_type":"agent","role":"architecture-reviewer"},'
    b'{"member_id":"u1","member_type":"member","role":"reviewer"}]'
)
_SINGLE_MEMBER_JSON = b'[{"member_id":"a1","member_type":"agent","role":"architecture-reviewer"}]'


@pytest.mark.parametrize(
    ("json_bytes", "expected"),
    [
        (
            _SQUAD_MEMBERS_JSON,
            (
                SquadMember(member_id="a1", member_type="agent", role="architecture-reviewer"),
                SquadMember(member_id="u1", member_type="member", role="reviewer"),
            ),
        ),
        (
            _SINGLE_MEMBER_JSON,
            (SquadMember(member_id="a1", member_type="agent", role="architecture-reviewer"),),
        ),
    ],
)
def test_squad_member_decoding(json_bytes: bytes, expected: tuple[SquadMember, ...]) -> None:
    members = decode_json(json_bytes, list[SquadMember], command="test")
    assert tuple(members) == expected


@pytest.mark.parametrize(
    ("json_bytes", "expected"),
    [
        (_SKILLS_JSON, (AgentSkill(id="sk_1", name="openspec-propose", enabled=True),)),
    ],
)
def test_agent_skill_list_decoding(json_bytes: bytes, expected: tuple[AgentSkill, ...]) -> None:
    skills = decode_json(json_bytes, list[AgentSkill], command="test")
    assert tuple(skills) == expected
