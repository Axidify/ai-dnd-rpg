"""
Turn service: the game logic for one player action, independent of transport.

Both /api/game/action (JSON) and /api/game/action/stream (SSE) run a turn
through the same three steps:

    start = start_turn(session, action)       # guards, arbiter, early exits
    ... the endpoint gets narration from the DM model (blocking or streamed) ...
    outcome = finish_turn(session, action, narrator_text, start)

Each step returns an ordered list of events (plain dicts, the same shapes
the SSE stream sends). ``{"type": "chunk", "content": ...}`` events are
player-visible text; everything else is structured data for the UI. The
JSON endpoint joins the chunks into one message; the SSE endpoint yields
each event as it goes. Keeping the rules here means the two endpoints can
no longer drift apart.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from dm_engine import (
    parse_roll_request, parse_combat_request, parse_item_rewards,
    parse_gold_rewards, parse_xp_rewards, parse_buy_transactions,
    parse_gold_costs, parse_recruit_tags,
    roll_skill_check, format_roll_result, strip_dm_tags,
)
from dm_scene import (
    prepare_action_turn,
    build_roll_outcome_narration,
    is_weak_roll_narration,
)
from game_mechanics import (
    complete_ready_quests,
    start_structured_combat,
    apply_scenario_transition,
    is_session_blocked,
    try_hostile_combat_gate,
)
from inventory import get_item, add_item_to_inventory
from text_match import has_any, has_phrase


COMBAT_UNDERWAY_MESSAGE = (
    "⚔️ **Combat is underway!** Use **Attack**, **Defend**, or **Flee** "
    "below — narrative actions are paused until the fight ends."
)
EMPTY_NARRATION_FALLBACK = "The Dungeon Master pauses. *What would you like to do?*"
SOCIAL_BLOCK_MESSAGES = {
    "same_approach": (
        "*You consider pressing the same point again, but something in the NPC's "
        "expression tells you it would be futile. They've made their position clear, "
        "and repeating yourself would only damage what rapport remains.*\n\n"
        "Perhaps try a different approach, or accept the situation as it stands."
    ),
    "npc_hostile": (
        "*You move to speak, but the person pointedly turns away from you. Whatever "
        "chance you had with them has passed. Their body language makes it abundantly "
        "clear: this conversation is over.*\n\nYou'll need to find another way forward."
    ),
}


def chunk(text: str) -> Dict[str, Any]:
    return {"type": "chunk", "content": text}


def message_text(events: List[Dict[str, Any]]) -> str:
    """Join the player-visible text of a list of events."""
    return "".join(e["content"] for e in events if e["type"] == "chunk")


def _record_dm_message(session, content: str, **extra) -> None:
    session.messages.append({
        "type": "dm",
        "content": content,
        "timestamp": datetime.now().isoformat(),
        **extra,
    })


# =============================================================================
# DETECTION HELPERS
# =============================================================================

def detect_npc_talk(action: str, npc_manager) -> list:
    """
    Detect if a player action involves talking to an NPC.

    Returns:
        List of NPC IDs that were talked to
    """
    if not npc_manager:
        return []

    talked_to = []
    action_lower = action.lower()

    # Common talk patterns
    talk_patterns = [
        r"talk\s+(?:to|with)\s+(\w+)",
        r"speak\s+(?:to|with)\s+(\w+)",
        r"greet\s+(\w+)",
        r"ask\s+(\w+)",
        r"approach\s+(\w+)",
        r"hello\s+(\w+)",
    ]

    for pattern in talk_patterns:
        matches = re.findall(pattern, action_lower)
        for name in matches:
            # Check if this name matches any NPC
            for npc in npc_manager.get_all_npcs():
                if name.lower() in npc.name.lower() or name.lower() == npc.id.lower():
                    if npc.id not in talked_to:
                        talked_to.append(npc.id)

    return talked_to


# Extra words that tie a DM reply to a specific quest (beyond its name)
QUEST_KEYWORDS = {
    "rescue_lily": ["lily", "daughter", "save her"],
    "clear_the_path": ["road", "wolves", "safer"],
    "chiefs_treasure": ["treasure", "hoard", "grotnak"],
    "recover_heirlooms": ["heirloom", "heirlooms", "locket", "ring"],
}
ACCEPT_PATTERNS = [
    r"\byes\b", r"\baccept\b", r"\bi('ll| will) help\b", r"\bagree\b",
    r"\bcount me in\b", r"\bi'm in\b", r"\blet's do it\b", r"\bi'll save\b",
    r"\blet me help\b", r"\bof course\b", r"\bvery well\b", r"\bi'll do it\b",
]


def detect_quest_acceptance(player_action: str, dm_response: str, quest_manager, npc_manager=None) -> list:
    """
    Detect which quest(s) the player just accepted.

    The player must say something accept-like. The quest giver is the one
    the player named, else the first quest giver the DM's reply mentions;
    only that giver's quests are considered (agreeing to help Bram must not
    also accept the barkeep's quests). Of those, quests the reply refers to
    (by name or keywords) are accepted; failing that, the giver's first
    available quest. Prerequisites are enforced by accept_quest().

    Returns:
        List of quest IDs that were accepted
    """
    if not quest_manager:
        return []
    action_lower = player_action.lower()
    response_lower = dm_response.lower()
    if not any(re.search(pat, action_lower) for pat in ACCEPT_PATTERNS):
        return []

    def giver_names(giver_id):
        names = [giver_id.replace("_", " ")]
        npc = npc_manager.get_npc(giver_id) if npc_manager else None
        if npc:
            names.append(npc.name.lower())
            names.extend(part for part in npc.name.lower().split() if len(part) > 3)
        return names

    by_giver = {}
    for quest_id, quest in quest_manager.available_quests.items():
        if quest.giver_npc_id:
            by_giver.setdefault(quest.giver_npc_id.lower(), []).append((quest_id, quest))
    if not by_giver:
        return []

    named = [g for g in by_giver if has_any(action_lower, giver_names(g))]
    if named:
        givers = named
    else:
        positions = []
        for g in by_giver:
            hits = [m.start() for name in giver_names(g)
                    for m in re.finditer(rf"\b{re.escape(name)}\b", response_lower)]
            if hits:
                positions.append((min(hits), g))
        givers = [min(positions)[1]] if positions else []

    accepted = []
    for giver in givers:
        quests = by_giver[giver]
        specific = [
            quest_id for quest_id, quest in quests
            if has_phrase(response_lower, quest.name.lower())
            or has_any(response_lower, QUEST_KEYWORDS.get(quest_id, []))
        ]
        for quest_id in specific or [quests[0][0]]:
            if quest_manager.accept_quest(quest_id):
                accepted.append(quest_id)
    return accepted


# =============================================================================
# TURN STEPS
# =============================================================================

@dataclass
class TurnStart:
    """Result of start_turn.

    If ``finished`` is True the turn ended before the narrator (combat lock,
    game over, hostile action, scripted response, blocked social retry) and
    ``events`` is the whole reply. Otherwise the endpoint must narrate and
    call finish_turn; ``events`` holds anything to send before narration.
    """
    finished: bool
    events: List[Dict[str, Any]] = field(default_factory=list)
    # Extra keys for the JSON endpoint's response body
    response: Dict[str, Any] = field(default_factory=dict)
    arbiter_roll_result: Optional[dict] = None
    scene_action: Optional[str] = None
    arbiter_no_roll: bool = False


@dataclass
class TurnOutcome:
    """Result of finish_turn: post-narration events plus a summary."""
    events: List[Dict[str, Any]]
    roll_result: Optional[dict] = None
    combat_started: bool = False
    items_gained: List[str] = field(default_factory=list)
    gold_gained: int = 0
    xp_gained: int = 0
    leveled_up: bool = False
    quests_accepted: List[str] = field(default_factory=list)


def _finished(session, text: str, extra_events=(), record_extra=None, response=None) -> TurnStart:
    _record_dm_message(session, text, **(record_extra or {}))
    return TurnStart(
        finished=True,
        events=[chunk(text), *extra_events],
        response=response or {},
    )


def start_turn(session, action: str) -> TurnStart:
    """Record the player's action and run every rule that comes before narration."""
    session.touch()
    session.messages.append({
        "type": "player",
        "content": action,
        "timestamp": datetime.now().isoformat(),
    })

    if session.in_combat:
        return _finished(session, COMBAT_UNDERWAY_MESSAGE)

    blocked, _ = is_session_blocked(session)
    if blocked:
        session.game_over = True
    if session.game_over:
        text = f"🎮 **GAME OVER**\n\n{session.game_over_reason}\n\n*Start a new game to try again.*"
        return _finished(
            session, text,
            extra_events=[{"type": "game_over", "reason": session.game_over_reason}],
            record_extra={"game_over": True},
            response={"game_over": True},
        )

    # Hostile action → structured combat (before narrator)
    hostile = try_hostile_combat_gate(session, action)
    if hostile:
        return _finished(
            session, hostile["message"],
            extra_events=[{"type": "combat", "enemies": hostile.get("enemies", [])}],
            response={"combat_started": True},
        )

    # Phase 1: arbiter + scene rules
    context_for_arbiter = f"Location: {session.current_location or 'Unknown'}"
    if session.quest_manager:
        active_quests = session.quest_manager.get_active_quests()
        if active_quests:
            context_for_arbiter += f"\nActive quests: {', '.join(q.name for q in active_quests)}"

    turn = prepare_action_turn(session, action, context_for_arbiter)
    arbiter_roll_result = turn["arbiter_roll_result"]

    if arbiter_roll_result:
        decision = turn["arbiter_decision"]
        print(
            f"   🎲 Arbiter ({decision.source}): {arbiter_roll_result['skill']} "
            f"DC {arbiter_roll_result['dc']} = {arbiter_roll_result['total']} "
            f"({'✓' if arbiter_roll_result['success'] else '✗'})"
        )
    if turn.get("social_failure_info"):
        info = turn["social_failure_info"]
        print(f"   ⚠️ Social failure recorded ({info['failures']}/{info['max_failures']})")

    if turn.get("deterministic_response"):
        return _finished(session, turn["deterministic_response"])

    if turn["social_blocked"]:
        reason = turn["social_block_reason"]
        text = SOCIAL_BLOCK_MESSAGES.get(reason) or session.game_over_reason or "You cannot proceed with this action."
        return _finished(
            session, text,
            extra_events=[{"type": "blocked", "reason": reason}],
            record_extra={"blocked": True},
            response={"blocked": True, "block_reason": reason},
        )

    pre_events = []
    if arbiter_roll_result:
        # The UI renders the roll card before the narration arrives
        pre_events.append({"type": "roll", "result": arbiter_roll_result})

    return TurnStart(
        finished=False,
        events=pre_events,
        arbiter_roll_result=arbiter_roll_result,
        scene_action=turn["scene_action"],
        arbiter_no_roll=turn["arbiter_no_roll"],
    )


SEARCH_SKILLS = {"perception", "investigation"}


def _apply_search_discoveries(session, roll: Optional[dict], events: List[Dict[str, Any]], say) -> None:
    """
    On a successful Perception/Investigation roll, reveal what that roll beats:
    secret exits from the current location ("skill:<skill>:<dc>" discovery
    conditions) and hidden items here. Discovery is mechanical, so it happens
    whatever the narrator chose to describe.
    """
    if not roll or not roll.get("success"):
        return
    if str(roll.get("skill", "")).replace("_", " ").lower() not in SEARCH_SKILLS:
        return
    manager = session.location_manager
    here = manager.get_current_location() if manager else None
    if not here:
        return
    total = roll.get("total", 0)

    for exit_name, dest_id in here.exits.items():
        dest = manager.locations.get(dest_id)
        if not dest or not dest.hidden or dest_id in manager.discovered_secrets:
            continue
        parts = (dest.discovery_condition or "").split(":")
        if len(parts) == 3 and parts[0] == "skill" and parts[2].isdigit() and total >= int(parts[2]):
            if manager.discover_secret(dest_id):
                events.append({"type": "discovery", "location_id": dest_id, "exit": exit_name})
                say(f"\n\n🔍 You discover a hidden way: **{dest.name}** ({exit_name}).")

    for hidden in list(here.get_undiscovered_hidden_items()):
        if total < hidden.dc or not here.discover_hidden_item(hidden.item_id):
            continue
        item = get_item(hidden.item_id)
        if not (item and session.character):
            continue
        add_item_to_inventory(session.character.inventory, item)
        if hidden.item_id in here.items:
            here.items.remove(hidden.item_id)
        events.append({"type": "item", "item": hidden.item_id, "message": f"Found: {item.name}"})
        say(f"\n\n🔍 Hidden away, you find: **{item.name}**.")
        if session.quest_manager:
            for quest_id, objective in session.quest_manager.on_item_acquired(hidden.item_id):
                quest = session.quest_manager.get_quest(quest_id)
                if quest:
                    events.append({"type": "quest_update", "quest_id": quest_id,
                                   "objective_id": objective.id, "quest": quest.to_dict()})


TAKE_VERBS = ["take", "grab", "pick up", "pocket", "loot", "collect", "snatch", "gather"]
TAKE_ALL = ["everything", "all of it", "it all", "the loot"]


def _apply_pickups(session, action: str, roll: Optional[dict], events: List[Dict[str, Any]], say) -> set:
    """
    Pick up items listed at the current location that the player asked to
    take (by name, key or main noun, or "everything"). Skipped if the action
    called for a roll and the roll failed. Gold pouches become gold.
    Returns the names of items picked up.
    """
    picked = set()
    if roll and not roll.get("success"):
        return picked
    if not has_any(action, TAKE_VERBS):
        return picked
    manager = session.location_manager
    here = manager.get_current_location() if manager else None
    character = session.character
    if not (here and character and here.items):
        return picked

    take_all = has_any(action, TAKE_ALL)
    for key in list(here.items):
        item = get_item(key)
        if not item:
            continue
        noun = item.name.split()[-1].strip("'").lower()
        wanted = take_all or has_any(action, [item.name.lower(), key.replace("_", " "), noun])
        if not wanted:
            continue
        here.items.remove(key)
        picked.add(item.name)
        if key.startswith("gold_"):
            character.gold += item.value
            events.append({"type": "gold", "amount": item.value, "total": character.gold})
            say(f"\n\n💰 You take the {item.name.lower()}: {item.value} gold (Total: {character.gold})")
            continue
        add_item_to_inventory(character.inventory, item)
        events.append({"type": "item", "item": key, "message": f"Took: {item.name}"})
        say(f"\n\n📦 You take: {item.name}")
        if session.quest_manager:
            for quest_id, objective in session.quest_manager.on_item_acquired(key):
                quest = session.quest_manager.get_quest(quest_id)
                if quest:
                    events.append({"type": "quest_update", "quest_id": quest_id,
                                   "objective_id": objective.id, "quest": quest.to_dict()})
    return picked


def finish_turn(
    session,
    action: str,
    narrator_text: str,
    start: TurnStart,
    shown_narration: Optional[str] = None,
) -> TurnOutcome:
    """
    Apply the mechanics in the narrator's raw text (control tags included)
    and record the turn. ``narrator_text`` is the unfiltered DM output; the
    player-visible narration has already been sent by the endpoint, so the
    returned events only cover what comes after it. ``shown_narration`` is
    that visible text when it differs from strip_dm_tags(narrator_text)
    (the streaming filter), so the transcript matches what was displayed.
    """
    events: List[Dict[str, Any]] = []
    # Everything the player sees this turn, for the transcript
    display_parts = [strip_dm_tags(narrator_text) if shown_narration is None else shown_narration]

    def say(text: str) -> None:
        display_parts.append(text)
        events.append(chunk(text))

    character = session.character
    arbiter_roll_result = start.arbiter_roll_result
    outcome = TurnOutcome(events=events, roll_result=arbiter_roll_result)

    # Fallback for empty narration, or a setup line that never states the roll outcome
    clean_narration = strip_dm_tags(narrator_text).strip()
    needs_fallback = not clean_narration
    if arbiter_roll_result and is_weak_roll_narration(clean_narration, arbiter_roll_result):
        needs_fallback = True
    if needs_fallback:
        text = (
            build_roll_outcome_narration(session, action, arbiter_roll_result)
            if arbiter_roll_result else EMPTY_NARRATION_FALLBACK
        )
        # Start a new paragraph after whatever thin narration was shown
        say(f"\n\n{text}" if clean_narration else text)

    # The narrator may request a roll only if the arbiter didn't already decide
    if not arbiter_roll_result and not start.arbiter_no_roll:
        skill, dc = parse_roll_request(narrator_text)
        if skill and dc and character:
            result = roll_skill_check(character, skill, dc)
            outcome.roll_result = {
                "skill": result["skill"],
                "roll": result["roll"],
                "modifier": result["modifier"],
                "total": result["total"],
                "dc": dc,
                "success": result["success"],
                "formatted": format_roll_result(result),
                "source": "narrator_ai",
            }
            events.append({"type": "roll", "result": outcome.roll_result})

    # A successful search can reveal secret exits and hidden items here
    _apply_search_discoveries(session, outcome.roll_result, events, say)

    # [COMBAT: ...]
    enemies, surprise = parse_combat_request(narrator_text)
    if enemies:
        outcome.combat_started = True
        start_structured_combat(session, enemies, surprise)
        events.append({"type": "combat", "enemies": enemies})
        say(f"\n\n⚔️ COMBAT STARTED! Enemies: {', '.join(enemies)}")

    # "I take the key": pick up items lying here, whatever the narrator does
    picked = _apply_pickups(session, action, outcome.roll_result, events, say)

    # [ITEM: name]
    for item_name in parse_item_rewards(narrator_text):
        item = get_item(item_name)
        if not (item and character):
            continue
        if item.name in picked:
            continue  # already picked up deterministically this turn
        add_item_to_inventory(character.inventory, item)
        outcome.items_gained.append(item_name)
        events.append({"type": "item", "item": item_name, "message": f"Received: {item.name}"})
        say(f"\n\n📦 Received: {item.name}")
        if session.quest_manager:
            completed = session.quest_manager.on_item_acquired(item_name.lower().replace(" ", "_"))
            for quest_id, objective in completed:
                quest = session.quest_manager.get_quest(quest_id)
                if quest:
                    events.append({"type": "quest_update", "quest_id": quest_id,
                                   "objective_id": objective.id, "quest": quest.to_dict()})

    # [GOLD: amount]
    gold_gained = parse_gold_rewards(narrator_text)
    if gold_gained > 0 and character:
        character.gold += gold_gained
        outcome.gold_gained = gold_gained
        events.append({"type": "gold", "amount": gold_gained, "total": character.gold})
        say(f"\n\n💰 Received {gold_gained} gold (Total: {character.gold})")

    # [XP: amount | reason]
    for xp_amount, reason in parse_xp_rewards(narrator_text):
        if not character:
            continue
        leveled_up = bool(character.gain_xp(xp_amount, reason).get("level_up", False))
        outcome.xp_gained += xp_amount
        outcome.leveled_up = outcome.leveled_up or leveled_up
        events.append({"type": "xp", "amount": xp_amount, "reason": reason, "leveled_up": leveled_up})
        say(f"\n\n⭐ Gained {xp_amount} XP: {reason}" + (" 🎉 LEVEL UP!" if leveled_up else ""))

    # [BUY: item, price]
    for item_name, price in parse_buy_transactions(narrator_text):
        if not (character and character.gold >= price):
            continue
        item = get_item(item_name)
        if item:
            character.gold -= price
            add_item_to_inventory(character.inventory, item)
            events.append({"type": "buy", "item": item_name, "price": price,
                           "gold_remaining": character.gold})
            say(f"\n\n🛒 Purchased {item_name} for {price} gold (Gold: {character.gold})")

    # [PAY: amount, reason] — hiring, bribes, etc.
    for cost, reason in parse_gold_costs(narrator_text):
        if character and character.gold >= cost:
            character.gold -= cost
            events.append({"type": "pay", "amount": cost, "reason": reason,
                           "gold_remaining": character.gold})
            say(f"\n\n💸 Paid {cost} gold: {reason} (Gold: {character.gold})")
            print(f"   💸 Paid {cost} gold: {reason}")

    # [RECRUIT: npc_id]
    for npc_id in parse_recruit_tags(narrator_text):
        from party import get_recruitable_npc, Party
        if not session.party:
            session.party = Party()
        if session.party.is_full:
            continue
        member = get_recruitable_npc(npc_id)
        if member:
            session.party.add_member(member)
            events.append({"type": "recruit", "npc_id": npc_id, "name": member.name})
            say(f"\n\n🎉 {member.name} joins your party!")
            print(f"   🎉 {member.name} joined the party!")

    # Quest objectives for talking to NPCs
    if session.quest_manager and session.npc_manager:
        for npc_id in detect_npc_talk(action, session.npc_manager):
            for quest_id, objective in session.quest_manager.on_npc_talked(npc_id):
                quest = session.quest_manager.get_quest(quest_id)
                if quest:
                    events.append({"type": "quest_update", "quest_id": quest_id,
                                   "objective_id": objective.id, "quest": quest.to_dict()})
                    say(f"\n\n📜 Quest Objective Complete: {objective.description}")

    # Quest acceptance
    outcome.quests_accepted = detect_quest_acceptance(
        action, narrator_text, session.quest_manager, session.npc_manager
    )
    for quest_id in outcome.quests_accepted:
        quest = session.quest_manager.get_quest(quest_id)
        if quest and character:
            # Items you already carry count toward "find" objectives
            from inventory import find_item_in_inventory
            for objective in quest.objectives:
                if objective.objective_type.name in ("FIND_ITEM", "COLLECT") and \
                        find_item_in_inventory(character.inventory, objective.target):
                    session.quest_manager.on_item_acquired(objective.target)
        if quest:
            events.append({"type": "quest_accepted", "quest_id": quest_id, "quest": quest.to_dict()})
            say(f"\n\n📜 Quest Accepted: {quest.name}")
            print(f"   📜 Quest accepted: {quest.name}")

    # Quests whose objectives are now all done pay out
    for quest_msg in complete_ready_quests(session):
        say(f"\n\n{quest_msg}")
        events.append({"type": "quest_completed", "message": quest_msg})

    # Scene transitions and adventure progress
    if session.scenario:
        session.scenario.record_exchange()
    transition = apply_scenario_transition(session, action, narrator_text)
    if transition:
        say(f"\n\n{transition}")
        events.append({"type": "transition", "message": transition})

    if session.game_over:
        say(f"\n\n---\n\n🎮 **GAME OVER**\n\n{session.game_over_reason}")
        events.append({"type": "game_over", "reason": session.game_over_reason})
    else:
        warning = session.get_social_warning()
        if warning:
            say(f"\n\n{warning}")
            events.append({"type": "warning", "message": warning})

    _record_dm_message(
        session,
        "".join(display_parts).strip(),
        roll_result=outcome.roll_result,
        combat_started=outcome.combat_started,
        game_over=session.game_over,
    )
    return outcome
