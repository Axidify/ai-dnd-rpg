"""
DM Arbiter - Structured rules classifier for D&D mechanics.

This module implements a Two-Phase AI approach:
Phase 1 (Arbiter): Decides if an action requires a skill check (structured JSON output)
Phase 2 (Narrator): Writes the narrative response (handled by dm_engine)

The arbiter is separate from the narrator to prevent "narrative temptation" - 
the tendency for AI to skip mechanics for storytelling purposes.
"""

import os
import re
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

# Try to import Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


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
    """Valid D&D 5e skills."""
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

def check_code_overrides(action: str, context: str = "") -> Optional[ArbiterDecision]:
    """
    Hard-coded overrides that AI cannot bypass.
    These catch the most common/obvious cases with 100% reliability.
    """
    action_lower = action.lower()
    context_lower = context.lower() if context else ""
    
    # =========================================================================
    # MONETARY NEGOTIATIONS - ALWAYS REQUIRE ROLL
    # =========================================================================
    money_keywords = ["gold", "coin", "pay", "price", "cost", "silver", "copper", "gp", "sp", "cp"]
    negotiation_keywords = [
        "more", "less", "discount", "upfront", "advance", "deposit", "downpayment",
        "down payment", "negotiate", "bargain", "deal", "offer", "counter", "haggle",
        "take it or leave", "final offer", "best price", "lower", "higher", "half",
        "double", "triple", "extra", "bonus", "fee", "payment", "installment"
    ]
    
    has_money = any(w in action_lower for w in money_keywords)
    has_negotiation = any(w in action_lower for w in negotiation_keywords)
    
    if has_money and has_negotiation:
        # Determine if it's more intimidation or persuasion
        intimidation_signals = ["take it or leave", "demand", "or else", "threaten", "final", "now"]
        is_intimidation = any(w in action_lower for w in intimidation_signals)
        
        return ArbiterDecision(
            action_type=ActionType.SOCIAL.value,
            requires_roll=True,
            skill="Intimidation" if is_intimidation else "Persuasion",
            dc=12,
            reasoning="Monetary negotiation always requires a social check",
            source="code_override"
        )
    
    # =========================================================================
    # LYING / DECEPTION - ALWAYS REQUIRE ROLL
    # =========================================================================
    deception_keywords = [
        "lie", "lying", "bluff", "bluffing", "deceive", "trick", "fool", 
        "pretend", "fake", "disguise", "false", "fabricate", "mislead"
    ]
    
    if any(w in action_lower for w in deception_keywords):
        return ArbiterDecision(
            action_type=ActionType.SOCIAL.value,
            requires_roll=True,
            skill="Deception",
            dc=13,
            reasoning="Deception attempt always requires a Deception check",
            source="code_override"
        )
    
    # =========================================================================
    # EXPLICIT THREATS - ALWAYS REQUIRE ROLL
    # =========================================================================
    threat_keywords = [
        "threaten", "threatening", "intimidate", "intimidating", "scare", 
        "menace", "demand", "or else", "i'll kill", "i will kill"
    ]
    
    if any(w in action_lower for w in threat_keywords):
        return ArbiterDecision(
            action_type=ActionType.SOCIAL.value,
            requires_roll=True,
            skill="Intimidation",
            dc=13,
            reasoning="Threat/intimidation always requires an Intimidation check",
            source="code_override"
        )
    
    # =========================================================================
    # SPECIFIC SEARCH / EXAMINATION - REQUIRE ROLL
    # (Vague "look around" is handled by dm_scene — free survey, no roll)
    # =========================================================================
    specific_search_keywords = [
        "search for", "look for", "examine", "inspect", "investigate",
        "check for", "look under", "look behind", "look closely at",
        "peer at", "peer into", "anything hidden", "hidden door",
        "hidden trap", "secret ", "tracks", "eavesdrop", "listen in",
        "listen closely", "study the", "scrutinize",
    ]
    
    if any(w in action_lower for w in specific_search_keywords):
        is_specific = any(
            w in action_lower
            for w in ["examine", "inspect", "investigate", "study", "read"]
        )
        return ArbiterDecision(
            action_type=ActionType.EXPLORATION.value,
            requires_roll=True,
            skill="Investigation" if is_specific else "Perception",
            dc=12,
            reasoning="Specific search/examination requires a skill check",
            source="code_override"
        )
    
    # =========================================================================
    # STEALTH - ALWAYS REQUIRE ROLL
    # =========================================================================
    stealth_keywords = [
        "sneak", "sneaking", "hide", "hiding", "quietly", "silently", 
        "stealthily", "creep", "creeping", "tiptoe", "undetected", "unseen"
    ]
    
    if any(w in action_lower for w in stealth_keywords):
        return ArbiterDecision(
            action_type=ActionType.STEALTH.value,
            requires_roll=True,
            skill="Stealth",
            dc=12,
            reasoning="Stealth attempt always requires a Stealth check",
            source="code_override"
        )
    
    # =========================================================================
    # LOCK PICKING - ALWAYS REQUIRE ROLL
    # =========================================================================
    lockpick_keywords = [
        "pick the lock", "pick lock", "lockpick", "pick it", "unlock", 
        "jimmy the lock", "force the lock", "open the lock"
    ]
    
    if any(w in action_lower for w in lockpick_keywords):
        return ArbiterDecision(
            action_type=ActionType.PHYSICAL.value,
            requires_roll=True,
            skill="Sleight_of_Hand",
            dc=14,
            reasoning="Lock picking always requires a Sleight of Hand check",
            source="code_override"
        )
    
    # =========================================================================
    # PHYSICAL FEATS - ALWAYS REQUIRE ROLL
    # =========================================================================
    athletics_keywords = [
        "climb", "climbing", "jump", "jumping", "leap", "swim", "swimming",
        "break down", "force open", "push", "pull", "lift", "carry", "grapple"
    ]
    
    if any(w in action_lower for w in athletics_keywords):
        return ArbiterDecision(
            action_type=ActionType.PHYSICAL.value,
            requires_roll=True,
            skill="Athletics",
            dc=12,
            reasoning="Physical feat always requires an Athletics check",
            source="code_override"
        )
    
    # =========================================================================
    # ACROBATICS - ALWAYS REQUIRE ROLL
    # =========================================================================
    acrobatics_keywords = [
        "balance", "balancing", "tumble", "tumbling", "flip", "dodge", 
        "roll under", "roll over", "squeeze through", "tight space"
    ]
    
    if any(w in action_lower for w in acrobatics_keywords):
        return ArbiterDecision(
            action_type=ActionType.PHYSICAL.value,
            requires_roll=True,
            skill="Acrobatics",
            dc=12,
            reasoning="Acrobatic feat always requires an Acrobatics check",
            source="code_override"
        )
    
    # No code override - let AI arbiter decide
    return None


# =============================================================================
# ARBITER AI PROMPT
# =============================================================================

ARBITER_SYSTEM_PROMPT = """You are a D&D 5e rules arbiter. Your ONLY job is to determine if a player action requires a skill check, and if so, which skill and DC.

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

🗣️ SOCIAL (ALWAYS roll, even if NPC is desperate/friendly):
- Convincing, negotiating, requesting favors → Persuasion
- Threatening, demanding, asserting dominance → Intimidation  
- Lying, bluffing, hiding intentions → Deception
- Reading motives, detecting lies → Insight

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
{context[:500]}  

PLAYER ACTION: {action}

Respond with JSON only:"""

    for attempt in range(max_retries):
        try:
            # json_mode is very slow on some local models; prompt already demands JSON.
            from llm_client import get_llm_provider
            response_text = generate_text(
                prompt,
                temperature=0.1,
                max_tokens=200,
                json_mode=get_llm_provider() != "vllm",
                max_retries=1,
            )

            if not response_text:
                print(f"⚠️ Arbiter empty response (attempt {attempt + 1})")
                continue

            # Parse JSON
            decision = json.loads(response_text)
            
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
    action_lower = action.lower()
    
    # Simple greetings and basic social - NO ROLL (these don't require persuasion)
    simple_social = ["hello", "hi", "greet", "wave", "nod", "smile", "bow", "thank"]
    if any(w in action_lower for w in simple_social):
        return ArbiterDecision(
            action_type=ActionType.SOCIAL.value,
            requires_roll=False,
            reasoning="Fallback: Simple greeting - no roll needed",
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
# COMBAT DETECTION (BONUS)
# =============================================================================

def detect_combat_intent(action: str, context: str = "") -> Optional[Tuple[List[str], bool]]:
    """
    Detect if an action should trigger combat.
    Returns (enemy_list, surprise) or None.
    
    Note: This is a simple keyword-based detection. The narrator AI
    still handles complex combat scenarios.
    """
    action_lower = action.lower()
    
    attack_keywords = [
        "attack", "strike", "hit", "stab", "slash", "swing at", 
        "shoot", "cast at", "fight", "kill"
    ]
    
    if any(w in action_lower for w in attack_keywords):
        # Extract target from context
        # This is simplified - the narrator AI handles the actual combat trigger
        return None  # Let narrator handle combat
    
    return None


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
