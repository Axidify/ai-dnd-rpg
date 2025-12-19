"""
Shop System for AI D&D Text RPG (Phase 3.3.3)
Handles merchant shops, buying, selling, haggling, and stock management.

FEATURES:
- Shop dataclass with inventory and markup
- ShopManager for shop tracking and lookup
- Transaction functions for buy/sell/haggle
- Stock tracking with optional restock
- Disposition-based price modifiers
- Beautiful shop display formatting

ARCHITECTURE:
- Shops are separate entities from NPCs
- NPCs own shops via owner_npc_id
- Integrates with NPC disposition for pricing
- Uses central ITEMS dict from inventory.py
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Tuple, Union
import random

# Import from sibling modules
from inventory import Item, ItemType, ITEMS, add_item_to_inventory, remove_item_from_inventory, find_item_in_inventory, get_item


# =============================================================================
# CONSTANTS
# =============================================================================

# Default price modifiers
DEFAULT_MARKUP = 1.2          # 20% above base value when buying
DEFAULT_SELL_RATE = 0.5       # 50% of base value when selling
HAGGLE_SUCCESS_DISCOUNT = 0.20  # 20% discount on success
HAGGLE_FAILURE_INCREASE = 0.10  # 10% increase on failure
HAGGLE_FAILURE_DISPOSITION = -5  # Disposition penalty on failure

# Disposition-based price modifiers (multipliers)
DISPOSITION_PRICE_MODIFIERS = {
    "hostile": None,      # Won't trade
    "unfriendly": 1.25,   # +25% prices
    "neutral": 1.0,       # Normal prices
    "friendly": 0.9,      # -10% discount
    "trusted": 0.8        # -20% discount
}


# =============================================================================
# SHOP TYPE ENUM
# =============================================================================

class ShopType(Enum):
    """Types of shops with different behaviors."""
    GENERAL = auto()      # Sells various items, average markup
    BLACKSMITH = auto()   # Weapons and armor, can repair
    ALCHEMIST = auto()    # Potions and consumables
    TRAVELING = auto()    # Random inventory, higher markup
    SPECIALTY = auto()    # Specific item types only


# =============================================================================
# HAGGLE RESULT
# =============================================================================

@dataclass
class HaggleResult:
    """Result of a haggle attempt."""
    success: bool
    roll: int
    modifier: int
    total: int
    dc: int
    discount: float = 0.0      # Applied discount (0.0 to 0.20)
    price_increase: float = 0.0  # Applied price increase (0.0 to 0.10)
    message: str = ""


# =============================================================================
# TRANSACTION RESULT
# =============================================================================

@dataclass
class TransactionResult:
    """Result of a buy/sell transaction."""
    success: bool
    item_name: str = ""
    quantity: int = 0
    total_price: int = 0
    gold_before: int = 0
    gold_after: int = 0
    message: str = ""
    stock_remaining: int = -1  # -1 = unlimited


# =============================================================================
# SHOP INVENTORY ITEM
# =============================================================================

@dataclass
class ShopInventoryItem:
    """A single item in a shop's inventory with stock tracking."""
    item_id: str
    stock: int = -1           # -1 = unlimited, 0+ = current stock
    max_stock: int = -1       # -1 = unlimited, used for restocking
    base_markup: float = 1.0  # Item-specific markup multiplier
    
    def is_unlimited(self) -> bool:
        """Check if this item has unlimited stock."""
        return self.stock == -1
    
    def is_in_stock(self) -> bool:
        """Check if item is available."""
        return self.stock == -1 or self.stock > 0
    
    def get_available(self) -> int:
        """Get available quantity (-1 for unlimited)."""
        return self.stock
    
    def decrement(self, amount: int = 1) -> bool:
        """Reduce stock. Returns True if successful."""
        if self.stock == -1:
            return True  # Unlimited
        if self.stock >= amount:
            self.stock -= amount
            return True
        return False
    
    def restock(self, amount: Optional[int] = None):
        """Restock to max or by amount."""
        if self.stock == -1:
            return  # Already unlimited
        if amount is not None:
            self.stock = min(self.stock + amount, self.max_stock if self.max_stock > 0 else 999)
        elif self.max_stock > 0:
            self.stock = self.max_stock
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "item_id": self.item_id,
            "stock": self.stock,
            "max_stock": self.max_stock,
            "base_markup": self.base_markup
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ShopInventoryItem":
        """Create from dictionary."""
        return cls(
            item_id=data["item_id"],
            stock=data.get("stock", -1),
            max_stock=data.get("max_stock", -1),
            base_markup=data.get("base_markup", 1.0)
        )


# =============================================================================
# SHOP DATACLASS
# =============================================================================

@dataclass
class Shop:
    """
    Represents a merchant shop in the game world.
    
    Attributes:
        id: Unique identifier (e.g., "blacksmith_shop", "mira_trading_post")
        name: Display name (e.g., "Gavin's Forge", "Mira's Trading Post")
        owner_npc_id: ID of the NPC who owns this shop (for disposition)
        location_id: Location where this shop is found
        shop_type: Type of shop (affects behavior)
        inventory: List of items for sale with stock
        base_markup: Default price multiplier (1.2 = 20% above base)
        accepts_haggle: Whether haggling is allowed
        haggle_dc: Difficulty class for haggle attempts
    """
    id: str
    name: str
    owner_npc_id: str = ""
    location_id: str = ""
    shop_type: ShopType = ShopType.GENERAL
    inventory: List[ShopInventoryItem] = field(default_factory=list)
    base_markup: float = DEFAULT_MARKUP
    accepts_haggle: bool = True
    haggle_dc: int = 12
    
    def __post_init__(self):
        """Validate shop data."""
        if not self.id:
            raise ValueError("Shop must have an id")
        if not self.name:
            raise ValueError("Shop must have a name")
    
    def get_inventory_item(self, item_id: str) -> Optional[ShopInventoryItem]:
        """Get a shop inventory item by ID."""
        for inv_item in self.inventory:
            if inv_item.item_id == item_id:
                return inv_item
        return None
    
    def has_item(self, item_id: str) -> bool:
        """Check if shop sells this item."""
        inv_item = self.get_inventory_item(item_id)
        return inv_item is not None and inv_item.is_in_stock()
    
    def check_stock(self, item_id: str) -> int:
        """Check stock for an item. Returns -1 for unlimited, 0 if not sold/out."""
        inv_item = self.get_inventory_item(item_id)
        if inv_item is None:
            return 0
        return inv_item.get_available()
    
    def decrement_stock(self, item_id: str, amount: int = 1) -> bool:
        """Reduce stock for an item after purchase."""
        inv_item = self.get_inventory_item(item_id)
        if inv_item is None:
            return False
        return inv_item.decrement(amount)
    
    def add_item(self, item_id: str, stock: int = -1, max_stock: int = -1, markup: float = 1.0):
        """Add an item to the shop's inventory."""
        # Check if item already exists
        existing = self.get_inventory_item(item_id)
        if existing:
            if stock > 0:
                existing.stock = stock
            if max_stock > 0:
                existing.max_stock = max_stock
            existing.base_markup = markup
        else:
            self.inventory.append(ShopInventoryItem(
                item_id=item_id,
                stock=stock,
                max_stock=max_stock,
                base_markup=markup
            ))
    
    def remove_item(self, item_id: str) -> bool:
        """Remove an item from the shop's inventory."""
        for i, inv_item in enumerate(self.inventory):
            if inv_item.item_id == item_id:
                self.inventory.pop(i)
                return True
        return False
    
    def restock_all(self):
        """Restock all items to their max stock."""
        for inv_item in self.inventory:
            inv_item.restock()
    
    def get_items_for_sale(self) -> List[Tuple[ShopInventoryItem, Item]]:
        """Get all in-stock items with their Item definitions."""
        result = []
        for inv_item in self.inventory:
            if inv_item.is_in_stock():
                item = get_item(inv_item.item_id)
                if item:
                    result.append((inv_item, item))
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert shop to dictionary for saving."""
        return {
            "id": self.id,
            "name": self.name,
            "owner_npc_id": self.owner_npc_id,
            "location_id": self.location_id,
            "shop_type": self.shop_type.name,
            "inventory": [inv.to_dict() for inv in self.inventory],
            "base_markup": self.base_markup,
            "accepts_haggle": self.accepts_haggle,
            "haggle_dc": self.haggle_dc
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Shop":
        """Create shop from dictionary (for loading)."""
        shop_type = ShopType[data.get("shop_type", "GENERAL")]
        inventory = [ShopInventoryItem.from_dict(inv) for inv in data.get("inventory", [])]
        
        return cls(
            id=data["id"],
            name=data["name"],
            owner_npc_id=data.get("owner_npc_id", ""),
            location_id=data.get("location_id", ""),
            shop_type=shop_type,
            inventory=inventory,
            base_markup=data.get("base_markup", DEFAULT_MARKUP),
            accepts_haggle=data.get("accepts_haggle", True),
            haggle_dc=data.get("haggle_dc", 12)
        )


# =============================================================================
# SHOP MANAGER
# =============================================================================

class ShopManager:
    """
    Manages all shops in the game world.
    Handles shop lookup, state tracking, and persistence.
    """
    
    def __init__(self):
        self._shops: Dict[str, Shop] = {}
        self._haggle_state: Dict[str, Dict[str, Any]] = {}  # shop_id -> {discount, increase, attempted}
    
    def add_shop(self, shop: Shop):
        """Add a shop to the manager."""
        self._shops[shop.id] = shop
        # Initialize haggle state
        self._haggle_state[shop.id] = {"discount": 0.0, "increase": 0.0, "attempted": False}
    
    def get_shop(self, shop_id: str) -> Optional[Shop]:
        """Get a shop by ID."""
        return self._shops.get(shop_id)
    
    def get_shop_at_location(self, location_id: str) -> Optional[Shop]:
        """Get shop at a specific location."""
        for shop in self._shops.values():
            if shop.location_id == location_id:
                return shop
        return None
    
    def get_shop_by_owner(self, npc_id: str) -> Optional[Shop]:
        """Get shop owned by a specific NPC."""
        for shop in self._shops.values():
            if shop.owner_npc_id == npc_id:
                return shop
        return None
    
    def get_shops_by_type(self, shop_type: ShopType) -> List[Shop]:
        """Get all shops of a specific type."""
        return [shop for shop in self._shops.values() if shop.shop_type == shop_type]
    
    def get_all_shops(self) -> List[Shop]:
        """Get all shops."""
        return list(self._shops.values())
    
    def get_haggle_state(self, shop_id: str) -> Dict[str, Any]:
        """Get haggle state for a shop."""
        if shop_id not in self._haggle_state:
            self._haggle_state[shop_id] = {"discount": 0.0, "increase": 0.0, "attempted": False}
        return self._haggle_state[shop_id]
    
    def set_haggle_result(self, shop_id: str, discount: float = 0.0, increase: float = 0.0):
        """Set haggle result for a shop."""
        self._haggle_state[shop_id] = {
            "discount": discount,
            "increase": increase,
            "attempted": True
        }
    
    def reset_haggle_state(self, shop_id: Optional[str] = None):
        """Reset haggle state for one or all shops."""
        if shop_id:
            self._haggle_state[shop_id] = {"discount": 0.0, "increase": 0.0, "attempted": False}
        else:
            for sid in self._haggle_state:
                self._haggle_state[sid] = {"discount": 0.0, "increase": 0.0, "attempted": False}
    
    def restock_all_shops(self):
        """Restock all shops (call on rest/new day)."""
        for shop in self._shops.values():
            shop.restock_all()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert shop manager state to dictionary for saving."""
        return {
            "shops": {shop_id: shop.to_dict() for shop_id, shop in self._shops.items()},
            "haggle_state": self._haggle_state.copy()
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Restore shop manager state from dictionary."""
        self._shops.clear()
        self._haggle_state.clear()
        
        for shop_id, shop_data in data.get("shops", {}).items():
            self._shops[shop_id] = Shop.from_dict(shop_data)
        
        self._haggle_state = data.get("haggle_state", {})


# =============================================================================
# PRICE CALCULATION FUNCTIONS
# =============================================================================

def calculate_buy_price(
    base_value: int,
    shop_markup: float = DEFAULT_MARKUP,
    item_markup: float = 1.0,
    disposition_modifier: float = 1.0,
    haggle_discount: float = 0.0,
    haggle_increase: float = 0.0
) -> int:
    """
    Calculate the price to buy an item from a shop.
    
    Formula: base_value * shop_markup * item_markup * disposition * (1 - discount + increase)
    
    Args:
        base_value: Item's base gold value
        shop_markup: Shop's general markup (default 1.2 = 20% higher)
        item_markup: Individual item markup multiplier
        disposition_modifier: Based on NPC disposition (0.8 to 1.25)
        haggle_discount: Discount from successful haggle (0.0 to 0.20)
        haggle_increase: Price increase from failed haggle (0.0 to 0.10)
    
    Returns:
        Final price in gold (minimum 1)
    """
    price = base_value * shop_markup * item_markup * disposition_modifier
    price = price * (1.0 - haggle_discount + haggle_increase)
    return max(1, int(price))


def calculate_sell_price(
    base_value: int,
    sell_rate: float = DEFAULT_SELL_RATE,
    disposition_modifier: float = 1.0
) -> int:
    """
    Calculate the price to sell an item to a shop.
    
    Formula: base_value * sell_rate * disposition_modifier
    
    Args:
        base_value: Item's base gold value
        sell_rate: Shop's buy rate (default 0.5 = 50% of value)
        disposition_modifier: Bonus from friendly disposition (inverse of buy modifier)
    
    Returns:
        Sell price in gold (minimum 1)
    """
    # Invert disposition modifier for selling (friendly = better sell price)
    if disposition_modifier > 1.0:
        # Unfriendly - worse sell price
        sell_modifier = 2.0 - disposition_modifier  # 1.25 -> 0.75
    elif disposition_modifier < 1.0:
        # Friendly - better sell price
        sell_modifier = 2.0 - disposition_modifier  # 0.8 -> 1.2
    else:
        sell_modifier = 1.0
    
    price = base_value * sell_rate * sell_modifier
    return max(1, int(price))


def get_disposition_price_modifier(disposition_level: str) -> Optional[float]:
    """
    Get price modifier based on NPC disposition level.
    
    Returns:
        Float multiplier, or None if NPC won't trade (hostile)
    """
    return DISPOSITION_PRICE_MODIFIERS.get(disposition_level, 1.0)


# =============================================================================
# TRANSACTION FUNCTIONS
# =============================================================================

def buy_item(
    character,  # Character object
    shop: Shop,
    item_id: str,
    quantity: int = 1,
    shop_manager: Optional[ShopManager] = None,
    npc_disposition: str = "neutral"
) -> TransactionResult:
    """
    Process buying an item from a shop.
    
    Args:
        character: Player character with gold and inventory
        shop: Shop to buy from
        item_id: ID of item to purchase
        quantity: Number to buy
        shop_manager: For haggle state (optional)
        npc_disposition: Disposition level of shop owner
    
    Returns:
        TransactionResult with success/failure info
    """
    # Validate quantity
    if quantity <= 0:
        return TransactionResult(
            success=False,
            message="Invalid quantity"
        )
    
    if quantity > 99:
        return TransactionResult(
            success=False,
            message="Maximum 99 items per purchase"
        )
    
    # Get disposition modifier
    disp_modifier = get_disposition_price_modifier(npc_disposition)
    if disp_modifier is None:
        return TransactionResult(
            success=False,
            message=f"The merchant refuses to trade with you!"
        )
    
    # Check if item is for sale
    inv_item = shop.get_inventory_item(item_id)
    if inv_item is None:
        return TransactionResult(
            success=False,
            message=f"This shop doesn't sell that item."
        )
    
    # Check stock
    if not inv_item.is_unlimited():
        if inv_item.stock < quantity:
            if inv_item.stock == 0:
                return TransactionResult(
                    success=False,
                    message=f"Out of stock!"
                )
            return TransactionResult(
                success=False,
                message=f"Only {inv_item.stock} in stock."
            )
    
    # Get item definition
    item = get_item(item_id)
    if item is None:
        return TransactionResult(
            success=False,
            message=f"Item not found in database."
        )
    
    # Get haggle state
    haggle_discount = 0.0
    haggle_increase = 0.0
    if shop_manager:
        haggle_state = shop_manager.get_haggle_state(shop.id)
        haggle_discount = haggle_state.get("discount", 0.0)
        haggle_increase = haggle_state.get("increase", 0.0)
    
    # Calculate price
    unit_price = calculate_buy_price(
        base_value=item.value,
        shop_markup=shop.base_markup,
        item_markup=inv_item.base_markup,
        disposition_modifier=disp_modifier,
        haggle_discount=haggle_discount,
        haggle_increase=haggle_increase
    )
    total_price = unit_price * quantity
    
    # Check if player can afford
    gold_before = character.gold
    if gold_before < total_price:
        affordable = gold_before // unit_price if unit_price > 0 else 0
        if affordable > 0:
            return TransactionResult(
                success=False,
                gold_before=gold_before,
                message=f"Not enough gold! Need {total_price}g, have {gold_before}g. You can afford {affordable}."
            )
        return TransactionResult(
            success=False,
            gold_before=gold_before,
            message=f"Not enough gold! Need {total_price}g, have {gold_before}g."
        )
    
    # Process purchase
    character.gold -= total_price
    
    # Add item(s) to inventory
    for _ in range(quantity):
        add_item_to_inventory(character.inventory, item)
    
    # Decrement shop stock
    shop.decrement_stock(item_id, quantity)
    
    # Get remaining stock
    stock_remaining = shop.check_stock(item_id)
    
    return TransactionResult(
        success=True,
        item_name=item.name,
        quantity=quantity,
        total_price=total_price,
        gold_before=gold_before,
        gold_after=character.gold,
        stock_remaining=stock_remaining,
        message=f"Purchased {quantity}x {item.name} for {total_price}g!"
    )


def sell_item(
    character,  # Character object
    shop: Shop,
    item_id: str,
    quantity: int = 1,
    npc_disposition: str = "neutral"
) -> TransactionResult:
    """
    Process selling an item to a shop.
    
    Args:
        character: Player character with gold and inventory
        shop: Shop to sell to
        item_id: ID of item to sell
        quantity: Number to sell
        npc_disposition: Disposition level of shop owner
    
    Returns:
        TransactionResult with success/failure info
    """
    # Get disposition modifier
    disp_modifier = get_disposition_price_modifier(npc_disposition)
    if disp_modifier is None:
        return TransactionResult(
            success=False,
            message=f"The merchant refuses to trade with you!"
        )
    
    # Find item in player inventory
    item = find_item_in_inventory(character.inventory, item_id)
    if item is None:
        return TransactionResult(
            success=False,
            message=f"You don't have that item."
        )
    
    # Check quantity (for stackable items)
    available = item.quantity if item.stackable else 1
    if available < quantity:
        return TransactionResult(
            success=False,
            message=f"You only have {available}."
        )
    
    # Calculate sell price
    unit_price = calculate_sell_price(
        base_value=item.value,
        disposition_modifier=disp_modifier
    )
    total_price = unit_price * quantity
    
    # Process sale
    gold_before = character.gold
    character.gold += total_price
    
    # Remove from inventory
    for _ in range(quantity):
        remove_item_from_inventory(character.inventory, item_id)
    
    return TransactionResult(
        success=True,
        item_name=item.name,
        quantity=quantity,
        total_price=total_price,
        gold_before=gold_before,
        gold_after=character.gold,
        message=f"Sold {quantity}x {item.name} for {total_price}g!"
    )


def attempt_haggle(
    character,  # Character object (needs charisma stat)
    shop: Shop,
    shop_manager: ShopManager,
    npc=None  # NPC object for disposition change
) -> HaggleResult:
    """
    Attempt to haggle for better prices.
    
    Args:
        character: Player character with charisma
        shop: Shop to haggle at
        shop_manager: For tracking haggle state
        npc: Shop owner NPC (optional, for disposition change)
    
    Returns:
        HaggleResult with roll details and outcome
    """
    # Check if already haggled
    haggle_state = shop_manager.get_haggle_state(shop.id)
    if haggle_state.get("attempted", False):
        if haggle_state.get("discount", 0) > 0:
            return HaggleResult(
                success=True,
                roll=0,
                modifier=0,
                total=0,
                dc=shop.haggle_dc,
                discount=haggle_state["discount"],
                message=f"You already have a {int(haggle_state['discount']*100)}% discount here!"
            )
        else:
            return HaggleResult(
                success=False,
                roll=0,
                modifier=0,
                total=0,
                dc=shop.haggle_dc,
                price_increase=haggle_state.get("increase", 0),
                message="The merchant won't negotiate further after your previous attempt."
            )
    
    # Check if shop accepts haggling
    if not shop.accepts_haggle:
        return HaggleResult(
            success=False,
            roll=0,
            modifier=0,
            total=0,
            dc=shop.haggle_dc,
            message="This merchant doesn't negotiate prices."
        )
    
    # Roll charisma check
    roll = random.randint(1, 20)
    cha_mod = (character.charisma - 10) // 2
    total = roll + cha_mod
    dc = shop.haggle_dc
    
    if total >= dc:
        # Success!
        shop_manager.set_haggle_result(shop.id, discount=HAGGLE_SUCCESS_DISCOUNT, increase=0.0)
        return HaggleResult(
            success=True,
            roll=roll,
            modifier=cha_mod,
            total=total,
            dc=dc,
            discount=HAGGLE_SUCCESS_DISCOUNT,
            message=f"Success! You negotiate a {int(HAGGLE_SUCCESS_DISCOUNT*100)}% discount!"
        )
    else:
        # Failure
        shop_manager.set_haggle_result(shop.id, discount=0.0, increase=HAGGLE_FAILURE_INCREASE)
        
        # Disposition penalty
        if npc is not None:
            npc.modify_disposition(HAGGLE_FAILURE_DISPOSITION)
        
        return HaggleResult(
            success=False,
            roll=roll,
            modifier=cha_mod,
            total=total,
            dc=dc,
            price_increase=HAGGLE_FAILURE_INCREASE,
            message=f"Failed! Prices increase by {int(HAGGLE_FAILURE_INCREASE*100)}%!"
        )


# =============================================================================
# DISPLAY FUNCTIONS
# =============================================================================

def format_shop_display(
    shop: Shop,
    player_gold: int,
    disposition_level: str = "neutral",
    haggle_discount: float = 0.0,
    haggle_increase: float = 0.0
) -> str:
    """
    Format shop inventory for display.
    
    Args:
        shop: Shop to display
        player_gold: Player's current gold
        disposition_level: For price calculation
        haggle_discount: Current haggle discount
        haggle_increase: Current price increase from failed haggle
    
    Returns:
        Formatted string with shop inventory
    """
    lines = []
    
    # Header
    lines.append("┌" + "─" * 58 + "┐")
    lines.append(f"│ 🛒 {shop.name:<53} │")
    lines.append(f"│ 💰 Your Gold: {player_gold:<43} │")
    lines.append("├" + "─" * 58 + "┤")
    
    # Price modifiers info
    disp_mod = get_disposition_price_modifier(disposition_level)
    if disp_mod is None:
        lines.append("│ ⚠️  The merchant refuses to trade with you!              │")
        lines.append("└" + "─" * 58 + "┘")
        return "\n".join(lines)
    
    if haggle_discount > 0:
        lines.append(f"│ ✨ Haggle Discount: {int(haggle_discount*100)}% off!{' ' * 33} │")
    elif haggle_increase > 0:
        lines.append(f"│ ⚠️  Price Increase: +{int(haggle_increase*100)}%{' ' * 34} │")
    
    if disposition_level == "friendly":
        lines.append(f"│ 🤝 Friendly Discount: 10% off{' ' * 27} │")
    elif disposition_level == "trusted":
        lines.append(f"│ 💎 Trusted Customer: 20% off{' ' * 28} │")
    elif disposition_level == "unfriendly":
        lines.append(f"│ 😒 Unfriendly Markup: +25%{' ' * 30} │")
    
    lines.append("│" + " " * 58 + "│")
    lines.append("│ FOR SALE:" + " " * 48 + "│")
    
    # Items
    items_for_sale = shop.get_items_for_sale()
    if not items_for_sale:
        lines.append("│   (Nothing in stock)" + " " * 36 + "│")
    else:
        for i, (inv_item, item) in enumerate(items_for_sale, 1):
            # Calculate display price
            price = calculate_buy_price(
                base_value=item.value,
                shop_markup=shop.base_markup,
                item_markup=inv_item.base_markup,
                disposition_modifier=disp_mod,
                haggle_discount=haggle_discount,
                haggle_increase=haggle_increase
            )
            
            # Stock display
            if inv_item.is_unlimited():
                stock_str = ""
            else:
                stock_str = f" (x{inv_item.stock})"
            
            # Affordability marker
            afford = "✓" if player_gold >= price else "✗"
            
            # Build stats string for weapons/armor
            stats_str = ""
            if hasattr(item, 'damage_dice') and item.damage_dice:
                stats_str = f"[DMG: {item.damage_dice}]"
            elif hasattr(item, 'ac_bonus') and item.ac_bonus:
                stats_str = f"[AC: +{item.ac_bonus}]"
            elif hasattr(item, 'heal_amount') and item.heal_amount:
                stats_str = f"[HEAL: {item.heal_amount}]"
            
            # Format item line with stats
            item_name = f"{i}. {item.name}{stock_str}"
            price_str = f"{price}g {afford}"
            
            if stats_str:
                # Include stats after name
                name_with_stats = f"{item_name} {stats_str}"
                dots = "." * max(1, 50 - len(name_with_stats) - len(price_str))
                lines.append(f"│   {name_with_stats}{dots}{price_str} │")
            else:
                dots = "." * (50 - len(item_name) - len(price_str))
                lines.append(f"│   {item_name}{dots}{price_str} │")
            
            # Description (truncated)
            desc = item.description[:50] + "..." if len(item.description) > 50 else item.description
            lines.append(f"│      ({desc}){' ' * (52 - len(desc))} │")
    
    lines.append("├" + "─" * 58 + "┤")
    lines.append("│ Commands: buy <item>, sell <item>, haggle, leave        │")
    lines.append("└" + "─" * 58 + "┘")
    
    return "\n".join(lines)


def format_transaction_result(result: TransactionResult) -> str:
    """Format a transaction result for display."""
    if result.success:
        lines = [
            f"✅ {result.message}",
            f"💰 Gold: {result.gold_before}g → {result.gold_after}g"
        ]
        if result.stock_remaining >= 0:
            lines.append(f"📦 Stock remaining: {result.stock_remaining}")
        return "\n".join(lines)
    else:
        return f"❌ {result.message}"


def format_haggle_result(result: HaggleResult) -> str:
    """Format a haggle result for display."""
    if result.roll == 0:
        # Already attempted or not allowed
        return f"{'✅' if result.success else '❌'} {result.message}"
    
    lines = [
        "🗣️ Haggling...",
        f"📋 Charisma Check (DC {result.dc})",
        f"🎲 Roll: [{result.roll}]{'+' if result.modifier >= 0 else ''}{result.modifier} = {result.total}"
    ]
    
    if result.success:
        lines.append(f"✨ {result.message}")
    else:
        lines.append(f"😤 {result.message}")
    
    return "\n".join(lines)


# =============================================================================
# SHOP FACTORY FUNCTIONS
# =============================================================================

def create_general_shop(
    id: str,
    name: str,
    owner_npc_id: str,
    location_id: str,
    items: Dict[str, int],  # item_id -> stock (-1 for unlimited)
    markup: float = 1.2
) -> Shop:
    """
    Factory function to create a general store.
    
    Args:
        id: Shop ID
        name: Display name
        owner_npc_id: Owning NPC ID
        location_id: Location ID
        items: Dict of item_id -> stock count
        markup: Base price markup
    
    Returns:
        Configured Shop object
    """
    shop = Shop(
        id=id,
        name=name,
        owner_npc_id=owner_npc_id,
        location_id=location_id,
        shop_type=ShopType.GENERAL,
        base_markup=markup,
        accepts_haggle=True
    )
    
    for item_id, stock in items.items():
        shop.add_item(item_id, stock=stock, max_stock=stock)
    
    return shop


def create_blacksmith_shop(
    id: str,
    name: str,
    owner_npc_id: str,
    location_id: str,
    weapons: Dict[str, int],
    armor: Dict[str, int],
    markup: float = 1.15  # Blacksmiths are usually fair
) -> Shop:
    """Factory function to create a blacksmith shop."""
    shop = Shop(
        id=id,
        name=name,
        owner_npc_id=owner_npc_id,
        location_id=location_id,
        shop_type=ShopType.BLACKSMITH,
        base_markup=markup,
        accepts_haggle=True
    )
    
    for item_id, stock in weapons.items():
        shop.add_item(item_id, stock=stock, max_stock=stock)
    
    for item_id, stock in armor.items():
        shop.add_item(item_id, stock=stock, max_stock=stock)
    
    return shop


def create_traveling_merchant_shop(
    id: str,
    name: str,
    owner_npc_id: str,
    items: Dict[str, int],
    markup: float = 1.5  # Traveling merchants charge more
) -> Shop:
    """Factory function to create a traveling merchant's shop."""
    shop = Shop(
        id=id,
        name=name,
        owner_npc_id=owner_npc_id,
        location_id="",  # Moves around
        shop_type=ShopType.TRAVELING,
        base_markup=markup,
        accepts_haggle=True,
        haggle_dc=14  # Traveling merchants are shrewd
    )
    
    for item_id, stock in items.items():
        shop.add_item(item_id, stock=stock, max_stock=stock)
    
    return shop
