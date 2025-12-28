"""Quick test for Marcus recruitment tags."""
import requests
import time

BASE_URL = "http://localhost:5000"

# Create session
resp = requests.post(f"{BASE_URL}/api/game/start", json={
    "character": {"name": "TestRecruiter", "class": "Fighter", "race": "Human"}
})
if resp.status_code != 200:
    print(f"Failed to start: {resp.text}")
    exit(1)
    
session_id = resp.json().get("session_id")
print(f"Session: {session_id}\n")

# Go to tavern
resp = requests.post(f"{BASE_URL}/api/game/action", json={
    "session_id": session_id,
    "action": "go west"
})
print("Moved to tavern\n")
time.sleep(1)

# Check how much gold we have
resp = requests.get(f"{BASE_URL}/api/game/state", params={"session_id": session_id})
if resp.status_code == 200:
    gold = resp.json().get("character", {}).get("gold", 0)
    print(f"Current gold: {gold}\n")

# Try to hire Marcus with very explicit language
print("=" * 60)
print("ATTEMPTING MARCUS RECRUITMENT")
print("=" * 60)

# Explicitly offer 20 gold to hire Marcus
resp = requests.post(f"{BASE_URL}/api/game/action", json={
    "session_id": session_id,
    "action": "I offer Marcus 20 gold to join my party. Here's my payment."
})

if resp.status_code == 200:
    dm_response = resp.json().get("message", "")
    print(f"\nFULL DM RESPONSE:\n{dm_response}")
    
    # Check for tags
    import re
    pay_tags = re.findall(r'\[PAY:\s*(\d+),\s*([^\]]+)\]', dm_response)
    recruit_tags = re.findall(r'\[RECRUIT:\s*(\w+)\]', dm_response)
    
    print(f"\n" + "=" * 60)
    print("TAG ANALYSIS:")
    print(f"[PAY:] tags found: {pay_tags}")
    print(f"[RECRUIT:] tags found: {recruit_tags}")
    
    if pay_tags and recruit_tags:
        print("✅ SUCCESS - Both tags generated!")
    elif pay_tags or recruit_tags:
        print("⚠️ PARTIAL - Only one tag type generated")
    else:
        print("❌ FAILED - No recruitment tags generated")
else:
    print(f"Error: {resp.text}")
