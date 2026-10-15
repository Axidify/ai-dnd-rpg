"""
World state: things in the world that change, owned by the engine.

Step 4 of the single-source-of-truth design. Players change the world in
ways the narrator used to decide on its own ("I pick the lock and free
Lily"). Now the scenario defines those interactions as data, and the
engine resolves them before narration:

    interactions.yaml
    - id: free_lily
      location: goblin_camp_cages
      target: [lily, cage, girl]          # what the action must refer to
      verbs: [free, release, unlock, pick, open, break, force]
      approaches:                         # first usable one is taken
        - {requires_item: lockpicks, skill: Sleight_of_Hand, dc: 12}
        - {skill: Athletics, dc: 15}
      success: [npc_status:lily:freed, follow:lily, ...]
      success_fact: Lily is free and now follows the hero.
      failure_fact: The lock holds. Lily is still caged.

The outcome (roll, state changes) is decided first; the narrator is told
exactly what happened and describes it. State lives in session.world and is
saved with the game:

    npc_status    {npc_id: "captive" | "freed" | ...}
    npc_location  {npc_id: location_id}   authoritative where set
    followers     [npc_id]                 move with the hero
    done          [interaction_id]
"""

import re
from typing import Any, Dict, List, Optional

from text_match import has_any, has_phrase


def new_world() -> Dict[str, Any]:
    return {"npc_status": {}, "npc_location": {}, "followers": [], "done": []}


def world(session) -> Dict[str, Any]:
    if not isinstance(getattr(session, "world", None), dict):
        session.world = new_world()
    for key, empty in new_world().items():
        session.world.setdefault(key, empty)
    return session.world


def seed_world(session) -> None:
    """New game: NPCs that start in a fixed state (a captive in a cage) are pinned there."""
    state = world(session)
    for npc in (session.npc_manager.get_all_npcs() if session.npc_manager else []):
        if npc.status and npc.id not in state["npc_status"]:
            state["npc_status"][npc.id] = npc.status
            if npc.status == "captive" and npc.location_id:
                state["npc_location"][npc.id] = npc.location_id


# =============================================================================
# WHERE PEOPLE ARE
# =============================================================================

def npc_pinned_location(session, npc_id: str) -> Optional[str]:
    """Where the world model says an NPC is, if it says (captives, followers, moved NPCs)."""
    state = world(session)
    if npc_id in state["followers"]:
        return session.current_location_id or (
            session.location_manager.current_location_id if session.location_manager else None)
    return state["npc_location"].get(npc_id)


def npc_status(session, npc_id: str) -> str:
    return world(session)["npc_status"].get(npc_id, "")


def on_travel(session) -> None:
    """Followers walk with the hero."""
    state = world(session)
    here = session.location_manager.current_location_id if session.location_manager else None
    for npc_id in state["followers"]:
        state["npc_location"][npc_id] = here
        npc = session.npc_manager.get_npc(npc_id) if session.npc_manager else None
        if npc and here:
            npc.location_id = here


def status_lines(session) -> List[str]:
    """World facts for the GM briefing."""
    state = world(session)
    lines = []
    for npc_id, status in state["npc_status"].items():
        npc = session.npc_manager.get_npc(npc_id) if session.npc_manager else None
        name = npc.name if npc else npc_id
        if npc_id in state["followers"]:
            lines.append(f"{name}: {status}, travelling with the hero")
        elif status == "captive":
            lines.append(f"{name}: captive - locked up until the game reports them freed")
        else:
            lines.append(f"{name}: {status}")
    return lines


def status_label(session, npc_id: str) -> str:
    """Short status for the player's People panel ('' when unremarkable)."""
    state = world(session)
    if npc_id in state["followers"]:
        return "With you"
    return {"captive": "Captive", "freed": "Freed"}.get(state["npc_status"].get(npc_id, ""), "")


# =============================================================================
# INTERACTIONS
# =============================================================================

def interactions(session) -> List[Dict[str, Any]]:
    scenario = session.scenario.active_scenario if session.scenario else None
    return list(getattr(scenario, "interactions", None) or [])


def _plain(text: str) -> str:
    return re.sub(r"['’]s(?![a-z])", "", (text or "").lower())


def match_interaction(session, action: str) -> Optional[Dict[str, Any]]:
    """The interaction at this location the action is attempting, if any."""
    here = session.location_manager.current_location_id if session.location_manager else None
    text = _plain(action)
    done = world(session)["done"]
    for inter in interactions(session):
        places = inter.get("location")
        if here not in (places if isinstance(places, list) else [places]):
            continue
        if inter.get("once", True) and inter["id"] in done:
            continue
        targets = inter.get("target") or []
        if has_any(text, inter.get("verbs") or []) and any(has_phrase(text, t) for t in targets):
            return inter
    return None


def _approach(session, inter: Dict[str, Any], action: str) -> Optional[Dict[str, Any]]:
    """First approach the hero can use; one whose tool they name or carry wins."""
    from world_model import carries

    followers = world(session)["followers"]
    usable = [a for a in inter.get("approaches") or [{}]
              if (not a.get("requires_item") or carries(session, a["requires_item"]))
              and (not a.get("requires_follower") or a["requires_follower"] in followers)]
    if not usable:
        return None
    named = [a for a in usable if a.get("requires_item") and
             has_phrase(_plain(action), a["requires_item"].replace("_", " "))]
    return (named or usable)[0]


def resolve_interaction(session, inter: Dict[str, Any], action: str) -> Dict[str, Any]:
    """
    Decide the outcome: roll if the approach needs one, apply effects on
    success. Returns {success, roll, facts, moments}.
    """
    from dm_engine import roll_skill_check

    approach = _approach(session, inter, action)
    hero = session.character.name if session.character else "The hero"
    if approach is None:
        fact = inter.get("blocked_fact") or "The hero has no way to do that yet."
        return {"success": False, "roll": None, "facts": [fact], "moments": []}

    roll = None
    success = True
    if approach.get("skill"):
        roll = roll_skill_check(session.character, approach["skill"], int(approach.get("dc", 12)))
        roll["source"] = "interaction"
        success = bool(roll.get("success"))

    moments: List[str] = []
    if success:
        moments = apply_effects(session, inter.get("success") or [], hero)
        if inter.get("once", True):
            world(session)["done"].append(inter["id"])
        fact = inter.get("success_fact", "It works.")
    else:
        fact = inter.get("failure_fact", "It doesn't work.")
    return {"success": success, "roll": roll, "facts": [fact.replace("{hero}", hero)], "moments": moments}


def apply_effects(session, effects: List[str], hero: str) -> List[str]:
    """Apply an interaction's effects. Returns player-facing moment lines."""
    from world_memory import chronicle, remember

    state = world(session)
    moments: List[str] = []
    for effect in effects:
        kind, _, rest = str(effect).partition(":")
        rest = rest.replace("{hero}", hero)
        if kind == "npc_status":
            npc_id, _, status = rest.partition(":")
            state["npc_status"][npc_id] = status
        elif kind == "follow":
            if rest not in state["followers"]:
                state["followers"].append(rest)
            on_travel(session)  # with the hero from now on
            npc = session.npc_manager.get_npc(rest) if session.npc_manager else None
            if npc:
                moments.append(f"🎉 {npc.name} is with you now.")
        elif kind == "unfollow":
            if rest in state["followers"]:
                state["followers"].remove(rest)
        elif kind == "place":
            npc_id, _, location_id = rest.partition(":")
            state["npc_location"][npc_id] = location_id
            npc = session.npc_manager.get_npc(npc_id) if session.npc_manager else None
            if npc:
                npc.location_id = location_id
        elif kind == "chronicle":
            chronicle(session, rest)
        elif kind == "memory":
            npc_id, _, fact = rest.partition(":")
            npc = session.npc_manager.get_npc(npc_id) if session.npc_manager else None
            if npc:
                remember(npc, fact)
        elif kind == "talked":
            # Counts as speaking with them for quest objectives
            if session.quest_manager:
                session.quest_manager.on_npc_talked(rest)
        elif kind == "objective":
            scenario = session.scenario.active_scenario if session.scenario else None
            if scenario:
                scenario.complete_objective(rest)
        elif kind == "xp" and session.character:
            amount = int(rest)
            session.character.gain_xp(amount, "interaction")
            moments.append(f"⭐ Gained {amount} XP")
    return moments
