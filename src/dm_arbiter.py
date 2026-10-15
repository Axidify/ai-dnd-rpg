"""
DM Arbiter - Structured rules classifier for d20 rules mechanics.

This module implements a Two-Phase AI approach:
Phase 1 (Arbiter): Decides if an action requires a skill check (structured JSON output)
Phase 2 (Narrator): Writes the narrative response (handled by dm_engine)

The arbiter is separate from the narrator to prevent "narrative temptation" - 
the tendency for AI to skip mechanics for storytelling purposes.
"""

import json
import re
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

from text_match import has_any

# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class ActionType(Enum):
    SOCIAL = "social"
    EXPLORATION = "exploration"
    COMBAT = "combat"
    STEALTH = "stealth"
    PHYSICAL = "physical"
    KNOWLEDGE = "knowledge"
    MOVEMENT = "movement"
    OTHER = "other"


class SkillName(Enum):
    """Valid skills."""
    PERSUASION = "Persuasion"
    INTIMIDATION = "Intimidation"
    DECEPTION = "Deception"
    INSIGHT = "Insight"
    PERCEPTION = "Perception"
    INVESTIGATION = "Investigation"
    STEALTH = "Stealth"
    ATHLETICS = "Athletics"
    ACROBATICS = "Acrobatics"
    ARCANA = "Arcana"
    HISTORY = "History"
    NATURE = "Nature"
    RELIGION = "Religion"
    SURVIVAL = "Survival"
    MEDICINE = "Medicine"
    ANIMAL_HANDLING = "Animal_Handling"
    SLEIGHT_OF_HAND = "Sleight_of_Hand"
    PERFORMANCE = "Performance"


@dataclass
class ArbiterDecision:
    """The structured output from the arbiter AI."""
    action_type: str
    requires_roll: bool
    skill: Optional[str] = None
    dc: Optional[int] = None
    reasoning: str = ""
    source: str = "arbiter_ai"  # "code_override", "arbiter_ai", "fallback"
    combat_enemies: Optional[List[str]] = None  # For combat triggers
    surprise: bool = False


# =============================================================================
# CODE OVERRIDES (100% RELIABLE - AI CANNOT BYPASS)
# =============================================================================

def _roll(action_type: ActionType, skill: str, dc: int, reasoning: str) -> ArbiterDecision:
    return ArbiterDecision(
        action_type=action_type.value,
        requires_roll=True,
        skill=skill,
        dc=dc,
        reasoning=reasoning,
        source="code_override",
    )


def _no_roll(reasoning: str) -> ArbiterDecision:
    return ArbiterDecision(
        action_type=ActionType.SOCIAL.value,
        requires_roll=False,
        reasoning=reasoning,
        source="code_override",
    )


# Keyword tables. All matching is whole-word (see text_match), so "bow"
# does not fire on "crossbow" and "now" does not fire on "know".
MONEY_KEYWORDS = ["gold", "coin", "coins", "pay", "price", "cost", "silver", "copper", "gp", "sp", "cp"]
NEGOTIATION_KEYWORDS = [
    "more", "less", "discount", "upfront", "advance", "deposit", "downpayment",
    "down payment", "negotiate", "bargain", "deal", "counter", "counteroffer", "haggle",
    "take it or leave it", "final offer", "best price", "lower", "higher", "half",
    "double", "triple", "extra", "bonus", "installment",
]
INTIMIDATION_SIGNALS = ["take it or leave it", "demand", "or else", "threaten", "final", "now"]
DECEPTION_KEYWORDS = [
    "lie", "lies", "lied", "lying", "bluff", "deceive", "trick", "fool",
    "pretend", "fake", "disguise", "false", "fabricate", "mislead",
]
THREAT_KEYWORDS = [
    "threaten", "intimidate", "scare", "menace", "demand", "or else",
    "i'll kill", "i will kill",
]
SPECIFIC_SEARCH_KEYWORDS = [
    "search", "look for", "examine", "inspect", "investigate",
    "check for", "look under", "look behind", "look closely at",
    "peer at", "peer into", "anything hidden", "hidden door",
    "hidden trap", "secret", "tracks", "eavesdrop", "listen in",
    "listen closely", "study the", "scrutinize",
]
INVESTIGATION_SIGNALS = ["examine", "inspect", "investigate", "study", "read"]
STEALTH_KEYWORDS = [
    "sneak", "hide", "hiding", "quietly", "silently", "stealthily",
    "creep", "tiptoe", "undetected", "unseen",
]
LOCKPICK_KEYWORDS = [
    "pick the lock", "pick lock", "pick its lock", "lockpick", "pick it", "unlock",
    "jimmy the lock", "force the lock", "open the lock",
]
ATHLETICS_KEYWORDS = [
    "climb", "jump", "leap", "swim", "break down", "force open",
    "push", "pull", "lift", "carry", "grapple",
]
ACROBATICS_KEYWORDS = [
    "balance", "tumble", "flip", "dodge", "roll under", "roll over",
    "squeeze through", "tight space",
]
GREETING_KEYWORDS = ["hello", "hi", "greet", "wave", "nod", "smile", "bow", "thank", "thanks"]
ACCEPT_HELP_PATTERNS = [
    "i accept", "accept the quest", "accept bram", "accept his offer",
    "yes, i will help", "yes i will help", "i will help", "i'll help",
    "ill help", "count me in", "you have my sword", "i agree to help",
    "let's do it", "lets do it", "i'm in", "im in", "of course",
]
CONVINCE_KEYWORDS = [
    "convince", "persuade", "sway", "make him agree", "make her agree",
    "change his mind", "change her mind", "talk him into", "talk her into",
]
QUESTION_PATTERNS = [
    "ask", "asks", "asked", "tell me", "what do you know",
    "what happened", "where is", "where was", "where did", "where are",
    "who is", "who was", "how do i get", "how far", "do you know",
]


def check_code_overrides(action: str, context: str = "") -> Optional[ArbiterDecision]:
    """
    Hard-coded overrides that AI cannot bypass.
    These catch the most common/obvious cases with 100% reliability.

    Order matters: every rule that *requires* a roll runs before the
    "basic social, no roll" shortcuts, so "I bow and pick the lock" still
    rolls Sleight of Hand.
    """
    # Monetary negotiation
    if has_any(action, MONEY_KEYWORDS) and has_any(action, NEGOTIATION_KEYWORDS):
        is_intimidation = has_any(action, INTIMIDATION_SIGNALS)
        return _roll(
            ActionType.SOCIAL,
            "Intimidation" if is_intimidation else "Persuasion",
            12,
            "Monetary negotiation always requires a social check",
        )

    if has_any(action, DECEPTION_KEYWORDS):
        return _roll(ActionType.SOCIAL, "Deception", 13,
                     "Deception attempt always requires a Deception check")

    if has_any(action, THREAT_KEYWORDS):
        return _roll(ActionType.SOCIAL, "Intimidation", 13,
                     "Threat/intimidation always requires an Intimidation check")

    # Lock picking before search, so "pick the lock on the secret door" is
    # Sleight of Hand rather than Perception.
    if has_any(action, LOCKPICK_KEYWORDS):
        return _roll(ActionType.PHYSICAL, "Sleight_of_Hand", 14,
                     "Lock picking always requires a Sleight of Hand check")

    if has_any(action, STEALTH_KEYWORDS):
        return _roll(ActionType.STEALTH, "Stealth", 12,
                     "Stealth attempt always requires a Stealth check")

    # Specific search / examination (vague "look around" is handled by
    # dm_scene as a free survey, no roll).
    if has_any(action, SPECIFIC_SEARCH_KEYWORDS):
        skill = "Investigation" if has_any(action, INVESTIGATION_SIGNALS) else "Perception"
        return _roll(ActionType.EXPLORATION, skill, 12,
                     "Specific search/examination requires a skill check")

    if has_any(action, ATHLETICS_KEYWORDS):
        return _roll(ActionType.PHYSICAL, "Athletics", 12,
                     "Physical feat always requires an Athletics check")

    if has_any(action, ACROBATICS_KEYWORDS):
        return _roll(ActionType.PHYSICAL, "Acrobatics", 12,
                     "Acrobatic feat always requires an Acrobatics check")

    # Basic social: no roll
    if has_any(action, GREETING_KEYWORDS):
        return _no_roll("Simple greeting or thanks — no roll needed")

    if action.lower().strip().rstrip(".") in ("i speak up", "speak up"):
        return _no_roll("Vague speak action — no roll until player states intent")

    if has_any(action, ACCEPT_HELP_PATTERNS):
        return _no_roll("Accepting a quest or agreeing to help — no roll needed")

    if has_any(action, QUESTION_PATTERNS) and not has_any(action, CONVINCE_KEYWORDS):
        return _no_roll("Asking an NPC for information — no roll unless persuasion is required")

    # No code override - let AI arbiter decide
    return None


# =============================================================================
# ARBITER AI PROMPT
# =============================================================================

ARBITER_SYSTEM_PROMPT = """You are a tabletop RPG rules arbiter (d20 system). Your ONLY job is to determine if a player action requires a skill check, and if so, which skill and DC.

OUTPUT: You MUST respond with ONLY a valid JSON object. No other text.

REQUIRED JSON STRUCTURE:
{
  "action_type": "social|exploration|combat|stealth|physical|knowledge|movement|other",
  "requires_roll": true or false,
  "skill": "SkillName or null",
  "dc": number (8-20) or null,
  "reasoning": "Brief explanation (under 50 words)"
}

VALID SKILL NAMES (use exactly these):
Persuasion, Intimidation, Deception, Insight, Perception, Investigation, Stealth, 
Athletics, Acrobatics, Arcana, History, Nature, Religion, Survival, Medicine,
Animal_Handling, Sleight_of_Hand, Performance

WHEN TO REQUIRE ROLLS:

🗣️ SOCIAL — roll ONLY when outcome is uncertain:
- Convincing an unwilling NPC, negotiating price, requesting a difficult favor → Persuasion
- Threatening, demanding, asserting dominance → Intimidation
- Lying, bluffing, hiding intentions → Deception
- Reading motives, detecting lies → Insight

NO ROLL for social:
- Greetings, small talk, asking willing NPCs for information they would freely share
- Accepting/declining quests or offers without haggling
- "I speak up" or vague talk before a specific request

DC ADJUSTMENT FOR SOCIAL: If NPC is desperate/scared/friendly, use DC 8-10. Otherwise DC 12-15.

🔍 EXPLORATION:
- Vague "look around" / get bearings at a NEW scene → NO ROLL (free description)
- Repeat vague looking at same scene → NO ROLL (redirect to interact)
- Specific search (look FOR, examine X, hidden, tracks, eavesdrop) → Perception or Investigation DC 12-15

🥷 STEALTH (ALWAYS roll):
- Sneaking, hiding, moving silently → Stealth

💪 PHYSICAL (ALWAYS roll):
- Climbing, jumping, swimming, breaking → Athletics
- Balancing, tumbling, dodging → Acrobatics
- Picking locks, sleight of hand → Sleight_of_Hand

🧠 KNOWLEDGE (roll when relevant):
- Magical knowledge → Arcana
- Historical knowledge → History
- Nature/creature knowledge → Nature
- Religious knowledge → Religion

NO ROLL NEEDED:
- Simple movement (walk, go to)
- Basic conversation (greet, say hello)
- Using owned items normally
- Accepting/declining offers without negotiation

IMPORTANT: When a player negotiates price, demands more money, or haggles - ALWAYS require Persuasion or Intimidation, even if the NPC is desperate to give them the quest."""


ARBITER_CONTEXT_CHARS = 4000  # generous during development; trim when tuning cost


def parse_arbiter_json(text: str) -> Dict[str, Any]:
    """
    Parse the arbiter's reply, tolerating what models actually send: code
    fences, prose around the object, and replies cut off mid-object. A
    truncated reply is salvaged field by field when the essential fields
    (action_type, requires_roll, and skill/dc for a roll) made it through.
    Raises json.JSONDecodeError when nothing usable is there.
    """
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", (text or "").strip(), flags=re.IGNORECASE)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(cleaned[start:end + 1])
        except json.JSONDecodeError:
            pass

    def field(name: str, pattern: str):
        m = re.search(rf'"{name}"\s*:\s*{pattern}', cleaned, re.IGNORECASE)
        return m.group(1) if m else None

    action_type = field("action_type", r'"([a-z_]+)"')
    requires = field("requires_roll", r"(true|false)")
    if action_type is None or requires is None:
        raise json.JSONDecodeError("No usable arbiter JSON", cleaned, 0)
    decision: Dict[str, Any] = {
        "action_type": action_type,
        "requires_roll": requires.lower() == "true",
        "skill": field("skill", r'"([A-Za-z_ ]+)"'),
        "dc": int(field("dc", r"(\d+)") or 0) or None,
        "reasoning": field("reasoning", r'"([^"]*)') or "",
    }
    return decision


def get_arbiter_ai_decision(
    action: str, 
    context: str,
    max_retries: int = 3
) -> Optional[Dict[str, Any]]:
    """
    Call the AI arbiter to classify the player action.
    Returns parsed JSON or None if all retries fail.
    """
    from llm_client import generate_text, is_llm_configured

    if not is_llm_configured():
        return None

    prompt = f"""{ARBITER_SYSTEM_PROMPT}

GAME CONTEXT:
{context[:ARBITER_CONTEXT_CHARS]}

PLAYER ACTION: {action}

Respond with JSON only:"""

    for attempt in range(max_retries):
        try:
            # json_mode is very slow on some local models; prompt already demands JSON.
            from llm_client import CLASSIFIER_MAX_TOKENS, get_llm_provider
            response_text = generate_text(
                prompt,
                temperature=0.1,
                max_tokens=CLASSIFIER_MAX_TOKENS,
                json_mode=get_llm_provider() != "vllm",
                max_retries=1,
            )

            if not response_text:
                print(f"⚠️ Arbiter empty response (attempt {attempt + 1})")
                continue

            decision = parse_arbiter_json(response_text)
            
            # Validate structure
            if "action_type" not in decision:
                raise ValueError("Missing action_type")
            if "requires_roll" not in decision:
                raise ValueError("Missing requires_roll")
            
            # Validate roll fields if roll required
            if decision.get("requires_roll"):
                if not decision.get("skill"):
                    raise ValueError("Roll required but no skill specified")
                if not decision.get("dc"):
                    raise ValueError("Roll required but no DC specified")
                
                # Validate DC range
                dc = decision["dc"]
                if not isinstance(dc, int) or dc < 5 or dc > 25:
                    raise ValueError(f"Invalid DC: {dc}")
                
                # Validate skill name
                valid_skills = [s.value for s in SkillName]
                if decision["skill"] not in valid_skills:
                    # Try to fix common mistakes
                    skill_lower = decision["skill"].lower().replace(" ", "_")
                    skill_map = {
                        "lockpicking": "Sleight_of_Hand",
                        "thievery": "Sleight_of_Hand",
                        "climbing": "Athletics",
                        "swimming": "Athletics",
                        "lying": "Deception",
                        "threatening": "Intimidation",
                        "searching": "Perception",
                        "tracking": "Survival",
                    }
                    if skill_lower in skill_map:
                        decision["skill"] = skill_map[skill_lower]
                    else:
                        raise ValueError(f"Invalid skill: {decision['skill']}")
            
            return decision
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Arbiter JSON parse error (attempt {attempt + 1}): {e}")
            continue
        except ValueError as e:
            print(f"⚠️ Arbiter validation error (attempt {attempt + 1}): {e}")
            continue
        except Exception as e:
            print(f"⚠️ Arbiter error (attempt {attempt + 1}): {e}")
            continue
    
    return None


# =============================================================================
# FALLBACK DECISION
# =============================================================================

def get_fallback_decision(action: str) -> ArbiterDecision:
    """
    Conservative fallback when AI fails.
    For ambiguous cases, we're now LESS aggressive to avoid false positives.
    The AI arbiter should handle nuanced cases.
    """
    
    # Simple greetings and basic social - NO ROLL (these don't require persuasion)
    if has_any(action, GREETING_KEYWORDS):
        return ArbiterDecision(
            action_type=ActionType.SOCIAL.value,
            requires_roll=False,
            reasoning="Fallback: Simple greeting - no roll needed",
            source="fallback"
        )
    
    # Clear attempts to change an NPC's mind still get their check
    if has_any(action, CONVINCE_KEYWORDS):
        return ArbiterDecision(
            action_type=ActionType.SOCIAL.value,
            requires_roll=True,
            skill="Persuasion",
            dc=12,
            reasoning="Fallback: trying to persuade someone",
            source="fallback"
        )

    # Default: no roll needed (be less aggressive)
    return ArbiterDecision(
        action_type=ActionType.OTHER.value,
        requires_roll=False,
        reasoning="Fallback: No obvious skill check trigger",
        source="fallback"
    )


# =============================================================================
# MAIN ARBITER FUNCTION
# =============================================================================

def get_arbiter_decision(
    action: str,
    context: str = "",
    use_ai: bool = True,
    scene_context: str = "",
) -> ArbiterDecision:
    """
    Main entry point: Determine if a player action requires a skill check.
    
    Multi-layer approach:
    1. Code overrides (100% reliable) - catches obvious cases
    2. AI arbiter (structured JSON) - handles nuanced cases
    3. Fallback (conservative) - when AI fails
    
    Args:
        action: The player's action text
        context: Game context (location, NPCs, etc.)
        use_ai: Whether to use AI for non-obvious cases
        
    Returns:
        ArbiterDecision with skill check requirements
    """
    full_context = context
    if scene_context:
        full_context = f"{context}\n{scene_context}" if context else scene_context

    # Layer 1: Code overrides
    override = check_code_overrides(action, full_context)
    if override:
        if override.requires_roll:
            print(f"🎯 Arbiter (code override): {override.skill} DC {override.dc}")
        else:
            print(f"🎯 Arbiter (code override): No roll — {override.reasoning}")
        return override

    # Layer 2: AI arbiter
    if use_ai:
        ai_decision = get_arbiter_ai_decision(action, full_context)
        if ai_decision:
            decision = ArbiterDecision(
                action_type=ai_decision.get("action_type", "other"),
                requires_roll=ai_decision.get("requires_roll", False),
                skill=ai_decision.get("skill"),
                dc=ai_decision.get("dc"),
                reasoning=ai_decision.get("reasoning", ""),
                source="arbiter_ai"
            )
            if decision.requires_roll:
                print(f"🤖 Arbiter (AI): {decision.skill} DC {decision.dc} - {decision.reasoning}")
            else:
                print(f"🤖 Arbiter (AI): No roll needed - {decision.reasoning}")
            return decision
    
    # Layer 3: Fallback
    fallback = get_fallback_decision(action)
    if fallback.requires_roll:
        print(f"⚠️ Arbiter (fallback): {fallback.skill} DC {fallback.dc}")
    else:
        print(f"⚠️ Arbiter (fallback): No roll needed")
    return fallback


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    # Test cases
    test_actions = [
        ("I demand a downpayment of 10 gold, take it or leave it", "Talking to desperate farmer"),
        ("I search the room for hidden treasure", "In a dusty tavern"),
        ("I sneak past the guards", "Guards at the gate"),
        ("I try to pick the lock on the chest", "Old wooden chest"),
        ("I climb up the wall", "Stone wall, 20 feet high"),
        ("I walk to the tavern", "In the village square"),
        ("I say hello to the barkeep", "Inside the tavern"),
        ("I convince the merchant to lower his price", "At the market"),
        ("I lie about my identity to the guard", "City gate checkpoint"),
    ]
    
    print("=" * 60)
    print("ARBITER TEST RESULTS")
    print("=" * 60)
    
    for action, context in test_actions:
        print(f"\nAction: {action}")
        print(f"Context: {context}")
        decision = get_arbiter_decision(action, context, use_ai=False)  # Test without AI
        print(f"Decision: requires_roll={decision.requires_roll}, skill={decision.skill}, dc={decision.dc}")
        print(f"Source: {decision.source}")
        print("-" * 40)
