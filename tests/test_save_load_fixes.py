"""Regression tests for save/load and travel-condition bugs."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from character import Character
from inventory import get_item
from save_system import (
    character_to_dict, dict_to_character, scenario_to_dict, restore_scenario,
    generate_save_filename,
)
from scenario import ScenarioManager, check_exit_condition


def _hero():
    return Character(name="Tess", race="Human", char_class="Fighter")


def test_downed_character_stays_at_zero_hp_after_load():
    hero = _hero()
    hero.current_hp = 0
    loaded = dict_to_character(character_to_dict(hero), Character)
    assert loaded.current_hp == 0


def test_from_dict_keeps_saved_derived_stats():
    data = character_to_dict(_hero())
    data.update(max_hp=40, current_hp=3, armor_class=18, weapon="rapier")
    loaded = Character.from_dict(data)
    assert (loaded.max_hp, loaded.current_hp, loaded.armor_class, loaded.weapon) == (40, 3, 18, "rapier")


def test_slot_must_be_integer_in_filename():
    assert generate_save_filename("Tess", 2) == "save_tess_slot2.json"
    with pytest.raises((ValueError, TypeError)):
        generate_save_filename("Tess", "/../../evil")


def test_has_item_exit_with_plain_list_inventory():
    key = get_item("torch")
    ok, _ = check_exit_condition("has_item:torch", {"inventory": [key]})
    assert ok
    ok, _ = check_exit_condition("has_item:torch", {"inventory": []})
    assert not ok


def test_event_objective_unlocks_and_survives_save():
    manager = ScenarioManager()
    manager.start_scenario("goblin_cave")
    manager.active_scenario.complete_objective("rescue_lily")
    assert "rescue_lily" in manager.active_scenario.completed_objectives

    ok, _ = check_exit_condition(
        "objective:rescue_lily",
        {"completed_objectives": manager.active_scenario.completed_objectives},
    )
    assert ok

    restored = ScenarioManager()
    assert restore_scenario(restored, scenario_to_dict(manager))
    assert "rescue_lily" in restored.active_scenario.completed_objectives
