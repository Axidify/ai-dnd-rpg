"""
SCENARIO TEMPLATE
=================
Copy this file to src/ and modify to create a new scenario.
Replace all UPPERCASE placeholders with your content.

File: docs/SCENARIO_TEMPLATE.py
Usage: Copy to src/my_scenario.py, modify, then register in ScenarioManager
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from scenario import (
    Location, LocationEvent, EventTrigger, LocationAtmosphere,
    Scene, SceneStatus, Scenario, LocationManager
)
from npc import NPC, NPCRole, NPCManager, Personality
from quest import (
    Quest, QuestType, QuestManager,
    create_kill_objective, create_find_objective,
    create_talk_objective, create_location_objective
)


def create_YOUR_SCENARIO_NAME() -> Scenario:
    """
    Factory function to create your scenario.
    
    Replace YOUR_SCENARIO_NAME with your scenario ID (e.g., create_haunted_manor)
    This function will be registered with ScenarioManager.
    """
    
    # =========================================================================
    # STEP 1: DEFINE ALL LOCATIONS
    # =========================================================================
    # Each location is a physical place players can visit.
    # Define them all here first, then reference by ID in scenes.
    
    locations = {
        # -----------------------------------------------------------------
        # SCENE 1 LOCATIONS (starting area)
        # -----------------------------------------------------------------
        "starting_location": Location(
            id="starting_location",
            name="YOUR_STARTING_LOCATION_NAME",  # Display name
            description="DESCRIBE_THIS_LOCATION_FOR_AI_DM",
            
            # Exits: Map direction names to destination location IDs
            exits={
                "north": "second_location",
                "door": "second_location",  # Can have multiple names for same exit
            },
            
            # NPCs present (by ID, for AI DM context)
            npcs=["npc_name"],
            
            # Items that can be picked up (inventory item IDs)
            items=["healing_potion", "torch"],
            
            # AI guidance
            atmosphere="DESCRIBE_ATMOSPHERE_MOOD_SENSORY_DETAILS",
            enter_text="TEXT_SHOWN_FIRST_TIME_ENTERING",
            
            # Events (optional) - things that happen at this location
            events=[
                LocationEvent(
                    id="unique_event_id",
                    trigger=EventTrigger.ON_FIRST_VISIT,  # or ON_ENTER, ON_LOOK
                    narration="HINT_FOR_AI_DM_TO_DESCRIBE",
                    effect=None,  # Optional: "damage:1d4", "add_item:key"
                    one_time=True  # Only triggers once
                )
            ],
            
            # Combat encounter (optional) - Phase 3.2.2
            # List exact enemy types for balanced difficulty
            encounter=[],  # e.g., ["goblin", "goblin"] for 2 goblins
        ),
        
        "second_location": Location(
            id="second_location",
            name="YOUR_SECOND_LOCATION_NAME",
            description="DESCRIBE_THIS_LOCATION",
            exits={"back": "starting_location", "forward": "combat_location"},
            npcs=[],
            items=[],
            atmosphere="ATMOSPHERE_DESCRIPTION",
            enter_text="FIRST_ENTRY_TEXT",
        ),
        
        # -----------------------------------------------------------------
        # COMBAT LOCATION EXAMPLE
        # -----------------------------------------------------------------
        "combat_location": Location(
            id="combat_location",
            name="Dangerous Room",
            description="A room where enemies lurk. DESCRIBE ENEMIES AND ENVIRONMENT.",
            exits={"retreat": "second_location", "forward": "boss_room"},
            npcs=["enemies"],  # AI DM context
            items=["loot_after_combat"],
            atmosphere="Tense, dangerous, enemies watching",
            enter_text="You enter a dangerous area. Enemies block your path!",
            
            # Phase 3.2.2: FIXED ENCOUNTER
            # List EXACT enemy types - no more, no less
            # This ensures balanced difficulty
            encounter=["goblin", "goblin", "goblin"],  # Exactly 3 goblins
        ),
        
        # -----------------------------------------------------------------
        # BOSS LOCATION EXAMPLE
        # -----------------------------------------------------------------
        "boss_room": Location(
            id="boss_room",
            name="Boss Lair",
            description="The final confrontation. DESCRIBE BOSS AND LAIR.",
            exits={"escape": "combat_location"},
            npcs=["boss_name"],
            items=["boss_loot", "healing_potion"],
            atmosphere="Menacing, climactic, boss presence",
            enter_text="The boss turns to face you!",
            
            # Boss fight: boss + minions
            encounter=["goblin_boss", "goblin", "goblin"],  # Boss + 2 bodyguards
            
            events=[
                LocationEvent(
                    id="boss_confrontation",
                    trigger=EventTrigger.ON_FIRST_VISIT,
                    narration="The boss rises with a thunderous roar!",
                    effect=None,
                    one_time=True
                )
            ]
        ),
        
        # -----------------------------------------------------------------
        # RESOLUTION LOCATIONS
        # -----------------------------------------------------------------
        "ending_location": Location(
            id="ending_location",
            name="Victory Location",
            description="Where the scenario ends. DESCRIBE VICTORY STATE.",
            exits={},  # No exits = scenario end
            npcs=["rescued_npc", "grateful_villagers"],
            items=[],
            atmosphere="Triumphant, celebratory",
            enter_text="You have completed your quest!",
        ),
    }
    
    # =========================================================================
    # STEP 2: DEFINE SCENES (story chapters)
    # =========================================================================
    # Scenes group locations together and provide AI DM guidance.
    # Players progress through scenes in order.
    
    scenes = {
        # -----------------------------------------------------------------
        # SCENE 1: Opening/Introduction
        # -----------------------------------------------------------------
        "intro_scene": Scene(
            id="intro_scene",
            name="YOUR_INTRO_SCENE_NAME",
            description="Brief description for logs/debugging",
            
            # AI DM Guidance
            setting="PHYSICAL_SETTING_DESCRIPTION",
            mood="welcoming, mysterious, tense, etc.",
            
            # IMPORTANT: Detailed instructions for AI DM
            dm_instructions="""
WRITE DETAILED GUIDANCE FOR THE AI DM HERE.
- What NPCs should say and do
- What information to reveal
- How to respond to player actions
- When to transition to next scene

OBJECTIVES (tell DM what player must do):
1. meet_quest_giver - Player meets the NPC who gives the quest
2. accept_quest - Player agrees to help

LOCATION NOTES:
- Player starts at: starting_location
- Can explore: starting_location, second_location
- Transition trigger: Player accepts the quest
""",
            
            # Pacing
            min_exchanges=2,  # Minimum actions before can transition
            
            # Objectives (what player must do in this scene)
            objectives=["meet_quest_giver", "accept_quest"],
            
            # Phase 3.2.2: XP rewards for objectives
            objective_xp={
                "meet_quest_giver": 10,  # Small reward for meeting NPC
                "accept_quest": 15,       # Reward for accepting quest
            },
            
            # Transition
            transition_hint="Player accepts the quest",
            next_scene_id="combat_scene",  # ID of next scene
            
            # Locations available in this scene
            location_ids=["starting_location", "second_location"],
            starting_location_id="starting_location",
            
            # Status (always start LOCKED, code will set to ACTIVE)
            status=SceneStatus.LOCKED,
        ),
        
        # -----------------------------------------------------------------
        # SCENE 2: Combat/Challenge Scene
        # -----------------------------------------------------------------
        "combat_scene": Scene(
            id="combat_scene",
            name="The Dangerous Area",
            description="Combat challenges",
            setting="COMBAT_AREA_DESCRIPTION",
            mood="tense, dangerous",
            dm_instructions="""
Player enters the dangerous area. Combat awaits.

⚠️ FIXED ENCOUNTERS - Use EXACTLY the enemies defined:
- combat_location: 3 goblins → [COMBAT: goblin, goblin, goblin]
- boss_room: 1 boss + 2 goblins → [COMBAT: goblin_boss, goblin, goblin]

Do NOT vary enemy counts. This ensures fair difficulty.

After victory, describe loot and guide player forward.

COMBAT XP IS AUTOMATIC - Do NOT award XP for defeating enemies.
The game automatically awards XP based on enemy types.
""",
            min_exchanges=1,
            objectives=["defeat_boss"],
            objective_xp={"defeat_boss": 50},
            transition_hint="Player defeats the boss",
            next_scene_id="resolution_scene",
            location_ids=["combat_location", "boss_room"],
            starting_location_id="combat_location",
            status=SceneStatus.LOCKED,
        ),
        
        # -----------------------------------------------------------------
        # SCENE 3: Resolution/Ending
        # -----------------------------------------------------------------
        "resolution_scene": Scene(
            id="resolution_scene",
            name="Victory!",
            description="Quest complete, wrap up story",
            setting="VICTORY_SETTING",
            mood="triumphant, relieved",
            dm_instructions="""
The quest is complete! Celebrate the player's victory.
- Describe the aftermath
- NPCs thank the player
- Hint at future adventures
- Award any final rewards

This is the final scene. When player is ready, describe the satisfying conclusion.
""",
            min_exchanges=1,
            objectives=[],  # No objectives for ending
            objective_xp={},
            transition_hint=None,  # No transition, this is the end
            next_scene_id=None,    # None = scenario complete
            location_ids=["ending_location"],
            starting_location_id="ending_location",
            status=SceneStatus.LOCKED,
        ),
    }
    
    # =========================================================================
    # STEP 3: CREATE LOCATION MANAGER
    # =========================================================================
    location_manager = LocationManager()
    for location in locations.values():
        location_manager.add_location(location)
    
    # =========================================================================
    # STEP 4: CREATE NPCs
    # =========================================================================
    npc_manager = NPCManager()
    
    # Quest Giver NPC
    quest_giver = NPC(
        id="quest_giver",
        name="YOUR_NPC_NAME",
        description="PHYSICAL_DESCRIPTION_AND_PERSONALITY",
        role=NPCRole.QUEST_GIVER,  # MERCHANT, INFO, HOSTILE, RECRUITABLE, NEUTRAL
        location_id="starting_location",  # Where NPC is found
        dialogue={
            "greeting": "WHAT_NPC_SAYS_WHEN_PLAYER_TALKS",
            "about_quest": "INFORMATION_ABOUT_THE_QUEST",
            "farewell": "GOODBYE_MESSAGE"
        },
        disposition=50,  # Starting relationship (-100 to 100)
        personality=Personality(
            traits=["brave", "honest", "worried"],
            speech_style="formal and respectful",
            motivations=["protect family", "reward adventurers"],
            fears=["monsters", "losing loved ones"]
        )
    )
    npc_manager.add_npc(quest_giver)
    
    # Merchant NPC (inside a shop location)
    merchant = NPC(
        id="shop_merchant",
        name="YOUR_MERCHANT_NAME",
        description="MERCHANT_DESCRIPTION",
        role=NPCRole.MERCHANT,
        location_id="shop_location",  # Must be a separate shop location!
        dialogue={
            "greeting": "Welcome! Browse my wares.",
            "haggle_accept": "Fine, you drive a hard bargain.",
            "haggle_reject": "My prices are already fair."
        },
        disposition=40,
        shop_inventory={
            "healing_potion": 5,
            "torch": 10,
            "dagger": 3
        },
        merchant_markup=1.1  # 10% markup
    )
    npc_manager.add_npc(merchant)
    
    # =========================================================================
    # STEP 5: CREATE QUESTS
    # =========================================================================
    quest_manager = QuestManager()
    
    # Main Quest
    main_quest = Quest(
        id="main_quest",
        name="YOUR_MAIN_QUEST_NAME",
        description="WHAT_THE_PLAYER_MUST_DO",
        giver_npc_id="quest_giver",
        quest_type=QuestType.MAIN,  # +25 disposition on complete
        objectives=[
            create_location_objective("reach_destination", "Reach the destination", "boss_room"),
            create_kill_objective("defeat_boss", "Defeat the boss", "goblin_boss", count=1),
            create_location_objective("return_home", "Return home", "ending_location")
        ],
        rewards={
            "xp": 100,
            "gold": 50,
            "items": ["healing_potion"]
        }
    )
    quest_manager.register_quest(main_quest)
    
    # Side Quest (optional)
    side_quest = Quest(
        id="side_quest",
        name="Optional Side Quest",
        description="SIDE_QUEST_DESCRIPTION",
        giver_npc_id="quest_giver",
        quest_type=QuestType.SIDE,  # +15 disposition on complete
        objectives=[
            create_find_objective("find_item", "Find the lost item", "lost_item")
        ],
        rewards={
            "xp": 50,
            "gold": 25
        },
        prerequisites=["main_quest"]  # Must accept main quest first
    )
    quest_manager.register_quest(side_quest)
    
    # =========================================================================
    # STEP 6: CREATE AND RETURN SCENARIO
    # =========================================================================
    scenario = Scenario(
        id="your_scenario_id",  # Unique ID for this scenario
        name="Your Scenario Display Name",
        description="Brief description shown in scenario selection",
        hook="The exciting opening premise that draws players in...",
        estimated_duration="15-30 minutes",  # Estimated play time
        
        scenes=scenes,
        scene_order=["intro_scene", "combat_scene", "resolution_scene"],
        location_manager=location_manager,
        npc_manager=npc_manager,
        quest_manager=quest_manager,
    )
    
    return scenario


# =============================================================================
# STEP 7: REGISTER WITH SCENARIO MANAGER
# =============================================================================
# Add this to scenario.py's create_scenario_manager() function:
#
# from my_scenario import create_YOUR_SCENARIO_NAME
# manager.register_scenario("your_scenario_id", create_YOUR_SCENARIO_NAME)
#
# =============================================================================


# =============================================================================
# QUICK REFERENCE
# =============================================================================
"""
ENEMY TYPES (from combat.py):
- goblin (HP: 5, XP: 25, Gold: 3)
- goblin_boss (HP: 21, XP: 100, Gold: 20, Loot: healing_potion + class weapon)
- skeleton (HP: 13, XP: 25, Gold: 0)
- orc (HP: 15, XP: 50, Gold: 10)
- wolf (HP: 8, XP: 30, Gold: 0)

NPC ROLES:
- NPCRole.QUEST_GIVER - Gives and receives quests
- NPCRole.MERCHANT - Has shop inventory, can buy/sell
- NPCRole.INFO - Provides information
- NPCRole.HOSTILE - Hostile NPC
- NPCRole.RECRUITABLE - Can join player party
- NPCRole.NEUTRAL - Background NPC

QUEST TYPES:
- QuestType.MAIN - Main story (+25 disposition on complete)
- QuestType.SIDE - Side quest (+15 disposition on complete)
- QuestType.MINOR - Fetch quest (+10 disposition on complete)

OBJECTIVE FACTORIES:
- create_kill_objective(id, desc, enemy_id, count=1)
- create_find_objective(id, desc, item_id)
- create_talk_objective(id, desc, npc_id)
- create_location_objective(id, desc, location_id)
- create_collect_objective(id, desc, item_id, count)

EVENT TRIGGERS:
- EventTrigger.ON_ENTER - Every time player enters location
- EventTrigger.ON_FIRST_VISIT - Only first time entering
- EventTrigger.ON_LOOK - When player uses 'look' command
- EventTrigger.ON_ITEM_TAKE - When player takes a specific item

EVENT EFFECTS (optional):
- "damage:1d4" - Deal damage to player
- "add_item:key" - Add item to inventory
- "objective:rescue_npc" - Mark objective complete
- "skill_check:dex:12|damage:1d4" - Skill check or take damage

LOCATION ATMOSPHERE (for stealth/perception DCs):
- LocationAtmosphere(
      threat_level="threatening",  # none, uneasy, threatening, deadly
      stealth_dc=14,               # Difficulty for stealth approach
      perception_dc=12             # Difficulty for cautious approach
  )

ITEM IDs (from inventory.py):
- healing_potion, greater_healing_potion
- dagger, shortsword, longsword, greataxe, mace, quarterstaff
- shortbow, longbow
- torch, rations, lockpicks
- leather_armor, chain_mail, plate_armor

BALANCE GUIDELINES:
- Level 1 players have ~10 HP
- 4 goblins = challenging but fair (100 XP)
- Boss + 1 minion = hard fight (125 XP)
- Players should reach Level 2 (~100 XP) before boss
- Total scenario XP should be 200-300 for short scenarios

IMPORTANT - SHOP LOCATIONS:
- Merchants should be in SEPARATE shop locations
- Village Square should have an EXIT to the shop
- Don't put merchants directly in public areas
- Example: village_square → blacksmith_shop (with Gavin inside)

VARIABLE NAMING (in game.py main loop):
- Use `location_manager` and `npc_manager` (full names)
- Don't re-extract from scenario_manager in each block
- Function parameters can use `loc_mgr`/`npc_mgr` for brevity
"""
