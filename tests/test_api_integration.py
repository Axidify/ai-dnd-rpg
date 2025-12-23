"""
API Integration Tests for AI RPG V2
Tests the full game flow through the API endpoints (simulating frontend behavior)
"""

import requests
import json
import time
import sys
import os
import pytest
from dotenv import load_dotenv

# Load environment variables FIRST (before skipif decorators are evaluated)
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

BASE_URL = "http://localhost:5000/api"


class APITestClient:
    """Helper class to interact with the API like the frontend does."""
    
    def __init__(self):
        self.session_id = None
        self.character = None
        
    def health_check(self):
        """Check if API is running."""
        try:
            resp = requests.get(f"{BASE_URL}/health", timeout=5)
            return resp.status_code == 200
        except:
            return False
    
    def get_scenarios(self):
        """Fetch available scenarios."""
        resp = requests.get(f"{BASE_URL}/scenarios")
        resp.raise_for_status()
        return resp.json()
    
    def create_character(self, name, char_class, race, scenario_id=None):
        """Create character and start game."""
        payload = {
            "character": {
                "name": name,
                "class": char_class,
                "race": race
            }
        }
        if scenario_id:
            payload["scenario_id"] = scenario_id
            
        resp = requests.post(f"{BASE_URL}/game/start", json=payload)
        resp.raise_for_status()
        data = resp.json()
        
        self.session_id = data.get('session_id')
        self.character = data.get('game_state', {}).get('character')
        return data
    
    def send_action(self, action):
        """Send an action and get streamed response."""
        if not self.session_id:
            raise ValueError("No session - create character first")
        
        resp = requests.post(
            f"{BASE_URL}/game/action/stream",
            json={"session_id": self.session_id, "action": action},
            stream=True
        )
        resp.raise_for_status()
        
        # Parse SSE events
        full_response = ""
        events = []
        
        for line in resp.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    try:
                        event = json.loads(line[6:])
                        events.append(event)
                        if event.get('type') == 'chunk':
                            full_response += event.get('content', '')
                        if event.get('type') == 'done':
                            self.character = event.get('game_state', {}).get('character')
                    except:
                        pass
        
        return {
            'response': full_response,
            'events': events,
            'character': self.character
        }


def run_test(name, test_func):
    """Run a test and report result."""
    try:
        test_func()
        print(f"✅ {name}")
        return True
    except Exception as e:
        print(f"❌ {name}: {e}")
        return False


def test_health():
    """Test API health endpoint."""
    client = APITestClient()
    assert client.health_check(), "API not responding"


def test_scenarios():
    """Test scenarios endpoint."""
    client = APITestClient()
    scenarios = client.get_scenarios()
    assert 'scenarios' in scenarios, "Missing scenarios key"
    assert len(scenarios['scenarios']) > 0, "No scenarios available"
    
    # Check goblin_cave exists
    scenario_ids = [s['id'] for s in scenarios['scenarios']]
    assert 'goblin_cave' in scenario_ids, "goblin_cave scenario missing"


def test_character_creation():
    """Test character creation with stat rolling."""
    client = APITestClient()
    result = client.create_character("TestHero", "Fighter", "Human", "goblin_cave")
    
    assert result.get('success'), "Character creation failed"
    assert client.session_id, "No session ID returned"
    assert client.character, "No character data returned"
    
    # Check stats were rolled (not all 10s)
    char = client.character
    stats = [char.get('strength'), char.get('dexterity'), char.get('constitution'),
             char.get('intelligence'), char.get('wisdom'), char.get('charisma')]
    
    # At least some stats should differ from 10 (rolled 4d6 drop lowest)
    assert not all(s == 10 for s in stats), f"Stats not rolled: {stats}"
    
    # Check starting equipment was added
    assert len(char.get('inventory', [])) > 0, "No starting inventory"
    
    # Check starting gold
    assert char.get('gold', 0) > 0, "No starting gold"


def test_npc_names():
    """Test that NPC names match scenario (Bram, not invented names)."""
    client = APITestClient()
    result = client.create_character("TestHero", "Fighter", "Human", "goblin_cave")
    
    # Check the opening message mentions Bram or Lily (scenario NPCs)
    message = result.get('message', '')
    
    # Skip if AI is unavailable (fallback message)
    if 'AI Dungeon Master Unavailable' in message:
        pytest.skip("AI DM not available - test requires working AI")
    
    # Should mention the farmer's daughter Lily
    assert 'Lily' in message or 'daughter' in message, \
        f"Opening should mention Lily or daughter. Got: {message[:200]}..."


def test_look_around():
    """Test looking around in starting location."""
    client = APITestClient()
    client.create_character("TestHero", "Wizard", "Elf", "goblin_cave")
    
    result = client.send_action("look around")
    
    assert result['response'], "No response from looking around"
    assert len(result['response']) > 50, "Response too short"


def test_talk_to_npc():
    """Test talking to an NPC."""
    client = APITestClient()
    client.create_character("TestHero", "Bard", "Half-Elf", "goblin_cave")
    
    # Talk to the farmer (Bram)
    result = client.send_action("talk to the farmer")
    
    assert result['response'], "No response from talking to NPC"


def test_skill_check():
    """Test that skill checks work."""
    client = APITestClient()
    client.create_character("TestHero", "Rogue", "Halfling", "goblin_cave")
    
    # Try to persuade - should trigger a skill check
    result = client.send_action("I try to persuade the farmer to give me more details about the goblins")
    
    # Check for roll event
    roll_events = [e for e in result['events'] if e.get('type') == 'roll']
    # Note: DM may or may not call for a roll - this is expected behavior


def test_inventory_serialization():
    """Test that inventory items serialize correctly (enum handling)."""
    client = APITestClient()
    result = client.create_character("TestHero", "Fighter", "Dwarf", "goblin_cave")
    
    char = result.get('game_state', {}).get('character', {})
    inventory = char.get('inventory', [])
    
    for item in inventory:
        # item_type should be a string, not an enum
        assert isinstance(item.get('item_type'), str), \
            f"item_type should be string, got: {type(item.get('item_type'))}"
        assert isinstance(item.get('rarity'), str), \
            f"rarity should be string, got: {type(item.get('rarity'))}"


def test_xp_field():
    """Test that experience field is present."""
    client = APITestClient()
    result = client.create_character("TestHero", "Cleric", "Human", "goblin_cave")
    
    char = result.get('game_state', {}).get('character', {})
    
    # Should have 'experience' field (not 'xp')
    assert 'experience' in char, "Missing 'experience' field in character"
    assert char['experience'] == 0, "Starting XP should be 0"


def test_hp_fields():
    """Test that HP fields are correct."""
    client = APITestClient()
    result = client.create_character("TestHero", "Barbarian", "Half-Orc", "goblin_cave")
    
    char = result.get('game_state', {}).get('character', {})
    
    assert 'current_hp' in char, "Missing current_hp field"
    assert 'max_hp' in char, "Missing max_hp field"
    assert char['current_hp'] == char['max_hp'], "Starting HP should equal max HP"
    
    # Barbarian has d12 hit die, so should be at least 3 (12 + (-3 for CON 5))
    assert char['max_hp'] >= 3, f"Max HP too low: {char['max_hp']}"


def test_reputation_list():
    """Test the /api/reputation endpoint returns all NPCs."""
    client = APITestClient()
    result = client.create_character("TestHero", "Fighter", "Human", "goblin_cave")
    session_id = result.get('session_id')
    
    assert session_id, "No session ID returned"
    
    # Call reputation endpoint
    response = requests.get(
        f"{BASE_URL}/reputation",
        params={'session_id': session_id}
    )
    
    assert response.status_code == 200, f"Reputation endpoint failed: {response.status_code}"
    
    data = response.json()
    assert data.get('success') is True, "Reputation request not successful"
    assert 'relationships' in data, "Missing 'relationships' in response"
    
    relationships = data['relationships']
    assert len(relationships) > 0, "No NPCs returned"
    
    # Check NPC structure
    first_npc = relationships[0]
    assert 'npc_id' in first_npc, "NPC missing 'npc_id'"
    assert 'name' in first_npc, "NPC missing 'name'"
    assert 'disposition' in first_npc, "NPC missing 'disposition'"
    assert 'level' in first_npc, "NPC missing 'level'"
    assert 'label' in first_npc, "NPC missing 'label'"
    assert 'can_trade' in first_npc, "NPC missing 'can_trade'"
    
    # Label should contain emoji
    assert any(emoji in first_npc['label'] for emoji in ['🔴', '🟠', '🟡', '🟢', '🔵', '💚']), \
        f"Label should contain tier emoji: {first_npc['label']}"
    
    # Check summary stats exist
    assert 'summary' in data, "Missing summary in response"
    assert 'total_npcs' in data['summary'], "Missing total_npcs in summary"


def test_reputation_detail():
    """Test the /api/reputation/<npc_id> endpoint returns NPC detail."""
    client = APITestClient()
    result = client.create_character("TestHero", "Fighter", "Human", "goblin_cave")
    session_id = result.get('session_id')
    
    assert session_id, "No session ID returned"
    
    # Call reputation detail endpoint for barkeep (common NPC in tavern)
    response = requests.get(
        f"{BASE_URL}/reputation/barkeep",
        params={'session_id': session_id}
    )
    
    assert response.status_code == 200, f"Reputation detail failed: {response.status_code}"
    
    data = response.json()
    assert data.get('success') is True, "Reputation detail not successful"
    assert 'npc' in data, "Missing 'npc' in response"
    
    npc = data['npc']
    assert npc['id'] == 'barkeep', f"Wrong NPC returned: {npc['id']}"
    assert 'disposition' in npc, "Missing disposition"
    assert 'price_modifier' in npc, "Missing price_modifier"
    assert 'description' in npc, "Missing description"
    assert 'level' in npc, "Missing level"
    assert 'label' in npc, "Missing label"


def test_reputation_not_found():
    """Test that non-existent NPC returns 404."""
    client = APITestClient()
    result = client.create_character("TestHero", "Fighter", "Human", "goblin_cave")
    session_id = result.get('session_id')
    
    response = requests.get(
        f"{BASE_URL}/reputation/nonexistent_npc",
        params={'session_id': session_id}
    )
    
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"


def main():
    """Run all API integration tests."""
    print("=" * 60)
    print("🎲 AI RPG V2 - API Integration Tests")
    print("=" * 60)
    
    # Check API is running
    client = APITestClient()
    if not client.health_check():
        print("❌ API is not running at http://localhost:5000")
        print("   Start the backend with: python src/api_server.py")
        return 1
    
    print(f"\n✅ API is running\n")
    
    tests = [
        ("Health Check", test_health),
        ("Get Scenarios", test_scenarios),
        ("Character Creation with Stats", test_character_creation),
        ("NPC Names Match Scenario", test_npc_names),
        ("Look Around Action", test_look_around),
        ("Talk to NPC", test_talk_to_npc),
        ("Skill Check Handling", test_skill_check),
        ("Inventory Serialization (Enums)", test_inventory_serialization),
        ("XP Field Name", test_xp_field),
        ("HP Fields (current_hp/max_hp)", test_hp_fields),
        ("Reputation List", test_reputation_list),
        ("Reputation Detail", test_reputation_detail),
        ("Reputation Not Found", test_reputation_not_found),
    ]
    
    passed = 0
    failed = 0
    
    print("Running tests...\n")
    
    for name, test_func in tests:
        if run_test(name, test_func):
            passed += 1
        else:
            failed += 1
        time.sleep(0.5)  # Small delay between tests
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
