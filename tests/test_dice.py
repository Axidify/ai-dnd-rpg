"""
Dice Rolling System - Test Script
Test the dice mechanics before integrating into the main game.

Run with: python tests/test_dice.py
"""

import random
import re


def roll_dice(dice_notation: str) -> dict:
    """
    Parse and roll dice notation like "d20", "2d6+3", "d8-1"
    
    Returns dict with:
        - notation: original input
        - dice: list of individual roll results
        - modifier: the +/- number
        - total: final result
    """
    # Pattern: optional count, 'd', sides, optional modifier
    pattern = r'^(\d*)d(\d+)([+-]\d+)?$'
    match = re.match(pattern, dice_notation.lower().replace(' ', ''))
    
    if not match:
        return None
    
    count = int(match.group(1)) if match.group(1) else 1
    sides = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0
    
    # Roll the dice
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


def format_roll_result(result: dict) -> str:
    """Format a roll result for display."""
    if not result:
        return "Invalid dice notation"
    
    # Format: 2d6+3 = [4, 2] + 3 = 9
    rolls_str = f"[{', '.join(map(str, result['rolls']))}]"
    
    if result['modifier'] > 0:
        mod_str = f" + {result['modifier']}"
    elif result['modifier'] < 0:
        mod_str = f" - {abs(result['modifier'])}"
    else:
        mod_str = ""
    
    return f"{result['notation']} = {rolls_str}{mod_str} = {result['total']}"


# Skill to ability mapping (D&D 5e)
SKILL_ABILITIES = {
    'athletics': 'strength',
    'acrobatics': 'dexterity',
    'sleight_of_hand': 'dexterity',
    'stealth': 'dexterity',
    'arcana': 'intelligence',
    'history': 'intelligence',
    'investigation': 'intelligence',
    'nature': 'intelligence',
    'religion': 'intelligence',
    'animal_handling': 'wisdom',
    'insight': 'wisdom',
    'medicine': 'wisdom',
    'perception': 'wisdom',
    'survival': 'wisdom',
    'deception': 'charisma',
    'intimidation': 'charisma',
    'performance': 'charisma',
    'persuasion': 'charisma',
}


class MockCharacter:
    """Mock character for testing."""
    def __init__(self):
        self.strength = 14      # +2
        self.dexterity = 16     # +3
        self.constitution = 12  # +1
        self.intelligence = 10  # +0
        self.wisdom = 13        # +1
        self.charisma = 8       # -1
    
    def get_modifier(self, stat_value):
        return (stat_value - 10) // 2
    
    def get_stat(self, stat_name):
        return getattr(self, stat_name.lower(), 10)


def roll_skill_check(character, skill_name: str, dc: int = None) -> dict:
    """
    Roll a skill check with character modifiers.
    
    Returns dict with roll info and pass/fail if DC provided.
    """
    skill_lower = skill_name.lower().replace(' ', '_')
    
    # Get the ability for this skill
    if skill_lower in SKILL_ABILITIES:
        ability = SKILL_ABILITIES[skill_lower]
        stat_value = character.get_stat(ability)
        modifier = character.get_modifier(stat_value)
    else:
        # Try direct stat check
        stat_value = character.get_stat(skill_lower)
        modifier = character.get_modifier(stat_value) if stat_value else 0
        ability = skill_lower
    
    # Roll d20
    roll = random.randint(1, 20)
    total = roll + modifier
    
    result = {
        'skill': skill_name,
        'ability': ability,
        'roll': roll,
        'modifier': modifier,
        'total': total,
        'is_nat_20': roll == 20,
        'is_nat_1': roll == 1,
    }
    
    if dc is not None:
        result['dc'] = dc
        result['success'] = total >= dc
    
    return result


def format_skill_check(result: dict) -> str:
    """Format a skill check result for display."""
    mod_sign = '+' if result['modifier'] >= 0 else ''
    base = f"{result['skill'].title()} ({result['ability'][:3].upper()}): d20{mod_sign}{result['modifier']}"
    
    roll_str = f"[{result['roll']}]{mod_sign}{result['modifier']} = {result['total']}"
    
    if result['is_nat_20']:
        roll_str += " ✨ Natural 20!"
    elif result['is_nat_1']:
        roll_str += " 💀 Natural 1!"
    
    if 'dc' in result:
        outcome = "✅ SUCCESS" if result['success'] else "❌ FAILURE"
        roll_str += f" vs DC {result['dc']} = {outcome}"
    
    return f"🎲 {base}\n   {roll_str}"


# =============================================================================
# INTERACTIVE TEST
# =============================================================================

def main():
    print("=" * 60)
    print("        🎲 DICE ROLLING SYSTEM - TEST MODE 🎲")
    print("=" * 60)
    
    character = MockCharacter()
    print("\nTest Character Stats:")
    print(f"  STR: {character.strength} ({character.get_modifier(character.strength):+d})")
    print(f"  DEX: {character.dexterity} ({character.get_modifier(character.dexterity):+d})")
    print(f"  CON: {character.constitution} ({character.get_modifier(character.constitution):+d})")
    print(f"  INT: {character.intelligence} ({character.get_modifier(character.intelligence):+d})")
    print(f"  WIS: {character.wisdom} ({character.get_modifier(character.wisdom):+d})")
    print(f"  CHA: {character.charisma} ({character.get_modifier(character.charisma):+d})")
    
    print("\n" + "-" * 60)
    print("COMMANDS:")
    print("  roll d20         - Roll a d20")
    print("  roll 2d6+3       - Roll 2d6 with +3 modifier")
    print("  roll stealth     - Roll Stealth (d20 + DEX modifier)")
    print("  roll perception  - Roll Perception (d20 + WIS modifier)")
    print("  check stealth 15 - Roll Stealth vs DC 15")
    print("  quit             - Exit test mode")
    print("-" * 60)
    
    while True:
        print()
        user_input = input("🎲 Test: ").strip().lower()
        
        if user_input in ['quit', 'exit', 'q']:
            print("Exiting dice test.")
            break
        
        if not user_input:
            continue
        
        # Parse command
        parts = user_input.split()
        
        if parts[0] == 'roll':
            if len(parts) < 2:
                print("Usage: roll <dice> or roll <skill>")
                continue
            
            dice_or_skill = parts[1]
            
            # Check if it's dice notation
            if 'd' in dice_or_skill:
                result = roll_dice(dice_or_skill)
                if result:
                    print(f"  🎲 {format_roll_result(result)}")
                else:
                    print("  Invalid dice notation. Try: d20, 2d6+3, 1d8-1")
            else:
                # It's a skill
                result = roll_skill_check(character, dice_or_skill)
                print(format_skill_check(result))
        
        elif parts[0] == 'check':
            if len(parts) < 3:
                print("Usage: check <skill> <DC>")
                continue
            
            skill = parts[1]
            try:
                dc = int(parts[2])
            except ValueError:
                print("DC must be a number")
                continue
            
            result = roll_skill_check(character, skill, dc)
            print(format_skill_check(result))
        
        else:
            # Try to interpret as dice notation
            result = roll_dice(user_input)
            if result:
                print(f"  🎲 {format_roll_result(result)}")
            else:
                print("Unknown command. Try: roll d20, roll stealth, check perception 15")


if __name__ == "__main__":
    main()
