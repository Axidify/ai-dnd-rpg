"""Quick test for combat tag generation."""
import requests

import time

API = 'http://localhost:5000'

# Start a game
r = requests.post(f'{API}/api/game/start', json={
    'character': {
        'name': 'Tester',
        'class': 'Fighter',
        'race': 'Human'
    },
    'scenario_id': 'goblin_cave'
})
data = r.json()
print(f'Start response: {r.status_code}')
if 'error' in data:
    print(f'Error: {data["error"]}')
    exit(1)
session_id = data.get('session_id')
if not session_id:
    print(f'No session_id in response: {data.keys()}')
    exit(1)
print(f'Session: {session_id}')

# Unlock all locations for testing (using debug endpoint)
print('\n--- Unlocking all locations ---')
r = requests.post(f'{API}/api/debug/unlock_all_locations', json={
    'session_id': session_id
})
if r.status_code == 200:
    data = r.json()
    print(f'✓ Unlocked {data.get("unlocked_count", 0)} locations')
else:
    print(f'✗ Failed to unlock: {r.json()}')

# Travel step by step to goblin camp
print('\n--- Navigating to goblin camp ---')

def travel(dest):
    r = requests.post(f'{API}/api/travel', json={'session_id': session_id, 'destination': dest})
    resp = r.json()
    success = resp.get('success', False)
    msg = resp.get('message', '')[:60]
    loc = resp.get('new_location', {})
    loc_name = loc.get('name', '') if isinstance(loc, dict) else str(loc)
    print(f'  {dest}: {"✓" if success else "✗"} {loc_name if success else msg}')
    return success

# Full path through scenes
travel('outside')
travel('east road')
travel('deeper')
travel('east')
travel('cave')
travel('enter cave')
travel('inside')
travel('deeper')
travel('camp')

# Now attack
print('\n--- Sending attack action ---')
r = requests.post(f'{API}/api/game/action', json={
    'session_id': session_id,
    'action': 'I attack the goblins!'
})
data = r.json()
response = data.get('message', data.get('dm_response', ''))
print(f'\nAI Response ({len(response)} chars):')
print(response[:1500])
print('\n--- Checking for tags ---')
if '[COMBAT:' in response:
    print('✅ Found [COMBAT:] tag!')
    import re
    matches = re.findall(r'\[COMBAT:[^\]]+\]', response)
    for m in matches:
        print(f'  Tag: {m}')
else:
    print('❌ No [COMBAT:] tag found')

# Check if combat started
if data.get('in_combat') or data.get('combat_started'):
    print('✅ Combat state: ACTIVE')
else:
    print('⚠️ Combat state: NOT ACTIVE')
