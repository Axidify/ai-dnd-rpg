"""
AI DM Combat Mechanics Assessment
==================================
Focused tests on combat triggering and format compliance.
Includes proper rate limiting delays to avoid API quota issues.

Tests:
1. Combat trigger detection from player actions
2. Combat tag format compliance
3. Enemy count matching
4. Surprise mechanic handling
5. Non-combat situations (false positive avoidance)
6. Edge cases for combat initiation

Run with: python -m tests.test_dm_combat
Requires: GOOGLE_API_KEY environment variable
"""

import sys
import os
import time
import re
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from character import Character
from scenario import ScenarioManager, create_goblin_cave_shops
import google.generativeai as genai

from dm_engine import (
    DM_SYSTEM_PROMPT,
    parse_roll_request,
    parse_combat_request,
)


# Rate limiting configuration
API_DELAY = 3.0  # Seconds between API calls
CATEGORY_DELAY = 5.0  # Seconds between test categories


@dataclass
class CombatTestResult:
    """Result of a combat test."""
    category: str
    test_name: str
    player_action: str
    dm_response: str
    expected_combat: bool
    actual_combat: bool
    expected_enemies: Optional[List[str]] = None
    actual_enemies: Optional[List[str]] = None
    expected_surprise: Optional[bool] = None
    actual_surprise: Optional[bool] = None
    passed: bool = False
    notes: str = ""


@dataclass
class CombatReport:
    """Report of combat testing."""
    timestamp: str = ""
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    api_calls: int = 0
    results: List[CombatTestResult] = field(default_factory=list)
    
    @property
    def pass_rate(self) -> float:
        return (self.passed / self.total_tests * 100) if self.total_tests > 0 else 0


class DMCombatTester:
    """Test DM combat mechanics with rate limiting."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.report = CombatReport(timestamp=datetime.now().isoformat())
        
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found!")
        genai.configure(api_key=self.api_key)
    
    def log(self, msg: str, force: bool = False):
        if self.verbose or force:
            print(msg)
    
    def setup_game(self, extra_context: str = ""):
        """Initialize game state."""
        character = Character(
            name="CombatTester",
            race="Human",
            char_class="Fighter",
            level=3,
            strength=16, dexterity=14, constitution=14,
            intelligence=10, wisdom=12, charisma=10
        )
        character.gold = 100
        
        scenario_manager = ScenarioManager()
        scenario_manager.start_scenario("goblin_cave")
        
        return character, scenario_manager
    
    def create_dm(self, character, scenario_context: str, combat_context: str = ""):
        """Create DM chat session with combat context."""
        system_prompt = f"""{DM_SYSTEM_PROMPT}

CHARACTER:
- Name: {character.name}
- Race: {character.race}
- Class: {character.char_class}
- Level: {character.level}
- HP: {character.current_hp}/{character.max_hp}
- Gold: {character.gold}
- Weapon: Longsword

{scenario_context}

{combat_context}

Available enemies for combat: goblin, goblin_boss, skeleton, orc, bandit, wolf
"""
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash-exp',
            system_instruction=system_prompt
        )
        return model.start_chat()
    
    def send_with_delay(self, chat, msg: str, delay: float = API_DELAY) -> str:
        """Send message to DM with rate limiting."""
        self.report.api_calls += 1
        try:
            response = chat.send_message(msg)
            time.sleep(delay)  # Rate limiting
            return response.text
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                self.log(f"   ⚠️ Rate limited, waiting 30s...")
                time.sleep(30)
                try:
                    response = chat.send_message(msg)
                    time.sleep(delay)
                    return response.text
                except:
                    pass
            return f"[ERROR: {error_msg}]"
    
    def record_result(self, result: CombatTestResult):
        """Record a test result."""
        self.report.total_tests += 1
        if result.passed:
            self.report.passed += 1
        else:
            self.report.failed += 1
        self.report.results.append(result)
    
    # =========================================================================
    # COMBAT TRIGGER TESTS
    # =========================================================================
    
    def test_combat_triggers(self):
        """Test that combat is triggered correctly from player actions."""
        self.log("\n" + "="*70)
        self.log("CATEGORY: Combat Trigger Detection")
        self.log("="*70)
        
        char, scenario = self.setup_game()
        context = scenario.get_dm_context()
        
        # Test cases: (name, action, combat_context, should_trigger, expected_enemies)
        test_cases = [
            # Direct attacks
            ("Direct Attack - Single Goblin",
             "I draw my sword and attack the goblin!",
             "A single goblin stands before you, growling menacingly.",
             True, ["goblin"]),
            
            ("Direct Attack - Multiple Enemies",
             "I charge at the two goblins with my sword drawn!",
             "Two goblins are blocking the path ahead.",
             True, ["goblin", "goblin"]),
            
            ("Aggressive Action - Punch",
             "I punch the orc in the face as hard as I can!",
             "A large orc stands guard at the door.",
             True, ["orc"]),
            
            ("Weapon Draw + Attack",
             "I unsheathe my longsword and swing at the bandit!",
             "A ragged bandit demands your coin purse.",
             True, ["bandit"]),
            
            # Ambush scenarios
            ("Stealth Attack",
             "I sneak up behind the sleeping guard and attack!",
             "A guard is dozing at his post, unaware of your presence.",
             True, ["bandit"]),  # Expecting SURPRISE modifier
            
            # Non-combat (should NOT trigger)
            ("Peaceful Dialogue",
             "I greet the barkeep and ask for a drink.",
             "Gorn the barkeep polishes mugs behind the counter.",
             False, None),
            
            ("Examine Enemy",
             "I carefully observe the goblin from a safe distance.",
             "A goblin patrol passes by below.",
             False, None),
            
            ("Flee Action",
             "I turn around and run away from the goblins!",
             "Three goblins have spotted you!",
             False, None),
            
            ("Negotiate",
             "I hold up my hands and try to negotiate with the bandits.",
             "Bandits surround you, weapons drawn.",
             False, None),
            
            # Edge cases
            ("Implied Violence",
             "I'm going to kill that goblin!",
             "A goblin scouts the area nearby.",
             True, ["goblin"]),
            
            ("Defensive Strike",
             "As the wolf lunges at me, I swing my sword to defend myself!",
             "A wolf growls and prepares to pounce.",
             True, ["wolf"]),
        ]
        
        for name, action, combat_context, should_trigger, expected_enemies in test_cases:
            chat = self.create_dm(char, context, combat_context)
            response = self.send_with_delay(chat, action)
            
            self.log(f"\n⚔️ Test: {name}")
            self.log(f"   Action: {action[:60]}...")
            self.log(f"   Context: {combat_context[:50]}...")
            self.log(f"   Response: {response[:150]}...")
            
            # Parse combat trigger
            enemies, surprise = parse_combat_request(response)
            actual_combat = len(enemies) > 0
            
            # Determine pass/fail
            passed = (actual_combat == should_trigger)
            notes = ""
            
            if should_trigger:
                if actual_combat:
                    notes = f"Combat triggered: {enemies}"
                    # Check enemy count
                    if expected_enemies and len(enemies) != len(expected_enemies):
                        notes += f" (expected {len(expected_enemies)} enemies)"
                else:
                    notes = "MISSING: Should have triggered combat"
            else:
                if actual_combat:
                    notes = f"FALSE POSITIVE: Combat triggered when shouldn't: {enemies}"
                    passed = False
                else:
                    notes = "Correctly no combat"
            
            status = "✅ PASS" if passed else "❌ FAIL"
            self.log(f"   Result: {status} - {notes}")
            
            result = CombatTestResult(
                category="combat_trigger",
                test_name=name,
                player_action=action,
                dm_response=response[:500],
                expected_combat=should_trigger,
                actual_combat=actual_combat,
                expected_enemies=expected_enemies,
                actual_enemies=enemies if enemies else None,
                passed=passed,
                notes=notes
            )
            self.record_result(result)
    
    # =========================================================================
    # COMBAT FORMAT TESTS
    # =========================================================================
    
    def test_combat_format(self):
        """Test combat tag format compliance."""
        self.log("\n" + "="*70)
        self.log("CATEGORY: Combat Format Compliance")
        self.log("="*70)
        
        char, scenario = self.setup_game()
        context = scenario.get_dm_context()
        
        time.sleep(CATEGORY_DELAY)  # Delay between categories
        
        test_cases = [
            # Single enemy format
            ("Single Enemy Format",
             "I attack the goblin with my sword!",
             "A goblin blocks your path.",
             1),
            
            # Multiple enemy format
            ("Double Enemy Format",
             "I attack both skeletons!",
             "Two skeletons rise from the ground before you.",
             2),
            
            # Mixed enemy format
            ("Mixed Enemy Format",
             "I engage the goblin and the orc!",
             "A goblin and an orc guard the treasure chest.",
             2),
        ]
        
        for name, action, combat_context, expected_count in test_cases:
            chat = self.create_dm(char, context, combat_context)
            response = self.send_with_delay(chat, action)
            
            self.log(f"\n📋 Test: {name}")
            self.log(f"   Action: {action[:60]}...")
            self.log(f"   Response: {response[:150]}...")
            
            enemies, surprise = parse_combat_request(response)
            
            passed = True
            notes = ""
            
            # Check format
            if enemies:
                # Check correct format was used
                combat_pattern = r'\[COMBAT:\s*[^\]]+\]'
                match = re.search(combat_pattern, response, re.IGNORECASE)
                
                if match:
                    notes = f"Correct format: {match.group()}"
                    
                    # Check enemy count
                    if len(enemies) != expected_count:
                        passed = False
                        notes += f" | WRONG COUNT: got {len(enemies)}, expected {expected_count}"
                else:
                    passed = False
                    notes = "Combat found but wrong format"
            else:
                passed = False
                notes = "No combat tag found"
            
            # Check for wrong formats
            wrong_formats = [
                (r'\[FIGHT:', "Used [FIGHT: instead of [COMBAT:"),
                (r'\[BATTLE:', "Used [BATTLE: instead of [COMBAT:"),
                (r'\[ATTACK:', "Used [ATTACK: instead of [COMBAT:"),
            ]
            for pattern, desc in wrong_formats:
                if re.search(pattern, response, re.IGNORECASE):
                    passed = False
                    notes = f"WRONG FORMAT: {desc}"
                    break
            
            status = "✅ PASS" if passed else "❌ FAIL"
            self.log(f"   Result: {status} - {notes}")
            
            result = CombatTestResult(
                category="combat_format",
                test_name=name,
                player_action=action,
                dm_response=response[:500],
                expected_combat=True,
                actual_combat=len(enemies) > 0,
                expected_enemies=None,
                actual_enemies=enemies if enemies else None,
                passed=passed,
                notes=notes
            )
            self.record_result(result)
    
    # =========================================================================
    # SURPRISE MECHANIC TESTS
    # =========================================================================
    
    def test_surprise_mechanic(self):
        """Test surprise modifier handling."""
        self.log("\n" + "="*70)
        self.log("CATEGORY: Surprise Mechanic")
        self.log("="*70)
        
        char, scenario = self.setup_game()
        context = scenario.get_dm_context()
        
        time.sleep(CATEGORY_DELAY)
        
        test_cases = [
            # Player surprise (stealth attack)
            ("Stealth Attack - Should Surprise",
             "I silently creep up behind the guard and stab him!",
             "The guard is completely unaware, facing away from you.",
             True),
            
            ("Sleeping Enemy - Should Surprise",
             "I attack the sleeping goblin!",
             "A goblin sleeps soundly, snoring loudly.",
             True),
            
            ("Ambush from Hiding - Should Surprise",
             "From my hiding spot, I leap out and attack the bandit!",
             "The bandit hasn't noticed you hiding in the shadows.",
             True),
            
            # No surprise (fair fight)
            ("Face to Face - No Surprise",
             "I charge at the orc!",
             "The orc sees you and roars, readying his axe.",
             False),
            
            ("Enemy Alert - No Surprise",
             "I attack the goblin!",
             "The goblin spots you and draws its dagger.",
             False),
        ]
        
        for name, action, combat_context, should_surprise in test_cases:
            chat = self.create_dm(char, context, combat_context)
            response = self.send_with_delay(chat, action)
            
            self.log(f"\n🎯 Test: {name}")
            self.log(f"   Action: {action[:60]}...")
            self.log(f"   Response: {response[:150]}...")
            
            enemies, surprise = parse_combat_request(response)
            
            passed = True
            notes = ""
            
            if enemies:
                if should_surprise:
                    if surprise:
                        notes = "Correctly used SURPRISE modifier"
                    else:
                        # This is a soft fail - DM might interpret differently
                        notes = "Expected SURPRISE but not included (soft fail)"
                        passed = True  # Not strict fail
                else:
                    if surprise:
                        notes = "WRONG: Used SURPRISE when enemy was alert"
                        passed = False
                    else:
                        notes = "Correctly no SURPRISE"
            else:
                notes = "No combat triggered"
                passed = False
            
            status = "✅ PASS" if passed else "❌ FAIL"
            self.log(f"   Result: {status} - {notes}")
            
            result = CombatTestResult(
                category="surprise_mechanic",
                test_name=name,
                player_action=action,
                dm_response=response[:500],
                expected_combat=True,
                actual_combat=len(enemies) > 0,
                expected_surprise=should_surprise,
                actual_surprise=surprise,
                passed=passed,
                notes=notes
            )
            self.record_result(result)
    
    # =========================================================================
    # EDGE CASE TESTS
    # =========================================================================
    
    def test_edge_cases(self):
        """Test combat edge cases."""
        self.log("\n" + "="*70)
        self.log("CATEGORY: Combat Edge Cases")
        self.log("="*70)
        
        char, scenario = self.setup_game()
        context = scenario.get_dm_context()
        
        time.sleep(CATEGORY_DELAY)
        
        test_cases = [
            # Verbal vs actual attack
            ("Verbal Threat Only",
             "I threaten to attack the goblin if he doesn't leave!",
             "A goblin blocks your path.",
             False),  # Should be intimidation, not combat
            
            # Group combat
            ("Attack Group",
             "I attack all three goblins at once!",
             "Three goblins surround you.",
             True),
            
            # Ranged attack
            ("Ranged Attack",
             "I shoot an arrow at the distant wolf!",
             "A wolf prowls at the edge of the clearing.",
             True),
            
            # Unarmed attack
            ("Unarmed Strike",
             "I tackle the goblin and wrestle him to the ground!",
             "A small goblin blocks the door.",
             True),
            
            # Object attack (non-enemy)
            ("Attack Object",
             "I smash the locked door with my sword!",
             "A sturdy wooden door blocks your path.",
             False),  # Should be Athletics, not combat
            
            # Attack friendly NPC
            ("Attack Friendly",
             "I attack Gorn the barkeep!",
             "Gorn is cleaning mugs behind the bar.",
             True),  # Should trigger, but with consequences
        ]
        
        for name, action, combat_context, should_combat in test_cases:
            chat = self.create_dm(char, context, combat_context)
            response = self.send_with_delay(chat, action)
            
            self.log(f"\n🔧 Test: {name}")
            self.log(f"   Action: {action[:60]}...")
            self.log(f"   Response: {response[:150]}...")
            
            enemies, surprise = parse_combat_request(response)
            skill, dc = parse_roll_request(response)
            
            passed = True
            notes = ""
            actual_combat = len(enemies) > 0
            
            if should_combat:
                if actual_combat:
                    notes = f"Combat triggered: {enemies}"
                elif skill:
                    notes = f"DM chose skill check instead: {skill} DC {dc}"
                    # Some cases this is acceptable
                    if name == "Attack Object":
                        notes += " (acceptable)"
                    else:
                        passed = False
                else:
                    notes = "No combat or skill check triggered"
                    passed = False
            else:
                if actual_combat:
                    notes = f"FALSE POSITIVE: Combat triggered: {enemies}"
                    # For "Verbal Threat", DM might escalate to combat - soft fail
                    if name == "Verbal Threat Only":
                        notes += " (DM chose to escalate)"
                        passed = True
                    else:
                        passed = False
                elif skill:
                    notes = f"Correctly used skill check: {skill}"
                else:
                    notes = "Correctly handled without combat"
            
            status = "✅ PASS" if passed else "❌ FAIL"
            self.log(f"   Result: {status} - {notes}")
            
            result = CombatTestResult(
                category="edge_cases",
                test_name=name,
                player_action=action,
                dm_response=response[:500],
                expected_combat=should_combat,
                actual_combat=actual_combat,
                passed=passed,
                notes=notes
            )
            self.record_result(result)
    
    # =========================================================================
    # RUN ALL TESTS
    # =========================================================================
    
    def run_all_tests(self):
        """Run all combat tests."""
        self.log("\n" + "="*70, force=True)
        self.log("AI DM COMBAT MECHANICS ASSESSMENT", force=True)
        self.log(f"(API delay: {API_DELAY}s between calls)", force=True)
        self.log("="*70, force=True)
        self.log(f"Started: {self.report.timestamp}", force=True)
        
        test_methods = [
            self.test_combat_triggers,
            self.test_combat_format,
            self.test_surprise_mechanic,
            self.test_edge_cases,
        ]
        
        for method in test_methods:
            try:
                method()
            except Exception as e:
                self.log(f"\n❌ Test category crashed: {str(e)}", force=True)
            time.sleep(CATEGORY_DELAY)
        
        self.print_report()
        self.save_report()
    
    def print_report(self):
        """Print combat test report."""
        self.log("\n" + "="*70, force=True)
        self.log("COMBAT MECHANICS REPORT", force=True)
        self.log("="*70, force=True)
        
        self.log(f"\n📊 RESULTS:", force=True)
        self.log(f"   Total Tests: {self.report.total_tests}", force=True)
        self.log(f"   Passed: {self.report.passed}", force=True)
        self.log(f"   Failed: {self.report.failed}", force=True)
        self.log(f"   Pass Rate: {self.report.pass_rate:.1f}%", force=True)
        self.log(f"   API Calls: {self.report.api_calls}", force=True)
        
        # Category breakdown
        categories = {}
        for r in self.report.results:
            if r.category not in categories:
                categories[r.category] = {"total": 0, "passed": 0}
            categories[r.category]["total"] += 1
            if r.passed:
                categories[r.category]["passed"] += 1
        
        self.log(f"\n📊 BY CATEGORY:", force=True)
        for cat, data in categories.items():
            rate = (data["passed"] / data["total"] * 100) if data["total"] > 0 else 0
            status = "✅" if rate >= 80 else "⚠️" if rate >= 50 else "❌"
            self.log(f"   {status} {cat}: {data['passed']}/{data['total']} ({rate:.0f}%)", force=True)
        
        # Failures
        failures = [r for r in self.report.results if not r.passed]
        if failures:
            self.log(f"\n🔴 FAILURES ({len(failures)}):", force=True)
            for f in failures:
                self.log(f"\n   [{f.category}] {f.test_name}", force=True)
                self.log(f"   Notes: {f.notes}", force=True)
                self.log(f"   Action: {f.player_action[:60]}...", force=True)
    
    def save_report(self):
        """Save report to JSON."""
        report_data = {
            "timestamp": self.report.timestamp,
            "total_tests": self.report.total_tests,
            "passed": self.report.passed,
            "failed": self.report.failed,
            "pass_rate": self.report.pass_rate,
            "api_calls": self.report.api_calls,
            "results": [
                {
                    "category": r.category,
                    "test_name": r.test_name,
                    "expected_combat": r.expected_combat,
                    "actual_combat": r.actual_combat,
                    "expected_enemies": r.expected_enemies,
                    "actual_enemies": r.actual_enemies,
                    "passed": r.passed,
                    "notes": r.notes
                }
                for r in self.report.results
            ]
        }
        
        filepath = os.path.join(os.path.dirname(__file__), "dm_combat_report.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        
        self.log(f"\n📄 Report saved to: {filepath}", force=True)


if __name__ == "__main__":
    print("Starting AI DM Combat Mechanics Assessment...")
    print(f"Using {API_DELAY}s delay between API calls to avoid rate limiting.\n")
    
    tester = DMCombatTester(verbose=True)
    tester.run_all_tests()
