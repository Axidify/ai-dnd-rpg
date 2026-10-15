"""
Shared game mechanics helpers for API integration.
Location events, scenario transitions, party combat, proficiency,
player defeat lifecycle, hostile-action combat gate, travel pipeline.
"""

from __future__ import annotations

import random
import re
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from world_memory import chronicle, remember

if TYPE_CHECKING:
    from api_server import GameSession

from character import CLASS_HIT_DICE
from combat import roll_dice, ENEMIES
from inventory import get_item, add_item_to_inventory, remove_item_from_inventory, find_item_in_inventory
from text_match import has_any, has_phrase

# Class skill proficiencies (simplified — one primary skill per class)
CLASS_SKILL_PROFICIENCIES = {
    "Fighter": ["athletics"],
    "Barbarian": ["athletics"],
    "Paladin": ["persuasion", "athletics"],
    "Ranger": ["survival", "perception"],
    "Rogue": ["stealth", "sleight_of_hand", "acrobatics"],
    "Wizard": ["arcana", "investigation"],
    "Sorcerer": ["arcana"],
    "Cleric": ["religion", "insight"],
    "Druid": ["nature", "survival"],
    "Bard": ["persuasion", "performance"],
    "Warlock": ["arcana", "intimidation"],
    "Monk": ["acrobatics", "stealth"],
}



def get_class_hit_die(char_class: str) -> int:
    return CLASS_HIT_DICE.get(char_class, 8)


def is_proficient_in_skill(character, skill_name: str) -> bool:
    if not character:
        return False
    skill = skill_name.lower().replace(" ", "_")
    profs = CLASS_SKILL_PROFICIENCIES.get(character.char_class, [])
    return skill in profs


def skill_check_modifier(character, skill_name: str, skill_abilities: dict) -> int:
    """Ability mod + proficiency (if proficient)."""
    skill_lower = skill_name.lower().replace(" ", "_")
    ability = skill_abilities.get(skill_lower, skill_lower)
    modifier = character.get_ability_modifier(ability)
    if is_proficient_in_skill(character, skill_name):
        modifier += character.get_proficiency_bonus()
    return modifier


def parse_damage_dice(damage_dice: str) -> Tuple[str, int]:
    """Parse '1d8+2' into ('1d8', 2)."""
    if "+" in damage_dice:
        dice, bonus = damage_dice.rsplit("+", 1)
        return dice.strip(), int(bonus.strip())
    if "-" in damage_dice:
        dice, bonus = damage_dice.rsplit("-", 1)
        return dice.strip(), -int(bonus.strip())
    return damage_dice.strip(), 0


def party_member_attack(ally, target) -> Tuple[bool, int, str]:
    """Resolve one party member attack. Returns (hit, damage, message)."""
    d20 = random.randint(1, 20)
    total = d20 + ally.attack_bonus
    is_crit = d20 == 20
    is_fumble = d20 == 1
    hit = (total >= target.armor_class or is_crit) and not is_fumble

    if not hit:
        return False, 0, f"⚔️ {ally.name} swings at {target.name} — miss."

    dice_str, bonus = parse_damage_dice(ally.damage_dice)
    damage_total, _ = roll_dice(dice_str)
    if is_crit:
        crit_extra, _ = roll_dice(dice_str)
        damage_total += crit_extra
    final = max(1, damage_total + bonus)
    status = target.take_damage(final)
    crit = " (CRIT!)" if is_crit else ""
    return True, final, f"⚔️ {ally.name} hits {target.name} for {final}{crit}. {status}"


def run_party_ally_attacks(session, living_enemies: list, result_messages: list) -> list:
    """Allies attack after the player's turn. Returns updated living_enemies."""
    if not session.party or not living_enemies:
        return living_enemies

    allies = session.party.get_alive_members()
    if not allies:
        return living_enemies

    result_messages.append("\n--- Ally Turn ---")
    for ally in allies:
        living_enemies = [e for e in living_enemies if not e.is_dead]
        if not living_enemies:
            break
        target = living_enemies[0]
        _, _, msg = party_member_attack(ally, target)
        result_messages.append(msg)

    return [e for e in living_enemies if not e.is_dead]


def apply_location_event_effects(session, events: list) -> Tuple[List[str], bool]:
    """
    Apply mechanical effects from location events.
    Returns (messages, combat_started).
    """
    messages: List[str] = []
    combat_started = False

    if not events or not session.character:
        return messages, combat_started

    for event in events:
        if not getattr(event, "effect", None):
            continue
        label = event.id.replace("_", " ")
        avoided = False  # a passed "skill_check:" save skips the event's damage

        for part in event.effect.split("|"):
            part = part.strip()
            if not part:
                continue

            if part.startswith("skill_check:"):
                # "skill_check:<ability>:<dc>": an ability check to avoid harm
                _, ability, dc_str = (part.split(":") + ["", ""])[:3]
                try:
                    dc = int(dc_str)
                except ValueError:
                    continue
                mod = session.character.get_ability_modifier(ability.strip().lower())
                roll = random.randint(1, 20)
                avoided = roll + mod >= dc
                messages.append(
                    f"🎲 {ability.strip().upper()} check: [{roll}]{mod:+d} = {roll + mod} vs DC {dc}"
                    + (" — you avoid it!" if avoided else " — too slow!")
                )

            elif part.startswith("start_combat:"):
                enemy_str = part.split(":", 1)[1]
                enemies = [e.strip().lower().replace(" ", "_") for e in enemy_str.split(",") if e.strip()]
                if enemies:
                    start_structured_combat(session, enemies)
                    combat_started = True
                    messages.append(f"⚔️ Ambush! Combat: {', '.join(enemies)}")

            elif part.startswith("damage:"):
                if avoided:
                    continue
                dice = part.split(":", 1)[1].strip()
                total, _ = roll_dice(dice)
                status, _defeated = apply_player_damage(session, total, label)
                messages.append(status or f"💔 You take {total} damage from the {label}!")

            elif part.startswith("add_item:"):
                item_key = part.split(":", 1)[1].strip()
                item = get_item(item_key)
                if item:
                    add_item_to_inventory(session.character.inventory, item)
                    messages.append(f"📦 Found: {item.name}")

            elif part.startswith("xp:"):
                try:
                    amount = int(part.split(":", 1)[1].strip())
                    session.character.gain_xp(amount, event.id)
                    messages.append(f"⭐ +{amount} XP")
                except ValueError:
                    pass

            elif part.startswith("objective:"):
                obj_id = part.split(":", 1)[1].strip()
                if session.scenario and session.scenario.active_scenario:
                    session.scenario.active_scenario.complete_objective(obj_id)
                    messages.append(f"📜 Objective complete: {obj_id.replace('_', ' ').capitalize()}")

    return messages, combat_started


def apply_scenario_transition(session, player_action: str, dm_response: str) -> str:
    """Run scenario scene transition check; sync session location from manager."""
    if not session.scenario:
        return ""

    transition = session.scenario.check_transition(player_action, dm_response)
    _sync_session_location(session)
    return transition or ""


def _sync_session_location(session) -> None:
    """Update session location fields from location_manager."""
    if session.location_manager:
        loc = session.location_manager.get_current_location()
        if loc:
            session.current_location = loc.name
            session.current_location_id = loc.id


def sync_session_from_scenario(session) -> None:
    """After load or scenario start, wire managers from active scenario."""
    if not session.scenario or not session.scenario.active_scenario:
        return
    scenario = session.scenario.active_scenario
    if scenario.location_manager:
        session.location_manager = scenario.location_manager
    if scenario.npc_manager:
        session.npc_manager = scenario.npc_manager
    _sync_session_location(session)


def serialize_session_state(session) -> Dict[str, Any]:
    """Extra session fields for save files."""
    combat_state = None
    if session.combat_state:
        combat_state = {
            k: v for k, v in session.combat_state.items()
            if k != "enemy_objects"
        }
    return {
        "in_combat": session.in_combat,
        "combat_state": combat_state,
        "game_over": session.game_over,
        "game_over_reason": session.game_over_reason,
        "failed_social_checks": session.failed_social_checks,
        "social_check_blocked_npcs": list(session.social_check_blocked_npcs),
        "current_location": session.current_location,
        "current_location_id": session.current_location_id,
        "session_id": session.session_id,
        "scene_state": getattr(session, "scene_state", None) or {},
        "npc_states": {
            npc.id: {
                "disposition": npc.disposition,
                "recruited": npc.recruited,
                "location_id": npc.location_id,
                "memories": list(npc.memories),
            }
            for npc in (session.npc_manager.get_all_npcs() if session.npc_manager else [])
        },
        "chronicle": list(getattr(session, "chronicle", [])),
        "shop_manager": (
            session.shop_manager.to_dict()
            if getattr(session, "shop_manager", None) else None
        ),
    }


def restore_session_state(session, data: Optional[Dict[str, Any]]) -> None:
    """Restore extra session fields from save."""
    if not data:
        return
    session.in_combat = data.get("in_combat", False)
    session.combat_state = data.get("combat_state")
    session.game_over = data.get("game_over", False)
    session.game_over_reason = data.get("game_over_reason")
    session.failed_social_checks = data.get("failed_social_checks", 0)
    blocked = data.get("social_check_blocked_npcs", [])
    session.social_check_blocked_npcs = set(blocked) if blocked else set()
    if data.get("current_location"):
        session.current_location = data["current_location"]
    if data.get("current_location_id"):
        session.current_location_id = data["current_location_id"]
    session.dm_chat = None
    if data.get("scene_state") is not None:
        session.scene_state = data.get("scene_state") or {}
    # NPC disposition etc. (scenario NPCs are rebuilt fresh on load)
    if data.get("npc_states") and session.npc_manager:
        session.npc_manager.update_npc_states(data["npc_states"])
    session.chronicle = list(data.get("chronicle", []))
    if data.get("shop_manager"):
        from shop import ShopManager
        session.shop_manager = ShopManager()
        session.shop_manager.from_dict(data["shop_manager"])


def is_thin_legacy_save(save_data: dict) -> bool:
    """Detect old API-only saves without SaveManager schema."""
    return "version" not in save_data and "character" in save_data


# ---------------------------------------------------------------------------
# Player defeat / HP authority
# ---------------------------------------------------------------------------

DEFEAT_REASON_DEFAULT = (
    "You have fallen unconscious. Your adventure ends here."
)


def on_player_defeat(session, reason: Optional[str] = None) -> None:
    """Mark session as game over after HP reaches zero."""
    if session.game_over:
        return
    if session.character:
        session.character.current_hp = 0
    session.in_combat = False
    session.combat_state = None
    session.game_over = True
    session.game_over_reason = reason or DEFEAT_REASON_DEFAULT


def apply_player_damage(
    session, amount: int, source: str = ""
) -> Tuple[str, bool]:
    """
    Apply damage through Character.take_damage and trigger defeat at 0 HP.
    Returns (status_message, defeated).
    """
    if not session.character or amount <= 0:
        return ("", False)
    if session.game_over:
        return ("", True)

    msg = session.character.take_damage(amount)
    if session.character.current_hp <= 0:
        defeat_reason = (
            f"You were slain by {source}. Your adventure ends here."
            if source
            else DEFEAT_REASON_DEFAULT
        )
        on_player_defeat(session, defeat_reason)
        return (msg, True)
    return (msg, False)


def is_session_blocked(session) -> Tuple[bool, str]:
    """True when game over or player is at 0 HP (auto-sets game over)."""
    if session.game_over:
        return True, session.game_over_reason or "game_over"
    if session.character and session.character.current_hp <= 0:
        on_player_defeat(session)
        return True, session.game_over_reason or DEFEAT_REASON_DEFAULT
    return False, ""


def build_travel_game_state(session) -> Dict[str, Any]:
    """Game state dict for location manager condition checks."""
    visited = []
    if session.location_manager:
        visited = [
            loc.id
            for loc in session.location_manager.locations.values()
            if loc.visited
        ]
    completed_objectives = []
    if session.scenario and session.scenario.active_scenario:
        completed_objectives = list(
            getattr(session.scenario.active_scenario, "completed_objectives", []) or []
        )
    return {
        "character": session.character,
        "inventory": session.character.inventory if session.character else [],
        "visited_locations": visited,
        "completed_objectives": completed_objectives,
    }


def start_structured_combat(
    session, enemies: List[str], surprise: bool = False
) -> None:
    """
    Enter structured combat with enemy type ids. If they belong to this
    location's fixed encounter, that encounter counts as fought (so the DM is
    never told to start it again).
    """
    enemy_ids = [e.strip().lower().replace(" ", "_") for e in enemies if e.strip()]
    session.in_combat = True
    session.combat_state = {
        "enemies": enemy_ids,
        "surprise": surprise,
        "round": 1,
    }
    here = session.location_manager.get_current_location() if session.location_manager else None
    if here and here.encounter and set(enemy_ids) & set(here.encounter):
        here.encounter_triggered = True


def _consume_item_key(session, item_key: str) -> Optional[str]:
    """Remove a keyed item from inventory after using a exit key."""
    if not session.character:
        return None
    item = find_item_in_inventory(session.character.inventory, item_key)
    if item:
        remove_item_from_inventory(session.character.inventory, item.name, 1)
        return item.name
    return None


def finish_quest(session, quest_id: str) -> Optional[Dict[str, Any]]:
    """
    Complete a quest whose objectives are done and grant its rewards (XP,
    gold, items, giver disposition). Returns {'quest', 'xp', 'gold', 'items'}
    or None if the quest isn't ready.
    """
    if not session.quest_manager:
        return None
    result = session.quest_manager.complete_quest(quest_id)
    if not result:
        return None
    quest_rewards, quest = result
    rewards = {"quest": quest, "xp": 0, "gold": 0, "items": []}
    character = session.character
    if character:
        # Quest items the quest asked you to find are handed over on completion
        for objective in quest.objectives:
            if objective.objective_type.name in ("FIND_ITEM", "COLLECT"):
                item = find_item_in_inventory(character.inventory, objective.target)
                if item and item.item_type.name == "QUEST":
                    remove_item_from_inventory(character.inventory, item.name, item.quantity)
    if character and quest_rewards:
        if quest_rewards.get("xp"):
            character.gain_xp(quest_rewards["xp"], quest.name)
            rewards["xp"] = quest_rewards["xp"]
        if quest_rewards.get("gold"):
            character.gold += quest_rewards["gold"]
            rewards["gold"] = quest_rewards["gold"]
        for item_key in quest_rewards.get("items", []):
            item = get_item(item_key)
            if item:
                add_item_to_inventory(character.inventory, item)
                rewards["items"].append(item.name)
    if session.npc_manager and quest.giver_npc_id:
        npc = session.npc_manager.get_npc(quest.giver_npc_id)
        if npc:
            npc.modify_disposition(quest.get_disposition_reward())
            remember(npc, f"The hero completed '{quest.name}' for them")
    chronicle(session, f"Quest completed: {quest.name}.")
    return rewards


def complete_ready_quests(session) -> List[str]:
    """Finish every active quest whose required objectives are all done."""
    if not session.quest_manager:
        return []
    messages = []
    for quest in list(session.quest_manager.get_active_quests()):
        if not quest.is_ready_to_complete():
            continue
        rewards = finish_quest(session, quest.id)
        if not rewards:
            continue
        parts = [f"+{rewards['xp']} XP" if rewards["xp"] else "",
                 f"+{rewards['gold']} gold" if rewards["gold"] else "",
                 ", ".join(rewards["items"])]
        gained = ", ".join(p for p in parts if p)
        messages.append(f"🏆 Quest complete: **{quest.name}**" + (f" ({gained})" if gained else ""))
    return messages


def blocked_path_hint(session) -> str:
    """
    If exits from here lead into the next scene but aren't open yet, say which
    and what's still to do, so a closed way forward never looks like a dead end.
    """
    scenario = session.scenario.active_scenario if session.scenario else None
    manager = session.location_manager
    scene = scenario.get_current_scene() if scenario else None
    here = manager.get_current_location() if manager else None
    if not (scene and scene.next_scene_id and here):
        return ""
    next_ids = set(scenario.scenes[scene.next_scene_id].location_ids)
    closed = [name for name, dest in here.exits.items()
              if dest in next_ids and dest not in manager.available_location_ids]
    if not closed:
        return ""
    todo = [o.replace("_", " ") for o in scene.objectives if o not in scene.objectives_complete]
    reason = f" Still to do: {', '.join(todo)}." if todo else " Explore a little more first."
    return f"🚪 The way onward ({', '.join(closed)}) isn't open yet.{reason}"


def process_travel(session, destination: str) -> Dict[str, Any]:
    """
    Full travel pipeline: exit checks (incl. skill), move, random encounters,
    location events, defeat handling.
    """
    from dm_engine import roll_skill_check, format_roll_result

    if not session.location_manager:
        old = session.current_location
        session.current_location = destination.title()
        msg = f"📍 You travel to **{session.current_location}**."
        return {
            "success": True,
            "message": msg,
            "new_location": session.current_location,
            "old_location": old,
            "events": [],
            "quest_updates": [],
            "combat_started": False,
            "game_over": session.game_over,
        }

    blocked, block_reason = is_session_blocked(session)
    if blocked:
        return {"success": False, "message": block_reason, "game_over": True}

    game_state = build_travel_game_state(session)
    previous_id = session.location_manager.current_location_id
    skill_check_override = False
    skill_roll_text = ""

    success, new_location, travel_note, events = session.location_manager.move(
        destination, game_state, skill_check_override=skill_check_override
    )

    if not success and travel_note and travel_note.startswith("skill_check:"):
        parts = travel_note.split(":")
        if len(parts) >= 3:
            skill, dc_str = parts[1], parts[2]
            try:
                dc = int(dc_str)
            except ValueError:
                dc = 10
            result = roll_skill_check(session.character, skill, dc)
            skill_roll_text = format_roll_result(result)
            if result["success"]:
                success, new_location, travel_note, events = (
                    session.location_manager.move(
                        destination, game_state, skill_check_override=True
                    )
                )
            else:
                fail = travel_note
                loc = session.location_manager.get_current_location()
                if loc:
                    for exit_name in session.location_manager.get_exits():
                        cond = loc.get_exit_condition(exit_name)
                        if cond and cond.fail_message:
                            fail = cond.fail_message
                            break
                return {
                    "success": False,
                    "message": f"{skill_roll_text}\n\n{fail}",
                }

    if not success or not new_location:
        return {
            "success": False,
            "message": travel_note or "You cannot go that way.",
        }

    session.current_location = new_location.name
    session.current_location_id = new_location.id
    session.previous_location_id = previous_id  # where fleeing leads back to

    # Exploring advances the story: travel is an exchange, and arriving in the
    # next scene's area starts that scene
    new_scene = None
    scenario = session.scenario.active_scenario if session.scenario else None
    if scenario:
        scenario.record_exchange()
        new_scene = scenario.advance_on_arrival(new_location.id)

    quest_updates: List[Dict[str, Any]] = []
    if session.quest_manager:
        completed = session.quest_manager.on_location_entered(new_location.id)
        for quest_id, objective in completed:
            quest = session.quest_manager.get_quest(quest_id)
            if quest:
                quest_updates.append({
                    "quest_id": quest_id,
                    "objective_id": objective.id,
                    "quest": quest.to_dict(),
                })

    quest_messages = complete_ready_quests(session)

    travel_msg = f"📍 You travel to **{new_location.name}**.\n\n{new_location.description}"
    for quest_msg in quest_messages:
        travel_msg += f"\n\n{quest_msg}"
    if new_scene:
        travel_msg = f"## {new_scene.name}\n\n{travel_msg}"
    if skill_roll_text:
        travel_msg = f"{skill_roll_text}\n\n{travel_msg}"

    if travel_note and travel_note.startswith("CONSUME_ITEM:"):
        item_key = travel_note.split(":", 1)[1].strip()
        used = _consume_item_key(session, item_key)
        if used:
            travel_msg += f"\n\n🔑 You use the {used} to proceed."

    combat_started = False
    encounter = session.location_manager.check_random_encounter(game_state)
    if encounter and encounter.enemies:
        start_structured_combat(session, encounter.enemies)
        combat_started = True
        narr = encounter.narration or f"⚔️ Ambush! {', '.join(encounter.enemies)}!"
        travel_msg += f"\n\n{narr}"

    if events:
        for event in events:
            travel_msg += f"\n\n⚡ {event.narration}"

    effect_msgs, event_combat = apply_location_event_effects(session, events)
    combat_started = combat_started or event_combat
    for effect_msg in effect_msgs:
        travel_msg += f"\n\n{effect_msg}"

    hint = blocked_path_hint(session)
    if hint:
        travel_msg += f"\n\n{hint}"

    is_session_blocked(session)

    return {
        "success": True,
        "message": travel_msg,
        "new_location": {
            "id": new_location.id,
            "name": new_location.name,
            "description": new_location.description,
            "exits": list(session.location_manager.get_exits().keys()),
        },
        "events": [e.to_dict() for e in events],
        "quest_updates": quest_updates,
        "combat_started": combat_started,
        "game_over": session.game_over,
        "game_over_reason": session.game_over_reason,
    }


# ---------------------------------------------------------------------------
# Hostile action → structured combat gate
# ---------------------------------------------------------------------------

HOSTILE_VERBS = (
    "attack", "hit", "hits", "strike", "punch", "kick", "stab", "stabbed", "slash",
    "shoot", "shot", "murder", "kill", "slay", "assault", "fight", "charge at",
    "swing at", "throw at", "fireball at",
)
# "cast <spell> at <target>" (idioms like "cast a glance at" are removed first)
HOSTILE_CAST_RE = re.compile(r"\bcast(?:s|ing)?\b(?:\s+[\w'-]+){1,3}\s+at\b")

# Figures of speech that contain a hostile verb. Removed before matching.
NON_HOSTILE_IDIOMS = (
    "strike a deal", "strike a bargain", "strike up", "strike a pose",
    "hit the road", "hit the hay", "hit the sack", "hit it off",
    "fight the urge", "fight back tears", "kill time", "killing time",
    "shoot a glance", "shoot a look", "shot a glance", "shoot the breeze",
    "cast a glance", "cast a look", "cast an eye", "cast my eye", "cast my eyes",
    "cast his eye", "cast her eye", "cast a shadow", "cast lots",
)

TARGET_ENEMY_MAP = {
    "goblin": "goblin",
    "orc": "orc",
    "wolf": "wolf",
    "wolves": "wolf",
    "skeleton": "skeleton",
    "bandit": "bandit",
    "spider": "giant_spider",
    "giant spider": "giant_spider",
    "boss": "goblin_boss",
    "chief": "goblin_boss",
    "goblin boss": "goblin_boss",
    "goblin chief": "goblin_boss",
    "villager": "bandit",
    "townsperson": "bandit",
    "civilian": "bandit",
    "peasant": "bandit",
    "farmer": "bandit",
    "merchant": "bandit",
    "blacksmith": "bandit",
    "smith": "bandit",
    "guard": "bandit",
    "innkeeper": "bandit",
    "bartender": "bandit",
    "npc": "bandit",
    "person": "bandit",
    "man": "bandit",
    "woman": "bandit",
}


def _is_hostile_action(action: str) -> bool:
    lower = " ".join(action.lower().split())
    for idiom in NON_HOSTILE_IDIOMS:
        lower = lower.replace(idiom, " ")
    return has_any(lower, HOSTILE_VERBS) or bool(HOSTILE_CAST_RE.search(lower))


def _resolve_hostile_enemies(action: str) -> List[str]:
    # Longest names first so "goblin chief" wins over "goblin"; whole words
    # only so "force" isn't an orc and "shaman" isn't a man.
    for target in sorted(TARGET_ENEMY_MAP, key=len, reverse=True):
        enemy_id = TARGET_ENEMY_MAP[target]
        if enemy_id in ENEMIES and has_phrase(action, target):
            return [enemy_id]
    for enemy_id in ENEMIES:
        if has_phrase(action, enemy_id.replace("_", " ")):
            return [enemy_id]
    return ["bandit"]


def _matching_encounter(session, enemy_id: str):
    """
    The location (here, or one exit away) whose untriggered fixed encounter
    includes ``enemy_id`` - e.g. attacking "the goblins" from the shadows
    beside a camp of four fights all four, not one.
    """
    manager = session.location_manager
    here = manager.get_current_location() if manager else None
    if not here:
        return None
    candidates = [here] + [manager.locations.get(d) for d in manager.get_exits().values()]
    for loc in candidates:
        if loc and loc.encounter and not loc.encounter_triggered and enemy_id in loc.encounter:
            return loc
    return None


def try_hostile_combat_gate(session, action: str) -> Optional[Dict[str, Any]]:
    """
    Intercept hostile player actions and start structured combat instead of
  narrative free-form damage. Returns response dict if combat started, else None.
    """
    if session.in_combat or session.game_over:
        return None
    if not _is_hostile_action(action):
        return None

    enemies = _resolve_hostile_enemies(action)
    encounter_loc = _matching_encounter(session, enemies[0])
    if encounter_loc:
        # Fight the whole group that's actually there, once
        enemies = list(encounter_loc.encounter)
        encounter_loc.encounter_triggered = True
    start_structured_combat(session, enemies)
    names = ", ".join(enemies)
    msg = (
        f"⚔️ **Combat erupts!** Your hostile action draws a fight.\n\n"
        f"Enemies: **{names}**\n\n"
        f"Use **Attack**, **Defend**, or **Flee** below."
    )
    return {
        "message": msg,
        "combat_started": True,
        "enemies": enemies,
    }
