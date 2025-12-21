"""
Travel System Automated Playtest Suite

This module performs 25 unique playthroughs specifically targeting the
travel/location/navigation system to find bugs.

Run with: python -m tests.playtest_travel
"""

import sys
import os
import traceback
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from character import Character
from scenario import (
    ScenarioManager, Location, LocationManager, LocationEvent, 
    EventTrigger, ExitCondition, create_goblin_cave_shops,
    normalize_travel_input, fuzzy_location_match
)
from npc import NPCManager, NPC, NPCRole
from quest import QuestManager
from inventory import add_item_to_inventory, get_item, ITEMS
from shop import ShopManager


@dataclass
class TravelTestResult:
    """Result of a single travel test."""
    name: str
    success: bool
    commands_executed: int
    locations_visited: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    final_location: str = ""


@dataclass 
class TravelBug:
    """A discovered travel system bug."""
    id: int
    severity: str
    description: str
    test_name: str
    command: str
    traceback: str = ""


class TravelTestHarness:
    """Test harness specifically for travel system testing."""
    
    def __init__(self):
        self.results: List[TravelTestResult] = []
        self.bugs: List[TravelBug] = []
        self.bug_counter = 0
    
    def setup_game_state(self) -> tuple:
        """Initialize a fresh game state for testing."""
        character = Character(name="Traveler", char_class="Rogue")
        character.gold = 50
        
        # Add starting items
        torch = get_item("torch")
        potion = get_item("healing_potion")
        if torch:
            add_item_to_inventory(character.inventory, torch)
        if potion:
            add_item_to_inventory(character.inventory, potion)
        
        scenario_manager = ScenarioManager()
        scenario_manager.start_scenario("goblin_cave")
        scenario = scenario_manager.active_scenario
        
        if scenario:
            location_manager = scenario.location_manager
            npc_manager = scenario.npc_manager
            quest_manager = QuestManager()
            shop_manager = ShopManager()
            
            # Add shops from scenario
            create_goblin_cave_shops(shop_manager)
            
            return character, location_manager, npc_manager, quest_manager, shop_manager
        
        return None, None, None, None, None
    
    def test_travel_command(self, command: str, location_manager, character) -> Dict[str, Any]:
        """Execute a travel-focused command and return results."""
        result = {
            "success": False,
            "output": "",
            "error": None,
            "new_location": None,
            "locations_visited": []
        }
        
        try:
            cmd_lower = command.lower().strip()
            
            # GO COMMAND - Primary travel mechanism
            if cmd_lower.startswith("go "):
                direction = command[3:].strip()
                if location_manager:
                    success, new_loc, message, events = location_manager.move(direction)
                    if success and new_loc:
                        result["success"] = True
                        result["output"] = f"Moved to {new_loc.name}"
                        result["new_location"] = new_loc.id
                    else:
                        result["output"] = message or f"Can't go '{direction}'"
                else:
                    result["output"] = "No location manager"
            
            # LOOK COMMAND
            elif cmd_lower in ["look", "look around", "l"]:
                if location_manager:
                    loc = location_manager.get_current_location()
                    if loc:
                        result["success"] = True
                        result["output"] = f"Location: {loc.name}"
                else:
                    result["output"] = "No location"
            
            # EXITS COMMAND
            elif cmd_lower in ["exits", "directions", "where"]:
                if location_manager:
                    exits = location_manager.get_exits()
                    result["success"] = True
                    result["output"] = f"Available exits: {list(exits.keys())}"
                else:
                    result["output"] = "No location manager"
            
            # TRAVEL MENU
            elif cmd_lower in ["travel", "destinations"]:
                if location_manager:
                    exits = location_manager.get_exits()
                    result["success"] = True
                    result["output"] = f"Travel options: {list(exits.keys())}"
                else:
                    result["output"] = "No location manager"
            
            # NUMBER SELECTION (for travel menu)
            elif cmd_lower.isdigit():
                if location_manager:
                    num = int(cmd_lower)
                    exits = list(location_manager.get_exits().keys())
                    if 1 <= num <= len(exits):
                        direction = exits[num - 1]
                        success, new_loc, message, events = location_manager.move(direction)
                        if success and new_loc:
                            result["success"] = True
                            result["output"] = f"Moved to {new_loc.name}"
                            result["new_location"] = new_loc.id
                        else:
                            result["output"] = message or f"Failed to move"
                    else:
                        result["output"] = f"Invalid selection: {num}"
                else:
                    result["output"] = "No location manager"
            
            # UNKNOWN COMMAND
            else:
                result["output"] = f"Unknown command: {command}"
                result["success"] = True  # Not a bug, just invalid input
        
        except Exception as e:
            result["error"] = str(e)
            result["output"] = f"Exception: {e}"
            result["traceback"] = traceback.format_exc()
        
        return result
    
    def run_travel_test(self, name: str, commands: List[str]) -> TravelTestResult:
        """Run a single travel-focused playthrough."""
        print(f"\n{'='*60}")
        print(f"  TRAVEL TEST: {name}")
        print("=" * 60)
        
        result = TravelTestResult(
            name=name,
            success=True,
            commands_executed=0,
            locations_visited=[]
        )
        
        # Setup fresh game state
        character, loc_mgr, npc_mgr, quest_mgr, shop_mgr = self.setup_game_state()
        
        if not character or not loc_mgr:
            result.success = False
            result.errors.append("Failed to initialize game state")
            self.results.append(result)
            return result
        
        # Track starting location
        start_loc = loc_mgr.get_current_location()
        if start_loc:
            result.locations_visited.append(start_loc.id)
        
        # Execute commands
        for i, command in enumerate(commands, 1):
            cmd_result = self.test_travel_command(command, loc_mgr, character)
            result.commands_executed += 1
            
            # Track new locations
            if cmd_result.get("new_location"):
                if cmd_result["new_location"] not in result.locations_visited:
                    result.locations_visited.append(cmd_result["new_location"])
            
            # Print progress
            output_preview = cmd_result["output"][:50] + "..." if len(cmd_result["output"]) > 50 else cmd_result["output"]
            status = "✓" if cmd_result["success"] or "Unknown command" in cmd_result["output"] else "✗"
            print(f"  [{i}/{len(commands)}] > {command}")
            print(f"    {status} {output_preview}")
            
            # Check for bugs
            if cmd_result.get("error"):
                self.bug_counter += 1
                bug = TravelBug(
                    id=self.bug_counter,
                    severity="critical",
                    description=f"Exception on '{command}': {cmd_result['error']}",
                    test_name=name,
                    command=command,
                    traceback=cmd_result.get("traceback", "")
                )
                self.bugs.append(bug)
                result.errors.append(cmd_result["error"])
                result.success = False
        
        # Get final location
        final_loc = loc_mgr.get_current_location()
        if final_loc:
            result.final_location = final_loc.id
        
        # Print result
        status = "✅ PASSED" if result.success else "❌ FAILED"
        print(f"\n  Result: {status}")
        print(f"  Locations visited: {len(result.locations_visited)}")
        print(f"  Final location: {result.final_location}")
        
        self.results.append(result)
        return result


# =============================================================================
# TRAVEL TEST SCENARIOS (25 unique tests)
# =============================================================================

def get_test_basic_navigation() -> List[str]:
    """Test #1: Basic navigation commands."""
    return [
        "look",
        "exits",
        "go outside",
        "look",
        "exits",
        "go forge",
        "look",
        "exits",
        "go outside",
        "go tavern",
        "look",
    ]


def get_test_cardinal_directions() -> List[str]:
    """Test #2: Cardinal direction shortcuts (n/s/e/w)."""
    return [
        "exits",
        "go n",
        "go north",
        "go s", 
        "go south",
        "go e",
        "go east",
        "go w",
        "go west",
        "look",
    ]


def get_test_natural_language() -> List[str]:
    """Test #3: Natural language travel input."""
    return [
        "go to the village square",
        "go towards the forge",
        "go outside",
        "go to tavern",
        "look",
        "go into the bar",
        "go back to main room",
        "look",
    ]


def get_test_partial_matching() -> List[str]:
    """Test #4: Partial exit name matching."""
    return [
        "go out",           # Should match "outside"
        "look",
        "go for",           # Should match "forge"
        "look",
        "go out",
        "go tav",           # Should match "tavern"
        "look",
        "go bar",           # Should match "bar"
        "look",
    ]


def get_test_case_insensitivity() -> List[str]:
    """Test #5: Case insensitivity in navigation."""
    return [
        "GO OUTSIDE",
        "look",
        "Go Forge",
        "look",
        "gO oUtSiDe",
        "look",
        "GO TAVERN",
        "look",
    ]


def get_test_whitespace_handling() -> List[str]:
    """Test #6: Whitespace in travel commands."""
    return [
        "  go outside  ",
        "look",
        "go   forge",
        "look",
        "go\toutside",
        "look",
        "go  \t  tavern",
        "look",
    ]


def get_test_invalid_destinations() -> List[str]:
    """Test #7: Invalid destination handling."""
    return [
        "go nowhere",
        "go invalid",
        "go to the moon",
        "go basement",
        "go secret room",
        "go admin_area",
        "go ../../../etc",
        "go '; DROP TABLE;--",
        "look",
        "exits",
    ]


def get_test_rapid_movement() -> List[str]:
    """Test #8: Rapid successive movement."""
    commands = []
    for _ in range(10):
        commands.extend(["go outside", "go tavern"])
    commands.append("look")
    return commands


def get_test_movement_spam() -> List[str]:
    """Test #9: Spamming same destination."""
    return [
        "go outside",
        "go outside",  # Already there
        "go outside",  # Already there
        "go forge",
        "go forge",    # Already there
        "go forge",    # Already there
        "look",
    ]


def get_test_circular_movement() -> List[str]:
    """Test #10: Circular navigation patterns."""
    return [
        "go outside",       # tavern -> square
        "go forge",         # square -> forge
        "go outside",       # forge -> square
        "go tavern",        # square -> tavern
        "go bar",           # tavern -> bar
        "go main room",     # bar -> tavern
        "go outside",       # tavern -> square
        "go east road",     # square -> road
        "go village",       # road -> square
        "look",
    ]


def get_test_deep_navigation() -> List[str]:
    """Test #11: Deep into nested locations."""
    return [
        "look",
        "go bar",           # tavern_main -> tavern_bar
        "look",
        "go main room",     # tavern_bar -> tavern_main
        "go outside",       # tavern_main -> village_square
        "go east road",     # village_square -> east_road
        "look",
        "go village",       # east_road -> village_square
        "go forge",         # village_square -> blacksmith
        "look",
        "exits",
    ]


def get_test_travel_menu() -> List[str]:
    """Test #12: Travel menu commands."""
    return [
        "travel",
        "destinations",
        "where",
        "exits",
        "directions",
        "go outside",
        "travel",
        "look",
    ]


def get_test_number_selection() -> List[str]:
    """Test #13: Numeric exit selection."""
    return [
        "exits",
        "1",            # Select first exit
        "look",
        "exits",
        "2",            # Select second exit
        "look",
        "exits",
        "99",           # Invalid number
        "0",            # Invalid number
        "-1",           # Invalid number
        "look",
    ]


def get_test_empty_input() -> List[str]:
    """Test #14: Empty and whitespace input."""
    return [
        "go",
        "go ",
        "go  ",
        "go\t",
        "",
        "   ",
        "\t",
        "look",
    ]


def get_test_special_characters() -> List[str]:
    """Test #15: Special characters in destinations."""
    return [
        "go outside!",
        "go forge?",
        "go tavern...",
        "go 'outside'",
        'go "forge"',
        "go outside;",
        "go forge|tavern",
        "go outside&forge",
        "look",
    ]


def get_test_unicode_destinations() -> List[str]:
    """Test #16: Unicode in destinations."""
    return [
        "go 酒場",          # Japanese "tavern"
        "go café",
        "go über",
        "go 🏠",
        "go →outside",
        "go ←back",
        "look",
    ]


def get_test_injection_attempts() -> List[str]:
    """Test #17: Injection attacks on travel."""
    return [
        "go '; DROP TABLE locations;--",
        "go ../../../etc/passwd",
        "go <script>alert('xss')</script>",
        "go ${7*7}",
        "go {{config}}",
        "go %s%n%x",
        "go \x00hidden",
        "look",
    ]


def get_test_long_destinations() -> List[str]:
    """Test #18: Very long destination strings."""
    return [
        "go " + "A" * 100,
        "go " + "B" * 500,
        "go " + "C" * 1000,
        "go " + "outside" * 50,
        "look",
    ]


def get_test_command_variations() -> List[str]:
    """Test #19: Various travel command formats."""
    return [
        "go outside",
        "walk outside",     # Not supported but shouldn't crash
        "run to forge",     # Not supported
        "move to tavern",   # Not supported
        "travel to square", # Not supported
        "head outside",     # Not supported
        "proceed to forge", # Not supported
        "look",
    ]


def get_test_destination_aliases() -> List[str]:
    """Test #20: Testing location name aliases."""
    return [
        "go outside",
        "go blacksmith",    # Alias for forge
        "look",
        "go square",        # Alias for village_square
        "look",
        "go inn",           # Alias for tavern
        "look",
    ]


def get_test_filler_word_stripping() -> List[str]:
    """Test #21: Filler words in travel commands."""
    return [
        "go to the outside",
        "go towards the forge",
        "go into the tavern",
        "go through the door",
        "go up to the bar",
        "go down the road",
        "look",
    ]


def get_test_mixed_valid_invalid() -> List[str]:
    """Test #22: Mix of valid and invalid commands."""
    return [
        "go outside",       # Valid
        "go nowhere",       # Invalid
        "go forge",         # Valid
        "go xyz",           # Invalid
        "go outside",       # Valid
        "go !!!",           # Invalid
        "go tavern",        # Valid
        "look",
    ]


def get_test_location_state() -> List[str]:
    """Test #23: Location state persistence."""
    return [
        "look",
        "go outside",
        "look",
        "go forge",
        "look",
        # Go back and check state preserved
        "go outside",
        "look",
        "go tavern",
        "look",
        "go bar",
        "look",
        "go main room",
        "look",
    ]


def get_test_exit_list_accuracy() -> List[str]:
    """Test #24: Exit list accuracy."""
    return [
        "exits",            # Check tavern exits
        "go outside",
        "exits",            # Check square exits
        "go forge",
        "exits",            # Check forge exits
        "go outside",
        "exits",
        "go east road",
        "exits",            # Check road exits
        "look",
    ]


def get_test_stress_navigation() -> List[str]:
    """Test #25: Stress test navigation system."""
    commands = []
    # 100 navigation commands
    destinations = ["outside", "tavern", "forge", "east road", "village", "bar", "main room"]
    for i in range(50):
        commands.append(f"go {destinations[i % len(destinations)]}")
    commands.extend(["look", "exits"])
    return commands


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def main():
    """Run all 25 travel system tests."""
    print("\n" + "=" * 60)
    print("  AI RPG V2 - TRAVEL SYSTEM TEST SUITE")
    print("=" * 60)
    print("  Running 25 travel-focused tests...")
    
    harness = TravelTestHarness()
    
    # All 25 tests
    tests = [
        ("Basic Navigation", get_test_basic_navigation()),
        ("Cardinal Directions", get_test_cardinal_directions()),
        ("Natural Language", get_test_natural_language()),
        ("Partial Matching", get_test_partial_matching()),
        ("Case Insensitivity", get_test_case_insensitivity()),
        ("Whitespace Handling", get_test_whitespace_handling()),
        ("Invalid Destinations", get_test_invalid_destinations()),
        ("Rapid Movement", get_test_rapid_movement()),
        ("Movement Spam", get_test_movement_spam()),
        ("Circular Movement", get_test_circular_movement()),
        ("Deep Navigation", get_test_deep_navigation()),
        ("Travel Menu", get_test_travel_menu()),
        ("Number Selection", get_test_number_selection()),
        ("Empty Input", get_test_empty_input()),
        ("Special Characters", get_test_special_characters()),
        ("Unicode Destinations", get_test_unicode_destinations()),
        ("Injection Attempts", get_test_injection_attempts()),
        ("Long Destinations", get_test_long_destinations()),
        ("Command Variations", get_test_command_variations()),
        ("Destination Aliases", get_test_destination_aliases()),
        ("Filler Word Stripping", get_test_filler_word_stripping()),
        ("Mixed Valid/Invalid", get_test_mixed_valid_invalid()),
        ("Location State", get_test_location_state()),
        ("Exit List Accuracy", get_test_exit_list_accuracy()),
        ("Stress Navigation", get_test_stress_navigation()),
    ]
    
    for name, commands in tests:
        harness.run_travel_test(name, commands)
    
    # Summary
    print("\n" + "=" * 60)
    print("  TRAVEL TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in harness.results if r.success)
    failed = len(harness.results) - passed
    total_commands = sum(r.commands_executed for r in harness.results)
    total_locations = sum(len(r.locations_visited) for r in harness.results)
    
    print(f"  Tests: {passed} passed, {failed} failed")
    print(f"  Total commands: {total_commands}")
    print(f"  Total unique locations visited: {total_locations}")
    print(f"  Bugs found: {len(harness.bugs)}")
    
    if harness.bugs:
        print("\n" + "-" * 60)
        print("  BUGS DISCOVERED:")
        print("-" * 60)
        for bug in harness.bugs:
            print(f"\n  [{bug.severity.upper()}] Bug #{bug.id}")
            print(f"    Test: {bug.test_name}")
            print(f"    Command: {bug.command}")
            print(f"    Description: {bug.description}")
            if bug.traceback:
                tb_lines = bug.traceback.strip().split("\n")[-3:]
                for line in tb_lines:
                    print(f"    {line}")
    
    # Write report
    with open("Travel_Test.log", "w", encoding="utf-8") as f:
        f.write("AI RPG V2 - Travel System Test Results\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Tests: {passed}/{len(harness.results)} passed\n")
        f.write(f"Total commands: {total_commands}\n")
        f.write(f"Bugs found: {len(harness.bugs)}\n\n")
        
        for result in harness.results:
            f.write(f"\n{'='*40}\n")
            f.write(f"Test: {result.name}\n")
            f.write(f"Status: {'PASSED' if result.success else 'FAILED'}\n")
            f.write(f"Commands: {result.commands_executed}\n")
            f.write(f"Locations visited: {result.locations_visited}\n")
            f.write(f"Final location: {result.final_location}\n")
            if result.errors:
                f.write(f"Errors:\n")
                for err in result.errors:
                    f.write(f"  - {err}\n")
        
        if harness.bugs:
            f.write(f"\n\n{'='*60}\n")
            f.write("BUGS FOUND:\n")
            f.write("=" * 60 + "\n")
            for bug in harness.bugs:
                f.write(f"\n[{bug.severity.upper()}] Bug #{bug.id}\n")
                f.write(f"  Test: {bug.test_name}\n")
                f.write(f"  Command: {bug.command}\n")
                f.write(f"  Description: {bug.description}\n")
                if bug.traceback:
                    f.write(f"  Traceback:\n{bug.traceback}\n")
    
    print(f"\n  Results written to Travel_Test.log")
    print("=" * 60)
    
    return harness.bugs


if __name__ == "__main__":
    bugs = main()
    sys.exit(0 if not bugs else 1)
