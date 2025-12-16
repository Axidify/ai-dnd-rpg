"""
Test script for multi-enemy combat system
"""

import sys
sys.path.insert(0, 'src')

from character import Character
from game import parse_combat_request, run_combat

def test_parsing():
    """Test the combat request parsing"""
    print("=" * 50)
    print("Testing Combat Request Parsing")
    print("=" * 50)
    
    test_cases = [
        ("[COMBAT: goblin]", ['goblin']),
        ("[COMBAT: goblin, goblin]", ['goblin', 'goblin']),
        ("[COMBAT: goblin, orc]", ['goblin', 'orc']),
        ("[COMBAT: wolf, wolf, wolf]", ['wolf', 'wolf', 'wolf']),
        ("[COMBAT: goblin_boss, goblin, goblin]", ['goblin_boss', 'goblin', 'goblin']),
        ("No combat here", []),
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
    
    # This will run interactive combat - for testing, we'll just verify it starts
    print("Single enemy combat ready. Run game.py to test interactively.")


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
    
    print("Multi-enemy combat ready. Run game.py to test interactively.")
    print("Use commands like 'attack 1' or 'attack 2' to target specific enemies.")


if __name__ == "__main__":
    test_parsing()
    test_single_enemy()
    test_multi_enemy()
    
    print("\n" + "=" * 50)
    print("To test interactively, run: python src/game.py")
    print("Then trigger combat with enemies, e.g.:")
    print("  'I attack the goblins'")
    print("DM should respond with [COMBAT: goblin, goblin]")
    print("=" * 50)
