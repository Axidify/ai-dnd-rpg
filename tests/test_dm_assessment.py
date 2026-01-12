"""
AI DM Mechanics Assessment Framework
=====================================
Comprehensive testing of AI DM adherence to game mechanics.

This test measures:
1. Skill check triggering accuracy
2. Combat system compliance
3. Item/reward system usage
4. NPC/Location invention (hallucination)
5. Navigation system compliance
6. XP awarding rules
7. Format compliance for tags

Each test category calculates deviation percentage and identifies root causes.

Run with: python -m tests.test_dm_assessment
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

# Load environment before imports
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from character import Character
from scenario import ScenarioManager, create_goblin_cave_shops
from shop import ShopManager
import google.generativeai as genai

# Import DM engine functions
from dm_engine import (
    DM_SYSTEM_PROMPT,
    parse_roll_request,
    parse_combat_request,
    parse_item_rewards,
    parse_gold_rewards,
    parse_xp_rewards,
    parse_buy_transactions,
    parse_recruit_tags,
    parse_gold_costs,
    SKILL_ABILITIES,
)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class MechanicsDeviation:
    """Records a single deviation from expected game mechanics."""
    category: str  # e.g., "skill_check", "combat", "item", "npc_invention"
    description: str
    expected_behavior: str
    actual_behavior: str
    player_input: str
    dm_response: str
    severity: str  # "critical", "major", "minor"
    

@dataclass
class CategoryResult:
    """Results for a specific mechanics category."""
    category: str
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    deviations: List[MechanicsDeviation] = field(default_factory=list)
    
    @property
    def deviation_percentage(self) -> float:
        if self.tests_run == 0:
            return 0.0
        return (self.tests_failed / self.tests_run) * 100
    
    @property
    def compliance_percentage(self) -> float:
        return 100 - self.deviation_percentage


@dataclass
class AssessmentReport:
    """Complete assessment report."""
    timestamp: str = ""
    total_tests: int = 0
    total_passed: int = 0
    total_failed: int = 0
    total_api_calls: int = 0
    category_results: Dict[str, CategoryResult] = field(default_factory=dict)
    all_deviations: List[MechanicsDeviation] = field(default_factory=list)
    
    @property
    def overall_deviation_percentage(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.total_failed / self.total_tests) * 100


# =============================================================================
# DM ASSESSMENT HARNESS
# =============================================================================

class DMAssessmentHarness:
    """Comprehensive AI DM mechanics assessment."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.report = AssessmentReport(timestamp=datetime.now().isoformat())
        
        # API setup
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found! Add to .env file.")
        genai.configure(api_key=self.api_key)
        
        # Initialize category results
        categories = [
            "skill_check_trigger",
            "skill_check_format",
            "combat_trigger",
            "combat_format",
            "item_reward",
            "gold_reward",
            "xp_reward",
            "buy_transaction",
            "npc_invention",
            "location_invention",
            "navigation_compliance",
            "reroll_prevention",
        ]
        for cat in categories:
            self.report.category_results[cat] = CategoryResult(category=cat)
    
    def log(self, msg: str, force: bool = False):
        """Print if verbose or forced."""
        if self.verbose or force:
            print(msg)
    
    def setup_game_state(self) -> Tuple[Any, Any, Any, Any]:
        """Initialize game state for testing."""
        character = Character(
            name="AssessmentHero",
            race="Human",
            char_class="Fighter",
            level=3,
            strength=16,
            dexterity=14,
            constitution=14,
            intelligence=10,
            wisdom=12,
            charisma=12
        )
        character.gold = 100
        
        shop_manager = ShopManager()
        scenario_manager = ScenarioManager()
        scenario_manager.start_scenario("goblin_cave")
        create_goblin_cave_shops(shop_manager)
        
        return character, shop_manager, scenario_manager, scenario_manager.get_dm_context()
    
    def create_dm_chat(self, character, scenario_context: str):
        """Create a DM chat session."""
        # Build system prompt
        system_prompt = f"""{DM_SYSTEM_PROMPT}

CHARACTER:
- Name: {character.name}
- Race: {character.race}
- Class: {character.char_class}
- Level: {character.level}
- HP: {character.current_hp}/{character.max_hp}
- Gold: {character.gold}
- AC: {character.armor_class}

{scenario_context}

IMPORTANT: You are being assessed for mechanics compliance. Follow all rules precisely.
"""
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash-exp',
            system_instruction=system_prompt
        )
        return model.start_chat()
    
    def send_to_dm(self, chat, player_input: str, extra_context: str = "") -> str:
        """Send message to DM and get response."""
        self.report.total_api_calls += 1
        try:
            full_input = player_input
            if extra_context:
                full_input = f"{player_input}\n\n[CONTEXT: {extra_context}]"
            response = chat.send_message(full_input)
            return response.text
        except Exception as e:
            return f"[ERROR: {str(e)}]"
    
    def record_result(self, category: str, passed: bool, deviation: Optional[MechanicsDeviation] = None):
        """Record a test result."""
        self.report.total_tests += 1
        cat_result = self.report.category_results[category]
        cat_result.tests_run += 1
        
        if passed:
            self.report.total_passed += 1
            cat_result.tests_passed += 1
        else:
            self.report.total_failed += 1
            cat_result.tests_failed += 1
            if deviation:
                cat_result.deviations.append(deviation)
                self.report.all_deviations.append(deviation)
    
    # =========================================================================
    # SKILL CHECK TESTS
    # =========================================================================
    
    def test_skill_check_triggers(self):
        """Test that skill checks are triggered appropriately."""
        self.log("\n" + "="*70)
        self.log("CATEGORY: Skill Check Triggering")
        self.log("="*70)
        
        char, shop_mgr, scenario_mgr, context = self.setup_game_state()
        chat = self.create_dm_chat(char, context)
        
        # Test cases: (player_input, should_trigger_check, expected_skill_or_none)
        test_cases = [
            ("I carefully search the room for hidden objects", True, ["perception", "investigation"]),
            ("I try to convince the merchant to lower the price", True, ["persuasion", "deception"]),
            ("I sneak quietly past the guards", True, ["stealth"]),
            ("I try to climb up the wall", True, ["athletics"]),
            ("I examine the strange runes on the door", True, ["arcana", "history"]),
            ("I attempt to pick the lock on this chest", True, ["sleight_of_hand", "dexterity"]),
            ("I say hello to the barkeep", False, None),  # Simple greeting, no check needed
            ("I walk through the open door", False, None),  # Simple movement
            ("I ask what time it is", False, None),  # Simple question
        ]
        
        for player_input, should_trigger, expected_skills in test_cases:
            response = self.send_to_dm(chat, player_input)
            self.log(f"\nPlayer: {player_input}")
            self.log(f"DM: {response[:200]}...")
            
            skill, dc = parse_roll_request(response)
            triggered = skill is not None
            
            # Check if triggering matches expectation
            if should_trigger:
                if triggered:
                    # Check if correct skill
                    skill_lower = skill.lower()
                    if expected_skills and skill_lower not in [s.lower() for s in expected_skills]:
                        self.record_result("skill_check_trigger", False, MechanicsDeviation(
                            category="skill_check_trigger",
                            description=f"Wrong skill check triggered",
                            expected_behavior=f"Should trigger one of: {expected_skills}",
                            actual_behavior=f"Triggered: {skill}",
                            player_input=player_input,
                            dm_response=response[:300],
                            severity="major"
                        ))
                        self.log(f"  ❌ Wrong skill: {skill}, expected one of {expected_skills}")
                    else:
                        self.record_result("skill_check_trigger", True)
                        self.log(f"  ✅ Correctly triggered {skill} DC {dc}")
                else:
                    self.record_result("skill_check_trigger", False, MechanicsDeviation(
                        category="skill_check_trigger",
                        description="Missing skill check",
                        expected_behavior=f"Should trigger skill check ({expected_skills})",
                        actual_behavior="No skill check triggered",
                        player_input=player_input,
                        dm_response=response[:300],
                        severity="major"
                    ))
                    self.log(f"  ❌ Should have triggered check but didn't")
            else:
                if triggered:
                    # Triggered when shouldn't - minor issue (overly cautious)
                    self.record_result("skill_check_trigger", False, MechanicsDeviation(
                        category="skill_check_trigger",
                        description="Unnecessary skill check",
                        expected_behavior="No skill check needed for simple action",
                        actual_behavior=f"Triggered {skill} check",
                        player_input=player_input,
                        dm_response=response[:300],
                        severity="minor"
                    ))
                    self.log(f"  ⚠️ Unnecessarily triggered {skill} check")
                else:
                    self.record_result("skill_check_trigger", True)
                    self.log(f"  ✅ Correctly did not trigger check")
            
            time.sleep(0.5)
    
    def test_skill_check_format(self):
        """Test that skill check tags use correct format."""
        self.log("\n" + "="*70)
        self.log("CATEGORY: Skill Check Format Compliance")
        self.log("="*70)
        
        char, shop_mgr, scenario_mgr, context = self.setup_game_state()
        chat = self.create_dm_chat(char, context)
        
        # Force skill checks and verify format
        test_inputs = [
            "I carefully examine the suspicious chest for traps",
            "I try to intimidate the goblin into surrendering",
            "I attempt to balance across the narrow ledge",
        ]
        
        for player_input in test_inputs:
            response = self.send_to_dm(chat, player_input)
            self.log(f"\nPlayer: {player_input}")
            self.log(f"DM: {response[:200]}...")
            
            # Check for correct format [ROLL: Skill DC X]
            correct_pattern = r'\[ROLL:\s*\w+\s+DC\s*\d+\]'
            wrong_patterns = [
                (r'\[SKILL CHECK:', "Used [SKILL CHECK: instead of [ROLL:"),
                (r'\[DICE:', "Used [DICE: instead of [ROLL:"),
                (r'\[CHECK:', "Used [CHECK: instead of [ROLL:"),
                (r'roll a d20', "Told player to roll instead of using tag"),
                (r'make a \w+ check', "Told player to make check instead of using tag"),
            ]
            
            has_correct_format = re.search(correct_pattern, response, re.IGNORECASE) is not None
            
            if has_correct_format:
                # Also verify DC is reasonable (10-20 typically)
                skill, dc = parse_roll_request(response)
                if dc and (dc < 5 or dc > 25):
                    self.record_result("skill_check_format", False, MechanicsDeviation(
                        category="skill_check_format",
                        description=f"Unreasonable DC value: {dc}",
                        expected_behavior="DC should be between 5-25",
                        actual_behavior=f"DC was {dc}",
                        player_input=player_input,
                        dm_response=response[:300],
                        severity="minor"
                    ))
                    self.log(f"  ⚠️ DC {dc} seems unreasonable")
                else:
                    self.record_result("skill_check_format", True)
                    self.log(f"  ✅ Correct format with reasonable DC")
            else:
                # Check if wrong format used
                for pattern, desc in wrong_patterns:
                    if re.search(pattern, response, re.IGNORECASE):
                        self.record_result("skill_check_format", False, MechanicsDeviation(
                            category="skill_check_format",
                            description=desc,
                            expected_behavior="Use [ROLL: SkillName DC X] format",
                            actual_behavior=desc,
                            player_input=player_input,
                            dm_response=response[:300],
                            severity="major"
                        ))
                        self.log(f"  ❌ Wrong format: {desc}")
                        break
                else:
                    # No check triggered at all
                    self.record_result("skill_check_format", False, MechanicsDeviation(
                        category="skill_check_format",
                        description="No skill check tag used",
                        expected_behavior="Should have [ROLL: Skill DC X] tag",
                        actual_behavior="No recognizable skill check format",
                        player_input=player_input,
                        dm_response=response[:300],
                        severity="major"
                    ))
                    self.log(f"  ❌ No skill check tag found")
            
            time.sleep(0.5)
    
    # =========================================================================
    # COMBAT TESTS
    # =========================================================================
    
    def test_combat_triggers(self):
        """Test that combat is triggered correctly."""
        self.log("\n" + "="*70)
        self.log("CATEGORY: Combat Triggering")
        self.log("="*70)
        
        char, shop_mgr, scenario_mgr, context = self.setup_game_state()
        chat = self.create_dm_chat(char, context)
        
        # Test cases
        test_cases = [
            ("I draw my sword and attack the goblin!", True, ["goblin"]),
            ("I charge at the bandits with my weapon drawn!", True, ["bandit"]),
            ("I punch the orc in the face!", True, ["orc"]),
            ("I talk to the merchant about weapons", False, None),
            ("I walk through the peaceful garden", False, None),
        ]
        
        for player_input, should_trigger, expected_enemies in test_cases:
            response = self.send_to_dm(chat, player_input, "There are enemies here: goblins, bandits, orcs nearby")
            self.log(f"\nPlayer: {player_input}")
            self.log(f"DM: {response[:200]}...")
            
            enemies, surprise = parse_combat_request(response)
            triggered = len(enemies) > 0
            
            if should_trigger:
                if triggered:
                    self.record_result("combat_trigger", True)
                    self.log(f"  ✅ Combat triggered: {enemies}")
                else:
                    self.record_result("combat_trigger", False, MechanicsDeviation(
                        category="combat_trigger",
                        description="Combat not triggered for attack",
                        expected_behavior="Should trigger combat when player attacks",
                        actual_behavior="No [COMBAT:] tag found",
                        player_input=player_input,
                        dm_response=response[:300],
                        severity="critical"
                    ))
                    self.log(f"  ❌ Combat should have triggered")
            else:
                if triggered:
                    self.record_result("combat_trigger", False, MechanicsDeviation(
                        category="combat_trigger",
                        description="Unexpected combat trigger",
                        expected_behavior="No combat for peaceful action",
                        actual_behavior=f"Combat triggered: {enemies}",
                        player_input=player_input,
                        dm_response=response[:300],
                        severity="major"
                    ))
                    self.log(f"  ❌ Should not have triggered combat")
                else:
                    self.record_result("combat_trigger", True)
                    self.log(f"  ✅ Correctly no combat")
            
            time.sleep(0.5)
    
    def test_combat_format(self):
        """Test combat tag format compliance."""
        self.log("\n" + "="*70)
        self.log("CATEGORY: Combat Format Compliance")
        self.log("="*70)
        
        char, shop_mgr, scenario_mgr, context = self.setup_game_state()
        chat = self.create_dm_chat(char, context)
        
        # Test scenarios
        test_cases = [
            ("I attack the two goblins!", 2),
            ("I sneak up and attack the sleeping guard!", 1),
        ]
        
        for player_input, expected_count in test_cases:
            response = self.send_to_dm(chat, player_input, "Enemies present: 2 goblins, 1 bandit guard")
            self.log(f"\nPlayer: {player_input}")
            self.log(f"DM: {response[:200]}...")
            
            enemies, surprise = parse_combat_request(response)
            
            if enemies:
                # Check enemy count matches narration
                if len(enemies) != expected_count:
                    self.record_result("combat_format", False, MechanicsDeviation(
                        category="combat_format",
                        description=f"Enemy count mismatch",
                        expected_behavior=f"Combat tag should have {expected_count} enemies",
                        actual_behavior=f"Combat tag has {len(enemies)} enemies: {enemies}",
                        player_input=player_input,
                        dm_response=response[:300],
                        severity="major"
                    ))
                    self.log(f"  ⚠️ Enemy count: {len(enemies)}, expected {expected_count}")
                else:
                    self.record_result("combat_format", True)
                    self.log(f"  ✅ Correct format and count")
                
                # Check surprise rule for stealth attack
                if "sneak" in player_input.lower() and not surprise:
                    self.record_result("combat_format", False, MechanicsDeviation(
                        category="combat_format",
                        description="Missing SURPRISE for sneak attack",
                        expected_behavior="Sneak attack should have | SURPRISE",
                        actual_behavior="No SURPRISE modifier",
                        player_input=player_input,
                        dm_response=response[:300],
                        severity="major"
                    ))
                    self.log(f"  ⚠️ Missing SURPRISE for sneak attack")
            else:
                self.record_result("combat_format", False, MechanicsDeviation(
                    category="combat_format",
                    description="No combat tag for attack",
                    expected_behavior="Should have [COMBAT: ...] tag",
                    actual_behavior="No combat tag found",
                    player_input=player_input,
                    dm_response=response[:300],
                    severity="critical"
                ))
                self.log(f"  ❌ No combat tag found")
            
            time.sleep(0.5)
    
    # =========================================================================
    # REWARD SYSTEM TESTS
    # =========================================================================
    
    def test_item_rewards(self):
        """Test item reward compliance."""
        self.log("\n" + "="*70)
        self.log("CATEGORY: Item Reward System")
        self.log("="*70)
        
        char, shop_mgr, scenario_mgr, context = self.setup_game_state()
        chat = self.create_dm_chat(char, context)
        
        # Test loot scenario
        response = self.send_to_dm(chat, "I search the defeated goblin's body for loot", 
                                    "The goblin had a small pouch and a dagger")
        self.log(f"\nPlayer: I search the goblin's body for loot")
        self.log(f"DM: {response[:200]}...")
        
        items = parse_item_rewards(response)
        gold = parse_gold_rewards(response)
        
        # Should have some reward tags
        if items or gold > 0:
            self.record_result("item_reward", True)
            self.log(f"  ✅ Rewards given: items={items}, gold={gold}")
        else:
            # Check if DM described items but didn't use tags
            if any(word in response.lower() for word in ["dagger", "gold", "coin", "pouch", "potion"]):
                self.record_result("item_reward", False, MechanicsDeviation(
                    category="item_reward",
                    description="Items described but no tags used",
                    expected_behavior="Use [ITEM:] and [GOLD:] tags for rewards",
                    actual_behavior="Items mentioned in text but no tags",
                    player_input="Search goblin body",
                    dm_response=response[:300],
                    severity="major"
                ))
                self.log(f"  ❌ Items described but no tags used")
            else:
                self.record_result("item_reward", True)
                self.log(f"  ✅ No items to give (acceptable)")
        
        time.sleep(0.5)
    
    def test_xp_rewards(self):
        """Test XP reward compliance."""
        self.log("\n" + "="*70)
        self.log("CATEGORY: XP Reward System")
        self.log("="*70)
        
        char, shop_mgr, scenario_mgr, context = self.setup_game_state()
        chat = self.create_dm_chat(char, context)
        
        # Test non-combat XP scenario (puzzle)
        response = self.send_to_dm(chat, "I solved the ancient puzzle to open the sealed door!", 
                                    "This was a complex puzzle that took cleverness to solve")
        self.log(f"\nPlayer: I solved the ancient puzzle!")
        self.log(f"DM: {response[:200]}...")
        
        xp_rewards = parse_xp_rewards(response)
        
        if xp_rewards:
            total_xp = sum(xp for xp, _ in xp_rewards)
            if total_xp > 0 and total_xp <= 100:  # Reasonable for puzzle
                self.record_result("xp_reward", True)
                self.log(f"  ✅ XP awarded: {xp_rewards}")
            elif total_xp > 100:
                self.record_result("xp_reward", False, MechanicsDeviation(
                    category="xp_reward",
                    description=f"Excessive XP for puzzle: {total_xp}",
                    expected_behavior="25-50 XP for puzzle solving",
                    actual_behavior=f"Awarded {total_xp} XP",
                    player_input="Solved puzzle",
                    dm_response=response[:300],
                    severity="major"
                ))
                self.log(f"  ⚠️ XP seems high: {total_xp}")
        else:
            # XP might be reasonable to skip for minor achievements
            self.record_result("xp_reward", True)
            self.log(f"  ✅ No XP (acceptable for minor achievement)")
        
        # Test that combat XP is NOT manually awarded
        chat2 = self.create_dm_chat(char, context)
        response2 = self.send_to_dm(chat2, "I just defeated the goblin in combat!", 
                                     "[CONTEXT: Combat just ended, goblin defeated]")
        self.log(f"\nPlayer: I just defeated the goblin!")
        self.log(f"DM: {response2[:200]}...")
        
        xp_rewards2 = parse_xp_rewards(response2)
        if xp_rewards2:
            self.record_result("xp_reward", False, MechanicsDeviation(
                category="xp_reward",
                description="Manual XP for combat (should be automatic)",
                expected_behavior="Combat XP is automatic - DM should NOT use [XP:] tag",
                actual_behavior=f"DM awarded XP: {xp_rewards2}",
                player_input="Defeated goblin in combat",
                dm_response=response2[:300],
                severity="major"
            ))
            self.log(f"  ❌ Should not manually award combat XP")
        else:
            self.record_result("xp_reward", True)
            self.log(f"  ✅ Correctly did not award combat XP")
        
        time.sleep(0.5)
    
    def test_buy_transactions(self):
        """Test shop purchase compliance."""
        self.log("\n" + "="*70)
        self.log("CATEGORY: Buy Transaction System")
        self.log("="*70)
        
        char, shop_mgr, scenario_mgr, context = self.setup_game_state()
        chat = self.create_dm_chat(char, context)
        
        response = self.send_to_dm(chat, "I want to buy a healing potion from the merchant", 
                                    "Shop inventory: healing_potion (25g), rope (5g), torch (1g)")
        self.log(f"\nPlayer: I want to buy a healing potion")
        self.log(f"DM: {response[:200]}...")
        
        purchases = parse_buy_transactions(response)
        items_free = parse_item_rewards(response)
        
        if purchases:
            self.record_result("buy_transaction", True)
            self.log(f"  ✅ Used [BUY:] tag: {purchases}")
        elif items_free:
            # Used [ITEM:] instead of [BUY:] - common mistake!
            self.record_result("buy_transaction", False, MechanicsDeviation(
                category="buy_transaction",
                description="Used [ITEM:] instead of [BUY:] for purchase",
                expected_behavior="Use [BUY: item, price] for shop purchases",
                actual_behavior=f"Used [ITEM:] which gives item free",
                player_input="Buy healing potion",
                dm_response=response[:300],
                severity="critical"
            ))
            self.log(f"  ❌ Used [ITEM:] instead of [BUY:] - gives item free!")
        else:
            self.record_result("buy_transaction", False, MechanicsDeviation(
                category="buy_transaction",
                description="No transaction tag for purchase",
                expected_behavior="Should use [BUY: item, price] tag",
                actual_behavior="No purchase tag found",
                player_input="Buy healing potion",
                dm_response=response[:300],
                severity="major"
            ))
            self.log(f"  ❌ No purchase tag found")
        
        time.sleep(0.5)
    
    # =========================================================================
    # HALLUCINATION TESTS
    # =========================================================================
    
    def test_npc_invention(self):
        """Test that DM doesn't invent NPCs not in context."""
        self.log("\n" + "="*70)
        self.log("CATEGORY: NPC Invention (Hallucination)")
        self.log("="*70)
        
        char, shop_mgr, scenario_mgr, context = self.setup_game_state()
        chat = self.create_dm_chat(char, context)
        
        # Ask about a made-up NPC
        response = self.send_to_dm(chat, "Where can I find Zarnok the Wise?", 
                                    "KNOWN NPCs: Gorn (barkeep), Mira (merchant)")
        self.log(f"\nPlayer: Where can I find Zarnok the Wise?")
        self.log(f"DM: {response[:250]}...")
        
        # Check if DM invented details about Zarnok
        invented_indicators = [
            "zarnok lives",
            "zarnok can be found",
            "you'll find zarnok",
            "zarnok's house",
            "zarnok is in",
            "head to see zarnok",
        ]
        
        invented = any(ind in response.lower() for ind in invented_indicators)
        correct_response = any(phrase in response.lower() for phrase in 
                               ["don't know", "never heard", "not familiar", "no one by that name",
                                "haven't heard of", "unknown"])
        
        if invented:
            self.record_result("npc_invention", False, MechanicsDeviation(
                category="npc_invention",
                description="DM invented NPC not in context",
                expected_behavior="Should say NPC is unknown",
                actual_behavior="Gave details about made-up NPC",
                player_input="Where is Zarnok the Wise?",
                dm_response=response[:300],
                severity="critical"
            ))
            self.log(f"  ❌ HALLUCINATION: Invented details about Zarnok!")
        elif correct_response:
            self.record_result("npc_invention", True)
            self.log(f"  ✅ Correctly stated NPC is unknown")
        else:
            # Ambiguous response
            self.record_result("npc_invention", True)  # Benefit of doubt
            self.log(f"  ✅ Did not invent NPC (response ambiguous)")
        
        time.sleep(0.5)
    
    def test_location_invention(self):
        """Test that DM doesn't invent locations not in context."""
        self.log("\n" + "="*70)
        self.log("CATEGORY: Location Invention (Hallucination)")
        self.log("="*70)
        
        char, shop_mgr, scenario_mgr, context = self.setup_game_state()
        chat = self.create_dm_chat(char, context)
        
        # Ask about a made-up location
        response = self.send_to_dm(chat, "How do I get to the Temple of the Silver Moon?", 
                                    "KNOWN LOCATIONS: Tavern (here), Blacksmith (east), Forest (north)")
        self.log(f"\nPlayer: How do I get to the Temple of the Silver Moon?")
        self.log(f"DM: {response[:250]}...")
        
        # Check for invented directions
        invented_indicators = [
            "temple is located",
            "temple lies",
            "head north to the temple",
            "the temple can be found",
            "to reach the temple",
            "follow the path to the temple",
        ]
        
        invented = any(ind in response.lower() for ind in invented_indicators)
        
        if invented:
            self.record_result("location_invention", False, MechanicsDeviation(
                category="location_invention",
                description="DM invented location not in context",
                expected_behavior="Should say location is unknown",
                actual_behavior="Gave directions to made-up location",
                player_input="How to get to Temple of Silver Moon?",
                dm_response=response[:300],
                severity="critical"
            ))
            self.log(f"  ❌ HALLUCINATION: Invented directions to location!")
        else:
            self.record_result("location_invention", True)
            self.log(f"  ✅ Did not invent location")
        
        time.sleep(0.5)
    
    # =========================================================================
    # NAVIGATION TESTS
    # =========================================================================
    
    def test_navigation_compliance(self):
        """Test that DM doesn't auto-transport player."""
        self.log("\n" + "="*70)
        self.log("CATEGORY: Navigation Compliance")
        self.log("="*70)
        
        char, shop_mgr, scenario_mgr, context = self.setup_game_state()
        chat = self.create_dm_chat(char, context)
        
        response = self.send_to_dm(chat, "I want to go to the forest", 
                                    "Current location: Village Square. Forest is to the north. Use 'go north' to travel.")
        self.log(f"\nPlayer: I want to go to the forest")
        self.log(f"DM: {response[:250]}...")
        
        # Check if DM auto-transported player
        auto_transport = any(phrase in response.lower() for phrase in [
            "you arrive at the forest",
            "you enter the forest",
            "you reach the forest",
            "arriving at the forest",
            "you find yourself in the forest",
        ])
        
        proper_direction = any(phrase in response.lower() for phrase in [
            "go north",
            "head north",
            "north to reach",
            "lies to the north",
            "travel north",
        ])
        
        if auto_transport and not proper_direction:
            self.record_result("navigation_compliance", False, MechanicsDeviation(
                category="navigation_compliance",
                description="DM auto-transported player",
                expected_behavior="Should tell player to use 'go north'",
                actual_behavior="Auto-transported player to location",
                player_input="I want to go to the forest",
                dm_response=response[:300],
                severity="critical"
            ))
            self.log(f"  ❌ Auto-transported player instead of giving directions")
        else:
            self.record_result("navigation_compliance", True)
            self.log(f"  ✅ Properly gave directions without auto-transport")
        
        time.sleep(0.5)
    
    # =========================================================================
    # REROLL PREVENTION
    # =========================================================================
    
    def test_reroll_prevention(self):
        """Test that DM prevents immediate rerolls after failure."""
        self.log("\n" + "="*70)
        self.log("CATEGORY: Reroll Prevention")
        self.log("="*70)
        
        char, shop_mgr, scenario_mgr, context = self.setup_game_state()
        chat = self.create_dm_chat(char, context)
        
        # First attempt - search
        response1 = self.send_to_dm(chat, "I search the room carefully")
        self.log(f"\nPlayer: I search the room carefully")
        self.log(f"DM: {response1[:150]}...")
        
        # Send failure result
        response2 = self.send_to_dm(chat, "[ROLL RESULT: Perception = 6 vs DC 15 = FAILURE]")
        self.log(f"Roll Result: FAILURE")
        self.log(f"DM: {response2[:150]}...")
        
        # Try to immediately re-search
        response3 = self.send_to_dm(chat, "I search the room again, more carefully this time")
        self.log(f"\nPlayer: I search the room again, more carefully this time")
        self.log(f"DM: {response3[:250]}...")
        
        # Check if DM allowed a reroll
        skill, dc = parse_roll_request(response3)
        
        if skill:
            # DM allowed reroll - deviation
            self.record_result("reroll_prevention", False, MechanicsDeviation(
                category="reroll_prevention",
                description="Allowed immediate reroll after failure",
                expected_behavior="Should deny reroll without changed circumstances",
                actual_behavior=f"Triggered another {skill} check",
                player_input="Search again after failure",
                dm_response=response3[:300],
                severity="major"
            ))
            self.log(f"  ❌ Allowed reroll: {skill} DC {dc}")
        else:
            # Check if DM properly denied
            denied_indicators = ["already searched", "already checked", "nothing more", 
                                "same result", "thorough", "can't find anything"]
            properly_denied = any(ind in response3.lower() for ind in denied_indicators)
            
            if properly_denied:
                self.record_result("reroll_prevention", True)
                self.log(f"  ✅ Properly denied reroll attempt")
            else:
                # Ambiguous but no reroll
                self.record_result("reroll_prevention", True)
                self.log(f"  ✅ Did not allow reroll")
        
        time.sleep(0.5)
    
    # =========================================================================
    # RUN ALL TESTS
    # =========================================================================
    
    def run_all_tests(self):
        """Run the complete assessment."""
        self.log("\n" + "="*70, force=True)
        self.log("AI DM MECHANICS ASSESSMENT", force=True)
        self.log("="*70, force=True)
        self.log(f"Started: {self.report.timestamp}", force=True)
        
        test_methods = [
            self.test_skill_check_triggers,
            self.test_skill_check_format,
            self.test_combat_triggers,
            self.test_combat_format,
            self.test_item_rewards,
            self.test_xp_rewards,
            self.test_buy_transactions,
            self.test_npc_invention,
            self.test_location_invention,
            self.test_navigation_compliance,
            self.test_reroll_prevention,
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log(f"\n❌ Test crashed: {str(e)}", force=True)
            time.sleep(1)  # Rate limiting between test categories
        
        self.print_report()
        self.save_report()
    
    def print_report(self):
        """Print the assessment report."""
        self.log("\n" + "="*70, force=True)
        self.log("ASSESSMENT REPORT", force=True)
        self.log("="*70, force=True)
        
        self.log(f"\nOVERALL RESULTS:", force=True)
        self.log(f"  Total Tests: {self.report.total_tests}", force=True)
        self.log(f"  Passed: {self.report.total_passed}", force=True)
        self.log(f"  Failed: {self.report.total_failed}", force=True)
        self.log(f"  API Calls: {self.report.total_api_calls}", force=True)
        self.log(f"\n  📊 OVERALL DEVIATION: {self.report.overall_deviation_percentage:.1f}%", force=True)
        self.log(f"  📊 OVERALL COMPLIANCE: {100 - self.report.overall_deviation_percentage:.1f}%", force=True)
        
        self.log(f"\nCATEGORY BREAKDOWN:", force=True)
        self.log("-"*70, force=True)
        
        for cat_name, cat_result in self.report.category_results.items():
            if cat_result.tests_run > 0:
                status = "✅" if cat_result.deviation_percentage == 0 else "⚠️" if cat_result.deviation_percentage < 50 else "❌"
                self.log(f"  {status} {cat_name}:", force=True)
                self.log(f"      Tests: {cat_result.tests_run} | Passed: {cat_result.tests_passed} | Failed: {cat_result.tests_failed}", force=True)
                self.log(f"      Deviation: {cat_result.deviation_percentage:.1f}% | Compliance: {cat_result.compliance_percentage:.1f}%", force=True)
        
        if self.report.all_deviations:
            self.log(f"\nDEVIATIONS FOUND ({len(self.report.all_deviations)}):", force=True)
            self.log("-"*70, force=True)
            
            # Group by severity
            critical = [d for d in self.report.all_deviations if d.severity == "critical"]
            major = [d for d in self.report.all_deviations if d.severity == "major"]
            minor = [d for d in self.report.all_deviations if d.severity == "minor"]
            
            if critical:
                self.log(f"\n🔴 CRITICAL ({len(critical)}):", force=True)
                for d in critical:
                    self.log(f"  [{d.category}] {d.description}", force=True)
                    self.log(f"    Expected: {d.expected_behavior}", force=True)
                    self.log(f"    Actual: {d.actual_behavior}", force=True)
            
            if major:
                self.log(f"\n🟠 MAJOR ({len(major)}):", force=True)
                for d in major:
                    self.log(f"  [{d.category}] {d.description}", force=True)
                    self.log(f"    Expected: {d.expected_behavior}", force=True)
            
            if minor:
                self.log(f"\n🟡 MINOR ({len(minor)}):", force=True)
                for d in minor:
                    self.log(f"  [{d.category}] {d.description}", force=True)
        
        # Root cause analysis
        self.log(f"\nROOT CAUSE ANALYSIS:", force=True)
        self.log("-"*70, force=True)
        
        cause_counts = {}
        for d in self.report.all_deviations:
            cause = self._identify_root_cause(d)
            cause_counts[cause] = cause_counts.get(cause, 0) + 1
        
        if cause_counts:
            for cause, count in sorted(cause_counts.items(), key=lambda x: -x[1]):
                self.log(f"  • {cause}: {count} occurrence(s)", force=True)
        else:
            self.log("  No deviations to analyze!", force=True)
    
    def _identify_root_cause(self, deviation: MechanicsDeviation) -> str:
        """Identify likely root cause of a deviation."""
        desc = deviation.description.lower()
        
        if "hallucination" in deviation.category or "invention" in deviation.category:
            return "Context Ignorance - AI ignoring provided context limits"
        elif "format" in deviation.category:
            return "Format Non-Compliance - AI using wrong tag format"
        elif "trigger" in deviation.category and "missing" in desc:
            return "Under-Triggering - AI not recognizing when mechanics apply"
        elif "trigger" in deviation.category and "unnecessary" in desc:
            return "Over-Triggering - AI applying mechanics when not needed"
        elif "reroll" in deviation.category:
            return "Rule Amnesia - AI forgetting previous interactions"
        elif "navigation" in deviation.category:
            return "Overreach - AI taking actions reserved for game system"
        elif "combat xp" in desc.lower():
            return "Rule Confusion - AI confused about automatic vs manual mechanics"
        elif "[item:]" in desc.lower() and "buy" in desc.lower():
            return "Tag Confusion - AI using wrong tag type"
        else:
            return "Other - Unclassified deviation"
    
    def save_report(self):
        """Save report to file."""
        report_data = {
            "timestamp": self.report.timestamp,
            "overall": {
                "total_tests": self.report.total_tests,
                "passed": self.report.total_passed,
                "failed": self.report.total_failed,
                "api_calls": self.report.total_api_calls,
                "deviation_percentage": self.report.overall_deviation_percentage,
                "compliance_percentage": 100 - self.report.overall_deviation_percentage,
            },
            "categories": {},
            "deviations": []
        }
        
        for cat_name, cat_result in self.report.category_results.items():
            if cat_result.tests_run > 0:
                report_data["categories"][cat_name] = {
                    "tests_run": cat_result.tests_run,
                    "passed": cat_result.tests_passed,
                    "failed": cat_result.tests_failed,
                    "deviation_percentage": cat_result.deviation_percentage,
                }
        
        for d in self.report.all_deviations:
            report_data["deviations"].append({
                "category": d.category,
                "severity": d.severity,
                "description": d.description,
                "expected": d.expected_behavior,
                "actual": d.actual_behavior,
                "root_cause": self._identify_root_cause(d),
            })
        
        filepath = os.path.join(os.path.dirname(__file__), "dm_assessment_report.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        
        self.log(f"\n📄 Report saved to: {filepath}", force=True)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("Starting AI DM Mechanics Assessment...")
    print("This will make multiple API calls to test the DM's mechanics compliance.\n")
    
    harness = DMAssessmentHarness(verbose=True)
    harness.run_all_tests()
