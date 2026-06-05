"""
Integration tests for HP defeat, hostile combat gate, quest complete, travel pipeline.
"""

import os
import sys
import uuid

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from api_server import app, game_sessions, GameSession
from character import Character
from party import Party
from quest import QuestManager, Quest, QuestObjective, QuestStatus, ObjectiveType
from scenario import ScenarioManager, LocationManager
from npc import NPCManager
from game_mechanics import (
    apply_player_damage,
    on_player_defeat,
    is_session_blocked,
    try_hostile_combat_gate,
    process_travel,
)


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def session_with_character():
    sid = str(uuid.uuid4())
    session = GameSession(sid)
    session.character = Character(name="TestHero", race="Human", char_class="Fighter")
    session.character._add_starting_equipment()
    session.scenario = ScenarioManager()
    session.npc_manager = NPCManager()
    session.quest_manager = QuestManager()
    session.party = Party()
    session.location_manager = LocationManager()
    session.current_location = "Village Square"
    game_sessions[sid] = session
    yield sid
    game_sessions.pop(sid, None)


def test_hp_zero_sets_game_over(session_with_character):
    session = game_sessions[session_with_character]
    session.character.current_hp = 5
    _, defeated = apply_player_damage(session, 10, "goblin")
    assert defeated is True
    assert session.game_over is True
    assert session.character.current_hp == 0
    blocked, _ = is_session_blocked(session)
    assert blocked is True


def test_rest_blocked_at_game_over(client, session_with_character):
    session = game_sessions[session_with_character]
    on_player_defeat(session)
    resp = client.post(
        "/api/character/rest",
        json={"session_id": session_with_character, "type": "short"},
    )
    body = resp.get_json()
    assert body["success"] is False
    assert body.get("game_over") is True


def test_hostile_action_starts_combat(client, session_with_character):
    sid = session_with_character
    resp = client.post(
        "/api/game/action",
        json={"session_id": sid, "action": "I attack the blacksmith"},
    )
    body = resp.get_json()
    assert body["success"] is True
    assert body.get("combat_started") is True
    assert game_sessions[sid].in_combat is True


def test_quest_complete_uses_manager(client, session_with_character):
    sid = session_with_character
    session = game_sessions[sid]
    quest = Quest(
        id="test_quest",
        name="Test Quest",
        description="Do the thing",
        status=QuestStatus.ACTIVE,
        objectives=[
            QuestObjective(
                id="obj1",
                description="Kill rat",
                objective_type=ObjectiveType.KILL,
                target="rat",
                completed=True,
            )
        ],
        rewards={"xp": 10, "gold": 5, "items": []},
    )
    session.quest_manager.active_quests["test_quest"] = quest

    resp = client.post(
        "/api/quests/complete",
        json={"session_id": sid, "quest_id": "test_quest"},
    )
    body = resp.get_json()
    assert body["success"] is True
    assert "test_quest" in session.quest_manager.completed_quests
    assert "test_quest" not in session.quest_manager.active_quests
    assert body["rewards"]["xp"] == 10


def test_action_blocked_after_game_over(client, session_with_character):
    sid = session_with_character
    session = game_sessions[sid]
    on_player_defeat(session)
    resp = client.post(
        "/api/game/action",
        json={"session_id": sid, "action": "I look around"},
    )
    body = resp.get_json()
    assert body.get("game_over") is True


def test_try_hostile_combat_gate_unit(session_with_character):
    session = game_sessions[session_with_character]
    result = try_hostile_combat_gate(session, "I punch the villager")
    assert result is not None
    assert session.in_combat is True


def test_process_travel_free_mode(session_with_character):
    session = game_sessions[session_with_character]
    session.location_manager = None
    result = process_travel(session, "tavern")
    assert result["success"] is True
    assert "Tavern" in result["new_location"]
