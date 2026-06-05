"""
Scene-aware DM rules: when to roll, fail-forward outcomes, repeat-action handling.

Implements table-DM best practices:
- Free scene survey on first vague look (no roll)
- Redirect on repeat vague looks (no roll loop)
- Rolls only for specific searches / uncertain outcomes
- Success = actionable clue; failure = complication (fail forward)
"""

from __future__ import annotations

import random
import re
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from dm_arbiter import ArbiterDecision

# ---------------------------------------------------------------------------
# Location hooks (actionable leads + fail-forward complications)
# ---------------------------------------------------------------------------

LOCATION_DATA: Dict[str, Dict[str, Any]] = {
    "village square": {
        "interactables": [
            "**The Rusty Dragon** tavern to the west — warm light and muffled voices.",
            "**The blacksmith's forge** to the east — hammer on anvil, sparks in the soot.",
            "**A worried crowd at the well** — hushed talk of missing livestock and goblin caves to the north.",
        ],
        "success_clues": [
            "Fresh mud with **clawed prints** trails from the well toward the **northern road**.",
            "A merchant hurriedly scrubs a **chalk goblin mark** off a crate — someone told him to stay quiet.",
            "You catch a fragment of conversation: *\"…took a calf two nights ago, near the old mill road…\"*",
        ],
        "failure_complications": [
            "You miss the subtle signs, but your staring makes the **well crowd go quiet**. A woman points toward the tavern: *\"Ask Bren if you're heading north.\"*",
            "Nothing hidden reveals itself — yet a **town crier** passes, calling for volunteers to investigate **goblin caves**.",
            "A guard notices your scrutiny: *\"Lost, traveler? Tavern's west if you need directions.\"* — his hand rests on his club.",
        ],
    },
    "_default": {
        "interactables": [
            "Points of interest nearby that invite closer inspection.",
            "Locals or travelers who might know more if approached.",
            "Paths, doors, or landmarks that suggest where to go next.",
        ],
        "success_clues": [
            "You spot something **out of place** — a detail others seem to have missed.",
            "A small sign of recent trouble: disturbed earth, a dropped token, a hurried footprint.",
        ],
        "failure_complications": [
            "You find nothing new, but **someone nearby takes notice** of your searching — curious, wary, or helpful.",
            "The moment passes without a lead, though the **obvious options** around you remain open.",
        ],
    },
}


VAGUE_SURVEY_PATTERNS = [
    "look around",
    "look about",
    "look carefully around",
    "take in my surroundings",
    "take in the surroundings",
    "take in your surroundings",
    "survey the area",
    "survey the scene",
    "what do i see",
    "what can i see",
    "glance around",
    "observe my surroundings",
    "observe the area",
    "get my bearings",
    "size up the area",
    "scan the area",
]

SPECIFIC_SEARCH_PATTERNS = [
    "search for",
    "look for",
    "examine ",
    "inspect ",
    "investigate ",
    "check for",
    "look under",
    "look behind",
    "look closely at",
    "look closely",
    "peer at",
    "peer into",
    "anything hidden",
    "hidden door",
    "hidden trap",
    "secret ",
    "tracks",
    "clue",
    "eavesdrop",
    "listen in",
    "listen closely",
    "read the",
    "study the",
    "scrutinize",
]


def classify_exploration_action(action: str) -> str:
    """Return 'vague_survey', 'specific_search', or 'other'."""
    lower = action.lower().strip()
    if any(p in lower for p in SPECIFIC_SEARCH_PATTERNS):
        return "specific_search"
    if any(p in lower for p in VAGUE_SURVEY_PATTERNS):
        return "vague_survey"
    if re.match(r"^(i )?(look|scan|observe|survey)\b", lower) and not any(
        w in lower for w in ("for", "at", "under", "behind", "into")
    ):
        return "vague_survey"
    return "other"


def get_scene_key(session) -> str:
    if getattr(session, "current_location_id", None):
        return str(session.current_location_id)
    return (session.current_location or "unknown").lower()


def _ensure_scene_state(session) -> Dict[str, Any]:
    if not getattr(session, "scene_state", None):
        session.scene_state = {}
    return session.scene_state


def get_survey_count(session) -> int:
    state = _ensure_scene_state(session)
    key = get_scene_key(session)
    return int(state.get("survey_counts", {}).get(key, 0))


def increment_survey_count(session) -> int:
    state = _ensure_scene_state(session)
    counts = state.setdefault("survey_counts", {})
    key = get_scene_key(session)
    counts[key] = counts.get(key, 0) + 1
    return counts[key]


def build_scene_context_for_arbiter(session) -> str:
    key = get_scene_key(session)
    count = get_survey_count(session)
    loc = session.current_location or "Unknown"
    return (
        f"Location: {loc}\n"
        f"Scene surveys at this location: {count}\n"
        f"Exploration note: vague 'look around' with survey_count>=1 should NOT re-roll; "
        f"redirect player to interact. Only specific searches warrant Perception/Investigation."
    )


def apply_scene_arbiter_rules(action: str, decision, session):
    """Adjust arbiter decision using scene memory. Returns (decision, scene_action)."""
    from dm_arbiter import ArbiterDecision, ActionType

    exploration = classify_exploration_action(action)

    if exploration == "vague_survey":
        count = get_survey_count(session)
        if count >= 1:
            return ArbiterDecision(
                action_type=ActionType.EXPLORATION.value,
                requires_roll=False,
                reasoning="Repeat vague survey — redirect, no re-roll",
                source="scene_override",
            ), "survey_repeat"
        return ArbiterDecision(
            action_type=ActionType.EXPLORATION.value,
            requires_roll=False,
            reasoning="First vague survey — free scene description, no roll",
            source="scene_override",
        ), "survey_first"

    if exploration == "specific_search":
        skill = "Investigation" if any(
            w in action.lower() for w in ("examine", "inspect", "investigate", "study", "read")
        ) else "Perception"
        return ArbiterDecision(
            action_type=ActionType.EXPLORATION.value,
            requires_roll=True,
            skill=skill,
            dc=12,
            reasoning="Specific search for hidden details",
            source="scene_override",
        ), "specific_search"

    return decision, "none"


def _location_data(session) -> Dict[str, Any]:
    loc = (session.current_location or "").lower()
    if loc in LOCATION_DATA:
        return LOCATION_DATA[loc]
    for key, data in LOCATION_DATA.items():
        if key != "_default" and key in loc:
            return data
    return LOCATION_DATA["_default"]


def build_scene_redirect_narration(session) -> str:
    """Deterministic response when player repeats vague looking."""
    loc = session.current_location or "this place"
    data = _location_data(session)
    hooks = data["interactables"]
    hook_lines = "\n".join(f"- {h}" for h in hooks[:3])
    return (
        f"You've already taken in **{loc}**. The scene hasn't changed — "
        f"the square won't reveal more until you **engage** with something.\n\n"
        f"**Where will you go?**\n{hook_lines}\n\n"
        f"*Approach someone, enter a building, or examine something specific.*"
    )


def build_survey_dm_instruction(session) -> str:
    """Strict narrator instruction for first free survey (no roll)."""
    data = _location_data(session)
    hooks = "\n".join(f"- {h}" for h in data["interactables"][:3])
    loc = session.current_location or "the area"
    return f"""[SCENE SURVEY — NO SKILL CHECK]
The player is getting their bearings at {loc}. This is a FREE survey — do NOT request any [ROLL:] tags.

Your job:
1. Briefly acknowledge what they notice (1 short paragraph — sensory details they already could see).
2. Present exactly these points of interest (you may rephrase, keep the leads):
{hooks}
3. End by asking what they focus on or where they go next.

Do NOT call for Perception or Investigation. Do NOT describe hidden secrets yet — those require a specific search."""


def build_roll_outcome_instruction(action: str, roll_result: dict) -> str:
    """Extra narrator constraints for resolved exploration rolls."""
    success = roll_result.get("success")
    skill = roll_result.get("skill", "Check")
    base = (
        f"\n\nOUTCOME RULES (mandatory):\n"
        f"- The {skill} check is ALREADY resolved. Do NOT add [ROLL:] tags.\n"
    )
    if success:
        base += (
            "- SUCCESS: Reveal ONE concrete, actionable clue the player can follow "
            "(a name, direction, object, footprint, overheard line). Not vague atmosphere.\n"
            "- Do NOT repeat the setup paragraph about scanning the area.\n"
        )
    else:
        base += (
            "- FAILURE (fail forward): The player misses the hidden detail, BUT something still "
            "happens — an NPC reacts, a rumor reaches them, they feel watched, or a lead appears "
            "through complication. Never end with only 'you notice nothing'.\n"
            "- Do NOT repeat the setup paragraph about scanning the area.\n"
        )
    return base


def build_roll_outcome_narration(session, action: str, roll_result: dict) -> str:
    """Deterministic fail-forward / success payoff when AI narration is weak."""
    data = _location_data(session)
    skill = roll_result.get("skill", "check")

    if roll_result.get("is_nat_20"):
        clue = random.choice(data["success_clues"])
        return (
            f"**Critical success!** Your {skill.lower()} is uncanny. {clue}\n\n"
            f"*What do you do with this lead?*"
        )
    if roll_result.get("is_nat_1"):
        comp = random.choice(data["failure_complications"])
        return (
            f"**Critical failure** on your {skill.lower()} — the worst timing. {comp}\n\n"
            f"*How do you recover?*"
        )
    if roll_result.get("success"):
        clue = random.choice(data["success_clues"])
        return (
            f"Your {skill.lower()} pays off. {clue}\n\n"
            f"*What do you do next?*"
        )
    comp = random.choice(data["failure_complications"])
    return (
        f"Your {skill.lower()} comes up short, but the scene doesn't freeze. {comp}\n\n"
        f"*Try another approach?*"
    )


def is_weak_roll_narration(text: str, roll_result: Optional[dict]) -> bool:
    """Detect setup-only narration that ignores roll outcome."""
    if not roll_result or not text:
        return bool(roll_result)

    lower = text.lower()
    payoff_words = [
        "notice", "spot", "find", "discover", "reveal", "catch", "see",
        "mark", "track", "clue", "print", "sign", "overhear", "whisper",
        "trail", "hidden", "chalk", "mud", "fragment",
    ]
    complication_words = [
        "but", "however", "miss", "quiet", "wary", "suspicious", "point",
        "call out", "notice you", "approach", "interrupt", "crier", "guard",
        "ask", "toward the", "instead",
    ]
    if roll_result.get("success") and any(w in lower for w in payoff_words):
        return False
    if not roll_result.get("success") and any(w in lower for w in complication_words):
        return False
    if len(text.strip()) < 100:
        return True

    setup_phrases = [
        "you narrow your eyes",
        "you scan",
        "you look",
        "you focus",
        "you search",
        "you observe",
        "you take a moment",
        "you sharpen your focus",
        "tuning out",
    ]
    has_setup = any(p in lower for p in setup_phrases)

    if roll_result.get("success"):
        if has_setup and not any(w in lower for w in payoff_words):
            return True
    else:
        if has_setup and not any(w in lower for w in complication_words):
            return True

    return False


def prepare_action_turn(session, action: str, context_for_arbiter: str) -> Dict[str, Any]:
    """
    Run arbiter + scene rules for one player action.
    Returns dict with arbiter_decision, arbiter_roll_result, scene_action,
    social_blocked, social_block_reason, deterministic_response, is_social_check.
    """
    from dm_arbiter import get_arbiter_decision
    from dm_engine import roll_skill_check, format_roll_result

    scene_context = build_scene_context_for_arbiter(session)
    arbiter_decision = get_arbiter_decision(
        action, context_for_arbiter, scene_context=scene_context
    )
    arbiter_decision, scene_action = apply_scene_arbiter_rules(
        action, arbiter_decision, session
    )

    out: Dict[str, Any] = {
        "arbiter_decision": arbiter_decision,
        "arbiter_roll_result": None,
        "scene_action": scene_action,
        "social_blocked": False,
        "social_block_reason": None,
        "deterministic_response": None,
        "is_social_check": (
            arbiter_decision.action_type == "social" and arbiter_decision.requires_roll
        ),
        "arbiter_no_roll": not arbiter_decision.requires_roll,
    }

    if scene_action == "survey_repeat":
        out["deterministic_response"] = build_scene_redirect_narration(session)
        increment_survey_count(session)
        return out

    if scene_action == "survey_first":
        increment_survey_count(session)

    if out["is_social_check"]:
        blocked, reason = session.is_social_retry_blocked(
            npc_context=context_for_arbiter,
            skill=arbiter_decision.skill,
        )
        if blocked:
            out["social_blocked"] = True
            out["social_block_reason"] = reason
            return out

    if arbiter_decision.requires_roll and session.character:
        result = roll_skill_check(
            session.character, arbiter_decision.skill, arbiter_decision.dc
        )
        out["arbiter_roll_result"] = {
            "skill": result["skill"],
            "roll": result["roll"],
            "modifier": result["modifier"],
            "total": result["total"],
            "dc": arbiter_decision.dc,
            "success": result["success"],
            "is_nat_20": result.get("is_nat_20", False),
            "is_nat_1": result.get("is_nat_1", False),
            "formatted": format_roll_result(result),
            "source": arbiter_decision.source,
            "action_type": arbiter_decision.action_type,
        }
        if out["is_social_check"] and not out["arbiter_roll_result"]["success"]:
            out["social_failure_info"] = session.record_social_failure(
                npc_context=context_for_arbiter,
                skill=arbiter_decision.skill,
            )

    return out
