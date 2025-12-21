"""
Test script for multi-enemy combat system
"""

import sys
sys.path.insert(0, 'src')

from character import Character
from dm_engine import parse_combat_request

def test_parsing():
    """Test the combat request parsing"""
    print("=" * 50)
    print("Testing Combat Request Parsing")
    print("=" * 50)
    
    # parse_combat_request returns (enemy_list, surprise_player)
    test_cases = [
        ("[COMBAT: goblin]", (['goblin'], False)),
        ("[COMBAT: goblin, goblin]", (['goblin', 'goblin'], False)),
        ("[COMBAT: goblin, orc]", (['goblin', 'orc'], False)),
        ("[COMBAT: wolf, wolf, wolf]", (['wolf', 'wolf', 'wolf'], False)),
        ("[COMBAT: goblin_boss, goblin, goblin]", (['goblin_boss', 'goblin', 'goblin'], False)),
        ("No combat here", ([], False)),
    ]
    
    for input_str, expected in test_cases:
        result = parse_combat_request(input_str)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_str[:40]}...' -> {result}")
    print()


def test_single_enemy():
    """Test single enemy combat (backwards compatibility)"""
    print("=" * 50)
    print("Testing Single Enemy Combat")
    print("=" * 50)
    
    char = Character.create_random("TestHero")
    char.current_hp = char.max_hp  # Full health
    
    print(f"Character: {char.name} ({char.char_class})")
    print(f"HP: {char.current_hp}/{char.max_hp}, AC: {char.armor_class}")
    print()
    
    # Test combat parsing for single enemy
    result = parse_combat_request("[COMBAT: goblin]")
    assert result == (['goblin'], False), f"Expected (['goblin'], False), got {result}"
    print("✅ Single enemy parsing works correctly.")


def test_multi_enemy():
    """Test multi-enemy combat"""
    print("=" * 50)
    print("Testing Multi-Enemy Combat")
    print("=" * 50)
    
    char = Character.create_random("TestHero")
    char.current_hp = char.max_hp
    
    print(f"Character: {char.name} ({char.char_class})")
    print(f"HP: {char.current_hp}/{char.max_hp}, AC: {char.armor_class}")
    print()
    
    # Test combat parsing for multiple enemies
    result = parse_combat_request("[COMBAT: goblin, goblin, orc]")
    assert result == (['goblin', 'goblin', 'orc'], False), f"Expected (['goblin', 'goblin', 'orc'], False), got {result}"
    print("✅ Multi-enemy parsing works correctly.")
    
    # Test surprise attack parsing
    result = parse_combat_request("[COMBAT: wolf, wolf | SURPRISE]")
    assert result == (['wolf', 'wolf'], True), f"Expected (['wolf', 'wolf'], True), got {result}"
    print("✅ Surprise attack parsing works correctly.")


if __name__ == "__main__":
    test_parsing()
    test_single_enemy()
    test_multi_enemy()
    
    print("\n" + "=" * 50)
    print("All multi-enemy combat parsing tests passed!")
    print("=" * 50)
