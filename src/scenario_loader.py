"""
Load scenario content from data files.

Each scenario is a folder under data/scenarios/<scenario_id>/:

    scenario.yaml   metadata + scenes          (scenario.Scenario / Scene)
    locations.yaml  list of locations          (scenario.Location)
    npcs.yaml       list of NPCs               (npc.NPC)
    quests.yaml     list of quests             (quest.Quest)
    shops.yaml      list of shops              (shop.Shop)

Field names map 1:1 to the dataclasses; see data_codec for the conversion.
Adding a scenario means adding a folder, no code changes.
"""

import os
from functools import lru_cache
from typing import Any, List

import yaml

from data_codec import from_data
from npc import NPC, NPCManager
from quest import Quest, QuestManager
from shop import Shop, ShopManager

SCENARIOS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "scenarios")


@lru_cache(maxsize=None)
def _read(scenario_id: str, name: str) -> Any:
    path = os.path.join(SCENARIOS_DIR, scenario_id, f"{name}.yaml")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def list_scenario_ids() -> List[str]:
    """Every folder under data/scenarios that has a scenario.yaml."""
    if not os.path.isdir(SCENARIOS_DIR):
        return []
    return sorted(
        name for name in os.listdir(SCENARIOS_DIR)
        if os.path.exists(os.path.join(SCENARIOS_DIR, name, "scenario.yaml"))
    )


def load_npcs(scenario_id: str) -> NPCManager:
    manager = NPCManager()
    for data in _read(scenario_id, "npcs") or []:
        manager.add_npc(from_data(NPC, data))
    return manager


def register_quests(scenario_id: str, quest_manager: QuestManager) -> None:
    for data in _read(scenario_id, "quests") or []:
        quest_manager.register_quest(from_data(Quest, data))


def load_shops(scenario_id: str) -> List[Shop]:
    return [from_data(Shop, data) for data in _read(scenario_id, "shops") or []]


def register_shops(scenario_id: str, shop_manager: ShopManager) -> None:
    for shop in load_shops(scenario_id):
        shop_manager.add_shop(shop)


def load_scenario(scenario_id: str):
    """Build a fresh Scenario (new objects every call; the YAML is cached)."""
    from scenario import Location, LocationManager, Scenario

    meta = _read(scenario_id, "scenario")
    if meta is None:
        raise ValueError(f"Unknown scenario: {scenario_id}")

    location_manager = LocationManager()
    for data in _read(scenario_id, "locations") or []:
        location_manager.add_location(from_data(Location, data))

    scenario = from_data(Scenario, meta)
    scenario.location_manager = location_manager
    scenario.npc_manager = load_npcs(scenario_id)
    return scenario
