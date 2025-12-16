"""
Test Save/Load System - Phase 3.1
Tests the save and load functionality for game persistence.
"""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from character import Character
from scenario import ScenarioManager
from save_system import (
    SaveManager, character_to_dict, dict_to_character,
    item_to_dict, dict_to_item, quick_save, quick_load, format_saves_list,
    scenario_to_dict, restore_scenario
)
from inventory import get_item, add_item_to_inventory


def test_character_serialization():
    """Test converting character to/from dictionary."""
    print("\n" + "=" * 50)
    print("TEST: Character Serialization")
    print("=" * 50)
    
    # Create a character with stats and items
    char = Character(
        name="Test Hero",
        race="Elf",
        char_class="Wizard",
        strength=8,
        dexterity=14,
        constitution=12,
        intelligence=16,
        wisdom=13,
        charisma=10
    )
    char.experience = 150
    char.gold = 50
    char.current_hp = 6
    
    # Add an item
    potion = get_item("healing_potion")
    if potion:
        add_item_to_inventory(char.inventory, potion)
    
    print(f"Original: {char.name}, L{char.level} {char.race} {char.char_class}")
    print(f"  HP: {char.current_hp}/{char.max_hp}, XP: {char.experience}, Gold: {char.gold}")
    print(f"  Items: {len(char.inventory)}")
    
    # Convert to dict
    char_dict = character_to_dict(char)
    print(f"\nSerialized to dict with {len(char_dict)} keys")
    
    # Restore from dict
    restored = dict_to_character(char_dict, Character)
    print(f"\nRestored: {restored.name}, L{restored.level} {restored.race} {restored.char_class}")
    print(f"  HP: {restored.current_hp}/{restored.max_hp}, XP: {restored.experience}, Gold: {restored.gold}")
    print(f"  Items: {len(restored.inventory)}")
    
    # Verify
    assert restored.name == char.name, "Name mismatch"
    assert restored.race == char.race, "Race mismatch"
    assert restored.char_class == char.char_class, "Class mismatch"
    assert restored.current_hp == char.current_hp, "HP mismatch"
    assert restored.experience == char.experience, "XP mismatch"
    assert restored.gold == char.gold, "Gold mismatch"
    assert len(restored.inventory) == len(char.inventory), "Inventory count mismatch"
    
    print("\n✅ Character serialization test PASSED")


def test_save_and_load():
    """Test saving and loading a game."""
    print("\n" + "=" * 50)
    print("TEST: Save and Load Game")
    print("=" * 50)
    
    # Create a character
    char = Character(
        name="Save Test Hero",
        race="Dwarf",
        char_class="Fighter",
        strength=16,
        dexterity=12,
        constitution=14,
        intelligence=10,
        wisdom=12,
        charisma=8
    )
    char.experience = 250
    char.gold = 75
    char.current_hp = 10
    
    # Add items
    sword = get_item("longsword")
    if sword:
        add_item_to_inventory(char.inventory, sword)
    potion = get_item("healing_potion")
    if potion:
        add_item_to_inventory(char.inventory, potion)
    
    print(f"Original character: {char.name}")
    print(f"  Level {char.level}, {char.race} {char.char_class}")
    print(f"  HP: {char.current_hp}/{char.max_hp}")
    print(f"  XP: {char.experience}, Gold: {char.gold}")
    print(f"  Inventory: {len(char.inventory)} items")
    
    # Save game (now returns tuple)
    save_manager = SaveManager()
    filepath, message = save_manager.save_game(
        char,
        scenario_manager=None,
        slot=99,  # Test slot
        description="Unit test save"
    )
    
    print(f"\nSaved to: {filepath}")
    print(f"Message: {message}")
    assert filepath, f"Save failed: {message}"
    assert os.path.exists(filepath), "Save file not created"
    
    # Load game
    result = save_manager.load_game(filepath, Character, ScenarioManager)
    assert result, "Load failed"
    
    loaded_char = result['character']
    print(f"\nLoaded character: {loaded_char.name}")
    print(f"  Level {loaded_char.level}, {loaded_char.race} {loaded_char.char_class}")
    print(f"  HP: {loaded_char.current_hp}/{loaded_char.max_hp}")
    print(f"  XP: {loaded_char.experience}, Gold: {loaded_char.gold}")
    print(f"  Inventory: {len(loaded_char.inventory)} items")
    
    # Verify
    assert loaded_char.name == char.name, "Name mismatch"
    assert loaded_char.race == char.race, "Race mismatch"
    assert loaded_char.char_class == char.char_class, "Class mismatch"
    assert loaded_char.level == char.level, "Level mismatch"
    assert loaded_char.current_hp == char.current_hp, "HP mismatch"
    assert loaded_char.max_hp == char.max_hp, "Max HP mismatch"
    assert loaded_char.experience == char.experience, "XP mismatch"
    assert loaded_char.gold == char.gold, "Gold mismatch"
    assert len(loaded_char.inventory) == len(char.inventory), "Inventory count mismatch"
    
    # Cleanup test file
    try:
        os.remove(filepath)
        print(f"\n🧹 Cleaned up test save file")
    except:
        pass
    
    print("\n✅ Save and Load test PASSED")


def test_list_saves():
    """Test listing saved games."""
    print("\n" + "=" * 50)
    print("TEST: List Saves")
    print("=" * 50)
    
    save_manager = SaveManager()
    saves, errors = save_manager.list_saves()  # Now returns tuple
    
    print(f"Found {len(saves)} save(s)")
    if errors:
        print(f"Warnings: {len(errors)}")
    
    if saves:
        print(format_saves_list(saves, errors))
    
    print("\n✅ List saves test PASSED")


def test_item_serialization():
    """Test converting items to/from dictionary."""
    print("\n" + "=" * 50)
    print("TEST: Item Serialization")
    print("=" * 50)
    
    # Get various item types
    items_to_test = ["healing_potion", "longsword", "leather_armor", "torch"]
    
    for item_id in items_to_test:
        original = get_item(item_id)
        if not original:
            print(f"  ⚠️ Item '{item_id}' not found, skipping")
            continue
        
        # Serialize
        item_dict = item_to_dict(original)
        
        # Deserialize
        restored = dict_to_item(item_dict)
        
        # Verify
        assert restored.name == original.name, f"{item_id}: Name mismatch"
        assert restored.item_type == original.item_type, f"{item_id}: Type mismatch"
        
        print(f"  ✓ {original.name} ({original.item_type.value})")
    
    print("\n✅ Item serialization test PASSED")


def test_scenario_serialization():
    """Test saving and loading scenario state for full game continuity."""
    print("\n" + "=" * 50)
    print("TEST: Scenario Serialization (Continuity)")
    print("=" * 50)
    
    # Create and start a scenario
    sm = ScenarioManager()
    first_scene = sm.start_scenario("goblin_cave")
    
    print(f"Started scenario: {sm.active_scenario.name}")
    print(f"Current scene: {sm.active_scenario.current_scene_id}")
    
    # Simulate some gameplay progress
    sm.active_scenario.record_exchange()
    sm.active_scenario.record_exchange()
    sm.active_scenario.complete_objective("meet_bram")
    
    scene = sm.active_scenario.get_current_scene()
    print(f"After gameplay:")
    print(f"  Exchange count: {scene.exchange_count}")
    print(f"  Objectives complete: {scene.objectives_complete}")
    
    # Serialize the scenario
    scenario_data = scenario_to_dict(sm)
    print(f"\nSerialized scenario data:")
    print(f"  ID: {scenario_data['id']}")
    print(f"  Current scene: {scenario_data['current_scene_id']}")
    print(f"  Scene states: {len(scenario_data['scene_states'])} scenes")
    
    # Create a new ScenarioManager and restore
    sm2 = ScenarioManager()
    success = restore_scenario(sm2, scenario_data)
    
    assert success, "Scenario restore failed"
    assert sm2.active_scenario is not None, "Active scenario not restored"
    
    # Verify restored state
    restored_scene = sm2.active_scenario.get_current_scene()
    print(f"\nRestored scenario:")
    print(f"  Current scene: {sm2.active_scenario.current_scene_id}")
    print(f"  Exchange count: {restored_scene.exchange_count}")
    print(f"  Objectives complete: {restored_scene.objectives_complete}")
    
    # Verify values match
    assert sm2.active_scenario.current_scene_id == sm.active_scenario.current_scene_id, "Scene ID mismatch"
    assert restored_scene.exchange_count == scene.exchange_count, "Exchange count mismatch"
    assert restored_scene.objectives_complete == scene.objectives_complete, "Objectives mismatch"
    
    print("\n✅ Scenario serialization test PASSED")


def test_error_handling():
    """Test comprehensive error handling in save system."""
    from save_system import (
        SaveFileNotFoundError, SaveFileCorruptedError, 
        SaveValidationError, validate_character_data, validate_save_data
    )
    
    print("\n" + "=" * 50)
    print("TEST: Error Handling")
    print("=" * 50)
    
    save_manager = SaveManager()
    
    # Test 1: Load non-existent file
    print("\n1. Testing SaveFileNotFoundError...")
    try:
        save_manager.load_game("nonexistent_file.json", Character, ScenarioManager)
        assert False, "Should have raised SaveFileNotFoundError"
    except SaveFileNotFoundError as e:
        print(f"  ✓ Caught: {e.message}")
        print(f"  ✓ Hint: {e.recovery_hint}")
    
    # Test 2: Validate invalid character data
    print("\n2. Testing character validation...")
    invalid_char_data = {
        'name': '',  # Empty name
        'level': 10,  # Over cap
        'strength': 50,  # Over 30
    }
    is_valid, errors = validate_character_data(invalid_char_data)
    assert not is_valid, "Invalid data should fail validation"
    print(f"  ✓ Validation caught {len(errors)} errors:")
    for e in errors:
        print(f"    - {e}")
    
    # Test 3: Validate save data structure
    print("\n3. Testing save data validation...")
    invalid_save = {
        'version': '9.9',  # Unsupported version
        'timestamp': 'not-a-date',
        # Missing character
    }
    is_valid, errors = validate_save_data(invalid_save)
    assert not is_valid, "Invalid save should fail validation"
    print(f"  ✓ Validation caught {len(errors)} errors:")
    for e in errors:
        print(f"    - {e}")
    
    # Test 4: Save with None character
    print("\n4. Testing save with None character...")
    filepath, message = save_manager.save_game(None)
    assert not filepath, "Should fail to save None character"
    print(f"  ✓ Error message: {message}")
    
    # Test 5: Verify error log tracking
    print("\n5. Testing error log tracking...")
    error_log = save_manager.get_last_errors()
    print(f"  ✓ Error log has {len(error_log)} entries")
    
    print("\n✅ Error handling test PASSED")


def run_all_tests():
    """Run all save system tests."""
    print("\n" + "=" * 60)
    print("       SAVE SYSTEM TESTS - Phase 3.1")
    print("=" * 60)
    
    tests = [
        ("Character Serialization", test_character_serialization),
        ("Item Serialization", test_item_serialization),
        ("Scenario Serialization", test_scenario_serialization),
        ("Error Handling", test_error_handling),
        ("Save and Load", test_save_and_load),
        ("List Saves", test_list_saves),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"❌ {name} FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {name} FAILED with error: {e}")
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
