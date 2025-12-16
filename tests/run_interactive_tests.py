"""
Unified Interactive Test Runner for AI D&D RPG
Combines all test modules into a single menu-driven interface.

Run with: python tests/run_interactive_tests.py
"""

import os
import sys
import subprocess

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()


# =============================================================================
# MENU DISPLAY
# =============================================================================

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def show_main_menu():
    """Display the main menu."""
    print()
    print("╔" + "═" * 62 + "╗")
    print("║" + "🎮 AI D&D RPG - INTERACTIVE TEST SUITE 🎮".center(62) + "║")
    print("╠" + "═" * 62 + "╣")
    print("║" + "  UNIT TESTS (no AI required)".ljust(62) + "║")
    print("║" + "    1. Combat System Tests (31 tests)".ljust(62) + "║")
    print("║" + "    2. Location System Tests (80 tests)".ljust(62) + "║")
    print("║" + "    3. Inventory System Tests (35 tests)".ljust(62) + "║")
    print("║" + "    4. Scenario System Tests (26 tests)".ljust(62) + "║")
    print("║" + "    5. Run ALL Unit Tests (228 total)".ljust(62) + "║")
    print("╠" + "═" * 62 + "╣")
    print("║" + "  INTERACTIVE TESTS (with AI DM)".ljust(62) + "║")
    print("║" + "    6. Interactive Combat".ljust(62) + "║")
    print("║" + "    7. Interactive Dice/Skill Checks".ljust(62) + "║")
    print("║" + "    8. Interactive Inventory (Shop: Coming Soon)".ljust(62) + "║")
    print("║" + "    9. Interactive Location Exploration".ljust(62) + "║")
    print("║" + "   10. Full Adventure (all systems combined)".ljust(62) + "║")
    print("╠" + "═" * 62 + "╣")
    print("║" + "  NARRATION TESTS".ljust(62) + "║")
    print("║" + "   11. Combat Narration Tests".ljust(62) + "║")
    print("║" + "   12. Location with DM Unit Tests (8 tests)".ljust(62) + "║")
    print("╠" + "═" * 62 + "╣")
    print("║" + "    0. Exit".ljust(62) + "║")
    print("╚" + "═" * 62 + "╝")
    
    return input("\n  Choice: ").strip()


# =============================================================================
# UNIT TEST RUNNERS
# =============================================================================

def run_pytest_tests(test_file: str, description: str):
    """Run pytest tests for a specific file."""
    print(f"\n{'=' * 60}")
    print(f"  🧪 {description}")
    print("=" * 60)
    
    test_path = os.path.join(os.path.dirname(__file__), test_file)
    result = subprocess.run(
        ["python", "-m", "pytest", test_path, "-v", "--tb=short"],
        capture_output=False
    )
    
    return result.returncode == 0


def run_all_unit_tests():
    """Run all pytest unit tests."""
    print("\n" + "=" * 60)
    print("  🧪 RUNNING ALL UNIT TESTS")
    print("=" * 60)
    
    tests_dir = os.path.dirname(__file__)
    test_files = [
        "test_combat.py",
        "test_location.py",
        "test_inventory.py",
        "test_scenario.py",
        "test_character.py",
        "test_dice.py",
        "test_save_system.py",
    ]
    
    results = []
    for test_file in test_files:
        test_path = os.path.join(tests_dir, test_file)
        if os.path.exists(test_path):
            result = subprocess.run(
                ["python", "-m", "pytest", test_path, "-v", "--tb=short"],
                capture_output=False
            )
            results.append((test_file, result.returncode == 0))
    
    # Summary
    print("\n" + "=" * 60)
    print("  📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    failed = len(results) - passed
    
    for test_file, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {test_file}")
    
    print(f"\n  Total: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


# =============================================================================
# INTERACTIVE TEST RUNNERS
# =============================================================================

def run_interactive_combat():
    """Run interactive combat test."""
    print("\n" + "=" * 60)
    print("  ⚔️ LAUNCHING INTERACTIVE COMBAT TEST")
    print("=" * 60)
    
    try:
        import test_combat_with_dm
        test_combat_with_dm.main()
    except Exception as e:
        print(f"\n❌ Error: {e}")


def run_interactive_dice():
    """Run interactive dice/skill check test."""
    print("\n" + "=" * 60)
    print("  🎲 LAUNCHING INTERACTIVE DICE TEST")
    print("=" * 60)
    
    try:
        import test_dice_with_dm
        test_dice_with_dm.main()
    except Exception as e:
        print(f"\n❌ Error: {e}")


def run_interactive_inventory():
    """Run interactive inventory test. Shop is a test prototype only."""
    print("\n" + "=" * 60)
    print("  🎒 LAUNCHING INTERACTIVE INVENTORY TEST")
    print("  ⚠️  Note: Shop feature is a prototype (not in main game yet)")
    print("=" * 60)
    
    try:
        import test_inventory_with_dm
        test_inventory_with_dm.run_interactive_test()
    except Exception as e:
        print(f"\n❌ Error: {e}")


def run_interactive_location():
    """Run interactive location exploration test."""
    print("\n" + "=" * 60)
    print("  🗺️ LAUNCHING INTERACTIVE LOCATION TEST")
    print("=" * 60)
    
    try:
        import test_location_with_dm
        test_location_with_dm.interactive_exploration()
    except Exception as e:
        print(f"\n❌ Error: {e}")


def run_combat_narration_tests():
    """Run combat narration unit tests."""
    print("\n" + "=" * 60)
    print("  📖 RUNNING COMBAT NARRATION TESTS")
    print("=" * 60)
    
    try:
        import test_combat_with_dm
        test_combat_with_dm.run_narration_tests()
    except Exception as e:
        print(f"\n❌ Error: {e}")


def run_location_dm_tests():
    """Run location with DM unit tests."""
    print("\n" + "=" * 60)
    print("  🗺️ RUNNING LOCATION DM UNIT TESTS")
    print("=" * 60)
    
    try:
        import test_location_with_dm
        test_location_with_dm.run_unit_tests()
    except Exception as e:
        print(f"\n❌ Error: {e}")


# =============================================================================
# FULL ADVENTURE MODE
# =============================================================================

def run_full_adventure():
    """Run a full adventure combining all systems."""
    print("\n" + "=" * 60)
    print("  🏰 FULL ADVENTURE MODE")
    print("=" * 60)
    print("""
This mode combines:
  - Location exploration (move, look, take items)
  - NPC dialogue (talk to NPCs)
  - Combat encounters (fight enemies)
  - Inventory management (use items, manage loot)
  - Skill checks (solve challenges)

The adventure follows the Goblin Cave scenario:
  A farmer's daughter has been kidnapped by goblins!
  Navigate the tavern, journey through the forest,
  and brave the goblin lair to rescue her.
""")
    
    input("Press Enter to begin the adventure...")
    
    # Initialize AI
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ No GOOGLE_API_KEY found in environment!")
        return
    
    genai.configure(api_key=api_key)
    
    # Import necessary modules
    from scenario import create_goblin_cave_scenario, ScenarioManager
    from character import Character
    from inventory import get_item, add_item_to_inventory, format_inventory
    from combat import create_enemy, ENEMIES
    
    # Create character
    print("\n" + "=" * 60)
    print("  ⚔️ CHARACTER CREATION")
    print("=" * 60)
    
    name = input("\n  Enter your character's name: ").strip() or "Adventurer"
    
    print("\n  Choose your class:")
    print("    1. Fighter (STR focus, heavy armor)")
    print("    2. Rogue (DEX focus, sneak attacks)")
    print("    3. Wizard (INT focus, spellcasting)")
    
    class_choice = input("\n  Choice (1-3): ").strip()
    
    class_map = {"1": "Fighter", "2": "Rogue", "3": "Wizard"}
    char_class = class_map.get(class_choice, "Fighter")
    
    # Create test character with chosen class
    character = Character()
    character.name = name
    character.char_class = char_class
    
    # Apply class bonuses
    if char_class == "Fighter":
        character.strength = 16
        character.armor_class = 16
        character.weapon = "longsword"
    elif char_class == "Rogue":
        character.dexterity = 16
        character.armor_class = 14
        character.weapon = "shortsword"
    else:  # Wizard
        character.intelligence = 16
        character.armor_class = 12
        character.weapon = "quarterstaff"
    
    print(f"\n  ✅ Created {character.name} the {character.char_class}!")
    print(f"     HP: {character.current_hp}/{character.max_hp}")
    print(f"     AC: {character.armor_class}")
    print(f"     Weapon: {character.weapon}")
    
    # Create scenario
    scenario = create_goblin_cave_scenario()
    scenario_manager = ScenarioManager()
    scenario_manager.start_scenario(scenario)
    
    # Setup AI
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=f"""You are the Dungeon Master for "The Goblin Cave" adventure.

Player: {character.name}, a level {character.level} {character.char_class}
HP: {character.current_hp}/{character.max_hp}, AC: {character.armor_class}

SCENARIO: A farmer named Bram's daughter Lily has been kidnapped by goblins.
The player must navigate to Darkhollow Cave and rescue her.

CURRENT SCENE: {scenario_manager.active_scenario.scenes[scenario_manager.active_scenario.current_scene_id].name}

Be vivid but concise (2-4 sentences per response).
Roleplay NPCs with distinct personalities.
When combat would occur, describe the situation but don't resolve attacks - say [COMBAT TRIGGER] instead.
"""
    )
    
    chat = model.start_chat(history=[])
    
    # Get location manager
    loc_mgr = scenario_manager.active_scenario.location_manager
    
    # Show starting location
    print("\n" + "=" * 60)
    print("  🎭 THE ADVENTURE BEGINS")
    print("=" * 60)
    
    location = loc_mgr.get_current_location()
    print(f"\n  📍 {location.name}")
    print(f"  {location.description}")
    if location.atmosphere:
        print(f"  ({location.atmosphere})")
    
    items_display = location.get_items_display()
    npcs_display = location.get_npcs_display()
    if items_display:
        print(f"  {items_display}")
    if npcs_display:
        print(f"  {npcs_display}")
    print(f"  {location.get_exits_display()}")
    
    # Initial DM narration
    print("\n🎲 Dungeon Master:")
    response = chat.send_message(
        "Begin the adventure. The player has just entered the tavern. Set the scene and introduce them to the worried farmer Bram."
    )
    print(f"  {response.text}")
    
    print("\n" + "-" * 40)
    print("Commands: look, exits, go <dir>, take <item>, talk <npc>")
    print("          inv, stats, help, quit")
    print("-" * 40)
    
    # Main game loop
    while True:
        try:
            command = input("\n> ").strip().lower()
            
            if not command:
                continue
            
            if command in ["quit", "exit", "q"]:
                print("\n  Thank you for playing! The adventure awaits your return...")
                break
            
            if command == "help":
                print("""
  📖 COMMANDS:
    look         - Describe current location
    exits        - Show available exits
    go <dir>     - Move in a direction
    take <item>  - Pick up an item
    talk <npc>   - Talk to an NPC
    inv          - Show inventory
    stats        - Show character stats
    quit         - End adventure
    
    (Any other input is sent to the DM)
""")
                continue
            
            location = loc_mgr.get_current_location()
            
            # Stats command
            if command in ["stats", "status", "char", "character"]:
                print(f"\n  ⚔️ {character.name} - {character.char_class} (Level {character.level})")
                print(f"  ❤️ HP: {character.current_hp}/{character.max_hp}")
                print(f"  🛡️ AC: {character.armor_class}")
                print(f"  💰 Gold: {character.gold}")
                print(f"  ⚔️ Weapon: {character.weapon}")
                continue
            
            # Look command
            if command in ["look", "look around", "l"]:
                print(f"\n  📍 {location.name}")
                print(f"  {location.description}")
                if location.atmosphere:
                    print(f"  ({location.atmosphere})")
                items_display = location.get_items_display()
                npcs_display = location.get_npcs_display()
                if items_display:
                    print(f"  {items_display}")
                if npcs_display:
                    print(f"  {npcs_display}")
                print(f"  {location.get_exits_display()}")
                continue
            
            # Exits command
            if command in ["exits", "directions"]:
                exits = loc_mgr.get_exits()
                if exits:
                    print(f"\n  🚪 Available exits: {', '.join(exits.keys())}")
                else:
                    print("\n  🚪 There are no obvious exits.")
                continue
            
            # Movement commands
            movement_prefixes = ["go ", "move ", "walk ", "head "]
            is_movement = any(command.startswith(p) for p in movement_prefixes)
            
            if is_movement or command in ["n", "s", "e", "w", "north", "south", "east", "west"]:
                if is_movement:
                    for prefix in movement_prefixes:
                        if command.startswith(prefix):
                            direction = command[len(prefix):].strip()
                            break
                else:
                    direction = command
                
                success, new_loc, msg = loc_mgr.move(direction)
                
                if success and new_loc:
                    print(f"\n  📍 You move to: {new_loc.name}")
                    if new_loc.enter_text:
                        print(f"  {new_loc.enter_text}")
                    print(f"  {new_loc.get_exits_display()}")
                    
                    # AI describes the location
                    print("\n🎲 Dungeon Master:")
                    response = chat.send_message(
                        f"[Player moved to {new_loc.name}. {new_loc.description}] Describe what they see."
                    )
                    print(f"  {response.text}")
                else:
                    print(f"\n  ❌ {msg}")
                continue
            
            # Take command
            if command.startswith("take ") or command.startswith("pick up ") or command.startswith("grab "):
                if command.startswith("pick up "):
                    item_name = command[8:].strip()
                elif command.startswith("grab "):
                    item_name = command[5:].strip()
                else:
                    item_name = command[5:].strip()
                
                if location.has_item(item_name):
                    item = get_item(item_name)
                    if item:
                        location.remove_item(item_name)
                        
                        if "gold_pouch" in item_name.lower() or (item.effect and "gold pieces" in item.effect.lower()):
                            character.gold += item.value
                            print(f"\n  💰 You found {item.value} gold pieces!")
                        else:
                            msg = add_item_to_inventory(character.inventory, item)
                            print(f"\n  ✅ {msg}")
                    else:
                        print(f"\n  ❓ You pick up the {item_name}.")
                        location.remove_item(item_name)
                else:
                    print(f"\n  ❌ You don't see '{item_name}' here.")
                continue
            
            # Talk command
            if command.startswith("talk ") or command.startswith("speak "):
                for prefix in ["talk to ", "speak to ", "talk ", "speak "]:
                    if command.startswith(prefix):
                        npc_name = command[len(prefix):].strip()
                        break
                
                if location.has_npc(npc_name):
                    npc_display = npc_name.replace("_", " ").title()
                    print(f"\n  💬 You approach {npc_display}...")
                    print("\n🎲 Dungeon Master:")
                    response = chat.send_message(
                        f"[Player wants to talk to {npc_display}] Roleplay this NPC."
                    )
                    print(f"  {response.text}")
                else:
                    present_npcs = [n.replace("_", " ").title() for n in location.npcs]
                    if present_npcs:
                        print(f"\n  ❌ You don't see '{npc_name}' here. Present: {', '.join(present_npcs)}")
                    else:
                        print(f"\n  ❌ There's no one here to talk to.")
                continue
            
            # Inventory command
            if command in ["inv", "inventory", "i"]:
                print(format_inventory(character.inventory, character.gold))
                continue
            
            # Unknown command - pass to AI
            print("\n🎲 Dungeon Master:")
            response = chat.send_message(f"[Player action in {location.name}: {command}]")
            print(f"  {response.text}")
            
        except KeyboardInterrupt:
            print("\n\n  Adventure paused. Type 'quit' to exit.")
        except Exception as e:
            print(f"\n❌ Error: {e}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    try:
        while True:
            choice = show_main_menu()
            
            if choice == "0":
                print("\n  Goodbye, adventurer! 🎲")
                break
            
            elif choice == "1":
                run_pytest_tests("test_combat.py", "Combat System Tests")
            
            elif choice == "2":
                run_pytest_tests("test_location.py", "Location System Tests")
            
            elif choice == "3":
                run_pytest_tests("test_inventory.py", "Inventory System Tests")
            
            elif choice == "4":
                run_pytest_tests("test_scenario.py", "Scenario System Tests")
            
            elif choice == "5":
                run_all_unit_tests()
            
            elif choice == "6":
                run_interactive_combat()
            
            elif choice == "7":
                run_interactive_dice()
            
            elif choice == "8":
                run_interactive_inventory()
            
            elif choice == "9":
                run_interactive_location()
            
            elif choice == "10":
                run_full_adventure()
            
            elif choice == "11":
                run_combat_narration_tests()
            
            elif choice == "12":
                run_location_dm_tests()
            
            else:
                print("\n  ❌ Invalid choice. Please try again.")
            
            input("\n  Press Enter to continue...")
    
    except KeyboardInterrupt:
        print("\n\n  Goodbye, adventurer! 🎲")
