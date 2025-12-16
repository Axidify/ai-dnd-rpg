"""
Skill Check + AI DM Integration Test
Test how SKILL CHECKS integrate with the AI Dungeon Master.
(Combat/Attack rolls will be implemented separately)

Run with: python tests/test_dice_with_dm.py
"""

import os
import sys
import random
import re

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()


# =============================================================================
# DICE SYSTEM
# =============================================================================

def roll_dice(dice_notation: str) -> dict:
    """Parse and roll dice notation like "d20", "2d6+3", "d8-1"."""
    pattern = r'^(\d*)d(\d+)([+-]\d+)?$'
    match = re.match(pattern, dice_notation.lower().replace(' ', ''))
    
    if not match:
        return None
    
    count = int(match.group(1)) if match.group(1) else 1
    sides = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0
    
    rolls = [random.randint(1, sides) for _ in range(count)]
    total = sum(rolls) + modifier
    
    return {
        'notation': dice_notation,
        'count': count,
        'sides': sides,
        'rolls': rolls,
        'modifier': modifier,
        'total': total
    }


# Skill to ability mapping
SKILL_ABILITIES = {
    'athletics': 'strength',
    'acrobatics': 'dexterity',
    'stealth': 'dexterity',
    'arcana': 'intelligence',
    'history': 'intelligence',
    'investigation': 'intelligence',
    'perception': 'wisdom',
    'insight': 'wisdom',
    'survival': 'wisdom',
    'deception': 'charisma',
    'intimidation': 'charisma',
    'persuasion': 'charisma',
}


class TestCharacter:
    """Simple test character."""
    def __init__(self):
        self.name = "Thorn"
        self.char_class = "Rogue"
        self.race = "Half-Elf"
        self.strength = 10      # +0
        self.dexterity = 16     # +3
        self.constitution = 12  # +1
        self.intelligence = 14  # +2
        self.wisdom = 12        # +1
        self.charisma = 10      # +0
    
    def get_modifier(self, stat_name):
        value = getattr(self, stat_name.lower(), 10)
        return (value - 10) // 2


def roll_skill_check(character, skill_name: str, dc: int) -> dict:
    """Roll a skill check with character modifiers."""
    skill_lower = skill_name.lower().replace(' ', '_')
    
    if skill_lower in SKILL_ABILITIES:
        ability = SKILL_ABILITIES[skill_lower]
    else:
        ability = skill_lower
    
    modifier = character.get_modifier(ability)
    roll = random.randint(1, 20)
    total = roll + modifier
    
    return {
        'skill': skill_name.title(),
        'ability': ability.upper()[:3],
        'roll': roll,
        'modifier': modifier,
        'total': total,
        'dc': dc,
        'success': total >= dc,
        'is_nat_20': roll == 20,
        'is_nat_1': roll == 1,
    }


def format_roll(result: dict) -> str:
    """Format roll result for display."""
    mod_sign = '+' if result['modifier'] >= 0 else ''
    outcome = "✅ SUCCESS" if result['success'] else "❌ FAILURE"
    
    nat_str = ""
    if result['is_nat_20']:
        nat_str = " ✨ NAT 20!"
    elif result['is_nat_1']:
        nat_str = " 💀 NAT 1!"
    
    return (
        f"🎲 {result['skill']} ({result['ability']}): "
        f"[{result['roll']}]{mod_sign}{result['modifier']} = {result['total']} "
        f"vs DC {result['dc']} = {outcome}{nat_str}"
    )


# =============================================================================
# AI DM INTEGRATION - SKILL CHECKS ONLY
# =============================================================================

# System prompt for testing SKILL CHECKS (no combat/attacks)
DM_SYSTEM_PROMPT = """You are an experienced Dungeon Master running a D&D adventure.

## SKILL CHECK SYSTEM (THIS TEST ONLY COVERS SKILL CHECKS)

When the situation requires a SKILL CHECK:
1. Describe the situation naturally
2. End your message with EXACTLY this format: [ROLL: SkillName DC X]

VALID SKILL CHECK FORMATS:
- [ROLL: Stealth DC 12]
- [ROLL: Perception DC 15]
- [ROLL: Investigation DC 10]
- [ROLL: Persuasion DC 14]
- [ROLL: Athletics DC 13]
- [ROLL: Acrobatics DC 12]
- [ROLL: Insight DC 11]
- [ROLL: Survival DC 10]
- [ROLL: Arcana DC 15]
- [ROLL: Intimidation DC 13]
- [ROLL: Deception DC 14]
- [ROLL: History DC 12]

IMPORTANT RULES:
- ONLY use the [ROLL: Skill DC X] format - nothing else
- Do NOT ask for attack rolls - combat is not implemented yet
- Do NOT explain how to roll dice - the system handles it
- Do NOT add extra text inside the brackets
- Wait for the result before narrating what happens

When you receive a [ROLL RESULT: ...]:
- SUCCESS: Describe the positive outcome - player achieved their goal
- FAILURE: Describe the negative consequence - don't soften it
- NATURAL 20: Make it EPIC! Something amazing happens
- NATURAL 1: Make it DISASTROUS! Comedic or dramatic failure

DO NOT fudge results. Failure makes success meaningful.

## PLAYER CHARACTER
Name: Thorn (Half-Elf Rogue)
Modifiers: STR +0, DEX +3, CON +1, INT +2, WIS +1, CHA +0
Background: Skilled infiltrator and lockpick

## CURRENT SCENE
A dungeon corridor with torchlight, shadows, and exploration challenges.
Focus on: stealth, investigation, perception, and social/environmental challenges.
NO COMBAT in this test - if danger arises, use skill checks to avoid/escape.
"""


def create_dm():
    """Initialize the AI DM."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not set in .env")
        sys.exit(1)
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=DM_SYSTEM_PROMPT
    )
    return model


def get_dm_response(chat, message, stream=True):
    """Get streaming response from DM."""
    try:
        response = chat.send_message(message, stream=stream)
        full_text = ""
        for chunk in response:
            if chunk.text:
                print(chunk.text, end="", flush=True)
                full_text += chunk.text
        print()
        return full_text
    except Exception as e:
        return f"[Error: {e}]"


def parse_roll_request(dm_response: str) -> tuple:
    """Parse [ROLL: skill DC X] from DM response."""
    pattern = r'\[ROLL:\s*(\w+)\s+DC\s*(\d+)\]'
    match = re.search(pattern, dm_response, re.IGNORECASE)
    
    if match:
        skill = match.group(1)
        dc = int(match.group(2))
        return skill, dc
    return None, None


# =============================================================================
# MAIN TEST
# =============================================================================

def main():
    print("=" * 60)
    print("      🎲 AI DM + SKILL CHECK TEST 🎲")
    print("         (Combat/Attacks Not Implemented)")
    print("=" * 60)
    
    character = TestCharacter()
    print(f"\nPlaying as: {character.name} ({character.race} {character.char_class})")
    print(f"DEX: +{character.get_modifier('dexterity')}, "
          f"WIS: +{character.get_modifier('wisdom')}, "
          f"INT: +{character.get_modifier('intelligence')}")
    
    print("\n" + "-" * 60)
    print("This test covers SKILL CHECKS only (no combat).")
    print("DM will request rolls like: [ROLL: Stealth DC 12]")
    print("-" * 60)
    
    model = create_dm()
    chat = model.start_chat(history=[])
    
    # Initial scene setup
    print("\n🎲 Dungeon Master:")
    dm_response = get_dm_response(
        chat, 
        "Set an exploration scene where Thorn enters a mysterious area. Create tension through environmental or social challenges that require skill checks. Request a skill check using [ROLL: SkillName DC X] format. Remember: no combat in this test."
    )
    
    print("\n" + "-" * 60)
    
    while True:
        # Check if DM requested a roll
        skill, dc = parse_roll_request(dm_response)
        
        if skill and dc:
            print(f"\n📋 DM requests: {skill.title()} check (DC {dc})")
            input("   Press Enter to roll...")
            
            # Perform the roll
            result = roll_skill_check(character, skill, dc)
            print(f"\n{format_roll(result)}")
            
            # Tell the DM the result
            result_msg = (
                f"[ROLL RESULT: {result['skill']} = {result['total']} vs DC {dc} = "
                f"{'SUCCESS' if result['success'] else 'FAILURE'}"
            )
            if result['is_nat_20']:
                result_msg += " (NATURAL 20!)"
            elif result['is_nat_1']:
                result_msg += " (NATURAL 1!)"
            result_msg += "]"
            
            print(f"\n🎲 Dungeon Master:")
            dm_response = get_dm_response(chat, result_msg)
            print()
        
        # Get player action
        print()
        action = input("⚔️  Your action (or 'quit'): ").strip()
        
        if action.lower() in ['quit', 'exit', 'q']:
            print("\nTest complete!")
            break
        
        if not action:
            continue
        
        # Send action to DM
        print("\n🎲 Dungeon Master:")
        dm_response = get_dm_response(chat, action)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted.")
