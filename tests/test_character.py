"""
Comprehensive tests for the Character system.
Covers: stats, modifiers, XP/leveling, damage, healing, creation.
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from character import (
    Character, CLASSES, RACES, XP_THRESHOLDS, MILESTONE_XP,
    quick_create_character
)


class TestCharacterCreation:
    """Tests for character creation and initialization."""
    
    def test_default_character(self):
        """Test default character has expected values."""
        char = Character()
        assert char.name == "Unnamed Hero"
        assert char.race == "Human"
        assert char.char_class == "Fighter"
        assert char.level == 1
        assert char.experience == 0
        assert char.strength == 10
        assert char.current_hp == char.max_hp
    
    def test_custom_character(self):
        """Test character with custom values."""
        char = Character(
            name="Gandalf",
            race="Elf",
            char_class="Wizard",
            strength=8,
            intelligence=18,
            wisdom=16
        )
        assert char.name == "Gandalf"
        assert char.race == "Elf"
        assert char.char_class == "Wizard"
        assert char.intelligence == 18
        assert char.weapon == "quarterstaff"  # Wizard default
    
    def test_quick_create(self):
        """Test quick character creation."""
        char = quick_create_character("TestHero")
        assert char.name == "TestHero"
        assert char.race in RACES
        assert char.char_class in CLASSES
        assert len(char.inventory) > 0  # Has starting equipment
    
    def test_random_create(self):
        """Test random character creation."""
        char = Character.create_random("RandomHero")
        assert char.name == "RandomHero"
        assert char.race in RACES
        assert char.char_class in CLASSES
        # Stats should be between 3-18 (4d6 drop lowest)
        assert 3 <= char.strength <= 18
        assert 3 <= char.dexterity <= 18


class TestAbilityModifiers:
    """Tests for ability score modifiers."""
    
    def test_modifier_calculation(self):
        """Test standard modifier calculation."""
        assert Character.get_modifier(10) == 0
        assert Character.get_modifier(11) == 0
        assert Character.get_modifier(12) == 1
        assert Character.get_modifier(8) == -1
        assert Character.get_modifier(18) == 4
        assert Character.get_modifier(1) == -5
        assert Character.get_modifier(20) == 5
    
    def test_get_ability_modifier_by_name(self):
        """Test getting modifiers by ability name."""
        char = Character(strength=16, dexterity=14, constitution=12)
        assert char.get_ability_modifier('strength') == 3
        assert char.get_ability_modifier('str') == 3
        assert char.get_ability_modifier('dexterity') == 2
        assert char.get_ability_modifier('dex') == 2
        assert char.get_ability_modifier('constitution') == 1
    
    def test_format_modifier(self):
        """Test modifier formatting as +/- string."""
        char = Character(strength=16, dexterity=8)
        assert char.format_modifier(16) == "+3"
        assert char.format_modifier(10) == "+0"
        assert char.format_modifier(8) == "-1"


class TestDerivedStats:
    """Tests for derived stats (HP, AC)."""
    
    def test_fighter_hp(self):
        """Fighter should have d10 hit die."""
        char = Character(char_class="Fighter", constitution=14)  # +2 CON
        assert char.max_hp == 12  # 10 + 2
    
    def test_wizard_hp(self):
        """Wizard should have d6 hit die."""
        char = Character(char_class="Wizard", constitution=14)  # +2 CON
        assert char.max_hp == 8  # 6 + 2
    
    def test_barbarian_hp(self):
        """Barbarian should have d12 hit die."""
        char = Character(char_class="Barbarian", constitution=14)  # +2 CON
        assert char.max_hp == 14  # 12 + 2
    
    def test_armor_class(self):
        """AC should be 10 + DEX modifier."""
        char = Character(dexterity=16)  # +3 DEX
        assert char.armor_class == 13


class TestDamageAndHealing:
    """Tests for damage and healing mechanics."""
    
    def test_take_damage(self):
        """Test damage reduces HP correctly."""
        char = Character()
        char.current_hp = 10
        char.max_hp = 10
        result = char.take_damage(3)
        assert char.current_hp == 7
        assert "takes 3 damage" in result
    
    def test_damage_cannot_go_negative(self):
        """HP should not go below 0."""
        char = Character()
        char.current_hp = 5
        char.max_hp = 10
        char.take_damage(100)
        assert char.current_hp == 0
    
    def test_unconscious_message(self):
        """Dropping to 0 HP should show unconscious message."""
        char = Character(name="TestHero")
        char.current_hp = 5
        char.max_hp = 10
        result = char.take_damage(5)
        assert "fallen unconscious" in result
    
    def test_heal(self):
        """Test healing increases HP."""
        char = Character()
        char.current_hp = 5
        char.max_hp = 10
        result = char.heal(3)
        assert char.current_hp == 8
        assert "heals 3 HP" in result
    
    def test_heal_cannot_exceed_max(self):
        """Healing should not exceed max HP."""
        char = Character()
        char.current_hp = 9
        char.max_hp = 10
        char.heal(100)
        assert char.current_hp == 10


class TestXPSystem:
    """Tests for XP and leveling (supplement to test_xp_system.py)."""
    
    def test_gain_xp_returns_info(self):
        """gain_xp should return detailed info dict."""
        char = Character()
        result = char.gain_xp(50, "test kill")
        assert result['xp_gained'] == 50
        assert result['source'] == "test kill"
        assert result['old_xp'] == 0
        assert result['new_xp'] == 50
        assert 'level_up' in result
    
    def test_level_up_increases_stats(self):
        """Level up should increase HP and return details."""
        char = Character(char_class="Fighter")
        char.experience = 100  # Enough for level 2
        initial_hp = char.max_hp
        result = char.level_up()
        assert result['success'] == True
        assert result['new_level'] == 2
        assert char.max_hp > initial_hp
    
    def test_level_up_full_heal(self):
        """Level up should restore HP to max."""
        char = Character()
        char.experience = 100
        char.current_hp = 1
        char.level_up()
        assert char.current_hp == char.max_hp
    
    def test_cannot_level_without_xp(self):
        """Cannot level up without enough XP."""
        char = Character()
        char.experience = 50  # Not enough for level 2
        result = char.level_up()
        assert result['success'] == False


class TestStatBlock:
    """Tests for character display formatting."""
    
    def test_stat_block_format(self):
        """Stat block should contain key info."""
        char = Character(name="DisplayTest", race="Elf", char_class="Wizard")
        block = char.get_stat_block()
        assert "DisplayTest" in block
        assert "Elf" in block
        assert "Wizard" in block
        assert "STR" in block
        assert "HP" in block
    
    def test_hp_bar_generation(self):
        """HP bar should show visual representation."""
        char = Character()
        char.current_hp = 5
        char.max_hp = 10
        bar = char._get_hp_bar()
        assert "█" in bar
        assert "░" in bar
    
    def test_context_for_dm(self):
        """DM context should include relevant character info."""
        char = Character(name="AITest", race="Dwarf", char_class="Cleric")
        context = char.get_context_for_dm()
        assert "AITest" in context
        assert "Dwarf" in context
        assert "Cleric" in context
        assert "HP:" in context


class TestProficiencyBonus:
    """Tests for proficiency bonus by level."""
    
    def test_level_1_proficiency(self):
        """Level 1-4 should have +2 proficiency."""
        char = Character(level=1)
        assert char.get_proficiency_bonus() == 2
    
    def test_level_5_proficiency(self):
        """Level 5 should have +3 proficiency."""
        char = Character(level=5)
        assert char.get_proficiency_bonus() == 3


class TestRollStat:
    """Tests for stat rolling."""
    
    def test_roll_stat_range(self):
        """Rolled stats should be in valid range (3-18)."""
        for _ in range(100):
            stat = Character.roll_stat()
            assert 3 <= stat <= 18


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
