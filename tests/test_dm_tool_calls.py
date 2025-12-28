"""
AI DM Tool Call Testing Suite
Tests that the AI DM correctly triggers game system tags for various player actions.

This test suite covers:
1. Combat triggers ([COMBAT: enemy_type])
2. Item rewards ([ITEM: item_name])
3. Gold rewards ([GOLD: amount])
4. XP rewards ([XP: amount | reason])
5. Roll format compliance ([ROLL: Skill DC X])
6. Multi-turn context memory
7. Edge case handling
8. Transaction tags ([BUY:], [PAY:], [RECRUIT:])
9. Anti-patterns (no-reroll, no-auto-travel, no-xp-for-combat)
10. Combat variants (multiple enemies, SURPRISE modifier)

Run with: python tests/test_dm_tool_calls.py
Requires: Backend server running at localhost:5000
"""

import requests
import re
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional

API_URL = "http://localhost:5000"


# =============================================================================
# TEST DEFINITIONS
# =============================================================================

# Combat trigger tests: (test_id, description, player_input, expected_enemy_type_pattern, required_location)
COMBAT_TRIGGER_TESTS = [
    (1, "Attack goblin explicitly", "I attack the goblin!", r"goblin", "cave_interior"),
    (2, "Draw weapon on enemy", "I draw my sword and charge at the goblins!", r"goblin|bandit|enemy", "cave_interior"),
    (3, "Hostile action to NPC", "I punch the barkeep in the face", r"barkeep|commoner|villager|bandit", "tavern_bar"),
    (4, "Indirect combat trigger", "I threaten the goblin with my weapon and attack it!", r"goblin", "cave_interior"),
    (5, "Multiple enemies", "I attack all the goblins at once!", r"goblin.*goblin|goblin,\s*goblin", "cave_interior"),
    (6, "Surprise attack", "I sneak up behind the goblin and attack from behind!", r"SURPRISE|surprise", "cave_interior"),
    (7, "Non-combat should not trigger", "I greet the barkeep warmly", None, "tavern_bar"),  # Should NOT trigger combat
]

# Item reward tests: situations where AI should give items
ITEM_REWARD_TESTS = [
    (1, "Search container", "I search the chest thoroughly", "should find item or empty message"),
    (2, "Loot after victory", "I search the body for loot", "should find item or nothing"),
    (3, "Take visible item", "I pick up the torch from the table", "should give torch or acknowledge"),
    (4, "NPC gives item", "I accept the reward from Bram", "should give quest reward item"),
]

# Gold reward tests: situations where AI should give gold
GOLD_REWARD_TESTS = [
    (1, "Find gold pile", "I pick up the gold coins on the ground", r"\[GOLD:\s*\d+\]"),
    (2, "Quest reward gold", "I collect my reward from completing the quest", r"\[GOLD:\s*\d+\]"),
    (3, "Loot gold from enemy", "I check the goblin's pouch for coins", r"\[GOLD:\s*\d+\]"),
]

# Roll format compliance tests - (test_id, description, player_input, expected_skill, required_location)
ROLL_FORMAT_TESTS = [
    (1, "Stealth movement", "I try to sneak past the goblins", "Stealth", "cave_interior"),
    (2, "Perception check", "I carefully scan the area for traps", "Perception", "cave_interior"),
    (3, "Persuasion attempt", "I try to convince the barkeep to give me a discount on ale", "Persuasion", "tavern_bar"),
    (4, "Investigation search", "I investigate the strange claw marks on the cave wall", "Investigation", "cave_interior"),
    (5, "Athletics climb", "I attempt to climb the rocky cave wall", "Athletics", "cave_interior"),
    (6, "Arcana identify", "I try to identify any magical energy in this cave", "Arcana", "cave_interior"),
]

# Transaction tag tests: [BUY:], [PAY:], [RECRUIT:]
TRANSACTION_TESTS = [
    {
        "id": 1,
        "description": "Buy item from blacksmith",
        "required_location": "blacksmith",
        "setup_action": "I look at what weapons you have for sale",
        "test_action": "I want to buy a dagger please",
        "expected_tag": r"\[BUY:\s*\w+\s*,\s*\d+\]",
        "tag_name": "BUY"
    },
    {
        "id": 2,
        "description": "Pay for service at tavern",
        "required_location": "tavern",  # Main room where Marcus is
        "setup_action": "I talk to Marcus about joining my adventure",
        "test_action": "I'll pay you 20 gold to join my party, Marcus",
        "expected_tag": r"\[PAY:\s*\d+",
        "tag_name": "PAY"
    },
    {
        "id": 3,
        "description": "Recruit companion at tavern",
        "required_location": "tavern",  # Main room where Marcus is
        "setup_action": "Marcus, I need a fighter to help me clear the goblin cave",
        "test_action": "I agree to your terms. Join my party.",
        "expected_tag": r"\[RECRUIT:\s*\w+\]",
        "tag_name": "RECRUIT"
    },
]

# Anti-pattern tests: things AI should NOT do
ANTI_PATTERN_TESTS = [
    {
        "id": 1,
        "description": "No reroll after failure",
        "required_location": "cave_interior",
        "setup_action": "I search the area for hidden items",  # First search
        "wait_for_failure": True,  # Only test if first one fails
        "test_action": "I search the area again more carefully",
        "forbidden_pattern": r"\[ROLL:\s*\w+\s+DC\s*\d+\]",
        "expected_behavior": "AI should deny the reroll"
    },
    {
        "id": 2,
        "description": "No auto-travel to locations",
        "required_location": "tavern",  # Start in tavern
        "setup_action": None,
        "test_action": "I want to go to the goblin cave immediately",
        "forbidden_pattern": r"you arrive|you enter the cave|entering the cave|inside the cave",
        "expected_behavior": "AI should tell player to use 'go <direction>'"
    },
    {
        "id": 3,
        "description": "No XP for combat",
        "required_location": "cave_interior",
        "setup_action": "I attack the goblin!",  # Start combat
        "test_action": "I defeat the goblin with my sword",
        "forbidden_pattern": r"\[XP:\s*\d+",
        "expected_behavior": "Combat XP is automatic, AI should not add more"
    },
    {
        "id": 4,
        "description": "No invented NPCs",
        "required_location": "tavern",
        "setup_action": None,
        "test_action": "I want to talk to Elara the healer",
        "forbidden_pattern": r"Elara\s+(says|tells|explains|greets|welcomes)",
        "expected_behavior": "AI should say NPC is unknown"
    },
]

# Multi-turn context tests
CONTEXT_MEMORY_TESTS = [
    {
        "id": 1,
        "description": "Remember NPC name",
        "required_location": "tavern_bar",  # Barkeep is in the bar area
        "setup_action": "I talk to the barkeep and ask his name",
        "test_action": "What was the barkeep's name again?",
        "expected_pattern": r"barkeep|name|told|said|called|Greth",  # Added NPC name
    },
    {
        "id": 2, 
        "description": "Remember location visited",
        "required_location": "blacksmith",  # Go somewhere specific
        "setup_action": "go east",  # Go back to village square
        "test_action": "Where did I just come from?",
        "expected_pattern": r"forge|blacksmith|came from|traveled from",
    },
    {
        "id": 3,
        "description": "Remember player's stated goal",
        "required_location": "tavern",  # Main room with Bram
        "setup_action": "I tell Bram I'm here to rescue his daughter from the goblins",
        "test_action": "What did I promise Bram?",
        "expected_pattern": r"rescue|daughter|help|promised|goblins|save|Sara",
    },
]

# Edge case tests
EDGE_CASE_TESTS = [
    (1, "Very short input", "hi", "should respond naturally"),
    (2, "Single word action", "attack", "should ask for clarification or describe scene"),
    (3, "Empty-ish input", "   ", "should ask what player wants to do"),
    (4, "Unicode/emoji input", "I cast ⚡ lightning at the enemy 🐉", "should handle gracefully"),
    (5, "Repeated words", "attack attack attack attack attack", "should not duplicate actions"),
    (6, "Numbers only", "12345", "should ask for clarification"),
    (7, "Mixed case", "I ATTACK THE GOBLIN", "should work normally"),
    (8, "Question only", "What can I do here?", "should describe options"),
]


# =============================================================================
# LOCATION NAVIGATION MAP
# =============================================================================

# Navigation paths from starting location (tavern_main - where player spawns)
# Map: tavern_main → (south) → village_square → (east) → forest_path → (east) → forest_clearing
#      → (east) → darkhollow_approach → (east) → cave_entrance → (east) → cave_tunnel
#      → (east) → goblin_camp_entrance (has goblins!)
#
# Tavern internal: tavern_main → (north) → tavern_bar (where barkeep Greth is)
# Direct travel destinations using location IDs (for /api/travel endpoint)
# The travel API accepts location_id or exit_name directly
LOCATION_IDS = {
    "tavern": "tavern_main",           # Starting location
    "tavern_bar": "tavern_bar",        # Bar area where barkeep Greth is  
    "village_square": "village_square", # Main village square
    "blacksmith": "blacksmith_shop",   # Torvin's forge
    "forest": "forest_path",           # First forest area
    "forest_clearing": "forest_clearing",
    "cave_entrance": "cave_entrance",  # Darkhollow cave entrance
    "cave_interior": "goblin_camp_main",  # Main goblin camp with goblins!
}

# Path from tavern_main to each location (used for fallback navigation if travel API fails)
LOCATION_PATHS = {
    "tavern": [],  # Starting location - player spawns in tavern main room
    "tavern_bar": ["north"],  # Bar area where barkeep Greth is
    "village_square": ["outside"],  # Exit tavern to village square
    "blacksmith": ["outside", "west"],  # Village square then west to forge
    "forest": ["outside", "east"],  # Village square then east to forest path
    "forest_clearing": ["outside", "east", "east"],  # Through forest to clearing
    "cave_entrance": ["outside", "east", "east", "east", "cave"],  # To cave entrance
    "cave_interior": ["outside", "east", "east", "east", "cave", "inside", "deeper", "camp"],  # Deep into goblin camp
}


# =============================================================================
# TEST HARNESS
# =============================================================================

class DMToolCallTester:
    """Test harness for DM tool call verification."""
    
    def __init__(self):
        self.results = []
        self.session_id = None
        self.api_healthy = False
        self.current_location = "spawn"  # Track location for navigation
        
    def check_api_health(self) -> bool:
        """Check if API is running."""
        try:
            resp = requests.get(f"{API_URL}/api/health", timeout=5)
            self.api_healthy = resp.status_code == 200
            return self.api_healthy
        except:
            self.api_healthy = False
            return False
    
    def create_session(self) -> bool:
        """Create a new game session."""
        try:
            resp = requests.post(f"{API_URL}/api/game/start", json={
                "character": {
                    "name": "TestHero",
                    "char_class": "Fighter",
                    "race": "Human"
                }
            }, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                self.session_id = data.get("session_id") or data.get("game_state", {}).get("session_id")
                return True
            return False
        except Exception as e:
            print(f"Session creation failed: {e}")
            return False
    
    def send_action(self, action_text: str) -> Optional[str]:
        """Send a player action and get DM response."""
        try:
            resp = requests.post(f"{API_URL}/api/game/action", json={
                "session_id": self.session_id,
                "action": action_text
            }, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("message", data.get("dm_response", data.get("narrative", "")))
            return None
        except Exception as e:
            print(f"Action failed: {e}")
            return None
    
    def travel_to(self, destination: str) -> bool:
        """Travel to a location using API endpoint."""
        try:
            resp = requests.post(f"{API_URL}/api/travel", json={
                "session_id": self.session_id,
                "destination": destination
            }, timeout=30)
            return resp.status_code == 200
        except:
            return False
    
    def advance_to_cave_scene(self) -> bool:
        """Advance the game to the goblin_camp scene for combat testing.
        
        This accepts the quest and progresses through scenes until goblin_camp is available.
        """
        # Step 1: Accept the quest (simulated by action)
        response = self.send_action("I agree to help Bram rescue his daughter from the goblins")
        if not response:
            return False
        time.sleep(0.5)
        
        # Step 2: Navigate to forest
        if not self.travel_to("outside"):
            return False
        time.sleep(0.3)
        
        # Check if forest_clearing is available
        resp = requests.get(f"{API_URL}/api/locations?session_id={self.session_id}")
        if resp.status_code == 200:
            loc_data = resp.json()
            exits = loc_data.get('current_exits', [])
            # If we can go deeper, the journey scene is active
            if 'east road' in exits or 'east' in exits:
                if not self.travel_to("east road"):
                    self.travel_to("east")
                time.sleep(0.3)
        
        # Keep navigating until we reach the cave
        nav_path = ["deeper", "east", "cave", "enter cave", "inside", "deeper", "camp"]
        for step in nav_path:
            result = self.travel_to(step)
            if result:
                time.sleep(0.3)
        
        return True
    
    def navigate_to_location(self, location_key: str) -> bool:
        """Navigate to a specific location using the travel API.
        
        Uses direct location IDs when available, with fallback path navigation.
        """
        # For cave_interior, we need to advance scenes first
        if location_key == "cave_interior":
            return self.advance_to_cave_scene()
        
        # First, try to travel directly using location ID
        location_id = LOCATION_IDS.get(location_key)
        if location_id:
            print(f"    Traveling directly to {location_id}...")
            if self.travel_to(location_id):
                self.current_location = location_key
                print(f"    ✓ Arrived at {location_key}")
                return True
            else:
                print(f"    ✗ Direct travel failed, trying path navigation...")
        
        # Fallback: use step-by-step path navigation
        path = LOCATION_PATHS.get(location_key, [])
        if not path:
            print(f"    ✗ No path defined for {location_key}")
            return False
            
        for step in path:
            print(f"    Step: {step}")
            if not self.travel_to(step):
                print(f"    ✗ Failed at step: {step}")
                return False
            time.sleep(0.3)
        
        self.current_location = location_key
        print(f"    ✓ Arrived at {location_key} via path")
        return True

    # =========================================================================
    # COMBAT TRIGGER TESTS
    # =========================================================================
    
    def test_combat_triggers(self) -> List[Dict]:
        """Test that combat is properly triggered."""
        results = []
        print("\n" + "="*60)
        print("COMBAT TRIGGER TESTS")
        print("="*60)
        
        for test_id, description, player_input, expected_pattern, required_location in COMBAT_TRIGGER_TESTS:
            print(f"\nTest {test_id}: {description}")
            print(f"  Location: {required_location}")
            print(f"  Input: {player_input}")
            
            if not self.create_session():
                results.append({
                    "test_id": test_id,
                    "description": description,
                    "status": "ERROR",
                    "error": "Failed to create session"
                })
                continue
            
            # Navigate to required location
            if not self.navigate_to_location(required_location):
                results.append({
                    "test_id": test_id,
                    "description": description,
                    "status": "ERROR",
                    "error": f"Failed to navigate to {required_location}"
                })
                continue
            
            response = self.send_action(player_input)
            
            if not response:
                results.append({
                    "test_id": test_id,
                    "description": description,
                    "status": "ERROR",
                    "error": "No response received"
                })
                continue
            
            # Check for combat trigger
            combat_match = re.search(r'\[COMBAT:\s*([^\]]+)\]', response, re.IGNORECASE)
            
            # Special case: test 7 expects NO combat trigger
            if expected_pattern is None:
                if combat_match:
                    status = "FAIL"
                    print(f"  ❌ Combat triggered when it shouldn't: {combat_match.group(1)}")
                else:
                    status = "PASS"
                    print(f"  ✅ Correctly did not trigger combat")
                results.append({
                    "test_id": test_id,
                    "description": description,
                    "status": status,
                    "combat_triggered": combat_match is not None,
                    "should_trigger": False,
                    "response_preview": response[:200]
                })
            elif combat_match:
                enemy_type = combat_match.group(1)
                pattern_match = re.search(expected_pattern, enemy_type, re.IGNORECASE)
                status = "PASS" if pattern_match else "PARTIAL"
                results.append({
                    "test_id": test_id,
                    "description": description,
                    "status": status,
                    "combat_triggered": True,
                    "enemy_type": enemy_type,
                    "response_preview": response[:200]
                })
                print(f"  ✅ Combat triggered: {enemy_type}")
            else:
                # Combat might be handled differently (e.g., no valid target)
                results.append({
                    "test_id": test_id,
                    "description": description,
                    "status": "FAIL" if "attack" in player_input.lower() else "WARN",
                    "combat_triggered": False,
                    "response_preview": response[:200]
                })
                print(f"  ❌ No combat tag found")
            
            time.sleep(1)
        
        return results

    # =========================================================================
    # ROLL FORMAT TESTS
    # =========================================================================
    
    def test_roll_format(self) -> List[Dict]:
        """Test that skill checks use correct format."""
        results = []
        print("\n" + "="*60)
        print("ROLL FORMAT COMPLIANCE TESTS")
        print("="*60)
        
        for test_id, description, player_input, expected_skill, required_location in ROLL_FORMAT_TESTS:
            print(f"\nTest {test_id}: {description}")
            print(f"  Location: {required_location}")
            print(f"  Input: {player_input}")
            print(f"  Expected skill: {expected_skill}")
            
            if not self.create_session():
                results.append({
                    "test_id": test_id,
                    "description": description,
                    "status": "ERROR",
                    "error": "Failed to create session"
                })
                continue
            
            # Navigate to required location
            if not self.navigate_to_location(required_location):
                results.append({
                    "test_id": test_id,
                    "description": description,
                    "status": "ERROR",
                    "error": f"Failed to navigate to {required_location}"
                })
                continue
            
            response = self.send_action(player_input)
            
            if not response:
                results.append({
                    "test_id": test_id,
                    "description": description,
                    "status": "ERROR",
                    "error": "No response received"
                })
                continue
            
            # Check for correct roll format
            roll_match = re.search(r'\[ROLL:\s*(\w+)\s+DC\s*(\d+)\]', response, re.IGNORECASE)
            
            if roll_match:
                skill_found = roll_match.group(1)
                dc_found = int(roll_match.group(2))
                
                # Check skill matches
                correct_skill = skill_found.lower() == expected_skill.lower()
                
                # Check DC is reasonable (5-25)
                reasonable_dc = 5 <= dc_found <= 25
                
                status = "PASS" if correct_skill and reasonable_dc else "PARTIAL"
                
                results.append({
                    "test_id": test_id,
                    "description": description,
                    "status": status,
                    "has_roll": True,
                    "skill_found": skill_found,
                    "dc_found": dc_found,
                    "correct_skill": correct_skill,
                    "reasonable_dc": reasonable_dc,
                    "response_preview": response[:200]
                })
                print(f"  ✅ Roll format: [ROLL: {skill_found} DC {dc_found}]")
                if not correct_skill:
                    print(f"      ⚠️ Expected {expected_skill}")
            else:
                # Check for malformed roll tags
                any_roll = re.search(r'\[ROLL', response, re.IGNORECASE)
                results.append({
                    "test_id": test_id,
                    "description": description,
                    "status": "FAIL",
                    "has_roll": False,
                    "has_malformed": any_roll is not None,
                    "response_preview": response[:200]
                })
                print(f"  ❌ No valid roll format found")
            
            time.sleep(1)
        
        return results

    # =========================================================================
    # CONTEXT MEMORY TESTS
    # =========================================================================
    
    def test_context_memory(self) -> List[Dict]:
        """Test that AI remembers previous context."""
        results = []
        print("\n" + "="*60)
        print("MULTI-TURN CONTEXT MEMORY TESTS")
        print("="*60)
        
        for test in CONTEXT_MEMORY_TESTS:
            print(f"\nTest {test['id']}: {test['description']}")
            print(f"  Location: {test.get('required_location', 'spawn')}")
            
            if not self.create_session():
                results.append({
                    "test_id": test['id'],
                    "description": test['description'],
                    "status": "ERROR",
                    "error": "Failed to create session"
                })
                continue
            
            # Navigate to required location if specified
            if test.get('required_location'):
                if not self.navigate_to_location(test['required_location']):
                    results.append({
                        "test_id": test['id'],
                        "description": test['description'],
                        "status": "ERROR",
                        "error": f"Failed to navigate to {test['required_location']}"
                    })
                    continue
            
            # Setup action
            print(f"  Setup: {test['setup_action']}")
            setup_response = self.send_action(test['setup_action'])
            if not setup_response:
                results.append({
                    "test_id": test['id'],
                    "description": test['description'],
                    "status": "ERROR",
                    "error": "Setup action failed"
                })
                continue
            
            time.sleep(1)
            
            # Test action
            print(f"  Test: {test['test_action']}")
            test_response = self.send_action(test['test_action'])
            
            if not test_response:
                results.append({
                    "test_id": test['id'],
                    "description": test['description'],
                    "status": "ERROR",
                    "error": "Test action failed"
                })
                continue
            
            # Check for expected pattern
            pattern_found = re.search(test['expected_pattern'], test_response, re.IGNORECASE)
            
            status = "PASS" if pattern_found else "FAIL"
            results.append({
                "test_id": test['id'],
                "description": test['description'],
                "status": status,
                "setup_response": setup_response[:200],
                "test_response": test_response[:300],
                "pattern_found": pattern_found is not None
            })
            
            if pattern_found:
                print(f"  ✅ Context retained")
            else:
                print(f"  ❌ Context not found in response")
            
            time.sleep(1)
        
        return results

    # =========================================================================
    # EDGE CASE TESTS
    # =========================================================================
    
    def test_edge_cases(self) -> List[Dict]:
        """Test edge case handling."""
        results = []
        print("\n" + "="*60)
        print("EDGE CASE TESTS")
        print("="*60)
        
        for test_id, description, player_input, expected_behavior in EDGE_CASE_TESTS:
            print(f"\nTest {test_id}: {description}")
            print(f"  Input: '{player_input[:50]}...'")
            
            if not self.create_session():
                results.append({
                    "test_id": test_id,
                    "description": description,
                    "status": "ERROR",
                    "error": "Failed to create session"
                })
                continue
            
            response = self.send_action(player_input)
            
            if not response:
                results.append({
                    "test_id": test_id,
                    "description": description,
                    "status": "FAIL",
                    "error": "No response received"
                })
                continue
            
            # Check for reasonable response
            issues = []
            
            # Should have some content
            if len(response) < 10:
                issues.append("Response too short")
            
            # Should not have error messages
            if "[ERROR" in response or "exception" in response.lower():
                issues.append("Contains error message")
            
            # Should not leak system prompt
            system_leak_patterns = [
                r"system\s+instruction",
                r"as\s+an\s+AI",
                r"I\s+cannot",
                r"my\s+programming",
            ]
            for pattern in system_leak_patterns:
                if re.search(pattern, response, re.IGNORECASE):
                    issues.append(f"System leak: {pattern}")
            
            status = "PASS" if len(issues) == 0 else "WARN"
            results.append({
                "test_id": test_id,
                "description": description,
                "status": status,
                "response_length": len(response),
                "issues": issues,
                "response_preview": response[:200]
            })
            
            if len(issues) == 0:
                print(f"  ✅ Handled gracefully")
            else:
                print(f"  ⚠️ Issues: {', '.join(issues)}")
            
            time.sleep(1)
        
        return results

    # =========================================================================
    # REWARD TAG TESTS
    # =========================================================================
    
    def test_reward_tags(self) -> List[Dict]:
        """Test that reward tags are properly formatted."""
        results = []
        print("\n" + "="*60)
        print("REWARD TAG FORMAT TESTS")
        print("="*60)
        
        if not self.create_session():
            return [{"status": "ERROR", "error": "Failed to create session"}]
        
        # Test a scenario that should give rewards
        # Complete a simple objective
        test_cases = [
            ("Search for items", "I carefully search around the tavern for anything useful"),
            ("Ask for reward", "I ask Bram about the reward for helping"),
            ("Check for gold", "I look for any loose coins or valuables"),
        ]
        
        for description, action in test_cases:
            print(f"\nTest: {description}")
            print(f"  Action: {action}")
            
            response = self.send_action(action)
            
            if not response:
                results.append({
                    "description": description,
                    "status": "ERROR",
                    "error": "No response"
                })
                continue
            
            # Check for any reward tags
            gold_match = re.search(r'\[GOLD:\s*(\d+)\]', response, re.IGNORECASE)
            item_match = re.search(r'\[ITEM:\s*([^\]]+)\]', response, re.IGNORECASE)
            xp_match = re.search(r'\[XP:\s*(\d+)\s*\|\s*([^\]]+)\]', response, re.IGNORECASE)
            
            reward_found = {
                "gold": gold_match.group(1) if gold_match else None,
                "item": item_match.group(1) if item_match else None,
                "xp": (xp_match.group(1), xp_match.group(2)) if xp_match else None
            }
            
            results.append({
                "description": description,
                "status": "INFO",  # These are informational
                "rewards_found": reward_found,
                "response_preview": response[:200]
            })
            
            if any(reward_found.values()):
                print(f"  ✅ Rewards found: {reward_found}")
            else:
                print(f"  ℹ️ No reward tags (may be expected)")
            
            time.sleep(1)
        
        return results

    # =========================================================================
    # TRANSACTION TAG TESTS
    # =========================================================================
    
    def test_transaction_tags(self) -> List[Dict]:
        """Test that transaction tags (BUY, PAY, RECRUIT) are properly triggered."""
        results = []
        print("\n" + "="*60)
        print("TRANSACTION TAG TESTS")
        print("="*60)
        
        for test in TRANSACTION_TESTS:
            print(f"\nTest {test['id']}: {test['description']}")
            print(f"  Location: {test.get('required_location', 'spawn')}")
            
            if not self.create_session():
                results.append({
                    "test_id": test['id'],
                    "description": test['description'],
                    "status": "ERROR",
                    "error": "Failed to create session"
                })
                continue
            
            # Navigate to required location
            if test.get('required_location'):
                if not self.navigate_to_location(test['required_location']):
                    results.append({
                        "test_id": test['id'],
                        "description": test['description'],
                        "status": "ERROR",
                        "error": f"Failed to navigate to {test['required_location']}"
                    })
                    continue
            
            # Setup action if needed
            if test.get('setup_action'):
                print(f"  Setup: {test['setup_action']}")
                setup_response = self.send_action(test['setup_action'])
                if not setup_response:
                    results.append({
                        "test_id": test['id'],
                        "description": test['description'],
                        "status": "ERROR",
                        "error": "Setup action failed"
                    })
                    continue
                time.sleep(1)
            
            # Test action
            print(f"  Action: {test['test_action']}")
            response = self.send_action(test['test_action'])
            
            if not response:
                results.append({
                    "test_id": test['id'],
                    "description": test['description'],
                    "status": "ERROR",
                    "error": "No response received"
                })
                continue
            
            # Check for expected tag
            tag_match = re.search(test['expected_tag'], response, re.IGNORECASE)
            
            if tag_match:
                status = "PASS"
                print(f"  ✅ {test['tag_name']} tag found: {tag_match.group(0)}")
            else:
                # Check if tag was attempted but malformed
                partial_match = re.search(rf"\[{test['tag_name']}", response, re.IGNORECASE)
                status = "PARTIAL" if partial_match else "FAIL"
                print(f"  ❌ No valid {test['tag_name']} tag found")
            
            results.append({
                "test_id": test['id'],
                "description": test['description'],
                "status": status,
                "tag_name": test['tag_name'],
                "tag_found": tag_match.group(0) if tag_match else None,
                "response_preview": response[:300]
            })
            
            time.sleep(1)
        
        return results

    # =========================================================================
    # ANTI-PATTERN TESTS
    # =========================================================================
    
    def test_anti_patterns(self) -> List[Dict]:
        """Test that AI does NOT do forbidden actions."""
        results = []
        print("\n" + "="*60)
        print("ANTI-PATTERN TESTS (Things AI should NOT do)")
        print("="*60)
        
        for test in ANTI_PATTERN_TESTS:
            print(f"\nTest {test['id']}: {test['description']}")
            print(f"  Location: {test.get('required_location', 'spawn')}")
            
            if not self.create_session():
                results.append({
                    "test_id": test['id'],
                    "description": test['description'],
                    "status": "ERROR",
                    "error": "Failed to create session"
                })
                continue
            
            # Navigate to required location
            if test.get('required_location'):
                if not self.navigate_to_location(test['required_location']):
                    results.append({
                        "test_id": test['id'],
                        "description": test['description'],
                        "status": "ERROR",
                        "error": f"Failed to navigate to {test['required_location']}"
                    })
                    continue
            
            # Setup action if needed
            if test.get('setup_action'):
                print(f"  Setup: {test['setup_action']}")
                setup_response = self.send_action(test['setup_action'])
                if not setup_response:
                    results.append({
                        "test_id": test['id'],
                        "description": test['description'],
                        "status": "ERROR",
                        "error": "Setup action failed"
                    })
                    continue
                
                # For no-reroll test, check if we need a failure first
                if test.get('wait_for_failure'):
                    if not re.search(r'fail|failed|cannot|unable', setup_response, re.IGNORECASE):
                        results.append({
                            "test_id": test['id'],
                            "description": test['description'],
                            "status": "SKIP",
                            "reason": "First attempt did not fail, cannot test reroll denial"
                        })
                        print(f"  ⏭️ Skipped: First action succeeded")
                        continue
                
                time.sleep(1)
            
            # Test action
            print(f"  Action: {test['test_action']}")
            response = self.send_action(test['test_action'])
            
            if not response:
                results.append({
                    "test_id": test['id'],
                    "description": test['description'],
                    "status": "ERROR",
                    "error": "No response received"
                })
                continue
            
            # Check for FORBIDDEN pattern (we want this to NOT match)
            forbidden_match = re.search(test['forbidden_pattern'], response, re.IGNORECASE)
            
            if forbidden_match:
                status = "FAIL"
                print(f"  ❌ AI did forbidden action: {forbidden_match.group(0)}")
            else:
                status = "PASS"
                print(f"  ✅ AI correctly avoided: {test['expected_behavior']}")
            
            results.append({
                "test_id": test['id'],
                "description": test['description'],
                "status": status,
                "forbidden_found": forbidden_match.group(0) if forbidden_match else None,
                "expected_behavior": test['expected_behavior'],
                "response_preview": response[:300]
            })
            
            time.sleep(1)
        
        return results

    # =========================================================================
    # COMBAT VARIANT TESTS
    # =========================================================================
    
    def test_combat_variants(self) -> List[Dict]:
        """Test combat trigger variations (multiple enemies, surprise)."""
        results = []
        print("\n" + "="*60)
        print("COMBAT VARIANT TESTS")
        print("="*60)
        
        # Subset of combat tests for variants (all require cave_interior)
        variant_tests = [
            (1, "Multiple enemies", "I attack all the goblins at once", r"goblin.*goblin|goblin,\s*goblin|goblins"),
            (2, "Surprise attack", "I sneak up behind the goblin and ambush it from the shadows", r"SURPRISE"),
        ]
        
        for test_id, description, player_input, expected_pattern in variant_tests:
            print(f"\nTest {test_id}: {description}")
            print(f"  Location: cave_interior")
            print(f"  Input: {player_input}")
            
            if not self.create_session():
                results.append({
                    "test_id": test_id,
                    "description": description,
                    "status": "ERROR",
                    "error": "Failed to create session"
                })
                continue
            
            # Navigate to cave interior where goblins are
            if not self.navigate_to_location("cave_interior"):
                results.append({
                    "test_id": test_id,
                    "description": description,
                    "status": "ERROR",
                    "error": "Failed to navigate to cave_interior"
                })
                continue
            
            response = self.send_action(player_input)
            
            if not response:
                results.append({
                    "test_id": test_id,
                    "description": description,
                    "status": "ERROR",
                    "error": "No response received"
                })
                continue
            
            # Check for combat trigger with expected pattern
            combat_match = re.search(r'\[COMBAT:\s*([^\]]+)\]', response, re.IGNORECASE)
            
            if combat_match:
                combat_content = combat_match.group(1)
                pattern_match = re.search(expected_pattern, combat_content, re.IGNORECASE)
                
                if pattern_match:
                    status = "PASS"
                    print(f"  ✅ Combat variant correct: {combat_match.group(0)}")
                else:
                    status = "PARTIAL"
                    print(f"  ⚠️ Combat triggered but missing variant: {combat_match.group(0)}")
            else:
                status = "FAIL"
                print(f"  ❌ No combat trigger found")
            
            results.append({
                "test_id": test_id,
                "description": description,
                "status": status,
                "combat_found": combat_match.group(0) if combat_match else None,
                "expected_pattern": expected_pattern,
                "response_preview": response[:300]
            })
            
            time.sleep(1)
        
        return results

    # =========================================================================
    # MAIN TEST RUNNER
    # =========================================================================
    
    def run_all_tests(self):
        """Run all test suites."""
        print("\n" + "="*70)
        print("AI DM TOOL CALL TESTING SUITE")
        print("="*70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"API URL: {API_URL}")
        
        if not self.check_api_health():
            print("\n❌ ERROR: API is not running at", API_URL)
            print("Please start the backend server first:")
            print("  python src/api_server.py")
            return
        
        print("\n✅ API is healthy, starting tests...\n")
        
        all_results = {
            "timestamp": datetime.now().isoformat(),
            "api_url": API_URL,
            "tests": {}
        }
        
        # Run each test suite
        print("\n" + "="*70)
        print("RUNNING TEST SUITES")
        print("="*70)
        
        all_results["tests"]["roll_format"] = self.test_roll_format()
        all_results["tests"]["context_memory"] = self.test_context_memory()
        all_results["tests"]["edge_cases"] = self.test_edge_cases()
        all_results["tests"]["reward_tags"] = self.test_reward_tags()
        all_results["tests"]["transaction_tags"] = self.test_transaction_tags()
        all_results["tests"]["anti_patterns"] = self.test_anti_patterns()
        all_results["tests"]["combat_variants"] = self.test_combat_variants()
        
        # Combat triggers can be disruptive, run last
        all_results["tests"]["combat_triggers"] = self.test_combat_triggers()
        
        # Print summary
        self.print_summary(all_results)
        
        # Save results
        self.save_results(all_results)
    
    def print_summary(self, all_results: Dict):
        """Print test summary."""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        total_pass = 0
        total_fail = 0
        total_warn = 0
        total_error = 0
        
        for suite_name, results in all_results["tests"].items():
            suite_pass = sum(1 for r in results if r.get("status") == "PASS")
            suite_fail = sum(1 for r in results if r.get("status") == "FAIL")
            suite_warn = sum(1 for r in results if r.get("status") in ["WARN", "PARTIAL"])
            suite_error = sum(1 for r in results if r.get("status") == "ERROR")
            
            total_pass += suite_pass
            total_fail += suite_fail
            total_warn += suite_warn
            total_error += suite_error
            
            print(f"\n{suite_name}:")
            print(f"  ✅ PASS: {suite_pass}  ❌ FAIL: {suite_fail}  ⚠️ WARN: {suite_warn}  🔴 ERROR: {suite_error}")
        
        print("\n" + "-"*40)
        print("TOTALS:")
        print(f"  ✅ PASSED:  {total_pass}")
        print(f"  ❌ FAILED:  {total_fail}")
        print(f"  ⚠️ WARNED:  {total_warn}")
        print(f"  🔴 ERRORS:  {total_error}")
        
        total_tests = total_pass + total_fail + total_warn + total_error
        if total_tests > 0:
            pass_rate = (total_pass / total_tests) * 100
            print(f"\n  Pass Rate: {pass_rate:.1f}%")
    
    def save_results(self, results: Dict):
        """Save results to JSON file."""
        import os
        # Use script's directory for output
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(script_dir, "tool_call_results.json")
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n📄 Results saved to {output_path}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run the test suite."""
    tester = DMToolCallTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
