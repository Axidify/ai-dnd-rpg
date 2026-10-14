"""Quests finish (and pay out) as soon as their objectives are done."""

import pytest

from api_server import app, game_sessions, record_quest_kill
from combat import create_enemy
from game_mechanics import complete_ready_quests


@pytest.fixture
def session():
    app.config["TESTING"] = True
    with app.test_client() as client:
        sid = client.post("/api/game/start", json={
            "character": {"name": "Quester", "race": "Human", "class": "Fighter"},
            "scenario_id": "goblin_cave",
        }).get_json()["session_id"]
    return game_sessions[sid]


def test_quest_completes_and_pays_out(session):
    qm = session.quest_manager
    assert qm.accept_quest("rescue_lily")
    for target in ("cave_entrance", "tavern_celebration"):
        qm.on_location_entered(target)
    qm.on_npc_talked("lily")
    xp, gold = session.character.experience, session.character.gold

    messages = complete_ready_quests(session)

    assert messages and "Rescue Lily" in messages[0]
    assert "rescue_lily" in qm.completed_quests
    assert session.character.experience == xp + 100
    assert session.character.gold == gold + 50
    # Its follow-up quest (prerequisite: rescue_lily) can now be accepted
    assert qm.accept_quest("recover_heirlooms")


def test_ally_kill_counts_for_quest(session):
    qm = session.quest_manager
    assert qm.accept_quest("chiefs_treasure")
    boss = create_enemy("goblin_boss")
    boss.take_damage(999)  # killed by someone other than the player
    messages = []
    record_quest_kill(session, boss, messages)
    record_quest_kill(session, boss, messages)  # counted once
    objective = next(o for o in qm.get_quest("chiefs_treasure").objectives if o.id == "defeat_chief")
    assert objective.completed and objective.current_count == 1


def test_unaccepted_quests_survive_save_and_load(session):
    app.config["TESTING"] = True
    with app.test_client() as client:
        saved = client.post("/api/game/save", json={"session_id": session.session_id, "slot": 7}).get_json()
        try:
            loaded = client.post("/api/game/load", json={"name": saved["name"]}).get_json()
        finally:
            import os
            os.remove(saved["save_path"])
    restored = game_sessions[loaded["session_id"]].quest_manager
    assert {"rescue_lily", "clear_the_path"} <= set(restored.available_quests)


def test_found_quest_items_are_handed_over(session):
    from inventory import get_item, add_item_to_inventory
    qm = session.quest_manager
    for key in ("silver_locket", "family_ring"):
        add_item_to_inventory(session.character.inventory, get_item(key))
    qm.completed_quests.append("rescue_lily")  # prerequisite
    assert qm.accept_quest("recover_heirlooms")
    for key in ("silver_locket", "family_ring"):
        qm.on_item_acquired(key)
    assert complete_ready_quests(session)
    names = {i.name for i in session.character.inventory}
    assert "Silver Locket" not in names and "Family Ring" not in names
