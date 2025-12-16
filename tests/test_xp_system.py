"""
Unit tests for the XP/Leveling System.
Run with: python tests/test_xp_system.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from character import Character, XP_THRESHOLDS, MILESTONE_XP


def test_initial_state():
    """Test 1: Character starts at level 1 with 0 XP."""
    c = Character('TestHero', 'warrior')
    assert c.level == 1, f"Expected level 1, got {c.level}"
    assert c.experience == 0, f"Expected 0 XP, got {c.experience}"
    print("1. Initial state: PASS")


def test_xp_gain():
    """Test 2: XP gain works correctly."""
    c = Character('TestHero', 'warrior')
    result = c.gain_xp(50, 'Defeated goblin')
    assert c.experience == 50, f"Expected 50 XP, got {c.experience}"
    assert result['xp_gained'] == 50, f"Expected xp_gained=50, got {result['xp_gained']}"
    assert not c.can_level_up(), "Should not be able to level up yet"
    print("2. XP gain (below threshold): PASS")


def test_level_threshold():
    """Test 3: Level up becomes available at threshold."""
    c = Character('TestHero', 'warrior')
    c.gain_xp(50)
    c.gain_xp(60)  # Total: 110 XP, threshold for L2 is 100
    assert c.experience == 110, f"Expected 110 XP, got {c.experience}"
    assert c.can_level_up(), "Should be able to level up"
    print("3. Level threshold detection: PASS")


def test_level_up():
    """Test 4: Level up increases level and HP."""
    c = Character('TestHero', 'warrior')
    c.gain_xp(110)
    old_hp = c.max_hp
    result = c.level_up()
    
    assert result is not None, "Level up should return result"
    assert result['old_level'] == 1, f"Expected old_level=1, got {result['old_level']}"
    assert result['new_level'] == 2, f"Expected new_level=2, got {result['new_level']}"
    assert c.level == 2, f"Expected level 2, got {c.level}"
    assert c.max_hp > old_hp, "HP should increase on level up"
    print(f"4. Level up (L1→L2, +{result['hp_gain']} HP): PASS")


def test_xp_to_next_level():
    """Test 5: XP needed calculation is correct."""
    c = Character('TestHero', 'warrior')
    c.level = 2
    c.experience = 110
    needed = c.xp_to_next_level()
    expected = XP_THRESHOLDS[3] - c.experience  # 300 - 110 = 190
    assert needed == expected, f"Expected {expected} XP needed, got {needed}"
    print(f"5. XP to next level ({needed} needed): PASS")


def test_max_level_cap():
    """Test 6: Cannot level up past max level."""
    c = Character('TestHero', 'warrior')
    c.level = 5
    c.experience = 2000
    assert not c.can_level_up(), "Should not level up at max level"
    result = c.level_up()
    assert result['success'] == False, "Level up should fail at max level"
    print("6. Max level cap (L5): PASS")


def test_xp_progress():
    """Test 7: XP progress calculation is correct."""
    c = Character('TestHero', 'warrior')
    c.level = 2
    c.experience = 200  # Threshold for L2=100, L3=300
    progress, total = c.xp_progress()
    # Progress since L2: 200 - 100 = 100
    # Total needed for L3: 300 - 100 = 200
    assert progress == 100, f"Expected progress=100, got {progress}"
    assert total == 200, f"Expected total=200, got {total}"
    print(f"7. XP progress ({progress}/{total}): PASS")


def test_milestone_xp_values():
    """Test 8: Milestone XP values are defined correctly."""
    assert MILESTONE_XP['minor'] == 25
    assert MILESTONE_XP['major'] == 50
    assert MILESTONE_XP['boss'] == 100
    assert MILESTONE_XP['adventure'] == 150
    print("8. Milestone XP values: PASS")


def test_proficiency_bonus():
    """Test 9: Proficiency bonus scales with level."""
    c = Character('TestHero', 'warrior')
    
    # Level 1-4 should have +2
    c.level = 1
    assert c.get_proficiency_bonus() == 2
    c.level = 4
    assert c.get_proficiency_bonus() == 2
    
    # Level 5 should have +3
    c.level = 5
    assert c.get_proficiency_bonus() == 3
    
    print("9. Proficiency bonus: PASS")


def test_cannot_level_without_xp():
    """Test 10: Cannot level up without enough XP."""
    c = Character('TestHero', 'warrior')
    c.gain_xp(50)  # Not enough for level 2
    assert not c.can_level_up()
    result = c.level_up()
    assert result['success'] == False
    assert c.level == 1
    print("10. Cannot level without XP: PASS")


if __name__ == "__main__":
    print("=" * 50)
    print("       XP SYSTEM UNIT TESTS")
    print("=" * 50)
    print()
    
    test_initial_state()
    test_xp_gain()
    test_level_threshold()
    test_level_up()
    test_xp_to_next_level()
    test_max_level_cap()
    test_xp_progress()
    test_milestone_xp_values()
    test_proficiency_bonus()
    test_cannot_level_without_xp()
    
    print()
    print("=" * 50)
    print("       ALL 10 TESTS PASSED ✓")
    print("=" * 50)
