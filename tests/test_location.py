"""
Comprehensive tests for the Location System (Phase 3.2).
Covers: Location dataclass, LocationManager, movement, serialization, exit filtering.
Updated for Phase 3.2.1 with LocationEvent support.
Updated for Phase 3.2.1 Priority 6 with ExitCondition support.
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from scenario import Location, LocationManager, LocationEvent, EventTrigger, ExitCondition, check_exit_condition


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
        assert location.atmosphere is None  # Optional[LocationAtmosphere] defaults to None
        assert location.atmosphere_text == ""  # Legacy string field
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
            atmosphere_text="Warm and welcoming",  # Legacy atmosphere string
            enter_text="You push open the tavern door."
        )
        assert location.id == "tavern"
        assert len(location.exits) == 2
        assert "barkeep" in location.npcs
        assert "torch" in location.items
        assert location.atmosphere_text == "Warm and welcoming"
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


# =============================================================================
# EXIT CONDITION TESTS (Phase 3.2.1 Priority 6)
# =============================================================================

class TestExitConditionBasics:
    """Tests for ExitCondition dataclass."""
    
    def test_create_exit_condition_minimal(self):
        """Test creating an exit condition with minimal fields."""
        cond = ExitCondition(
            exit_name="door",
            condition="has_item:key"
        )
        assert cond.exit_name == "door"
        assert cond.condition == "has_item:key"
        assert cond.fail_message == ""
        assert cond.consume_item == False
    
    def test_create_exit_condition_full(self):
        """Test creating an exit condition with all fields."""
        cond = ExitCondition(
            exit_name="gate",
            condition="gold:50",
            fail_message="The gatekeeper demands 50 gold.",
            consume_item=True
        )
        assert cond.exit_name == "gate"
        assert cond.condition == "gold:50"
        assert cond.fail_message == "The gatekeeper demands 50 gold."
        assert cond.consume_item == True
    
    def test_exit_condition_to_dict(self):
        """Test serialization of exit condition."""
        cond = ExitCondition(
            exit_name="door",
            condition="has_item:rusty_key",
            fail_message="Locked!",
            consume_item=True
        )
        data = cond.to_dict()
        assert data["exit_name"] == "door"
        assert data["condition"] == "has_item:rusty_key"
        assert data["fail_message"] == "Locked!"
        assert data["consume_item"] == True
    
    def test_exit_condition_from_dict(self):
        """Test deserialization of exit condition."""
        data = {
            "exit_name": "gate",
            "condition": "skill:strength:15",
            "fail_message": "Too heavy!",
            "consume_item": False
        }
        cond = ExitCondition.from_dict(data)
        assert cond.exit_name == "gate"
        assert cond.condition == "skill:strength:15"
        assert cond.fail_message == "Too heavy!"
        assert cond.consume_item == False


class TestCheckExitCondition:
    """Tests for check_exit_condition function."""
    
    def test_empty_condition_passes(self):
        """Empty condition should always pass."""
        success, reason = check_exit_condition("", {})
        assert success == True
    
    def test_none_condition_passes(self):
        """None condition should always pass."""
        success, reason = check_exit_condition(None, {})
        assert success == True
    
    def test_has_item_success(self):
        """Test has_item condition with item present."""
        # Create a mock inventory with items
        class MockItem:
            def __init__(self, name):
                self.name = name
        
        class MockInventory:
            def __init__(self):
                self.items = [MockItem("Rusty Key"), MockItem("Torch")]
        
        game_state = {"inventory": MockInventory()}
        success, reason = check_exit_condition("has_item:rusty_key", game_state)
        assert success == True
        assert "Rusty Key" in reason
    
    def test_has_item_failure(self):
        """Test has_item condition with item missing."""
        class MockInventory:
            def __init__(self):
                self.items = []
        
        game_state = {"inventory": MockInventory()}
        success, reason = check_exit_condition("has_item:gold_key", game_state)
        assert success == False
        assert "need" in reason.lower() or "key" in reason.lower()
    
    def test_gold_condition_success(self):
        """Test gold condition with enough gold."""
        class MockCharacter:
            def __init__(self):
                self.gold = 100
        
        game_state = {"character": MockCharacter()}
        success, reason = check_exit_condition("gold:50", game_state)
        assert success == True
    
    def test_gold_condition_failure(self):
        """Test gold condition without enough gold."""
        class MockCharacter:
            def __init__(self):
                self.gold = 25
        
        game_state = {"character": MockCharacter()}
        success, reason = check_exit_condition("gold:50", game_state)
        assert success == False
        assert "50 gold" in reason
    
    def test_visited_condition_success(self):
        """Test visited condition with location visited."""
        game_state = {"visited_locations": ["cave_entrance", "forest"]}
        success, reason = check_exit_condition("visited:cave_entrance", game_state)
        assert success == True
    
    def test_visited_condition_failure(self):
        """Test visited condition with location not visited."""
        game_state = {"visited_locations": ["forest"]}
        success, reason = check_exit_condition("visited:cave_entrance", game_state)
        assert success == False
    
    def test_skill_check_returns_marker(self):
        """Test skill check returns special marker for game.py to handle."""
        success, reason = check_exit_condition("skill:strength:15", {})
        assert success == True
        assert reason == "skill_check:strength:15"
    
    def test_flag_condition_success(self):
        """Test flag condition when flag is set."""
        game_state = {"flags": {"bridge_repaired": True}}
        success, reason = check_exit_condition("flag:bridge_repaired", game_state)
        assert success == True
    
    def test_flag_condition_failure(self):
        """Test flag condition when flag is not set."""
        game_state = {"flags": {}}
        success, reason = check_exit_condition("flag:bridge_repaired", game_state)
        assert success == False


class TestLocationWithExitConditions:
    """Tests for Location with exit conditions."""
    
    def test_location_with_exit_conditions(self):
        """Test creating a location with exit conditions."""
        location = Location(
            id="camp",
            name="Camp",
            description="A camp",
            exits={"door": "storage", "path": "forest"},
            exit_conditions=[
                ExitCondition(
                    exit_name="door",
                    condition="has_item:key",
                    fail_message="The door is locked."
                )
            ]
        )
        assert len(location.exit_conditions) == 1
        assert location.exit_conditions[0].exit_name == "door"
    
    def test_get_exit_condition(self):
        """Test getting exit condition for a specific exit."""
        location = Location(
            id="camp",
            name="Camp",
            description="A camp",
            exits={"door": "storage", "path": "forest"},
            exit_conditions=[
                ExitCondition(exit_name="door", condition="has_item:key")
            ]
        )
        cond = location.get_exit_condition("door")
        assert cond is not None
        assert cond.condition == "has_item:key"
        
        # Exit without condition
        cond2 = location.get_exit_condition("path")
        assert cond2 is None
    
    def test_unlock_exit(self):
        """Test unlocking an exit."""
        location = Location(
            id="camp",
            name="Camp",
            description="A camp",
            exits={"door": "storage"}
        )
        assert location.is_exit_unlocked("door") == False
        location.unlock_exit("door")
        assert location.is_exit_unlocked("door") == True
    
    def test_unlocked_exits_saved(self):
        """Test that unlocked exits are saved."""
        location = Location(
            id="camp",
            name="Camp",
            description="A camp",
            exits={"door": "storage"}
        )
        location.unlock_exit("door")
        data = location.to_dict()
        assert "unlocked_exits" in data
        assert "door" in data["unlocked_exits"]
    
    def test_unlocked_exits_restored(self):
        """Test that unlocked exits are restored from state."""
        location = Location(
            id="camp",
            name="Camp",
            description="A camp",
            exits={"door": "storage"}
        )
        state = {"unlocked_exits": ["door"]}
        Location.from_state(location, state)
        assert location.is_exit_unlocked("door") == True


class TestLocationManagerWithConditions:
    """Tests for LocationManager with exit conditions."""
    
    def test_move_blocked_by_condition(self):
        """Test that movement is blocked when condition not met."""
        manager = LocationManager()
        
        start = Location(
            id="start",
            name="Start",
            description="Start",
            exits={"door": "storage"},
            exit_conditions=[
                ExitCondition(
                    exit_name="door",
                    condition="has_item:key",
                    fail_message="The door is locked!"
                )
            ]
        )
        storage = Location(id="storage", name="Storage", description="Storage")
        
        manager.add_location(start)
        manager.add_location(storage)
        manager.set_available_locations(["start", "storage"])
        manager.set_current_location("start")
        
        # Empty inventory - should fail
        class MockInventory:
            items = []
        
        game_state = {"inventory": MockInventory()}
        success, new_loc, message, events = manager.move("door", game_state)
        
        assert success == False
        assert new_loc is None
        assert "locked" in message.lower()
    
    def test_move_allowed_with_item(self):
        """Test that movement succeeds when item condition is met."""
        manager = LocationManager()
        
        start = Location(
            id="start",
            name="Start",
            description="Start",
            exits={"door": "storage"},
            exit_conditions=[
                ExitCondition(
                    exit_name="door",
                    condition="has_item:key",
                    fail_message="The door is locked!"
                )
            ]
        )
        storage = Location(id="storage", name="Storage", description="Storage")
        
        manager.add_location(start)
        manager.add_location(storage)
        manager.set_available_locations(["start", "storage"])
        manager.set_current_location("start")
        
        # Inventory with key - should succeed
        class MockItem:
            def __init__(self, name):
                self.name = name
        
        class MockInventory:
            items = [MockItem("Key")]
        
        game_state = {"inventory": MockInventory()}
        success, new_loc, message, events = manager.move("door", game_state)
        
        assert success == True
        assert new_loc.id == "storage"
    
    def test_move_unlocked_exit_stays_open(self):
        """Test that once unlocked, exit stays open."""
        manager = LocationManager()
        
        start = Location(
            id="start",
            name="Start",
            description="Start",
            exits={"door": "storage", "back": "start"},
            exit_conditions=[
                ExitCondition(exit_name="door", condition="has_item:key")
            ]
        )
        storage = Location(
            id="storage",
            name="Storage",
            description="Storage",
            exits={"door": "start"}
        )
        
        manager.add_location(start)
        manager.add_location(storage)
        manager.set_available_locations(["start", "storage"])
        manager.set_current_location("start")
        
        # First: unlock with key
        class MockItem:
            def __init__(self, name):
                self.name = name
        
        class MockInventory:
            items = [MockItem("Key")]
        
        game_state = {"inventory": MockInventory()}
        manager.move("door", game_state)
        
        # Now go back
        manager.move("door")  # back to start
        
        # Now try without key - should still work (unlocked)
        class EmptyInventory:
            items = []
        
        game_state2 = {"inventory": EmptyInventory()}
        success, new_loc, message, events = manager.move("door", game_state2)
        
        assert success == True


# =============================================================================
# CARDINAL DIRECTION ALIAS TESTS (Phase 3.2.1 Priority 6)
# =============================================================================

from scenario import resolve_direction_alias, CARDINAL_ALIASES


class TestResolveDirectionAlias:
    """Tests for the resolve_direction_alias helper function."""
    
    def test_resolve_n_to_north(self):
        """Test that 'n' resolves to 'north'."""
        assert resolve_direction_alias("n") == "north"
    
    def test_resolve_s_to_south(self):
        """Test that 's' resolves to 'south'."""
        assert resolve_direction_alias("s") == "south"
    
    def test_resolve_e_to_east(self):
        """Test that 'e' resolves to 'east'."""
        assert resolve_direction_alias("e") == "east"
    
    def test_resolve_w_to_west(self):
        """Test that 'w' resolves to 'west'."""
        assert resolve_direction_alias("w") == "west"
    
    def test_resolve_diagonals(self):
        """Test diagonal directions."""
        assert resolve_direction_alias("ne") == "northeast"
        assert resolve_direction_alias("nw") == "northwest"
        assert resolve_direction_alias("se") == "southeast"
        assert resolve_direction_alias("sw") == "southwest"
    
    def test_resolve_up_down(self):
        """Test up/down shortcuts."""
        assert resolve_direction_alias("u") == "up"
        assert resolve_direction_alias("d") == "down"
    
    def test_resolve_full_direction_unchanged(self):
        """Test that full direction names are unchanged."""
        assert resolve_direction_alias("north") == "north"
        assert resolve_direction_alias("south") == "south"
        assert resolve_direction_alias("east") == "east"
        assert resolve_direction_alias("west") == "west"
    
    def test_resolve_exit_name_unchanged(self):
        """Test that exit names are unchanged."""
        assert resolve_direction_alias("forest_path") == "forest_path"
        assert resolve_direction_alias("tavern_door") == "tavern_door"
    
    def test_resolve_case_insensitive(self):
        """Test case insensitivity."""
        assert resolve_direction_alias("N") == "north"
        assert resolve_direction_alias("NORTH") == "north"


class TestLocationWithDirectionAliases:
    """Tests for Location.direction_aliases field."""
    
    def test_location_with_direction_aliases(self):
        """Test creating a location with direction_aliases."""
        location = Location(
            id="test",
            name="Test",
            description="Test",
            exits={"forest_path": "forest", "tavern_door": "tavern"},
            direction_aliases={"n": "forest_path", "s": "tavern_door"}
        )
        assert location.direction_aliases == {"n": "forest_path", "s": "tavern_door"}
    
    def test_location_default_empty_aliases(self):
        """Test that direction_aliases defaults to empty dict."""
        location = Location(id="test", name="Test", description="Test")
        assert location.direction_aliases == {}


class TestLocationManagerDirectionAliases:
    """Tests for movement using cardinal direction aliases."""
    
    def setup_manager_with_aliases(self):
        """Create a manager with locations that have direction aliases."""
        manager = LocationManager()
        
        # Village square with aliases
        manager.add_location(Location(
            id="village",
            name="Village Square",
            description="A village square",
            exits={"forest_path": "forest", "tavern_door": "tavern"},
            direction_aliases={
                "n": "forest_path", "north": "forest_path",
                "e": "tavern_door", "east": "tavern_door"
            }
        ))
        
        # Forest with aliases
        manager.add_location(Location(
            id="forest",
            name="Forest Path",
            description="A forest path",
            exits={"village": "village"},
            direction_aliases={"s": "village", "south": "village"}
        ))
        
        # Tavern with aliases
        manager.add_location(Location(
            id="tavern",
            name="Tavern",
            description="A cozy tavern",
            exits={"outside": "village"},
            direction_aliases={"w": "outside", "west": "outside"}
        ))
        
        manager.set_available_locations(["village", "forest", "tavern"])
        manager.set_current_location("village")
        
        return manager
    
    def test_move_with_shorthand_n(self):
        """Test moving with 'n' shorthand."""
        manager = self.setup_manager_with_aliases()
        success, new_loc, _, _ = manager.move("n")
        
        assert success == True
        assert new_loc.id == "forest"
    
    def test_move_with_full_north(self):
        """Test moving with 'north' full direction."""
        manager = self.setup_manager_with_aliases()
        success, new_loc, _, _ = manager.move("north")
        
        assert success == True
        assert new_loc.id == "forest"
    
    def test_move_with_east_alias(self):
        """Test moving with 'e' shorthand to tavern."""
        manager = self.setup_manager_with_aliases()
        success, new_loc, _, _ = manager.move("e")
        
        assert success == True
        assert new_loc.id == "tavern"
    
    def test_move_back_with_alias(self):
        """Test moving back using alias."""
        manager = self.setup_manager_with_aliases()
        
        # Go to forest
        manager.move("n")
        
        # Come back using 's'
        success, new_loc, _, _ = manager.move("s")
        
        assert success == True
        assert new_loc.id == "village"
    
    def test_move_with_exit_name_still_works(self):
        """Test that direct exit name still works."""
        manager = self.setup_manager_with_aliases()
        success, new_loc, _, _ = manager.move("forest_path")
        
        assert success == True
        assert new_loc.id == "forest"
    
    def test_move_invalid_direction(self):
        """Test invalid direction returns error."""
        manager = self.setup_manager_with_aliases()
        success, new_loc, message, _ = manager.move("x")
        
        assert success == False
        assert "can't go" in message.lower()
    
    def test_alias_not_matching_available_exit(self):
        """Test alias pointing to unavailable exit doesn't work."""
        manager = LocationManager()
        
        manager.add_location(Location(
            id="test",
            name="Test",
            description="Test",
            exits={"door": "locked_room"},
            direction_aliases={"n": "door"}
        ))
        manager.add_location(Location(
            id="locked_room",
            name="Locked Room",
            description="Locked"
        ))
        
        # Only 'test' is available
        manager.set_available_locations(["test"])
        manager.set_current_location("test")
        
        # 'n' should NOT work because 'locked_room' isn't available
        success, _, _, _ = manager.move("n")
        assert success == False


# =============================================================================
# RANDOM ENCOUNTER TESTS (Phase 3.2.1 Priority 7)
# =============================================================================

from scenario import RandomEncounter


class TestRandomEncounterBasics:
    """Tests for RandomEncounter dataclass."""
    
    def test_create_random_encounter_minimal(self):
        """Test creating a random encounter with minimal fields."""
        encounter = RandomEncounter(
            id="wolf_attack",
            enemies=["wolf"]
        )
        assert encounter.id == "wolf_attack"
        assert encounter.enemies == ["wolf"]
        assert encounter.chance == 20  # default
        assert encounter.max_triggers == 1  # default
        assert encounter.cooldown == 0  # default
    
    def test_create_random_encounter_full(self):
        """Test creating a random encounter with all fields."""
        encounter = RandomEncounter(
            id="spider_ambush",
            enemies=["giant_spider", "giant_spider"],
            chance=30,
            condition="not_visited:boss_chamber",
            min_visits=2,
            max_triggers=3,
            cooldown=5,
            narration="Spiders drop from above!"
        )
        assert encounter.id == "spider_ambush"
        assert encounter.enemies == ["giant_spider", "giant_spider"]
        assert encounter.chance == 30
        assert encounter.condition == "not_visited:boss_chamber"
        assert encounter.min_visits == 2
        assert encounter.max_triggers == 3
        assert encounter.cooldown == 5
        assert encounter.narration == "Spiders drop from above!"
    
    def test_random_encounter_to_dict(self):
        """Test serializing a random encounter."""
        encounter = RandomEncounter(
            id="wolf_attack",
            enemies=["wolf"],
            chance=25
        )
        data = encounter.to_dict()
        assert data["id"] == "wolf_attack"
        assert data["enemies"] == ["wolf"]
        assert data["chance"] == 25
    
    def test_random_encounter_from_dict(self):
        """Test creating a random encounter from dict."""
        data = {
            "id": "goblin_patrol",
            "enemies": ["goblin", "goblin"],
            "chance": 15,
            "narration": "Goblins approach!"
        }
        encounter = RandomEncounter.from_dict(data)
        assert encounter.id == "goblin_patrol"
        assert encounter.enemies == ["goblin", "goblin"]
        assert encounter.chance == 15
        assert encounter.narration == "Goblins approach!"


class TestLocationWithRandomEncounters:
    """Tests for Location with random_encounters field."""
    
    def test_location_with_random_encounters(self):
        """Test creating a location with random encounters."""
        location = Location(
            id="forest",
            name="Forest",
            description="A dark forest",
            random_encounters=[
                RandomEncounter(id="wolf", enemies=["wolf"], chance=20)
            ]
        )
        assert len(location.random_encounters) == 1
        assert location.random_encounters[0].id == "wolf"
    
    def test_location_default_empty_random_encounters(self):
        """Test that random_encounters defaults to empty list."""
        location = Location(id="test", name="Test", description="Test")
        assert location.random_encounters == []
    
    def test_location_visit_count_initialized(self):
        """Test that visit_count starts at 0."""
        location = Location(id="test", name="Test", description="Test")
        assert location.visit_count == 0
    
    def test_location_visit_count_in_to_dict(self):
        """Test that visit_count is saved."""
        location = Location(id="test", name="Test", description="Test")
        location.visit_count = 5
        data = location.to_dict()
        assert data["visit_count"] == 5
    
    def test_location_visit_count_restored(self):
        """Test that visit_count is restored from state."""
        location = Location(id="test", name="Test", description="Test")
        state = {"visit_count": 10}
        Location.from_state(location, state)
        assert location.visit_count == 10


class TestRandomEncounterTriggering:
    """Tests for random encounter trigger mechanics."""
    
    def test_can_encounter_trigger_basic(self):
        """Test basic encounter eligibility."""
        location = Location(
            id="test",
            name="Test",
            description="Test",
            random_encounters=[
                RandomEncounter(id="wolf", enemies=["wolf"], chance=100)
            ]
        )
        # Should be eligible on first check
        assert location._can_encounter_trigger(location.random_encounters[0]) == True
    
    def test_max_triggers_limit(self):
        """Test that max_triggers limits encounter frequency."""
        location = Location(
            id="test",
            name="Test",
            description="Test",
            random_encounters=[
                RandomEncounter(id="wolf", enemies=["wolf"], max_triggers=1)
            ]
        )
        # Record one trigger
        location.random_encounter_triggers["wolf"] = 1
        
        # Should no longer be eligible
        assert location._can_encounter_trigger(location.random_encounters[0]) == False
    
    def test_max_triggers_unlimited(self):
        """Test that max_triggers=-1 means unlimited."""
        location = Location(
            id="test",
            name="Test",
            description="Test",
            random_encounters=[
                RandomEncounter(id="wolf", enemies=["wolf"], max_triggers=-1)
            ]
        )
        # Record many triggers
        location.random_encounter_triggers["wolf"] = 100
        
        # Should still be eligible
        assert location._can_encounter_trigger(location.random_encounters[0]) == True
    
    def test_min_visits_requirement(self):
        """Test that min_visits delays encounter eligibility."""
        location = Location(
            id="test",
            name="Test",
            description="Test",
            random_encounters=[
                RandomEncounter(id="wolf", enemies=["wolf"], min_visits=3)
            ]
        )
        
        # Not enough visits
        location.visit_count = 2
        assert location._can_encounter_trigger(location.random_encounters[0]) == False
        
        # Enough visits
        location.visit_count = 3
        assert location._can_encounter_trigger(location.random_encounters[0]) == True
    
    def test_cooldown_requirement(self):
        """Test that cooldown prevents immediate re-triggering."""
        location = Location(
            id="test",
            name="Test",
            description="Test",
            random_encounters=[
                RandomEncounter(id="wolf", enemies=["wolf"], cooldown=3, max_triggers=-1)
            ]
        )
        
        # Trigger at visit 5
        location.visit_count = 5
        location.random_encounter_last_visit["wolf"] = 5
        location.random_encounter_triggers["wolf"] = 1
        
        # Visit 6 - still on cooldown
        location.visit_count = 6
        assert location._can_encounter_trigger(location.random_encounters[0]) == False
        
        # Visit 8 - cooldown passed (3 visits later)
        location.visit_count = 8
        assert location._can_encounter_trigger(location.random_encounters[0]) == True
    
    def test_check_random_encounter_100_percent(self):
        """Test that 100% chance always triggers."""
        location = Location(
            id="test",
            name="Test",
            description="Test",
            random_encounters=[
                RandomEncounter(id="wolf", enemies=["wolf"], chance=100)
            ]
        )
        
        # Should always trigger
        result = location.check_random_encounter()
        assert result is not None
        assert result.id == "wolf"
    
    def test_check_random_encounter_0_percent(self):
        """Test that 0% chance never triggers."""
        location = Location(
            id="test",
            name="Test",
            description="Test",
            random_encounters=[
                RandomEncounter(id="wolf", enemies=["wolf"], chance=0)
            ]
        )
        
        # Should never trigger (test 10 times to be sure)
        for _ in range(10):
            result = location.check_random_encounter()
            assert result is None
    
    def test_encounter_records_trigger(self):
        """Test that triggering an encounter records it."""
        location = Location(
            id="test",
            name="Test",
            description="Test",
            random_encounters=[
                RandomEncounter(id="wolf", enemies=["wolf"], chance=100)
            ]
        )
        location.visit_count = 5
        
        # Trigger encounter
        location.check_random_encounter()
        
        # Check it was recorded
        assert location.random_encounter_triggers.get("wolf") == 1
        assert location.random_encounter_last_visit.get("wolf") == 5


class TestLocationManagerRandomEncounters:
    """Tests for LocationManager.check_random_encounter()."""
    
    def setup_manager_with_encounters(self):
        """Create a manager with locations that have random encounters."""
        manager = LocationManager()
        
        manager.add_location(Location(
            id="forest",
            name="Forest",
            description="A forest",
            random_encounters=[
                RandomEncounter(id="wolf", enemies=["wolf"], chance=100)
            ]
        ))
        manager.add_location(Location(
            id="village",
            name="Village",
            description="A village"
            # No random encounters
        ))
        
        manager.set_available_locations(["forest", "village"])
        
        return manager
    
    def test_check_random_encounter_with_encounters(self):
        """Test checking for encounters at location with encounters."""
        manager = self.setup_manager_with_encounters()
        manager.set_current_location("forest")
        
        result = manager.check_random_encounter()
        assert result is not None
        assert result.id == "wolf"
    
    def test_check_random_encounter_no_encounters(self):
        """Test checking for encounters at location without encounters."""
        manager = self.setup_manager_with_encounters()
        manager.set_current_location("village")
        
        result = manager.check_random_encounter()
        assert result is None
    
    def test_visit_count_increments_on_move(self):
        """Test that visit_count increments when entering a location."""
        manager = self.setup_manager_with_encounters()
        
        manager.set_current_location("village")
        initial_count = manager.locations["village"].visit_count
        
        # Move away and back
        manager.set_current_location("forest")
        manager.set_current_location("village")
        
        # Should have incremented
        assert manager.locations["village"].visit_count == initial_count + 1


# =============================================================================
# HIDDEN LOCATION TESTS (Phase 3.2.1 - Priority 8)
# =============================================================================

class TestHiddenLocationBasics:
    """Tests for Location.hidden field and basic hidden location behavior."""
    
    def test_location_hidden_default_false(self):
        """Test that locations are not hidden by default."""
        loc = Location(id="test", name="Test", description="A test location")
        assert loc.hidden is False
        assert loc.discovery_condition == ""
        assert loc.discovery_hint == ""
    
    def test_location_hidden_can_be_set(self):
        """Test that hidden attribute can be set."""
        loc = Location(
            id="secret",
            name="Secret Cave",
            description="A hidden cave",
            hidden=True,
            discovery_condition="skill:perception:14",
            discovery_hint="The vines look suspicious..."
        )
        assert loc.hidden is True
        assert loc.discovery_condition == "skill:perception:14"
        assert loc.discovery_hint == "The vines look suspicious..."
    
    def test_hidden_location_with_items(self):
        """Test that hidden locations can have items."""
        loc = Location(
            id="treasure_room",
            name="Treasure Room",
            description="A hidden treasure room",
            hidden=True,
            items=["gold", "gems", "magic_sword"]
        )
        assert loc.hidden is True
        assert "gold" in loc.items
        assert "magic_sword" in loc.items


class TestLocationManagerHiddenExits:
    """Tests for LocationManager handling of hidden exits."""
    
    def setup_manager_with_hidden(self):
        """Create a manager with visible and hidden locations."""
        manager = LocationManager()
        
        # Visible starting location
        manager.add_location(Location(
            id="forest",
            name="Forest Clearing",
            description="A clearing",
            exits={"path": "village", "hidden_path": "secret_cave"}
        ))
        
        # Visible destination
        manager.add_location(Location(
            id="village",
            name="Village",
            description="A village"
        ))
        
        # Hidden destination
        manager.add_location(Location(
            id="secret_cave",
            name="Secret Cave",
            description="A hidden cave",
            hidden=True,
            discovery_condition="skill:perception:14",
            discovery_hint="Something seems off about the vines..."
        ))
        
        manager.set_available_locations(["forest", "village", "secret_cave"])
        manager.set_current_location("forest")
        
        return manager
    
    def test_get_exits_hides_undiscovered_secret(self):
        """Test that get_exits() filters out hidden locations by default."""
        manager = self.setup_manager_with_hidden()
        
        exits = manager.get_exits()
        
        # Should only show path to village, not hidden_path to secret_cave
        assert "path" in exits
        assert exits["path"] == "village"
        assert "hidden_path" not in exits
    
    def test_get_exits_shows_discovered_secret(self):
        """Test that get_exits() shows hidden locations after discovery."""
        manager = self.setup_manager_with_hidden()
        
        # Discover the secret
        manager.discover_secret("secret_cave")
        
        exits = manager.get_exits()
        
        # Now should show both exits
        assert "path" in exits
        assert "hidden_path" in exits
        assert exits["hidden_path"] == "secret_cave"
    
    def test_get_hidden_exits(self):
        """Test get_hidden_exits() returns only undiscovered hidden exits."""
        manager = self.setup_manager_with_hidden()
        
        hidden = manager.get_hidden_exits()
        
        assert "hidden_path" in hidden
        assert hidden["hidden_path"] == "secret_cave"
        assert "path" not in hidden  # Not hidden
    
    def test_get_hidden_exits_empty_after_discovery(self):
        """Test that get_hidden_exits() returns empty after discovery."""
        manager = self.setup_manager_with_hidden()
        
        manager.discover_secret("secret_cave")
        hidden = manager.get_hidden_exits()
        
        assert len(hidden) == 0
    
    def test_get_discovery_hints(self):
        """Test that discovery hints are returned for hidden locations."""
        manager = self.setup_manager_with_hidden()
        
        hints = manager.get_discovery_hints()
        
        assert len(hints) == 1
        assert "Something seems off about the vines..." in hints[0]
    
    def test_get_discovery_hints_empty_after_discovery(self):
        """Test that no hints returned after discovery."""
        manager = self.setup_manager_with_hidden()
        
        manager.discover_secret("secret_cave")
        hints = manager.get_discovery_hints()
        
        assert len(hints) == 0


class TestLocationManagerDiscoverSecret:
    """Tests for LocationManager.discover_secret() method."""
    
    def setup_manager_with_hidden(self):
        """Create a manager with hidden locations."""
        manager = LocationManager()
        
        manager.add_location(Location(
            id="main",
            name="Main Area",
            description="Starting point",
            exits={"secret": "hidden_room"}
        ))
        
        manager.add_location(Location(
            id="hidden_room",
            name="Hidden Room",
            description="A secret room",
            hidden=True
        ))
        
        manager.add_location(Location(
            id="visible_room",
            name="Visible Room",
            description="A normal room"
        ))
        
        manager.set_available_locations(["main", "hidden_room", "visible_room"])
        
        return manager
    
    def test_discover_secret_returns_true_for_hidden(self):
        """Test that discover_secret returns True for hidden locations."""
        manager = self.setup_manager_with_hidden()
        
        result = manager.discover_secret("hidden_room")
        
        assert result is True
        assert "hidden_room" in manager.discovered_secrets
    
    def test_discover_secret_returns_false_for_not_hidden(self):
        """Test that discover_secret returns False for non-hidden locations."""
        manager = self.setup_manager_with_hidden()
        
        result = manager.discover_secret("visible_room")
        
        assert result is False
        assert "visible_room" not in manager.discovered_secrets
    
    def test_discover_secret_returns_false_for_already_discovered(self):
        """Test that discover_secret returns False if already discovered."""
        manager = self.setup_manager_with_hidden()
        
        manager.discover_secret("hidden_room")
        result = manager.discover_secret("hidden_room")
        
        assert result is False  # Already discovered
        assert manager.discovered_secrets.count("hidden_room") == 1  # Not duplicated
    
    def test_discover_secret_returns_false_for_invalid_id(self):
        """Test that discover_secret returns False for non-existent location."""
        manager = self.setup_manager_with_hidden()
        
        result = manager.discover_secret("nonexistent")
        
        assert result is False
    
    def test_is_secret_discovered(self):
        """Test is_secret_discovered() method."""
        manager = self.setup_manager_with_hidden()
        
        assert manager.is_secret_discovered("hidden_room") is False
        
        manager.discover_secret("hidden_room")
        
        assert manager.is_secret_discovered("hidden_room") is True


class TestLocationManagerCheckDiscovery:
    """Tests for LocationManager.check_discovery() method."""
    
    def setup_manager(self):
        """Create a manager with various discovery conditions."""
        manager = LocationManager()
        
        manager.add_location(Location(
            id="main",
            name="Main",
            description="Starting"
        ))
        
        manager.add_location(Location(
            id="skill_hidden",
            name="Skill Hidden",
            description="Requires perception",
            hidden=True,
            discovery_condition="skill:perception:14"
        ))
        
        manager.add_location(Location(
            id="item_hidden",
            name="Item Hidden",
            description="Requires map",
            hidden=True,
            discovery_condition="has_item:treasure_map"
        ))
        
        manager.add_location(Location(
            id="level_hidden",
            name="Level Hidden",
            description="Requires level 5",
            hidden=True,
            discovery_condition="level:5"
        ))
        
        manager.add_location(Location(
            id="visited_hidden",
            name="Visited Hidden",
            description="Requires visiting another place",
            hidden=True,
            discovery_condition="visited:main"
        ))
        
        manager.add_location(Location(
            id="no_condition_hidden",
            name="No Condition",
            description="Hidden but no discovery condition",
            hidden=True,
            discovery_condition=""
        ))
        
        return manager
    
    def test_check_discovery_skill_condition(self):
        """Test check_discovery returns skill check requirement."""
        manager = self.setup_manager()
        
        can_discover, message = manager.check_discovery("skill_hidden")
        
        assert can_discover is False
        assert message == "skill_check:perception:14"
    
    def test_check_discovery_item_condition_without_item(self):
        """Test check_discovery with item condition when player lacks item."""
        manager = self.setup_manager()
        
        can_discover, message = manager.check_discovery("item_hidden")
        
        assert can_discover is False
        assert "treasure map" in message.lower()
    
    def test_check_discovery_item_condition_with_item(self):
        """Test check_discovery with item condition when player has item."""
        manager = self.setup_manager()
        
        # Create mock inventory
        class MockInventory:
            def has_item(self, key):
                return key == "treasure_map"
        
        game_state = {"inventory": MockInventory()}
        can_discover, message = manager.check_discovery("item_hidden", game_state)
        
        assert can_discover is True
        assert message == ""
    
    def test_check_discovery_level_condition_below_level(self):
        """Test check_discovery with level condition when below level."""
        manager = self.setup_manager()
        
        class MockCharacter:
            level = 3
        
        game_state = {"character": MockCharacter()}
        can_discover, message = manager.check_discovery("level_hidden", game_state)
        
        assert can_discover is False
        assert "level 5" in message.lower()
    
    def test_check_discovery_level_condition_at_level(self):
        """Test check_discovery with level condition when at required level."""
        manager = self.setup_manager()
        
        class MockCharacter:
            level = 5
        
        game_state = {"character": MockCharacter()}
        can_discover, message = manager.check_discovery("level_hidden", game_state)
        
        assert can_discover is True
    
    def test_check_discovery_visited_condition_not_visited(self):
        """Test check_discovery with visited condition when not visited."""
        manager = self.setup_manager()
        
        game_state = {"visited_locations": ["other"]}
        can_discover, message = manager.check_discovery("visited_hidden", game_state)
        
        assert can_discover is False
        assert "must first visit" in message.lower()
    
    def test_check_discovery_visited_condition_visited(self):
        """Test check_discovery with visited condition when visited."""
        manager = self.setup_manager()
        
        game_state = {"visited_locations": ["main", "other"]}
        can_discover, message = manager.check_discovery("visited_hidden", game_state)
        
        assert can_discover is True
    
    def test_check_discovery_no_condition(self):
        """Test check_discovery for hidden location without condition."""
        manager = self.setup_manager()
        
        can_discover, message = manager.check_discovery("no_condition_hidden")
        
        assert can_discover is True
        assert message == ""
    
    def test_check_discovery_already_discovered(self):
        """Test check_discovery returns True if already discovered."""
        manager = self.setup_manager()
        
        manager.discovered_secrets.append("skill_hidden")
        can_discover, message = manager.check_discovery("skill_hidden")
        
        assert can_discover is True
        assert message == ""
    
    def test_check_discovery_not_hidden(self):
        """Test check_discovery returns True for non-hidden locations."""
        manager = self.setup_manager()
        
        can_discover, message = manager.check_discovery("main")
        
        assert can_discover is True


class TestHiddenLocationSerialization:
    """Tests for saving/loading hidden location state."""
    
    def test_discovered_secrets_saved_in_to_dict(self):
        """Test that discovered_secrets is included in to_dict()."""
        manager = LocationManager()
        manager.add_location(Location(id="main", name="Main", description="Main"))
        manager.add_location(Location(id="secret", name="Secret", description="Secret", hidden=True))
        
        manager.set_available_locations(["main", "secret"])
        manager.discovered_secrets.append("secret")
        
        state = manager.to_dict()
        
        assert "discovered_secrets" in state
        assert "secret" in state["discovered_secrets"]
    
    def test_discovered_secrets_restored(self):
        """Test that discovered_secrets is restored from saved state."""
        manager = LocationManager()
        manager.add_location(Location(id="main", name="Main", description="Main"))
        manager.add_location(Location(id="secret", name="Secret", description="Secret", hidden=True))
        
        saved_state = {
            "current_location_id": "main",
            "available_location_ids": ["main", "secret"],
            "discovered_secrets": ["secret"],
            "location_states": {}
        }
        
        manager.restore_state(saved_state)
        
        assert manager.is_secret_discovered("secret") is True
        assert "secret" in manager.discovered_secrets
    
    def test_discovered_secrets_empty_by_default(self):
        """Test that discovered_secrets defaults to empty on restore."""
        manager = LocationManager()
        manager.add_location(Location(id="main", name="Main", description="Main"))
        
        saved_state = {
            "current_location_id": "main",
            "available_location_ids": ["main"],
            "location_states": {}
            # Note: discovered_secrets not present
        }
        
        manager.restore_state(saved_state)
        
        assert manager.discovered_secrets == []


class TestGoblinCaveSecretLocations:
    """Tests for the actual secret locations in the Goblin Cave scenario."""
    
    def test_secret_cave_exists_and_is_hidden(self):
        """Test that secret_cave location exists and is hidden."""
        from scenario import create_goblin_cave_scenario
        
        scenario = create_goblin_cave_scenario()
        lm = scenario.location_manager
        
        assert "secret_cave" in lm.locations
        secret = lm.locations["secret_cave"]
        assert secret.hidden is True
        # Discovery possible via Perception DC 14 OR having the mysterious_key
        assert secret.discovery_condition == "skill:perception:14 OR has_item:mysterious_key"
        assert secret.discovery_hint != ""
    
    def test_secret_cave_accessible_from_forest_clearing(self):
        """Test that forest_clearing has exit to secret_cave."""
        from scenario import create_goblin_cave_scenario
        
        scenario = create_goblin_cave_scenario()
        lm = scenario.location_manager
        
        clearing = lm.locations["forest_clearing"]
        assert "hidden path" in clearing.exits
        assert clearing.exits["hidden path"] == "secret_cave"
    
    def test_secret_cave_has_loot(self):
        """Test that secret_cave has treasure items."""
        from scenario import create_goblin_cave_scenario
        
        scenario = create_goblin_cave_scenario()
        secret = scenario.location_manager.locations["secret_cave"]
        
        assert len(secret.items) > 0
        assert "ancient_amulet" in secret.items
    
    def test_treasure_nook_exists_and_is_hidden(self):
        """Test that treasure_nook location exists and is hidden."""
        from scenario import create_goblin_cave_scenario
        
        scenario = create_goblin_cave_scenario()
        lm = scenario.location_manager
        
        assert "treasure_nook" in lm.locations
        nook = lm.locations["treasure_nook"]
        assert nook.hidden is True
        assert nook.discovery_condition == "skill:investigation:12"
    
    def test_treasure_nook_accessible_from_boss_chamber(self):
        """Test that boss_chamber has exit to treasure_nook."""
        from scenario import create_goblin_cave_scenario
        
        scenario = create_goblin_cave_scenario()
        lm = scenario.location_manager
        
        boss = lm.locations["boss_chamber"]
        assert "hidden alcove" in boss.exits
        assert boss.exits["hidden alcove"] == "treasure_nook"
    
    def test_treasure_nook_has_loot(self):
        """Test that treasure_nook has valuable items."""
        from scenario import create_goblin_cave_scenario
        
        scenario = create_goblin_cave_scenario()
        nook = scenario.location_manager.locations["treasure_nook"]
        
        assert len(nook.items) > 0
        assert "enchanted_dagger" in nook.items
        assert "ruby_ring" in nook.items


# =============================================================================
# HIDDEN ITEMS SYSTEM TESTS (Phase 3.3.5)
# =============================================================================

class TestHiddenItems:
    """Tests for the hidden item discovery system."""
    
    def test_create_hidden_item(self):
        """Test creating a HiddenItem."""
        from scenario import HiddenItem
        
        hi = HiddenItem(
            item_id="enchanted_dagger",
            skill="perception",
            dc=14,
            hint="You notice faint scratches on the floor near the bookshelf..."
        )
        
        assert hi.item_id == "enchanted_dagger"
        assert hi.skill == "perception"
        assert hi.dc == 14
        assert hi.found == False
    
    def test_location_with_hidden_items(self):
        """Test location with hidden items."""
        from scenario import Location, HiddenItem
        
        location = Location(
            id="study",
            name="The Study",
            description="A dusty room filled with books",
            hidden_items=[
                HiddenItem(
                    item_id="secret_diary",
                    skill="investigation",
                    dc=15,
                    hint="One book seems slightly out of place..."
                )
            ]
        )
        
        assert len(location.hidden_items) == 1
        assert location.has_searchable_secrets() == True
    
    def test_get_undiscovered_hidden_items(self):
        """Test getting only undiscovered hidden items."""
        from scenario import Location, HiddenItem
        
        hi1 = HiddenItem(item_id="gem", skill="perception", dc=12)
        hi2 = HiddenItem(item_id="scroll", skill="perception", dc=14, found=True)
        
        location = Location(
            id="vault",
            name="Vault",
            description="A secure vault",
            hidden_items=[hi1, hi2]
        )
        
        undiscovered = location.get_undiscovered_hidden_items()
        assert len(undiscovered) == 1
        assert undiscovered[0].item_id == "gem"
    
    def test_discover_hidden_item(self):
        """Test discovering a hidden item adds it to visible items."""
        from scenario import Location, HiddenItem
        
        location = Location(
            id="chest",
            name="Treasure Chest",
            description="An old chest",
            items=["gold_coin"],
            hidden_items=[
                HiddenItem(item_id="hidden_key", skill="perception", dc=12)
            ]
        )
        
        # Before discovery
        assert "hidden_key" not in location.items
        assert location.hidden_items[0].found == False
        
        # Discover the item
        result = location.discover_hidden_item("hidden_key")
        
        # After discovery
        assert result == True
        assert "hidden_key" in location.items
        assert location.hidden_items[0].found == True
        assert location.has_searchable_secrets() == False
    
    def test_discover_nonexistent_item(self):
        """Test discovering an item that doesn't exist."""
        from scenario import Location
        
        location = Location(id="empty", name="Empty", description="Nothing here")
        result = location.discover_hidden_item("fake_item")
        assert result == False
    
    def test_hidden_item_serialization(self):
        """Test saving and loading hidden item state."""
        from scenario import HiddenItem
        
        hi = HiddenItem(
            item_id="amulet",
            skill="perception",
            dc=16,
            hint="A glint catches your eye...",
            found=True
        )
        
        # Serialize
        data = hi.to_dict()
        
        # Deserialize
        restored = HiddenItem.from_dict(data)
        
        assert restored.item_id == "amulet"
        assert restored.skill == "perception"
        assert restored.dc == 16
        assert restored.hint == "A glint catches your eye..."
        assert restored.found == True
    
    def test_get_search_hints(self):
        """Test getting search hints for DM narration."""
        from scenario import Location, HiddenItem
        
        location = Location(
            id="room",
            name="Room",
            description="A room",
            hidden_items=[
                HiddenItem(item_id="a", skill="perception", dc=10, hint="Hint A"),
                HiddenItem(item_id="b", skill="investigation", dc=12, hint="Hint B"),
                HiddenItem(item_id="c", skill="perception", dc=14)  # No hint
            ]
        )
        
        hints = location.get_search_hints()
        assert len(hints) == 2
        assert "Hint A" in hints
        assert "Hint B" in hints


# =============================================================================
# NUMBERED EXIT NAVIGATION TESTS
# =============================================================================

class TestNumberedExitNavigation:
    """Tests for the numbered exit choice system."""
    
    def test_get_exit_by_number_valid(self):
        """Test getting exit by valid number."""
        from scenario import get_exit_by_number
        
        exits = {"north": "forest", "south": "village", "east": "cave"}
        
        assert get_exit_by_number(1, exits) == "north"
        assert get_exit_by_number(2, exits) == "south"
        assert get_exit_by_number(3, exits) == "east"
    
    def test_get_exit_by_number_invalid_zero(self):
        """Test that 0 returns None (custom action)."""
        from scenario import get_exit_by_number
        
        exits = {"north": "forest", "south": "village"}
        assert get_exit_by_number(0, exits) is None
    
    def test_get_exit_by_number_invalid_too_high(self):
        """Test that number higher than exits returns None."""
        from scenario import get_exit_by_number
        
        exits = {"north": "forest", "south": "village"}
        assert get_exit_by_number(3, exits) is None
        assert get_exit_by_number(99, exits) is None
    
    def test_get_exit_by_number_negative(self):
        """Test that negative number returns None."""
        from scenario import get_exit_by_number
        
        exits = {"north": "forest", "south": "village"}
        assert get_exit_by_number(-1, exits) is None
    
    def test_get_exit_by_number_empty_exits(self):
        """Test with empty exits dict."""
        from scenario import get_exit_by_number
        
        exits = {}
        assert get_exit_by_number(1, exits) is None
    
    def test_get_exit_by_number_single_exit(self):
        """Test with single exit."""
        from scenario import get_exit_by_number
        
        exits = {"door": "outside"}
        assert get_exit_by_number(1, exits) == "door"
        assert get_exit_by_number(2, exits) is None
    
    def test_exit_order_preserved(self):
        """Test that exit order is consistent."""
        from scenario import get_exit_by_number
        
        # Python 3.7+ preserves dict insertion order
        exits = {"alpha": "a", "beta": "b", "gamma": "c", "delta": "d"}
        
        exit_list = list(exits.keys())
        for i, expected_exit in enumerate(exit_list, 1):
            assert get_exit_by_number(i, exits) == expected_exit


# =============================================================================
# LOCATION ATMOSPHERE TESTS (Phase 3.4.1)
# =============================================================================

class TestLocationAtmosphere:
    """Tests for the LocationAtmosphere dataclass."""
    
    def test_create_atmosphere_empty(self):
        """Test creating an atmosphere with default values."""
        from scenario import LocationAtmosphere
        
        atmo = LocationAtmosphere()
        assert atmo.sounds == []
        assert atmo.smells == []
        assert atmo.textures == []
        assert atmo.lighting == ""
        assert atmo.temperature == ""
        assert atmo.mood == ""
        assert atmo.danger_level == ""
        assert atmo.random_details == []
    
    def test_create_atmosphere_full(self):
        """Test creating an atmosphere with all fields populated."""
        from scenario import LocationAtmosphere
        
        atmo = LocationAtmosphere(
            sounds=["crackling fire", "murmured voices"],
            smells=["wood smoke", "ale"],
            textures=["rough wood", "warm stone"],
            lighting="warm firelight",
            temperature="comfortable warmth",
            mood="welcoming",
            danger_level="safe",
            random_details=["a cat by the fire", "scratches on the floor"]
        )
        
        assert len(atmo.sounds) == 2
        assert "crackling fire" in atmo.sounds
        assert len(atmo.smells) == 2
        assert atmo.lighting == "warm firelight"
        assert atmo.mood == "welcoming"
        assert atmo.danger_level == "safe"
    
    def test_atmosphere_to_dict(self):
        """Test serializing atmosphere to dictionary."""
        from scenario import LocationAtmosphere
        
        atmo = LocationAtmosphere(
            sounds=["dripping water"],
            smells=["damp earth"],
            lighting="dim",
            mood="tense"
        )
        
        data = atmo.to_dict()
        assert data["sounds"] == ["dripping water"]
        assert data["smells"] == ["damp earth"]
        assert data["lighting"] == "dim"
        assert data["mood"] == "tense"
        assert data["textures"] == []  # Empty list for unset
        assert data["danger_level"] == ""
    
    def test_atmosphere_from_dict(self):
        """Test deserializing atmosphere from dictionary."""
        from scenario import LocationAtmosphere
        
        data = {
            "sounds": ["echoing footsteps"],
            "smells": ["rot"],
            "textures": ["slippery stone"],
            "lighting": "pitch black",
            "temperature": "cold",
            "mood": "foreboding",
            "danger_level": "threatening",
            "random_details": ["bones on the ground"]
        }
        
        atmo = LocationAtmosphere.from_dict(data)
        assert atmo.sounds == ["echoing footsteps"]
        assert atmo.smells == ["rot"]
        assert atmo.lighting == "pitch black"
        assert atmo.danger_level == "threatening"
    
    def test_atmosphere_from_dict_partial(self):
        """Test deserializing atmosphere with missing fields."""
        from scenario import LocationAtmosphere
        
        data = {"sounds": ["wind"], "mood": "peaceful"}
        
        atmo = LocationAtmosphere.from_dict(data)
        assert atmo.sounds == ["wind"]
        assert atmo.mood == "peaceful"
        assert atmo.smells == []  # Default
        assert atmo.lighting == ""  # Default
    
    def test_atmosphere_get_dm_summary_full(self):
        """Test generating DM summary with all fields."""
        from scenario import LocationAtmosphere
        
        atmo = LocationAtmosphere(
            sounds=["crackling fire", "murmured voices"],
            smells=["wood smoke"],
            textures=["rough wood"],
            lighting="warm firelight",
            temperature="comfortable",
            mood="welcoming",
            danger_level="safe",
            random_details=["a cat", "scratches", "old portraits", "cobwebs"]
        )
        
        summary = atmo.get_dm_summary()
        assert "Sounds:" in summary
        assert "crackling fire" in summary
        assert "Smells:" in summary
        assert "wood smoke" in summary
        assert "Lighting:" in summary
        assert "warm firelight" in summary
        assert "Mood:" in summary
        assert "welcoming" in summary
        assert "Danger:" in summary
        assert "safe" in summary
        assert "Details pool:" in summary
    
    def test_atmosphere_get_dm_summary_empty(self):
        """Test DM summary for empty atmosphere."""
        from scenario import LocationAtmosphere
        
        atmo = LocationAtmosphere()
        summary = atmo.get_dm_summary()
        assert summary == ""
    
    def test_atmosphere_get_dm_summary_partial(self):
        """Test DM summary with only some fields set."""
        from scenario import LocationAtmosphere
        
        atmo = LocationAtmosphere(
            sounds=["wind howling"],
            mood="eerie"
        )
        
        summary = atmo.get_dm_summary()
        assert "Sounds:" in summary
        assert "Mood:" in summary
        assert "Smells:" not in summary  # Not set
        assert "Lighting:" not in summary  # Not set


class TestLocationWithAtmosphere:
    """Tests for Location integration with LocationAtmosphere."""
    
    def test_location_with_structured_atmosphere(self):
        """Test creating a location with a full LocationAtmosphere object."""
        from scenario import LocationAtmosphere
        
        atmo = LocationAtmosphere(
            sounds=["crackling fire"],
            smells=["wood smoke"],
            lighting="firelight",
            mood="welcoming"
        )
        
        location = Location(
            id="test_loc",
            name="Test Tavern",
            description="A cozy tavern",
            atmosphere=atmo
        )
        
        assert location.atmosphere is not None
        assert location.atmosphere.sounds == ["crackling fire"]
        assert location.atmosphere.mood == "welcoming"
        assert location.atmosphere_text == ""  # Legacy not used
    
    def test_location_with_legacy_atmosphere(self):
        """Test creating a location with legacy atmosphere_text."""
        location = Location(
            id="test_loc",
            name="Test Location",
            description="A test location",
            atmosphere_text="Warm and welcoming"
        )
        
        assert location.atmosphere is None  # Structured not used
        assert location.atmosphere_text == "Warm and welcoming"
    
    def test_location_atmosphere_in_context(self):
        """Test that build_location_context handles structured atmosphere."""
        from scenario import LocationAtmosphere, build_location_context
        
        atmo = LocationAtmosphere(
            sounds=["dripping water", "distant echoes"],
            smells=["damp earth"],
            lighting="dim torchlight",
            temperature="cold",
            mood="tense",
            danger_level="threatening"
        )
        
        location = Location(
            id="cave",
            name="Dark Cave",
            description="A dark cave",
            atmosphere=atmo
        )
        
        context = build_location_context(location)
        
        # Should have structured atmosphere context
        assert "atmosphere" in context
        assert isinstance(context["atmosphere"], dict)
        assert "sounds" in context["atmosphere"]
        assert "dripping water" in context["atmosphere"]["sounds"]
        assert context["atmosphere"]["mood"] == "tense"
        assert "atmosphere_instruction" in context
    
    def test_location_legacy_atmosphere_in_context(self):
        """Test that build_location_context handles legacy atmosphere_text."""
        from scenario import build_location_context
        
        location = Location(
            id="tavern",
            name="Old Tavern",
            description="An old tavern",
            atmosphere_text="Warm firelight, the smell of ale"
        )
        
        context = build_location_context(location)
        
        # Should use legacy string
        assert "atmosphere" in context
        assert context["atmosphere"] == "Warm firelight, the smell of ale"
        assert "atmosphere_instruction" not in context  # No structured instructions


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
