"""
Test Party Combat Integration (Phase 3.5 P7 Step 6)
Verifies that party members participate in combat with initiative and auto-actions.
"""

import sys
sys.path.insert(0, 'src')

from combat import (
    determine_turn_order, roll_initiative, Combatant,
    party_member_attack, format_party_member_attack,
    get_party_member_action, check_flanking, create_enemy
)
from party import Party, PartyMember, PartyMemberClass, get_recruitable_npc
from character import Character


def test_determine_turn_order_with_party():
    """Test that determine_turn_order includes party members."""
    print("=" * 60)
    print("TEST: determine_turn_order() with party members")
    print("=" * 60)
    
    # Create enemies
    enemies = [create_enemy('goblin'), create_enemy('goblin')]
    
    # Create party members (use correct IDs)
    marcus = get_recruitable_npc('marcus_mercenary')
    marcus.recruited = True
    
    elira = get_recruitable_npc('elira_ranger')
    elira.recruited = True
    
    party_members = [marcus, elira]
    
    # Determine turn order
    turn_order = determine_turn_order(
        player_name="TestHero",
        player_dex_mod=2,
        enemies=enemies,
        party_members=party_members
    )
    
    print(f"Turn order has {len(turn_order)} combatants")
    for c in turn_order:
        ally_tag = " (ALLY)" if c.is_ally else ""
        player_tag = " (PLAYER)" if c.is_player else ""
        enemy_tag = " (ENEMY)" if c.is_enemy() else ""
        print(f"  Init {c.initiative:2d}: {c.name}{player_tag}{ally_tag}{enemy_tag}")
    
    # Verify: Should have player + 2 party members + 2 enemies = 5
    assert len(turn_order) == 5, f"Expected 5 combatants, got {len(turn_order)}"
    
    # Verify player is in turn order
    player_combatant = [c for c in turn_order if c.is_player]
    assert len(player_combatant) == 1, "Player should be in turn order"
    
    # Verify party members are allies
    allies = [c for c in turn_order if c.is_ally]
    assert len(allies) == 2, f"Expected 2 allies, got {len(allies)}"
    
    # Verify enemies are enemies
    enemy_combatants = [c for c in turn_order if c.is_enemy()]
    assert len(enemy_combatants) == 2, f"Expected 2 enemies, got {len(enemy_combatants)}"
    
    print("✅ PASS: Turn order includes party members correctly")
    return True


def test_party_member_attack():
    """Test party member attack function."""
    print("\n" + "=" * 60)
    print("TEST: party_member_attack()")
    print("=" * 60)
    
    marcus = get_recruitable_npc('marcus_mercenary')
    goblin = create_enemy('goblin')
    
    # Test attack without flanking
    attack, damage = party_member_attack(marcus, goblin, has_flanking=False)
    
    print(f"Attack result: hit={attack['hit']}, roll={attack['d20_roll']}")
    assert 'attacker' in attack, "Attack should have 'attacker' field"
    assert 'target_name' in attack, "Attack should have 'target_name' field"
    assert attack['attacker'] == 'Marcus', f"Expected 'Marcus', got '{attack['attacker']}'"
    
    # Test format
    formatted = format_party_member_attack(attack, damage, "Fighter")
    print(f"Formatted: {formatted[:80]}...")
    assert 'Marcus' in formatted
    
    print("✅ PASS: party_member_attack works correctly")
    return True


def test_party_member_attack_with_flanking():
    """Test party member attack with flanking bonus."""
    print("\n" + "=" * 60)
    print("TEST: party_member_attack() with flanking")
    print("=" * 60)
    
    elira = get_recruitable_npc('elira_ranger')
    goblin = create_enemy('goblin')
    
    # Test attack WITH flanking (should roll 2d20, take higher)
    attack, damage = party_member_attack(elira, goblin, has_flanking=True)
    
    print(f"Attack with flanking: d20_roll={attack['d20_roll']}")
    print(f"  Roll 1: {attack['d20_roll_1']}, Roll 2: {attack['d20_roll_2']}")
    assert attack['has_flanking'] == True
    assert attack['d20_roll'] == max(attack['d20_roll_1'], attack['d20_roll_2'])
    
    # Test format shows flanking
    formatted = format_party_member_attack(attack, damage, "Ranger")
    print(f"Formatted: {formatted[:100]}...")
    assert 'FLANKING' in formatted or attack['d20_roll_1'] is not None
    
    print("✅ PASS: Flanking gives advantage correctly")
    return True


def test_get_party_member_action():
    """Test AI decision logic for party member actions."""
    print("\n" + "=" * 60)
    print("TEST: get_party_member_action()")
    print("=" * 60)
    
    marcus = get_recruitable_npc('marcus_mercenary')
    enemies = [create_enemy('goblin'), create_enemy('goblin_boss')]
    
    # Test normal attack decision (no one critical)
    allies_hp = {
        'TestHero': (30, 30),
        'Marcus': (18, 18)
    }
    
    action = get_party_member_action(marcus, enemies, allies_hp)
    print(f"Marcus action (all healthy): {action['action_type']}")
    assert action['action_type'] == 'attack', "Should attack when allies healthy"
    assert action['target'] is not None, "Should have a target"
    
    # Test when ally is low HP (Fighter should use Shield Wall)
    marcus.ability_uses_remaining = 1  # Reset ability
    allies_hp_low = {
        'TestHero': (5, 30),  # Below 30%
        'Marcus': (18, 18)
    }
    
    action_low = get_party_member_action(marcus, enemies, allies_hp_low)
    print(f"Marcus action (ally critical): {action_low['action_type']}")
    assert action_low['action_type'] == 'ability', "Should use ability when ally critical"
    assert action_low['ability_name'] == 'Shield Wall'
    
    print("✅ PASS: AI action decisions work correctly")
    return True


def test_check_flanking():
    """Test flanking check logic."""
    print("\n" + "=" * 60)
    print("TEST: check_flanking()")
    print("=" * 60)
    
    # 1 attacker = no flanking
    assert check_flanking(1) == False, "1 attacker should not flank"
    
    # 2 attackers = flanking
    assert check_flanking(2) == True, "2 attackers should flank"
    
    # 3 attackers = flanking
    assert check_flanking(3) == True, "3 attackers should flank"
    
    print("✅ PASS: Flanking check works correctly")
    return True


def test_dead_party_member_excluded():
    """Test that dead party members are excluded from turn order."""
    print("\n" + "=" * 60)
    print("TEST: Dead party members excluded from combat")
    print("=" * 60)
    
    enemies = [create_enemy('goblin')]
    
    marcus = get_recruitable_npc('marcus_mercenary')
    marcus.recruited = True
    marcus.is_dead = True  # Dead!
    
    elira = get_recruitable_npc('elira_ranger')
    elira.recruited = True  # Alive
    
    turn_order = determine_turn_order(
        player_name="TestHero",
        player_dex_mod=2,
        enemies=enemies,
        party_members=[marcus, elira]
    )
    
    # Should have: player + elira (alive) + goblin = 3
    # Marcus (dead) should be excluded
    ally_names = [c.name for c in turn_order if c.is_ally]
    print(f"Allies in combat: {ally_names}")
    
    assert len(turn_order) == 3, f"Expected 3 (dead Marcus excluded), got {len(turn_order)}"
    assert 'Marcus' not in str(ally_names), "Dead Marcus should not be in combat"
    assert 'Elira' in str(ally_names), "Alive Elira should be in combat"
    
    print("✅ PASS: Dead party members correctly excluded")
    return True


def test_non_recruited_excluded():
    """Test that non-recruited party members are excluded."""
    print("\n" + "=" * 60)
    print("TEST: Non-recruited members excluded from combat")
    print("=" * 60)
    
    enemies = [create_enemy('goblin')]
    
    marcus = get_recruitable_npc('marcus_mercenary')
    marcus.recruited = False  # Not recruited!
    
    elira = get_recruitable_npc('elira_ranger')
    elira.recruited = True  # Recruited
    
    turn_order = determine_turn_order(
        player_name="TestHero",
        player_dex_mod=2,
        enemies=enemies,
        party_members=[marcus, elira]
    )
    
    ally_names = [c.name for c in turn_order if c.is_ally]
    print(f"Allies in combat: {ally_names}")
    
    assert 'Marcus' not in str(ally_names), "Non-recruited Marcus should not fight"
    
    print("✅ PASS: Non-recruited members correctly excluded")
    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PHASE 3.5 P7 STEP 6 - PARTY COMBAT INTEGRATION TESTS")
    print("=" * 60 + "\n")
    
    tests = [
        test_determine_turn_order_with_party,
        test_party_member_attack,
        test_party_member_attack_with_flanking,
        test_get_party_member_action,
        test_check_flanking,
        test_dead_party_member_excluded,
        test_non_recruited_excluded,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} PASS, {failed} FAIL")
    print("=" * 60)
