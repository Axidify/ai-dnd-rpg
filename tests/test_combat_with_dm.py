"""
Combat + AI DM Integration Test
Test how combat integrates with the AI Dungeon Master.

Run with: python tests/test_combat_with_dm.py
"""

import os
import sys
import random
import re

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
import google.generativeai as genai
from combat import (
    create_enemy, Enemy, ENEMIES, WEAPONS,
    roll_attack, roll_damage, enemy_attack,
    format_attack_result, format_damage_result, format_enemy_attack,
    roll_initiative, format_initiative_roll, determine_turn_order,
    display_turn_order, Combatant
)

# Load environment variables
load_dotenv()


# =============================================================================
# TEST CHARACTER
# =============================================================================

class TestCharacter:
    """Simple test character for combat."""
    def __init__(self):
        self.name = "Kira"
        self.char_class = "Fighter"
        self.race = "Human"
        self.strength = 16      # +3
        self.dexterity = 14     # +2
        self.constitution = 14  # +2
        self.intelligence = 10  # +0
        self.wisdom = 12        # +1
        self.charisma = 8       # -1
        self.max_hp = 12
        self.current_hp = 12
        self.armor_class = 14  # Chain shirt
        self.weapon = "longsword"
    
    def get_ability_modifier(self, ability_name):
        ability_map = {
            'strength': self.strength,
            'str': self.strength,
            'dexterity': self.dexterity,
            'dex': self.dexterity,
            'constitution': self.constitution,
            'con': self.constitution,
            'intelligence': self.intelligence,
            'int': self.intelligence,
            'wisdom': self.wisdom,
            'wis': self.wisdom,
            'charisma': self.charisma,
            'cha': self.charisma,
        }
        score = ability_map.get(ability_name.lower(), 10)
        return (score - 10) // 2
    
    def take_damage(self, amount):
        self.current_hp = max(0, self.current_hp - amount)
        return self.current_hp > 0


# =============================================================================
# AI DM INTEGRATION - COMBAT
# =============================================================================

DM_COMBAT_PROMPT = """You are an experienced Dungeon Master narrating D&D combat.

## YOUR ONLY JOB
Narrate combat cinematically based on results YOU RECEIVE. You are a NARRATOR only.

## ABSOLUTE RULES - BREAKING THESE RUINS THE GAME:

🚫 NEVER EVER write these yourself:
   - [ATTACK RESULT: ...]
   - [ENEMY ATTACK: ...]  
   - [ROLL: ...]
   - Any bracketed commands
   
These are SYSTEM MESSAGES that only the GAME ENGINE sends to you.

🚫 NEVER:
   - Make up damage numbers
   - Decide if attacks hit or miss
   - Say "the goblin hits you for X damage"
   - Narrate attacks BEFORE receiving results
   
✅ ALWAYS:
   - WAIT for bracketed results before narrating outcomes
   - ONLY describe what the bracketed result tells you happened
   - Keep combat narration to 2-3 SHORT sentences
   - Ask "What do you do?" at the end

## WHAT YOU WILL RECEIVE (react to these):

You'll get messages like:
- "[ATTACK RESULT: HIT for 7 damage. Goblin: wounded (2/7 HP)]" 
  → Narrate the player's sword slicing the goblin
  
- "[ATTACK RESULT: MISS. Goblin: healthy (7/7 HP)]"
  → Narrate the goblin dodging
  
- "[ENEMY ATTACK: HIT for 5 damage. Player HP: 7/12]"
  → Narrate the goblin hurting the player
  
- "[ENEMY ATTACK: MISS. Player HP: 12/12]"
  → Narrate the player dodging

## EXAMPLE GOOD RESPONSE:

Input: "[ATTACK RESULT: HIT for 8 damage. Goblin: badly wounded (2/7 HP)]"
Output: "Your longsword arcs through the air and bites deep into the goblin's shoulder! It staggers back, blood streaming from the wound. What do you do?"

## CURRENT COMBAT
Player: Kira (Human Fighter), Weapon: Longsword
Enemy: Goblin
"""


def create_dm():
    """Initialize the AI DM for combat."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not set in .env")
        sys.exit(1)
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=DM_COMBAT_PROMPT
    )
    return model


def filter_dm_output(text: str) -> str:
    """Remove any bracketed commands the DM might accidentally generate."""
    # Remove any [ATTACK RESULT: ...], [ENEMY ATTACK: ...], [ROLL: ...] etc.
    patterns = [
        r'\[ATTACK RESULT:[^\]]*\]',
        r'\[ENEMY ATTACK:[^\]]*\]',
        r'\[ROLL:[^\]]*\]',
        r'\[ATTACK:[^\]]*\]',
    ]
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    # Clean up any extra whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'  +', ' ', text)  # Multiple spaces to single
    return text.strip()


def has_forbidden_brackets(text: str) -> bool:
    """Check if text contains bracketed commands that should be filtered."""
    patterns = [
        r'\[ATTACK RESULT:',
        r'\[ENEMY ATTACK:',
        r'\[ROLL:',
        r'\[ATTACK:',
    ]
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def get_dm_response(chat, message, stream=True):
    """Get streaming response from DM, filtering out invalid commands."""
    try:
        response = chat.send_message(message, stream=stream)
        full_text = ""
        
        # Collect chunks and print as they stream
        for chunk in response:
            if chunk.text:
                full_text += chunk.text
                print(chunk.text, end="", flush=True)
        
        print()  # Final newline
        
        # Check if DM generated forbidden brackets
        if has_forbidden_brackets(full_text):
            # Clear the bad output and reprint clean version
            filtered = filter_dm_output(full_text)
            print("\r" + " " * 80)  # Clear line
            print(f"(Corrected: {filtered})")
            return filtered
        
        return full_text.strip()
    except Exception as e:
        return f"[Error: {e}]"


def parse_attack_request(dm_response: str) -> str:
    """Parse [ATTACK: target] from DM response."""
    pattern = r'\[ATTACK:\s*([^\]]+)\]'
    match = re.search(pattern, dm_response, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def show_combat_status(character, enemy, round_num=1):
    """Display detailed combat status panel."""
    # Player HP bar
    hp_percent = character.current_hp / character.max_hp
    hp_filled = int(hp_percent * 10)
    hp_bar = "█" * hp_filled + "░" * (10 - hp_filled)
    
    if hp_percent > 0.75:
        hp_color = "🟢"
    elif hp_percent > 0.5:
        hp_color = "🟡"
    elif hp_percent > 0.25:
        hp_color = "🟠"
    else:
        hp_color = "🔴"
    
    # Enemy HP bar
    enemy_hp_percent = enemy.current_hp / enemy.max_hp
    enemy_hp_filled = int(enemy_hp_percent * 10)
    enemy_hp_bar = "█" * enemy_hp_filled + "░" * (10 - enemy_hp_filled)
    
    # Get weapon info
    weapon_name = character.weapon.title()
    weapon_data = WEAPONS.get(character.weapon, {})
    weapon_damage = weapon_data.get('damage', '1d6')
    
    # Enemy damage (from enemy's damage_dice attribute)
    enemy_damage = enemy.damage_dice
    if enemy.damage_bonus:
        enemy_damage += f"+{enemy.damage_bonus}"
    
    print()
    print("╔" + "═" * 60 + "╗")
    print(f"║  🗡️ COMBAT STATUS - Round {round_num}".ljust(61) + "║")
    print("╠" + "═" * 60 + "╣")
    print(f"║  YOU: {character.name} ({character.char_class})".ljust(61) + "║")
    print(f"║  {hp_color} {hp_bar} {character.current_hp}/{character.max_hp} HP  |  AC: {character.armor_class}  |  {weapon_name} ({weapon_damage})".ljust(61) + "║")
    print("╠" + "═" * 60 + "╣")
    print(f"║  ENEMY: {enemy.name}".ljust(61) + "║")
    print(f"║  ⚔️ {enemy_hp_bar} {enemy.current_hp}/{enemy.max_hp} HP  |  AC: {enemy.armor_class}  |  Damage: {enemy_damage}".ljust(61) + "║")
    print("╚" + "═" * 60 + "╝")


# =============================================================================
# MAIN COMBAT TEST
# =============================================================================

def main():
    print("=" * 60)
    print("      ⚔️ AI DM + COMBAT INTEGRATION TEST ⚔️")
    print("=" * 60)
    
    character = TestCharacter()
    enemy = create_enemy('goblin')
    
    print(f"\nYou are: {character.name} ({character.race} {character.char_class})")
    print(f"Wielding: {character.weapon.title()}")
    print(f"HP: {character.current_hp}/{character.max_hp}, AC: {character.armor_class}")
    
    print(f"\nOpponent: {enemy.name}")
    print(f"HP: {enemy.current_hp}/{enemy.max_hp}, AC: {enemy.armor_class}")
    
    # =========================================================================
    # INITIATIVE PHASE
    # =========================================================================
    print("\n" + "=" * 60)
    print("              🎯 INITIATIVE PHASE 🎯")
    print("=" * 60)
    
    input("\nPress Enter to roll initiative...")
    
    # Roll player initiative
    player_init = roll_initiative(character.get_ability_modifier('dexterity'))
    print(f"\n{format_initiative_roll(character.name, player_init)}")
    
    # Roll enemy initiative
    enemy_init = roll_initiative(enemy.dex_modifier)
    print(format_initiative_roll(enemy.name, enemy_init))
    
    # Determine turn order
    player_goes_first = player_init['total'] >= enemy_init['total']
    
    if player_goes_first:
        print(f"\n✨ {character.name} goes first!")
        turn_order = [character.name, enemy.name]
    else:
        print(f"\n⚡ {enemy.name} goes first!")
        turn_order = [enemy.name, character.name]
    
    print("\n╔══════════════════════════════════════╗")
    print("║          ⚔️ TURN ORDER ⚔️            ║")
    print("╠══════════════════════════════════════╣")
    for i, name in enumerate(turn_order, 1):
        marker = "(You)" if name == character.name else ""
        print(f"║  {i}. {name} {marker}".ljust(39) + "║")
    print("╚══════════════════════════════════════╝")
    
    print("\n" + "-" * 60)
    print("Combat commands: 'attack', 'defend', 'flee', 'status', 'quit'")
    print("-" * 60)
    
    model = create_dm()
    chat = model.start_chat(history=[])
    
    # Build initiative context for DM
    init_context = f"Initiative rolled! Turn order: "
    if player_goes_first:
        init_context += f"{character.name} ({player_init['total']}) then {enemy.name} ({enemy_init['total']}). {character.name} acts first!"
    else:
        init_context += f"{enemy.name} ({enemy_init['total']}) then {character.name} ({player_init['total']}). {enemy.name} acts first!"
    
    # Start combat
    print("\n🎲 Dungeon Master:")
    context = f"Combat begins! {init_context}\n\nKira (HP {character.current_hp}/{character.max_hp}) faces a {enemy.name} (HP {enemy.current_hp}/{enemy.max_hp}). Set the scene for this confrontation."
    
    if player_goes_first:
        context += f" The player acts first. Describe the tense standoff."
    else:
        context += f" The {enemy.name} acts first - describe it lunging to attack."
    
    dm_response = get_dm_response(chat, context)
    
    # If enemy goes first, process their attack
    if not player_goes_first:
        print(f"\n   The {enemy.name} attacks first!")
        input("   Press Enter...")
        
        enemy_atk, enemy_dmg = enemy_attack(enemy, character.armor_class)
        print(f"\n{format_enemy_attack(enemy_atk, enemy_dmg)}")
        
        if enemy_dmg:
            character.take_damage(enemy_dmg['total'])
            crit = " CRITICAL!" if enemy_atk['is_crit'] else ""
            enemy_msg = f"[ENEMY ATTACK: HIT for {enemy_dmg['total']} damage{crit}. Player HP: {character.current_hp}/{character.max_hp}]"
        else:
            enemy_msg = f"[ENEMY ATTACK: MISS. Player HP: {character.current_hp}/{character.max_hp}]"
        
        print("\n🎲 Dungeon Master:")
        dm_response = get_dm_response(chat, enemy_msg + f" Now it's {character.name}'s turn.")
    
    # Combat loop
    round_num = 1
    while True:
        if enemy.is_dead:
            print("\n🎉 Victory!")
            print("\n🎲 Dungeon Master:")
            dm_response = get_dm_response(chat, f"[VICTORY: Player killed the {enemy.name}! Narrate the killing blow and victory moment. Keep it to 2-3 dramatic sentences.]")
            break
        
        if character.current_hp <= 0:
            print("\n💀 You have fallen...")
            print("\n🎲 Dungeon Master:")
            dm_response = get_dm_response(chat, f"[DEFEAT: The {enemy.name} has struck down {character.name}! Narrate the death scene dramatically but briefly. 2-3 sentences.]")
            break
        
        show_combat_status(character, enemy, round_num)
        action = input("\n⚔️ Your action: ").strip().lower()
        
        if action in ['quit', 'exit', 'q']:
            print("\nCombat ended.")
            break
        
        if action == 'status':
            continue
        
        # Check for attack intent
        attack_words = ['attack', 'hit', 'strike', 'swing', 'slash', 'stab', 'a', 
                        'i attack', 'i hit', 'i strike', 'i swing', 'attack goblin',
                        'fight', 'i fight', 'kill', 'i kill']
        is_attack = any(word in action for word in attack_words) or action == 'a'
        
        # Check for defend action
        defend_words = ['defend', 'block', 'parry', 'dodge', 'i defend', 'i block', 'i dodge']
        is_defend = any(word in action for word in defend_words)
        
        # Check for flee action
        flee_words = ['flee', 'run', 'escape', 'retreat', 'i flee', 'i run', 'i escape', 'run away']
        is_flee = any(word in action for word in flee_words)
        
        if is_attack:
            # Player attack
            print(f"\n   Press Enter to attack the {enemy.name}...")
            input()
            
            attack = roll_attack(character, enemy.armor_class, character.weapon)
            print(f"\n{format_attack_result(attack)}")
            
            # Build message for DM
            if attack['is_crit']:
                damage = roll_damage(character, character.weapon, True)
                print(format_damage_result(damage))
                enemy.take_damage(damage['total'])
                result_msg = f"[ATTACK RESULT: CRITICAL HIT for {damage['total']} damage! {enemy.get_status()}]"
            elif attack['is_fumble']:
                result_msg = "[ATTACK RESULT: FUMBLE! The attack goes terribly wrong.]"
            elif attack['hit']:
                damage = roll_damage(character, character.weapon, False)
                print(format_damage_result(damage))
                enemy.take_damage(damage['total'])
                result_msg = f"[ATTACK RESULT: HIT for {damage['total']} damage. {enemy.get_status()}]"
            else:
                result_msg = f"[ATTACK RESULT: MISS. {enemy.get_status()}]"
            
            # DM narrates player attack
            print("\n🎲 Dungeon Master:")
            dm_response = get_dm_response(chat, result_msg)
            
            # Enemy counterattack if alive
            if not enemy.is_dead:
                print(f"\n   The {enemy.name} retaliates!")
                input("   Press Enter...")
                
                enemy_atk, enemy_dmg = enemy_attack(enemy, character.armor_class)
                print(f"\n{format_enemy_attack(enemy_atk, enemy_dmg)}")
                
                if enemy_dmg:
                    character.take_damage(enemy_dmg['total'])
                    crit = " CRITICAL!" if enemy_atk['is_crit'] else ""
                    enemy_msg = f"[ENEMY ATTACK: HIT for {enemy_dmg['total']} damage{crit}. Player HP: {character.current_hp}/{character.max_hp}]"
                else:
                    enemy_msg = f"[ENEMY ATTACK: MISS. Player HP: {character.current_hp}/{character.max_hp}]"
                
                print("\n🎲 Dungeon Master:")
                dm_response = get_dm_response(chat, enemy_msg)
        
        elif is_defend:
            # Defend action - gives +2 AC for enemy's attack this round
            print("\n🛡️ You take a defensive stance! (+2 AC this round)")
            temp_ac_bonus = 2
            
            # Enemy attacks against boosted AC
            if not enemy.is_dead:
                print(f"\n   The {enemy.name} attacks!")
                input("   Press Enter...")
                
                boosted_ac = character.armor_class + temp_ac_bonus
                enemy_atk, enemy_dmg = enemy_attack(enemy, boosted_ac)
                print(f"\n{format_enemy_attack(enemy_atk, enemy_dmg)}")
                
                if enemy_dmg:
                    character.take_damage(enemy_dmg['total'])
                    enemy_msg = f"[PLAYER DEFENDED but {enemy.name} HIT for {enemy_dmg['total']} damage. Player HP: {character.current_hp}/{character.max_hp}]"
                else:
                    enemy_msg = f"[PLAYER DEFENDED - {enemy.name} attack DEFLECTED. Player HP: {character.current_hp}/{character.max_hp}]"
                
                print("\n🎲 Dungeon Master:")
                dm_response = get_dm_response(chat, enemy_msg)
        
        elif is_flee:
            # Flee action - DEX check to escape
            print("\n🏃 You attempt to flee!")
            input("   Press Enter to roll escape check...")
            
            flee_dc = 10 + enemy.dex_modifier
            flee_roll = random.randint(1, 20)
            flee_mod = character.get_ability_modifier('dexterity')
            flee_total = flee_roll + flee_mod
            
            mod_sign = '+' if flee_mod >= 0 else ''
            
            if flee_total >= flee_dc:
                print(f"\n🎯 Escape: [{flee_roll}]{mod_sign}{flee_mod} = {flee_total} vs DC {flee_dc} = ✅ ESCAPED!")
                print("\n🎲 Dungeon Master:")
                dm_response = get_dm_response(chat, "[FLEE: SUCCESS - Player escaped! Describe their retreat.]")
                print("\n🏃 You successfully fled the battle!")
                break
            else:
                print(f"\n🎯 Escape: [{flee_roll}]{mod_sign}{flee_mod} = {flee_total} vs DC {flee_dc} = ❌ FAILED!")
                print(f"\n   The {enemy.name} gets an opportunity attack!")
                input("   Press Enter...")
                
                enemy_atk, enemy_dmg = enemy_attack(enemy, character.armor_class)
                print(f"\n{format_enemy_attack(enemy_atk, enemy_dmg)}")
                
                if enemy_dmg:
                    character.take_damage(enemy_dmg['total'])
                    enemy_msg = f"[FLEE FAILED - Opportunity attack HIT for {enemy_dmg['total']}. Player HP: {character.current_hp}/{character.max_hp}]"
                else:
                    enemy_msg = f"[FLEE FAILED - Opportunity attack MISSED. Player HP: {character.current_hp}/{character.max_hp}]"
                
                print("\n🎲 Dungeon Master:")
                dm_response = get_dm_response(chat, enemy_msg)
        
        else:
            # Unrecognized action - ask player to clarify (don't skip their turn!)
            print(f"\n❓ Unknown action: '{action}'")
            print("   Valid commands: attack, defend, flee, status, quit")
            print("   (Your turn is NOT skipped - try again)")
            # Continue loop without enemy attacking - player keeps their turn
            continue
        
        # Increment round after valid action (unknown actions skip via continue above)
        round_num += 1
    
    print("\nCombat test complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCombat interrupted.")
