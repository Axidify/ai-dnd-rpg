"""
Inventory + AI DM Integration Test
Interactive inventory management with AI Dungeon Master narration.

NOTE: The shop system in this test is a PROTOTYPE for testing AI merchant
interactions. The shop feature is NOT yet implemented in the main game.
Shop implementation is planned for Phase 3.3 (NPC System).

Run with: python tests/test_inventory_with_dm.py
"""

import os
import sys
import random

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
import google.generativeai as genai
from inventory import (
    Item, ItemType, Rarity, ITEMS,
    get_item, add_item_to_inventory, remove_item_from_inventory,
    find_item_in_inventory, format_inventory, format_item_details,
    use_item, generate_loot, gold_from_enemy
)
from combat import roll_dice

# Load environment variables
load_dotenv()


# =============================================================================
# MOCK CHARACTER
# =============================================================================

class MockCharacter:
    """Simple mock character for inventory testing."""
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
        self.armor_class = 14
        self.weapon = "longsword"
        self.equipped_armor = "chain_shirt"
        self.level = 1
        self.gold = 25
        self.inventory = []
        
        # Add starting equipment
        self._add_starting_gear()
    
    def _add_starting_gear(self):
        """Add starting items to inventory."""
        # Add healing potions
        potion = get_item("healing_potion")
        if potion:
            potion.quantity = 2
            add_item_to_inventory(self.inventory, potion)
        
        # Add some rations
        rations = get_item("rations")
        if rations:
            rations.quantity = 5
            add_item_to_inventory(self.inventory, rations)
        
        # Add torches
        torch = get_item("torch")
        if torch:
            torch.quantity = 3
            add_item_to_inventory(self.inventory, torch)
        
        # Add rope
        rope = get_item("rope")
        if rope:
            add_item_to_inventory(self.inventory, rope)
    
    def get_ability_modifier(self, ability_name):
        ability_map = {
            'strength': self.strength,
            'dexterity': self.dexterity,
            'constitution': self.constitution,
            'intelligence': self.intelligence,
            'wisdom': self.wisdom,
            'charisma': self.charisma,
        }
        score = ability_map.get(ability_name.lower(), 10)
        return (score - 10) // 2


# =============================================================================
# AI DM INTEGRATION - INVENTORY & SHOPPING
# =============================================================================

DM_INVENTORY_PROMPT = """You are an experienced Dungeon Master narrating inventory and shopping scenes in a D&D game.

## YOUR ROLE
Narrate item interactions, shopping, and loot discovery cinematically. React to what the player does with their items.

## STYLE GUIDELINES:
- Keep descriptions vivid but concise (2-4 sentences)
- Describe items in-world, not as game mechanics
- React to player's inventory actions naturally
- When shopping, roleplay as merchants with personality
- When finding loot, make it feel like a discovery

## CONTEXT MESSAGES YOU'LL RECEIVE:
- "[ITEM USED: Healing Potion - Healed 8 HP]" → Describe drinking the potion
- "[ITEM ADDED: Longsword]" → Describe acquiring the weapon
- "[ITEM REMOVED: 10 gold]" → Describe the transaction
- "[LOOT FOUND: Goblin Ear, 5 gold]" → Describe searching the corpse
- "[INVENTORY CHECK]" → Describe the character checking their pack

## EXAMPLE RESPONSES:

Input: "[ITEM USED: Healing Potion - Healed 6 HP]"
Output: "You uncork the small vial, the crimson liquid glowing faintly in the dim light. As you drink, warmth spreads through your limbs and the ache of your wounds begins to fade. Much better!"

Input: "[LOOT FOUND: Dagger, Goblin Ear, 3 gold]"
Output: "You search the fallen goblin's belongings. Its crude dagger still has some edge to it, and you find a small pouch with a few coins. You also claim an ear as proof of your victory—some tavern keepers pay bounties for these."

## PLAYER CHARACTER
Name: Kira (Human Fighter)
Equipped: Longsword, Chain Shirt
"""


MERCHANT_PROMPT = """You are a colorful merchant in a fantasy marketplace. You have a distinct personality.

## YOUR PERSONALITY
Choose ONE persona for the conversation:
- **Gruff Dwarf Smith**: Direct, prices firm, respects warriors
- **Charming Halfling**: Jokes, tries to upsell, knows gossip  
- **Mysterious Elf Apothecary**: Cryptic hints, speaks in riddles
- **Jovial Human Trader**: Friendly, loves to haggle, tells stories

## STYLE
- Stay in character throughout
- React to what the player buys or sells
- Comment on their choices ("Ah, a healing potion! Smart adventurer!")
- Keep responses short and punchy (2-3 sentences)

## MESSAGES YOU'LL RECEIVE
- "[PLAYER BOUGHT: Item Name for X gold]"
- "[PLAYER SOLD: Item Name for X gold]"
- "[PLAYER BROWSING: Category]"
- "[PLAYER GOLD: X]"

React naturally as your merchant character!
"""


def create_dm():
    """Initialize the AI DM for inventory narration."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not set in .env")
        sys.exit(1)
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=DM_INVENTORY_PROMPT
    )
    return model


def create_merchant():
    """Initialize the AI Merchant for shopping scenes."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not set in .env")
        sys.exit(1)
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=MERCHANT_PROMPT
    )
    return model


def get_dm_response(chat, message, stream=True):
    """Get streaming response from DM."""
    try:
        response = chat.send_message(message, stream=stream)
        full_text = ""
        
        for chunk in response:
            if chunk.text:
                full_text += chunk.text
                print(chunk.text, end="", flush=True)
        
        print()  # Final newline
        return full_text.strip()
    except Exception as e:
        print(f"(DM error: {e})")
        return None


# =============================================================================
# SHOP SYSTEM
# =============================================================================

SHOP_INVENTORY = {
    "weapons": {
        "dagger": 2,
        "shortsword": 10,
        "longsword": 15,
        "rapier": 25,
        "shortbow": 25,
        "longbow": 50,
    },
    "armor": {
        "leather_armor": 10,
        "studded_leather": 45,
        "chain_shirt": 50,
    },
    "potions": {
        "healing_potion": 50,
        "greater_healing_potion": 150,
        "antidote": 25,
    },
    "supplies": {
        "torch": 1,
        "rope": 1,
        "rations": 1,
        "lockpicks": 25,
    }
}


def display_shop_category(category):
    """Display items in a shop category."""
    print(f"\n╔══════════════════════════════════════╗")
    print(f"║  {category.upper():^34}  ║")
    print(f"╠══════════════════════════════════════╣")
    
    items = SHOP_INVENTORY.get(category, {})
    for item_key, price in items.items():
        item = get_item(item_key)
        if item:
            print(f"║  {item.name:<25} {price:>6} gp  ║")
    
    print(f"╚══════════════════════════════════════╝")


def buy_item(character, item_key, price, chat):
    """Process buying an item."""
    if character.gold < price:
        print(f"\n💰 Not enough gold! You have {character.gold} gp, need {price} gp.")
        return False
    
    item = get_item(item_key)
    if not item:
        print(f"\n❌ Item not found.")
        return False
    
    # Deduct gold and add item
    character.gold -= price
    result = add_item_to_inventory(character.inventory, item)
    
    print(f"\n💰 -{price} gold (Remaining: {character.gold} gp)")
    print(f"📦 {result}")
    
    # AI narration
    if chat:
        get_dm_response(chat, f"[PLAYER BOUGHT: {item.name} for {price} gold]")
    
    return True


def sell_item(character, item_name, chat):
    """Process selling an item."""
    item = find_item_in_inventory(character.inventory, item_name)
    if not item:
        print(f"\n❌ You don't have '{item_name}'.")
        return False
    
    # Calculate sell price (half value)
    sell_price = max(1, item.value // 2)
    
    # Remove item and add gold
    success, msg = remove_item_from_inventory(character.inventory, item_name)
    if success:
        character.gold += sell_price
        print(f"\n💰 +{sell_price} gold (Total: {character.gold} gp)")
        print(f"📦 {msg}")
        
        # AI narration
        if chat:
            get_dm_response(chat, f"[PLAYER SOLD: {item.name} for {sell_price} gold]")
        
        return True
    return False


# =============================================================================
# LOOT SYSTEM
# =============================================================================

def loot_enemy(character, enemy_name, chat):
    """Loot a defeated enemy with AI narration."""
    print(f"\n🔍 Searching the {enemy_name}...")
    
    # Generate loot
    loot = generate_loot(enemy_name)
    gold = gold_from_enemy(enemy_name)
    
    loot_names = []
    
    # Add items to inventory
    for item in loot:
        add_item_to_inventory(character.inventory, item)
        loot_names.append(item.name)
    
    # Add gold
    character.gold += gold
    
    # Display results
    print(f"\n💰 Found {gold} gold! (Total: {character.gold} gp)")
    if loot:
        print(f"📦 Found: {', '.join(loot_names)}")
    else:
        print(f"📦 No items found.")
    
    # AI narration
    if chat:
        loot_desc = ", ".join(loot_names) if loot_names else "nothing of value"
        get_dm_response(chat, f"[LOOT FOUND: {loot_desc}, {gold} gold from {enemy_name}]")


# =============================================================================
# ITEM USE SYSTEM
# =============================================================================

def use_item_from_inventory(character, item_name, chat):
    """Use an item from inventory with AI narration."""
    item = find_item_in_inventory(character.inventory, item_name)
    if not item:
        print(f"\n❌ You don't have '{item_name}'.")
        return False
    
    # Try to use the item
    success, message = use_item(item, character)
    
    if success:
        # Remove from inventory
        remove_item_from_inventory(character.inventory, item_name)
        print(f"\n{message}")
        
        # AI narration
        if chat:
            get_dm_response(chat, f"[ITEM USED: {item.name} - {message}]")
        
        return True
    else:
        print(f"\n{message}")
        return False


# =============================================================================
# INTERACTIVE TEST MENU
# =============================================================================

def display_main_menu():
    """Display the main interaction menu."""
    print("\n" + "=" * 50)
    print("         ⚔️  INVENTORY TEST MENU  ⚔️")
    print("=" * 50)
    print("  1. View Inventory")
    print("  2. Use Item")
    print("  3. Visit Shop")
    print("  4. Loot Enemy")
    print("  5. Inspect Item")
    print("  6. Take Damage (test healing)")
    print("  7. Character Status")
    print("  8. Exit")
    print("=" * 50)


def display_shop_menu():
    """Display the shop menu."""
    print("\n" + "=" * 50)
    print("          🏪  MERCHANT'S SHOP  🏪")
    print("=" * 50)
    print("  1. Browse Weapons")
    print("  2. Browse Armor")
    print("  3. Browse Potions")
    print("  4. Browse Supplies")
    print("  5. Sell Item")
    print("  6. Leave Shop")
    print("=" * 50)


def display_enemy_menu():
    """Display lootable enemies."""
    print("\n" + "=" * 50)
    print("         💀  SELECT ENEMY TO LOOT  💀")
    print("=" * 50)
    print("  1. Goblin")
    print("  2. Goblin Boss")
    print("  3. Orc")
    print("  4. Bandit")
    print("  5. Skeleton")
    print("  6. Wolf")
    print("  7. Cancel")
    print("=" * 50)


def run_shop_scene(character, merchant_chat):
    """Run the interactive shop scene."""
    print("\n🏪 You enter the merchant's shop...")
    
    if merchant_chat:
        get_dm_response(merchant_chat, 
            f"[PLAYER ENTERS SHOP with {character.gold} gold. Greet them in character!]")
    
    while True:
        display_shop_menu()
        print(f"\n💰 Your gold: {character.gold} gp")
        choice = input("\nChoice: ").strip()
        
        if choice == "1":
            display_shop_category("weapons")
            item = input("Buy which item (or 'back'): ").strip().lower()
            if item != 'back' and item in SHOP_INVENTORY["weapons"]:
                buy_item(character, item, SHOP_INVENTORY["weapons"][item], merchant_chat)
        
        elif choice == "2":
            display_shop_category("armor")
            item = input("Buy which item (or 'back'): ").strip().lower().replace(" ", "_")
            if item != 'back' and item in SHOP_INVENTORY["armor"]:
                buy_item(character, item, SHOP_INVENTORY["armor"][item], merchant_chat)
        
        elif choice == "3":
            display_shop_category("potions")
            item = input("Buy which item (or 'back'): ").strip().lower().replace(" ", "_")
            if item != 'back' and item in SHOP_INVENTORY["potions"]:
                buy_item(character, item, SHOP_INVENTORY["potions"][item], merchant_chat)
        
        elif choice == "4":
            display_shop_category("supplies")
            item = input("Buy which item (or 'back'): ").strip().lower()
            if item != 'back' and item in SHOP_INVENTORY["supplies"]:
                buy_item(character, item, SHOP_INVENTORY["supplies"][item], merchant_chat)
        
        elif choice == "5":
            print(format_inventory(character.inventory, character.gold))
            item = input("Sell which item (or 'back'): ").strip()
            if item != 'back':
                sell_item(character, item, merchant_chat)
        
        elif choice == "6":
            print("\n👋 You leave the shop.")
            if merchant_chat:
                get_dm_response(merchant_chat, "[PLAYER LEAVES SHOP. Say farewell in character!]")
            break
        
        else:
            print("Invalid choice.")


def run_interactive_test():
    """Main interactive test loop."""
    print("\n" + "=" * 60)
    print("       🎒 INVENTORY SYSTEM INTERACTIVE TEST 🎒")
    print("=" * 60)
    print("\nInitializing AI Dungeon Master...")
    
    # Initialize AI
    dm_model = create_dm()
    dm_chat = dm_model.start_chat(history=[])
    
    merchant_model = create_merchant()
    
    # Create mock character
    character = MockCharacter()
    
    print(f"\n✨ Welcome, {character.name} the {character.race} {character.char_class}!")
    print(f"💰 You have {character.gold} gold.")
    print(f"❤️ HP: {character.current_hp}/{character.max_hp}")
    
    # Initial inventory check
    get_dm_response(dm_chat, 
        f"[SCENE START] {character.name} checks their adventuring pack before setting out. Describe the scene briefly.")
    
    while True:
        display_main_menu()
        choice = input("\nChoice: ").strip()
        
        if choice == "1":
            # View Inventory
            print(format_inventory(character.inventory, character.gold))
            get_dm_response(dm_chat, "[INVENTORY CHECK] The player examines their belongings.")
        
        elif choice == "2":
            # Use Item
            print("\n📦 Your consumables:")
            consumables = [i for i in character.inventory if i.item_type == ItemType.CONSUMABLE]
            for item in consumables:
                qty = f" x{item.quantity}" if item.quantity > 1 else ""
                print(f"  • {item.name}{qty}")
            
            if not consumables:
                print("  (No consumables)")
            else:
                item_name = input("\nUse which item: ").strip()
                if item_name:
                    use_item_from_inventory(character, item_name, dm_chat)
        
        elif choice == "3":
            # Visit Shop
            merchant_chat = merchant_model.start_chat(history=[])
            run_shop_scene(character, merchant_chat)
        
        elif choice == "4":
            # Loot Enemy
            display_enemy_menu()
            enemy_choice = input("\nChoice: ").strip()
            enemies = {
                "1": "goblin",
                "2": "goblin_boss", 
                "3": "orc",
                "4": "bandit",
                "5": "skeleton",
                "6": "wolf"
            }
            if enemy_choice in enemies:
                loot_enemy(character, enemies[enemy_choice], dm_chat)
        
        elif choice == "5":
            # Inspect Item
            print("\n📦 Your items:")
            for item in character.inventory:
                qty = f" x{item.quantity}" if item.quantity > 1 else ""
                print(f"  • {item.name}{qty}")
            
            item_name = input("\nInspect which item: ").strip()
            item = find_item_in_inventory(character.inventory, item_name)
            if item:
                print(f"\n{format_item_details(item)}")
            else:
                print(f"\n❌ Item not found.")
        
        elif choice == "6":
            # Take Damage
            damage = random.randint(3, 8)
            character.current_hp = max(0, character.current_hp - damage)
            print(f"\n💥 You take {damage} damage! HP: {character.current_hp}/{character.max_hp}")
            
            if character.current_hp == 0:
                print("💀 You have fallen unconscious!")
                character.current_hp = 1  # Don't actually die in test
                print("   (Reset to 1 HP for testing)")
            
            get_dm_response(dm_chat, 
                f"[DAMAGE TAKEN: {damage} damage. Player HP: {character.current_hp}/{character.max_hp}] Narrate briefly.")
        
        elif choice == "7":
            # Character Status
            print(f"\n" + "=" * 40)
            print(f"  {character.name} - {character.race} {character.char_class}")
            print(f"  Level: {character.level}")
            print(f"  HP: {character.current_hp}/{character.max_hp}")
            print(f"  AC: {character.armor_class}")
            print(f"  Gold: {character.gold} gp")
            print(f"  Weapon: {character.weapon}")
            print(f"  Armor: {character.equipped_armor}")
            print(f"  Items: {len(character.inventory)}")
            print(f"=" * 40)
        
        elif choice == "8":
            print("\n👋 Farewell, adventurer!")
            break
        
        else:
            print("Invalid choice. Try again.")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  INVENTORY + AI DM INTEGRATION TEST")
    print("  Tests inventory management with AI narration")
    print("=" * 60)
    
    try:
        run_interactive_test()
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
