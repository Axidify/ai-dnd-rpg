"""
Unified Interactive Test Runner for AI RPG
Combines all test modules into a single menu-driven interface.

Run with: python tests/run_interactive_tests.py
"""

import os
import sys
import subprocess

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

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
    print("║" + "🎮 AI RPG - INTERACTIVE TEST SUITE 🎮".center(62) + "║")
    print("╠" + "═" * 62 + "╣")
    print("║" + "  UNIT TESTS (no AI required)".ljust(62) + "║")
    print("║" + "    1. Combat System Tests (31 tests)".ljust(62) + "║")
    print("║" + "    2. Location System Tests (174 tests)".ljust(62) + "║")
    print("║" + "    3. Inventory System Tests (35 tests)".ljust(62) + "║")
    print("║" + "    4. Scenario System Tests (31 tests)".ljust(62) + "║")
    print("║" + "    5. Shop System Tests (28 tests)".ljust(62) + "║")
    print("║" + "    6. NPC & Reputation Tests (128 tests)".ljust(62) + "║")
    print("║" + "    7. Run ALL Unit Tests (728 total)".ljust(62) + "║")
    print("╠" + "═" * 62 + "╣")
    print("║" + "  INTERACTIVE TESTS (with AI DM)".ljust(62) + "║")
    print("║" + "    8. Interactive Combat".ljust(62) + "║")
    print("║" + "    9. Interactive Dice/Skill Checks".ljust(62) + "║")
    print("║" + "   10. Interactive Inventory".ljust(62) + "║")
    print("║" + "   11. Interactive Shop (Buy/Sell/Haggle)".ljust(62) + "║")
    print("║" + "   12. Interactive Location Exploration".ljust(62) + "║")
    print("║" + "   13. Full Adventure (all systems combined)".ljust(62) + "║")
    print("╠" + "═" * 62 + "╣")
    print("║" + "  NARRATION TESTS".ljust(62) + "║")
    print("║" + "   14. Combat Narration Tests".ljust(62) + "║")
    print("║" + "   15. Location with DM Unit Tests (8 tests)".ljust(62) + "║")
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


def run_npc_reputation_tests():
    """Run NPC and Reputation system tests."""
    print("\n" + "=" * 60)
    print("  🧪 RUNNING NPC & REPUTATION TESTS")
    print("=" * 60)
    
    tests_dir = os.path.dirname(__file__)
    test_files = [
        "test_npc.py",
        "test_reputation.py",
        "test_reputation_hostile.py",
    ]
    
    results = []
    for test_file in test_files:
        test_path = os.path.join(tests_dir, test_file)
        if os.path.exists(test_path):
            print(f"\n  Running {test_file}...")
            result = subprocess.run(
                ["python", "-m", "pytest", test_path, "-v", "--tb=short"],
                capture_output=False
            )
            results.append((test_file, result.returncode == 0))
    
    # Summary
    print("\n" + "=" * 60)
    print("  📊 NPC & REPUTATION TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    failed = len(results) - passed
    
    for test_file, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {test_file}")
    
    print(f"\n  Total: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


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
        "test_shop.py",
        "test_npc.py",
        "test_dialogue.py",
        "test_xp_system.py",
        "test_reputation.py",
        "test_reputation_hostile.py",
        "test_quest.py",
        "test_traveling_merchant.py",
        "test_multi_enemy.py",
        "test_hostile_player.py",
        "test_prompt_injection.py",
        "test_flow_breaking.py",
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
    """Run interactive inventory test."""
    print("\n" + "=" * 60)
    print("  🎒 LAUNCHING INTERACTIVE INVENTORY TEST")
    print("=" * 60)
    
    try:
        import test_inventory_with_dm
        test_inventory_with_dm.run_interactive_test()
    except Exception as e:
        print(f"\n❌ Error: {e}")


def run_interactive_shop():
    """Run interactive shop test with Trader Mira and AI narration."""
    print("\n" + "=" * 60)
    print("  🛒 LAUNCHING INTERACTIVE SHOP TEST (with AI DM)")
    print("=" * 60)
    print("""
This test simulates shopping with Trader Mira at the forest clearing.
The AI Game Master will narrate your shopping experience!

Available commands:
  shop       - View Mira's wares
  buy <item> - Purchase an item
  sell <item> - Sell from your inventory
  haggle     - Try to negotiate prices (CHA DC 12)
  inventory  - View your items and gold
  talk       - Chat with Mira (AI responds)
  quit       - Exit the shop test
""")
    
    input("Press Enter to enter the shop...")
    
    # Check for API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ No GOOGLE_API_KEY found! Running without AI narration.")
        ai_enabled = False
    else:
        genai.configure(api_key=api_key)
        ai_enabled = True
    
    # Import necessary modules
    from character import Character
    from scenario import create_goblin_cave_npcs
    from npc import (
        get_merchant_at_location, format_shop_display,
        calculate_buy_price, calculate_sell_price,
        check_stock, decrement_stock, get_shop_inventory_for_prompt
    )
    from inventory import (
        ITEMS, get_item, add_item_to_inventory, remove_item_from_inventory,
        find_item_in_inventory, format_inventory
    )
    from combat import roll_dice
    
    # Setup character with some gold and starting items
    character = Character()
    character.name = "Adventurer"
    character.gold = 150
    character.charisma = 14  # +2 modifier for haggle tests
    
    # Add starting items (need to get Item objects from ITEMS dict)
    for item_id in ["dagger", "goblin_ear", "torch"]:
        item = get_item(item_id)
        if item:
            add_item_to_inventory(character.inventory, item)
    
    # Get merchant from scenario
    npc_manager = create_goblin_cave_npcs()
    merchant = get_merchant_at_location(npc_manager, "forest_clearing")
    
    if not merchant:
        print("❌ Could not find Trader Mira!")
        return
    
    # Setup AI chat
    chat = None
    if ai_enabled:
        # Get actual inventory for prompt
        inventory_info = get_shop_inventory_for_prompt(merchant, ITEMS)
        
        SHOP_DM_PROMPT = f"""You are the Game Master narrating a shopping interaction in a tabletop-style RPG.

MERCHANT: {merchant.name}
Description: {merchant.description}
Personality: Friendly but business-minded, disposition {merchant.disposition}/100
Location: Forest clearing along the path to Darkhollow

{inventory_info}

PLAYER: {character.name}
Gold: {character.gold}g
Charisma modifier: +{(character.charisma - 10) // 2}

Your role:
1. Narrate the shopping experience with atmosphere and immersion
2. Voice Trader Mira's dialogue (she's a weathered but friendly merchant)
3. React to purchases, sales, and haggling attempts
4. Keep responses SHORT (2-3 sentences for actions, slightly more for conversation)
5. Add sensory details - the forest clearing, her pack mule, goods on display
6. Never reveal game mechanics directly - describe outcomes narratively

CRITICAL RULES:
- When asked about stock/quantities, ONLY reference the EXACT numbers above!
- NEVER invent different quantities or item types that aren't listed!
- If player asks "how many X do you have?" refer to the actual inventory numbers.
- There is only ONE type of healing potion (not "lesser" or "greater" variants).

When the player buys/sells/haggles, you'll be told the outcome. Narrate it colorfully.
When the player wants to talk, engage in character as Mira."""
        
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=SHOP_DM_PROMPT
        )
        chat = model.start_chat(history=[])
        
        # Opening narration
        print("\n🎲 Game Master:")
        try:
            response = chat.send_message(
                "The adventurer approaches the merchant's stall in the forest clearing. Set the scene briefly."
            )
            print(f"  {response.text}")
        except Exception as e:
            print(f"  [AI Error: {e}]")
            print(f"  You approach {merchant.name} at the forest clearing.")
    else:
        print(f"\n  📍 You approach {merchant.name} at the forest clearing.")
        print(f"  💬 \"{merchant.get_dialogue('greeting')}\"")
    
    print(f"\n  💰 Your gold: {character.gold}g")
    
    # Track haggle state
    haggle_state = {merchant.id: {"discount": 0.0, "increase": 0.0}}
    
    # Auto-display shop on entry
    print("\n  📋 Mira's current inventory:")
    display = format_shop_display(merchant, ITEMS, character.gold, discount=0.0, price_increase=0.0)
    print(display)
    
    while True:
        print()
        player_input = input("  🛒 Shop > ").strip()
        lower_input = player_input.lower()
        
        if lower_input in ["quit", "exit", "leave", "q"]:
            if ai_enabled and chat:
                print("\n🎲 Game Master:")
                try:
                    response = chat.send_message("The adventurer is leaving the shop. Give a brief farewell from Mira.")
                    print(f"  {response.text}")
                except:
                    print(f"  💬 \"{merchant.get_dialogue('farewell')}\"")
            else:
                print(f"\n  💬 \"{merchant.get_dialogue('farewell')}\"")
            print("  👋 You leave the shop.")
            break
        
        # Check for shop/browse commands (expanded for natural language)
        shop_phrases = ["shop", "browse", "wares", "show", "what do you sell", 
                        "what do you have", "items", "goods", "stock", "see wares",
                        "show me", "display", "list"]
        if any(phrase in lower_input for phrase in shop_phrases):
            state = haggle_state[merchant.id]
            display = format_shop_display(
                merchant, ITEMS, character.gold,
                discount=state["discount"],
                price_increase=state["increase"]
            )
            print(display)
            if ai_enabled and chat:
                print("\n🎲 Game Master:")
                try:
                    response = chat.send_message("The player is browsing the wares. Brief reaction from Mira (1 sentence).")
                    print(f"  {response.text}")
                except:
                    pass
            continue
        
        if lower_input in ["inv", "inventory", "i"]:
            print(format_inventory(character.inventory, character.gold))
            continue
        
        if lower_input.startswith("buy "):
            item_name = player_input[4:].strip()
            
            # Find in merchant inventory (handle both dict and list formats)
            matching_item_id = None
            if isinstance(merchant.shop_inventory, dict):
                inventory_items = list(merchant.shop_inventory.keys())
            else:
                inventory_items = merchant.shop_inventory
            
            for inv_item in inventory_items:
                if item_name.lower() in inv_item.lower():
                    matching_item_id = inv_item
                    break
            
            if not matching_item_id:
                print(f"  ❌ Mira doesn't sell '{item_name}'.")
                if ai_enabled and chat:
                    print("\n🎲 Game Master:")
                    try:
                        response = chat.send_message(f"Player tried to buy '{item_name}' but Mira doesn't have it. Her response.")
                        print(f"  {response.text}")
                    except:
                        pass
                continue
            
            # Check stock
            stock = check_stock(merchant, matching_item_id)
            if stock == 0:
                item = get_item(matching_item_id)
                item_display = item.name if item else matching_item_id
                print(f"  ❌ Mira is out of {item_display}!")
                if ai_enabled and chat:
                    print("\n🎲 Game Master:")
                    try:
                        response = chat.send_message(f"Player tried to buy {item_display} but it's out of stock. Mira's apologetic response.")
                        print(f"  {response.text}")
                    except:
                        pass
                continue
            
            item = get_item(matching_item_id)
            if not item:
                print(f"  ❌ Item '{matching_item_id}' not in database.")
                continue
            
            # Calculate price with modifiers
            state = haggle_state[merchant.id]
            base_price = calculate_buy_price(item.value, merchant.merchant_markup)
            final_price = int(base_price * (1 - state["discount"] + state["increase"]))
            
            if character.gold < final_price:
                print(f"  ❌ Not enough gold! Need {final_price}g, have {character.gold}g")
                if ai_enabled and chat:
                    print("\n🎲 Game Master:")
                    try:
                        response = chat.send_message(f"Player can't afford {item.name} ({final_price}g). Mira's sympathetic but firm response.")
                        print(f"  {response.text}")
                    except:
                        pass
            else:
                character.gold -= final_price
                purchased_item = get_item(matching_item_id)
                add_item_to_inventory(character.inventory, purchased_item)
                decrement_stock(merchant, matching_item_id)
                
                # Show stock remaining
                remaining = check_stock(merchant, matching_item_id)
                if remaining == -1:
                    print(f"  ✅ Purchased {item.name} for {final_price}g!")
                elif remaining == 0:
                    print(f"  ✅ Purchased {item.name} for {final_price}g! (LAST ONE!)")
                else:
                    print(f"  ✅ Purchased {item.name} for {final_price}g! ({remaining} left in stock)")
                print(f"  💰 Remaining: {character.gold}g")
                
                if ai_enabled and chat:
                    print("\n🎲 Game Master:")
                    try:
                        stock_msg = ""
                        if remaining == 0:
                            stock_msg = " That was the last one!"
                        elif remaining > 0:
                            stock_msg = f" {remaining} remaining."
                        response = chat.send_message(f"Player bought {item.name} for {final_price}g.{stock_msg} Narrate the exchange briefly.")
                        print(f"  {response.text}")
                    except:
                        pass
            continue
        
        if lower_input.startswith("sell "):
            item_name = player_input[5:].strip()
            item = find_item_in_inventory(character.inventory, item_name)
            
            if not item:
                print(f"  ❌ You don't have '{item_name}' to sell.")
                continue
            
            sell_price = calculate_sell_price(item.value)
            remove_item_from_inventory(character.inventory, item_name)
            character.gold += sell_price
            print(f"  ✅ Sold {item.name} for {sell_price}g!")
            print(f"  💰 Your gold: {character.gold}g")
            if ai_enabled and chat:
                print("\n🎲 Game Master:")
                try:
                    response = chat.send_message(f"Player sold {item.name} for {sell_price}g. Mira's reaction to the item.")
                    print(f"  {response.text}")
                except:
                    pass
            continue
        
        if lower_input in ["haggle", "bargain", "negotiate"]:
            state = haggle_state[merchant.id]
            
            if state["discount"] > 0:
                print(f"  ✓ Already have a {int(state['discount']*100)}% discount!")
                continue
            if state["increase"] > 0:
                print(f"  ❌ Mira won't negotiate after your failed attempt.")
                continue
            
            print(f"\n  🗣️ Attempting to haggle with {merchant.name}...")
            print("  📋 Charisma Check (DC 12)")
            input("     Press Enter to roll...")
            
            roll = roll_dice("1d20")[0]
            cha_mod = (character.charisma - 10) // 2
            total = roll + cha_mod
            
            print(f"  🎲 Rolled: {roll} + {cha_mod} (CHA) = {total}")
            
            if total >= 12:
                haggle_state[merchant.id]["discount"] = 0.20
                print(f"\n  ✅ Success! 20% discount earned!")
                if ai_enabled and chat:
                    print("\n🎲 Game Master:")
                    try:
                        response = chat.send_message(f"Player succeeded haggling (rolled {total} vs DC 12)! They get 20% discount. Narrate Mira reluctantly agreeing.")
                        print(f"  {response.text}")
                    except:
                        print(f"  💬 \"{merchant.get_dialogue('haggle_accept') or 'Fine, you win!'}\"")
                else:
                    print(f"  💬 \"{merchant.get_dialogue('haggle_accept') or 'Fine, you win!'}\"")
            else:
                haggle_state[merchant.id]["increase"] = 0.10
                merchant.disposition = max(0, merchant.disposition - 5)
                print(f"\n  ❌ Failed! Prices increased by 10%!")
                if ai_enabled and chat:
                    print("\n🎲 Game Master:")
                    try:
                        response = chat.send_message(f"Player failed haggling (rolled {total} vs DC 12). Mira is offended, prices go UP 10%. Narrate her annoyance.")
                        print(f"  {response.text}")
                    except:
                        print(f"  💬 \"{merchant.get_dialogue('haggle_reject') or 'How insulting!'}\"")
                else:
                    print(f"  💬 \"{merchant.get_dialogue('haggle_reject') or 'How insulting!'}\"")
            continue
        
        if lower_input.startswith("talk") or lower_input.startswith("speak") or lower_input.startswith("ask"):
            # Extract topic if any
            topic = player_input.split(" ", 1)[1] if " " in player_input else "general"
            
            if ai_enabled and chat:
                print("\n🎲 Game Master:")
                try:
                    response = chat.send_message(f"Player wants to talk to Mira about: {topic}. Respond as Mira in character.")
                    print(f"  {response.text}")
                except Exception as e:
                    print(f"  [AI Error: {e}]")
            else:
                # Use static dialogue
                if "danger" in topic.lower() or "darkhollow" in topic.lower():
                    print(f"  💬 \"{merchant.get_dialogue('about_danger') or 'The eastern path is dangerous.'}\"")
                elif "wares" in topic.lower() or "sell" in topic.lower():
                    print(f"  💬 \"{merchant.get_dialogue('about_wares') or 'I have many fine goods!'}\"")
                else:
                    print(f"  💬 \"{merchant.get_dialogue('greeting')}\"")
            continue
        
        if lower_input == "help":
            print("""
  Commands:
    shop       - View merchant's wares
    buy <item> - Purchase an item  
    sell <item> - Sell from inventory
    haggle     - Negotiate for discount
    talk [topic] - Chat with Mira (AI-powered)
    inventory  - View your items
    quit       - Leave the shop
""")
            continue
        
        # Unknown command - let AI handle freeform input
        if ai_enabled and chat:
            print("\n🎲 Game Master:")
            try:
                response = chat.send_message(f"Player action in shop: '{player_input}'. React appropriately as DM/Mira.")
                print(f"  {response.text}")
            except Exception as e:
                print(f"  ❓ Unknown command. Type 'help' for commands.")
        else:
            print("  ❓ Unknown command. Type 'help' for commands.")


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
        system_instruction=f"""You are the Game Master for "The Goblin Cave" adventure.

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
    print("\n🎲 Game Master:")
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
                    print("\n🎲 Game Master:")
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
                    print("\n🎲 Game Master:")
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
            print("\n🎲 Game Master:")
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
                run_pytest_tests("test_shop.py", "Shop System Tests")
            
            elif choice == "6":
                run_npc_reputation_tests()
            
            elif choice == "7":
                run_all_unit_tests()
            
            elif choice == "8":
                run_interactive_combat()
            
            elif choice == "9":
                run_interactive_dice()
            
            elif choice == "10":
                run_interactive_inventory()
            
            elif choice == "11":
                run_interactive_shop()
            
            elif choice == "12":
                run_interactive_location()
            
            elif choice == "13":
                run_full_adventure()
            
            elif choice == "14":
                run_combat_narration_tests()
            
            elif choice == "15":
                run_location_dm_tests()
            
            else:
                print("\n  ❌ Invalid choice. Please try again.")
            
            input("\n  Press Enter to continue...")
    
    except KeyboardInterrupt:
        print("\n\n  Goodbye, adventurer! 🎲")
