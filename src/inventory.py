"""
Inventory System for AI D&D RPG
Handles items, equipment, consumables, and inventory management
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ItemType(Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    QUEST = "quest"
    MISC = "misc"


class Rarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"


@dataclass
class Item:
    """Base item class"""
    name: str
    item_type: ItemType
    description: str
    rarity: Rarity = Rarity.COMMON
    value: int = 0  # Gold value
    stackable: bool = False
    quantity: int = 1
    
    # Weapon stats (if weapon)
    damage_dice: Optional[str] = None
    finesse: bool = False
    
    # Armor stats (if armor)
    ac_bonus: Optional[int] = None
    
    # Consumable stats (if consumable)
    heal_amount: Optional[str] = None  # e.g., "2d4+2"
    effect: Optional[str] = None  # Description of effect


# ============================================================
#                     ITEM DATABASE
# ============================================================

ITEMS = {
    # -------------------- WEAPONS --------------------
    "dagger": Item(
        name="Dagger",
        item_type=ItemType.WEAPON,
        description="A simple blade for close combat.",
        damage_dice="1d4",
        finesse=True,
        value=2
    ),
    "shortsword": Item(
        name="Shortsword",
        item_type=ItemType.WEAPON,
        description="A versatile blade favored by rogues.",
        damage_dice="1d6",
        finesse=True,
        value=10
    ),
    "longsword": Item(
        name="Longsword",
        item_type=ItemType.WEAPON,
        description="A reliable warrior's weapon.",
        damage_dice="1d8",
        finesse=False,
        value=15
    ),
    "greataxe": Item(
        name="Greataxe",
        item_type=ItemType.WEAPON,
        description="A massive two-handed axe for brutal strikes.",
        damage_dice="1d12",
        finesse=False,
        value=30
    ),
    "quarterstaff": Item(
        name="Quarterstaff",
        item_type=ItemType.WEAPON,
        description="A simple wooden staff, versatile in combat.",
        damage_dice="1d6",
        finesse=False,
        value=2
    ),
    "longbow": Item(
        name="Longbow",
        item_type=ItemType.WEAPON,
        description="A powerful ranged weapon.",
        damage_dice="1d8",
        finesse=False,
        value=50
    ),
    "shortbow": Item(
        name="Shortbow",
        item_type=ItemType.WEAPON,
        description="A compact bow for mobile archers.",
        damage_dice="1d6",
        finesse=False,
        value=25
    ),
    "mace": Item(
        name="Mace",
        item_type=ItemType.WEAPON,
        description="A heavy bludgeoning weapon.",
        damage_dice="1d6",
        finesse=False,
        value=5
    ),
    "rapier": Item(
        name="Rapier",
        item_type=ItemType.WEAPON,
        description="An elegant thrusting weapon.",
        damage_dice="1d8",
        finesse=True,
        value=25
    ),
    
    # -------------------- ARMOR --------------------
    "leather_armor": Item(
        name="Leather Armor",
        item_type=ItemType.ARMOR,
        description="Light armor made of cured leather.",
        ac_bonus=1,
        value=10
    ),
    "studded_leather": Item(
        name="Studded Leather",
        item_type=ItemType.ARMOR,
        description="Leather reinforced with metal rivets.",
        ac_bonus=2,
        value=45
    ),
    "chain_shirt": Item(
        name="Chain Shirt",
        item_type=ItemType.ARMOR,
        description="A shirt of interlocking metal rings.",
        ac_bonus=3,
        value=50
    ),
    "chain_mail": Item(
        name="Chain Mail",
        item_type=ItemType.ARMOR,
        description="Full chain mail armor.",
        ac_bonus=4,
        value=75,
        rarity=Rarity.UNCOMMON
    ),
    "plate_armor": Item(
        name="Plate Armor",
        item_type=ItemType.ARMOR,
        description="Heavy metal plates covering the whole body.",
        ac_bonus=6,
        value=200,
        rarity=Rarity.RARE
    ),
    
    # -------------------- CONSUMABLES --------------------
    "healing_potion": Item(
        name="Healing Potion",
        item_type=ItemType.CONSUMABLE,
        description="A red liquid that restores health.",
        heal_amount="2d4+2",
        stackable=True,
        value=50
    ),
    "greater_healing_potion": Item(
        name="Greater Healing Potion",
        item_type=ItemType.CONSUMABLE,
        description="A stronger healing draught.",
        heal_amount="4d4+4",
        stackable=True,
        value=150,
        rarity=Rarity.UNCOMMON
    ),
    "antidote": Item(
        name="Antidote",
        item_type=ItemType.CONSUMABLE,
        description="Cures poison effects.",
        effect="Cures poison",
        stackable=True,
        value=25
    ),
    "rations": Item(
        name="Rations",
        item_type=ItemType.CONSUMABLE,
        description="A day's worth of food.",
        effect="Prevents hunger",
        stackable=True,
        value=1
    ),
    
    # -------------------- MISC ITEMS --------------------
    "torch": Item(
        name="Torch",
        item_type=ItemType.MISC,
        description="Provides light in dark places.",
        stackable=True,
        value=1
    ),
    "rope": Item(
        name="Rope (50 ft)",
        item_type=ItemType.MISC,
        description="Hempen rope, useful for climbing.",
        value=1
    ),
    "lockpicks": Item(
        name="Thieves' Tools",
        item_type=ItemType.MISC,
        description="Tools for picking locks.",
        value=25
    ),
    "bedroll": Item(
        name="Bedroll",
        item_type=ItemType.MISC,
        description="For resting on the road.",
        value=1
    ),
    
    # -------------------- QUEST ITEMS --------------------
    "mysterious_key": Item(
        name="Mysterious Key",
        item_type=ItemType.QUEST,
        description="An ornate key with strange runes.",
        value=0
    ),
    "ancient_scroll": Item(
        name="Ancient Scroll",
        item_type=ItemType.QUEST,
        description="A weathered scroll with forgotten knowledge.",
        value=0
    ),
    "goblin_ear": Item(
        name="Goblin Ear",
        item_type=ItemType.QUEST,
        description="Proof of a goblin slain.",
        stackable=True,
        value=2
    ),
}


# ============================================================
#                   INVENTORY FUNCTIONS
# ============================================================

def get_item(item_name: str) -> Optional[Item]:
    """Get an item from the database by name (case-insensitive)"""
    # Try exact match first
    key = item_name.lower().replace(" ", "_").replace("'", "")
    if key in ITEMS:
        return _copy_item(ITEMS[key])
    
    # Try partial match
    for item_key, item in ITEMS.items():
        if item_name.lower() in item.name.lower():
            return _copy_item(item)
    
    return None


def _copy_item(item: Item) -> Item:
    """Create a copy of an item"""
    return Item(
        name=item.name,
        item_type=item.item_type,
        description=item.description,
        rarity=item.rarity,
        value=item.value,
        stackable=item.stackable,
        quantity=1,
        damage_dice=item.damage_dice,
        finesse=item.finesse,
        ac_bonus=item.ac_bonus,
        heal_amount=item.heal_amount,
        effect=item.effect
    )


def add_item_to_inventory(inventory: list, item: Item) -> str:
    """Add an item to inventory, stacking if possible"""
    if item.stackable:
        # Check if already in inventory
        for inv_item in inventory:
            if inv_item.name == item.name:
                inv_item.quantity += item.quantity
                return f"Added {item.quantity}x {item.name} (now have {inv_item.quantity})"
    
    inventory.append(item)
    if item.quantity > 1:
        return f"Added {item.quantity}x {item.name} to inventory"
    return f"Added {item.name} to inventory"


def remove_item_from_inventory(inventory: list, item_name: str, quantity: int = 1) -> tuple[bool, str]:
    """Remove an item from inventory. Returns (success, message)"""
    for i, item in enumerate(inventory):
        if item_name.lower() in item.name.lower():
            if item.stackable and item.quantity > quantity:
                item.quantity -= quantity
                return True, f"Removed {quantity}x {item.name} ({item.quantity} remaining)"
            else:
                inventory.pop(i)
                return True, f"Removed {item.name} from inventory"
    
    return False, f"You don't have {item_name}"


def find_item_in_inventory(inventory: list, item_name: str) -> Optional[Item]:
    """Find an item in inventory by name"""
    for item in inventory:
        if item_name.lower() in item.name.lower():
            return item
    return None


def format_inventory(inventory: list, gold: int = 0) -> str:
    """Format inventory for display"""
    if not inventory and gold == 0:
        return "Your inventory is empty."
    
    lines = []
    lines.append("╔══════════════════════════════════════════════════════════╗")
    lines.append("║                      INVENTORY                           ║")
    lines.append("╠══════════════════════════════════════════════════════════╣")
    
    # Gold
    lines.append(f"║  💰 Gold: {gold:<46}║")
    lines.append("╠══════════════════════════════════════════════════════════╣")
    
    if not inventory:
        lines.append("║  (No items)                                              ║")
    else:
        # Group by type
        weapons = [i for i in inventory if i.item_type == ItemType.WEAPON]
        armor = [i for i in inventory if i.item_type == ItemType.ARMOR]
        consumables = [i for i in inventory if i.item_type == ItemType.CONSUMABLE]
        quest = [i for i in inventory if i.item_type == ItemType.QUEST]
        misc = [i for i in inventory if i.item_type == ItemType.MISC]
        
        for group_name, group in [("⚔️ Weapons", weapons), ("🛡️ Armor", armor), 
                                   ("🧪 Consumables", consumables), ("📜 Quest", quest),
                                   ("📦 Misc", misc)]:
            if group:
                lines.append(f"║  {group_name:<54}║")
                for item in group:
                    qty_str = f" x{item.quantity}" if item.quantity > 1 else ""
                    rarity_str = f" [{item.rarity.value}]" if item.rarity != Rarity.COMMON else ""
                    item_line = f"    • {item.name}{qty_str}{rarity_str}"
                    lines.append(f"║{item_line:<58}║")
    
    lines.append("╚══════════════════════════════════════════════════════════╝")
    return "\n".join(lines)


def format_item_details(item: Item) -> str:
    """Format detailed item info"""
    lines = []
    lines.append(f"📦 {item.name}")
    lines.append(f"   Type: {item.item_type.value.capitalize()}")
    lines.append(f"   {item.description}")
    
    if item.rarity != Rarity.COMMON:
        lines.append(f"   Rarity: {item.rarity.value.capitalize()}")
    
    if item.damage_dice:
        finesse = " (finesse)" if item.finesse else ""
        lines.append(f"   Damage: {item.damage_dice}{finesse}")
    
    if item.ac_bonus:
        lines.append(f"   AC Bonus: +{item.ac_bonus}")
    
    if item.heal_amount:
        lines.append(f"   Heals: {item.heal_amount}")
    
    if item.effect:
        lines.append(f"   Effect: {item.effect}")
    
    if item.value > 0:
        lines.append(f"   Value: {item.value} gold")
    
    return "\n".join(lines)


# ============================================================
#                    USE ITEM LOGIC
# ============================================================

def use_item(item: Item, character) -> tuple[bool, str]:
    """
    Use a consumable item on a character.
    Returns (success, message)
    """
    from combat import roll_dice  # Import here to avoid circular imports
    
    if item.item_type != ItemType.CONSUMABLE:
        return False, f"You can't use {item.name} like that."
    
    result_lines = []
    
    # Healing
    if item.heal_amount:
        heal_total, heal_rolls = roll_dice(item.heal_amount)
        old_hp = character.current_hp
        character.current_hp = min(character.max_hp, character.current_hp + heal_total)
        actual_heal = character.current_hp - old_hp
        result_lines.append(f"🧪 You drink the {item.name}!")
        result_lines.append(f"💚 Healed {actual_heal} HP ({old_hp} → {character.current_hp}/{character.max_hp})")
    
    # Other effects
    if item.effect:
        result_lines.append(f"✨ {item.effect}")
    
    if not result_lines:
        return False, f"The {item.name} has no effect."
    
    return True, "\n".join(result_lines)


# ============================================================
#                   LOOT GENERATION
# ============================================================

def generate_loot(enemy_name: str) -> list[Item]:
    """Generate random loot from defeated enemy"""
    import random
    
    loot = []
    
    # Basic loot table based on enemy
    loot_tables = {
        "goblin": [("goblin_ear", 0.5), ("dagger", 0.2), ("torch", 0.3)],
        "goblin_boss": [("goblin_ear", 1.0), ("shortsword", 0.5), ("healing_potion", 0.3)],
        "skeleton": [("dagger", 0.3), ("ancient_scroll", 0.1)],
        "orc": [("greataxe", 0.2), ("healing_potion", 0.2), ("rations", 0.5)],
        "bandit": [("shortsword", 0.3), ("lockpicks", 0.2), ("healing_potion", 0.25)],
        "wolf": [("rations", 0.5)],  # Wolf meat as rations
    }
    
    enemy_key = enemy_name.lower().replace(" ", "_")
    table = loot_tables.get(enemy_key, [])
    
    for item_key, chance in table:
        if random.random() < chance:
            item = get_item(item_key)
            if item:
                loot.append(item)
    
    return loot


def gold_from_enemy(enemy_name: str) -> int:
    """Generate gold dropped by enemy"""
    import random
    
    gold_ranges = {
        "goblin": (1, 5),
        "goblin_boss": (10, 25),
        "skeleton": (0, 3),
        "orc": (5, 15),
        "bandit": (5, 20),
        "wolf": (0, 0),
    }
    
    enemy_key = enemy_name.lower().replace(" ", "_")
    min_gold, max_gold = gold_ranges.get(enemy_key, (1, 5))
    
    return random.randint(min_gold, max_gold)
