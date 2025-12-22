"""
AI DM Skill Check Testing Suite
Tests that the AI DM correctly triggers skill checks for various player actions.
Creates fresh game sessions and sends player inputs to verify skill check responses.
"""

import requests
import re
import json
import time
from datetime import datetime

API_URL = "http://localhost:5000"

# Test definitions: (test_id, category, player_input, expected_skill, min_dc, max_dc)
# Tests use generic targets that always exist (villagers, people, the area)
# Avoid specific NPCs like "guard", "elder", "merchant" that may not be in scene
SKILL_CHECK_TESTS = [
    # Persuasion Tests (1-5) - Use generic NPCs/situations
    (1, "Persuasion", "I try to convince one of the villagers to pay me more for helping", "Persuasion", 12, 15),
    (2, "Persuasion", "I ask a nearby person to help me with supplies", "Persuasion", 12, 15),
    (3, "Persuasion", "I try to convince someone to give me a better reward", "Persuasion", 12, 15),
    (4, "Persuasion", "I try to talk my way out of paying for something", "Persuasion", 12, 15),
    (5, "Persuasion", "I attempt to haggle with someone for a better deal", "Persuasion", 12, 15),
    
    # Intimidation Tests (6-8) - Use generic NPCs
    (6, "Intimidation", "I threaten someone nearby: tell me what you know or else", "Intimidation", 12, 16),
    (7, "Intimidation", "I grab a villager by the collar and demand answers", "Intimidation", 13, 16),
    (8, "Intimidation", "I use threatening body language to make someone talk", "Intimidation", 12, 15),
    
    # Deception Tests (9-11) - Use generic targets
    (9, "Deception", "I lie about being sent here on official business", "Deception", 13, 16),
    (10, "Deception", "I deceive someone into thinking reinforcements are coming", "Deception", 13, 15),
    (11, "Deception", "I pretend to be a simple traveler to avoid suspicion", "Deception", 12, 14),
    
    # Perception Tests (12-14) - Work anywhere
    (12, "Perception", "I carefully scan my surroundings for hidden threats", "Perception", 12, 14),
    (13, "Perception", "I look for traps or ambushes in this area", "Perception", 10, 15),
    (14, "Perception", "I try to spot anything unusual or out of place", "Perception", 10, 13),
    
    # Investigation Tests (15-16) - Use existing objects
    (15, "Investigation", "I examine the area closely for clues about what happened here", "Investigation", 12, 15),
    (16, "Investigation", "I investigate the nearby cart to figure out what happened", "Investigation", 12, 15),
    
    # Athletics Tests (17-19) - Physical challenges
    (17, "Athletics", "I try to climb the large oak tree", "Athletics", 11, 14),
    (18, "Athletics", "I leap across the stream with a running start", "Athletics", 11, 15),
    (19, "Athletics", "I try to push the heavy cart out of the way", "Athletics", 12, 16),
    
    # Stealth Tests (20-21) - Work anywhere
    (20, "Stealth", "I try to move through the area without being noticed", "Stealth", 12, 15),
    (21, "Stealth", "I hide in the shadows to avoid detection", "Stealth", 12, 14),
    
    # Knowledge Tests (22-23) - Work anywhere
    (22, "Arcana", "I try to identify any magical auras or enchantments here", "Arcana", 13, 16),
    (23, "History", "I try to recall legends or stories about this place", "History", 11, 14),
    
    # Insight Tests (24-25) - Use generic targets
    (24, "Insight", "I study someone nearby to see if they're hiding something", "Insight", 11, 14),
    (25, "Insight", "I try to read someone's body language to judge their honesty", "Insight", 10, 14),
]

class SkillCheckTester:
    def __init__(self):
        self.results = []
        self.session_id = None
        
    def check_api_health(self):
        """Check if API is running"""
        try:
            resp = requests.get(f"{API_URL}/api/health", timeout=5)
            return resp.status_code == 200
        except:
            return False
    
    def create_session(self):
        """Create a new game session"""
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
                # Session ID can be at top level or in game_state
                self.session_id = data.get("session_id") or data.get("game_state", {}).get("session_id")
                return True
            return False
        except Exception as e:
            print(f"Session creation failed: {e}")
            return False
    
    def travel_to(self, destination):
        """Use the travel API to move to a location"""
        try:
            resp = requests.post(f"{API_URL}/api/travel", json={
                "session_id": self.session_id,
                "destination": destination
            }, timeout=30)
            return resp.status_code == 200
        except:
            return False
    
    def setup_context(self, category, test_id=None):
        """Skip context setup - let player actions be self-contained"""
        # Don't send any context action - let the player action stand alone
        # This avoids the AI saying "you already did that"
        pass  # No context setup
    
    def send_action(self, action_text):
        """Send a player action and get DM response"""
        try:
            resp = requests.post(f"{API_URL}/api/game/action", json={
                "session_id": self.session_id,
                "action": action_text
            }, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                # Response is in 'message' field
                return data.get("message", data.get("dm_response", data.get("narrative", "")))
            return None
        except Exception as e:
            print(f"Action failed: {e}")
            return None
    
    def analyze_response(self, response, expected_skill, min_dc, max_dc):
        """Analyze DM response for skill check pattern"""
        if not response:
            return {
                "has_skill_check": False,
                "skill_found": None,
                "dc_found": None,
                "correct_skill": False,
                "correct_dc": False,
                "error": "No response received"
            }
        
        # Pattern: [ROLL: SkillName DC X]
        pattern = r'\[ROLL:\s*(\w+)\s+DC\s*(\d+)\]'
        match = re.search(pattern, response, re.IGNORECASE)
        
        if match:
            skill_found = match.group(1)
            dc_found = int(match.group(2))
            
            # Check if skill matches (case-insensitive)
            correct_skill = skill_found.lower() == expected_skill.lower()
            
            # Check if DC is in acceptable range
            correct_dc = min_dc <= dc_found <= max_dc
            
            return {
                "has_skill_check": True,
                "skill_found": skill_found,
                "dc_found": dc_found,
                "correct_skill": correct_skill,
                "correct_dc": correct_dc,
                "error": None
            }
        else:
            # Check if there's any skill check pattern at all
            any_check = re.search(r'\[ROLL:', response, re.IGNORECASE)
            return {
                "has_skill_check": False,
                "skill_found": None,
                "dc_found": None,
                "correct_skill": False,
                "correct_dc": False,
                "error": "No skill check found in response" if not any_check else "Malformed skill check"
            }
    
    def run_test(self, test_id, category, player_input, expected_skill, min_dc, max_dc):
        """Run a single skill check test"""
        print(f"\n{'='*60}")
        print(f"TEST {test_id}: {category}")
        print(f"{'='*60}")
        print(f"Player Input: {player_input}")
        print(f"Expected: [ROLL: {expected_skill} DC {min_dc}-{max_dc}]")
        
        # Create fresh session for each test
        if not self.create_session():
            return {
                "test_id": test_id,
                "category": category,
                "player_input": player_input,
                "expected_skill": expected_skill,
                "status": "ERROR",
                "dm_response": "Failed to create session",
                "analysis": None
            }
        
        # Set up context first (go to appropriate location/NPC)
        print(f"Setting up context for {category}...")
        self.setup_context(category, test_id)
        
        # Send the actual test action
        response = self.send_action(player_input)
        
        # Analyze the response
        analysis = self.analyze_response(response, expected_skill, min_dc, max_dc)
        
        # Determine pass/fail
        if analysis["has_skill_check"] and analysis["correct_skill"]:
            if analysis["correct_dc"]:
                status = "PASS"
            else:
                status = "WARN"  # Right skill, DC out of range
        elif analysis["has_skill_check"]:
            status = "FAIL"  # Wrong skill
        else:
            status = "FAIL"  # No skill check
        
        # Print results
        print(f"\nDM Response (truncated): {response[:200] if response else 'None'}...")
        print(f"\nAnalysis:")
        print(f"  - Has Skill Check: {analysis['has_skill_check']}")
        print(f"  - Skill Found: {analysis['skill_found']}")
        print(f"  - DC Found: {analysis['dc_found']}")
        print(f"  - Correct Skill: {analysis['correct_skill']}")
        print(f"  - Correct DC: {analysis['correct_dc']}")
        print(f"\n>>> STATUS: {status} <<<")
        
        return {
            "test_id": test_id,
            "category": category,
            "player_input": player_input,
            "expected_skill": expected_skill,
            "expected_dc_range": f"{min_dc}-{max_dc}",
            "status": status,
            "dm_response": response[:500] if response else None,
            "analysis": analysis
        }
    
    def run_all_tests(self):
        """Run all 25 skill check tests"""
        print("\n" + "="*70)
        print("AI DM SKILL CHECK TESTING SUITE")
        print("="*70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"API URL: {API_URL}")
        print(f"Total Tests: {len(SKILL_CHECK_TESTS)}")
        
        # Check API health
        if not self.check_api_health():
            print("\n❌ ERROR: API is not running at", API_URL)
            print("Please start the backend server first.")
            return
        
        print("\n✅ API is healthy, starting tests...\n")
        
        # Run each test
        for test_data in SKILL_CHECK_TESTS:
            result = self.run_test(*test_data)
            self.results.append(result)
            time.sleep(1)  # Small delay between tests
        
        # Print summary
        self.print_summary()
        
        # Save results to file
        self.save_results()
    
    def print_summary(self):
        """Print test summary"""
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        warned = sum(1 for r in self.results if r["status"] == "WARN")
        errors = sum(1 for r in self.results if r["status"] == "ERROR")
        
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Total Tests: {len(self.results)}")
        print(f"✅ PASSED:  {passed}")
        print(f"❌ FAILED:  {failed}")
        print(f"⚠️  WARNED:  {warned}")
        print(f"🔴 ERRORS:  {errors}")
        print(f"\nPass Rate: {(passed/len(self.results)*100):.1f}%")
        
        # List failures
        if failed > 0:
            print("\n" + "-"*40)
            print("FAILED TESTS:")
            for r in self.results:
                if r["status"] == "FAIL":
                    print(f"  Test {r['test_id']}: {r['category']} - {r['analysis']['error'] if r['analysis'] else 'Unknown'}")
        
        # List warnings
        if warned > 0:
            print("\n" + "-"*40)
            print("WARNED TESTS (DC out of range):")
            for r in self.results:
                if r["status"] == "WARN":
                    print(f"  Test {r['test_id']}: Expected DC {r['expected_dc_range']}, Got DC {r['analysis']['dc_found']}")
    
    def save_results(self):
        """Save results to JSON file"""
        output = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if r["status"] == "PASS"),
            "failed": sum(1 for r in self.results if r["status"] == "FAIL"),
            "warned": sum(1 for r in self.results if r["status"] == "WARN"),
            "results": self.results
        }
        
        with open("tests/skill_check_results.json", "w") as f:
            json.dump(output, f, indent=2)
        
        print(f"\n📄 Results saved to tests/skill_check_results.json")


def main():
    tester = SkillCheckTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
