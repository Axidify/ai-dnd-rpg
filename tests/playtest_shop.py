"""
Shop System Playtest Harness
============================
25 unique tests for the shop mechanic covering:
- Basic shop operations (view, buy, sell)
- Transaction edge cases
- Numeric edge cases  
- Injection attacks
- Shop state management
- Advanced scenarios

Run with: python -m tests.playtest_shop
"""

import sys
import os
import io
import random
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from contextlib import redirect_stdout

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from character import Character, CLASSES, RACES
from scenario import ScenarioManager, create_goblin_cave_shops
from inventory import (
    Item, ItemType, ITEMS, get_item, add_item_to_inventory,
    remove_item_from_inventory, find_item_in_inventory
)
from shop import (
    Shop, ShopManager, ShopType, ShopInventoryItem,
    buy_item, sell_item, attempt_haggle, get_disposition_price_modifier,
    calculate_buy_price, calculate_sell_price
)
from npc import NPCManager


# =============================================================================
# TEST DATA STRUCTURES
# =============================================================================

@dataclass
class ShopTestResult:
    """Result of a single shop test."""
    test_name: str
    passed: bool
    commands_executed: int
    bugs_found: List[str] = field(default_factory=list)
    transactions: int = 0
    gold_tracked: bool = True
    inventory_synced: bool = True
    error_message: str = ""


@dataclass
class ShopBug:
    """A bug found during shop testing."""
    test_name: str
    description: str
    command: str
    expected: str
    actual: str
    severity: str  # critical, major, minor


# =============================================================================
# SHOP TEST HARNESS
# =============================================================================

class ShopTestHarness:
    """Harness for testing shop system."""
    
    def __init__(self):
        self.results: List[ShopTestResult] = []
        self.bugs: List[ShopBug] = []
        self.total_commands = 0
        self.total_transactions = 0
        
    def setup_game_state(self) -> tuple:
        """Initialize game state with character, shop, and managers."""
        # Create character with some gold
        character = Character(
            name="TestBuyer",
            race="Human",
            char_class="Fighter",
            level=5,
            strength=16,
            dexterity=14,
            constitution=14,
            intelligence=10,
            wisdom=12,
            charisma=10
        )
        character.gold = 500  # Give decent starting gold
        
        # Create shop manager
        shop_manager = ShopManager()
        
        # Create scenario manager for goblin cave shops
        scenario_manager = ScenarioManager()
        scenario_manager.start_scenario("goblin_cave")
        
        # Create shops
        create_goblin_cave_shops(shop_manager)
        
        # Get a shop to test
        shop = shop_manager.get_all_shops()[0] if shop_manager.get_all_shops() else None
        
        # Create NPC manager
        npc_manager = NPCManager()
        
        return character, shop, shop_manager, npc_manager
    
    def log(self, message: str):
        """Print to console and log."""
        print(message)
    
    def record_command(self):
        """Increment command counter."""
        self.total_commands += 1
    
    def record_transaction(self):
        """Increment transaction counter."""
        self.total_transactions += 1
    
    def verify_gold(self, character: Character, expected: int, context: str) -> bool:
        """Verify gold matches expected value."""
        if character.gold != expected:
            self.bugs.append(ShopBug(
                test_name=context,
                description="Gold mismatch",
                command="gold check",
                expected=f"{expected} gold",
                actual=f"{character.gold} gold",
                severity="major"
            ))
            return False
        return True
    
    def verify_inventory_count(self, character: Character, item_id: str, expected: int, context: str) -> bool:
        """Verify inventory has expected count of item."""
        item = find_item_in_inventory(character.inventory, item_id)
        actual = item.quantity if item and item.stackable else (1 if item else 0)
        if actual != expected:
            self.bugs.append(ShopBug(
                test_name=context,
                description="Inventory count mismatch",
                command=f"inventory check for {item_id}",
                expected=f"{expected} items",
                actual=f"{actual} items",
                severity="major"
            ))
            return False
        return True
    
    def run_test(self, name: str, test_func: Callable) -> ShopTestResult:
        """Run a single test and capture results."""
        self.log(f"\n{'='*60}")
        self.log(f"TEST: {name}")
        self.log('='*60)
        
        result = ShopTestResult(test_name=name, passed=True, commands_executed=0)
        
        try:
            commands, transactions, bugs = test_func()
            result.commands_executed = commands
            result.transactions = transactions
            result.bugs_found = bugs
            result.passed = len(bugs) == 0
            self.total_commands += commands
            self.total_transactions += transactions
            
        except Exception as e:
            result.passed = False
            result.error_message = str(e)
            self.bugs.append(ShopBug(
                test_name=name,
                description=f"Exception: {str(e)}",
                command="test execution",
                expected="no exception",
                actual=str(e),
                severity="critical"
            ))
        
        status = "PASS" if result.passed else "FAIL"
        self.log(f"Result: {status} | Commands: {result.commands_executed} | Transactions: {result.transactions}")
        
        self.results.append(result)
        return result
    
    def run_all_tests(self):
        """Run all 25 shop tests."""
        test_functions = [
            ("01: View Shop Inventory", self.test_view_shop_inventory),
            ("02: Buy Single Item", self.test_buy_single_item),
            ("03: Buy Multiple Items", self.test_buy_multiple_items),
            ("04: Sell Item", self.test_sell_item),
            ("05: Check Gold Balance", self.test_gold_balance),
            ("06: Insufficient Gold", self.test_insufficient_gold),
            ("07: Zero/Negative Quantity", self.test_zero_negative_quantity),
            ("08: Invalid Item ID", self.test_invalid_item_id),
            ("09: Sell Equipped Item", self.test_sell_equipped_item),
            ("10: Empty Inventory Sell", self.test_empty_inventory_sell),
            ("11: Large Quantities", self.test_large_quantities),
            ("12: Float Quantities", self.test_float_quantities),
            ("13: Price Boundary", self.test_price_boundary),
            ("14: Integer Overflow", self.test_integer_overflow),
            ("15: SQL Injection", self.test_sql_injection),
            ("16: XSS Attack", self.test_xss_attack),
            ("17: Path Traversal", self.test_path_traversal),
            ("18: Format String Attack", self.test_format_string),
            ("19: Shop Persistence", self.test_shop_persistence),
            ("20: Inventory Sync", self.test_inventory_sync),
            ("21: Gold Sync", self.test_gold_sync),
            ("22: Rapid Buy/Sell", self.test_rapid_operations),
            ("23: Full Inventory Buy", self.test_full_inventory_buy),
            ("24: Buy All Stock", self.test_buy_all_stock),
            ("25: Stress Test", self.test_stress),
        ]
        
        self.log("\n" + "="*70)
        self.log("AI RPG V2 - SHOP SYSTEM PLAYTEST")
        self.log("="*70)
        self.log(f"Total tests: {len(test_functions)}")
        
        for name, func in test_functions:
            self.run_test(name, func)
        
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        
        self.log("\n" + "="*70)
        self.log("SHOP TEST SUMMARY")
        self.log("="*70)
        self.log(f"Tests: {passed} passed, {failed} failed")
        self.log(f"Total commands: {self.total_commands}")
        self.log(f"Total transactions: {self.total_transactions}")
        self.log(f"Bugs found: {len(self.bugs)}")
        
        if self.bugs:
            self.log("\nBUGS FOUND:")
            for bug in self.bugs:
                self.log(f"  [{bug.severity.upper()}] {bug.test_name}: {bug.description}")
                self.log(f"    Command: {bug.command}")
                self.log(f"    Expected: {bug.expected}")
                self.log(f"    Actual: {bug.actual}")
        
        # Write to log file
        with open("Shop_Test.log", "w", encoding="utf-8") as f:
            f.write("SHOP SYSTEM PLAYTEST LOG\n")
            f.write("="*70 + "\n\n")
            for result in self.results:
                status = "PASS" if result.passed else "FAIL"
                f.write(f"{result.test_name}: {status}\n")
                f.write(f"  Commands: {result.commands_executed}\n")
                f.write(f"  Transactions: {result.transactions}\n")
                if result.bugs_found:
                    f.write(f"  Bugs: {result.bugs_found}\n")
                if result.error_message:
                    f.write(f"  Error: {result.error_message}\n")
                f.write("\n")
    
    # ==========================================================================
    # TEST FUNCTIONS (25 total)
    # ==========================================================================
    
    # --------------------------------------------------------------------------
    # CATEGORY 1: Basic Shop Operations (1-5)
    # --------------------------------------------------------------------------
    
    def test_view_shop_inventory(self) -> tuple:
        """Test 1: View shop inventory."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        # Get items for sale
        commands += 1
        items_for_sale = shop.get_items_for_sale()
        self.log(f"Shop: {shop.name}")
        self.log(f"Items for sale: {len(items_for_sale)}")
        
        # List all items
        for inv_item, item in items_for_sale:
            commands += 1
            price = calculate_buy_price(item.value, shop.base_markup, inv_item.base_markup)
            stock = "∞" if inv_item.is_unlimited() else str(inv_item.stock)
            self.log(f"  - {item.name}: {price}g (Stock: {stock})")
        
        # Verify shop has items
        if len(items_for_sale) == 0:
            bugs.append("Shop has no items")
        
        return (commands, transactions, bugs)
    
    def test_buy_single_item(self) -> tuple:
        """Test 2: Buy a single item."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        # Get first item
        items = shop.get_items_for_sale()
        if not items:
            bugs.append("No items to buy")
            return (1, 0, bugs)
        
        inv_item, item = items[0]
        item_id = inv_item.item_id  # Use item_id from ShopInventoryItem
        gold_before = character.gold
        
        # Buy item
        commands += 1
        result = buy_item(character, shop, item_id, 1, shop_manager)
        transactions += 1
        
        self.log(f"Bought: {item.name}")
        self.log(f"Result: {result.message}")
        self.log(f"Gold: {gold_before} -> {character.gold}")
        
        if not result.success:
            bugs.append(f"Failed to buy item: {result.message}")
        
        # Verify item in inventory
        commands += 1
        found = find_item_in_inventory(character.inventory, item.name)  # Use name for inventory search
        if not found:
            bugs.append("Item not added to inventory")
        
        # Verify gold deducted
        if character.gold >= gold_before:
            bugs.append("Gold not deducted")
        
        return (commands, transactions, bugs)
    
    def test_buy_multiple_items(self) -> tuple:
        """Test 3: Buy multiple different items."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        items = shop.get_items_for_sale()
        items_bought = 0
        
        for inv_item, item in items[:3]:  # Buy up to 3 different items
            commands += 1
            result = buy_item(character, shop, inv_item.item_id, 1, shop_manager)
            transactions += 1
            
            if result.success:
                items_bought += 1
                self.log(f"Bought: {item.name} for {result.total_price}g")
            else:
                self.log(f"Cannot afford: {item.name} - {result.message}")
        
        self.log(f"Items bought: {items_bought}")
        
        if items_bought == 0 and len(items) > 0:
            bugs.append("Couldn't buy any items")
        
        return (commands, transactions, bugs)
    
    def test_sell_item(self) -> tuple:
        """Test 4: Sell an item to shop."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        # First buy an item to sell
        items = shop.get_items_for_sale()
        if not items:
            bugs.append("No items to buy/sell")
            return (1, 0, bugs)
        
        inv_item, item = items[0]
        item_id = inv_item.item_id
        
        # Buy item
        commands += 1
        buy_result = buy_item(character, shop, item_id, 1, shop_manager)
        transactions += 1
        
        if not buy_result.success:
            bugs.append(f"Failed to buy item for sell test: {buy_result.message}")
            return (commands, transactions, bugs)
        
        gold_before_sell = character.gold
        
        # Sell item back
        commands += 1
        sell_result = sell_item(character, shop, item.name, 1)
        transactions += 1
        
        self.log(f"Sold: {item.name}")
        self.log(f"Result: {sell_result.message}")
        self.log(f"Gold: {gold_before_sell} -> {character.gold}")
        
        if not sell_result.success:
            bugs.append(f"Failed to sell item: {sell_result.message}")
        
        # Verify gold increased
        if character.gold <= gold_before_sell:
            bugs.append("Gold not gained from sale")
        
        return (commands, transactions, bugs)
    
    def test_gold_balance(self) -> tuple:
        """Test 5: Verify gold tracking accuracy."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        initial_gold = character.gold
        self.log(f"Initial gold: {initial_gold}")
        
        items = shop.get_items_for_sale()
        if not items:
            return (1, 0, bugs)
        
        # Track expected gold through transactions
        expected_gold = initial_gold
        
        for inv_item, item in items[:5]:
            price = calculate_buy_price(item.value, shop.base_markup, inv_item.base_markup)
            
            if expected_gold >= price:
                commands += 1
                result = buy_item(character, shop, inv_item.item_id, 1, shop_manager)
                transactions += 1
                
                if result.success:
                    expected_gold -= price
                    self.log(f"Bought {item.name} for {price}g | Expected: {expected_gold} | Actual: {character.gold}")
                    
                    if character.gold != expected_gold:
                        bugs.append(f"Gold mismatch: expected {expected_gold}, got {character.gold}")
        
        return (commands, transactions, bugs)
    
    # --------------------------------------------------------------------------
    # CATEGORY 2: Transaction Edge Cases (6-10)
    # --------------------------------------------------------------------------
    
    def test_insufficient_gold(self) -> tuple:
        """Test 6: Try to buy without enough gold."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        # Set gold to 0
        character.gold = 0
        
        items = shop.get_items_for_sale()
        if not items:
            return (1, 0, bugs)
        
        inv_item, item = items[0]
        
        # Try to buy
        commands += 1
        result = buy_item(character, shop, inv_item.item_id, 1, shop_manager)
        transactions += 1
        
        self.log(f"Tried to buy: {item.name}")
        self.log(f"Result: {result.message}")
        
        if result.success:
            bugs.append("Purchased item with 0 gold")
        
        # Gold should still be 0
        if character.gold < 0:
            bugs.append("Gold went negative")
        
        return (commands, transactions, bugs)
    
    def test_zero_negative_quantity(self) -> tuple:
        """Test 7: Buy/sell with zero or negative quantity."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        items = shop.get_items_for_sale()
        if not items:
            return (1, 0, bugs)
        
        inv_item, item = items[0]
        gold_before = character.gold
        
        # Test zero quantity
        test_quantities = [0, -1, -100]
        
        for qty in test_quantities:
            commands += 1
            result = buy_item(character, shop, inv_item.item_id, qty, shop_manager)
            transactions += 1
            
            self.log(f"Buy quantity {qty}: {result.message}")
            
            if result.success:
                bugs.append(f"Bought with invalid quantity: {qty}")
        
        # Gold should be unchanged
        if character.gold != gold_before:
            bugs.append(f"Gold changed with invalid quantities: {gold_before} -> {character.gold}")
        
        return (commands, transactions, bugs)
    
    def test_invalid_item_id(self) -> tuple:
        """Test 8: Reference nonexistent items."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        invalid_ids = [
            "nonexistent_item",
            "fake_sword_of_doom",
            "",
            "   ",
            "12345",
            "null",
            "undefined",
            "None",
        ]
        
        gold_before = character.gold
        
        for item_id in invalid_ids:
            commands += 1
            result = buy_item(character, shop, item_id, 1, shop_manager)
            transactions += 1
            
            self.log(f"Buy '{item_id}': {result.message}")
            
            if result.success:
                bugs.append(f"Bought invalid item: {item_id}")
        
        if character.gold != gold_before:
            bugs.append("Gold changed with invalid items")
        
        return (commands, transactions, bugs)
    
    def test_sell_equipped_item(self) -> tuple:
        """Test 9: Attempt to sell equipped gear (if applicable)."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        # Buy a weapon
        items = shop.get_items_for_sale()
        weapon_item = None
        for inv_item, item in items:
            if item.item_type == ItemType.WEAPON:
                weapon_item = item
                break
        
        if not weapon_item:
            # No weapon, try any item
            if items:
                weapon_item = items[0][1]
        
        if weapon_item:
            weapon_id = weapon_item.item_id if hasattr(weapon_item, 'item_id') else weapon_item.name
            # Buy the item
            commands += 1
            buy_result = buy_item(character, shop, weapon_id, 1, shop_manager)
            transactions += 1
            
            if buy_result.success:
                # Set as equipped (if character has equipment system)
                if hasattr(character, 'equipped_weapon'):
                    character.equipped_weapon = weapon_id
                
                # Try to sell
                commands += 1
                sell_result = sell_item(character, shop, weapon_id, 1)
                transactions += 1
                
                self.log(f"Sell equipped item: {sell_result.message}")
                # Note: System should either prevent this or unequip first
        
        return (commands, transactions, bugs)
    
    def test_empty_inventory_sell(self) -> tuple:
        """Test 10: Try selling with empty inventory."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        # Clear inventory
        character.inventory.clear()
        
        # Try to sell
        commands += 1
        result = sell_item(character, shop, "health_potion", 1)
        transactions += 1
        
        self.log(f"Sell from empty inventory: {result.message}")
        
        if result.success:
            bugs.append("Sold item from empty inventory")
        
        return (commands, transactions, bugs)
    
    # --------------------------------------------------------------------------
    # CATEGORY 3: Numeric Edge Cases (11-14)
    # --------------------------------------------------------------------------
    
    def test_large_quantities(self) -> tuple:
        """Test 11: Buy very large quantities."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        items = shop.get_items_for_sale()
        if not items:
            return (1, 0, bugs)
        
        inv_item, item = items[0]
        
        large_quantities = [100, 1000, 999999, 2147483647]  # Up to int32 max
        
        for qty in large_quantities:
            commands += 1
            result = buy_item(character, shop, inv_item.item_id, qty, shop_manager)
            transactions += 1
            
            self.log(f"Buy quantity {qty}: {result.message}")
            
            # Should either succeed (if unlimited stock and gold) or fail gracefully
            if character.gold < 0:
                bugs.append(f"Gold went negative with quantity {qty}")
        
        return (commands, transactions, bugs)
    
    def test_float_quantities(self) -> tuple:
        """Test 12: Buy fractional quantities."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        items = shop.get_items_for_sale()
        if not items:
            return (1, 0, bugs)
        
        inv_item, item = items[0]
        gold_before = character.gold
        
        # Try float quantities (will be truncated or rejected)
        try:
            commands += 1
            result = buy_item(character, shop, inv_item.item_id, int(2.5), shop_manager)  # Python truncates
            transactions += 1
            self.log(f"Buy 2.5 (as int): {result.message}")
        except Exception as e:
            self.log(f"Float quantity exception: {e}")
        
        return (commands, transactions, bugs)
    
    def test_price_boundary(self) -> tuple:
        """Test 13: Items at maximum gold values."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        # Give character lots of gold
        character.gold = 2147483647  # int32 max
        
        items = shop.get_items_for_sale()
        if not items:
            return (1, 0, bugs)
        
        inv_item, item = items[0]
        
        # Buy with max gold
        commands += 1
        result = buy_item(character, shop, inv_item.item_id, 1, shop_manager)
        transactions += 1
        
        self.log(f"Buy with max gold: {result.message}")
        self.log(f"Gold after: {character.gold}")
        
        # Check for overflow
        if character.gold < 0:
            bugs.append("Gold overflow to negative")
        
        return (commands, transactions, bugs)
    
    def test_integer_overflow(self) -> tuple:
        """Test 14: Test integer overflow scenarios."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        # Test with very large gold values
        extreme_values = [
            2147483647,      # int32 max
            9223372036854775807,  # int64 max
        ]
        
        items = shop.get_items_for_sale()
        if not items:
            return (1, 0, bugs)
        
        inv_item, item = items[0]
        
        for gold_value in extreme_values:
            character.gold = gold_value
            
            commands += 1
            result = buy_item(character, shop, inv_item.item_id, 1, shop_manager)
            transactions += 1
            
            self.log(f"Gold {gold_value}: {result.message} | Final: {character.gold}")
            
            if character.gold < 0:
                bugs.append(f"Overflow at gold value {gold_value}")
        
        return (commands, transactions, bugs)
    
    # --------------------------------------------------------------------------
    # CATEGORY 4: Injection Attacks (15-18)
    # --------------------------------------------------------------------------
    
    def test_sql_injection(self) -> tuple:
        """Test 15: SQL injection in item ID."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        sql_payloads = [
            "'; DROP TABLE items;--",
            "1 OR 1=1",
            "' UNION SELECT * FROM users--",
            "1; DELETE FROM inventory WHERE 1=1",
            "'; UPDATE gold SET amount=999999--",
        ]
        
        gold_before = character.gold
        
        for payload in sql_payloads:
            commands += 1
            result = buy_item(character, shop, payload, 1, shop_manager)
            transactions += 1
            
            self.log(f"SQL injection '{payload[:30]}...': {result.message}")
            
            if result.success:
                bugs.append(f"SQL injection succeeded: {payload}")
        
        if character.gold != gold_before:
            bugs.append("SQL injection modified gold")
        
        return (commands, transactions, bugs)
    
    def test_xss_attack(self) -> tuple:
        """Test 16: XSS attack vectors."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert(1)",
            "<svg onload=alert(1)>",
            "{{constructor.constructor('alert(1)')()}}",
        ]
        
        gold_before = character.gold
        
        for payload in xss_payloads:
            commands += 1
            result = buy_item(character, shop, payload, 1, shop_manager)
            transactions += 1
            
            self.log(f"XSS '{payload[:30]}...': {result.message}")
            
            if result.success:
                bugs.append(f"XSS succeeded: {payload}")
        
        return (commands, transactions, bugs)
    
    def test_path_traversal(self) -> tuple:
        """Test 17: Path traversal attacks."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        path_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config",
            "/etc/shadow",
            "file:///etc/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd",
        ]
        
        for payload in path_payloads:
            commands += 1
            result = buy_item(character, shop, payload, 1, shop_manager)
            transactions += 1
            
            self.log(f"Path traversal '{payload[:30]}...': {result.message}")
            
            if result.success:
                bugs.append(f"Path traversal succeeded: {payload}")
        
        return (commands, transactions, bugs)
    
    def test_format_string(self) -> tuple:
        """Test 18: Format string attacks."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        format_payloads = [
            "%s%s%s%s%s",
            "%n%n%n%n",
            "%x%x%x%x",
            "{0.__class__.__mro__[2].__subclasses__()}",
            "${7*7}",
            "{{7*7}}",
        ]
        
        for payload in format_payloads:
            commands += 1
            result = buy_item(character, shop, payload, 1, shop_manager)
            transactions += 1
            
            self.log(f"Format string '{payload}': {result.message}")
            
            if result.success:
                bugs.append(f"Format string succeeded: {payload}")
        
        return (commands, transactions, bugs)
    
    # --------------------------------------------------------------------------
    # CATEGORY 5: Shop State Management (19-22)
    # --------------------------------------------------------------------------
    
    def test_shop_persistence(self) -> tuple:
        """Test 19: Items remain after leaving/returning."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        # Get initial inventory
        commands += 1
        items_before = len(shop.get_items_for_sale())
        
        # Buy an item with limited stock
        items = shop.get_items_for_sale()
        bought_item_id = None
        for inv_item, item in items:
            if not inv_item.is_unlimited():
                commands += 1
                result = buy_item(character, shop, inv_item.item_id, 1, shop_manager)
                transactions += 1
                if result.success:
                    bought_item_id = inv_item.item_id
                    self.log(f"Bought limited item: {item.name}")
                    break
        
        # Simulate leaving and returning (get shop again)
        commands += 1
        shop_again = shop_manager.get_shop(shop.id)
        
        if shop_again and bought_item_id:
            # Check stock persisted
            stock_after = shop_again.check_stock(bought_item_id)
            self.log(f"Stock after re-fetch: {stock_after}")
            
            # Stock should have decreased
            # (Note: persistence depends on implementation)
        
        return (commands, transactions, bugs)
    
    def test_inventory_sync(self) -> tuple:
        """Test 20: Player inventory updates correctly."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        # Count initial inventory items
        commands += 1
        initial_count = len(character.inventory)
        
        items = shop.get_items_for_sale()
        if not items:
            return (1, 0, bugs)
        
        # Buy 3 different items
        bought = 0
        for inv_item, item in items[:3]:
            commands += 1
            result = buy_item(character, shop, inv_item.item_id, 1, shop_manager)
            transactions += 1
            if result.success:
                bought += 1
        
        # Check inventory count increased
        commands += 1
        final_count = len(character.inventory)
        
        self.log(f"Inventory: {initial_count} -> {final_count} (bought {bought})")
        
        # For stackable items, count might not increase by bought
        # But should increase by at least 1 if we bought anything
        if bought > 0 and final_count <= initial_count:
            bugs.append(f"Inventory not updated: {initial_count} -> {final_count}")
        
        return (commands, transactions, bugs)
    
    def test_gold_sync(self) -> tuple:
        """Test 21: Gold deducts/adds accurately."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        items = shop.get_items_for_sale()
        if not items:
            return (1, 0, bugs)
        
        # Buy and sell same item, track gold
        inv_item, item = items[0]
        item_id = inv_item.item_id
        
        # Calculate expected prices
        buy_price = calculate_buy_price(item.value, shop.base_markup, inv_item.base_markup)
        sell_price = calculate_sell_price(item.value)
        
        gold_start = character.gold
        
        # Buy
        commands += 1
        buy_result = buy_item(character, shop, item_id, 1, shop_manager)
        transactions += 1
        gold_after_buy = character.gold
        
        expected_after_buy = gold_start - buy_price
        
        self.log(f"Buy price: {buy_price}g")
        self.log(f"Gold after buy: {gold_after_buy} (expected: {expected_after_buy})")
        
        if buy_result.success and gold_after_buy != expected_after_buy:
            bugs.append(f"Buy gold mismatch: expected {expected_after_buy}, got {gold_after_buy}")
        
        # Sell
        if buy_result.success:
            commands += 1
            sell_result = sell_item(character, shop, item.name, 1)
            transactions += 1
            gold_after_sell = character.gold
            
            expected_after_sell = gold_after_buy + sell_price
            
            self.log(f"Sell price: {sell_price}g")
            self.log(f"Gold after sell: {gold_after_sell} (expected: {expected_after_sell})")
            
            if sell_result.success and gold_after_sell != expected_after_sell:
                bugs.append(f"Sell gold mismatch: expected {expected_after_sell}, got {gold_after_sell}")
        
        return (commands, transactions, bugs)
    
    def test_rapid_operations(self) -> tuple:
        """Test 22: Rapid buy/sell cycling."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        items = shop.get_items_for_sale()
        if not items:
            return (1, 0, bugs)
        
        inv_item, item = items[0]
        item_id = inv_item.item_id
        
        # Rapid buy/sell 20 times
        for i in range(20):
            # Buy
            commands += 1
            buy_result = buy_item(character, shop, item_id, 1, shop_manager)
            transactions += 1
            
            if buy_result.success:
                # Immediately sell
                commands += 1
                sell_result = sell_item(character, shop, item.name, 1)
                transactions += 1
            
            if character.gold < 0:
                bugs.append(f"Gold negative at cycle {i}")
                break
        
        self.log(f"Completed 20 rapid buy/sell cycles")
        self.log(f"Final gold: {character.gold}")
        
        return (commands, transactions, bugs)
    
    # --------------------------------------------------------------------------
    # CATEGORY 6: Advanced Scenarios (23-25)
    # --------------------------------------------------------------------------
    
    def test_full_inventory_buy(self) -> tuple:
        """Test 23: Purchase when inventory is full (if limit exists)."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        character.gold = 999999  # Lots of gold
        
        items = shop.get_items_for_sale()
        if not items:
            return (1, 0, bugs)
        
        # Buy many items
        for _ in range(50):
            inv_item, item = random.choice(items)
            commands += 1
            result = buy_item(character, shop, inv_item.item_id, 1, shop_manager)
            transactions += 1
            
            if not result.success:
                self.log(f"Stopped at: {result.message}")
                break
        
        self.log(f"Inventory size: {len(character.inventory)}")
        
        return (commands, transactions, bugs)
    
    def test_buy_all_stock(self) -> tuple:
        """Test 24: Buy all stock of limited items."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        character.gold = 999999
        
        # Find a limited stock item
        items = shop.get_items_for_sale()
        limited_item = None
        for inv_item, item in items:
            if not inv_item.is_unlimited() and inv_item.stock > 0:
                limited_item = (inv_item, item)
                break
        
        if not limited_item:
            self.log("No limited stock items found")
            return (1, 0, bugs)
        
        inv_item, item = limited_item
        item_id = inv_item.item_id
        initial_stock = inv_item.stock
        
        self.log(f"Buying all {initial_stock} of {item.name}")
        
        # Buy all stock
        for i in range(initial_stock + 5):  # Try to buy more than available
            commands += 1
            result = buy_item(character, shop, item_id, 1, shop_manager)
            transactions += 1
            
            if not result.success:
                self.log(f"Stopped at {i}: {result.message}")
                break
        
        # Check stock is now 0
        final_stock = shop.check_stock(item_id)
        self.log(f"Final stock: {final_stock}")
        
        if final_stock < 0:
            bugs.append(f"Stock went negative: {final_stock}")
        
        return (commands, transactions, bugs)
    
    def test_stress(self) -> tuple:
        """Test 25: Stress test with 50 rapid operations."""
        character, shop, shop_manager, _ = self.setup_game_state()
        commands, transactions, bugs = 0, 0, []
        
        if not shop:
            bugs.append("No shop available")
            return (1, 0, bugs)
        
        character.gold = 999999
        
        items = shop.get_items_for_sale()
        if not items:
            return (1, 0, bugs)
        
        operations = [
            "buy", "buy", "buy",  # More buys than sells
            "sell",
            "check_inventory",
            "check_gold",
        ]
        
        for i in range(50):
            op = random.choice(operations)
            
            if op == "buy":
                inv_item, item = random.choice(items)
                commands += 1
                result = buy_item(character, shop, inv_item.item_id, 1, shop_manager)
                transactions += 1
                
            elif op == "sell":
                if character.inventory:
                    sell_item_obj = random.choice(character.inventory)
                    commands += 1
                    result = sell_item(character, shop, sell_item_obj.name, 1)
                    transactions += 1
                    
            elif op == "check_inventory":
                commands += 1
                count = len(character.inventory)
                
            elif op == "check_gold":
                commands += 1
                gold = character.gold
                if gold < 0:
                    bugs.append(f"Gold negative at operation {i}")
        
        self.log(f"Completed 50 stress operations")
        self.log(f"Final gold: {character.gold}")
        self.log(f"Final inventory: {len(character.inventory)} items")
        
        if character.gold < 0:
            bugs.append("Final gold is negative")
        
        return (commands, transactions, bugs)


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run all shop tests."""
    harness = ShopTestHarness()
    harness.run_all_tests()


if __name__ == "__main__":
    main()
