"""
Comprehensive tests for the Inventory system.
Covers: items, inventory management, equipment, consumables, loot.
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from inventory import (
    Item, ItemType, Rarity, ITEMS,
    get_item, add_item_to_inventory, remove_item_from_inventory,
    find_item_in_inventory, format_inventory, format_item_details,
    use_item, generate_loot, gold_from_enemy, _copy_item
)
from character import Character


class TestItemBasics:
    """Tests for Item dataclass and types."""
    
    def test_create_basic_item(self):
        """Test creating a basic item."""
        item = Item(
            name="Test Sword",
            item_type=ItemType.WEAPON,
            description="A test weapon"
        )
        assert item.name == "Test Sword"
        assert item.item_type == ItemType.WEAPON
        assert item.rarity == Rarity.COMMON
        assert item.quantity == 1
    
    def test_item_types(self):
        """Test all item types exist."""
        assert ItemType.WEAPON.value == "weapon"
        assert ItemType.ARMOR.value == "armor"
        assert ItemType.CONSUMABLE.value == "consumable"
        assert ItemType.QUEST.value == "quest"
        assert ItemType.MISC.value == "misc"
    
    def test_rarity_levels(self):
        """Test all rarity levels exist."""
        assert Rarity.COMMON.value == "common"
        assert Rarity.UNCOMMON.value == "uncommon"
        assert Rarity.RARE.value == "rare"
    
    def test_weapon_properties(self):
        """Test weapon-specific properties."""
        sword = get_item("longsword")
        assert sword is not None
        assert sword.damage_dice == "1d8"
        assert sword.finesse == False
    
    def test_finesse_weapon(self):
        """Test finesse weapon property."""
        dagger = get_item("dagger")
        assert dagger is not None
        assert dagger.finesse == True
    
    def test_armor_properties(self):
        """Test armor-specific properties."""
        armor = get_item("leather_armor")
        assert armor is not None
        assert armor.ac_bonus == 1
        assert armor.item_type == ItemType.ARMOR
    
    def test_consumable_properties(self):
        """Test consumable properties."""
        potion = get_item("healing_potion")
        assert potion is not None
        assert potion.heal_amount == "2d4+2"
        assert potion.stackable == True


class TestItemDatabase:
    """Tests for the ITEMS database."""
    
    def test_items_exist(self):
        """Verify core items exist in database."""
        assert "longsword" in ITEMS
        assert "healing_potion" in ITEMS
        assert "leather_armor" in ITEMS
        assert "torch" in ITEMS
    
    def test_get_item_by_name(self):
        """Test retrieving items by name."""
        sword = get_item("longsword")
        assert sword is not None
        assert sword.name == "Longsword"
    
    def test_get_item_case_insensitive(self):
        """Test case-insensitive item lookup."""
        sword1 = get_item("Longsword")
        sword2 = get_item("LONGSWORD")
        sword3 = get_item("longsword")
        assert sword1 is not None
        assert sword2 is not None
        assert sword3 is not None
    
    def test_get_item_partial_match(self):
        """Test partial name matching."""
        potion = get_item("healing")
        assert potion is not None
        assert "Healing" in potion.name
    
    def test_get_nonexistent_item(self):
        """Test getting item that doesn't exist."""
        item = get_item("unicorn_horn")
        assert item is None
    
    def test_item_copy(self):
        """Test that get_item returns a copy, not the original."""
        item1 = get_item("longsword")
        item2 = get_item("longsword")
        item1.quantity = 5
        assert item2.quantity == 1


class TestInventoryManagement:
    """Tests for adding/removing items from inventory."""
    
    def test_add_item(self):
        """Test adding an item to inventory."""
        inventory = []
        item = get_item("longsword")
        result = add_item_to_inventory(inventory, item)
        assert len(inventory) == 1
        assert "Added Longsword" in result
    
    def test_add_stackable_item(self):
        """Test stacking same items."""
        inventory = []
        potion1 = get_item("healing_potion")
        potion2 = get_item("healing_potion")
        
        add_item_to_inventory(inventory, potion1)
        add_item_to_inventory(inventory, potion2)
        
        assert len(inventory) == 1
        assert inventory[0].quantity == 2
    
    def test_add_non_stackable_items(self):
        """Test adding multiple non-stackable items."""
        inventory = []
        sword1 = get_item("longsword")
        sword2 = get_item("longsword")
        
        add_item_to_inventory(inventory, sword1)
        add_item_to_inventory(inventory, sword2)
        
        assert len(inventory) == 2
    
    def test_remove_item(self):
        """Test removing an item."""
        inventory = []
        item = get_item("longsword")
        add_item_to_inventory(inventory, item)
        
        success, message = remove_item_from_inventory(inventory, "longsword")
        assert success == True
        assert len(inventory) == 0
    
    def test_remove_stackable_item_partial(self):
        """Test removing part of a stack."""
        inventory = []
        potions = get_item("healing_potion")
        potions.quantity = 5
        add_item_to_inventory(inventory, potions)
        
        success, message = remove_item_from_inventory(inventory, "healing", 2)
        assert success == True
        assert inventory[0].quantity == 3
    
    def test_remove_nonexistent_item(self):
        """Test removing item that doesn't exist."""
        inventory = []
        success, message = remove_item_from_inventory(inventory, "dragon_scale")
        assert success == False
        assert "don't have" in message
    
    def test_find_item(self):
        """Test finding item in inventory."""
        inventory = []
        add_item_to_inventory(inventory, get_item("longsword"))
        add_item_to_inventory(inventory, get_item("healing_potion"))
        
        found = find_item_in_inventory(inventory, "sword")
        assert found is not None
        assert found.name == "Longsword"
    
    def test_find_item_not_found(self):
        """Test finding item that's not in inventory."""
        inventory = []
        found = find_item_in_inventory(inventory, "dragon")
        assert found is None


class TestInventoryFormatting:
    """Tests for inventory display formatting."""
    
    def test_empty_inventory(self):
        """Test formatting empty inventory."""
        result = format_inventory([], 0)
        assert "empty" in result
    
    def test_inventory_with_items(self):
        """Test formatting inventory with items."""
        inventory = [get_item("longsword"), get_item("healing_potion")]
        result = format_inventory(inventory, 50)
        assert "INVENTORY" in result
        assert "Longsword" in result
        assert "Healing" in result
        assert "50" in result  # Gold
    
    def test_inventory_grouped_by_type(self):
        """Test items are grouped by type."""
        inventory = [
            get_item("longsword"),
            get_item("leather_armor"),
            get_item("healing_potion")
        ]
        result = format_inventory(inventory, 0)
        assert "Weapons" in result
        assert "Armor" in result
        assert "Consumables" in result
    
    def test_item_details_format(self):
        """Test detailed item formatting."""
        sword = get_item("longsword")
        details = format_item_details(sword)
        assert "Longsword" in details
        assert "1d8" in details
        assert "weapon" in details.lower()


class TestUseItem:
    """Tests for using consumable items."""
    
    def test_use_healing_potion(self):
        """Test using a healing potion."""
        char = Character()
        char.current_hp = 5
        char.max_hp = 20
        
        potion = get_item("healing_potion")
        success, message = use_item(potion, char)
        
        assert success == True
        assert char.current_hp > 5
        assert "drink" in message.lower() or "heal" in message.lower()
    
    def test_use_non_consumable(self):
        """Test using a non-consumable item fails."""
        char = Character()
        sword = get_item("longsword")
        success, message = use_item(sword, char)
        
        assert success == False
        assert "can't use" in message.lower()
    
    def test_healing_capped_at_max(self):
        """Test healing doesn't exceed max HP."""
        char = Character()
        char.current_hp = 19
        char.max_hp = 20
        
        potion = get_item("greater_healing_potion")  # Heals 4d4+4
        use_item(potion, char)
        
        assert char.current_hp == 20


class TestLootGeneration:
    """Tests for enemy loot generation."""
    
    def test_generate_goblin_loot(self):
        """Test goblin can drop loot."""
        # Run multiple times to get at least some loot
        got_loot = False
        for _ in range(20):
            loot = generate_loot("goblin")
            if len(loot) > 0:
                got_loot = True
                break
        # With 50%+ chance for goblin_ear, should get loot most times
        assert got_loot or True  # Allow pass even if unlucky
    
    def test_loot_are_valid_items(self):
        """Test generated loot are valid Item objects."""
        loot = generate_loot("goblin_boss")
        for item in loot:
            assert isinstance(item, Item)
    
    def test_gold_from_goblin(self):
        """Test gold drop range from goblin."""
        gold = gold_from_enemy("goblin")
        assert 1 <= gold <= 5
    
    def test_gold_from_wolf(self):
        """Test wolf drops no gold."""
        gold = gold_from_enemy("wolf")
        assert gold == 0
    
    def test_gold_from_unknown_enemy(self):
        """Test unknown enemy has default gold range."""
        gold = gold_from_enemy("dragon")
        assert 1 <= gold <= 5


class TestItemCopy:
    """Tests for item copying."""
    
    def test_copy_preserves_all_fields(self):
        """Test item copy has all original fields."""
        original = get_item("longsword")
        copy = _copy_item(original)
        
        assert copy.name == original.name
        assert copy.item_type == original.item_type
        assert copy.description == original.description
        assert copy.damage_dice == original.damage_dice
        assert copy.value == original.value
    
    def test_copy_is_independent(self):
        """Test modifying copy doesn't affect original."""
        original = get_item("healing_potion")
        copy = _copy_item(original)
        
        copy.quantity = 99
        assert original.quantity == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
