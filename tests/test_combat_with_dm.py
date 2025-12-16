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
    roll_attack, roll_attack_with_advantage, roll_damage, enemy_attack,
    format_attack_result, format_damage_result, format_enemy_attack,
    roll_initiative, format_initiative_roll, determine_turn_order,
    display_turn_order, Combatant
)
from game import (
    build_combat_context, get_combat_narration, display_combat_narration,
    COMBAT_NARRATION_PROMPT
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
        self.level = 1
        self.experience = 0
    
    # XP thresholds for leveling (same as main Character class)
    XP_THRESHOLDS = {1: 0, 2: 100, 3: 300, 4: 600, 5: 1000}
    
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
    
    def gain_xp(self, amount: int, source: str = ""):
        """Add XP and check if level up is available."""
        old_xp = self.experience
        self.experience += amount
        can_level = self.can_level_up()
        return {
            'old_xp': old_xp,
            'new_xp': self.experience,
            'gained': amount,
            'source': source,
            'level_up': can_level
        }
    
    def can_level_up(self) -> bool:
        """Check if character has enough XP to level up."""
        if self.level >= 5:
            return False
        next_level = self.level + 1
        return self.experience >= self.XP_THRESHOLDS.get(next_level, float('inf'))
    
    def xp_to_next_level(self) -> int:
        """Return XP needed to reach next level."""
        if self.level >= 5:
            return 0
        next_level = self.level + 1
        threshold = self.XP_THRESHOLDS.get(next_level, self.experience)
        return max(0, threshold - self.experience)
    
    def level_up(self) -> dict:
        """Level up the character if eligible."""
        if not self.can_level_up():
            return None
        
        old_level = self.level
        self.level += 1
        
        # Gain HP
        con_mod = self.get_ability_modifier('constitution')
        hp_gain = max(1, 5 + con_mod)  # Fighter uses d10, avg 5.5 -> 5
        self.max_hp += hp_gain
        self.current_hp += hp_gain
        
        return {
            'old_level': old_level,
            'new_level': self.level,
            'hp_gain': hp_gain,
            'new_max_hp': self.max_hp
        }


# =============================================================================
# COMBAT NARRATION SYSTEM TESTS
# =============================================================================

def test_combat_context_building():
    """Test that build_combat_context creates proper context dicts."""
    print("\n" + "=" * 60)
    print("     COMBAT NARRATION SYSTEM TESTS")
    print("=" * 60)
    
    # Test hit context
    attack_result = {'hit': True, 'is_crit': False, 'is_fumble': False}
    damage_result = {'total': 8, 'damage_type': 'slashing'}
    
    context = build_combat_context(
        attacker_name="Kira",
        target_name="Goblin",
        weapon="longsword",
        attack_result=attack_result,
        damage_result=damage_result,
        target_died=False,
        is_player_attacking=True
    )
    
    assert context['attacker'] == "Kira"
    assert context['target'] == "Goblin"
    assert context['weapon'] == "longsword"
    assert context['outcome'] == 'hit'
    assert context['damage'] == 8
    assert context['damage_type'] == 'slashing'
    assert context['is_player_attack'] == True
    print("✅ Hit context built correctly")
    
    # Test critical hit context
    attack_result_crit = {'hit': True, 'is_crit': True, 'is_fumble': False}
    context_crit = build_combat_context(
        attacker_name="Kira",
        target_name="Orc",
        weapon="greatsword",
        attack_result=attack_result_crit,
        damage_result={'total': 18, 'damage_type': 'slashing'},
        target_died=True,
        is_player_attacking=True
    )
    
    assert context_crit['outcome'] == 'critical_hit'
    assert context_crit['target_killed'] == True
    print("✅ Critical hit context built correctly")
    
    # Test miss context
    attack_result_miss = {'hit': False, 'is_crit': False, 'is_fumble': False}
    context_miss = build_combat_context(
        attacker_name="Kira",
        target_name="Wolf",
        weapon="shortbow",
        attack_result=attack_result_miss,
        damage_result=None,
        target_died=False,
        is_player_attacking=True
    )
    
    assert context_miss['outcome'] == 'miss'
    assert 'damage' not in context_miss
    print("✅ Miss context built correctly")
    
    # Test fumble context
    attack_result_fumble = {'hit': False, 'is_crit': False, 'is_fumble': True}
    context_fumble = build_combat_context(
        attacker_name="Kira",
        target_name="Skeleton",
        weapon="mace",
        attack_result=attack_result_fumble,
        damage_result=None,
        target_died=False,
        is_player_attacking=True
    )
    
    assert context_fumble['outcome'] == 'critical_miss'
    print("✅ Fumble context built correctly")
    
    # Test enemy attack context
    enemy_attack_result = {'hit': True, 'is_crit': False, 'is_fumble': False}
    enemy_context = build_combat_context(
        attacker_name="Goblin",
        target_name="Kira",
        weapon="rusty dagger",
        attack_result=enemy_attack_result,
        damage_result={'total': 5, 'damage_type': 'piercing'},
        target_died=False,
        is_player_attacking=False
    )
    
    assert enemy_context['is_player_attack'] == False
    assert enemy_context['attacker'] == "Goblin"
    print("✅ Enemy attack context built correctly")
    
    print("\n✅ All combat context tests passed!")
    return True


def test_combat_narration_with_ai():
    """Test actual AI combat narration generation."""
    print("\n" + "=" * 60)
    print("     AI COMBAT NARRATION TEST")
    print("=" * 60)
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("⚠️ GOOGLE_API_KEY not set - skipping AI narration test")
        return True
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="gemini-2.0-flash")
    chat = model.start_chat(history=[])
    
    # Test narration for a hit
    attack_result = {'hit': True, 'is_crit': False, 'is_fumble': False}
    damage_result = {'total': 8, 'damage_type': 'slashing'}
    
    context = build_combat_context(
        attacker_name="Kira",
        target_name="Goblin",
        weapon="longsword",
        attack_result=attack_result,
        damage_result=damage_result,
        target_died=False,
        is_player_attacking=True
    )
    
    print("\n📖 Testing AI narration for a HIT...")
    narration = get_combat_narration(chat, context)
    print(f"   Narration: {narration}")
    assert len(narration) > 10, "Narration should have meaningful content"
    print("✅ AI generated narration for hit")
    
    # Test narration for a critical hit kill
    context_crit = build_combat_context(
        attacker_name="Kira",
        target_name="Orc Warlord",
        weapon="greatsword",
        attack_result={'hit': True, 'is_crit': True, 'is_fumble': False},
        damage_result={'total': 24, 'damage_type': 'slashing'},
        target_died=True,
        is_player_attacking=True
    )
    
    print("\n📖 Testing AI narration for CRITICAL HIT KILL...")
    narration_crit = get_combat_narration(chat, context_crit)
    print(f"   Narration: {narration_crit}")
    assert len(narration_crit) > 10, "Narration should have meaningful content"
    print("✅ AI generated narration for critical kill")
    
    # Test enemy attack narration
    enemy_context = build_combat_context(
        attacker_name="Wolf",
        target_name="Kira",
        weapon="claws",
        attack_result={'hit': True, 'is_crit': False, 'is_fumble': False},
        damage_result={'total': 6, 'damage_type': 'piercing'},
        target_died=False,
        is_player_attacking=False
    )
    
    print("\n📖 Testing AI narration for ENEMY ATTACK...")
    narration_enemy = get_combat_narration(chat, enemy_context)
    print(f"   Narration: {narration_enemy}")
    assert len(narration_enemy) > 10, "Narration should have meaningful content"
    print("✅ AI generated narration for enemy attack")
    
    print("\n✅ All AI narration tests passed!")
    return True


def test_display_combat_narration():
    """Test the display function handles edge cases."""
    print("\n" + "=" * 60)
    print("     DISPLAY NARRATION TESTS")
    print("=" * 60)
    
    # Test with valid narration
    import io
    import sys
    
    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    
    display_combat_narration("Your blade strikes true!")
    
    output = buffer.getvalue()
    sys.stdout = old_stdout
    
    assert "📖" in output
    assert "Your blade strikes true!" in output
    print("✅ Valid narration displays correctly")
    
    # Test with empty narration (should not print anything)
    sys.stdout = buffer = io.StringIO()
    display_combat_narration("")
    output = buffer.getvalue()
    sys.stdout = old_stdout
    
    assert output == ""
    print("✅ Empty narration handled correctly (no output)")
    
    # Test with None-like narration
    sys.stdout = buffer = io.StringIO()
    display_combat_narration(None)  # Should handle gracefully
    sys.stdout = old_stdout
    print("✅ None narration handled gracefully")
    
    print("\n✅ All display tests passed!")
    return True


def run_narration_tests():
    """Run all combat narration tests."""
    print("\n" + "=" * 60)
    print("     RUNNING COMBAT NARRATION SYSTEM TESTS")
    print("=" * 60)
    
    tests_passed = 0
    tests_failed = 0
    
    try:
        if test_combat_context_building():
            tests_passed += 1
    except Exception as e:
        print(f"❌ Context building test failed: {e}")
        tests_failed += 1
    
    try:
        if test_display_combat_narration():
            tests_passed += 1
    except Exception as e:
        print(f"❌ Display test failed: {e}")
        tests_failed += 1
    
    try:
        if test_combat_narration_with_ai():
            tests_passed += 1
    except Exception as e:
        print(f"❌ AI narration test failed: {e}")
        tests_failed += 1
    
    print("\n" + "=" * 60)
    print(f"     NARRATION TESTS: {tests_passed} passed, {tests_failed} failed")
    print("=" * 60)
    
    return tests_failed == 0


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

def select_enemies():
    """Let user select enemy configuration for testing."""
    print("\n📋 SELECT ENEMY CONFIGURATION:")
    print("-" * 40)
    print("  1. Single goblin")
    print("  2. Two goblins (multi-enemy test)")
    print("  3. Goblin + Wolf (mixed enemies)")
    print("  4. Three wolves (pack attack)")
    print("  5. Goblin Boss + 2 goblins")
    print("  6. Custom (enter enemy types)")
    print("-" * 40)
    print("  7. Two goblins + SURPRISE (ambush test)")
    print("  8. Goblin + Wolf + SURPRISE")
    print("-" * 40)
    print("  Tip: Add 's' to any option for surprise (e.g., '2s', '4s')")
    print("-" * 40)
    
    choice = input("\nSelect (1-8): ").strip()
    
    # Check for surprise modifier
    surprise_player = False
    if 's' in choice.lower():
        surprise_player = True
        choice = choice.lower().replace('s', '').strip()
        print("⚡ SURPRISE enabled! Enemies will be surprised in round 1.")
    
    if choice == '1':
        enemies = [create_enemy('goblin')]
    elif choice == '2':
        enemies = [create_enemy('goblin'), create_enemy('goblin')]
        enemies[0].name = "Goblin 1"
        enemies[1].name = "Goblin 2"
    elif choice == '3':
        enemies = [create_enemy('goblin'), create_enemy('wolf')]
    elif choice == '4':
        enemies = [create_enemy('wolf'), create_enemy('wolf'), create_enemy('wolf')]
        for i, e in enumerate(enemies, 1):
            e.name = f"Wolf {i}"
    elif choice == '5':
        enemies = [create_enemy('goblin_boss'), create_enemy('goblin'), create_enemy('goblin')]
        enemies[1].name = "Goblin 1"
        enemies[2].name = "Goblin 2"
    elif choice == '6':
        print("\nEnter enemy types separated by commas (e.g., 'goblin, orc, wolf'):")
        print("Available: goblin, goblin_boss, orc, wolf, skeleton, bandit, giant_spider")
        custom = input("> ").strip()
        enemy_types = [e.strip().lower().replace(' ', '_') for e in custom.split(',')]
        enemies = []
        type_counts = {}
        for etype in enemy_types:
            type_counts[etype] = type_counts.get(etype, 0) + 1
        type_indices = {}
        for etype in enemy_types:
            enemy = create_enemy(etype)
            if enemy:
                if type_counts.get(etype, 1) > 1:
                    type_indices[etype] = type_indices.get(etype, 0) + 1
                    enemy.name = f"{enemy.name} {type_indices[etype]}"
                enemies.append(enemy)
        if not enemies:
            print("No valid enemies, defaulting to goblin.")
    elif choice == '7':
        # Multi-enemy + Surprise combo test
        enemies = [create_enemy('goblin'), create_enemy('goblin')]
        enemies[0].name = "Goblin 1"
        enemies[1].name = "Goblin 2"
        surprise_player = True
    elif choice == '8':
        # Mixed enemies + Surprise combo test
        enemies = [create_enemy('goblin'), create_enemy('wolf')]
        surprise_player = True
    else:
        print("Invalid choice, defaulting to single goblin.")
        enemies = [create_enemy('goblin')]
    
    return enemies, surprise_player


def show_multi_combat_status(character, enemies, round_num=1):
    """Display combat status for multiple enemies."""
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
    
    weapon_name = character.weapon.title()
    weapon_data = WEAPONS.get(character.weapon, {})
    weapon_damage = weapon_data.get('damage', '1d6')
    
    print()
    print("╔" + "═" * 60 + "╗")
    print(f"║  🗡️ COMBAT STATUS - Round {round_num}".ljust(61) + "║")
    print("╠" + "═" * 60 + "╣")
    print(f"║  YOU: {character.name} ({character.char_class})".ljust(61) + "║")
    print(f"║  {hp_color} {hp_bar} {character.current_hp}/{character.max_hp} HP  |  AC: {character.armor_class}  |  {weapon_name} ({weapon_damage})".ljust(61) + "║")
    print("╠" + "═" * 60 + "╣")
    print("║  ENEMIES:".ljust(61) + "║")
    
    for i, enemy in enumerate(enemies, 1):
        if enemy.is_dead:
            print(f"║  [{i}] ☠️ {enemy.name} - DEFEATED".ljust(61) + "║")
        else:
            e_hp_percent = enemy.current_hp / enemy.max_hp
            e_hp_filled = int(e_hp_percent * 10)
            e_hp_bar = "█" * e_hp_filled + "░" * (10 - e_hp_filled)
            print(f"║  [{i}] {enemy.name}: {e_hp_bar} {enemy.current_hp}/{enemy.max_hp} HP, AC {enemy.armor_class}".ljust(61) + "║")
    
    print("╚" + "═" * 60 + "╝")


def main():
    print("=" * 60)
    print("      ⚔️ AI DM + COMBAT INTEGRATION TEST ⚔️")
    print("=" * 60)
    
    character = TestCharacter()
    enemies, surprise_player = select_enemies()
    
    print(f"\nYou are: {character.name} ({character.race} {character.char_class})")
    print(f"Wielding: {character.weapon.title()}")
    print(f"HP: {character.current_hp}/{character.max_hp}, AC: {character.armor_class}")
    
    if surprise_player:
        print("\n⚡ SURPRISE ATTACK! Enemies are caught off guard!")
    
    print(f"\nOpponents ({len(enemies)}):")
    for i, enemy in enumerate(enemies, 1):
        print(f"  [{i}] {enemy.name} - HP: {enemy.current_hp}/{enemy.max_hp}, AC: {enemy.armor_class}")
    
    # Use first enemy for backwards compatibility with single-enemy code
    enemy = enemies[0]
    
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
    
    # Roll initiative for ALL enemies
    enemy_initiatives = []
    for e in enemies:
        e_init = roll_initiative(e.dex_modifier)
        enemy_initiatives.append((e, e_init))
        print(format_initiative_roll(e.name, e_init))
    
    # Determine turn order - collect all combatants with their initiatives
    combatants = [('player', character.name, player_init['total'])]
    for e, e_init in enemy_initiatives:
        combatants.append(('enemy', e.name, e_init['total']))
    
    # Sort by initiative (highest first), player wins ties
    combatants.sort(key=lambda x: (x[2], 1 if x[0] == 'player' else 0), reverse=True)
    
    # Check if player goes before any enemy
    player_goes_first = combatants[0][0] == 'player'
    
    if player_goes_first:
        print(f"\n✨ {character.name} goes first!")
    else:
        print(f"\n⚡ {combatants[0][1]} goes first!")
    
    # Surprise announcement
    if surprise_player:
        print("\n⚡ SURPRISE! You have caught the enemies off guard!")
        print("   Enemies are surprised and cannot act in Round 1.")
        print("   You have ADVANTAGE on your first attack (roll 2d20, take higher).")
    
    print("\n╔══════════════════════════════════════╗")
    print("║          ⚔️ TURN ORDER ⚔️            ║")
    print("╠══════════════════════════════════════╣")
    for i, (ctype, name, init_val) in enumerate(combatants, 1):
        marker = "(You)" if ctype == 'player' else ""
        surprised_mark = " (SURPRISED)" if ctype == 'enemy' and surprise_player else ""
        print(f"║  {i}. {name} [{init_val}] {marker}{surprised_mark}".ljust(39) + "║")
    print("╚══════════════════════════════════════╝")
    
    print("\n" + "-" * 60)
    print("Combat commands: 'attack', 'defend', 'flee', 'status', 'quit'")
    print("-" * 60)
    
    model = create_dm()
    chat = model.start_chat(history=[])
    
    # Build initiative context for DM
    turn_order_str = ", ".join([f"{name} ({init_val})" for _, name, init_val in combatants])
    init_context = f"Initiative rolled! Turn order: {turn_order_str}."
    if player_goes_first:
        init_context += f" {character.name} acts first!"
    else:
        init_context += f" Enemies act first!"
    
    # Start combat
    print("\n🎲 Dungeon Master:")
    # Build initial context for DM - mention all enemies
    enemy_names = ", ".join([e.name for e in enemies])
    if surprise_player:
        context = f"Combat begins with SURPRISE! {init_context}\n\nKira (HP {character.current_hp}/{character.max_hp}) has caught {enemy_names} off guard! The enemies are surprised and cannot act in Round 1. Kira has advantage on her first attack! Set the scene for this ambush."
    else:
        context = f"Combat begins! {init_context}\n\nKira (HP {character.current_hp}/{character.max_hp}) faces {enemy_names}. Set the scene for this confrontation."
    
    dm_response = get_dm_response(chat, context)
    
    # =========================================================================
    # PROPER TURN-BASED COMBAT LOOP
    # Each combatant takes their turn in initiative order
    # =========================================================================
    
    round_num = 1
    player_is_defending = False  # Track if player is defending this round
    player_has_advantage = surprise_player  # Track if player has advantage on first attack
    
    while True:
        print(f"\n{'='*60}")
        print(f"                    ROUND {round_num}")
        print(f"{'='*60}")
        
        # Process each turn in initiative order
        for turn_idx, (ctype, name, init_val) in enumerate(combatants):
            # Check win/lose conditions
            alive_enemies = [e for e in enemies if not e.is_dead]
            if not alive_enemies:
                print("\n🎉 Victory! All enemies defeated!")
                
                # Award XP based on enemies defeated
                xp_per_enemy = {'Goblin': 25, 'Orc': 50, 'Skeleton': 25, 'Wolf': 25, 'Bandit': 50}
                total_xp = 0
                xp_breakdown = []
                for e in enemies:
                    xp_val = xp_per_enemy.get(e.name, 25)
                    total_xp += xp_val
                    xp_breakdown.append(f"{e.name}: {xp_val}")
                
                print(f"\n{'='*50}")
                print(f"  ⭐ EXPERIENCE GAINED")
                print(f"{'='*50}")
                for entry in xp_breakdown:
                    print(f"  • {entry} XP")
                print(f"  ────────────────────────")
                print(f"  Total: +{total_xp} XP")
                
                # Award XP to character
                xp_result = character.gain_xp(total_xp, "Combat Victory")
                print(f"  XP: {xp_result['old_xp']} → {xp_result['new_xp']}")
                
                # Check for level up
                if xp_result['level_up']:
                    print(f"\n  🎉 LEVEL UP AVAILABLE!")
                    print(f"  Type 'levelup' to advance (or press Enter to skip)...")
                    level_input = input("  > ").strip().lower()
                    if level_input in ['levelup', 'level up', 'y', 'yes', '']:
                        result = character.level_up()
                        if result:
                            print(f"\n  {'='*40}")
                            print(f"  🎉 LEVEL UP! Level {result['old_level']} → {result['new_level']}!")
                            print(f"  ❤️  +{result['hp_gain']} HP (now {result['new_max_hp']} max)")
                            print(f"  {'='*40}")
                else:
                    xp_needed = character.xp_to_next_level()
                    print(f"  Need {xp_needed} more XP to reach Level {character.level + 1}")
                
                print(f"{'='*50}")
                
                print("\n🎲 Dungeon Master:")
                dm_response = get_dm_response(chat, f"[VICTORY: Player defeated all enemies! They gained {total_xp} XP. Narrate the victory moment. 2-3 dramatic sentences.]")
                print("\nCombat test complete!")
                return
            
            if character.current_hp <= 0:
                print("\n💀 You have fallen...")
                print("\n🎲 Dungeon Master:")
                dm_response = get_dm_response(chat, f"[DEFEAT: The enemies have struck down {character.name}! Narrate the death scene. 2-3 sentences.]")
                print("\nCombat test complete!")
                return
            
            # === PLAYER'S TURN ===
            if ctype == 'player':
                # Reset defend at start of player's turn (defend lasts until next turn)
                was_defending = player_is_defending
                player_is_defending = False
                
                show_multi_combat_status(character, enemies, round_num)
                print(f"\n   🎯 {character.name}'s turn (Initiative: {init_val})")
                
                if len(alive_enemies) > 1:
                    print(f"   Target with 'attack 1', 'attack 2', etc. or just type a number.")
                
                # Player action loop (retry on invalid input)
                player_acted = False
                while not player_acted:
                    action = input("\n⚔️ Your action: ").strip().lower()
                    
                    if action in ['quit', 'exit', 'q']:
                        print("\nCombat ended.")
                        return
                    
                    if action == 'status':
                        show_multi_combat_status(character, enemies, round_num)
                        continue
                    
                    # Check for attack
                    attack_words = ['attack', 'hit', 'strike', 'swing', 'slash', 'stab', 'a', 
                                    'i attack', 'fight', 'kill']
                    is_attack = any(word in action for word in attack_words) or action == 'a' or action.isdigit()
                    
                    # Check for defend
                    defend_words = ['defend', 'block', 'parry', 'dodge']
                    is_defend = any(word in action for word in defend_words)
                    
                    # Check for flee
                    flee_words = ['flee', 'run', 'escape', 'retreat']
                    is_flee = any(word in action for word in flee_words)
                    
                    if is_attack:
                        # Determine target
                        target_enemy = None
                        if len(alive_enemies) == 1:
                            target_enemy = alive_enemies[0]
                        else:
                            target_num = None
                            for word in action.split():
                                if word.isdigit():
                                    target_num = int(word)
                                    break
                            if target_num is None and action.isdigit():
                                target_num = int(action)
                            
                            if target_num and 1 <= target_num <= len(enemies):
                                target_enemy = enemies[target_num - 1]
                                if target_enemy.is_dead:
                                    print(f"\n  ❌ {target_enemy.name} is already defeated!")
                                    continue
                            else:
                                print(f"\n  ❓ Which enemy? (1-{len(enemies)})")
                                for i, e in enumerate(enemies, 1):
                                    if not e.is_dead:
                                        print(f"     [{i}] {e.name}")
                                continue
                        
                        # Execute attack
                        if player_has_advantage:
                            print(f"\n   ⬆️ Press Enter to attack {target_enemy.name} with ADVANTAGE...")
                        else:
                            print(f"\n   Press Enter to attack {target_enemy.name}...")
                        input()
                        
                        # Use advantage roll if player still has it (first attack after surprise)
                        if player_has_advantage:
                            attack = roll_attack_with_advantage(character, target_enemy.armor_class, character.weapon)
                            player_has_advantage = False  # Consume advantage after first attack
                        else:
                            attack = roll_attack(character, target_enemy.armor_class, character.weapon)
                        print(f"\n{format_attack_result(attack)}")
                        
                        # NEW NARRATION SYSTEM
                        damage_result = None
                        target_died = False
                        
                        if attack['is_crit']:
                            damage = roll_damage(character, character.weapon, True)
                            print(format_damage_result(damage))
                            target_died = target_enemy.current_hp - damage['total'] <= 0
                            target_enemy.take_damage(damage['total'])
                            damage_result = {'total': damage['total'], 'damage_type': damage.get('damage_type', 'physical')}
                        elif attack['is_fumble']:
                            pass  # No damage on fumble
                        elif attack['hit']:
                            damage = roll_damage(character, character.weapon, False)
                            print(format_damage_result(damage))
                            target_died = target_enemy.current_hp - damage['total'] <= 0
                            target_enemy.take_damage(damage['total'])
                            damage_result = {'total': damage['total'], 'damage_type': damage.get('damage_type', 'physical')}
                        
                        # Build context and get AI narration
                        combat_ctx = build_combat_context(
                            attacker_name=character.name,
                            target_name=target_enemy.name,
                            weapon=character.weapon,
                            attack_result=attack,
                            damage_result=damage_result,
                            target_died=target_died,
                            is_player_attacking=True
                        )
                        narration = get_combat_narration(chat, combat_ctx)
                        display_combat_narration(narration)
                        
                        player_acted = True
                        player_is_defending = False
                        
                    elif is_defend:
                        print("\n🛡️ You take a defensive stance! (+2 AC until your next turn)")
                        player_is_defending = True
                        # Simple defend narration using new format
                        defend_ctx = {
                            'attacker': character.name,
                            'target': 'self',
                            'weapon': 'shield/stance',
                            'outcome': 'defend',
                            'is_player_attack': True
                        }
                        import json
                        defend_prompt = f"Briefly narrate (1 sentence) the player taking a defensive stance. Context: {json.dumps(defend_ctx)}"
                        try:
                            defend_narration = chat.send_message(defend_prompt).text.strip()
                            display_combat_narration(defend_narration)
                        except:
                            pass
                        player_acted = True
                        
                    elif is_flee:
                        print("\n🏃 You attempt to flee!")
                        input("   Press Enter to roll escape check...")
                        
                        highest_dex = max(e.dex_modifier for e in alive_enemies)
                        flee_dc = 10 + highest_dex
                        flee_roll = random.randint(1, 20)
                        flee_mod = character.get_ability_modifier('dexterity')
                        flee_total = flee_roll + flee_mod
                        mod_sign = '+' if flee_mod >= 0 else ''
                        
                        if flee_total >= flee_dc:
                            print(f"\n🎯 Escape: [{flee_roll}]{mod_sign}{flee_mod} = {flee_total} vs DC {flee_dc} = ✅ ESCAPED!")
                            # Narration for successful escape
                            escape_ctx = {
                                'attacker': character.name,
                                'target': 'escape',
                                'weapon': 'none',
                                'outcome': 'success',
                                'is_player_attack': True
                            }
                            import json
                            escape_prompt = f"Narrate the player's dramatic escape from combat. 2 sentences. Context: {json.dumps(escape_ctx)}"
                            try:
                                escape_narration = chat.send_message(escape_prompt).text.strip()
                                display_combat_narration(escape_narration)
                            except:
                                pass
                            print("\n🏃 You successfully fled!")
                            print("\nCombat test complete!")
                            return
                        else:
                            print(f"\n🎯 Escape: [{flee_roll}]{mod_sign}{flee_mod} = {flee_total} vs DC {flee_dc} = ❌ FAILED!")
                            # Opportunity attacks from all enemies with NEW narration system
                            for opp_enemy in alive_enemies:
                                print(f"\n   {opp_enemy.name} gets an opportunity attack!")
                                input("   Press Enter...")
                                enemy_atk, enemy_dmg = enemy_attack(opp_enemy, character.armor_class)
                                print(f"\n{format_enemy_attack(enemy_atk, enemy_dmg)}")
                                
                                # NEW narration for opportunity attack
                                opp_damage_result = None
                                if enemy_dmg:
                                    character.take_damage(enemy_dmg['total'])
                                    opp_damage_result = {
                                        'total': enemy_dmg['total'],
                                        'damage_type': 'physical'
                                    }
                                
                                opp_weapon = "claws" if "wolf" in opp_enemy.name.lower() else "rusty dagger"
                                opp_ctx = build_combat_context(
                                    attacker_name=opp_enemy.name,
                                    target_name=character.name,
                                    weapon=opp_weapon,
                                    attack_result=enemy_atk,
                                    damage_result=opp_damage_result,
                                    target_died=False,
                                    is_player_attacking=False
                                )
                                opp_narration = get_combat_narration(chat, opp_ctx)
                                display_combat_narration(opp_narration)
                                
                                if character.current_hp <= 0:
                                    break
                            player_acted = True
                            player_is_defending = False
                    else:
                        print(f"\n❓ Unknown action: '{action}'")
                        print("   Valid: attack, defend, flee, status, quit")
            
            # === ENEMY'S TURN ===
            else:
                # Find the enemy object
                current_enemy = None
                for e in enemies:
                    if e.name == name:
                        current_enemy = e
                        break
                
                if current_enemy and not current_enemy.is_dead:
                    # Surprise: enemies skip their turn in round 1
                    if surprise_player and round_num == 1:
                        print(f"\n   😵 {current_enemy.name} is SURPRISED and loses their turn!")
                        continue
                    
                    print(f"\n   ⚔️ {current_enemy.name}'s turn (Initiative: {init_val})")
                    input("   Press Enter...")
                    
                    # Apply defend bonus if player is defending
                    effective_ac = character.armor_class + (2 if player_is_defending else 0)
                    
                    enemy_atk, enemy_dmg = enemy_attack(current_enemy, effective_ac)
                    print(f"\n{format_enemy_attack(enemy_atk, enemy_dmg)}")
                    
                    # NEW NARRATION SYSTEM for enemy attacks
                    enemy_damage_result = None
                    if enemy_dmg:
                        character.take_damage(enemy_dmg['total'])
                        enemy_damage_result = {
                            'total': enemy_dmg['total'],
                            'damage_type': 'physical',
                            'is_crit': enemy_atk.get('is_crit', False)
                        }
                    
                    # Determine enemy weapon based on type
                    enemy_weapon = "claws" if "wolf" in current_enemy.name.lower() else "rusty dagger"
                    
                    combat_ctx = build_combat_context(
                        attacker_name=current_enemy.name,
                        target_name=character.name,
                        weapon=enemy_weapon,
                        attack_result=enemy_atk,
                        damage_result=enemy_damage_result,
                        target_died=False,  # Don't spoil player death
                        is_player_attacking=False
                    )
                    narration = get_combat_narration(chat, combat_ctx)
                    display_combat_narration(narration)
        
        # End of round
        round_num += 1
        # Note: player_is_defending is reset at start of player's turn, not here
    
    print("\nCombat test complete!")


def show_test_menu():
    """Show test selection menu."""
    print("\n" + "=" * 60)
    print("      ⚔️ COMBAT + DM TEST SUITE ⚔️")
    print("=" * 60)
    print("\nSelect test to run:")
    print("  1. Combat Narration System Tests (unit tests)")
    print("  2. Interactive Combat Test (full combat simulation)")
    print("  3. Run All Tests")
    print("  0. Exit")
    
    choice = input("\nChoice: ").strip()
    return choice


if __name__ == "__main__":
    try:
        choice = show_test_menu()
        
        if choice == '1':
            run_narration_tests()
        elif choice == '2':
            main()
        elif choice == '3':
            print("\n🧪 Running unit tests first...")
            if run_narration_tests():
                print("\n🎮 Now running interactive combat test...")
                main()
            else:
                print("\n❌ Unit tests failed. Fix before running interactive test.")
        elif choice == '0':
            print("Goodbye!")
        else:
            print("Invalid choice. Running interactive combat test...")
            main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted.")
