"""
AI D&D Text RPG - Core Game (Phase 2)
A D&D adventure where AI acts as Dungeon Master.
Now with integrated skill checks and dice rolling!
"""

import os
import re
import random
from dotenv import load_dotenv
import google.generativeai as genai
from character import Character, create_character_interactive, CLASSES, RACES
from scenario import ScenarioManager

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
- NATURAL 20: Make it EPIC! Something amazing happens
- NATURAL 1: Make it DISASTROUS! A dramatic or comedic failure

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
║  hp                       - Quick HP check               ║"""
    
    if scenario_active:
        help_text += """
║  progress                 - Show scenario progress       ║"""
    
    help_text += """
║  help, ?                  - Show this help               ║
║  quit, exit, q            - Exit the game                ║
╠══════════════════════════════════════════════════════════╣
║  🎲 SKILL CHECKS                                         ║
║  The DM will automatically request rolls when needed.    ║
║  Press Enter when prompted to roll your dice!            ║
╠══════════════════════════════════════════════════════════╣
║  Any other text sends your action to the Dungeon Master  ║
╚══════════════════════════════════════════════════════════╝
"""
    print(help_text)


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
    
    # Character creation
    print("\nWelcome, adventurer! Let's create your character.")
    print("\n[1] Create character (choose race, class, roll stats)")
    print("[2] Quick start (random character)")
    
    choice = input("\nYour choice (1/2): ").strip()
    
    if choice == "1":
        character = create_character_interactive()
    else:
        print("\nWhat is your character's name?")
        name = input("Name: ").strip() or "Hero"
        character = Character.create_random(name)
        print("\n✨ Character created!")
        print(character.get_stat_block())
    
    # Scenario selection
    scenario_manager = ScenarioManager()
    scenario_id = select_scenario(scenario_manager)
    
    scenario_context = ""
    if scenario_id:
        first_scene = scenario_manager.start_scenario(scenario_id)
        scenario = scenario_manager.active_scenario
        print(f"\n🏰 Starting: {scenario.name}")
        print(f"   \"{scenario.hook}\"")
        scenario_context = scenario_manager.get_dm_context()
    
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
        
        # Check for HP command
        if player_input.lower() == "hp":
            hp_bar = character._get_hp_bar()
            print(f"\n  ❤️  HP: {character.current_hp}/{character.max_hp} {hp_bar}")
            continue
        
        # Check for progress command
        if player_input.lower() == "progress":
            if scenario_manager.is_active():
                print(f"\n  📍 {scenario_manager.get_progress()}")
            else:
                print("\n  (No structured scenario active - Free Play mode)")
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
            
            # Build result message for DM
            result_msg = (
                f"[ROLL RESULT: {result['skill']} = {result['total']} vs DC {dc} = "
                f"{'SUCCESS' if result['success'] else 'FAILURE'}"
            )
            if result['is_nat_20']:
                result_msg += " (NATURAL 20!)"
            elif result['is_nat_1']:
                result_msg += " (NATURAL 1!)"
            result_msg += "]"
            
            # Get DM's reaction to the roll
            print(f"\n🎲 Dungeon Master:")
            response = get_dm_response(chat, result_msg, current_context)
            
            # Check if another roll is needed
            skill, dc = parse_roll_request(response)
        
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
