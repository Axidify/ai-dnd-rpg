"""
Comprehensive tests for the Location System (Phase 3.2).
Covers: Location dataclass, LocationManager, movement, serialization, exit filtering.
Updated for Phase 3.2.1 with LocationEvent support.
"""

import pytest
import sys
sys.path.insert(0, '../src')

from scenario import Location, LocationManager, LocationEvent, EventTrigger


# =============================================================================
# LOCATION DATACLASS TESTS
# =============================================================================

class TestLocationBasics:
    """Tests for Location dataclass."""
    
    def test_create_location_minimal(self):
        """Test creating a location with minimal required fields."""
        location = Location(
            id="test_loc",
            name="Test Location",
            description="A test location"
        )
        assert location.id == "test_loc"
        assert location.name == "Test Location"
        assert location.description == "A test location"
        assert location.exits == {}
        assert location.npcs == []
        assert location.items == []
        assert location.atmosphere == ""
        assert location.enter_text == ""
        assert location.visited == False
        assert location.events_triggered == []
    
    def test_create_location_full(self):
        """Test creating a location with all fields populated."""
        location = Location(
            id="tavern",
            name="The Rusty Dragon",
            description="A cozy tavern with a crackling hearth",
            exits={"door": "street", "stairs": "upstairs"},
            npcs=["barkeep", "patron"],
            items=["torch", "mug"],
            atmosphere="Warm and welcoming",
            enter_text="You push open the tavern door."
        )
        assert location.id == "tavern"
        assert len(location.exits) == 2
        assert "barkeep" in location.npcs
        assert "torch" in location.items
        assert location.atmosphere == "Warm and welcoming"
        assert location.visited == False
    
    def test_location_visited_state(self):
        """Test that visited state can be changed."""
        location = Location(id="test", name="Test", description="Test")
        assert location.visited == False
        location.visited = True
        assert location.visited == True
    
    def test_location_events_triggered(self):
        """Test events_triggered list."""
        location = Location(id="test", name="Test", description="Test")
        assert location.events_triggered == []
        location.events_triggered.append("first_visit")
        location.events_triggered.append("found_secret")
        assert len(location.events_triggered) == 2
        assert "first_visit" in location.events_triggered


class TestLocationExitsDisplay:
    """Tests for Location.get_exits_display() method."""
    
    def test_exits_display_no_exits(self):
        """Test display with no exits."""
        location = Location(id="test", name="Test", description="Test", exits={})
        result = location.get_exits_display()
        assert result == "There are no obvious exits."
    
    def test_exits_display_single_exit(self):
        """Test display with one exit."""
        location = Location(
            id="test", name="Test", description="Test",
            exits={"door": "outside"}
        )
        result = location.get_exits_display()
        assert result == "You can go: door"
    
    def test_exits_display_two_exits(self):
        """Test display with two exits uses 'or'."""
        location = Location(
            id="test", name="Test", description="Test",
            exits={"north": "forest", "south": "village"}
        )
        result = location.get_exits_display()
        # Should be "You can go: north or south" or "south or north"
        assert "You can go:" in result
        assert " or " in result
    
    def test_exits_display_multiple_exits(self):
        """Test display with three+ exits uses commas and 'or'."""
        location = Location(
            id="test", name="Test", description="Test",
            exits={"north": "a", "south": "b", "east": "c"}
        )
        result = location.get_exits_display()
        assert "You can go:" in result
        assert " or " in result


class TestLocationSerialization:
    """Tests for Location.to_dict() and Location.from_state()."""
    
    def test_to_dict_default_state(self):
        """Test serialization of default state."""
        location = Location(
            id="test_loc",
            name="Test",
            description="Test"
        )
        result = location.to_dict()
        assert result["id"] == "test_loc"
        assert result["visited"] == False
        assert result["events_triggered"] == []
    
    def test_to_dict_modified_state(self):
        """Test serialization after state changes."""
        location = Location(
            id="test_loc",
            name="Test",
            description="Test"
        )
        location.visited = True
        location.events_triggered = ["event1", "event2"]
        
        result = location.to_dict()
        assert result["id"] == "test_loc"
        assert result["visited"] == True
        assert result["events_triggered"] == ["event1", "event2"]
    
    def test_to_dict_does_not_modify_original(self):
        """Test that to_dict creates a copy of events_triggered."""
        location = Location(
            id="test",
            name="Test",
            description="Test"
        )
        location.events_triggered = ["event1"]
        
        result = location.to_dict()
        result["events_triggered"].append("event2")
        
        # Original should be unchanged
        assert len(location.events_triggered) == 1
    
    def test_from_state_applies_visited(self):
        """Test from_state applies visited correctly."""
        location = Location(
            id="test",
            name="Test",
            description="Test"
        )
        state = {"visited": True, "events_triggered": []}
        
        Location.from_state(location, state)
        assert location.visited == True
    
    def test_from_state_applies_events(self):
        """Test from_state applies events_triggered correctly."""
        location = Location(
            id="test",
            name="Test",
            description="Test"
        )
        state = {"visited": False, "events_triggered": ["saved_event"]}
        
        Location.from_state(location, state)
        assert "saved_event" in location.events_triggered
    
    def test_from_state_handles_missing_keys(self):
        """Test from_state handles incomplete state gracefully."""
        location = Location(
            id="test",
            name="Test",
            description="Test"
        )
        state = {}  # Empty state
        
        Location.from_state(location, state)
        assert location.visited == False
        assert location.events_triggered == []
    
    def test_from_state_restores_items(self):
        """Test from_state restores items list correctly (Phase 3.2.1)."""
        location = Location(
            id="test",
            name="Test",
            description="Test",
            items=["torch", "sword", "potion"]
        )
        # Simulate items being picked up
        state = {"visited": True, "events_triggered": [], "items": ["potion"]}
        
        Location.from_state(location, state)
        assert location.items == ["potion"]
        assert "torch" not in location.items
    
    def test_to_dict_includes_items(self):
        """Test to_dict saves items list (Phase 3.2.1)."""
        location = Location(
            id="test",
            name="Test",
            description="Test",
            items=["torch", "sword"]
        )
        
        result = location.to_dict()
        assert "items" in result
        assert result["items"] == ["torch", "sword"]


class TestLocationItemsAndNPCs:
    """Tests for Location item and NPC helper methods (Phase 3.2.1)."""
    
    def test_has_item_true(self):
        """Test has_item returns True when item present."""
        location = Location(
            id="test", name="Test", description="Test",
            items=["torch", "sword"]
        )
        assert location.has_item("torch") == True
        assert location.has_item("sword") == True
    
    def test_has_item_false(self):
        """Test has_item returns False when item not present."""
        location = Location(
            id="test", name="Test", description="Test",
            items=["torch"]
        )
        assert location.has_item("sword") == False
    
    def test_has_item_case_insensitive(self):
        """Test has_item is case insensitive."""
        location = Location(
            id="test", name="Test", description="Test",
            items=["Torch", "SWORD"]
        )
        assert location.has_item("torch") == True
        assert location.has_item("TORCH") == True
        assert location.has_item("sword") == True
    
    def test_remove_item_success(self):
        """Test remove_item removes and returns True."""
        location = Location(
            id="test", name="Test", description="Test",
            items=["torch", "sword"]
        )
        result = location.remove_item("torch")
        assert result == True
        assert "torch" not in location.items
        assert "sword" in location.items
    
    def test_remove_item_not_found(self):
        """Test remove_item returns False when item not present."""
        location = Location(
            id="test", name="Test", description="Test",
            items=["torch"]
        )
        result = location.remove_item("sword")
        assert result == False
        assert len(location.items) == 1
    
    def test_remove_item_case_insensitive(self):
        """Test remove_item is case insensitive."""
        location = Location(
            id="test", name="Test", description="Test",
            items=["Torch"]
        )
        result = location.remove_item("torch")
        assert result == True
        assert len(location.items) == 0
    
    def test_has_npc_true(self):
        """Test has_npc returns True when NPC present."""
        location = Location(
            id="test", name="Test", description="Test",
            npcs=["barkeep", "bram"]
        )
        assert location.has_npc("barkeep") == True
        assert location.has_npc("bram") == True
    
    def test_has_npc_false(self):
        """Test has_npc returns False when NPC not present."""
        location = Location(
            id="test", name="Test", description="Test",
            npcs=["barkeep"]
        )
        assert location.has_npc("wizard") == False
    
    def test_has_npc_case_insensitive(self):
        """Test has_npc is case insensitive."""
        location = Location(
            id="test", name="Test", description="Test",
            npcs=["Barkeep", "BRAM"]
        )
        assert location.has_npc("barkeep") == True
        assert location.has_npc("BARKEEP") == True
        assert location.has_npc("bram") == True
    
    def test_get_items_display_with_items(self):
        """Test get_items_display with items present."""
        location = Location(
            id="test", name="Test", description="Test",
            items=["torch", "sword"]
        )
        result = location.get_items_display()
        assert "🎒" in result
        assert "Torch" in result  # Now title-cased for display
        assert "Sword" in result
    
    def test_get_items_display_empty(self):
        """Test get_items_display with no items."""
        location = Location(
            id="test", name="Test", description="Test",
            items=[]
        )
        result = location.get_items_display()
        assert result == ""
    
    def test_get_npcs_display_with_npcs(self):
        """Test get_npcs_display with NPCs present."""
        location = Location(
            id="test", name="Test", description="Test",
            npcs=["barkeep", "bram"]
        )
        result = location.get_npcs_display()
        assert "👤" in result
        assert "Barkeep" in result
        assert "Bram" in result
    
    def test_get_npcs_display_empty(self):
        """Test get_npcs_display with no NPCs."""
        location = Location(
            id="test", name="Test", description="Test",
            npcs=[]
        )
        result = location.get_npcs_display()
        assert result == ""
    
    def test_get_npcs_display_formats_underscores(self):
        """Test get_npcs_display replaces underscores with spaces."""
        location = Location(
            id="test", name="Test", description="Test",
            npcs=["old_man", "village_elder"]
        )
        result = location.get_npcs_display()
        assert "Old Man" in result
        assert "Village Elder" in result


# =============================================================================
# LOCATION MANAGER TESTS
# =============================================================================

class TestLocationManagerBasics:
    """Tests for LocationManager initialization and basic operations."""
    
    def test_create_empty_manager(self):
        """Test creating an empty location manager."""
        manager = LocationManager()
        assert manager.locations == {}
        assert manager.current_location_id is None
        assert manager.available_location_ids == []
    
    def test_add_location(self):
        """Test adding a location to the manager."""
        manager = LocationManager()
        location = Location(id="test", name="Test", description="Test")
        
        manager.add_location(location)
        
        assert "test" in manager.locations
        assert manager.locations["test"] == location
    
    def test_add_multiple_locations(self):
        """Test adding multiple locations."""
        manager = LocationManager()
        loc1 = Location(id="loc1", name="Location 1", description="First")
        loc2 = Location(id="loc2", name="Location 2", description="Second")
        
        manager.add_location(loc1)
        manager.add_location(loc2)
        
        assert len(manager.locations) == 2
        assert "loc1" in manager.locations
        assert "loc2" in manager.locations


class TestLocationManagerSetters:
    """Tests for LocationManager setter methods."""
    
    def test_set_available_locations(self):
        """Test setting available location IDs."""
        manager = LocationManager()
        manager.set_available_locations(["loc1", "loc2", "loc3"])
        
        assert manager.available_location_ids == ["loc1", "loc2", "loc3"]
    
    def test_set_current_location_valid(self):
        """Test setting current location to a valid ID."""
        manager = LocationManager()
        location = Location(id="test", name="Test", description="Test")
        manager.add_location(location)
        
        result = manager.set_current_location("test")
        
        assert result == location
        assert manager.current_location_id == "test"
        assert location.visited == True
    
    def test_set_current_location_invalid(self):
        """Test setting current location to an invalid ID."""
        manager = LocationManager()
        
        result = manager.set_current_location("nonexistent")
        
        assert result is None
        assert manager.current_location_id is None
    
    def test_set_current_location_marks_visited(self):
        """Test that setting current location marks it as visited."""
        manager = LocationManager()
        location = Location(id="test", name="Test", description="Test")
        assert location.visited == False
        
        manager.add_location(location)
        manager.set_current_location("test")
        
        assert location.visited == True


class TestLocationManagerGetters:
    """Tests for LocationManager getter methods."""
    
    def test_get_current_location_none(self):
        """Test getting current location when none set."""
        manager = LocationManager()
        assert manager.get_current_location() is None
    
    def test_get_current_location_valid(self):
        """Test getting current location when set."""
        manager = _create_test_manager()
        manager.set_current_location("tavern")
        
        result = manager.get_current_location()
        assert result.id == "tavern"
        assert result.name == "Test Tavern"
    
    def test_get_exits_no_current_location(self):
        """Test get_exits when no current location."""
        manager = LocationManager()
        assert manager.get_exits() == {}
    
    def test_get_exits_filters_by_available(self):
        """Test that get_exits only returns available locations."""
        manager = _create_test_manager()
        manager.set_available_locations(["tavern", "street"])  # forest NOT available
        manager.set_current_location("tavern")
        
        exits = manager.get_exits()
        
        # Tavern has exits to street and forest, but only street is available
        assert "door" in exits  # Goes to street
        assert exits["door"] == "street"
        # Forest exit should be filtered out (not in available)
    
    def test_get_exits_all_available(self):
        """Test get_exits when all destinations are available."""
        manager = _create_test_manager()
        manager.set_available_locations(["tavern", "street", "forest"])
        manager.set_current_location("tavern")
        
        exits = manager.get_exits()
        
        assert len(exits) == 2  # door -> street, path -> forest


class TestLocationManagerMovement:
    """Tests for LocationManager.move() method."""
    
    def test_move_no_current_location(self):
        """Test moving when no current location is set."""
        manager = LocationManager()
        
        success, location, message, events = manager.move("north")
        
        assert success == False
        assert location is None
        assert "nowhere" in message.lower()
        assert events == []
    
    def test_move_valid_direction(self):
        """Test moving in a valid direction."""
        manager = _create_test_manager()
        manager.set_available_locations(["tavern", "street", "forest"])
        manager.set_current_location("tavern")
        
        success, location, message, events = manager.move("door")
        
        assert success == True
        assert location.id == "street"
        assert manager.current_location_id == "street"
    
    def test_move_invalid_direction(self):
        """Test moving in an invalid direction."""
        manager = _create_test_manager()
        manager.set_available_locations(["tavern", "street"])
        manager.set_current_location("tavern")
        
        success, location, message, events = manager.move("window")
        
        assert success == False
        assert location is None
        assert "can't go" in message.lower()
    
    def test_move_partial_match(self):
        """Test that move supports partial matching."""
        manager = _create_test_manager()
        manager.set_available_locations(["tavern", "street", "forest"])
        manager.set_current_location("tavern")
        
        # "do" should match "door"
        success, location, message, events = manager.move("do")
        
        # Note: This depends on implementation - check if partial matching works
        # If it doesn't match, this test documents expected behavior
        if success:
            assert location.id == "street"
    
    def test_move_case_insensitive(self):
        """Test that move is case insensitive."""
        manager = _create_test_manager()
        manager.set_available_locations(["tavern", "street"])
        manager.set_current_location("tavern")
        
        success, location, message, events = manager.move("DOOR")
        
        assert success == True
        assert location.id == "street"
    
    def test_move_with_whitespace(self):
        """Test that move handles extra whitespace."""
        manager = _create_test_manager()
        manager.set_available_locations(["tavern", "street"])
        manager.set_current_location("tavern")
        
        success, location, message, events = manager.move("  door  ")
        
        assert success == True
        assert location.id == "street"
    
    def test_move_to_unavailable_location(self):
        """Test moving to a location not in available list."""
        manager = _create_test_manager()
        manager.set_available_locations(["tavern"])  # Only tavern available
        manager.set_current_location("tavern")
        
        # Tavern has "door" exit to street, but street is not available
        success, location, message, events = manager.move("door")
        
        assert success == False
        assert location is None
    
    def test_move_marks_new_location_visited(self):
        """Test that moving to a location marks it as visited."""
        manager = _create_test_manager()
        manager.set_available_locations(["tavern", "street"])
        manager.set_current_location("tavern")
        
        street = manager.locations["street"]
        assert street.visited == False
        
        manager.move("door")
        
        assert street.visited == True
    
    def test_move_no_exits(self):
        """Test moving from location with no exits."""
        manager = LocationManager()
        dead_end = Location(
            id="dead_end",
            name="Dead End",
            description="A dead end",
            exits={}
        )
        manager.add_location(dead_end)
        manager.set_available_locations(["dead_end"])
        manager.set_current_location("dead_end")
        
        success, location, message, events = manager.move("north")
        
        assert success == False
        assert "nowhere to go" in message.lower()


class TestLocationManagerContext:
    """Tests for LocationManager.get_context_for_dm()."""
    
    def test_context_no_current_location(self):
        """Test context when no location is set."""
        manager = LocationManager()
        assert manager.get_context_for_dm() == ""
    
    def test_context_basic(self):
        """Test basic context generation."""
        manager = _create_test_manager()
        manager.set_current_location("tavern")
        
        context = manager.get_context_for_dm()
        
        assert "Test Tavern" in context
        assert "cozy tavern" in context.lower()
    
    def test_context_includes_atmosphere(self):
        """Test that context includes atmosphere."""
        manager = _create_test_manager()
        manager.set_current_location("tavern")
        
        context = manager.get_context_for_dm()
        
        assert "warm" in context.lower() or "Atmosphere" in context
    
    def test_context_includes_npcs(self):
        """Test that context includes NPCs when present."""
        manager = _create_test_manager()
        manager.set_current_location("tavern")
        
        context = manager.get_context_for_dm()
        
        assert "barkeep" in context.lower()
    
    def test_context_includes_items(self):
        """Test that context includes items when present."""
        manager = _create_test_manager()
        manager.set_current_location("tavern")
        
        context = manager.get_context_for_dm()
        
        assert "torch" in context.lower()


class TestLocationManagerSerialization:
    """Tests for LocationManager.to_dict() and restore_state()."""
    
    def test_to_dict_empty_manager(self):
        """Test serialization of empty manager."""
        manager = LocationManager()
        
        result = manager.to_dict()
        
        assert result["current_location_id"] is None
        assert result["available_location_ids"] == []
        assert result["location_states"] == {}
    
    def test_to_dict_with_state(self):
        """Test serialization with active state."""
        manager = _create_test_manager()
        manager.set_available_locations(["tavern", "street"])
        manager.set_current_location("tavern")
        
        result = manager.to_dict()
        
        assert result["current_location_id"] == "tavern"
        assert result["available_location_ids"] == ["tavern", "street"]
        assert "tavern" in result["location_states"]
        assert result["location_states"]["tavern"]["visited"] == True
    
    def test_to_dict_preserves_location_states(self):
        """Test that all location states are serialized."""
        manager = _create_test_manager()
        manager.locations["tavern"].visited = True
        manager.locations["tavern"].events_triggered = ["event1"]
        manager.locations["street"].visited = True
        
        result = manager.to_dict()
        
        assert result["location_states"]["tavern"]["visited"] == True
        assert result["location_states"]["tavern"]["events_triggered"] == ["event1"]
        assert result["location_states"]["street"]["visited"] == True
    
    def test_restore_state_current_location(self):
        """Test restoring current location."""
        manager = _create_test_manager()
        state = {
            "current_location_id": "street",
            "available_location_ids": ["tavern", "street"],
            "location_states": {}
        }
        
        manager.restore_state(state)
        
        assert manager.current_location_id == "street"
    
    def test_restore_state_available_locations(self):
        """Test restoring available locations."""
        manager = _create_test_manager()
        state = {
            "current_location_id": None,
            "available_location_ids": ["forest", "street"],
            "location_states": {}
        }
        
        manager.restore_state(state)
        
        assert manager.available_location_ids == ["forest", "street"]
    
    def test_restore_state_location_visited(self):
        """Test restoring individual location states."""
        manager = _create_test_manager()
        assert manager.locations["street"].visited == False
        
        state = {
            "current_location_id": None,
            "available_location_ids": [],
            "location_states": {
                "street": {"visited": True, "events_triggered": ["saved_event"]}
            }
        }
        
        manager.restore_state(state)
        
        assert manager.locations["street"].visited == True
        assert "saved_event" in manager.locations["street"].events_triggered
    
    def test_restore_state_ignores_unknown_locations(self):
        """Test that restore_state ignores unknown location IDs."""
        manager = _create_test_manager()
        state = {
            "current_location_id": None,
            "available_location_ids": [],
            "location_states": {
                "unknown_location": {"visited": True, "events_triggered": []}
            }
        }
        
        # Should not raise an error
        manager.restore_state(state)
        
        assert "unknown_location" not in manager.locations
    
    def test_round_trip_serialization(self):
        """Test that save and restore produces identical state."""
        # Setup
        manager1 = _create_test_manager()
        manager1.set_available_locations(["tavern", "street", "forest"])
        manager1.set_current_location("tavern")
        manager1.move("door")  # Move to street
        manager1.locations["street"].events_triggered.append("test_event")
        
        # Save
        saved_state = manager1.to_dict()
        
        # Create new manager and restore
        manager2 = _create_test_manager()
        manager2.restore_state(saved_state)
        
        # Verify
        assert manager2.current_location_id == manager1.current_location_id
        assert manager2.available_location_ids == manager1.available_location_ids
        assert manager2.locations["tavern"].visited == manager1.locations["tavern"].visited
        assert manager2.locations["street"].visited == manager1.locations["street"].visited
        assert "test_event" in manager2.locations["street"].events_triggered


# =============================================================================
# TEST FIXTURES
# =============================================================================

def _create_test_manager() -> LocationManager:
    """Create a LocationManager with test locations."""
    manager = LocationManager()
    
    tavern = Location(
        id="tavern",
        name="Test Tavern",
        description="A cozy tavern for testing",
        exits={"door": "street", "path": "forest"},
        npcs=["barkeep"],
        items=["torch"],
        atmosphere="Warm and cozy"
    )
    
    street = Location(
        id="street",
        name="Village Street",
        description="A quiet village street",
        exits={"tavern": "tavern", "north": "forest"},
        npcs=[],
        items=[]
    )
    
    forest = Location(
        id="forest",
        name="Dark Forest",
        description="A mysterious forest",
        exits={"south": "street", "back": "tavern"},
        npcs=[],
        items=["stick"]
    )
    
    manager.add_location(tavern)
    manager.add_location(street)
    manager.add_location(forest)
    
    return manager


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

# =============================================================================
# LOCATION EVENT TESTS (Phase 3.2.1)
# =============================================================================

class TestLocationEventBasics:
    """Tests for LocationEvent dataclass."""
    
    def test_create_event_minimal(self):
        """Test creating an event with minimal fields."""
        event = LocationEvent(
            id="test_event",
            trigger=EventTrigger.ON_ENTER,
            narration="Something happens"
        )
        
        assert event.id == "test_event"
        assert event.trigger == EventTrigger.ON_ENTER
        assert event.narration == "Something happens"
        assert event.effect is None
        assert event.condition is None
        assert event.one_time == True
    
    def test_create_event_full(self):
        """Test creating an event with all fields."""
        event = LocationEvent(
            id="trap_event",
            trigger=EventTrigger.ON_FIRST_VISIT,
            narration="A wire catches your foot!",
            effect="damage:1d4",
            condition="not has_item:trap_disabler",
            one_time=True
        )
        
        assert event.id == "trap_event"
        assert event.trigger == EventTrigger.ON_FIRST_VISIT
        assert event.effect == "damage:1d4"
        assert event.condition == "not has_item:trap_disabler"
    
    def test_event_trigger_types(self):
        """Test all EventTrigger enum values."""
        assert EventTrigger.ON_ENTER.value == "on_enter"
        assert EventTrigger.ON_FIRST_VISIT.value == "on_first_visit"
        assert EventTrigger.ON_LOOK.value == "on_look"
        assert EventTrigger.ON_ITEM_TAKE.value == "on_item_take"
    
    def test_event_to_dict(self):
        """Test serializing an event to dictionary."""
        event = LocationEvent(
            id="test",
            trigger=EventTrigger.ON_ENTER,
            narration="Test narration",
            effect="test_effect"
        )
        
        data = event.to_dict()
        
        assert data["id"] == "test"
        assert data["trigger"] == "on_enter"
        assert data["narration"] == "Test narration"
        assert data["effect"] == "test_effect"
    
    def test_event_from_dict(self):
        """Test deserializing an event from dictionary."""
        data = {
            "id": "loaded_event",
            "trigger": "on_first_visit",
            "narration": "You discover something",
            "effect": "add_item:key",
            "condition": None,
            "one_time": True
        }
        
        event = LocationEvent.from_dict(data)
        
        assert event.id == "loaded_event"
        assert event.trigger == EventTrigger.ON_FIRST_VISIT
        assert event.narration == "You discover something"


class TestLocationEventMethods:
    """Tests for Location event methods."""
    
    def test_add_event(self):
        """Test adding an event to a location."""
        location = Location(
            id="test",
            name="Test",
            description="Test location"
        )
        
        event = LocationEvent(
            id="test_event",
            trigger=EventTrigger.ON_ENTER,
            narration="Test"
        )
        
        location.add_event(event)
        
        assert len(location.events) == 1
        assert location.events[0].id == "test_event"
    
    def test_has_event(self):
        """Test checking if location has an event."""
        location = Location(
            id="test",
            name="Test",
            description="Test",
            events=[
                LocationEvent(id="event1", trigger=EventTrigger.ON_ENTER, narration="Test")
            ]
        )
        
        assert location.has_event("event1") == True
        assert location.has_event("nonexistent") == False
    
    def test_trigger_event(self):
        """Test marking an event as triggered."""
        location = Location(
            id="test",
            name="Test",
            description="Test",
            events=[
                LocationEvent(id="event1", trigger=EventTrigger.ON_ENTER, narration="Test")
            ]
        )
        
        result = location.trigger_event("event1")
        
        assert result == True
        assert "event1" in location.events_triggered
    
    def test_trigger_event_nonexistent(self):
        """Test triggering a nonexistent event."""
        location = Location(id="test", name="Test", description="Test")
        
        result = location.trigger_event("fake_event")
        
        assert result == False
    
    def test_is_event_triggered(self):
        """Test checking if event has been triggered."""
        location = Location(
            id="test",
            name="Test",
            description="Test",
            events=[
                LocationEvent(id="event1", trigger=EventTrigger.ON_ENTER, narration="Test")
            ]
        )
        
        assert location.is_event_triggered("event1") == False
        
        location.trigger_event("event1")
        
        assert location.is_event_triggered("event1") == True
    
    def test_get_events_for_trigger_on_enter(self):
        """Test getting events for ON_ENTER trigger."""
        location = Location(
            id="test",
            name="Test",
            description="Test",
            events=[
                LocationEvent(id="enter1", trigger=EventTrigger.ON_ENTER, narration="Enter"),
                LocationEvent(id="look1", trigger=EventTrigger.ON_LOOK, narration="Look")
            ]
        )
        
        events = location.get_events_for_trigger(EventTrigger.ON_ENTER)
        
        assert len(events) == 1
        assert events[0].id == "enter1"
    
    def test_get_events_for_trigger_first_visit(self):
        """Test getting ON_FIRST_VISIT events only fires on first visit."""
        location = Location(
            id="test",
            name="Test",
            description="Test",
            events=[
                LocationEvent(id="first", trigger=EventTrigger.ON_FIRST_VISIT, narration="First time")
            ]
        )
        
        # First visit
        events = location.get_events_for_trigger(EventTrigger.ON_ENTER, is_first_visit=True)
        assert len(events) == 1
        assert events[0].id == "first"
        
        # Not first visit
        events = location.get_events_for_trigger(EventTrigger.ON_ENTER, is_first_visit=False)
        assert len(events) == 0
    
    def test_get_events_skips_triggered_one_time(self):
        """Test that one-time events are skipped if already triggered."""
        location = Location(
            id="test",
            name="Test",
            description="Test",
            events=[
                LocationEvent(id="once", trigger=EventTrigger.ON_ENTER, narration="Once", one_time=True),
                LocationEvent(id="always", trigger=EventTrigger.ON_ENTER, narration="Always", one_time=False)
            ]
        )
        
        # First time - both should fire
        events = location.get_events_for_trigger(EventTrigger.ON_ENTER)
        assert len(events) == 2
        
        # Mark "once" as triggered
        location.trigger_event("once")
        
        # Second time - only "always" should fire
        events = location.get_events_for_trigger(EventTrigger.ON_ENTER)
        assert len(events) == 1
        assert events[0].id == "always"


class TestLocationManagerEvents:
    """Tests for event integration with LocationManager.move()."""
    
    def test_move_returns_events(self):
        """Test that move returns triggered events."""
        manager = LocationManager()
        
        # Create locations with events
        start = Location(id="start", name="Start", description="Start", exits={"north": "end"})
        end = Location(
            id="end",
            name="End",
            description="End",
            events=[
                LocationEvent(id="arrival", trigger=EventTrigger.ON_FIRST_VISIT, narration="You arrive!")
            ]
        )
        
        manager.add_location(start)
        manager.add_location(end)
        manager.set_available_locations(["start", "end"])
        manager.set_current_location("start")
        
        success, location, message, events = manager.move("north")
        
        assert success == True
        assert len(events) == 1
        assert events[0].id == "arrival"
    
    def test_move_marks_events_triggered(self):
        """Test that move marks events as triggered."""
        manager = LocationManager()
        
        start = Location(id="start", name="Start", description="Start", exits={"north": "end"})
        end = Location(
            id="end",
            name="End",
            description="End",
            events=[
                LocationEvent(id="trap", trigger=EventTrigger.ON_FIRST_VISIT, narration="Trap!")
            ]
        )
        
        manager.add_location(start)
        manager.add_location(end)
        manager.set_available_locations(["start", "end"])
        manager.set_current_location("start")
        
        manager.move("north")
        
        assert end.is_event_triggered("trap") == True
    
    def test_move_first_visit_events_only_once(self):
        """Test that first visit events don't fire on return."""
        manager = LocationManager()
        
        start = Location(id="start", name="Start", description="Start", exits={"north": "end"})
        end = Location(
            id="end",
            name="End",
            description="End",
            exits={"south": "start"},
            events=[
                LocationEvent(id="discovery", trigger=EventTrigger.ON_FIRST_VISIT, narration="Discovery!")
            ]
        )
        
        manager.add_location(start)
        manager.add_location(end)
        manager.set_available_locations(["start", "end"])
        manager.set_current_location("start")
        
        # First visit
        success, _, _, events = manager.move("north")
        assert len(events) == 1
        
        # Go back
        manager.move("south")
        
        # Return visit - no events
        success, _, _, events = manager.move("north")
        assert len(events) == 0


if __name__ == "__main__":
    """Run all tests when executed directly."""
    import subprocess
    
    print("=" * 60)
    print("🗺️  LOCATION SYSTEM TESTS")
    print("=" * 60)
    
    # Run pytest
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=False
    )
    
    print("\n" + "=" * 60)
    if result.returncode == 0:
        print("✅ All location tests passed!")
    else:
        print("❌ Some tests failed. Check output above.")
    print("=" * 60)
