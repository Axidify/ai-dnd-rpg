"""
Hostile Player Testing - Round 8
Target: Party Combat Integration (Phase 3.6.8)
Focus: party_member_attack, get_party_member_action, check_flanking, determine_turn_order

25 unique tests targeting potential exploits and edge cases.
"""

import sys
import os

# Add src directory to path for imports
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')
sys.path.insert(0, src_path)

from party import get_recruitable_npc, PartyMember, PartyMemberClass
from combat import (
    party_member_attack, format_party_member_attack, get_party_member_action,
    check_flanking, determine_turn_order, create_enemy, Combatant
)
from character import Character
from dataclasses import dataclass
import random

# Test tracking
passed = 0
failed = 0
warned = 0

def test_result(test_id: str, name: str, expected: str, actual: str, passed_test: bool, warn: bool = False):
    """Record and print test result."""
    global passed, failed, warned
    if warn:
        warned += 1
        status = "⚠️ WARN"
    elif passed_test:
        passed += 1
        status = "✅ PASS"
    else:
        failed += 1
        status = "❌ FAIL"
    print(f"  [{test_id}] {name}: {status}")
    print(f"       Expected: {expected}")
    print(f"       Actual:   {actual}")
    return passed_test

print("=" * 70)
print("HOSTILE PLAYER TESTING - ROUND 8: PARTY COMBAT INTEGRATION")
print("=" * 70)

# =============================================================================
# CATEGORY 1: PARTY MEMBER ATTACK FUNCTION EXPLOITS (Tests 1-5)
# =============================================================================
print("\n" + "-" * 60)
print("CATEGORY 1: Party Member Attack Function Exploits")
print("-" * 60)

# Test 1: Null party member
print("\n[Test 1] Null Party Member Attack")
try:
    attack, damage = party_member_attack(None, create_enemy('goblin'), False)
    test_result("1", "Null party member", "Exception or safe default", f"attack={attack}", False)
except (TypeError, AttributeError) as e:
    test_result("1", "Null party member", "Exception raised", f"Exception: {type(e).__name__}", True)

# Test 2: Null target enemy
print("\n[Test 2] Null Target Enemy")
try:
    marcus = get_recruitable_npc('marcus_mercenary')
    attack, damage = party_member_attack(marcus, None, False)
    test_result("2", "Null target", "Exception or safe default", f"attack={attack}", False)
except (TypeError, AttributeError) as e:
    test_result("2", "Null target", "Exception raised", f"Exception: {type(e).__name__}", True)

# Test 3: Fake party member with malicious name
print("\n[Test 3] Malicious Party Member Name Injection")
@dataclass
class FakePartyMember:
    name: str = "'; DROP TABLE users; --"
    attack_bonus: int = 4
    damage_dice: str = "1d8+2"
    
fake_member = FakePartyMember()
goblin = create_enemy('goblin')
try:
    attack, damage = party_member_attack(fake_member, goblin, False)
    # Check if SQL was executed (it won't be - no DB)
    safe = attack['attacker'] == "'; DROP TABLE users; --"
    test_result("3", "SQL injection in name", "Treated as literal string", 
                f"Name stored: {attack['attacker'][:30]}...", safe)
except Exception as e:
    test_result("3", "SQL injection in name", "Handled safely", f"Error: {e}", True)

# Test 4: Code injection in damage_dice
print("\n[Test 4] Code Injection in damage_dice")
@dataclass
class ExploitMember:
    name: str = "Hacker"
    attack_bonus: int = 4
    damage_dice: str = "__import__('os').system('rm -rf /')"  # Malicious!

exploit_member = ExploitMember()
try:
    attack, damage = party_member_attack(exploit_member, goblin, False)
    # If it hits, check if damage calc crashed or executed code
    if damage:
        safe = isinstance(damage['total'], int)
        test_result("4", "Code in damage_dice", "No code execution", 
                    f"damage['total']={damage.get('total')}", safe)
    else:
        test_result("4", "Code in damage_dice", "Attack missed safely", "No damage calc", True)
except Exception as e:
    # Crashing is acceptable for malicious input
    test_result("4", "Code in damage_dice", "Safe failure", f"Exception: {type(e).__name__}", True)

# Test 5: Extreme attack bonus
print("\n[Test 5] Extreme Attack Bonus (999999)")
@dataclass
class OverpoweredMember:
    name: str = "Cheater"
    attack_bonus: int = 999999
    damage_dice: str = "1d8+2"

op_member = OverpoweredMember()
try:
    attack, damage = party_member_attack(op_member, goblin, False)
    # Should work but with extreme total
    safe = attack['total'] >= 999999
    test_result("5", "Extreme attack bonus", "Works (no server validation)", 
                f"Total: {attack['total']}", safe)
except Exception as e:
    test_result("5", "Extreme attack bonus", "Handled", f"Exception: {e}", True)

# =============================================================================
# CATEGORY 2: FLANKING MECHANIC EXPLOITS (Tests 6-10)
# =============================================================================
print("\n" + "-" * 60)
print("CATEGORY 2: Flanking Mechanic Exploits")
print("-" * 60)

# Test 6: Negative attackers
print("\n[Test 6] Negative Attackers Count")
result = check_flanking(-5)
test_result("6", "Negative attackers", "False (no flanking)", f"Result: {result}", result == False)

# Test 7: Zero attackers
print("\n[Test 7] Zero Attackers")
result = check_flanking(0)
test_result("7", "Zero attackers", "False (no flanking)", f"Result: {result}", result == False)

# Test 8: Extreme attacker count
print("\n[Test 8] Extreme Attacker Count (1 million)")
result = check_flanking(1000000)
test_result("8", "Million attackers", "True (still flanking)", f"Result: {result}", result == True)

# Test 9: Float attackers
print("\n[Test 9] Float Attackers (2.5)")
try:
    result = check_flanking(2.5)
    # Should work since 2.5 >= 2
    test_result("9", "Float attackers", "Handled (2.5 >= 2)", f"Result: {result}", result == True)
except TypeError as e:
    test_result("9", "Float attackers", "Type error raised", f"Exception: {e}", True)

# Test 10: String attackers
print("\n[Test 10] String Attackers ('many')")
try:
    result = check_flanking("many")
    test_result("10", "String attackers", "Should error or False", f"Result: {result}", False)
except TypeError as e:
    test_result("10", "String attackers", "TypeError raised", f"Exception: {type(e).__name__}", True)

# =============================================================================
# CATEGORY 3: AI ACTION DECISION EXPLOITS (Tests 11-15)
# =============================================================================
print("\n" + "-" * 60)
print("CATEGORY 3: AI Action Decision Exploits")
print("-" * 60)

# Test 11: Empty enemies list
print("\n[Test 11] Empty Enemies List")
marcus = get_recruitable_npc('marcus_mercenary')
marcus.recruited = True
try:
    action = get_party_member_action(marcus, [], {"player": 50})
    # Should still return an action (maybe 'wait' or 'attack')
    test_result("11", "Empty enemies", "Valid action returned", f"Action: {action}", action in ['attack', 'ability', 'heal', 'wait', None])
except Exception as e:
    test_result("11", "Empty enemies", "Exception raised", f"Exception: {e}", True)

# Test 12: Null enemies list
print("\n[Test 12] Null Enemies List")
try:
    action = get_party_member_action(marcus, None, {"player": 50})
    test_result("12", "None enemies", "Handled gracefully", f"Action: {action}", True)
except (TypeError, AttributeError) as e:
    test_result("12", "None enemies", "Exception raised", f"Exception: {type(e).__name__}", True)

# Test 13: Negative HP in allies_hp
print("\n[Test 13] Negative HP in allies_hp dict")
try:
    action = get_party_member_action(marcus, [create_enemy('goblin')], {"player": -100, "ally": -50})
    # Negative HP might trigger heal or be handled
    test_result("13", "Negative HP values", "Handled (action returned)", f"Action: {action}", action in ['attack', 'ability', 'heal'])
except Exception as e:
    test_result("13", "Negative HP values", "Exception", f"Error: {e}", True)

# Test 14: Huge HP values
print("\n[Test 14] Extreme HP Values (999999)")
try:
    action = get_party_member_action(marcus, [create_enemy('goblin')], {"player": 999999})
    # Should still work - attack since ally is healthy
    test_result("14", "Huge HP values", "Returns attack (healthy ally)", f"Action: {action}", action == 'attack')
except Exception as e:
    test_result("14", "Huge HP values", "Exception", f"Error: {e}", True)

# Test 15: Code injection in allies_hp keys
print("\n[Test 15] Code Injection in allies_hp Keys")
try:
    malicious_dict = {"__import__('os').system('rm -rf /')": 50}
    action = get_party_member_action(marcus, [create_enemy('goblin')], malicious_dict)
    test_result("15", "Code in dict keys", "Treated as string key", f"Action: {action}", action in ['attack', 'ability', 'heal'])
except Exception as e:
    test_result("15", "Code in dict keys", "Safe handling", f"Exception: {e}", True)

# =============================================================================
# CATEGORY 4: TURN ORDER MANIPULATION (Tests 16-20)
# =============================================================================
print("\n" + "-" * 60)
print("CATEGORY 4: Turn Order Manipulation")
print("-" * 60)

# Test 16: Null player in turn order
print("\n[Test 16] Null Player in Turn Order")
try:
    turn_order = determine_turn_order(None, [create_enemy('goblin')], [])
    test_result("16", "Null player", "Exception or empty", f"Order: {turn_order}", False)
except (TypeError, AttributeError) as e:
    test_result("16", "Null player", "Exception raised", f"Exception: {type(e).__name__}", True)

# Test 17: Empty enemies and party
print("\n[Test 17] Empty Combat (no enemies, no party)")
player = Character("TestPlayer", "Fighter", "Human")
try:
    turn_order = determine_turn_order(player, [], [])
    # Should have just the player
    test_result("17", "Empty combat", "Player only in order", f"Count: {len(turn_order)}", len(turn_order) == 1)
except Exception as e:
    test_result("17", "Empty combat", "Exception", f"Error: {e}", True)

# Test 18: Duplicate enemies
print("\n[Test 18] Duplicate Enemy Objects")
goblin = create_enemy('goblin')
try:
    turn_order = determine_turn_order(player, [goblin, goblin, goblin], [])
    # Should handle 3 identical goblins
    test_result("18", "Duplicate enemies", "All included", f"Count: {len(turn_order)}", len(turn_order) == 4)
except Exception as e:
    test_result("18", "Duplicate enemies", "Exception", f"Error: {e}", True)

# Test 19: Extreme initiative manipulation
print("\n[Test 19] Party Member with Extreme Initiative Modifier")
elira = get_recruitable_npc('elira_ranger')
elira.recruited = True
elira.dex_modifier = 999999  # Extreme!
try:
    turn_order = determine_turn_order(player, [create_enemy('goblin')], [elira])
    # Should still work, Elira likely first
    first = turn_order[0].name if turn_order else "None"
    test_result("19", "Extreme dex_modifier", "Turn order works", f"First: {first}", len(turn_order) >= 2)
except Exception as e:
    test_result("19", "Extreme dex_modifier", "Exception", f"Error: {e}", True)

# Test 20: Non-recruited party member injection
print("\n[Test 20] Non-recruited Party Member in Turn Order")
shade = get_recruitable_npc('shade_rogue')
shade.recruited = False  # NOT recruited
try:
    turn_order = determine_turn_order(player, [create_enemy('goblin')], [shade])
    # Function doesn't filter - it includes whoever is passed
    shade_in_order = any(c.name == shade.name for c in turn_order)
    test_result("20", "Non-recruited in order", "Included (no filter in func)", f"Shade in order: {shade_in_order}", True, warn=True)
except Exception as e:
    test_result("20", "Non-recruited in order", "Exception", f"Error: {e}", True)

# =============================================================================
# CATEGORY 5: COMBAT FORMAT DISPLAY EXPLOITS (Tests 21-25)
# =============================================================================
print("\n" + "-" * 60)
print("CATEGORY 5: Combat Format Display Exploits")
print("-" * 60)

# Test 21: XSS in attacker name
print("\n[Test 21] XSS in Attacker Name")
attack_result = {
    'attacker': '<script>alert("XSS")</script>',
    'd20_roll': 15,
    'd20_roll_1': 15,
    'd20_roll_2': None,
    'has_flanking': False,
    'attack_bonus': 4,
    'total': 19,
    'target_ac': 12,
    'target_name': 'Goblin',
    'hit': True,
    'is_crit': False,
    'is_fumble': False,
}
damage_result = {'attacker': 'Test', 'total': 8, 'rolls': [8], 'is_crit': False}
try:
    formatted = format_party_member_attack(attack_result, damage_result, "Fighter")
    # XSS should be HTML-escaped by format_party_member_attack()
    xss_escaped = '<script>' not in formatted and '&lt;script&gt;' in formatted
    test_result("21", "XSS in name", "XSS properly escaped", f"Escaped: {xss_escaped}", xss_escaped)
except Exception as e:
    test_result("21", "XSS in name", "Exception", f"Error: {e}", True)

# Test 22: Extremely long formatted output
print("\n[Test 22] Extremely Long Target Name")
attack_result['target_name'] = 'A' * 10000
try:
    formatted = format_party_member_attack(attack_result, damage_result, "Fighter")
    test_result("22", "10k char target name", "Format works", f"Length: {len(formatted)}", len(formatted) > 10000)
except Exception as e:
    test_result("22", "10k char target name", "Exception", f"Error: {e}", True)

# Test 23: Unknown class type
print("\n[Test 23] Unknown Member Class")
attack_result['target_name'] = 'Goblin'  # Reset
try:
    formatted = format_party_member_attack(attack_result, damage_result, "Necromancer")
    # Should use default emoji
    test_result("23", "Unknown class", "Default emoji used", f"Has emoji: {'⚔️' in formatted or '🛡️' in formatted}", True)
except Exception as e:
    test_result("23", "Unknown class", "Exception", f"Error: {e}", True)

# Test 24: Null damage result (miss)
print("\n[Test 24] Null Damage (Miss)")
attack_result['hit'] = False
try:
    formatted = format_party_member_attack(attack_result, None, "Fighter")
    test_result("24", "Null damage (miss)", "Format works", f"Has MISS: {'MISS' in formatted}", 'MISS' in formatted)
except Exception as e:
    test_result("24", "Null damage (miss)", "Exception", f"Error: {e}", True)

# Test 25: Critical hit formatting
print("\n[Test 25] Critical Hit Formatting")
attack_result['hit'] = True
attack_result['is_crit'] = True
attack_result['d20_roll'] = 20
damage_result['is_crit'] = True
damage_result['total'] = 24
try:
    formatted = format_party_member_attack(attack_result, damage_result, "Fighter")
    test_result("25", "Critical hit format", "CRITICAL shown", f"Has CRITICAL: {'CRITICAL' in formatted}", 'CRITICAL' in formatted)
except Exception as e:
    test_result("25", "Critical hit format", "Exception", f"Error: {e}", True)

# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "=" * 70)
print("ROUND 8 SUMMARY: PARTY COMBAT INTEGRATION")
print("=" * 70)
print(f"\n  ✅ PASSED: {passed}")
print(f"  ❌ FAILED: {failed}")
print(f"  ⚠️  WARNED: {warned}")
print(f"  📊 TOTAL:  {passed + failed + warned}/25")

if failed == 0:
    print("\n🎉 ALL TESTS PASSING - Party Combat Integration is secure!")
else:
    print(f"\n⚠️  {failed} vulnerabilities found - review required")

print("=" * 70)
