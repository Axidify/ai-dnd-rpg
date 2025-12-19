"""
Test Travel Menu System (Phase 3.2.1 Priority 9)
Tests for the numbered travel menu, approach detection, and danger indicators.
"""

import os
import sys
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from game import (
    parse_approach_intent, 
    is_destination_dangerous, 
    get_destination_danger_level,
    APPROACH_KEYWORDS
)
from scenario import Location, LocationAtmosphere, RandomEncounter


# =============================================================================
# APPROACH KEYWORDS DETECTION TESTS
# =============================================================================

class TestParseApproachIntent:
    """Test approach intent parsing from player input."""
    
    def test_empty_input_returns_normal(self):
        """Empty input should return normal approach."""
        approach_type, skill = parse_approach_intent("")
        assert approach_type == "normal"
        assert skill is None
    
    def test_whitespace_input_returns_normal(self):
        """Whitespace-only input should return normal approach."""
        approach_type, skill = parse_approach_intent("   ")
        assert approach_type == "normal"
        assert skill is None
    
    def test_none_input_returns_normal(self):
        """None input should return normal approach."""
        approach_type, skill = parse_approach_intent(None)
        assert approach_type == "normal"
        assert skill is None
    
    # Stealth keywords
    def test_sneak_detected(self):
        """'sneak' should trigger stealth."""
        approach_type, skill = parse_approach_intent("sneak")
        assert approach_type == "stealth"
        assert skill == "stealth"
    
    def test_quietly_detected(self):
        """'quietly' should trigger stealth."""
        approach_type, skill = parse_approach_intent("quietly")
        assert approach_type == "stealth"
        assert skill == "stealth"
    
    def test_sneak_in_sentence(self):
        """'sneak' in a sentence should still trigger stealth."""
        approach_type, skill = parse_approach_intent("I want to sneak carefully")
        assert approach_type == "stealth"
        assert skill == "stealth"
    
    def test_creep_detected(self):
        """'creep' should trigger stealth."""
        approach_type, skill = parse_approach_intent("creep forward")
        assert approach_type == "stealth"
        assert skill == "stealth"
    
    def test_silently_detected(self):
        """'silently' should trigger stealth."""
        approach_type, skill = parse_approach_intent("move silently")
        assert approach_type == "stealth"
        assert skill == "stealth"
    
    def test_shadows_detected(self):
        """'shadows' should trigger stealth."""
        approach_type, skill = parse_approach_intent("stick to the shadows")
        assert approach_type == "stealth"
        assert skill == "stealth"
    
    # Urgent keywords
    def test_run_detected(self):
        """'run' should trigger urgent."""
        approach_type, skill = parse_approach_intent("run")
        assert approach_type == "urgent"
        assert skill is None
    
    def test_rush_detected(self):
        """'rush' should trigger urgent."""
        approach_type, skill = parse_approach_intent("rush in")
        assert approach_type == "urgent"
        assert skill is None
    
    def test_sprint_detected(self):
        """'sprint' should trigger urgent."""
        approach_type, skill = parse_approach_intent("sprint to the door")
        assert approach_type == "urgent"
        assert skill is None
    
    def test_flee_detected(self):
        """'flee' should trigger urgent."""
        approach_type, skill = parse_approach_intent("flee quickly")
        assert approach_type == "urgent"
        assert skill is None
    
    def test_hurry_detected(self):
        """'hurry' should trigger urgent."""
        approach_type, skill = parse_approach_intent("hurry over there")
        assert approach_type == "urgent"
        assert skill is None
    
    # Cautious keywords
    def test_carefully_detected(self):
        """'carefully' should trigger cautious."""
        approach_type, skill = parse_approach_intent("carefully")
        assert approach_type == "cautious"
        assert skill == "perception"
    
    def test_cautiously_detected(self):
        """'cautiously' should trigger cautious."""
        approach_type, skill = parse_approach_intent("proceed cautiously")
        assert approach_type == "cautious"
        assert skill == "perception"
    
    def test_look_around_detected(self):
        """'look around' should trigger cautious."""
        approach_type, skill = parse_approach_intent("look around first")
        assert approach_type == "cautious"
        assert skill == "perception"
    
    def test_wary_detected(self):
        """'wary' should trigger cautious."""
        approach_type, skill = parse_approach_intent("stay wary")
        assert approach_type == "cautious"
        assert skill == "perception"
    
    # Case insensitivity
    def test_case_insensitive_sneak(self):
        """Keywords should be case-insensitive."""
        approach_type, skill = parse_approach_intent("SNEAK")
        assert approach_type == "stealth"
        assert skill == "stealth"
    
    def test_case_insensitive_carefully(self):
        """Keywords should be case-insensitive."""
        approach_type, skill = parse_approach_intent("CAREFULLY")
        assert approach_type == "cautious"
        assert skill == "perception"
    
    # Normal (no keywords)
    def test_walk_normally_returns_normal(self):
        """Regular walking should return normal."""
        approach_type, skill = parse_approach_intent("walk normally")
        assert approach_type == "normal"
        assert skill is None
    
    def test_gibberish_returns_normal(self):
        """Unrecognized input should return normal."""
        approach_type, skill = parse_approach_intent("xyz abc 123")
        assert approach_type == "normal"
        assert skill is None


# =============================================================================
# DANGER LEVEL DETECTION TESTS
# =============================================================================

class TestGetDestinationDangerLevel:
    """Test danger level extraction from locations."""
    
    def test_safe_location(self):
        """Location with safe danger_level."""
        loc = Location(
            id="tavern",
            name="Tavern",
            description="A cozy tavern.",
            atmosphere=LocationAtmosphere(danger_level="safe")
        )
        assert get_destination_danger_level(loc) == "safe"
    
    def test_threatening_location(self):
        """Location with threatening danger_level."""
        loc = Location(
            id="cave",
            name="Dark Cave",
            description="A menacing cave.",
            atmosphere=LocationAtmosphere(danger_level="threatening")
        )
        assert get_destination_danger_level(loc) == "threatening"
    
    def test_deadly_location(self):
        """Location with deadly danger_level."""
        loc = Location(
            id="boss",
            name="Boss Lair",
            description="The final confrontation.",
            atmosphere=LocationAtmosphere(danger_level="deadly")
        )
        assert get_destination_danger_level(loc) == "deadly"
    
    def test_location_with_encounter_is_threatening(self):
        """Location with fixed encounter should be threatening."""
        loc = Location(
            id="ambush",
            name="Ambush Point",
            description="Danger awaits.",
            encounter=["goblin", "goblin"]
        )
        assert get_destination_danger_level(loc) == "threatening"
    
    def test_location_with_triggered_encounter_is_unknown(self):
        """Location with already-triggered encounter should be unknown."""
        loc = Location(
            id="cleared",
            name="Cleared Room",
            description="You cleared this room.",
            encounter=["goblin"],
            encounter_triggered=True
        )
        assert get_destination_danger_level(loc) == "unknown"
    
    def test_location_with_random_encounters_is_uneasy(self):
        """Location with random encounters should be uneasy."""
        loc = Location(
            id="forest",
            name="Forest Path",
            description="A winding path.",
            random_encounters=[
                RandomEncounter(id="wolf", enemies=["wolf"], chance=20)
            ]
        )
        assert get_destination_danger_level(loc) == "uneasy"
    
    def test_location_without_atmosphere_is_unknown(self):
        """Location without atmosphere data should be unknown."""
        loc = Location(
            id="plain",
            name="Plain Room",
            description="A plain room."
        )
        assert get_destination_danger_level(loc) == "unknown"


class TestIsDestinationDangerous:
    """Test dangerous destination detection."""
    
    def test_safe_visited_location_not_dangerous(self):
        """A safe, visited location should not be dangerous."""
        loc = Location(
            id="tavern",
            name="Tavern",
            description="A cozy tavern.",
            atmosphere=LocationAtmosphere(danger_level="safe"),
            visited=True
        )
        # Mock LocationManager
        class MockLocMgr:
            locations = {"tavern": loc}
        
        assert is_destination_dangerous(loc, MockLocMgr()) == False
    
    def test_threatening_location_is_dangerous(self):
        """A threatening location should be dangerous."""
        loc = Location(
            id="cave",
            name="Dark Cave",
            description="A menacing cave.",
            atmosphere=LocationAtmosphere(danger_level="threatening"),
            visited=True
        )
        class MockLocMgr:
            locations = {"cave": loc}
        
        assert is_destination_dangerous(loc, MockLocMgr()) == True
    
    def test_deadly_location_is_dangerous(self):
        """A deadly location should be dangerous."""
        loc = Location(
            id="boss",
            name="Boss Lair",
            description="Final battle.",
            atmosphere=LocationAtmosphere(danger_level="deadly"),
            visited=True
        )
        class MockLocMgr:
            locations = {"boss": loc}
        
        assert is_destination_dangerous(loc, MockLocMgr()) == True
    
    def test_location_with_encounter_is_dangerous(self):
        """Location with untriggered encounter should be dangerous."""
        loc = Location(
            id="ambush",
            name="Ambush Point",
            description="Danger awaits.",
            encounter=["goblin"],
            encounter_triggered=False,
            visited=True
        )
        class MockLocMgr:
            locations = {"ambush": loc}
        
        assert is_destination_dangerous(loc, MockLocMgr()) == True
    
    def test_location_with_random_encounters_is_dangerous(self):
        """Location with random encounters should be dangerous."""
        loc = Location(
            id="forest",
            name="Forest Path",
            description="A winding path.",
            random_encounters=[RandomEncounter(id="wolf", enemies=["wolf"], chance=20)],
            visited=True
        )
        class MockLocMgr:
            locations = {"forest": loc}
        
        assert is_destination_dangerous(loc, MockLocMgr()) == True
    
    def test_unvisited_location_is_dangerous(self):
        """First visit to any location should be considered dangerous."""
        loc = Location(
            id="new_room",
            name="New Room",
            description="Never been here.",
            visited=False
        )
        class MockLocMgr:
            locations = {"new_room": loc}
        
        assert is_destination_dangerous(loc, MockLocMgr()) == True


# =============================================================================
# APPROACH KEYWORDS COVERAGE TESTS
# =============================================================================

class TestApproachKeywordsCoverage:
    """Ensure all defined keywords work correctly."""
    
    def test_all_stealth_keywords(self):
        """All stealth keywords should trigger stealth."""
        for keyword in APPROACH_KEYWORDS["stealth"]:
            approach_type, skill = parse_approach_intent(keyword)
            assert approach_type == "stealth", f"'{keyword}' should trigger stealth"
            assert skill == "stealth", f"'{keyword}' should check stealth skill"
    
    def test_all_urgent_keywords(self):
        """All urgent keywords should trigger urgent."""
        for keyword in APPROACH_KEYWORDS["urgent"]:
            approach_type, skill = parse_approach_intent(keyword)
            assert approach_type == "urgent", f"'{keyword}' should trigger urgent"
            assert skill is None, f"'{keyword}' should not require skill check"
    
    def test_all_cautious_keywords(self):
        """All cautious keywords should trigger cautious."""
        for keyword in APPROACH_KEYWORDS["cautious"]:
            approach_type, skill = parse_approach_intent(keyword)
            assert approach_type == "cautious", f"'{keyword}' should trigger cautious"
            assert skill == "perception", f"'{keyword}' should check perception skill"


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_stealth_takes_priority_over_urgent(self):
        """If both stealth and urgent keywords present, stealth wins (checked first)."""
        approach_type, skill = parse_approach_intent("sneak and run")
        assert approach_type == "stealth"
    
    def test_stealth_takes_priority_over_cautious(self):
        """Stealth keywords should be checked before cautious."""
        approach_type, skill = parse_approach_intent("sneak carefully")
        assert approach_type == "stealth"
    
    def test_special_characters_handled(self):
        """Input with special characters should not crash."""
        approach_type, skill = parse_approach_intent("sneak! @#$%")
        assert approach_type == "stealth"
    
    def test_very_long_input_handled(self):
        """Very long input should still detect keywords."""
        long_input = "I want to " + "carefully " * 100 + "approach"
        approach_type, skill = parse_approach_intent(long_input)
        assert approach_type == "cautious"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
