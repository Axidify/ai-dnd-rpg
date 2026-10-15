"""The GM sees the canonical state, and NPC memory/attitude/chronicle persist."""

import os

import pytest

import api_server
from api_server import app, game_sessions, refresh_chat_context
from dm_engine import StreamTagFilter, strip_dm_tags
from game_mechanics import complete_ready_quests
from world_memory import (
    MAX_ATTITUDE_STEP,
    MAX_NPC_MEMORIES,
    apply_memory_tags,
    chronicle,
    remember,
    resolve_npc,
    state_briefing,
)


@pytest.fixture
def session():
    app.config["TESTING"] = True
    with app.test_client() as client:
        sid = client.post("/api/game/start", json={
            "character": {"name": "Brenna", "race": "Human", "class": "Fighter"},
            "scenario_id": "goblin_cave",
        }).get_json()["session_id"]
    return game_sessions[sid]


def _save_and_load(session):
    with app.test_client() as client:
        saved = client.post("/api/game/save", json={"session_id": session.session_id, "slot": 8}).get_json()
        try:
            loaded = client.post("/api/game/load", json={"name": saved["name"]}).get_json()
        finally:
            os.remove(saved["save_path"])
    return game_sessions[loaded["session_id"]]


# --- the briefing ---------------------------------------------------------

def test_briefing_has_full_character_state(session):
    text = state_briefing(session)
    c = session.character
    assert f"HP {c.current_hp}/{c.max_hp}" in text
    assert f"XP {c.experience}" in text
    assert "Carrying ONLY:" in text
    assert c.weapon in text


def test_briefing_details_present_npcs_and_lists_others(session):
    text = state_briefing(session)
    # The tavern NPCs are here: personality and ids are shown
    assert "NPCS HERE" in text and "[id: bram]" in text
    assert "PERSONALITY" in text
    # Others are listed briefly so the GM can't invent new named characters
    assert "OTHER KNOWN NPCS" in text and "[id: lily]" in text


def test_briefing_shows_objective_status(session):
    qm = session.quest_manager
    assert qm.accept_quest("rescue_lily")
    qm.on_location_entered("cave_entrance")
    text = state_briefing(session)
    assert "ACTIVE QUESTS" in text and "[x]" in text and "[ ]" in text


def test_context_update_carries_briefing_and_chronicles_notes(session, monkeypatch):
    session.dm_chat = object()  # pretend a chat exists so we get the update text
    session.dm_notes.append("The party killed: Goblin Boss. They stay dead.")
    update = refresh_chat_context(session)
    assert "Carrying ONLY:" in update and "NPCS HERE" in update
    assert "Goblin Boss" in update
    # The note became a permanent fact
    assert any("Goblin Boss" in e for e in session.chronicle)
    assert "Goblin Boss" in state_briefing(session)


# --- tags -------------------------------------------------------------------

def test_remember_and_attitude_tags_apply(session):
    bram = session.npc_manager.get_npc("bram")
    before = bram.disposition
    events = apply_memory_tags(session, (
        "Bram grips your hand. [REMEMBER: bram | Promised to bring Lily home] "
        "[ATTITUDE: Bram | +40 | she agreed to help]"
    ))
    assert "Promised to bring Lily home." in bram.memories
    assert bram.disposition == min(100, before + MAX_ATTITUDE_STEP)  # clamped
    assert {e["type"] for e in events} == {"npc_memory", "npc_attitude"}


def test_tags_for_unknown_npcs_are_ignored(session):
    assert apply_memory_tags(session, "[REMEMBER: gandolfo | knows a secret] [ATTITUDE: nobody | -5 | x]") == []


def test_memories_are_capped_and_deduplicated(session):
    bram = session.npc_manager.get_npc("bram")
    assert remember(bram, "Fact one")
    assert not remember(bram, "fact one.")
    for i in range(MAX_NPC_MEMORIES + 5):
        remember(bram, f"Fact number {i}")
    assert len(bram.memories) == MAX_NPC_MEMORIES
    assert bram.memories[-1] == f"Fact number {MAX_NPC_MEMORIES + 4}."


def test_resolve_npc_by_id_name_or_distinctive_word(session):
    manager = session.npc_manager
    assert resolve_npc(manager, "bram").id == "bram"
    bram = manager.get_npc("bram")
    assert resolve_npc(manager, bram.name).id == "bram"
    assert resolve_npc(manager, "the dragon") is None


def test_memory_tags_are_hidden_from_the_player():
    text = "He nods. [REMEMBER: bram | x] [ATTITUDE: bram | +5 | y]Done."
    assert "[" not in strip_dm_tags(text)
    f = StreamTagFilter()
    shown = f.feed(text[:20]) + f.feed(text[20:45]) + f.feed(text[45:]) + f.flush()
    assert "REMEMBER" not in shown and "ATTITUDE" not in shown and "Done." in shown


def test_turn_applies_memory_tags_and_hides_them(session, monkeypatch):
    monkeypatch.setattr(api_server, "get_dm_response",
                        lambda *a, **k: "Bram's eyes fill. [REMEMBER: bram | Swore to find Lily]")
    with app.test_client() as client:
        body = client.post("/api/game/action", json={
            "session_id": session.session_id, "action": "I promise Bram I'll find Lily"}).get_json()
    assert "REMEMBER" not in body["message"]
    assert "Swore to find Lily." in session.npc_manager.get_npc("bram").memories


# --- automatic memories -----------------------------------------------------

def test_quest_completion_is_remembered_and_chronicled(session):
    qm = session.quest_manager
    assert qm.accept_quest("rescue_lily")
    for target in ("cave_entrance", "tavern_celebration"):
        qm.on_location_entered(target)
    qm.on_npc_talked("lily")
    complete_ready_quests(session)
    giver = qm.get_quest("rescue_lily").giver_npc_id
    assert any("Rescue Lily" in m for m in session.npc_manager.get_npc(giver).memories)
    assert any("Rescue Lily" in e for e in session.chronicle)


# --- persistence -------------------------------------------------------------

def test_memories_attitude_and_chronicle_survive_save_and_load(session):
    bram = session.npc_manager.get_npc("bram")
    remember(bram, "Brenna paid for his drink")
    bram.disposition = 42
    chronicle(session, "The goblin chief Grak is dead.")

    restored = _save_and_load(session)

    rbram = restored.npc_manager.get_npc("bram")
    assert "Brenna paid for his drink." in rbram.memories
    assert rbram.disposition == 42
    assert restored.chronicle == ["The goblin chief Grak is dead."]
    assert "Grak is dead" in state_briefing(restored)


def test_initial_prompt_uses_briefing(session):
    prompt = api_server.build_dm_context(session, "[GAME START]")
    assert "Carrying ONLY:" in prompt and "CONSISTENCY & MEMORY" in prompt


# --- player-facing view -----------------------------------------------------

def test_people_view_lists_present_and_remembering_npcs_without_secrets(session):
    remember(session.npc_manager.get_npc("lily"), "Was rescued by the hero")
    people = {p["id"]: p for p in session.to_dict()["people"]}
    assert people["bram"]["here"] and people["bram"]["attitude"]
    assert people["lily"]["memories"] == ["Was rescued by the hero."] and not people["lily"]["here"]
    assert "personality" not in people["bram"]


def test_memory_moments_are_shown_once_per_npc(session, monkeypatch):
    monkeypatch.setattr(api_server, "get_dm_response", lambda *a, **k: (
        "He smiles. [REMEMBER: bram | Bought him a drink] [REMEMBER: bram | Was kind] "
        "[ATTITUDE: bram | +5 | kindness]"))
    with app.test_client() as client:
        body = client.post("/api/game/action", json={
            "session_id": session.session_id, "action": "I buy Bram a drink"}).get_json()
    name = session.npc_manager.get_npc("bram").name
    assert body["message"].count(f"{name} will remember that.") == 1
    assert f"{name} warms to you." in body["message"]
