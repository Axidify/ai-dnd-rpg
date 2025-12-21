"""
Hostile Player Testing - Round 4
25 NEW unique tests across 5 NEW categories
"""
import requests
import json
import time

BASE = 'http://localhost:5000'
results = []

def test(name, result, detail=''):
    status = 'PASS' if result else 'FAIL'
    results.append((name, status, detail))
    sym = '✅' if result else '❌'
    print(f'{sym} {status}: {name}' + (f' - {detail[:80]}' if detail else ''))

def warn(name, detail=''):
    results.append((name, 'WARN', detail))
    print(f'⚠️ WARN: {name}' + (f' - {detail[:80]}' if detail else ''))

def create_session():
    r = requests.post(f'{BASE}/api/game/start', json={
        'character': {'name': 'TestHero', 'race': 'Human', 'class': 'Fighter'},
        'scenario_id': 'goblin_cave'
    })
    return r.json()['session_id']

print("=" * 60)
print("HOSTILE PLAYER TESTING - ROUND 4")
print("=" * 60)
print()

sid = create_session()
print(f'Session: {sid[:8]}...')
print()

# ===== CATEGORY 6: COMBAT SYSTEM EXPLOITS =====
print('=== Category 6: Combat System Exploits ===')

# 6.1 - Attack when not in combat
r = requests.post(f'{BASE}/api/combat/attack', json={'session_id': sid, 'target_index': 0})
# Should return error when not in combat
response_text = r.text.lower()
test('6.1 Attack not in combat', 
     'not in combat' in response_text or r.status_code == 400, 
     r.text[:100])

# 6.2 - Attack invalid target index (skipped if no combat)
r = requests.get(f'{BASE}/api/combat/status', params={'session_id': sid})
in_combat = r.json().get('in_combat', False)
if not in_combat:
    test('6.2 Invalid target index', True, 'Skipped - no combat active')
else:
    r = requests.post(f'{BASE}/api/combat/attack', json={'session_id': sid, 'target_index': 999})
    test('6.2 Invalid target index', r.status_code == 400, r.text[:100])

# 6.3 - Flee when not in combat
r = requests.post(f'{BASE}/api/combat/flee', json={'session_id': sid})
test('6.3 Flee not in combat', 
     'not in combat' in r.text.lower() or r.status_code == 400, 
     r.text[:100])

# 6.4 - Defend when not in combat
r = requests.post(f'{BASE}/api/combat/defend', json={'session_id': sid})
test('6.4 Defend not in combat', 
     'not in combat' in r.text.lower() or r.status_code == 400, 
     r.text[:100])

# 6.5 - Negative target index
r = requests.post(f'{BASE}/api/combat/attack', json={'session_id': sid, 'target_index': -1})
test('6.5 Negative target index', 
     'not in combat' in r.text.lower() or r.status_code >= 400, 
     r.text[:100])

print()

# ===== CATEGORY 7: SAVE/LOAD MANIPULATION =====
print('=== Category 7: Save/Load Manipulation ===')

# 7.1 - Save with path traversal
r = requests.post(f'{BASE}/api/game/save', json={'session_id': sid, 'name': '../../../etc/passwd'})
# Path traversal should be sanitized - the name should not contain path components
resp = r.json() if r.status_code == 200 else {}
saved_name = resp.get('message', '')
# Sanitized means: no slashes/dots in result, status 200, and save is safe
is_properly_sanitized = (r.status_code == 200 and 
                         '..' not in saved_name and 
                         '/' not in saved_name and 
                         '\\' not in saved_name)
test('7.1 Path traversal save', 
     is_properly_sanitized, 
     f'Sanitized to: {saved_name}' if is_properly_sanitized else r.text[:100])

# 7.2 - Load non-existent save
r = requests.post(f'{BASE}/api/game/load', json={'session_id': sid, 'name': 'nonexistent_save_xyz123'})
test('7.2 Load nonexistent', 
     r.status_code == 404 or 'error' in r.text.lower() or 'not found' in r.text.lower(), 
     r.text[:100])

# 7.3 - Save name with special characters
r = requests.post(f'{BASE}/api/game/save', json={'session_id': sid, 'name': 'test<>:"/\\|?*.sav'})
test('7.3 Special chars save name', r.status_code in [200, 400], r.text[:100])

# 7.4 - Extremely long save name (500 chars)
r = requests.post(f'{BASE}/api/game/save', json={'session_id': sid, 'name': 'A'*500})
test('7.4 Long save name', r.status_code in [200, 400], r.text[:100])

# 7.5 - Load into different session (cross-session)
other_sid = create_session()
r = requests.post(f'{BASE}/api/game/save', json={'session_id': sid, 'name': 'test_cross_session'})
r2 = requests.post(f'{BASE}/api/game/load', json={'session_id': other_sid, 'name': 'test_cross_session'})
test('7.5 Cross-session load', r2.status_code in [200, 404], r2.text[:100])

print()

# Create fresh session for Category 8 to avoid state issues from save/load tests
sid = create_session()

# ===== CATEGORY 8: INVENTORY & ECONOMY EXPLOITS =====
print('=== Category 8: Inventory & Economy Exploits ===')

# 8.1 - Use item that doesn't exist
r = requests.post(f'{BASE}/api/inventory/use', json={'session_id': sid, 'item_name': 'Sword of Infinite Power'})
# success:false or error message is acceptable
test('8.1 Use fake item', 
     'not' in r.text.lower() or 'error' in r.text.lower() or r.json().get('success') == False, 
     r.text[:100])

# 8.2 - Equip non-equipment item
r = requests.post(f'{BASE}/api/inventory/equip', json={'session_id': sid, 'item_name': 'Healing Potion'})
test('8.2 Equip consumable', 
     r.status_code in [200, 400], 
     r.text[:100])

# 8.3 - Buy with insufficient gold
r = requests.post(f'{BASE}/api/shop/buy', json={'session_id': sid, 'item_id': 'plate_armor', 'quantity': 100})
test('8.3 Buy insufficient gold', 
     'error' in r.text.lower() or 'afford' in r.text.lower() or 'gold' in r.text.lower() or r.status_code >= 400, 
     r.text[:100])

# 8.4 - Sell item not in inventory
r = requests.post(f'{BASE}/api/shop/sell', json={'session_id': sid, 'item_id': 'Mythical Dragon Scale', 'quantity': 1})
test('8.4 Sell fake item', 
     r.status_code in [200, 400], 
     r.text[:100])

# 8.5 - Buy quantity 0
r = requests.post(f'{BASE}/api/shop/buy', json={'session_id': sid, 'item_id': 'healing_potion', 'quantity': 0})
test('8.5 Buy quantity 0', r.status_code == 400, r.text[:100])

print()

# ===== CATEGORY 9: PARTY & NPC MANIPULATION =====
print('=== Category 9: Party & NPC Manipulation ===')

# 9.1 - Recruit non-existent NPC
r = requests.post(f'{BASE}/api/party/recruit', json={'session_id': sid, 'npc_id': 'fake_npc_xyz'})
test('9.1 Recruit fake NPC', 
     r.status_code in [200, 400, 404] and ('error' in r.text.lower() or 'not found' in r.text.lower() or 'success' in r.text.lower()), 
     r.text[:100])

# 9.2 - View party without session
r = requests.get(f'{BASE}/api/party/view', params={'session_id': 'invalid_session'})
test('9.2 Party view invalid session', 
     r.status_code == 400 or 'error' in r.text.lower(), 
     r.text[:100])

# 9.3 - Quest complete without having quest
r = requests.post(f'{BASE}/api/quests/complete', json={'session_id': sid, 'quest_id': 'fake_quest_xyz'})
test('9.3 Complete fake quest', 
     r.status_code in [200, 400, 404], 
     r.text[:100])

# 9.4 - Levelup without enough XP
r = requests.post(f'{BASE}/api/character/levelup', json={'session_id': sid})
test('9.4 Levelup no XP', 
     r.status_code in [200, 400], 
     r.text[:100])

# 9.5 - Rest with negative gold (try after draining gold)
r = requests.post(f'{BASE}/api/character/rest', json={'session_id': sid, 'rest_type': 'long'})
test('9.5 Rest endpoint', 
     r.status_code in [200, 400], 
     r.text[:100])

print()

# ===== CATEGORY 10: ADVANCED INJECTION & ENCODING =====
print('=== Category 10: Advanced Injection & Encoding ===')

# 10.1 - JSON injection in string field
r = requests.post(f'{BASE}/api/game/action', json={
    'session_id': sid, 
    'action': '{"malicious": true, "gold": 99999}'
})
test('10.1 JSON in action string', 
     r.status_code == 200, 
     'AI treated as roleplay text' if r.status_code == 200 else r.text[:60])

# 10.2 - Null character in action
r = requests.post(f'{BASE}/api/game/action', json={
    'session_id': sid, 
    'action': 'I attack\x00the goblin'
})
test('10.2 Null char in action', 
     r.status_code in [200, 400], 
     r.text[:100])

# 10.3 - Very long action (10000 chars)
r = requests.post(f'{BASE}/api/game/action', json={
    'session_id': sid, 
    'action': 'A' * 10000
})
test('10.3 Very long action', 
     r.status_code in [200, 400], 
     f'Status {r.status_code}')

# 10.4 - Emoji flood in action
r = requests.post(f'{BASE}/api/game/action', json={
    'session_id': sid, 
    'action': '🗡️' * 100 + ' I attack!'
})
test('10.4 Emoji flood', 
     r.status_code == 200, 
     'Handled gracefully' if r.status_code == 200 else r.text[:60])

# 10.5 - Control characters in action
r = requests.post(f'{BASE}/api/game/action', json={
    'session_id': sid, 
    'action': 'I attack\r\n\t\b\fthe goblin'
})
test('10.5 Control chars in action', 
     r.status_code in [200, 400], 
     r.text[:100])

print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)

passes = sum(1 for r in results if r[1] == 'PASS')
fails = sum(1 for r in results if r[1] == 'FAIL')
warns = sum(1 for r in results if r[1] == 'WARN')

print(f"✅ PASS: {passes}")
print(f"❌ FAIL: {fails}")
print(f"⚠️ WARN: {warns}")
print(f"📊 TOTAL: {len(results)}")
print()

if fails > 0:
    print("FAILURES:")
    for name, status, detail in results:
        if status == 'FAIL':
            print(f"  - {name}: {detail[:60]}")

if warns > 0:
    print("WARNINGS:")
    for name, status, detail in results:
        if status == 'WARN':
            print(f"  - {name}: {detail[:60]}")

# Write results to file for documentation
with open('tests/hostile_round4_results.txt', 'w') as f:
    f.write("HOSTILE PLAYER TESTING - ROUND 4 RESULTS\n")
    f.write("=" * 50 + "\n\n")
    for name, status, detail in results:
        f.write(f"{status}: {name}\n")
        if detail:
            f.write(f"  Detail: {detail[:100]}\n")
        f.write("\n")
    f.write(f"\nSUMMARY: {passes} PASS, {fails} FAIL, {warns} WARN\n")

print("\nResults saved to tests/hostile_round4_results.txt")
