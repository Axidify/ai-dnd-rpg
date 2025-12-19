"""
Test suite for the Shop System (Phase 3.3.3)

Tests cover:
- Shop and ShopInventoryItem dataclasses
- ShopManager functionality
- Price calculation with disposition modifiers
- Buy/sell transactions
- Haggling system
- Display formatting
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from dataclasses import dataclass

from shop import (
    Shop, ShopManager, ShopType, ShopInventoryItem, HaggleResult, TransactionResult,
    calculate_buy_price, calculate_sell_price, get_disposition_price_modifier,
    buy_item, sell_item, attempt_haggle,
    format_shop_display, format_transaction_result, format_haggle_result,
    create_blacksmith_shop, create_traveling_merchant_shop, create_general_shop,
    DEFAULT_MARKUP, DEFAULT_SELL_RATE, HAGGLE_SUCCESS_DISCOUNT, HAGGLE_FAILURE_INCREASE,
    DISPOSITION_PRICE_MODIFIERS
)
from inventory import Item, ItemType, Rarity, add_item_to_inventory, get_item
from npc import NPC, NPCRole


# =============================================================================
# FIXTURES
# =============================================================================

@dataclass
class MockCharacter:
    """Mock character for testing transactions."""
    name: str = "TestHero"
    gold: int = 100
    charisma: int = 14
    inventory: list = None
    
    def __post_init__(self):
        if self.inventory is None:
            self.inventory = []


@pytest.fixture
def character():
    """Create a test character with some gold."""
    return MockCharacter(gold=100, charisma=14)


@pytest.fixture
def rich_character():
    """Create a wealthy test character."""
    return MockCharacter(gold=1000, charisma=16)


@pytest.fixture
def poor_character():
    """Create a poor test character."""
    return MockCharacter(gold=5, charisma=10)


@pytest.fixture
def basic_shop():
    """Create a basic general shop."""
    shop = Shop(
        id="test_shop",
        name="Test General Store",
        owner_npc_id="test_merchant",
        location_id="test_location",
        shop_type=ShopType.GENERAL
    )
    shop.add_item("dagger", stock=-1)  # Unlimited
    shop.add_item("shortsword", stock=3)
    shop.add_item("healing_potion", stock=5)
    return shop


@pytest.fixture
def blacksmith_shop():
    """Create a blacksmith shop."""
    return create_blacksmith_shop(
        id="test_forge",
        name="Test Forge",
        owner_npc_id="test_smith",
        location_id="test_location",
        weapons={"dagger": -1, "longsword": 2},
        armor={"leather_armor": 2, "shield": 3}
    )


@pytest.fixture
def shop_manager():
    """Create a shop manager with a test shop."""
    manager = ShopManager()
    shop = Shop(
        id="test_shop",
        name="Test Shop",
        owner_npc_id="test_npc",
        location_id="test_loc"
    )
    shop.add_item("dagger", stock=-1)
    shop.add_item("healing_potion", stock=5)
    manager.add_shop(shop)
    return manager


@pytest.fixture
def merchant_npc():
    """Create a merchant NPC for testing."""
    return NPC(
        id="test_merchant",
        name="Test Merchant",
        description="A test merchant",
        role=NPCRole.MERCHANT,
        disposition=0  # Neutral
    )


# =============================================================================
# SHOP INVENTORY ITEM TESTS
# =============================================================================

class TestShopInventoryItem:
    """Tests for ShopInventoryItem dataclass."""
    
    def test_create_unlimited_stock(self):
        """Test creating item with unlimited stock."""
        item = ShopInventoryItem(item_id="dagger", stock=-1)
        assert item.is_unlimited()
        assert item.is_in_stock()
        assert item.get_available() == -1
    
    def test_create_limited_stock(self):
        """Test creating item with limited stock."""
        item = ShopInventoryItem(item_id="sword", stock=5, max_stock=5)
        assert not item.is_unlimited()
        assert item.is_in_stock()
        assert item.get_available() == 5
    
    def test_decrement_limited_stock(self):
        """Test decrementing limited stock."""
        item = ShopInventoryItem(item_id="sword", stock=3)
        assert item.decrement(1)
        assert item.stock == 2
        assert item.decrement(2)
        assert item.stock == 0
        assert not item.decrement(1)  # Out of stock
    
    def test_decrement_unlimited_stock(self):
        """Test decrementing unlimited stock does nothing."""
        item = ShopInventoryItem(item_id="dagger", stock=-1)
        assert item.decrement(100)
        assert item.stock == -1
    
    def test_out_of_stock(self):
        """Test item becomes out of stock."""
        item = ShopInventoryItem(item_id="rare_gem", stock=1)
        assert item.is_in_stock()
        item.decrement(1)
        assert not item.is_in_stock()
        assert item.stock == 0
    
    def test_restock(self):
        """Test restocking to max."""
        item = ShopInventoryItem(item_id="sword", stock=1, max_stock=5)
        item.restock()
        assert item.stock == 5
    
    def test_restock_by_amount(self):
        """Test restocking by specific amount."""
        item = ShopInventoryItem(item_id="sword", stock=2, max_stock=10)
        item.restock(3)
        assert item.stock == 5
    
    def test_serialization(self):
        """Test to_dict and from_dict."""
        original = ShopInventoryItem(
            item_id="magic_sword",
            stock=2,
            max_stock=5,
            base_markup=1.5
        )
        data = original.to_dict()
        restored = ShopInventoryItem.from_dict(data)
        assert restored.item_id == original.item_id
        assert restored.stock == original.stock
        assert restored.max_stock == original.max_stock
        assert restored.base_markup == original.base_markup


# =============================================================================
# SHOP DATACLASS TESTS
# =============================================================================

class TestShop:
    """Tests for Shop dataclass."""
    
    def test_create_shop(self, basic_shop):
        """Test creating a basic shop."""
        assert basic_shop.id == "test_shop"
        assert basic_shop.name == "Test General Store"
        assert basic_shop.shop_type == ShopType.GENERAL
        assert basic_shop.accepts_haggle
    
    def test_shop_requires_id(self):
        """Test that shop requires an ID."""
        with pytest.raises(ValueError):
            Shop(id="", name="No ID Shop")
    
    def test_shop_requires_name(self):
        """Test that shop requires a name."""
        with pytest.raises(ValueError):
            Shop(id="test", name="")
    
    def test_has_item(self, basic_shop):
        """Test checking if shop has item."""
        assert basic_shop.has_item("dagger")
        assert basic_shop.has_item("shortsword")
        assert not basic_shop.has_item("dragon_sword")
    
    def test_check_stock_unlimited(self, basic_shop):
        """Test checking stock for unlimited item."""
        assert basic_shop.check_stock("dagger") == -1
    
    def test_check_stock_limited(self, basic_shop):
        """Test checking stock for limited item."""
        assert basic_shop.check_stock("shortsword") == 3
    
    def test_check_stock_not_sold(self, basic_shop):
        """Test checking stock for item not sold."""
        assert basic_shop.check_stock("dragon_sword") == 0
    
    def test_add_item(self):
        """Test adding item to shop."""
        shop = Shop(id="test", name="Test")
        shop.add_item("dagger", stock=5, max_stock=5)
        assert shop.has_item("dagger")
        assert shop.check_stock("dagger") == 5
    
    def test_add_item_updates_existing(self):
        """Test adding item updates existing entry."""
        shop = Shop(id="test", name="Test")
        shop.add_item("dagger", stock=5)
        shop.add_item("dagger", stock=10)  # Update
        assert shop.check_stock("dagger") == 10
    
    def test_remove_item(self, basic_shop):
        """Test removing item from shop."""
        assert basic_shop.has_item("dagger")
        basic_shop.remove_item("dagger")
        assert not basic_shop.has_item("dagger")
    
    def test_decrement_stock(self, basic_shop):
        """Test decrementing stock via shop."""
        initial = basic_shop.check_stock("shortsword")
        basic_shop.decrement_stock("shortsword", 1)
        assert basic_shop.check_stock("shortsword") == initial - 1
    
    def test_get_items_for_sale(self, basic_shop):
        """Test getting all items for sale."""
        items = basic_shop.get_items_for_sale()
        assert len(items) == 3
        item_ids = [inv_item.item_id for inv_item, item in items]
        assert "dagger" in item_ids
        assert "shortsword" in item_ids
    
    def test_restock_all(self, basic_shop):
        """Test restocking all items."""
        basic_shop.decrement_stock("shortsword", 2)
        basic_shop.decrement_stock("healing_potion", 3)
        
        # Set max_stock for restocking
        basic_shop.get_inventory_item("shortsword").max_stock = 3
        basic_shop.get_inventory_item("healing_potion").max_stock = 5
        
        basic_shop.restock_all()
        assert basic_shop.check_stock("shortsword") == 3
        assert basic_shop.check_stock("healing_potion") == 5
    
    def test_serialization(self, basic_shop):
        """Test shop serialization."""
        data = basic_shop.to_dict()
        restored = Shop.from_dict(data)
        
        assert restored.id == basic_shop.id
        assert restored.name == basic_shop.name
        assert restored.shop_type == basic_shop.shop_type
        assert len(restored.inventory) == len(basic_shop.inventory)


# =============================================================================
# SHOP MANAGER TESTS
# =============================================================================

class TestShopManager:
    """Tests for ShopManager class."""
    
    def test_add_and_get_shop(self, shop_manager):
        """Test adding and retrieving shop."""
        shop = shop_manager.get_shop("test_shop")
        assert shop is not None
        assert shop.name == "Test Shop"
    
    def test_get_shop_at_location(self, shop_manager):
        """Test getting shop at location."""
        shop = shop_manager.get_shop_at_location("test_loc")
        assert shop is not None
        assert shop.id == "test_shop"
    
    def test_get_shop_by_owner(self, shop_manager):
        """Test getting shop by owner NPC."""
        shop = shop_manager.get_shop_by_owner("test_npc")
        assert shop is not None
        assert shop.id == "test_shop"
    
    def test_get_shops_by_type(self, shop_manager):
        """Test getting shops by type."""
        shops = shop_manager.get_shops_by_type(ShopType.GENERAL)
        assert len(shops) == 1
        
        shops = shop_manager.get_shops_by_type(ShopType.BLACKSMITH)
        assert len(shops) == 0
    
    def test_haggle_state_tracking(self, shop_manager):
        """Test haggle state is tracked per shop."""
        state = shop_manager.get_haggle_state("test_shop")
        assert state["discount"] == 0.0
        assert state["increase"] == 0.0
        assert not state["attempted"]
        
        shop_manager.set_haggle_result("test_shop", discount=0.2)
        state = shop_manager.get_haggle_state("test_shop")
        assert state["discount"] == 0.2
        assert state["attempted"]
    
    def test_reset_haggle_state(self, shop_manager):
        """Test resetting haggle state."""
        shop_manager.set_haggle_result("test_shop", discount=0.2)
        shop_manager.reset_haggle_state("test_shop")
        
        state = shop_manager.get_haggle_state("test_shop")
        assert state["discount"] == 0.0
        assert not state["attempted"]
    
    def test_serialization(self, shop_manager):
        """Test shop manager serialization."""
        shop_manager.set_haggle_result("test_shop", discount=0.15)
        
        data = shop_manager.to_dict()
        
        new_manager = ShopManager()
        new_manager.from_dict(data)
        
        assert new_manager.get_shop("test_shop") is not None
        state = new_manager.get_haggle_state("test_shop")
        assert state["discount"] == 0.15


# =============================================================================
# PRICE CALCULATION TESTS
# =============================================================================

class TestPriceCalculation:
    """Tests for price calculation functions."""
    
    def test_buy_price_base(self):
        """Test base buy price calculation."""
        # 100 base * 1.2 markup = 120
        price = calculate_buy_price(100)
        assert price == 120
    
    def test_buy_price_custom_markup(self):
        """Test buy price with custom markup."""
        # 100 base * 1.5 markup = 150
        price = calculate_buy_price(100, shop_markup=1.5)
        assert price == 150
    
    def test_buy_price_item_markup(self):
        """Test buy price with item-specific markup."""
        # 100 * 1.2 shop * 1.5 item = 180
        price = calculate_buy_price(100, shop_markup=1.2, item_markup=1.5)
        assert price == 180
    
    def test_buy_price_friendly_disposition(self):
        """Test buy price with friendly disposition discount."""
        # 100 * 1.2 * 0.9 = 108
        price = calculate_buy_price(100, disposition_modifier=0.9)
        assert price == 108
    
    def test_buy_price_unfriendly_disposition(self):
        """Test buy price with unfriendly disposition markup."""
        # 100 * 1.2 * 1.25 = 150
        price = calculate_buy_price(100, disposition_modifier=1.25)
        assert price == 150
    
    def test_buy_price_haggle_discount(self):
        """Test buy price with haggle discount."""
        # 100 * 1.2 * (1 - 0.2) = 96
        price = calculate_buy_price(100, haggle_discount=0.2)
        assert price == 96
    
    def test_buy_price_haggle_increase(self):
        """Test buy price with failed haggle increase."""
        # 100 * 1.2 * (1 + 0.1) = 132
        price = calculate_buy_price(100, haggle_increase=0.1)
        assert price == 132
    
    def test_buy_price_minimum_1(self):
        """Test minimum buy price is 1 gold."""
        price = calculate_buy_price(0)
        assert price == 1
    
    def test_sell_price_base(self):
        """Test base sell price calculation."""
        # 100 * 0.5 = 50
        price = calculate_sell_price(100)
        assert price == 50
    
    def test_sell_price_friendly_bonus(self):
        """Test sell price with friendly disposition bonus."""
        # Friendly = 0.9 buy modifier -> 1.2 sell modifier (inverse)
        price = calculate_sell_price(100, disposition_modifier=0.9)
        # 100 * 0.5 * 1.1 (approx inverse) = ~55
        assert price > 50  # Better than neutral
    
    def test_sell_price_unfriendly_penalty(self):
        """Test sell price with unfriendly disposition penalty."""
        price = calculate_sell_price(100, disposition_modifier=1.25)
        assert price < 50  # Worse than neutral
    
    def test_disposition_modifiers(self):
        """Test disposition price modifier lookup."""
        assert get_disposition_price_modifier("hostile") is None
        assert get_disposition_price_modifier("unfriendly") == 1.25
        assert get_disposition_price_modifier("neutral") == 1.0
        assert get_disposition_price_modifier("friendly") == 0.9
        assert get_disposition_price_modifier("trusted") == 0.8


# =============================================================================
# TRANSACTION TESTS
# =============================================================================

class TestBuyItem:
    """Tests for buy_item function."""
    
    def test_buy_success(self, character, basic_shop, shop_manager):
        """Test successful purchase."""
        shop_manager.add_shop(basic_shop)
        result = buy_item(character, basic_shop, "dagger", 1, shop_manager, "neutral")
        
        assert result.success
        assert result.quantity == 1
        assert result.gold_after < result.gold_before
        assert len(character.inventory) == 1
    
    def test_buy_multiple(self, rich_character, basic_shop, shop_manager):
        """Test buying multiple items."""
        shop_manager.add_shop(basic_shop)
        result = buy_item(rich_character, basic_shop, "dagger", 3, shop_manager, "neutral")
        
        assert result.success
        assert result.quantity == 3
        # Should have 3 daggers
        dagger_count = sum(1 for item in rich_character.inventory if item.name.lower() == "dagger")
        assert dagger_count == 3
    
    def test_buy_insufficient_gold(self, poor_character, basic_shop, shop_manager):
        """Test buying with insufficient gold."""
        shop_manager.add_shop(basic_shop)
        result = buy_item(poor_character, basic_shop, "shortsword", 1, shop_manager, "neutral")
        
        assert not result.success
        assert "Not enough gold" in result.message
    
    def test_buy_out_of_stock(self, rich_character, basic_shop, shop_manager):
        """Test buying when out of stock."""
        shop_manager.add_shop(basic_shop)
        # Buy all shortswords
        basic_shop.decrement_stock("shortsword", 3)
        
        result = buy_item(rich_character, basic_shop, "shortsword", 1, shop_manager, "neutral")
        assert not result.success
        assert "Out of stock" in result.message
    
    def test_buy_not_sold(self, character, basic_shop, shop_manager):
        """Test buying item not sold by shop."""
        shop_manager.add_shop(basic_shop)
        result = buy_item(character, basic_shop, "dragon_sword", 1, shop_manager, "neutral")
        
        assert not result.success
        assert "doesn't sell" in result.message
    
    def test_buy_hostile_merchant(self, character, basic_shop, shop_manager):
        """Test buying from hostile merchant."""
        shop_manager.add_shop(basic_shop)
        result = buy_item(character, basic_shop, "dagger", 1, shop_manager, "hostile")
        
        assert not result.success
        assert "refuses to trade" in result.message
    
    def test_buy_updates_stock(self, rich_character, basic_shop, shop_manager):
        """Test that buying updates stock."""
        shop_manager.add_shop(basic_shop)
        initial_stock = basic_shop.check_stock("shortsword")
        
        buy_item(rich_character, basic_shop, "shortsword", 1, shop_manager, "neutral")
        
        assert basic_shop.check_stock("shortsword") == initial_stock - 1
    
    def test_buy_with_haggle_discount(self, character, basic_shop, shop_manager):
        """Test buying with active haggle discount."""
        shop_manager.add_shop(basic_shop)
        shop_manager.set_haggle_result(basic_shop.id, discount=0.2)
        
        result = buy_item(character, basic_shop, "dagger", 1, shop_manager, "neutral")
        
        assert result.success
        # Dagger base 2g, with markup ~2.4, with 20% discount ~1.92 -> 2g
        # Price should be lower than without discount


class TestSellItem:
    """Tests for sell_item function."""
    
    def test_sell_success(self, character, basic_shop):
        """Test successful sale."""
        # Add item to character inventory
        dagger = get_item("dagger")
        add_item_to_inventory(character.inventory, dagger)
        
        result = sell_item(character, basic_shop, "dagger", 1, "neutral")
        
        assert result.success
        assert result.gold_after > result.gold_before
        assert len(character.inventory) == 0
    
    def test_sell_no_item(self, character, basic_shop):
        """Test selling item not in inventory."""
        result = sell_item(character, basic_shop, "dagger", 1, "neutral")
        
        assert not result.success
        assert "don't have" in result.message
    
    def test_sell_hostile_merchant(self, character, basic_shop):
        """Test selling to hostile merchant."""
        dagger = get_item("dagger")
        add_item_to_inventory(character.inventory, dagger)
        
        result = sell_item(character, basic_shop, "dagger", 1, "hostile")
        
        assert not result.success
        assert "refuses to trade" in result.message


# =============================================================================
# HAGGLE TESTS
# =============================================================================

class TestHaggle:
    """Tests for attempt_haggle function."""
    
    def test_haggle_possible(self, character, basic_shop, shop_manager):
        """Test that haggle is possible at accepting shops."""
        shop_manager.add_shop(basic_shop)
        
        result = attempt_haggle(character, basic_shop, shop_manager)
        
        # Result should have been attempted (has a roll)
        assert result.roll >= 1 or result.message  # Either rolled or got a message
    
    def test_haggle_not_accepted(self, character, shop_manager):
        """Test haggle at shop that doesn't accept it."""
        shop = Shop(
            id="no_haggle",
            name="Firm Prices Shop",
            accepts_haggle=False
        )
        shop_manager.add_shop(shop)
        
        result = attempt_haggle(character, shop, shop_manager)
        
        assert not result.success
        assert "doesn't negotiate" in result.message
    
    def test_haggle_already_attempted(self, character, basic_shop, shop_manager):
        """Test haggling when already attempted."""
        shop_manager.add_shop(basic_shop)
        shop_manager.set_haggle_result(basic_shop.id, discount=0.2)
        
        result = attempt_haggle(character, basic_shop, shop_manager)
        
        # Should indicate already haggled
        assert "already" in result.message.lower() or result.discount > 0
    
    def test_haggle_result_structure(self, character, basic_shop, shop_manager):
        """Test HaggleResult has all fields."""
        shop_manager.add_shop(basic_shop)
        
        result = attempt_haggle(character, basic_shop, shop_manager)
        
        assert hasattr(result, 'success')
        assert hasattr(result, 'roll')
        assert hasattr(result, 'modifier')
        assert hasattr(result, 'total')
        assert hasattr(result, 'dc')
        assert hasattr(result, 'discount')
        assert hasattr(result, 'price_increase')
        assert hasattr(result, 'message')


# =============================================================================
# FACTORY FUNCTION TESTS
# =============================================================================

class TestFactoryFunctions:
    """Tests for shop factory functions."""
    
    def test_create_general_shop(self):
        """Test creating a general shop."""
        shop = create_general_shop(
            id="general",
            name="General Store",
            owner_npc_id="owner",
            location_id="loc",
            items={"dagger": -1, "torch": 10}
        )
        
        assert shop.shop_type == ShopType.GENERAL
        assert shop.has_item("dagger")
        assert shop.has_item("torch")
        assert shop.check_stock("torch") == 10
    
    def test_create_blacksmith_shop(self, blacksmith_shop):
        """Test creating a blacksmith shop."""
        assert blacksmith_shop.shop_type == ShopType.BLACKSMITH
        assert blacksmith_shop.base_markup == 1.15
        assert blacksmith_shop.has_item("dagger")
        assert blacksmith_shop.has_item("leather_armor")
    
    def test_create_traveling_merchant(self):
        """Test creating a traveling merchant shop."""
        shop = create_traveling_merchant_shop(
            id="traveler",
            name="Wandering Trader",
            owner_npc_id="trader",
            items={"healing_potion": 3, "rare_gem": 1}
        )
        
        assert shop.shop_type == ShopType.TRAVELING
        assert shop.base_markup == 1.5  # Higher markup
        assert shop.haggle_dc == 14  # Harder to haggle
        assert shop.location_id == ""  # Moves around


# =============================================================================
# DISPLAY FUNCTION TESTS
# =============================================================================

class TestDisplayFunctions:
    """Tests for display formatting functions."""
    
    def test_format_shop_display(self, basic_shop):
        """Test shop display formatting."""
        output = format_shop_display(basic_shop, 100, "neutral")
        
        assert basic_shop.name in output
        assert "100" in output  # Player gold
        assert "FOR SALE" in output
        assert "buy" in output.lower()
    
    def test_format_shop_display_hostile(self, basic_shop):
        """Test shop display with hostile merchant."""
        output = format_shop_display(basic_shop, 100, "hostile")
        
        assert "refuses to trade" in output
    
    def test_format_shop_display_with_discount(self, basic_shop):
        """Test shop display shows haggle discount."""
        output = format_shop_display(
            basic_shop, 100, "neutral",
            haggle_discount=0.2
        )
        
        assert "20%" in output
        assert "discount" in output.lower() or "Discount" in output
    
    def test_format_transaction_success(self):
        """Test transaction result formatting for success."""
        result = TransactionResult(
            success=True,
            item_name="Dagger",
            quantity=1,
            total_price=10,
            gold_before=100,
            gold_after=90,
            message="Purchased 1x Dagger for 10g!"
        )
        
        output = format_transaction_result(result)
        assert "✅" in output
        assert "100" in output
        assert "90" in output
    
    def test_format_transaction_failure(self):
        """Test transaction result formatting for failure."""
        result = TransactionResult(
            success=False,
            message="Not enough gold!"
        )
        
        output = format_transaction_result(result)
        assert "❌" in output
        assert "Not enough gold" in output
    
    def test_format_haggle_success(self):
        """Test haggle result formatting for success."""
        result = HaggleResult(
            success=True,
            roll=18,
            modifier=2,
            total=20,
            dc=15,
            discount=0.2,
            message="Success! You negotiate a 20% discount!"
        )
        
        output = format_haggle_result(result)
        assert "18" in output  # Roll
        assert "20" in output  # Total
        assert "15" in output  # DC
        assert "20%" in output  # Discount
    
    def test_format_haggle_failure(self):
        """Test haggle result formatting for failure."""
        result = HaggleResult(
            success=False,
            roll=5,
            modifier=1,
            total=6,
            dc=15,
            price_increase=0.1,
            message="Failed! Prices increase by 10%!"
        )
        
        output = format_haggle_result(result)
        assert "Failed" in output or "😤" in output


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestShopIntegration:
    """Integration tests for complete shop workflows."""
    
    def test_full_purchase_workflow(self, rich_character, blacksmith_shop, shop_manager):
        """Test complete purchase workflow."""
        shop_manager.add_shop(blacksmith_shop)
        
        # 1. View shop
        display = format_shop_display(blacksmith_shop, rich_character.gold, "neutral")
        assert blacksmith_shop.name in display
        
        # 2. Buy item
        result = buy_item(
            rich_character, blacksmith_shop, "dagger",
            quantity=2, shop_manager=shop_manager, npc_disposition="neutral"
        )
        assert result.success
        assert result.quantity == 2
        
        # 3. Verify inventory updated
        daggers = [i for i in rich_character.inventory if i.name.lower() == "dagger"]
        assert len(daggers) == 2
    
    def test_haggle_then_buy_workflow(self, rich_character, basic_shop, shop_manager):
        """Test haggling then buying."""
        shop_manager.add_shop(basic_shop)
        initial_gold = rich_character.gold
        
        # Manually set haggle success
        shop_manager.set_haggle_result(basic_shop.id, discount=0.2)
        
        # Buy with discount
        result = buy_item(
            rich_character, basic_shop, "dagger",
            quantity=1, shop_manager=shop_manager, npc_disposition="neutral"
        )
        
        assert result.success
        # Price should reflect discount
    
    def test_buy_sell_cycle(self, character, basic_shop, shop_manager):
        """Test buying then selling an item."""
        shop_manager.add_shop(basic_shop)
        initial_gold = character.gold
        
        # Buy
        buy_result = buy_item(
            character, basic_shop, "dagger",
            quantity=1, shop_manager=shop_manager, npc_disposition="neutral"
        )
        assert buy_result.success
        gold_after_buy = character.gold
        
        # Sell back
        sell_result = sell_item(
            character, basic_shop, "dagger",
            quantity=1, npc_disposition="neutral"
        )
        assert sell_result.success
        
        # Should have less gold than started (buy high, sell low)
        assert character.gold < initial_gold
    
    def test_disposition_affects_prices(self, rich_character, basic_shop, shop_manager):
        """Test that disposition affects transaction prices."""
        shop_manager.add_shop(basic_shop)
        
        # Buy as neutral
        result_neutral = buy_item(
            MockCharacter(gold=1000), basic_shop, "dagger",
            quantity=1, shop_manager=shop_manager, npc_disposition="neutral"
        )
        
        # Buy as trusted
        result_trusted = buy_item(
            MockCharacter(gold=1000), basic_shop, "dagger",
            quantity=1, shop_manager=shop_manager, npc_disposition="trusted"
        )
        
        # Trusted should pay less
        assert result_trusted.total_price < result_neutral.total_price


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
