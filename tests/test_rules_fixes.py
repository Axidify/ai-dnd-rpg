"""Regression tests for game-rules bugs: leveling, armor, shop, weapons, persistence."""

import os

import pytest

import combat
import game_mechanics
from api_server import app, game_sessions, get_session_shop, resolve_equipped_weapon
from character import CLASS_HIT_DICE, Character
from inventory import ITEMS, ItemType, calculate_armor_class, get_item
from shop import create_general_shop, sell_item


def _hero(**stats):
    return Character(name="Tess", race="Human", char_class="Fighter", **stats)


# --- 1. Multi-level XP grants apply HP for every level gained ---------------

def test_level_up_across_several_levels_grants_hp_per_level():
    hero = _hero(constitution=14)  # CON +2, Fighter d10 -> 6 + 2 = 8 HP per level
    start_hp = hero.max_hp
    hero.experience = 10_000
    result = hero.level_up()
    assert (result["old_level"], result["new_level"]) == (1, 5)
    assert result["hp_gain"] == 4 * 8
    assert hero.max_hp == start_hp + 32 == hero.current_hp
    assert result["benefits"].count("+1 to any stat (choose later)") == 2


def test_level_up_hp_gain_is_at_least_one_per_level():
    wizard = Character(name="Frail", char_class="Wizard", constitution=3)  # d6 avg 4, CON -4
    wizard.experience = 10_000
    assert wizard.level_up()["hp_gain"] == 4


def test_hit_dice_table_is_shared():
    assert game_mechanics.CLASS_HIT_DICE is CLASS_HIT_DICE
    assert game_mechanics.get_class_hit_die("Barbarian") == 12


# --- 2. Armor caps the DEX bonus by armor type ------------------------------

@pytest.mark.parametrize("armor_id, expected", [
    ("leather_armor", 10 + 1 + 4),   # light: full DEX
    ("chain_shirt", 10 + 3 + 2),     # medium: DEX capped at +2
    ("plate_armor", 10 + 6),         # heavy: no DEX
])
def test_armor_class_applies_dex_cap(armor_id, expected):
    assert calculate_armor_class(4, get_item(armor_id)) == expected


def test_armor_class_negative_dex_still_applies_to_medium_armor():
    assert calculate_armor_class(-1, get_item("chain_shirt")) == 12


def test_equip_endpoint_caps_dex_for_heavy_armor():
    app.config["TESTING"] = True
    with app.test_client() as client:
        start = client.post("/api/game/start", json={
            "character": {"name": "Plate", "race": "Human", "class": "Fighter"},
        })
        sid = start.get_json()["session_id"]
        hero = game_sessions[sid].character
        hero.dexterity = 18
        hero.inventory.append(get_item("plate_armor"))
        client.post("/api/inventory/equip", json={"session_id": sid, "item_name": "Plate Armor"})
        assert hero.armor_class == 16


def test_starting_armor_uses_dex_cap():
    rogue = Character(name="Quick", char_class="Rogue", dexterity=18)  # leather: light
    rogue._add_starting_equipment()
    assert rogue.armor_class == 10 + 1 + 4
    fighter = _hero(dexterity=18)  # chain shirt: medium
    fighter._add_starting_equipment()
    assert fighter.armor_class == 10 + 3 + 2


# --- 3. Quest items can't be sold ------------------------------------------

def test_quest_items_cannot_be_sold():
    hero = _hero()
    hero.inventory.append(get_item("silver_locket"))
    gold = hero.gold
    shop = create_general_shop("s", "Shop", "merchant", "village", {})
    result = sell_item(hero, shop, "Silver Locket")
    assert not result.success
    assert hero.gold == gold
    assert any(i.name == "Silver Locket" for i in hero.inventory)


# --- 4. Combat uses the equipped Item's stats -------------------------------

def test_quality_weapon_bonus_applies_in_combat(monkeypatch):
    hero = _hero(strength=10)
    legendary = get_item("Legendary Greataxe")
    assert legendary.damage_dice == "1d12+3"
    hero.inventory.append(legendary)
    hero.weapon = legendary.name
    weapon = resolve_equipped_weapon(hero)
    assert weapon is legendary

    monkeypatch.setattr(combat.random, "randint", lambda a, b: 1)
    damage = combat.roll_damage(hero, weapon)
    assert damage["damage_dice"] == "1d12+3"
    assert damage["total"] == 1 + 3
    # Crits double the dice, not the flat quality bonus
    assert combat.roll_damage(hero, weapon, is_crit=True)["total"] == 1 + 1 + 3


def test_plain_weapon_key_still_works():
    hero = _hero()
    hero.weapon = "Longsword"
    hero.inventory = []
    assert resolve_equipped_weapon(hero) == "longsword"


def test_bows_use_dex_in_items_and_combat():
    for key in ("shortbow", "longbow"):
        assert ITEMS[key].finesse == combat.WEAPONS[key]["finesse"] is True
    archer = _hero(strength=8, dexterity=16)
    assert combat.calculate_attack_bonus(archer, get_item("shortbow")) == 2 + 3


# --- 5. NPC disposition and shop state survive save/load --------------------

def test_npc_disposition_and_shop_state_persist_through_save_load():
    app.config["TESTING"] = True
    with app.test_client() as client:
        start = client.post("/api/game/start", json={
            "character": {"name": "Keeper", "race": "Human", "class": "Fighter"},
            "scenario_id": "goblin_cave",
        })
        sid = start.get_json()["session_id"]
        session = game_sessions[sid]
        npc = session.npc_manager.get_all_npcs()[0]
        npc.disposition = 42

        shop = get_session_shop(session)
        shop.add_item("antidote", stock=3, max_stock=3)
        session.character.gold = 500
        assert client.post("/api/shop/buy", json={
            "session_id": sid, "item_id": "antidote",
        }).get_json()["success"]
        session.shop_manager.set_haggle_result(shop.id, discount=0.2)
        # Stock persists between requests in the same session
        assert get_session_shop(session).check_stock("antidote") == 2

        saved = client.post("/api/game/save", json={"session_id": sid}).get_json()
        try:
            loaded = client.post("/api/game/load", json={"name": saved["name"]}).get_json()
        finally:
            os.remove(saved["save_path"])

    restored = game_sessions[loaded["session_id"]]
    assert restored.npc_manager.get_npc(npc.id).disposition == 42
    restored_shop = get_session_shop(restored)
    assert restored_shop.check_stock("antidote") == 2
    assert restored.shop_manager.get_haggle_state(shop.id)["discount"] == 0.2


def test_shop_browse_returns_items():
    app.config["TESTING"] = True
    with app.test_client() as client:
        sid = client.post("/api/game/start", json={
            "character": {"name": "Browser", "race": "Human", "class": "Fighter"},
        }).get_json()["session_id"]
        body = client.get(f"/api/shop/browse?session_id={sid}").get_json()
    assert body["success"] and any(i["id"] == "healing_potion" for i in body["items"])


# --- 6. No duplicate item definitions ---------------------------------------

def test_antidote_defined_once():
    import inspect
    import inventory
    assert inspect.getsource(inventory).count('"antidote": Item(') == 1
    assert ITEMS["antidote"].item_type == ItemType.CONSUMABLE
