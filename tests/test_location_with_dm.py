"""
Location System + AI DM Integration Test
Test how location exploration integrates with the AI Dungeon Master.
Includes event system testing (Phase 3.2.1).
Now with narrative location descriptions (Priority 4).

Run with: python tests/test_location_with_dm.py
"""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
import google.generativeai as genai
from scenario import (
    Location, LocationManager, LocationEvent, EventTrigger,
    ExitCondition, check_exit_condition,
    create_goblin_cave_scenario
)
from inventory import get_item, add_item_to_inventory, Item, ItemType, ITEMS
from dm_engine import (
    build_location_context_full as build_location_context,
    get_location_narration, display_location_narration
)

# Load environment variables
load_dotenv()


# =============================================================================
# MOCK CHARACTER (Simple)
# =============================================================================

class MockCharacter:
    """Simple mock character for location testing."""
    def __init__(self):
        self.name = "Kira"
        self.char_class = "Fighter"
        self.max_hp = 12
        self.current_hp = 12
        self.gold = 10
        self.inventory = []
        
    def get_ability_modifier(self, ability_name):
        """Return modifier for ability checks."""
        return 2  # Default +2 for testing


# =============================================================================
# TEST LOCATION SETUP
# =============================================================================

def create_test_location_manager() -> LocationManager:
    """Create a location manager with test locations."""
    manager = LocationManager()
    
    # Tavern location with items and NPCs
    tavern = Location(
        id="tavern",
        name="The Rusty Dragon",
        description="A cozy tavern with a crackling hearth. Wooden tables are scattered about.",
        exits={"door": "street", "bar": "tavern_bar"},
        npcs=["barkeep", "bram"],
        items=["torch", "healing_potion"],
        atmosphere="Warm firelight, murmured conversations, smell of ale and stew",
        enter_text="You push through the tavern door, warmth washing over you."
    )
    
    # Bar area
    tavern_bar = Location(
        id="tavern_bar",
        name="The Rusty Dragon - Bar",
        description="A worn wooden bar with bottles lining the shelves.",
        exits={"main room": "tavern"},
        npcs=["barkeep"],
        items=["rope"],
        atmosphere="Clinking glasses, the barkeep's watchful eye"
    )
    
    # Street with treasure
    street = Location(
        id="street",
        name="Village Street",
        description="A quiet village street with a few shops closed for the night.",
        exits={"tavern": "tavern", "north": "forest"},
        npcs=[],
        items=["gold_pouch_small"],
        atmosphere="Cool evening air, distant sounds of village life"
    )
    
    # Forest
    forest = Location(
        id="forest",
        name="Dark Forest",
        description="A winding path through ancient trees. Shadows dance in the moonlight.",
        exits={"south": "street", "deeper": "cave"},
        npcs=["merchant"],
        items=["rations", "dagger"],
        atmosphere="Rustling leaves, distant animal sounds, growing darkness",
        events=[
            LocationEvent(
                id="forest_ambush",
                trigger=EventTrigger.ON_FIRST_VISIT,
                narration="You hear rustling in the bushes - something is watching you!",
                effect=None,
                one_time=True
            )
        ]
    )
    
    # Cave with boss loot and trap
    cave = Location(
        id="cave",
        name="Goblin Cave Entrance",
        description="A dark cave mouth. The smell of goblins wafts from within.",
        exits={"forest": "forest"},
        npcs=[],
        items=["gold_pouch", "longsword", "poison_vial"],
        atmosphere="Foul smell, echoing sounds, sense of danger",
        events=[
            LocationEvent(
                id="cave_trap",
                trigger=EventTrigger.ON_FIRST_VISIT,
                narration="A tripwire! You barely spot it before stepping on it.",
                effect="skill_check:dex:12|damage:1d4",
                one_time=True
            ),
            LocationEvent(
                id="cave_discovery",
                trigger=EventTrigger.ON_FIRST_VISIT,
                narration="Among the bones at the entrance, you notice a glint of gold.",
                effect=None,
                one_time=True
            )
        ]
    )
    
    manager.add_location(tavern)
    manager.add_location(tavern_bar)
    manager.add_location(street)
    manager.add_location(forest)
    manager.add_location(cave)
    
    manager.set_available_locations(["tavern", "tavern_bar", "street", "forest", "cave"])
    manager.set_current_location("tavern")
    
    return manager


# =============================================================================
# UNIT TESTS
# =============================================================================

def test_look_command_display():
    """Test that look command shows items and NPCs correctly."""
    print("\n" + "=" * 60)
    print("     LOOK COMMAND DISPLAY TESTS")
    print("=" * 60)
    
    manager = create_test_location_manager()
    location = manager.get_current_location()
    
    # Test items display (now title-cased for user-friendly display)
    items_display = location.get_items_display()
    assert "🎒" in items_display, "Items display should have backpack emoji"
    assert "Torch" in items_display, "Should show Torch (title-cased)"
    assert "Healing Potion" in items_display, "Should show Healing Potion (title-cased)"
    print(f"✅ Items display: {items_display}")
    
    # Test NPCs display
    npcs_display = location.get_npcs_display()
    assert "👤" in npcs_display, "NPCs display should have person emoji"
    assert "Barkeep" in npcs_display, "Should show Barkeep (capitalized)"
    assert "Bram" in npcs_display, "Should show Bram (capitalized)"
    print(f"✅ NPCs display: {npcs_display}")
    
    # Test full look output
    print(f"\n📍 {location.name}")
    print(f"  {location.description}")
    if location.atmosphere:
        print(f"  ({location.atmosphere})")
    if items_display:
        print(f"  {items_display}")
    if npcs_display:
        print(f"  {npcs_display}")
    print(f"  {location.get_exits_display()}")
    
    print("\n✅ Look command display test passed!")


def test_take_command():
    """Test taking items from locations."""
    print("\n" + "=" * 60)
    print("     TAKE COMMAND TESTS")
    print("=" * 60)
    
    manager = create_test_location_manager()
    character = MockCharacter()
    location = manager.get_current_location()
    
    # Test taking an item
    assert location.has_item("torch"), "Tavern should have torch"
    item = get_item("torch")
    assert item is not None, "Torch should exist in ITEMS database"
    
    # Simulate take command
    location.remove_item("torch")
    msg = add_item_to_inventory(character.inventory, item)
    
    assert not location.has_item("torch"), "Torch should be removed from location"
    assert len(character.inventory) == 1, "Inventory should have 1 item"
    assert character.inventory[0].name == "Torch", "Item should be Torch"
    
    print(f"✅ Take: {msg}")
    print(f"✅ Location items remaining: {location.items}")
    print(f"✅ Inventory: {[i.name for i in character.inventory]}")
    
    print("\n✅ Take command test passed!")


def test_take_nonexistent_item():
    """Test taking an item that doesn't exist."""
    print("\n" + "=" * 60)
    print("     TAKE NONEXISTENT ITEM TEST")
    print("=" * 60)
    
    manager = create_test_location_manager()
    location = manager.get_current_location()
    
    # Try to take something not there
    assert not location.has_item("sword"), "Tavern should not have sword"
    print("✅ has_item('sword') correctly returns False")
    
    # Test case insensitivity
    assert location.has_item("TORCH"), "has_item should be case insensitive"
    assert location.has_item("Torch"), "has_item should be case insensitive"
    print("✅ has_item is case insensitive")
    
    print("\n✅ Nonexistent item test passed!")


def test_gold_pouch_handling():
    """Test that gold pouches add gold directly to character."""
    print("\n" + "=" * 60)
    print("     GOLD POUCH HANDLING TESTS")
    print("=" * 60)
    
    manager = create_test_location_manager()
    character = MockCharacter()
    
    # Move to street where gold_pouch_small is
    manager.set_current_location("street")
    location = manager.get_current_location()
    
    assert location.has_item("gold_pouch_small"), "Street should have gold pouch"
    
    # Get the gold pouch item
    item = get_item("gold_pouch_small")
    assert item is not None, "gold_pouch_small should exist in ITEMS"
    
    print(f"  Item: {item.name}")
    print(f"  Value: {item.value} gold")
    print(f"  Effect: {item.effect}")
    
    # Test gold pouch detection
    is_gold_pouch = "gold_pouch" in "gold_pouch_small".lower()
    has_gold_effect = item.effect and "gold pieces" in item.effect.lower()
    
    assert is_gold_pouch or has_gold_effect, "Should be detected as gold pouch"
    print(f"✅ Detected as gold pouch: name={is_gold_pouch}, effect={has_gold_effect}")
    
    # Simulate picking up gold pouch
    old_gold = character.gold
    location.remove_item("gold_pouch_small")
    character.gold += item.value
    
    assert character.gold == old_gold + item.value, "Gold should increase"
    assert not location.has_item("gold_pouch_small"), "Gold pouch should be removed"
    print(f"✅ Gold before: {old_gold}, after: {character.gold}")
    print(f"✅ Location items remaining: {location.items}")
    
    print("\n✅ Gold pouch handling test passed!")


def test_talk_command():
    """Test NPC detection for talk command."""
    print("\n" + "=" * 60)
    print("     TALK COMMAND TESTS")
    print("=" * 60)
    
    manager = create_test_location_manager()
    location = manager.get_current_location()
    
    # Test NPC detection
    assert location.has_npc("barkeep"), "Tavern should have barkeep"
    assert location.has_npc("bram"), "Tavern should have bram"
    assert not location.has_npc("wizard"), "Tavern should not have wizard"
    print("✅ NPC detection working")
    
    # Test case insensitivity
    assert location.has_npc("BARKEEP"), "has_npc should be case insensitive"
    assert location.has_npc("Bram"), "has_npc should be case insensitive"
    print("✅ has_npc is case insensitive")
    
    # Test NPC display formatting
    npcs_display = location.get_npcs_display()
    # Test data uses simple NPC IDs, display should capitalize them
    assert "Barkeep" in npcs_display or "barkeep" in npcs_display.lower(), "Should have barkeep in display"
    assert "Bram" in npcs_display, "Should have Bram in display"
    print(f"✅ NPC display: {npcs_display}")
    
    print("\n✅ Talk command test passed!")


def test_movement():
    """Test location movement with events."""
    print("\n" + "=" * 60)
    print("     MOVEMENT TESTS (with Events)")
    print("=" * 60)
    
    manager = create_test_location_manager()
    
    # Start in tavern
    assert manager.current_location_id == "tavern"
    print(f"✅ Starting location: {manager.get_current_location().name}")
    
    # Move to street via door (no events)
    success, new_loc, msg, events = manager.move("door")
    assert success, "Should be able to move through door"
    assert new_loc.id == "street", "Should be on street"
    print(f"✅ Moved to: {new_loc.name} (events: {len(events)})")
    
    # Move to forest (has first-visit event)
    success, new_loc, msg, events = manager.move("north")
    assert success, "Should be able to move north"
    assert new_loc.id == "forest", "Should be in forest"
    assert len(events) == 1, "Should have 1 first-visit event"
    assert events[0].id == "forest_ambush", "Should be the ambush event"
    print(f"✅ Moved to: {new_loc.name} with event: {events[0].narration}")
    
    # Return to forest (no events - already triggered)
    manager.move("south")  # Back to street
    success, new_loc, msg, events = manager.move("north")  # Back to forest
    assert success, "Should be able to return to forest"
    assert len(events) == 0, "No events on return visit"
    print(f"✅ Returned to: {new_loc.name} (no events on revisit)")
    
    # Try invalid direction
    success, new_loc, msg, events = manager.move("west")
    assert not success, "Should not be able to move west"
    print(f"✅ Invalid move rejected: {msg}")
    
    print("\n✅ Movement test passed!")


def test_location_events():
    """Test location event system."""
    print("\n" + "=" * 60)
    print("     LOCATION EVENT TESTS")
    print("=" * 60)
    
    manager = create_test_location_manager()
    
    # Check cave has events
    cave = manager.locations["cave"]
    assert len(cave.events) == 2, "Cave should have 2 events"
    print(f"✅ Cave has {len(cave.events)} events")
    
    for event in cave.events:
        print(f"  - {event.id}: {event.narration}")
        if event.effect:
            print(f"    Effect: {event.effect}")
    
    # Move to cave and check events fire
    manager.set_current_location("forest")
    success, new_loc, msg, events = manager.move("deeper")
    
    assert success, "Should move to cave"
    assert len(events) == 2, "Should trigger both first-visit events"
    print(f"✅ Entered cave, triggered {len(events)} events")
    
    for event in events:
        print(f"  🎯 Event: {event.id}")
    
    # Check events are marked as triggered
    assert cave.is_event_triggered("cave_trap"), "Trap should be triggered"
    assert cave.is_event_triggered("cave_discovery"), "Discovery should be triggered"
    print("✅ Events marked as triggered")
    
    print("\n✅ Location event test passed!")


def test_location_items_persistence():
    """Test that location items persist after being picked up."""
    print("\n" + "=" * 60)
    print("     ITEM PERSISTENCE TESTS")
    print("=" * 60)
    
    manager = create_test_location_manager()
    location = manager.get_current_location()
    
    # Initial state
    initial_items = location.items.copy()
    print(f"  Initial items: {initial_items}")
    
    # Pick up an item
    location.remove_item("torch")
    after_pickup = location.items.copy()
    print(f"  After pickup: {after_pickup}")
    
    # Serialize state
    state = manager.to_dict()
    print(f"  Saved state items: {state['location_states']['tavern']['items']}")
    
    # Create new manager and restore
    manager2 = create_test_location_manager()  # Fresh with all items
    manager2.restore_state(state)
    
    # Check restored state
    restored_items = manager2.locations["tavern"].items
    print(f"  Restored items: {restored_items}")
    
    assert "torch" not in restored_items, "Picked up torch should stay gone"
    assert "healing_potion" in restored_items, "Unpicked items should remain"
    
    print("\n✅ Item persistence test passed!")


# =============================================================================
# CONDITIONAL EXIT TESTS (Phase 3.2.1 - Priority 5)
# =============================================================================

def create_locked_door_test_manager() -> LocationManager:
    """Create a location manager with locked doors for testing."""
    manager = LocationManager()
    
    # Main room with locked storage door
    main_room = Location(
        id="main_room",
        name="Guard Post",
        description="A small guard post with a sturdy door marked 'STORAGE'.",
        exits={"outside": "outside", "storage": "storage"},
        npcs=["guard"],
        items=["storage_key", "torch"],
        atmosphere="Musty air, flickering torchlight",
        exit_conditions=[
            ExitCondition(
                exit_name="storage",
                condition="has_item:storage_key",
                fail_message="The storage door is locked. You need a key.",
                consume_item=False
            )
        ]
    )
    
    # Storage room (behind locked door)
    storage = Location(
        id="storage",
        name="Storage Room",
        description="A cramped storage room full of supplies and treasure.",
        exits={"main room": "main_room"},
        npcs=[],
        items=["gold_pouch", "healing_potion", "longsword"],
        atmosphere="Dusty shelves, the smell of old leather"
    )
    
    # Outside area
    outside = Location(
        id="outside",
        name="Outside",
        description="The path outside the guard post.",
        exits={"door": "main_room"},
        npcs=[],
        items=[]
    )
    
    manager.add_location(main_room)
    manager.add_location(storage)
    manager.add_location(outside)
    manager.set_available_locations(["main_room", "storage", "outside"])
    manager.set_current_location("main_room")
    
    return manager


def test_locked_door_blocked():
    """Test that locked doors block movement without key."""
    print("\n" + "=" * 60)
    print("     LOCKED DOOR BLOCKED TEST")
    print("=" * 60)
    
    manager = create_locked_door_test_manager()
    character = MockCharacter()
    character.inventory = []  # Empty inventory
    
    # Build game_state without the key
    game_state = {
        "character": character,
        "inventory": type('MockInv', (), {'items': []})(),
        "visited_locations": ["main_room"],
        "completed_objectives": [],
        "flags": {}
    }
    
    # Try to move to storage (should fail)
    success, new_loc, message, events = manager.move("storage", game_state)
    
    assert not success, "Should not be able to enter storage without key"
    assert "locked" in message.lower() or "key" in message.lower(), f"Message should mention locked: {message}"
    print(f"✅ Blocked: {message}")
    
    print("\n✅ Locked door blocked test passed!")


def test_locked_door_opened_with_key():
    """Test that locked doors open when player has the key."""
    print("\n" + "=" * 60)
    print("     LOCKED DOOR OPENED WITH KEY TEST")
    print("=" * 60)
    
    manager = create_locked_door_test_manager()
    
    # Create mock item for key
    class MockItem:
        def __init__(self, name):
            self.name = name
    
    class MockInventory:
        def __init__(self):
            self.items = [MockItem("Storage Key")]
    
    # Build game_state with the key
    game_state = {
        "inventory": MockInventory(),
        "visited_locations": ["main_room"],
        "completed_objectives": [],
        "flags": {}
    }
    
    # Try to move to storage (should succeed)
    success, new_loc, message, events = manager.move("storage", game_state)
    
    assert success, f"Should be able to enter storage with key. Got: {message}"
    assert new_loc.id == "storage", "Should be in storage room"
    print(f"✅ Entered storage room: {new_loc.name}")
    
    # Check that exit is now permanently unlocked
    main_room = manager.locations["main_room"]
    assert main_room.is_exit_unlocked("storage"), "Storage exit should be unlocked"
    print("✅ Exit is now permanently unlocked")
    
    print("\n✅ Locked door opened with key test passed!")


def test_unlocked_exit_stays_open():
    """Test that once unlocked, exits stay open even without key."""
    print("\n" + "=" * 60)
    print("     UNLOCKED EXIT STAYS OPEN TEST")
    print("=" * 60)
    
    manager = create_locked_door_test_manager()
    
    # First unlock with key
    class MockItem:
        def __init__(self, name):
            self.name = name
    
    class MockInventoryWithKey:
        items = [MockItem("Storage Key")]
    
    game_state_with_key = {"inventory": MockInventoryWithKey(), "visited_locations": [], "flags": {}}
    
    # Unlock the door
    success, new_loc, _, _ = manager.move("storage", game_state_with_key)
    assert success, "Should unlock with key"
    print("✅ First entry with key successful")
    
    # Go back to main room
    manager.move("main room")
    
    # Now try without key
    class MockInventoryEmpty:
        items = []
    
    game_state_no_key = {"inventory": MockInventoryEmpty(), "visited_locations": [], "flags": {}}
    
    success, new_loc, message, _ = manager.move("storage", game_state_no_key)
    assert success, f"Should be able to enter unlocked door without key. Got: {message}"
    print("✅ Re-entry without key successful (door stays unlocked)")
    
    print("\n✅ Unlocked exit stays open test passed!")


def test_check_exit_condition_function():
    """Test the check_exit_condition utility function."""
    print("\n" + "=" * 60)
    print("     CHECK EXIT CONDITION FUNCTION TEST")
    print("=" * 60)
    
    # Test has_item condition
    class MockItem:
        def __init__(self, name):
            self.name = name
    
    class MockInv:
        items = [MockItem("Rusty Key")]
    
    success, reason = check_exit_condition("has_item:rusty_key", {"inventory": MockInv()})
    assert success, "Should pass with item in inventory"
    print(f"✅ has_item check passed: {reason}")
    
    # Test gold condition
    class MockChar:
        gold = 100
    
    success, reason = check_exit_condition("gold:50", {"character": MockChar()})
    assert success, "Should pass with enough gold"
    print(f"✅ gold check passed: {reason}")
    
    success, reason = check_exit_condition("gold:200", {"character": MockChar()})
    assert not success, "Should fail without enough gold"
    print(f"✅ gold check failed correctly: {reason}")
    
    # Test visited condition
    success, reason = check_exit_condition("visited:forest", {"visited_locations": ["forest", "cave"]})
    assert success, "Should pass when location visited"
    print("✅ visited check passed")
    
    success, reason = check_exit_condition("visited:tower", {"visited_locations": ["forest"]})
    assert not success, "Should fail when location not visited"
    print("✅ visited check failed correctly")
    
    # Test skill check returns marker
    success, reason = check_exit_condition("skill:strength:18", {})
    assert success, "Skill checks always return success with marker"
    assert reason == "skill_check:strength:18", f"Should return skill check marker, got: {reason}"
    print(f"✅ skill check returns marker: {reason}")
    
    print("\n✅ Check exit condition function test passed!")


def test_goblin_cave_locked_storage():
    """Test the locked storage room in the actual Goblin Cave scenario."""
    print("\n" + "=" * 60)
    print("     GOBLIN CAVE LOCKED STORAGE TEST")
    print("=" * 60)
    
    # Create the real scenario
    scenario = create_goblin_cave_scenario()
    loc_mgr = scenario.location_manager
    
    # Check storage location exists
    assert "goblin_storage" in loc_mgr.locations, "goblin_storage should exist"
    print("✅ goblin_storage location exists")
    
    # Check storage_key item exists in shadows
    shadows = loc_mgr.locations.get("goblin_camp_shadows")
    assert shadows is not None, "goblin_camp_shadows should exist"
    assert "storage_key" in shadows.items, f"storage_key should be in shadows, got: {shadows.items}"
    print(f"✅ storage_key found in goblin_camp_shadows: {shadows.items}")
    
    # Check main camp has locked storage door
    main_camp = loc_mgr.locations.get("goblin_camp_main")
    assert main_camp is not None, "goblin_camp_main should exist"
    assert "storage" in main_camp.exits, "storage exit should exist"
    
    storage_cond = main_camp.get_exit_condition("storage")
    assert storage_cond is not None, "storage should have exit condition"
    assert storage_cond.condition == "has_item:storage_key", f"Should require storage_key, got: {storage_cond.condition}"
    print(f"✅ Storage door requires: {storage_cond.condition}")
    print(f"✅ Fail message: {storage_cond.fail_message}")
    
    print("\n✅ Goblin Cave locked storage test passed!")


def run_unit_tests():
    """Run all unit tests."""
    print("\n" + "=" * 60)
    print("🧪 RUNNING LOCATION SYSTEM UNIT TESTS")
    print("=" * 60)
    
    tests = [
        ("Look Command Display", test_look_command_display),
        ("Take Command", test_take_command),
        ("Take Nonexistent Item", test_take_nonexistent_item),
        ("Gold Pouch Handling", test_gold_pouch_handling),
        ("Talk Command", test_talk_command),
        ("Movement (with Events)", test_movement),
        ("Location Events", test_location_events),
        ("Item Persistence", test_location_items_persistence),
        # Conditional Exit Tests (Phase 3.2.1 Priority 5)
        ("Locked Door Blocked", test_locked_door_blocked),
        ("Locked Door Opened with Key", test_locked_door_opened_with_key),
        ("Unlocked Exit Stays Open", test_unlocked_exit_stays_open),
        ("Check Exit Condition Function", test_check_exit_condition_function),
        ("Goblin Cave Locked Storage", test_goblin_cave_locked_storage),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ {name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


# =============================================================================
# INTERACTIVE EXPLORATION MODE
# =============================================================================

def interactive_exploration():
    """Interactive mode for testing location exploration with AI DM."""
    print("\n" + "=" * 60)
    print("🗺️  INTERACTIVE LOCATION EXPLORATION")
    print("=" * 60)
    
    # Initialize AI
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ No GOOGLE_API_KEY found in environment!")
        return
    
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction="""You are the Dungeon Master for a D&D adventure.
You are in the middle of The Goblin Cave adventure - the player is exploring 
a village tavern before heading out to rescue a farmer's daughter from goblins.

When describing locations, be vivid but concise (2-3 sentences).
When the player talks to an NPC, roleplay that NPC with appropriate personality.
- Barkeep: Gruff but helpful, knows local gossip
- Bram: Worried farmer, desperate to save his daughter Lily
- Merchant: Traveling trader, sells supplies at fair prices

Keep responses focused and atmospheric."""
    )
    
    chat = model.start_chat(history=[])
    
    # Create test environment
    manager = create_test_location_manager()
    character = MockCharacter()
    
    # Generate AI narration for starting location
    print("\n" + "=" * 50)
    location = manager.get_current_location()
    is_first = not location.visited
    context = build_location_context(location, is_first_visit=is_first)
    narration = get_location_narration(chat, context)
    display_location_narration(location.name, narration, manager.get_exits())
    
    print("\n" + "-" * 40)
    print("Commands: look, scan, exits, go <dir>, take <item>, talk <npc>")
    print("          inv (inventory), gold, quit")
    print("-" * 40)
    
    while True:
        try:
            command = input("\n> ").strip().lower()
            
            if not command:
                continue
            
            if command in ["quit", "exit", "q"]:
                print("\nGoodbye, adventurer!")
                break
            
            location = manager.get_current_location()
            
            # Look command - AI narrative description
            if command in ["look", "look around", "l"]:
                # Build context for AI (Mechanics First)
                is_first = not location.visited
                context = build_location_context(location, is_first_visit=is_first)
                
                # Get AI narration (Narration Last)
                narration = get_location_narration(chat, context)
                
                # Display
                display_location_narration(location.name, narration, manager.get_exits())
                continue
            
            # Scan command - mechanical list (for players who want details)
            if command in ["scan", "survey"]:
                print(f"\n  📍 {location.name}")
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
                exits = manager.get_exits()
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
                
                success, new_loc, msg, events = manager.move(direction)
                
                if success and new_loc:
                    # Check if first visit (move() already marks visited, 
                    # so we check if there are events which indicates first visit)
                    is_first = len(events) > 0 or not new_loc.visited
                    
                    # Build context for AI (Mechanics First)
                    context = build_location_context(new_loc, is_first_visit=is_first, events=events)
                    
                    # Get AI narration (Narration Last)
                    narration = get_location_narration(chat, context)
                    
                    # Display
                    display_location_narration(new_loc.name, narration, manager.get_exits())
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
                        
                        # Gold pouch handling
                        if "gold_pouch" in item_name.lower() or (item.effect and "gold pieces" in item.effect.lower()):
                            character.gold += item.value
                            print(f"\n  💰 You found {item.value} gold pieces!")
                        else:
                            msg = add_item_to_inventory(character.inventory, item)
                            print(f"\n  ✅ {msg}")
                    else:
                        print(f"\n  ❓ You pick up the {item_name}, but it doesn't seem useful.")
                        location.remove_item(item_name)
                else:
                    print(f"\n  ❌ You don't see '{item_name}' here.")
                continue
            
            # Talk command
            if command.startswith("talk ") or command.startswith("speak ") or command.startswith("talk to ") or command.startswith("speak to "):
                for prefix in ["talk to ", "speak to ", "talk ", "speak "]:
                    if command.startswith(prefix):
                        npc_name = command[len(prefix):].strip()
                        break
                
                if location.has_npc(npc_name):
                    npc_display = npc_name.replace("_", " ").title()
                    print(f"\n  💬 You approach {npc_display}...")
                    print("\n🎲 Dungeon Master:")
                    response = chat.send_message(
                        f"[Player wants to talk to {npc_display} in {location.name}. Roleplay this NPC with appropriate personality. Keep response to 3-4 sentences.]"
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
                print("\n  📦 INVENTORY:")
                if not character.inventory:
                    print("    (empty)")
                else:
                    for item in character.inventory:
                        print(f"    - {item.name}: {item.description}")
                print(f"  💰 Gold: {character.gold}")
                continue
            
            # Gold command
            if command == "gold":
                print(f"\n  💰 You have {character.gold} gold pieces.")
                continue
            
            # Unknown command - pass to AI
            print("\n🎲 Dungeon Master:")
            response = chat.send_message(f"[Player action: {command}. Current location: {location.name}. Respond appropriately in 2-3 sentences.]")
            print(f"  {response.text}")
            
        except KeyboardInterrupt:
            print("\n\nExploration ended.")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


# =============================================================================
# MAIN MENU
# =============================================================================

def show_test_menu():
    """Show test selection menu."""
    print("\n" + "=" * 60)
    print("      🗺️ LOCATION + DM TEST SUITE 🗺️")
    print("=" * 60)
    print("\nSelect test to run:")
    print("  1. Unit Tests (look, take, talk, movement)")
    print("  2. Interactive Exploration (full AI DM integration)")
    print("  3. Run All Tests")
    print("  0. Exit")
    
    choice = input("\nChoice: ").strip()
    return choice


if __name__ == "__main__":
    try:
        choice = show_test_menu()
        
        if choice == '1':
            run_unit_tests()
        elif choice == '2':
            interactive_exploration()
        elif choice == '3':
            print("\n🧪 Running unit tests first...")
            if run_unit_tests():
                print("\n🎮 Now running interactive exploration...")
                interactive_exploration()
            else:
                print("\n❌ Unit tests failed. Fix before running interactive test.")
        elif choice == '0':
            print("Goodbye!")
        else:
            print("Invalid choice. Running unit tests...")
            run_unit_tests()
    except KeyboardInterrupt:
        print("\n\nTest interrupted.")
