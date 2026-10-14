"""Scenario content is loaded from data/scenarios/<id>/*.yaml."""

import dataclasses
import enum
from typing import Dict, List, Optional

import pytest

from data_codec import from_data, to_data
from quest import QuestManager
from scenario import ScenarioManager
from scenario_loader import list_scenario_ids, load_scenario, register_quests
from shop import ShopManager
from scenario_loader import register_shops


def test_goblin_cave_is_discovered():
    assert "goblin_cave" in list_scenario_ids()
    assert "goblin_cave" in ScenarioManager().available_scenarios


def test_goblin_cave_content_loads():
    scenario = load_scenario("goblin_cave")
    assert scenario.scene_order[0] == "tavern"
    assert set(scenario.scene_order) == set(scenario.scenes)
    assert len(scenario.location_manager.locations) == 22
    assert scenario.npc_manager.get_npc("bram") is not None

    quests = QuestManager()
    register_quests("goblin_cave", quests)
    assert "rescue_lily" in quests.available_quests

    shops = ShopManager()
    register_shops("goblin_cave", shops)
    assert shops.get_shop("gavins_forge") is not None


def test_scene_and_exit_references_are_valid():
    scenario = load_scenario("goblin_cave")
    locations = scenario.location_manager.locations
    for scene in scenario.scenes.values():
        for loc_id in scene.location_ids:
            assert loc_id in locations, f"scene {scene.id} references unknown location {loc_id}"
        if scene.next_scene_id:
            assert scene.next_scene_id in scenario.scenes
    for loc in locations.values():
        for exit_name, target in loc.exits.items():
            assert target in locations, f"{loc.id} exit {exit_name!r} -> unknown {target}"
        for npc_id in loc.npcs:
            # Crowds and enemies are scene flavour, not NPC records
            if npc_id in ("locals", "villagers", "goblins", "grotnak", "bodyguards"):
                continue
            assert scenario.npc_manager.get_npc(npc_id) is not None, f"{loc.id} has unknown NPC {npc_id}"


def test_each_load_returns_independent_objects():
    first = load_scenario("goblin_cave")
    first.location_manager.locations["tavern_main"].visited = True
    first.location_manager.locations["tavern_main"].npcs.append("intruder")
    first.scenes["tavern"].objectives_complete.append("meet_bram")

    second = load_scenario("goblin_cave")
    assert second.location_manager.locations["tavern_main"].visited is False
    assert "intruder" not in second.location_manager.locations["tavern_main"].npcs
    assert second.scenes["tavern"].objectives_complete == []


class Color(enum.Enum):
    RED = "red"


@dataclasses.dataclass
class Inner:
    name: str
    tags: List[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Outer:
    id: str
    color: Color = Color.RED
    inner: Optional[Inner] = None
    by_id: Dict[str, Inner] = dataclasses.field(default_factory=dict)
    weight: float = 0.0


def test_codec_round_trip_and_defaults_omitted():
    obj = Outer(id="x", inner=Inner("a", ["t"]), by_id={"b": Inner("b")}, weight=2)
    data = to_data(obj)
    assert "color" not in data  # default omitted
    assert data["by_id"] == {"b": {"name": "b"}}
    assert from_data(Outer, data) == obj


def test_codec_rejects_unknown_fields():
    with pytest.raises(ValueError, match="unknown field"):
        from_data(Outer, {"id": "x", "colour": "red"})


def test_every_scenario_item_exists():
    """Items placed in locations, hidden items and quest rewards must be defined."""
    from inventory import ITEMS

    scenario = load_scenario("goblin_cave")
    missing = set()
    for loc in scenario.location_manager.locations.values():
        missing |= {k for k in loc.items if k not in ITEMS}
        missing |= {h.item_id for h in loc.hidden_items if h.item_id not in ITEMS}
    quests = QuestManager()
    register_quests("goblin_cave", quests)
    for quest in quests.available_quests.values():
        missing |= {k for k in (quest.rewards or {}).get("items", []) if k not in ITEMS}
    assert not missing, f"undefined item keys: {sorted(missing)}"


def test_every_scene_is_reachable_on_foot():
    """Each scene's places must be reachable by exits from where the story starts."""
    scenario = load_scenario("goblin_cave")
    locations = scenario.location_manager.locations
    start = scenario.scenes[scenario.scene_order[0]].starting_location_id
    seen, frontier = {start}, [start]
    while frontier:
        for dest in locations[frontier.pop()].exits.values():
            if dest not in seen:
                seen.add(dest)
                frontier.append(dest)
    for scene_id in scenario.scene_order:
        scene = scenario.scenes[scene_id]
        unreachable = [loc for loc in scene.location_ids if loc not in seen]
        assert not unreachable, f"scene {scene_id}: no path to {unreachable}"
