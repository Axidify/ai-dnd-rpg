"""
AI D&D Text RPG - Core Game (Phase 2)
A D&D adventure where AI acts as Dungeon Master.
Now with integrated skill checks, dice rolling, and combat!
"""

import os
import re
import random
from dotenv import load_dotenv
import google.generativeai as genai
from character import Character, create_character_interactive, CLASSES, RACES
from scenario import ScenarioManager
from combat import (
    create_enemy, Enemy, ENEMIES, WEAPONS,
    roll_attack, roll_attack_with_advantage, roll_damage, enemy_attack,
    format_attack_result, format_damage_result, format_enemy_attack,
    roll_initiative, format_initiative_roll
)
from inventory import (
    get_item, add_item_to_inventory, remove_item_from_inventory,
    find_item_in_inventory, format_inventory, format_item_details,
    use_item, generate_loot, gold_from_enemy, Item, ItemType
)
from save_system import SaveManager, quick_save, quick_load, format_saves_list

# Load environment variables from .env
load_dotenv()


# =============================================================================
# DICE SYSTEM
# =============================================================================

# Skill to ability mapping for D&D 5e
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


def roll_skill_check(character: Character, skill_name: str, dc: int) -> dict:
    """Roll a skill check using the character's stats."""
    skill_lower = skill_name.lower().replace(' ', '_')
    
    # Map skill to ability, or use the skill name as ability for raw checks
    if skill_lower in SKILL_ABILITIES:
        ability = SKILL_ABILITIES[skill_lower]
    else:
        # Try direct ability check (strength, dexterity, etc.)
        ability = skill_lower
    
    # Get modifier from character using the new method
    modifier = character.get_ability_modifier(ability)
    
    # Roll d20
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


def format_roll_result(result: dict) -> str:
    """Format a roll result for display."""
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


def parse_roll_request(dm_response: str) -> tuple:
    """Parse [ROLL: skill DC X] from DM response."""
    pattern = r'\[ROLL:\s*(\w+)\s+DC\s*(\d+)\]'
    match = re.search(pattern, dm_response, re.IGNORECASE)
    
    if match:
        skill = match.group(1)
        dc = int(match.group(2))
        return skill, dc
    return None, None


def parse_combat_request(dm_response: str) -> tuple:
    """Parse [COMBAT: enemy_type, enemy_type, ... | SURPRISE] from DM response.
    
    Supports multiple enemies and surprise modifier:
    - [COMBAT: goblin] -> (['goblin'], False)
    - [COMBAT: goblin, goblin] -> (['goblin', 'goblin'], False)
    - [COMBAT: goblin, goblin | SURPRISE] -> (['goblin', 'goblin'], True)
    - [COMBAT: goblin | SURPRISE] -> (['goblin'], True)
    
    Returns tuple of (list of enemy types, surprise_player boolean).
    Returns ([], False) if no combat.
    """
    pattern = r'\[COMBAT:\s*([^\]]+)\]'
    match = re.search(pattern, dm_response, re.IGNORECASE)
    if match:
        content = match.group(1).strip().lower()
        
        # Check for SURPRISE modifier (pipe separator)
        surprise_player = False
        if '|' in content:
            parts = content.split('|')
            enemies_str = parts[0].strip()
            modifiers = parts[1].strip() if len(parts) > 1 else ''
            if 'surprise' in modifiers:
                surprise_player = True
        else:
            enemies_str = content
        
        # Split enemies by comma and clean up
        enemies = [e.strip() for e in enemies_str.split(',')]
        enemies = [e for e in enemies if e]  # Remove empty strings
        return (enemies, surprise_player)
    return ([], False)


def parse_item_rewards(dm_response: str) -> list:
    """Parse [ITEM: item_name] tags from DM response."""
    pattern = r'\[ITEM:\s*([^\]]+)\]'
    matches = re.findall(pattern, dm_response, re.IGNORECASE)
    return [m.strip() for m in matches]


def parse_gold_rewards(dm_response: str) -> int:
    """Parse [GOLD: amount] tags from DM response."""
    pattern = r'\[GOLD:\s*(\d+)\]'
    matches = re.findall(pattern, dm_response, re.IGNORECASE)
    return sum(int(m) for m in matches)


def parse_xp_rewards(dm_response: str) -> list:
    """
    Parse [XP: amount] or [XP: amount | source] tags from DM response.
    Returns list of (amount, source) tuples.
    """
    # Pattern: [XP: 50] or [XP: 50 | Defeated the goblin boss]
    pattern = r'\[XP:\s*(\d+)(?:\s*\|\s*([^\]]+))?\]'
    matches = re.findall(pattern, dm_response, re.IGNORECASE)
    results = []
    for match in matches:
        amount = int(match[0])
        source = match[1].strip() if match[1] else "Milestone"
        results.append((amount, source))
    return results


# =============================================================================
# DM SYSTEM PROMPT
# =============================================================================

# Base system prompt that defines the AI as a Dungeon Master
DM_SYSTEM_PROMPT_BASE = """You are an experienced Dungeon Master running a classic D&D adventure.

Your responsibilities:
- Narrate the story in an engaging, immersive way
- Describe environments, NPCs, and events vividly
- Respond to player actions and decisions
- Keep the adventure exciting and fair
- Follow the scene context provided to guide the story
- Progress the story naturally based on player actions

## SKILL CHECK SYSTEM

When a situation requires a skill check, end your narration with this EXACT format:
[ROLL: SkillName DC X]

VALID FORMATS:
- [ROLL: Stealth DC 12]
- [ROLL: Perception DC 15]
- [ROLL: Investigation DC 10]
- [ROLL: Persuasion DC 14]
- [ROLL: Athletics DC 13]
- [ROLL: Acrobatics DC 12]
- [ROLL: Insight DC 11]
- [ROLL: Arcana DC 15]
- [ROLL: Intimidation DC 13]
- [ROLL: Deception DC 14]
- [ROLL: Survival DC 10]
- [ROLL: History DC 12]

IMPORTANT RULES:
- Only use the [ROLL: Skill DC X] format - nothing else
- Do NOT explain how to roll dice - the game system handles it automatically
- Do NOT add extra text inside the brackets
- Wait for the result before narrating what happens
- Use appropriate DCs: Easy=10, Medium=13, Hard=15, Very Hard=18, Nearly Impossible=20+

When you receive a [ROLL RESULT: ...]:
- SUCCESS: Describe the positive outcome naturally
- FAILURE: Describe the negative consequence - be honest about failures
- CRITICAL SUCCESS (NATURAL 20): Make it LEGENDARY! The player achieves something beyond what 
  they hoped for. Describe an extraordinary, memorable moment - perhaps they discover a hidden 
  secret, impress everyone watching, or accomplish the task with incredible flair.
- CRITICAL FAILURE (NATURAL 1): Make it SPECTACULAR... spectacularly bad! Create a dramatic 
  or comedic disaster - equipment breaks, they fall on their face, make a fool of themselves, 
  or cause an unexpected complication. Keep it fun and memorable, not punishing.

## COMBAT SYSTEM

When combat should begin (player attacks, enemy ambush, etc.), trigger it with:
[COMBAT: enemy_type] for single enemy
[COMBAT: enemy1, enemy2] for multiple enemies
[COMBAT: enemy1, enemy2 | SURPRISE] for when player ambushes enemies

Available enemies: goblin, goblin_boss, skeleton, orc, bandit, wolf

Examples:
- Player attacks a goblin: [COMBAT: goblin]
- Two goblins ambush: [COMBAT: goblin, goblin]
- Mixed encounter: [COMBAT: goblin, orc]
- Ambushed by bandits: [COMBAT: bandit, bandit]
- Wolf pack: [COMBAT: wolf, wolf, wolf]
- Boss with minions: [COMBAT: goblin_boss, goblin, goblin]
- Player sneaks up on guards: [COMBAT: bandit, bandit | SURPRISE]
- Player ambushes wolves: [COMBAT: wolf, wolf | SURPRISE]

SURPRISE RULES:
- Add | SURPRISE when the PLAYER catches enemies off guard
- Player must have used stealth or caught enemies unaware
- Do NOT use SURPRISE when enemies ambush the player
- Surprised enemies cannot act in Round 1
- Player gets ADVANTAGE (roll 2d20, take higher) on first attack

COMBAT RULES:
- Match the number of enemies in [COMBAT] to your narration!
- If you describe 2 goblins, use [COMBAT: goblin, goblin]
- Only use [COMBAT: ...] to START combat
- The game system handles ALL dice rolling, damage, and mechanics
- You will receive combat results like [COMBAT RESULT: VICTORY] or [COMBAT RESULT: DEFEAT]
- After combat, narrate the aftermath based on the result
- Do NOT narrate attack rolls or damage yourself - wait for results

## ITEM & REWARD SYSTEM

When the player finds items or receives rewards, use these tags:
[ITEM: item_name] - Give an item to the player
[GOLD: amount] - Give gold to the player
[XP: amount] or [XP: amount | reason] - Award experience points

Available items: healing_potion, greater_healing_potion, antidote, rations, torch, rope, 
lockpicks, dagger, shortsword, longsword, greataxe, rapier, leather_armor, studded_leather,
chain_shirt, chain_mail, goblin_ear, mysterious_key, ancient_scroll

Examples:
- Player loots a chest: [ITEM: healing_potion] [GOLD: 15]
- Quest reward: [ITEM: longsword] [GOLD: 50] [XP: 50 | Quest Complete]
- Found in a drawer: [ITEM: torch]
- Defeated goblin: [XP: 25 | Defeated goblin]
- Solved puzzle: [XP: 50 | Clever solution]
- Boss fight victory: [XP: 100 | Defeated boss]

XP GUIDELINES:
- Minor milestone (defeat weak enemy, find clue): 25 XP
- Major milestone (solve puzzle, complete task, defeat enemy): 50 XP
- Boss encounter or major victory: 100 XP
- Complete adventure chapter: 150 XP
- Max level is 5, so be measured with XP rewards

ITEM RULES:
- Only use [ITEM: name] for rewards, found items, or quest rewards
- Gold amounts should be reasonable: small reward=5-15, medium=20-50, large=75-150
- The game system adds items to inventory automatically
- You'll see confirmation of what was added

Style guidelines:
- Use second person ("You enter the tavern...")
- Be descriptive but concise
- Create tension and mystery
- Encourage player creativity
- When transitioning between scenes, make it feel natural, not forced
"""


def create_client(character: Character = None, scenario_context: str = ""):
    """Configure and return the Gemini model with character and scenario context."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set.")
        print("Please add it to your .env file: GOOGLE_API_KEY=your-api-key-here")
        exit(1)
    
    genai.configure(api_key=api_key)
    
    # Get model name from env or use default
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    
    # Build system prompt with character and scenario context
    system_prompt = DM_SYSTEM_PROMPT_BASE
    if character:
        system_prompt += "\n" + character.get_context_for_dm()
    if scenario_context:
        system_prompt += "\n" + scenario_context
    
    # Create the model with system instruction
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt
    )
    
    return model


def get_dm_response(chat, player_input, scenario_context: str = "", stream=True):
    """Get a response from the AI Dungeon Master.
    
    Args:
        chat: The chat session
        player_input: What the player said/did
        scenario_context: Current scene context to inject
        stream: If True, yields chunks for streaming. If False, returns full text.
    """
    # Prepend scenario context to the message if provided
    if scenario_context:
        full_input = f"[SCENE CONTEXT: {scenario_context}]\n\nPlayer action: {player_input}"
    else:
        full_input = player_input
    
    try:
        if stream:
            response = chat.send_message(full_input, stream=True)
            full_response = ""
            for chunk in response:
                if chunk.text:
                    print(chunk.text, end="", flush=True)
                    full_response += chunk.text
            print()  # Final newline after streaming
            return full_response
        else:
            response = chat.send_message(player_input)
            return response.text
    except Exception as e:
        return f"[DM Error: {str(e)}]"


def show_help(scenario_active: bool = False):
    """Display available commands."""
    help_text = """
╔══════════════════════════════════════════════════════════╗
║                     COMMANDS                             ║
╠══════════════════════════════════════════════════════════╣
║  stats, character, sheet  - View your character sheet    ║
║  hp                       - Quick HP check               ║
║  xp, level                - View XP progress             ║
║  levelup                  - Level up (when ready)        ║
║  inventory, inv, i        - View your inventory          ║
║  use <item>               - Use a consumable item        ║
║  equip <item>             - Equip a weapon or armor      ║
║  inspect <item>           - View item details            ║
╠══════════════════════════════════════════════════════════╣
║  💾 SAVE & LOAD                                          ║
║  save                     - Save game to file            ║
║  load                     - Load a saved game            ║
║  saves                    - List all saved games         ║"""
    
    if scenario_active:
        help_text += """
║  progress                 - Show scenario progress       ║"""
    
    help_text += """
║  help, ?                  - Show this help               ║
║  quit, exit, q            - Exit the game                ║
╠══════════════════════════════════════════════════════════╣
║  🎲 SKILL CHECKS & COMBAT                                ║
║  The DM will automatically request rolls when needed.    ║
║  Combat triggers when you fight enemies!                 ║
║  Combat commands: attack, defend, flee, status           ║
╠══════════════════════════════════════════════════════════╣
║  Any other text sends your action to the Dungeon Master  ║
╚══════════════════════════════════════════════════════════╝
"""
    print(help_text)


# =============================================================================
# COMBAT INTEGRATION
# =============================================================================

def show_combat_status(character: Character, enemies: list, round_num: int = 1):
    """Display detailed combat status panel for multi-enemy combat."""
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
    
    # Get weapon info
    weapon_name = getattr(character, 'weapon', 'longsword').title()
    weapon_data = WEAPONS.get(getattr(character, 'weapon', 'longsword'), {})
    weapon_damage = weapon_data.get('damage', '1d8')
    
    print()
    print("╔" + "═" * 60 + "╗")
    print(f"║  🗡️ COMBAT STATUS - Round {round_num}".ljust(61) + "║")
    print("╠" + "═" * 60 + "╣")
    print(f"║  YOU: {character.name} ({character.char_class})".ljust(61) + "║")
    print(f"║  {hp_color} {hp_bar} {character.current_hp}/{character.max_hp} HP  |  AC: {character.armor_class}  |  {weapon_name} ({weapon_damage})".ljust(61) + "║")
    print("╠" + "═" * 60 + "╣")
    
    # Show all enemies
    alive_enemies = [e for e in enemies if not e.is_dead]
    for i, enemy in enumerate(enemies, 1):
        # Enemy HP bar
        if enemy.is_dead:
            status_line = f"║  [{i}] 💀 {enemy.name} (DEFEATED)".ljust(61) + "║"
        else:
            enemy_hp_percent = enemy.current_hp / enemy.max_hp
            enemy_hp_filled = int(enemy_hp_percent * 10)
            enemy_hp_bar = "█" * enemy_hp_filled + "░" * (10 - enemy_hp_filled)
            
            enemy_damage = enemy.damage_dice
            if enemy.damage_bonus:
                enemy_damage += f"+{enemy.damage_bonus}"
            
            status_line = f"║  [{i}] ⚔️ {enemy.name}: {enemy_hp_bar} {enemy.current_hp}/{enemy.max_hp} HP | AC: {enemy.armor_class}".ljust(61) + "║"
        print(status_line)
    
    print("╚" + "═" * 60 + "╝")


def run_combat(character: Character, enemy_types: list, chat, surprise_player: bool = False) -> str:
    """Run a multi-enemy combat encounter and return the result.
    
    Args:
        character: Player character
        enemy_types: List of enemy type strings (e.g., ['goblin', 'goblin'])
        chat: The chat session for DM responses
        surprise_player: If True, player has surprised enemies (enemies skip round 1,
                         player gets advantage on first attack)
    
    Returns: 'victory', 'defeat', or 'fled'
    """
    # Handle backwards compatibility - single enemy as string
    if isinstance(enemy_types, str):
        enemy_types = [enemy_types]
    
    # Create enemies
    enemies = []
    # Count how many of each type we need
    type_counts = {}
    for etype in enemy_types:
        type_counts[etype] = type_counts.get(etype, 0) + 1
    
    # Track current index for each type
    type_indices = {}
    
    for i, etype in enumerate(enemy_types):
        enemy = create_enemy(etype)
        if not enemy:
            print(f"(Unknown enemy type: {etype}, defaulting to goblin)")
            enemy = create_enemy('goblin')
            etype = 'goblin'
        
        # Add number suffix if multiple of same type
        if type_counts.get(etype, 1) > 1:
            type_indices[etype] = type_indices.get(etype, 0) + 1
            enemy.name = f"{enemy.name} {type_indices[etype]}"
        
        enemies.append(enemy)
    
    print("\n" + "=" * 60)
    print("              ⚔️ COMBAT BEGINS! ⚔️")
    print("=" * 60)
    
    if len(enemies) == 1:
        print(f"\nYou face a {enemies[0].name}!")
        print(f"HP: {enemies[0].current_hp}/{enemies[0].max_hp}, AC: {enemies[0].armor_class}")
    else:
        print(f"\nYou face {len(enemies)} enemies!")
        for i, enemy in enumerate(enemies, 1):
            print(f"  [{i}] {enemy.name} - HP: {enemy.current_hp}/{enemy.max_hp}, AC: {enemy.armor_class}")
    
    # Surprise announcement
    if surprise_player:
        print("\n⚡ SURPRISE! You have caught the enemies off guard!")
        print("   Enemies are surprised and cannot act in Round 1.")
        print("   You have ADVANTAGE on your first attack (roll 2d20, take higher).")
    
    # Roll initiative for everyone
    print("\n" + "-" * 40)
    input("Press Enter to roll initiative...")
    
    # Player initiative
    player_init = roll_initiative(character.get_ability_modifier('dexterity'))
    print(f"\n{format_initiative_roll(character.name, player_init)}")
    player_init_val = player_init['total']
    
    # Enemy initiatives
    for enemy in enemies:
        init = roll_initiative(enemy.dex_modifier)
        enemy.initiative = init['total']
        print(format_initiative_roll(enemy.name, init))
    
    # Build turn order (higher goes first, player wins ties)
    all_combatants = [('player', player_init_val, character)] + \
                     [('enemy', e.initiative, e) for e in enemies]
    all_combatants.sort(key=lambda x: (x[1], 0 if x[0] == 'player' else -1), reverse=True)
    
    print(f"\n📋 Turn Order:")
    for ctype, init_val, combatant in all_combatants:
        name = character.name if ctype == 'player' else combatant.name
        surprised_mark = " (SURPRISED)" if ctype == 'enemy' and surprise_player else ""
        print(f"   {init_val}: {name}{surprised_mark}")
    
    print("\n" + "-" * 60)
    if len(enemies) > 1:
        print("Combat commands: 'attack <#>', 'defend', 'flee', 'status'")
        print("Example: 'attack 1' to attack enemy #1")
    else:
        print("Combat commands: 'attack', 'defend', 'flee', 'status'")
    print("-" * 60)
    
    # Get weapon (default to longsword if not set)
    weapon = getattr(character, 'weapon', 'longsword')
    
    # =========================================================================
    # PROPER TURN-BASED COMBAT LOOP
    # Each combatant takes their turn in initiative order
    # =========================================================================
    
    round_num = 1
    result = None
    player_is_defending = False  # Track if player is defending
    player_has_advantage = surprise_player  # Track if player still has advantage from surprise
    
    while result is None:
        print(f"\n{'='*60}")
        print(f"                    ROUND {round_num}")
        print(f"{'='*60}")
        
        # Process each turn in initiative order
        for ctype, init_val, combatant in all_combatants:
            # Check win/lose conditions
            alive_enemies = [e for e in enemies if not e.is_dead]
            
            if not alive_enemies:
                print("\n🎉 Victory! All enemies defeated!")
                result = 'victory'
                break
            
            if character.current_hp <= 0:
                print("\n💀 You have fallen...")
                result = 'defeat'
                break
            
            # === PLAYER'S TURN ===
            if ctype == 'player':
                # Reset defend at start of player's turn
                player_is_defending = False
                
                show_combat_status(character, enemies, round_num)
                print(f"\n   🎯 {character.name}'s turn (Initiative: {init_val})")
                
                if len(alive_enemies) > 1:
                    print(f"   Target with 'attack 1', 'attack 2', etc. or just type a number.")
                
                # Player action loop (retry on invalid input)
                player_acted = False
                while not player_acted:
                    action = input("\n⚔️ Combat action: ").strip().lower()
                    
                    if action == 'status':
                        show_combat_status(character, enemies, round_num)
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
                            attack = roll_attack_with_advantage(character, target_enemy.armor_class, weapon)
                            player_has_advantage = False  # Consume advantage after first attack
                        else:
                            attack = roll_attack(character, target_enemy.armor_class, weapon)
                        print(f"\n{format_attack_result(attack)}")
                        
                        if attack['is_crit']:
                            damage = roll_damage(character, weapon, True)
                            print(format_damage_result(damage))
                            target_enemy.take_damage(damage['total'])
                        elif attack['hit']:
                            damage = roll_damage(character, weapon, False)
                            print(format_damage_result(damage))
                            target_enemy.take_damage(damage['total'])
                        
                        player_acted = True
                        
                    elif is_defend:
                        print("\n🛡️ You take a defensive stance! (+2 AC until your next turn)")
                        player_is_defending = True
                        player_acted = True
                        
                    elif is_flee:
                        print("\n🏃 You attempt to flee!")
                        input("   Press Enter to roll escape check...")
                        
                        max_dex = max(e.dex_modifier for e in alive_enemies)
                        flee_dc = 10 + max_dex
                        flee_roll = random.randint(1, 20)
                        flee_mod = character.get_ability_modifier('dexterity')
                        flee_total = flee_roll + flee_mod
                        mod_sign = '+' if flee_mod >= 0 else ''
                        
                        if flee_total >= flee_dc:
                            print(f"\n🎯 Escape: [{flee_roll}]{mod_sign}{flee_mod} = {flee_total} vs DC {flee_dc} = ✅ ESCAPED!")
                            print("\n🏃 You successfully fled the battle!")
                            result = 'fled'
                            break
                        else:
                            print(f"\n🎯 Escape: [{flee_roll}]{mod_sign}{flee_mod} = {flee_total} vs DC {flee_dc} = ❌ FAILED!")
                            # Opportunity attacks from all enemies
                            for opp_enemy in alive_enemies:
                                print(f"\n   {opp_enemy.name} gets an opportunity attack!")
                                input("   Press Enter...")
                                enemy_atk, enemy_dmg = enemy_attack(opp_enemy, character.armor_class)
                                print(f"\n{format_enemy_attack(enemy_atk, enemy_dmg)}")
                                if enemy_dmg:
                                    character.take_damage(enemy_dmg['total'])
                                if character.current_hp <= 0:
                                    break
                            player_acted = True
                    else:
                        print(f"\n❓ Unknown action: '{action}'")
                        if len(alive_enemies) > 1:
                            print("   Valid: attack <#>, defend, flee, status")
                        else:
                            print("   Valid: attack, defend, flee, status")
                
                # Check if flee succeeded (result set inside flee block)
                if result == 'fled':
                    break
            
            # === ENEMY'S TURN ===
            else:
                enemy = combatant
                if not enemy.is_dead:
                    # Surprise: enemies skip their turn in round 1
                    if surprise_player and round_num == 1:
                        print(f"\n   😵 {enemy.name} is SURPRISED and loses their turn!")
                        continue
                    
                    print(f"\n   ⚔️ {enemy.name}'s turn (Initiative: {init_val})")
                    input("   Press Enter...")
                    
                    # Apply defend bonus if player is defending
                    effective_ac = character.armor_class + (2 if player_is_defending else 0)
                    
                    enemy_atk, enemy_dmg = enemy_attack(enemy, effective_ac)
                    print(f"\n{format_enemy_attack(enemy_atk, enemy_dmg)}")
                    
                    if enemy_dmg:
                        character.take_damage(enemy_dmg['total'])
        
        # End of round
        round_num += 1
    
    print("\n" + "=" * 60)
    print("              COMBAT ENDED")
    print("=" * 60)
    
    return result


def select_scenario(scenario_manager: ScenarioManager) -> None:
    """Let player select a scenario to play."""
    scenarios = scenario_manager.list_available()
    
    print("\n" + "=" * 60)
    print("              📜 AVAILABLE ADVENTURES 📜")
    print("=" * 60)
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n  [{i}] {scenario['name']}")
        print(f"      {scenario['description']}")
        print(f"      ⏱️  Estimated: {scenario['duration']}")
    
    print(f"\n  [0] Free Play (no structured scenario)")
    
    while True:
        choice = input("\nSelect adventure (number): ").strip()
        if choice == "0":
            return None
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(scenarios):
                return scenarios[idx]["id"]
        except ValueError:
            pass
        print("Invalid choice. Please enter a number.")


def main():
    """Main game loop."""
    print("=" * 60)
    print("       AI D&D TEXT RPG - Dungeon Master Edition")
    print("=" * 60)
    
    # Check for saved games
    save_manager = SaveManager()
    saves, _ = save_manager.list_saves()  # Returns (saves, errors) tuple
    
    # Character creation / loading
    print("\nWelcome, adventurer!")
    print("\n[1] Create character (choose race, class, roll stats)")
    print("[2] Quick start (random character)")
    if saves:
        print(f"[3] Load saved game ({len(saves)} save(s) found)")
    
    choice = input("\nYour choice: ").strip()
    
    character = None
    scenario_manager = ScenarioManager()
    loaded_game = False
    
    if choice == "3" and saves:
        # Load game
        print(f"\n{format_saves_list(saves)}")
        print("  [0] Back to menu")
        
        load_choice = input("\nSelect save to load: ").strip()
        if load_choice != "0" and load_choice:
            try:
                idx = int(load_choice) - 1
                if 0 <= idx < len(saves):
                    result = save_manager.load_game(
                        saves[idx]['filepath'],
                        Character,
                        ScenarioManager
                    )
                    if result and result['character']:
                        character = result['character']
                        if result['scenario_manager']:
                            scenario_manager = result['scenario_manager']
                        loaded_game = True
                        print(f"\n  ✅ Game loaded: {character.name}")
                        print(character.get_stat_block())
            except (ValueError, IndexError):
                print("  ❌ Invalid selection.")
    
    if not character:
        if choice == "1":
            character = create_character_interactive()
        else:
            print("\nWhat is your character's name?")
            name = input("Name: ").strip() or "Hero"
            character = Character.create_random(name)
            print("\n✨ Character created!")
            print(character.get_stat_block())
    
    # Scenario selection (skip if loading a saved game with scenario)
    scenario_context = ""
    if not loaded_game or not scenario_manager.is_active():
        scenario_id = select_scenario(scenario_manager)
        
        if scenario_id:
            first_scene = scenario_manager.start_scenario(scenario_id)
            scenario = scenario_manager.active_scenario
            print(f"\n🏰 Starting: {scenario.name}")
            print(f"   \"{scenario.hook}\"")
            scenario_context = scenario_manager.get_dm_context()
    else:
        # Get context from loaded scenario
        scenario_context = scenario_manager.get_dm_context() if scenario_manager.is_active() else ""
        if scenario_manager.is_active():
            print(f"\n📍 Resuming scenario: {scenario_manager.active_scenario.name}")
    
    input("\nPress Enter to begin your adventure...")
    
    # Initialize the model with character context
    print("\nInitializing AI Dungeon Master...")
    model = create_client(character, scenario_context)
    
    # Start a chat session
    chat = model.start_chat(history=[])
    
    # Get the opening narration from the DM
    print("\n" + "-" * 60)
    
    if scenario_id and scenario_manager.active_scenario:
        scene = scenario_manager.active_scenario.get_current_scene()
        opening_prompt = f"""
Begin the adventure for {character.name}, a {character.race} {character.char_class}.
We are starting in: {scene.name}
Setting: {scene.setting}

Set the scene according to the DM instructions. Introduce the scenario hook naturally.
"""
        print(f"\n📍 {scene.name}")
        print("-" * 40)
    else:
        opening_prompt = f"Begin the adventure. Welcome {character.name}, a {character.race} {character.char_class}, and set the scene for their adventure. Make it appropriate for their class and race."
    
    print("\n🎲 Dungeon Master:")
    get_dm_response(chat, opening_prompt, scenario_context)
    
    print("\n" + "-" * 60)
    print("Commands: 'stats' for character, 'progress' for story, 'help' for more")
    print("-" * 60)
    
    # Main game loop
    while True:
        # Get player input
        print()
        player_input = input("⚔️  Your action: ").strip()
        
        # Check for exit commands
        if player_input.lower() in ["quit", "exit", "q"]:
            print(f"\n🎲 Dungeon Master: And so, {character.name}'s adventure ends here... for now.")
            print("Thanks for playing! See you next time, adventurer.")
            break
        
        # Check for stats command
        if player_input.lower() in ["stats", "character", "sheet", "char"]:
            print(character.get_stat_block())
            continue
        
        # =====================================================================
        # SAVE/LOAD SYSTEM COMMANDS
        # =====================================================================
        
        # Save game command
        if player_input.lower() in ["save", "savegame", "save game"]:
            save_manager = SaveManager()
            print("\n💾 SAVE GAME")
            print("-" * 40)
            print("  [1] Quick Save (Slot 1)")
            print("  [2] Save Slot 2")
            print("  [3] Save Slot 3")
            print("  [0] Cancel")
            
            slot_choice = input("\nSelect slot: ").strip()
            if slot_choice in ["1", "2", "3"]:
                slot = int(slot_choice)
                desc = input("Description (optional): ").strip() or f"Slot {slot} save"
                filepath, message = save_manager.save_game(
                    character,
                    scenario_manager,
                    chat_history=None,  # Could add chat history tracking later
                    slot=slot,
                    description=desc
                )
                if filepath:
                    print(f"\n  ✅ {message}")
                else:
                    print(f"\n  ❌ {message}")
            else:
                print("  Save cancelled.")
            continue
        
        # Load game command
        if player_input.lower() in ["load", "loadgame", "load game"]:
            save_manager = SaveManager()
            saves, errors = save_manager.list_saves()
            
            if not saves:
                print("\n  ❌ No saved games found.")
                if errors:
                    for e in errors:
                        print(f"    {e}")
                continue
            
            print(f"\n{format_saves_list(saves, errors)}")
            print("  [0] Cancel")
            
            load_choice = input("\nSelect save to load: ").strip()
            if load_choice == "0" or not load_choice:
                print("  Load cancelled.")
                continue
            
            try:
                idx = int(load_choice) - 1
                if 0 <= idx < len(saves):
                    print("\n⚠️  Loading will replace your current game!")
                    confirm = input("Continue? (y/n): ").strip().lower()
                    if confirm == 'y':
                        result = save_manager.load_game(
                            saves[idx]['filepath'],
                            Character,
                            ScenarioManager
                        )
                        if result and result['character']:
                            character = result['character']
                            if result['scenario_manager']:
                                scenario_manager = result['scenario_manager']
                            print(f"\n  ✅ Game loaded: {character.name}")
                            print(character.get_stat_block())
                            
                            # Re-initialize chat with loaded character
                            scenario_context = scenario_manager.get_dm_context() if scenario_manager.is_active() else ""
                            model = create_client(character, scenario_context)
                            chat = model.start_chat(history=[])
                            print("\n🎲 Dungeon Master: Welcome back to your adventure!")
                        else:
                            print("\n  ❌ Failed to load game.")
                    else:
                        print("  Load cancelled.")
                else:
                    print("  ❌ Invalid selection.")
            except ValueError:
                print("  ❌ Invalid selection.")
            continue
        
        # List saves command
        if player_input.lower() in ["saves", "list saves", "listsaves"]:
            save_manager = SaveManager()
            saves, errors = save_manager.list_saves()
            print(f"\n{format_saves_list(saves, errors)}")
            continue
        
        # =====================================================================
        # END SAVE/LOAD COMMANDS
        # =====================================================================
        
        # Check for HP command
        if player_input.lower() == "hp":
            hp_bar = character._get_hp_bar()
            print(f"\n  ❤️  HP: {character.current_hp}/{character.max_hp} {hp_bar}")
            continue
        
        # Check for XP/Level command
        if player_input.lower() in ["xp", "level", "exp", "experience"]:
            progress, needed = character.xp_progress()
            xp_bar_filled = int((progress / needed) * 10) if needed > 0 else 10
            xp_bar = "█" * xp_bar_filled + "░" * (10 - xp_bar_filled)
            print(f"\n  ⭐ Level {character.level} ({character.char_class})")
            print(f"  📊 XP: {character.experience} total")
            if character.level < 5:
                print(f"  📈 Progress: {xp_bar} {progress}/{needed} to Level {character.level + 1}")
            else:
                print(f"  🏆 MAX LEVEL REACHED!")
            if character.can_level_up():
                print(f"\n  🎉 Ready to level up! Type 'levelup' to advance.")
            continue
        
        # Check for level up command
        if player_input.lower() in ["levelup", "level up", "lvlup"]:
            if not character.can_level_up():
                if character.level >= 5:
                    print(f"\n  🏆 You are already at max level (5)!")
                else:
                    xp_needed = character.xp_to_next_level()
                    print(f"\n  ❌ Not enough XP. Need {xp_needed} more XP to reach Level {character.level + 1}.")
                continue
            
            # Perform level up
            result = character.level_up()
            print(f"\n{'='*50}")
            print(f"  🎉 LEVEL UP! Level {result['old_level']} → Level {result['new_level']}!")
            print(f"{'='*50}")
            print(f"  ❤️  +{result['hp_gain']} HP (now {result['new_max_hp']} max)")
            if result['benefits']:
                print(f"\n  ✨ Benefits:")
                for benefit in result['benefits']:
                    print(f"     • {benefit}")
            print(f"\n  Proficiency Bonus: +{character.get_proficiency_bonus()}")
            print(f"{'='*50}")
            continue
        
        # Check for progress command
        if player_input.lower() == "progress":
            if scenario_manager.is_active():
                print(f"\n  📍 {scenario_manager.get_progress()}")
            else:
                print("\n  (No structured scenario active - Free Play mode)")
            continue
        
        # Check for inventory command
        if player_input.lower() in ["inventory", "inv", "i", "items", "bag"]:
            print(format_inventory(character.inventory, character.gold))
            continue
        
        # Check for use item command
        if player_input.lower().startswith("use "):
            item_name = player_input[4:].strip()
            item = find_item_in_inventory(character.inventory, item_name)
            if not item:
                print(f"\n  ❌ You don't have '{item_name}' in your inventory.")
            elif item.item_type != ItemType.CONSUMABLE:
                print(f"\n  ❌ You can't use {item.name} like that. Try 'equip' for weapons/armor.")
            else:
                success, msg = use_item(item, character)
                if success:
                    remove_item_from_inventory(character.inventory, item_name)
                print(f"\n  {msg}")
            continue
        
        # Check for equip command
        if player_input.lower().startswith("equip "):
            item_name = player_input[6:].strip()
            item = find_item_in_inventory(character.inventory, item_name)
            if not item:
                print(f"\n  ❌ You don't have '{item_name}' in your inventory.")
            elif item.item_type == ItemType.WEAPON:
                character.weapon = item.name.lower()
                print(f"\n  ⚔️ Equipped {item.name} as your weapon!")
                if item.damage_dice:
                    print(f"     Damage: {item.damage_dice}")
            elif item.item_type == ItemType.ARMOR:
                # Unequip old armor bonus first
                if character.equipped_armor:
                    old_armor = get_item(character.equipped_armor)
                    if old_armor and old_armor.ac_bonus:
                        character.armor_class -= old_armor.ac_bonus
                # Equip new armor
                character.equipped_armor = item.name.lower()
                if item.ac_bonus:
                    character.armor_class += item.ac_bonus
                print(f"\n  🛡️ Equipped {item.name}!")
                print(f"     AC is now: {character.armor_class}")
            else:
                print(f"\n  ❌ You can't equip {item.name}.")
            continue
        
        # Check for inspect/examine item command
        if player_input.lower().startswith(("inspect ", "examine ", "look at ")):
            # Extract item name
            for prefix in ["inspect ", "examine ", "look at "]:
                if player_input.lower().startswith(prefix):
                    item_name = player_input[len(prefix):].strip()
                    break
            item = find_item_in_inventory(character.inventory, item_name)
            if not item:
                # Not an item - let DM handle it
                pass
            else:
                print(f"\n{format_item_details(item)}")
                continue
        
        # Check for help command
        if player_input.lower() in ["help", "?"]:
            show_help(scenario_manager.is_active())
            continue
        
        # Skip empty input
        if not player_input:
            print("(Please enter an action or 'quit' to exit)")
            continue
        
        # Get current scenario context
        current_context = scenario_manager.get_dm_context() if scenario_manager.is_active() else ""
        
        # Record the exchange
        if scenario_manager.is_active():
            scenario_manager.record_exchange()
        
        # Get DM response (streaming handles printing)
        print("\n🎲 Dungeon Master:")
        response = get_dm_response(chat, player_input, current_context)
        
        # Check if DM requested a skill check
        skill, dc = parse_roll_request(response)
        while skill and dc:
            print(f"\n📋 DM requests: {skill.title()} check (DC {dc})")
            input("   Press Enter to roll...")
            
            # Perform the roll
            result = roll_skill_check(character, skill, dc)
            print(f"\n{format_roll_result(result)}")
            
            # Build result message for DM with enhanced critical context
            if result['is_nat_20']:
                # Critical success - give AI explicit guidance
                result_msg = (
                    f"[ROLL RESULT: {result['skill']} = {result['total']} vs DC {dc} = "
                    f"CRITICAL SUCCESS - NATURAL 20! "
                    f"Narrate something EXTRAORDINARY happening - the player succeeds in a spectacular, "
                    f"memorable way that exceeds their wildest expectations!]"
                )
            elif result['is_nat_1']:
                # Critical failure - give AI explicit guidance
                result_msg = (
                    f"[ROLL RESULT: {result['skill']} = {result['total']} vs DC {dc} = "
                    f"CRITICAL FAILURE - NATURAL 1! "
                    f"Narrate a DISASTROUS or COMEDIC failure - something goes hilariously or dramatically wrong, "
                    f"creating an entertaining or tense moment!]"
                )
            else:
                # Normal success or failure
                result_msg = (
                    f"[ROLL RESULT: {result['skill']} = {result['total']} vs DC {dc} = "
                    f"{'SUCCESS' if result['success'] else 'FAILURE'}]"
                )
            
            # Get DM's reaction to the roll
            print(f"\n🎲 Dungeon Master:")
            response = get_dm_response(chat, result_msg, current_context)
            
            # Check if another roll is needed
            skill, dc = parse_roll_request(response)
        
        # Check if DM triggered combat
        enemy_types, surprise_player = parse_combat_request(response)
        if enemy_types:
            # Run combat encounter (now supports multiple enemies and surprise)
            combat_result = run_combat(character, enemy_types, chat, surprise_player=surprise_player)
            
            # Handle combat aftermath
            if combat_result == 'victory':
                # Generate loot from all defeated enemies
                loot_lines = []
                total_gold = 0
                
                for enemy_type in enemy_types:
                    loot = generate_loot(enemy_type)
                    gold_drop = gold_from_enemy(enemy_type)
                    
                    # Add loot to inventory
                    for item in loot:
                        msg = add_item_to_inventory(character.inventory, item)
                        loot_lines.append(f"  📦 {msg}")
                    
                    total_gold += gold_drop
                
                if total_gold > 0:
                    character.gold += total_gold
                    loot_lines.append(f"  💰 Found {total_gold} gold!")
                
                if loot_lines:
                    print("\n✨ LOOT:")
                    for line in loot_lines:
                        print(line)
                
                enemy_count = len(enemy_types)
                if enemy_count == 1:
                    result_msg = f"[COMBAT RESULT: VICTORY - {character.name} defeated the enemy! HP remaining: {character.current_hp}/{character.max_hp}]"
                else:
                    result_msg = f"[COMBAT RESULT: VICTORY - {character.name} defeated all {enemy_count} enemies! HP remaining: {character.current_hp}/{character.max_hp}]"
                
            elif combat_result == 'defeat':
                result_msg = f"[COMBAT RESULT: DEFEAT - {character.name} was defeated in battle!]"
                print("\n🎲 Dungeon Master:")
                get_dm_response(chat, result_msg, current_context)
                print("\n💀 GAME OVER")
                print("Thanks for playing! Better luck next time, adventurer.")
                break
            else:  # fled
                result_msg = f"[COMBAT RESULT: ESCAPED - {character.name} fled the battle! HP remaining: {character.current_hp}/{character.max_hp}]"
            
            # Get DM's narration of combat aftermath (unless defeated)
            if combat_result != 'defeat':
                print("\n🎲 Dungeon Master:")
                response = get_dm_response(chat, result_msg, current_context)
        
        # Check for item/gold/XP rewards from DM
        if response:
            items_given = parse_item_rewards(response)
            gold_given = parse_gold_rewards(response)
            xp_given = parse_xp_rewards(response)
            
            reward_lines = []
            for item_name in items_given:
                item = get_item(item_name)
                if item:
                    msg = add_item_to_inventory(character.inventory, item)
                    reward_lines.append(f"  📦 {msg}")
            
            if gold_given > 0:
                character.gold += gold_given
                reward_lines.append(f"  💰 Received {gold_given} gold!")
            
            # Process XP rewards
            for xp_amount, xp_source in xp_given:
                xp_result = character.gain_xp(xp_amount, xp_source)
                reward_lines.append(f"  ⭐ +{xp_amount} XP ({xp_source})")
                
                # Check for level up
                if xp_result['level_up']:
                    reward_lines.append(f"\n  🎉 LEVEL UP AVAILABLE!")
                    reward_lines.append(f"     Type 'levelup' to level up to Level {xp_result['new_level']}!")
            
            if reward_lines:
                print("\n✨ REWARDS:")
                for line in reward_lines:
                    print(line)
        
        # Check for scene transitions
        if scenario_manager.is_active() and response:
            transition = scenario_manager.check_transition(player_input, response)
            if transition:
                print(transition)
                
                # Check if scenario is complete
                if scenario_manager.active_scenario.is_complete:
                    print("\n🎉 Congratulations! You've completed this adventure!")
                    print("Thanks for playing! See you next time, adventurer.")
                    break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚔️  Game interrupted. Your adventure awaits another day!")
        print("Thanks for playing!")
    except EOFError:
        print("\n\n⚔️  Input stream closed. Exiting game.")
        print("Thanks for playing!")
