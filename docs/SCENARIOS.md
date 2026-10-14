# Scenario data format

A scenario is a folder under `data/scenarios/<scenario_id>/`. Any folder with a
`scenario.yaml` is offered as an adventure automatically (`ScenarioManager`
discovers it via `scenario_loader.list_scenario_ids()`).

| File | Contains | Maps to |
|---|---|---|
| `scenario.yaml` | id, name, hook, `scene_order`, `scenes` | `scenario.Scenario`, `scenario.Scene` |
| `locations.yaml` | list of locations | `scenario.Location` |
| `npcs.yaml` | list of NPCs | `npc.NPC` |
| `quests.yaml` | list of quests | `quest.Quest` |
| `shops.yaml` | list of shops | `shop.Shop` |

Keys are the dataclass field names, and nested objects follow the same rule
(`Location.events` → `LocationEvent`, `Quest.objectives` → `QuestObjective`,
`NPC.personality` → `Personality`, ...). Fields left out take the dataclass
default. An unknown key is an error, so typos fail loudly at load time.

Enums are written by name or value:

- `ObjectiveType`: `KILL`, `FIND_ITEM`, `TALK_TO`, `REACH_LOCATION`, `COLLECT`, `CUSTOM`
- `QuestType`, `ShopType`, `NPCRole`: the member names in `quest.py`, `shop.py`, `npc.py`
- `EventTrigger`: `on_enter`, `on_first_visit`, `on_look`, `on_item_take`

`data/scenarios/goblin_cave/` is the complete reference, and the quickest
start is to copy that folder and edit it.

## Things the engine reads from the text

- **Scene `dm_instructions`** go straight into the DM prompt for that scene.
  They tell the narrator what happens and which control tags to emit
  (`[XP: 25 | reason]`, `[ITEM: torch]`, `[GOLD: 10]`, `[COMBAT: goblin]`, ...).
- **Scene `objectives`** are ids. Combat objectives are completed by winning a
  fight (see `apply_combat_victory`). The Goblin Cave's conversational ones
  (`meet_bram`, `accept_quest`, `find_lily`, `examine_entrance`) are matched by
  keyword in `ScenarioManager.check_transition`, which is Goblin Cave–specific
  for now.
- **Exit and discovery conditions** use the string forms documented in
  `scenario.check_exit_condition`: `has_item:<item_key>`, `visited:<location_id>`,
  `gold:<amount>`, `skill:<ability>:<dc>`, `objective:<objective_id>`,
  `flag:<name>`.
- **Location events** use `effect` strings: `start_combat:<enemy>`,
  `damage:<dice>`, `add_item:<key>`, `xp:<amount>`, `objective:<id>`
  (see `game_mechanics.apply_location_event_effects`).

## Checking a new scenario

`tests/test_scenario_loader.py` validates the Goblin Cave's cross-references
(scene → location ids, exits → locations, NPC ids). Add your scenario id to
those tests, or copy them, to catch broken references before playing.
