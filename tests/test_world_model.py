"""The engine is the source of truth: premises are checked, grants validated.

Cases come from the consistency eval (tests/live/consistency_eval.py), where
the narrator went along with whatever the player's action assumed.
"""

import pytest

import api_server
from api_server import app, game_sessions, refresh_chat_context
from world_model import analyze_action, claim_item, grantable, grants_briefing


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


def turn(session, monkeypatch, action, narration="Nothing happens."):
    monkeypatch.setattr(api_server, "get_dm_response", lambda *a, **k: narration)
    with app.test_client() as client:
        return client.post("/api/game/action", json={"session_id": session.session_id, "action": action}).get_json()


# --- step 1: premise check ----------------------------------------------------

def test_absent_person_is_flagged_and_not_rolled(session):
    move(session, "cave_tunnel")
    premise = analyze_action(session, "I pick the lock on Lily's cage and free her.")
    assert "Lily is NOT here." in premise.facts
    assert premise.blocks_roll


def test_present_person_is_fine(session):
    premise = analyze_action(session, "I ask Bram what happened to his daughter.")
    assert "bram" in premise.refs["present"]
    assert not premise.blocks_roll  # Lily is only a topic; Bram is right here


def test_aliases_resolve_people(session):
    premise = analyze_action(session, "I walk over to the worried old farmer.")
    assert "bram" in premise.refs["present"]


def test_living_goblins_are_not_bodies(session):
    move(session, "goblin_camp_main")
    premise = analyze_action(session, "I check the fallen goblins. Is any of them still moving?")
    assert any("ALIVE" in f for f in premise.facts)
    assert premise.blocks_roll


def test_dead_after_victory(session):
    move(session, "boss_chamber")
    session.location_manager.get_current_location().encounter_defeated = True
    premise = analyze_action(session, "I ask the goblin chief where he hid his treasure.")
    assert any("dead" in f for f in premise.facts)


def test_absent_chief_cannot_answer(session):
    move(session, "goblin_camp_entrance")
    premise = analyze_action(session, "I ask the goblin chief where he hid his treasure.")
    assert "Chief Grotnak is NOT here." in premise.facts and premise.blocks_roll


def test_items_not_here_cannot_be_taken(session):
    move(session, "goblin_camp_main")
    premise = analyze_action(session, "I take the silver locket and the family ring.")
    assert any("silver locket" in f.lower() for f in premise.facts)
    assert premise.blocks_roll


def test_item_lying_here_is_fine(session):
    premise = analyze_action(session, "I take the torch from the table.")
    assert "torch" in premise.refs["present"] and not premise.blocks_roll


@pytest.mark.parametrize("action", [
    "I drink my potion of giant strength.",
    "I draw my enchanted greatsword and show it to Bram.",
])
def test_claimed_possessions_are_checked(session, action):
    premise = analyze_action(session, action)
    assert any("does NOT have" in f for f in premise.facts)
    assert premise.blocks_roll


@pytest.mark.parametrize("action", [
    "I swear on my sword that I will bring her home.",
    "I light my torch and peer into the darkness.",
    "I give my word to Bram.",
])
def test_real_possessions_and_figures_of_speech_pass(session, action):
    premise = analyze_action(session, action)
    assert not any("does NOT have" in f for f in premise.facts)


def test_facts_reach_the_narrator_and_skip_the_roll(session, monkeypatch):
    move(session, "village_square")
    body = turn(session, monkeypatch, "I pick the lock on Lily's cage and free her.")
    assert body["roll_result"] is None  # nothing real to roll against
    session.dm_chat = object()  # a chat exists, so the next refresh returns text
    session.turn_premise = analyze_action(session, "I free Lily.")
    update = refresh_chat_context(session)
    assert "[ENGINE CHECK" in update and "Lily is NOT here." in update
    assert session.turn_premise is None  # used once


# --- step 2: engine-owned grants ---------------------------------------------

def test_item_tag_for_something_that_isnt_here_is_rejected(session, monkeypatch):
    move(session, "cave_tunnel")
    before = len(session.character.inventory)
    body = turn(session, monkeypatch, "I search the walls.",
                "Lily hands you a silver locket. [ITEM: silver_locket]")
    assert body["items_gained"] == []
    assert len(session.character.inventory) == before
    assert any("did NOT receive" in n for n in session.dm_notes)


def test_npc_gift_works_once(session):
    bram = session.npc_manager.get_npc("bram")
    session.location_manager.get_current_location().items.remove("torch")  # only Bram's torch remains
    assert grantable(session) == {"torch": "bram"}
    assert claim_item(session, "torch") == (True, "torch")
    assert bram.gifts == []
    assert claim_item(session, "torch") == (False, "torch")


def test_gifts_are_used_before_items_lying_here(session):
    here = session.location_manager.get_current_location()
    assert claim_item(session, "torch")[0]  # Bram's spare torch...
    assert "torch" in here.items             # ...so the one on the table is still there to take
    assert claim_item(session, "torch")[0]
    assert "torch" not in here.items


def test_taking_needs_the_item_lying_here(session):
    session.location_manager.get_current_location().items.remove("torch")
    premise = analyze_action(session, "I take the torch from the table.")
    assert any("no Torch here to take" in f for f in premise.facts)


def test_narrated_gold_and_xp_are_rejected(session, monkeypatch):
    gold, xp = session.character.gold, session.character.experience
    body = turn(session, monkeypatch, "I thank Bram.",
                "He beams. [GOLD: 50] [XP: 100 | rescue]")
    assert body["gold_gained"] == 0 and body["xp_gained"] == 0
    assert (session.character.gold, session.character.experience) == (gold, xp)


def test_buy_needs_a_merchant_here(session, monkeypatch):
    session.character.gold = 500
    turn(session, monkeypatch, "I buy a longsword.", "Done. [BUY: longsword, 15]")
    assert session.character.gold == 500  # no merchant in the tavern
    move(session, "blacksmith_shop")
    turn(session, monkeypatch, "I buy a longsword for 1 gold.", "Done. [BUY: longsword, 1]")
    assert session.character.gold == 500  # Gavin is here, but 1 gold isn't a fair price


def test_recruit_needs_the_npc_here(session, monkeypatch):
    move(session, "village_square")
    body = turn(session, monkeypatch, "Marcus, join me.", "He joins you. [RECRUIT: marcus]")
    assert body["game_state"]["party"] == []


def test_absent_npcs_cannot_remember(session, monkeypatch):
    move(session, "cave_entrance")
    turn(session, monkeypatch, "I think of Bram.",
         "[REMEMBER: bram | Brenna safely rescued Lily] [ATTITUDE: bram | +10 | rescue]")
    bram = session.npc_manager.get_npc("bram")
    assert not any("rescued" in m for m in bram.memories)


def test_briefing_lists_only_what_exists(session):
    text = grants_briefing(session)
    assert "torch" in text and "Gold and XP are awarded by the game" in text
    move(session, "cave_tunnel")
    assert "none here" in grants_briefing(session)


def test_defeated_encounter_survives_save_and_load(session):
    move(session, "goblin_camp_main")
    session.location_manager.get_current_location().encounter_defeated = True
    with app.test_client() as client:
        saved = client.post("/api/game/save", json={"session_id": session.session_id, "slot": 6}).get_json()
        try:
            loaded = client.post("/api/game/load", json={"name": saved["name"]}).get_json()
        finally:
            import os
            os.remove(saved["save_path"])
    restored = game_sessions[loaded["session_id"]]
    assert restored.location_manager.locations["goblin_camp_main"].encounter_defeated


def test_picking_a_lock_needs_lockpicks(session):
    move(session, "goblin_camp_cages")
    premise = analyze_action(session, "I pick the lock on Lily's cage.")
    assert any("no lockpicks" in f for f in premise.facts)
    assert "lily" in premise.refs["present"]  # Lily is here; only the tool is missing


def test_failed_examine_roll_does_not_block_pickup(session, monkeypatch):
    from turn_service import _apply_pickups
    move(session, "darkhollow_approach")
    events = []
    picked = _apply_pickups(session, "I pick up the goblin ear and examine it",
                            {"skill": "Investigation", "success": False}, events, lambda t: None)
    assert picked == {"Goblin Ear"}
    move(session, "goblin_camp_main")
    picked = _apply_pickups(session, "I quietly take the shortsword",
                            {"skill": "Sleight_of_Hand", "success": False}, [], lambda t: None)
    assert picked == set()


# --- fights only against enemies that exist ----------------------------------

def test_defeated_boss_is_not_fought_again(session):
    from game_mechanics import try_hostile_combat_gate
    move(session, "boss_chamber")
    here = session.location_manager.get_current_location()
    here.encounter_triggered = here.encounter_defeated = True
    assert try_hostile_combat_gate(session, "I charge at Chief Grotnak with my longsword!") is None
    assert not session.in_combat


def test_monsters_are_not_conjured(session):
    from game_mechanics import try_hostile_combat_gate
    move(session, "village_square")
    assert try_hostile_combat_gate(session, "I attack the goblin chief!") is None
    assert try_hostile_combat_gate(session, "I punch the villager") is None  # nobody here to brawl with


def test_brawl_needs_someone_present(session):
    from game_mechanics import try_hostile_combat_gate
    assert try_hostile_combat_gate(session, "I punch the barkeep") is not None


def test_fixed_encounter_still_fights_the_whole_group(session):
    from game_mechanics import try_hostile_combat_gate
    move(session, "goblin_camp_main")
    result = try_hostile_combat_gate(session, "I draw my longsword and attack the goblins!")
    assert result["enemies"] == ["goblin", "goblin", "goblin", "goblin"]


def test_narrator_cannot_conjure_a_fight(session, monkeypatch):
    move(session, "cave_tunnel")
    turn(session, monkeypatch, "I listen.", "A wolf leaps at you! [COMBAT: wolf]")
    assert not session.in_combat
    assert any("No fight started" in n for n in session.dm_notes)


def test_looting_takes_what_lies_here(session):
    from turn_service import _apply_pickups
    move(session, "goblin_camp_main")
    picked = _apply_pickups(session, "I loot the camp.", None, [], lambda t: None)
    assert {"Shortsword", "Rations", "Healing Potion"} <= picked


def test_talking_counts_only_for_npcs_who_are_here(session):
    from world_model import npcs_addressed
    move(session, "goblin_camp_cages")
    assert npcs_addressed(session, 'I say: "Lily, your father sent me. We\'re going home."') == ["lily"]
    assert npcs_addressed(session, "I comfort the girl and promise to get her out.") == ["lily"]
    assert npcs_addressed(session, "I pick the lock.") == []
    move(session, "cave_tunnel")
    assert npcs_addressed(session, "I call out to Lily.") == []  # she isn't here


def test_rescue_quest_progresses_when_speaking_to_lily(session, monkeypatch):
    qm = session.quest_manager
    assert qm.accept_quest("rescue_lily")
    move(session, "goblin_camp_cages")
    turn(session, monkeypatch, 'I say: "Lily, your father sent me."', "Lily sobs with relief.")
    objective = next(o for o in qm.get_quest("rescue_lily").objectives if o.id == "find_lily")
    assert objective.completed


# --- step 3: narrate from facts ----------------------------------------------

def capture_narrator_facts(session, monkeypatch, action, narration="You do it."):
    seen = {}

    def fake(sess, *a, **k):
        seen["facts"] = list(sess.turn_premise.facts) if sess.turn_premise else []
        return narration
    monkeypatch.setattr(api_server, "get_dm_response", fake)
    with app.test_client() as client:
        body = client.post("/api/game/action", json={"session_id": session.session_id, "action": action}).get_json()
    return body, seen["facts"]


def test_pickup_happens_before_narration_and_narrator_is_told(session, monkeypatch):
    move(session, "darkhollow_approach")
    body, facts = capture_narrator_facts(session, monkeypatch, "I pick up the goblin ear.")
    assert any("took Goblin Ear and now carries it" in f for f in facts)
    assert any(i.name == "Goblin Ear" for i in session.character.inventory)
    assert body["message"].count("You take: Goblin Ear") == 1  # shown once, after the narration


def test_nothing_to_tell_when_nothing_happened(session, monkeypatch):
    _, facts = capture_narrator_facts(session, monkeypatch, "I hum a tune.")
    assert not any("ALREADY HAPPENED" in f for f in facts)
