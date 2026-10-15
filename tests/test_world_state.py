"""World changes (freeing Lily, bringing her home) are decided by the engine."""

import os

import pytest

import api_server
import dm_engine
from api_server import app, game_sessions, refresh_chat_context
from inventory import add_item_to_inventory, get_item
from world_memory import people_view, present_npc_ids, state_briefing
from world_state import match_interaction, on_travel, world


@pytest.fixture
def session():
    app.config["TESTING"] = True
    with app.test_client() as client:
        sid = client.post("/api/game/start", json={
            "character": {"name": "Brenna", "race": "Human", "class": "Fighter"},
            "scenario_id": "goblin_cave",
        }).get_json()["session_id"]
    return game_sessions[sid]


def move(session, location_id):
    session.location_manager.current_location_id = location_id
    session.current_location_id = location_id
    session.current_location = session.location_manager.get_current_location().name


def fixed_roll(monkeypatch, success):
    def roll(character, skill, dc):
        return {"skill": skill, "dc": dc, "roll": 15 if success else 2, "modifier": 0,
                "total": 15 if success else 2, "success": success, "is_nat_20": False, "is_nat_1": False}
    monkeypatch.setattr(dm_engine, "roll_skill_check", roll)


def turn(session, monkeypatch, action, narration="It happens."):
    monkeypatch.setattr(api_server, "get_dm_response", lambda *a, **k: narration)
    with app.test_client() as client:
        return client.post("/api/game/action", json={"session_id": session.session_id, "action": action}).get_json()


def test_captive_is_only_in_her_cage(session):
    assert world(session)["npc_status"]["lily"] == "captive"
    move(session, "goblin_camp_cages")
    assert "lily" in present_npc_ids(session)
    move(session, "cave_exit")  # the YAML lists her there for after the rescue
    assert "lily" not in present_npc_ids(session)


def test_freeing_lily_with_lockpicks(session, monkeypatch):
    move(session, "goblin_camp_cages")
    add_item_to_inventory(session.character.inventory, get_item("lockpicks"))
    fixed_roll(monkeypatch, True)
    body = turn(session, monkeypatch, "I pick the lock on Lily's cage and free her.")
    assert body["roll_result"]["skill"].lower().startswith("sleight")
    state = world(session)
    assert state["npc_status"]["lily"] == "freed" and state["followers"] == ["lily"]
    assert "Lily is with you now." in body["message"]
    assert any("freed Lily" in e for e in session.chronicle)
    objective = next(o for o in session.quest_manager.get_quest("rescue_lily").objectives if o.id == "find_lily")
    assert objective.completed or "rescue_lily" not in [q.id for q in session.quest_manager.get_active_quests()]


def test_failed_attempt_leaves_her_caged(session, monkeypatch):
    move(session, "goblin_camp_cages")
    fixed_roll(monkeypatch, False)
    body = turn(session, monkeypatch, "I break the lock on the cage.")
    assert body["roll_result"]["skill"].lower() == "athletics"  # no lockpicks: brute force
    assert world(session)["npc_status"]["lily"] == "captive"
    assert match_interaction(session, "I try to force the cage again")  # can try again


def test_narrator_is_told_the_outcome(session, monkeypatch):
    move(session, "goblin_camp_cages")
    fixed_roll(monkeypatch, True)
    turn(session, monkeypatch, "I force the cage open.")
    # The facts were consumed by the narration; check the next turn's state instead
    session.dm_chat = object()
    session.turn_premise = None
    update = refresh_chat_context(session)
    assert "WORLD STATE" in update and "Lily: freed, travelling with the hero" in update


def test_hitting_the_lock_is_not_a_brawl(session, monkeypatch):
    move(session, "goblin_camp_cages")
    fixed_roll(monkeypatch, False)
    turn(session, monkeypatch, "I hit the lock with my sword to free her.")
    assert not session.in_combat


def test_followers_travel_with_the_hero(session, monkeypatch):
    move(session, "goblin_camp_cages")
    fixed_roll(monkeypatch, True)
    turn(session, monkeypatch, "I free Lily.")
    move(session, "goblin_camp_main")
    on_travel(session)  # what process_travel does after every move
    assert "lily" in present_npc_ids(session)
    assert session.npc_manager.get_npc("lily").location_id == "goblin_camp_main"


def test_bringing_lily_home(session, monkeypatch):
    move(session, "tavern_celebration")
    body = turn(session, monkeypatch, "I bring Lily to Bram.")
    assert world(session)["npc_status"]["lily"] == "captive"  # she isn't with the hero
    move(session, "goblin_camp_cages")
    fixed_roll(monkeypatch, True)
    turn(session, monkeypatch, "I free Lily.")
    move(session, "tavern_celebration")
    body = turn(session, monkeypatch, "I bring Lily to her father.")
    state = world(session)
    assert state["npc_status"]["lily"] == "home" and state["followers"] == []
    assert "lily" in present_npc_ids(session)
    assert any("Brought his daughter Lily home" in m for m in session.npc_manager.get_npc("bram").memories)
    assert body["success"]


def test_world_state_survives_save_and_load(session, monkeypatch):
    move(session, "goblin_camp_cages")
    fixed_roll(monkeypatch, True)
    turn(session, monkeypatch, "I free Lily.")
    with app.test_client() as client:
        saved = client.post("/api/game/save", json={"session_id": session.session_id, "slot": 5}).get_json()
        try:
            loaded = client.post("/api/game/load", json={"name": saved["name"]}).get_json()
        finally:
            os.remove(saved["save_path"])
    restored = game_sessions[loaded["session_id"]]
    assert world(restored)["followers"] == ["lily"]
    assert "lily" in present_npc_ids(restored)
    assert "Lily: freed" in state_briefing(restored)


def test_people_panel_shows_status(session, monkeypatch):
    move(session, "goblin_camp_cages")
    lily = next(p for p in people_view(session) if p["id"] == "lily")
    assert lily["status"] == "Captive"
    fixed_roll(monkeypatch, True)
    turn(session, monkeypatch, "I free Lily.")
    lily = next(p for p in people_view(session) if p["id"] == "lily")
    assert lily["status"] == "With you"


def test_travel_moves_followers(session, monkeypatch):
    from game_mechanics import process_travel
    world(session)["followers"].append("lily")
    process_travel(session, "outside")
    assert session.current_location_id == "village_square"
    assert "lily" in present_npc_ids(session)


def test_lockpicks_count_when_carried(session):
    from world_model import analyze_action, carries
    add_item_to_inventory(session.character.inventory, get_item("lockpicks"))
    assert carries(session, "lockpicks")
    move(session, "goblin_camp_cages")
    assert not any("no lockpicks" in f for f in analyze_action(session, "I pick the lock.").facts)
