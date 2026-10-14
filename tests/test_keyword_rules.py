"""Keyword rules match whole words, not fragments of other words."""

import pytest

from api_server import get_skill_hint
from dm_scene import classify_exploration_action, is_weak_roll_narration
from game_mechanics import _is_hostile_action, _resolve_hostile_enemies
from inventory import get_item, add_item_to_inventory, find_item_in_inventory
from scenario import ScenarioManager


@pytest.mark.parametrize("action", [
    "I strike a deal with the merchant using all my force",
    "I cast a glance at the shaman",
    "I hit the road",
    "I talk to the shaman",
])
def test_not_hostile(action):
    assert not _is_hostile_action(action)


@pytest.mark.parametrize("action, enemy", [
    ("I attack the goblin chief", "goblin_boss"),
    ("I'm attacking the orc", "orc"),
    ("I cast magic missile at the wolves", "wolf"),
    ("Kill the spider!", "giant_spider"),
])
def test_hostile_targets(action, enemy):
    assert _is_hostile_action(action)
    assert _resolve_hostile_enemies(action) == [enemy]


def test_force_is_not_an_orc():
    assert _resolve_hostile_enemies("I punch him with all my force") == ["bandit"]


def test_prose_cannot_complete_the_boss_objective():
    manager = ScenarioManager()
    manager.start_scenario("goblin_cave")
    scenario = manager.active_scenario
    boss_scene = next(s for s in scenario.scenes.values() if "defeat_chief" in s.objectives)
    scenario.current_scene_id = boss_scene.id

    manager.check_transition("I wait", "Rain falls on the cave. A small victory: you stay dry.")
    assert "defeat_chief" not in boss_scene.objectives_complete


def test_vague_look_with_what():
    assert classify_exploration_action("I look around, taking in what's there") == "vague_survey"


def test_skill_hint_ignores_word_fragments():
    assert get_skill_hint("I order some bread and return to my table") == ""
    assert "Stealth" in get_skill_hint("I sneak behind the stall")


def test_failed_roll_with_about_is_still_weak():
    text = "You narrow your eyes and scan the square, thinking about the crowd. " * 2
    assert is_weak_roll_narration(text, {"success": False, "skill": "Perception"})


def test_inventory_prefers_exact_match():
    inventory = []
    add_item_to_inventory(inventory, get_item("greater healing potion") or get_item("healing potion"))
    add_item_to_inventory(inventory, get_item("healing potion"))
    assert find_item_in_inventory(inventory, "healing potion").name.lower() == "healing potion"
    assert find_item_in_inventory(inventory, "healing_potion").name.lower() == "healing potion"
    assert find_item_in_inventory(inventory, "potion") is not None
