"""
Integration tests for recent API fixes (save/load, combat block, mechanics).
Uses Flask test client — no live server or AI calls required.
"""

import json
import os
import sys
import uuid

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from api_server import app, game_sessions, GameSession
from character import Character
from party import Party
from quest import QuestManager
from scenario import ScenarioManager, LocationManager
from npc import NPCManager
from game_mechanics import (
    get_class_hit_die,
    is_thin_legacy_save,
    serialize_session_state,
    restore_session_state,
    skill_check_modifier,
)
from dm_engine import SKILL_ABILITIES


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def session_with_character():
    """Create a game session directly (avoids AI on /game/start)."""
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


def test_combat_blocks_narrative_action(client, session_with_character):
    sid = session_with_character
    session = game_sessions[sid]
    session.in_combat = True
    session.combat_state = {"enemies": ["goblin"], "round": 1, "surprise": False}

    resp = client.post(
        "/api/game/action",
        json={"session_id": sid, "action": "I sneak past the guards"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert "Combat is underway" in body["message"]
    assert body["game_state"]["in_combat"] is True


def test_combat_blocks_streaming_action(client, session_with_character):
    sid = session_with_character
    session = game_sessions[sid]
    session.in_combat = True
    session.combat_state = {"enemies": ["goblin"], "round": 1, "surprise": False}

    resp = client.post(
        "/api/game/action/stream",
        json={"session_id": sid, "action": "I cast fireball"},
    )
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    assert "Combat is underway" in text
    assert "done" in text


def test_save_load_roundtrip(client, session_with_character, monkeypatch, tmp_path):
    sid = session_with_character
    session = game_sessions[sid]
    session.current_location = "Goblin Cave"
    session.current_location_id = "goblin_cave"
    session.character.gold = 42

    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()
    real_join = os.path.join

    def patched_join(*parts):
        if len(parts) >= 2 and parts[-1] == "saves" and ".." in parts:
            return str(saves_dir)
        return real_join(*parts)

    import api_server as api_mod

    monkeypatch.setattr(api_mod.os.path, "join", patched_join)

    save_resp = client.post(
        "/api/game/save",
        json={"session_id": sid, "slot": 1, "description": "test save"},
    )
    assert save_resp.status_code == 200
    save_data = save_resp.get_json()
    assert save_data["success"] is True
    assert "save_" in save_data["name"]

    load_resp = client.post(
        "/api/game/load",
        json={"name": save_data["name"]},
    )
    assert load_resp.status_code == 200
    load_body = load_resp.get_json()
    gs = load_body["game_state"]
    assert gs["character"]["name"] == "TestHero"
    assert gs["character"]["gold"] == 42
    assert gs["current_location"] == "Goblin Cave"
    assert load_body["session_id"] != sid


def test_legacy_thin_save_detection():
    assert is_thin_legacy_save({"character": {"name": "x"}}) is True
    assert is_thin_legacy_save({"version": "2.0", "character": {}}) is False


def test_class_hit_die_and_proficiency():
    fighter = Character(name="F", race="Human", char_class="Fighter")
    wizard = Character(name="W", race="Human", char_class="Wizard")
    assert get_class_hit_die("Fighter") == 10
    assert get_class_hit_die("Wizard") == 6
    fighter_mod = skill_check_modifier(fighter, "athletics", SKILL_ABILITIES)
    wizard_mod = skill_check_modifier(wizard, "athletics", SKILL_ABILITIES)
    assert fighter_mod > wizard_mod


def test_session_state_serialize_restore():
    session = GameSession("test-sid")
    session.character = Character(name="H", race="Human", char_class="Rogue")
    session.in_combat = True
    session.combat_state = {"enemies": ["rat"], "round": 2}
    session.game_over = False
    session.current_location = "Tavern"

    blob = serialize_session_state(session)
    session2 = GameSession("other")
    restore_session_state(session2, blob)
    assert session2.in_combat is True
    assert session2.combat_state["round"] == 2
    assert session2.current_location == "Tavern"


def test_short_rest_uses_class_hit_die(client, session_with_character):
    sid = session_with_character
    session = game_sessions[sid]
    session.character.current_hp = 5
    session.combat_state = {"hit_dice_remaining": 2}

    resp = client.post(
        "/api/character/rest",
        json={"session_id": sid, "type": "short"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["new_hp"] > 5
