"""Character review: preview a roll, then start the game with exactly that character."""

import pytest

from api_server import app, game_sessions, pending_previews

HERO = {"name": "Wren", "race": "Elf", "class": "Rogue"}
STATS = ("strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma")


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def _preview(client, hero=HERO):
    body = client.post("/api/character/preview", json={"character": hero}).get_json()
    assert body["success"]
    return body["preview_token"], body["character"]


def test_preview_includes_derived_stats(client):
    _, char = _preview(client)
    assert all(3 <= char[s] <= 18 for s in STATS)
    assert set(char["ability_modifiers"]) == set(STATS)
    assert char["ability_modifiers"]["dexterity"] == (char["dexterity"] - 10) // 2
    assert char["proficiency_bonus"] == 2
    # Rogue starts with a finesse shortsword: attack = proficiency + DEX
    assert char["attack_bonus"] == 2 + char["ability_modifiers"]["dexterity"]
    assert char["weapon_damage"]
    assert char["next_level_xp"] == 100


def test_start_uses_the_previewed_character(client):
    token, previewed = _preview(client)
    start = client.post("/api/game/start", json={"character": HERO, "preview_token": token}).get_json()
    played = start["game_state"]["character"]
    for key in STATS + ("max_hp", "armor_class", "gold"):
        assert played[key] == previewed[key], key
    assert token not in pending_previews  # single use


def test_token_cannot_be_reused_or_swapped(client):
    token, _ = _preview(client)
    client.post("/api/game/start", json={"character": HERO, "preview_token": token})
    # Reusing it rolls a fresh character instead of failing
    again = client.post("/api/game/start", json={"character": HERO, "preview_token": token})
    assert again.status_code == 200

    token2, _ = _preview(client)
    other = client.post("/api/game/start", json={
        "character": {**HERO, "name": "Someone Else"}, "preview_token": token2,
    }).get_json()
    session = game_sessions[other["session_id"]]
    assert session.character.name == "Someone Else"
    assert token2 not in pending_previews


def test_preview_validates_name(client):
    assert client.post("/api/character/preview", json={"character": {"name": "  "}}).status_code == 400
