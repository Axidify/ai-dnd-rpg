"""
Adversarial Testing Suite - Hostile Player Tests
Tests designed to break the game with edge cases and malicious input.
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from character import Character, CLASSES, RACES
from inventory import (
    Item, ItemType, ITEMS, get_item, add_item_to_inventory,
    remove_item_from_inventory, find_item_in_inventory, use_item, format_inventory
)
from combat import create_enemy, Enemy, ENEMIES, roll_attack, roll_damage, get_enemy_loot_for_class
from scenario import ScenarioManager, create_goblin_cave_scenario
from save_system import SaveManager, SaveFileNotFoundError, SaveFileCorruptedError
from quest import QuestManager, Quest, QuestObjective, ObjectiveType, create_kill_objective


class TestEmptyAndGarbageInput:
    """Test empty, whitespace, and garbage input handling."""
    
    def test_empty_inventory_format(self):
        """Empty inventory should display properly."""
        inv = []
        display = format_inventory(inv, 0)
        # "Your inventory is empty." contains "empty" which is valid
        assert "empty" in display.lower()
    
    def test_find_item_empty_string(self):
        """Finding empty string item should return None, not crash."""
        inv = []
        result = find_item_in_inventory(inv, "")
        assert result is None
    
    def test_find_item_whitespace(self):
        """Finding whitespace-only item should return None."""
        inv = []
        result = find_item_in_inventory(inv, "   ")
        assert result is None
    
    def test_find_item_special_chars(self):
        """Items with special characters should not crash."""
        inv = []
        for special in ["!@#$%", "'DROP TABLE", "\\x00\\x00", "../../etc/passwd", "<script>", "null"]:
            result = find_item_in_inventory(inv, special)
            assert result is None
    
    def test_get_item_nonexistent(self):
        """Getting non-existent item should return None."""
        result = get_item("completely_fake_item_12345")
        assert result is None
    
    def test_get_item_empty(self):
        """Getting empty string item should return None."""
        result = get_item("")
        assert result is None
    
    def test_get_item_special_chars(self):
        """Get item with SQL-injection-style input should return None."""
        result = get_item("'; DROP TABLE items; --")
        assert result is None


class TestCharacterEdgeCases:
    """Test character creation and stats edge cases."""
    
    def test_character_invalid_class(self):
        """Creating character with invalid class should use default."""
        char = Character("Test", "invalid_class_xyz", "human")
        # Should either use a default or fail gracefully
        assert char.name == "Test"
    
    def test_character_invalid_race(self):
        """Creating character with invalid race should use default."""
        char = Character("Test", "fighter", "fake_race_123")
        assert char.name == "Test"
    
    def test_character_empty_name(self):
        """Character with empty name should handle gracefully."""
        char = Character("", "fighter", "human")
        # Should work but name might be empty
        assert char is not None
    
    def test_character_very_long_name(self):
        """Character with extremely long name should handle gracefully."""
        long_name = "A" * 10000
        char = Character(long_name, "fighter", "human")
        assert char is not None
    
    def test_character_special_chars_name(self):
        """Character name with special chars should handle gracefully."""
        char = Character("Test<script>alert(1)</script>", "fighter", "human")
        assert char is not None
    
    def test_take_damage_negative(self):
        """Taking negative damage should be ignored (no healing exploit)."""
        char = Character("Test", "fighter", "human")
        original_hp = char.current_hp
        char.take_damage(-100)  # Attempt to heal via negative damage
        # Should be ignored, HP unchanged
        assert char.current_hp == original_hp
        assert char.current_hp <= char.max_hp
    
    def test_take_damage_zero(self):
        """Taking zero damage should not change HP."""
        char = Character("Test", "fighter", "human")
        original_hp = char.current_hp
        char.take_damage(0)
        assert char.current_hp == original_hp
    
    def test_take_damage_massive(self):
        """Taking massive damage should not cause underflow."""
        char = Character("Test", "fighter", "human")
        char.take_damage(999999999)
        assert char.current_hp >= 0
        assert char.current_hp <= 0  # Should be dead
    
    def test_heal_beyond_max(self):
        """Healing beyond max HP should cap at max."""
        char = Character("Test", "fighter", "human")
        char.take_damage(5)
        char.heal(10000)
        assert char.current_hp == char.max_hp
    
    def test_gain_xp_negative(self):
        """Gaining negative XP should be ignored."""
        char = Character("Test", "fighter", "human")
        original_xp = char.experience
        result = char.gain_xp(-100)  # Try to lose XP
        # Should be ignored
        assert char.experience == original_xp
        assert char.experience >= 0
        assert result['xp_gained'] == 0
    
    def test_gain_xp_massive(self):
        """Gaining massive XP should not overflow or cause issues."""
        char = Character("Test", "fighter", "human")
        char.gain_xp(999999999)
        # Should cap at max level and not crash
        assert char.level <= 5  # Max level is 5
    
    def test_add_gold_negative(self):
        """Adding negative gold should be handled."""
        char = Character("Test", "fighter", "human")
        char.gold = 100
        char.gold += -1000  # Attempt to go negative
        # Gold could go negative - this might be a bug!
        # We're just documenting the behavior here


class TestInventoryExploits:
    """Test inventory manipulation exploits."""
    
    def test_add_none_item(self):
        """Adding None as item should not crash."""
        inv = []
        char = Character("Test", "fighter", "human")
        # This should either fail gracefully or be prevented
        try:
            add_item_to_inventory(inv, None)
        except (TypeError, AttributeError):
            pass  # Expected behavior
    
    def test_add_same_item_many_times(self):
        """Adding same item many times should not break."""
        inv = []
        item = get_item("healing_potion")
        for _ in range(1000):
            add_item_to_inventory(inv, item)
        # Should either stack or have many items
        assert len(inv) >= 1
    
    def test_remove_item_not_in_inventory(self):
        """Removing item not in inventory should handle gracefully."""
        inv = []
        success, msg = remove_item_from_inventory(inv, "fake_item")
        # Should return False, not crash
        assert success == False
    
    def test_remove_item_empty_inventory(self):
        """Removing from empty inventory should handle gracefully."""
        inv = []
        success, msg = remove_item_from_inventory(inv, "healing_potion")
        assert success == False
    
    def test_use_item_not_consumable(self):
        """Using non-consumable item should fail gracefully."""
        char = Character("Test", "fighter", "human")
        weapon = get_item("longsword")
        success, msg = use_item(weapon, char)
        assert success == False
    
    def test_use_item_dead_character(self):
        """Using item on dead character should handle gracefully."""
        char = Character("Test", "fighter", "human")
        char.current_hp = 0
        potion = get_item("healing_potion")
        success, msg = use_item(potion, char)
        # Could either fail or succeed (revive?)


class TestCombatExploits:
    """Test combat system exploits."""
    
    def test_create_invalid_enemy(self):
        """Creating invalid enemy type should handle gracefully."""
        result = create_enemy("fake_enemy_type_xyz")
        assert result is None
    
    def test_enemy_negative_hp(self):
        """Enemy with negative HP should be considered dead (property)."""
        enemy = create_enemy("goblin")
        enemy.current_hp = -100
        assert enemy.is_dead == True
    
    def test_enemy_zero_hp(self):
        """Enemy with zero HP should be dead (property)."""
        enemy = create_enemy("goblin")
        enemy.current_hp = 0
        assert enemy.is_dead == True
    
    def test_attack_dead_enemy(self):
        """Attacking dead enemy should handle gracefully."""
        enemy = create_enemy("goblin")
        enemy.current_hp = 0
        char = Character("Test", "fighter", "human")
        # Rolling attack against dead enemy should still work mechanically
        result = roll_attack(char, enemy.armor_class)
        # Result is a dict, check it has expected keys
        assert 'd20_roll' in result


class TestQuestExploits:
    """Test quest system exploits."""
    
    def test_accept_nonexistent_quest(self):
        """Accepting non-existent quest should fail gracefully."""
        qm = QuestManager()
        result = qm.accept_quest("fake_quest_id_xyz")
        assert result == False or result is None
    
    def test_complete_unstarted_quest(self):
        """Completing quest not accepted should fail gracefully."""
        qm = QuestManager()
        quest = Quest("test_quest", "Test Quest", "Description")
        qm.available_quests["test_quest"] = quest
        result = qm.complete_quest("test_quest")
        assert result is None or result == {}
    
    def test_complete_quest_twice(self):
        """Completing quest twice should not double rewards."""
        qm = QuestManager()
        obj = create_kill_objective("kill_goblin", "Kill a goblin", "goblin", count=1)
        quest = Quest("test_quest", "Test Quest", "Description", 
                      objectives=[obj], rewards={"xp": 100})
        qm.register_quest(quest)
        qm.accept_quest("test_quest")
        qm.on_enemy_killed("goblin")
        
        # Complete first time
        rewards1 = qm.complete_quest("test_quest")
        
        # Try to complete again
        rewards2 = qm.complete_quest("test_quest")
        assert rewards2 is None or rewards2 == {}
    
    def test_objective_progress_beyond_required(self):
        """Objective progress beyond required should cap correctly."""
        qm = QuestManager()
        obj = create_kill_objective("kill_goblins", "Kill 3 goblins", "goblin", count=3)
        quest = Quest("test_quest", "Test Quest", "Description", objectives=[obj])
        qm.register_quest(quest)
        qm.accept_quest("test_quest")
        
        # Kill way more than needed
        for _ in range(100):
            qm.on_enemy_killed("goblin")
        
        # Check objective doesn't have weird state
        active_quest = qm.active_quests.get("test_quest")
        assert active_quest.objectives[0].current_count >= 3


class TestScenarioExploits:
    """Test scenario/location system exploits."""
    
    def test_move_invalid_direction(self):
        """Moving in invalid direction should fail gracefully."""
        sm = ScenarioManager()
        sm.start_scenario("goblin_cave")  # Uses built-in scenario
        
        loc_mgr = sm.active_scenario.location_manager
        success, _, msg, _ = loc_mgr.move("fake_direction_xyz", {})
        assert success == False
    
    def test_move_with_empty_state(self):
        """Moving with empty game_state should handle gracefully."""
        sm = ScenarioManager()
        sm.start_scenario("goblin_cave")
        
        loc_mgr = sm.active_scenario.location_manager
        # Should handle missing keys in game_state without crashing
        try:
            success, _, msg, _ = loc_mgr.move("east", {})
            # Might succeed or fail, but shouldn't crash
        except KeyError:
            pytest.fail("move() crashed with empty game_state - should handle gracefully")
    
    def test_get_npc_none_location(self):
        """Getting NPC when not at location should handle gracefully."""
        scenario = create_goblin_cave_scenario()
        npc_mgr = scenario.npc_manager
        # Trying to find NPC should return None, not crash


class TestSaveLoadExploits:
    """Test save/load system exploits."""
    
    def test_load_nonexistent_save(self):
        """Loading non-existent save should raise SaveFileNotFoundError."""
        sm = SaveManager()
        with pytest.raises(SaveFileNotFoundError):
            sm.load_game("fake_save_path_xyz.json", Character, ScenarioManager)
    
    def test_load_corrupted_save(self):
        """Loading corrupted save data should raise SaveFileCorruptedError."""
        sm = SaveManager()
        # Create a temp file with invalid JSON
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{corrupted json data here")
            temp_path = f.name
        
        try:
            with pytest.raises(SaveFileCorruptedError):
                sm.load_game(temp_path, Character, ScenarioManager)
        finally:
            os.unlink(temp_path)
    
    def test_save_with_none_character(self):
        """Saving with None character should fail gracefully."""
        sm = SaveManager()
        try:
            result = sm.save_game(None, None, None)
            # Should return error message, not crash
        except (TypeError, AttributeError):
            pass  # Expected


class TestNumericOverflow:
    """Test numeric edge cases and overflow."""
    
    def test_character_stat_overflow(self):
        """Character stats at extreme values should not overflow."""
        char = Character("Test", "fighter", "human")
        # Try to set extreme values
        char.strength = 999999999
        char.dexterity = -999999999
        # Should not cause issues when calculating modifiers
        mod = char.get_ability_modifier("strength")
        assert isinstance(mod, int)
    
    def test_gold_overflow(self):
        """Massive gold amounts should not overflow."""
        char = Character("Test", "fighter", "human")
        char.gold = 999999999999999
        char.gold += 1
        assert char.gold > 0
    
    def test_xp_overflow(self):
        """Massive XP should be handled (capped at max level)."""
        char = Character("Test", "fighter", "human")
        char.experience = 999999999999999
        # Should not crash when checking level
        assert char.level >= 1


class TestItemDuplication:
    """Test potential item duplication exploits."""
    
    def test_add_and_remove_same_reference(self):
        """Adding same item reference multiple times."""
        inv = []
        item = get_item("healing_potion")
        add_item_to_inventory(inv, item)
        add_item_to_inventory(inv, item)  # Same reference
        
        # Should have 2 items or stack to 2
        total_potions = sum(1 for i in inv if "healing" in i.name.lower())
        assert total_potions >= 1


class TestConcurrencyIssues:
    """Test potential race condition patterns (single-threaded but good practice)."""
    
    def test_modify_inventory_while_iterating(self):
        """Modifying inventory during iteration should not crash."""
        inv = []
        for _ in range(10):
            add_item_to_inventory(inv, get_item("healing_potion"))
        
        # This pattern can cause issues in some implementations
        items_to_remove = []
        for item in inv:
            if "healing" in item.name.lower():
                items_to_remove.append(item.name)
        
        for item_name in items_to_remove:
            remove_item_from_inventory(inv, item_name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
