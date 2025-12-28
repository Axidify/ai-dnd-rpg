# AI D&D Text RPG - Development Plan

**Project:** Text-based D&D RPG with AI Dungeon Master  
**Status:** Phase 5 - Backend API & Community Modding (IN PROGRESS)  
**Architecture:** API-First (dm_engine.py → api_server.py → React/Flutter/Godot)  
**Methodology:** Core-First Development (Build → Test → Expose → Display)  
**Created:** December 15, 2025  
**Last Updated:** December 26, 2025  

---

## Project Overview

A text-based role-playing game where an AI acts as the Dungeon Master, narrating adventures, managing encounters, and responding to player actions in real-time. 

**Target Platforms:** React Web, Flutter Mobile, Godot Game Client  
**Architecture:** API-first design using `dm_engine.py` → `api_server.py` → Frontend clients  
**Legacy:** Terminal version (`game.py`) archived in `backup/legacy/`

---

## Development Phases

### Phase 1: Core Foundation ✅ Complete
**Goal:** Get a working conversation loop with basic game state

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 1.1 | Simple Chat Loop | ~~Python script~~ API endpoint with AI response | ✅ Complete |
| 1.2 | Basic Character Sheet | Name, class, HP, stats (STR, DEX, CON, INT, WIS, CHA) | ✅ Complete |
| 1.3 | Starting Scenario | Scene system with structured adventure | ✅ Complete |

**Success Criteria:**
- [x] Player can chat with AI DM
- [x] Player has a character with viewable stats
- [x] Player can take basic actions (look, move, talk)
- [x] Structured adventure with scene progression

---

### Phase 2: Core Game Mechanics ✅ Complete
**Goal:** Add actual D&D gameplay rules

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 2.1 | Dice Rolling System | d4, d6, d8, d10, d12, d20 with modifiers | ✅ Complete |
| 2.2 | Skill Checks | AI requests rolls, player rolls, outcome affects story | ✅ Complete |
| 2.3 | Combat System | Turn-based, HP tracking, attack/defend/flee actions | ✅ Complete |
| 2.4 | Combat Integration | Integrate combat into main game with AI triggers | ✅ Complete |
| 2.5 | Inventory System | Pick up items, use items, equip gear | ✅ Complete |
| 2.5.1 | Multi-Enemy Combat | Fight multiple enemies with proper turn order | ✅ Complete |
| 2.5.2 | Surprise & Advantage | Ambush attacks with surprise round and advantage | ✅ Complete |
| 2.6 | Leveling System | Simplified XP/milestone progression (cap at level 5) | ✅ Complete |
| 2.7 | Rest & Hit Dice | Short rest healing with limited Hit Dice resource | ✅ Complete |

**Success Criteria:**
- [x] Player can roll dice with proper modifiers
- [x] Skill checks affect story outcomes
- [x] Player can fight an enemy and win/lose
- [x] Combat works seamlessly in main game
- [x] Player can collect and use items
- [x] Player can fight multiple enemies simultaneously
- [x] Player can ambush enemies with surprise round
- [x] Player can level up and gain abilities

**Leveling System Features (2.6):**
```
- Level cap: 5
- XP Thresholds: 0 → 100 → 300 → 600 → 1000
- Commands: 'xp' (view progress), 'levelup' (advance)
- XP Sources (ALL SYSTEM-CONTROLLED):
  • Combat XP: Automatic per enemy (goblin=25, boss=100)
  • Objective XP: Automatic per scene objective (accept_quest=15)
  • Quest XP: Automatic on quest completion (main=100, side=50-75)
  • AI XP: RARE - only for exceptional roleplay (puzzles, creative solutions)
- Milestone XP: minor=25, major=50, boss=100, adventure=150
- Benefits: +2 HP/level, stat boosts at L2/L4, abilities at L3/L5
- Proficiency bonus: +2 (L1-4), +3 (L5)
```

**Multi-Enemy Combat Features (2.5.1):**
```
- DM triggers with [COMBAT: enemy1, enemy2, enemy3]
- All enemies roll initiative individually
- Proper D&D turn order (sorted by initiative)
```

**Surprise & Advantage Features (2.5.2):**
```
- DM triggers with [COMBAT: enemy1, enemy2 | SURPRISE]
- Surprised enemies skip their turn in Round 1
- Player gets ADVANTAGE on first attack (2d20, take higher)
- Attack shows both dice: [8, 15→15]+5 = 20
```
- Target selection: "attack 1", "attack 2" or just "1", "2"
- Defend bonus (+2 AC) persists until player's next turn
- Victory when all enemies defeated
- Loot drops from each defeated enemy
```

**Skill Check System Features (2.2):**
```
- AI requests with [ROLL: SkillName DC X]
- Automatic stat modifier application (STR, DEX, etc.)
- Display: 🎲 Stealth (DEX): [14]+3 = 17 vs DC 15 = ✅ SUCCESS
- Natural 20 → CRITICAL SUCCESS: AI narrates legendary/epic outcomes
- Natural 1 → CRITICAL FAILURE: AI narrates dramatic/comedic disasters
- Enhanced context sent to AI for memorable critical narration
- Perception vs Investigation distinction (10+ examples in DM prompt)
- Stealth movement rules: "any quiet movement = Stealth"
- 25 AI skill check tests at 100% pass rate (tests/test_skill_check_ai.py)
```

**AI DM Mechanics Testing (December 2025):** ✅ COMPLETE
```
Test Coverage:
- 45 comprehensive mechanics tests (test_dm_mechanics_round10.py)
- 22 focused scenario tests (test_dm_focused_round11.py) - 81.8% pass rate
- All 12 skill types generate correct [ROLL:] tags
- [COMBAT:], [BUY:], [PAY:], [RECRUIT:] tag generation validated
- Prompt injection resistance verified (AI stays in character)
- No auto-travel, no invented NPCs, no reroll spam confirmed
- Speed optimized: 50% faster test execution (1.5s→0.7s delays)

Reports:
- docs/DM_TESTING_COMPLETE_SUMMARY.md - Full test findings
- docs/DM_TESTING_ROUND11.md - Round 11 detailed results
```

**Leveling System Design (Planned):**
```
Level Cap: 5
XP Source: Milestones only (no kill grinding)

Level 1 → 2 (100 XP): +2 HP, +1 to any stat
Level 2 → 3 (300 XP): +2 HP, Class ability
Level 3 → 4 (600 XP): +2 HP, +1 to any stat  
Level 4 → 5 (1000 XP): +2 HP, +1 proficiency, Class ability

Milestone XP: Minor=25, Major=50, Boss=100, Adventure=150
```

**Combat Balance (Tuned):**
```
ENEMY STATS (Balanced for Level 1-3):
| Enemy        | HP | AC | Attack | Damage       | XP  |
|--------------|----|----|--------|--------------|-----|
| Goblin       | 5  | 12 | +3     | 1d6+1 (4.5)  | 25  |
| Goblin Boss  | 21 | 17 | +5     | 1d8+3 (7.5)  | 100 |
| Wolf         | 8  | 11 | +4     | 2d4+2 (7)    | 25  |
| Giant Spider | 18 | 13 | +4     | 1d8+2 (6.5)  | 50  |

DESIGN PHILOSOPHY:
- Standard enemies should be 2-3 hit kills for player
- Player should survive 3-4 hits from standard enemies
- Boss encounters reduced to 1 boss + 1 minion (was 1+2)
- Potions and rest mechanic critical for resource management
```

**Rest & Hit Dice System (2.7):** ✅ Complete
```
COMMANDS: 'rest', 'short rest', 'take a rest', 'heal', 'bandage'

MECHANICS:
- Each short rest consumes 1 Hit Die
- Hit Dice pool = Character Level (e.g., Level 1 = 1 Hit Die)
- Healing: 1d6 + CON modifier per rest
- Cannot rest during combat
- Cannot rest at full HP

HIT DICE RESTORATION:
- On boss kill (enemy name contains 'boss' or 'chief')
- On level up
- NOT restored after normal combat

DESIGN RATIONALE:
- Forces strategic potion use between fights
- Boss victories feel rewarding (full resource recovery)
- Level 1: Very limited resting (1 die until boss)
- Higher levels: More flexibility but still resource-gated
- Prevents "rest spam" exploit
```

---

### Phase 3: World & Persistence ✅ Complete
**Goal:** Make it feel like a real adventure

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 3.1 | Save/Load System | JSON file for character + story progress | ✅ Complete |
| 3.2 | Location System | Multiple rooms/areas with movement | ✅ Complete |
| 3.2.1 | Location Enhancements | Tests, items/NPCs, events, narration | ✅ Complete |
| 3.3 | NPCs | Dialogue, quests, shop functionality | ✅ Complete |

**Save/Load System Features (3.1):**
```
- Save game to numbered slots (1-3) or timestamped files
- Load from main menu or in-game
- Preserves: character stats, HP, XP, inventory, gold, equipped items
- Preserves: scenario progress and story flags
- Commands: 'save', 'load', 'saves' (list all)
- Save directory: /saves/
```

**Location System Features (3.2):**
```
- Location dataclass with: id, name, description, exits, npcs, items, atmosphere
- LocationManager: handles movement, exit validation, context for AI
- Pre-defined locations per scenario scene (18 locations in Goblin Cave)
- Scene → Location binding: each scene unlocks specific locations
- Commands: 'look' (describe location), 'exits' (show available), 'go <direction>'
- Cardinal directions supported: north, south, east, west, n, s, e, w
- AI receives location context for immersive narration
- Location state persisted in save files (visited, current location)
```

**Location System Enhancements (3.2.1):** ✅ Complete
```
Priority 1 - Test Coverage (HIGH): ✅ COMPLETE
  [x] Create tests/test_location.py with comprehensive tests (200 tests)
  [x] Test Location.to_dict() / from_state() serialization
  [x] Test LocationManager.move() with valid/invalid directions
  [x] Test exit filtering by available_location_ids
  [x] Test save/load round-trip for location state
  [x] Test LocationEvent class and event methods

Priority 2 - Item/NPC Integration (MEDIUM): ✅ COMPLETE
  [x] Display items on 'look' command
  [x] Add 'take <item>' command for location items
  [x] Show NPCs present in location
  [x] Add 'talk <npc>' command for NPC dialogue

Priority 3 - Location Events (MEDIUM): ✅ COMPLETE
  [x] Created LocationEvent dataclass with EventTrigger enum
  [x] Implement events_triggered functionality
  [x] trigger_event(), has_event(), is_event_triggered(), add_event() methods
  [x] get_events_for_trigger() with first-visit detection
  [x] Updated move() to return triggered events
  [x] AI DM receives event context for narration
  [x] Added events to 6 Goblin Cave locations (traps, discoveries, confrontations)

Priority 4 - Movement Narration (MEDIUM): ✅ COMPLETE
  [x] LOCATION_NARRATION_PROMPT for immersive AI descriptions
  [x] build_location_context() - gathers items, NPCs, events, atmosphere
  [x] get_location_narration() - requests AI narrative prose
  [x] display_location_narration() - consistent output format
  [x] 'look' command now uses AI narration (not bullet points)
  [x] Movement triggers AI narration with event context
  [x] Added 'scan' command for mechanical item/NPC/exit list
  [x] User-friendly item display ("Healing Potion" not "healing_potion")
  [x] Normalized item matching (spaces work: "take healing potion")

Priority 5 - Conditional Exits (MEDIUM): ✅ COMPLETE
  [x] Created ExitCondition dataclass with condition, fail_message, consume_item
  [x] Added exit_conditions field to Location dataclass
  [x] Created check_exit_condition() function for all condition types:
      - has_item: requires specific item in inventory
      - gold: requires minimum gold amount
      - visited: requires visiting another location first
      - skill: triggers skill check (handled by game.py)
      - objective: requires completed objective
      - flag: custom game flags
  [x] Updated move() to check conditions and unlock exits
  [x] Added unlocked_exits tracking (persists after first unlock)
  [x] Updated game.py to pass game_state and handle CONSUME_ITEM
  [x] Added locked storage room to Goblin Cave (requires storage_key)
  [x] Added storage_key item to inventory.py
  [x] Added 23 new tests (103 total location tests)

Priority 6 - Cardinal Aliases (LOW): ✅ COMPLETE
  [x] Add direction_aliases to Location dataclass
  [x] Map n/s/e/w to descriptive exits
  [x] resolve_direction_alias() helper function
  [x] CARDINAL_ALIASES constant (n/s/e/w/ne/nw/se/sw/u/d)
  [x] Updated move() to check aliases first
  [x] Added aliases to all Goblin Cave locations
  [x] Added 18 new tests (121 total location tests)

Priority 7 - Random Encounters (MEDIUM): ✅ COMPLETE
  [x] Create RandomEncounter dataclass with chance%, enemies, conditions
  [x] Add random_encounters field to Location
  [x] Roll for encounter on location entry (check_random_encounter method)
  [x] visit_count tracking on Location (persists in save/load)
  [x] max_triggers, min_visits, cooldown mechanics
  [x] Forest path: 20% chance wolf encounter (max 2x, 3-visit cooldown)
  [x] Cave tunnel: 25% chance giant_spider (not first visit)
  [x] Added giant_spider enemy to combat.py
  [x] Added 20 new tests (141 total location tests)

Priority 8 - Optional Areas (LOW): ✅ COMPLETE
  [x] Add hidden, discovery_condition, discovery_hint fields to Location
  [x] Add discovered_secrets tracking to LocationManager
  [x] Add discover_secret(), is_secret_discovered(), check_discovery() methods
  [x] get_exits() now filters hidden locations until discovered
  [x] Discovery condition formats: skill:, has_item:, level:, visited:
  [x] Add secret_cave to forest_clearing (perception DC 14, ancient_amulet loot)
  [x] Add treasure_nook to boss_chamber (investigation DC 12, enchanted_dagger loot)
  [x] Added 33 new tests (200 total location tests)

Priority 9 - Travel Menu System (HIGH): ✅ COMPLETE
  [x] Replace free-form travel input with numbered destination menu
  [x] Show travel menu after typing 'travel' command:
      - Display current location name/description
      - List numbered destinations: [1] Tavern, [2] Forest Path, etc.
      - Accept: number ("1"), cardinal ("n"), or exit name ("tavern")
  [x] Two-phase travel for dangerous areas:
      - Phase 1: Select destination (numbered)
      - Phase 2: "How do you approach?" (Enter = walk normally)
      - Parse approach keywords: sneak, run, carefully, etc.
      - Trigger skill checks based on approach (Stealth for sneak)
  [x] Smart approach prompting:
      - Only ask "How do you approach?" when:
        * First visit to new area
        * Destination has enemies/danger
        * Location marked with danger_level != "safe"
      - Skip prompt for safe/visited locations
  [x] Approach keywords detection:
      - STEALTH: sneak, quietly, stealthily, creep, hide, shadow, silently
      - URGENT: run, rush, hurry, sprint, dash, flee, quick, fast
      - CAUTIOUS: careful, cautiously, slowly, wary, look around, watching
  [x] Successful stealth approach grants SURPRISE in combat
  [x] Danger indicators: ⚠️ threatening, ☠️ deadly, ❓ uneasy
  [x] Visited markers (✓) for explored locations
  [x] Added tests/test_travel_menu.py (42 tests)
  [x] DRY refactoring: created perform_travel() shared function
  [x] Location-based DCs: stealth_dc and perception_dc in LocationAtmosphere
  [x] get_approach_dcs() extracts DCs from location
  [x] Old "go" handler refactored to use perform_travel()
```

---

### Phase 3.3: NPC System ✅ Complete
**Goal:** Deep NPC interactions for immersive gameplay

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 3.3.1 | NPC Dataclass | Name, dialogue, role, shop inventory, quest info | ✅ Complete |
| 3.3.2 | Dialogue System | Conversation trees, AI-enhanced responses | ✅ Complete |
| 3.3.3 | Shop System | Buy/sell items, haggle mechanic | ✅ |
| 3.3.4 | Quest System | Accept, track, complete quests | ✅ |
| 3.3.5 | Traveling Merchants | Random merchant encounters | ✅ Complete |
| 3.3.6 | NPC Relationships | Disposition tracking, reputation | ✅ Complete |
| 3.3.7 | **Party System** | Recruit companions, party combat bonuses | ✅ Complete |

**NPC System Implementation Plan:**
```
Priority 1 - NPC Foundation (HIGH): ✅ COMPLETE
  [x] Create src/npc.py with NPC dataclass
  [x] NPC fields: id, name, description, role, location_id
  [x] Role enum: MERCHANT, QUEST_GIVER, INFO, HOSTILE, RECRUITABLE, NEUTRAL
  [x] Add dialogue: Dict[str, str] for keyed responses
  [x] Add disposition: int (-100 to 100) for attitude
  [x] Create NPCManager class for NPC tracking
  [x] NPC.to_dict() / from_dict() serialization
  [x] Create tests/test_npc.py with comprehensive tests
  [x] Add 4 starter NPCs for Goblin Cave (Bram, Barkeep, Elira, Lily)

Priority 2 - Dialogue System (HIGH): ✅ COMPLETE
  [x] 'talk <npc>' command in game.py
  [x] Basic dialogue retrieval (greeting, farewell)
  [x] 'talk <npc> about <topic>' command
  [x] AI-enhanced responses using NPC personality
  [x] NPC_DIALOGUE_PROMPT for immersive AI responses
  [x] Disposition affects dialogue tone
  [x] Location 'look' already shows NPCs via AI narration
  [x] Added tests/test_dialogue.py (24 tests)

Priority 3 - Shop System (MEDIUM): ✅ COMPLETE
  [x] Add shop_inventory: List[str] to NPC (ALREADY EXISTS)
  [x] Add merchant_markup: float field (default 1.5) (ALREADY EXISTS)
  [x] Core functions: calculate_buy_price(), calculate_sell_price()
  [x] format_shop_display() - formatted shop UI
  [x] get_merchant_at_location() - find merchants at player location
  [x] 'shop' command - display merchant inventory with prices
  [x] 'buy <item>' command - purchase from shop
  [x] 'sell <item>' command - sell to merchant
  [x] 'haggle' command - CHA DC 12 check for discount
      └── Success: 20% discount for this merchant
      └── Failure: +10% prices, disposition -5
  [x] 'gold' command - check current gold (aliases: g, money, coins)
  [x] Add Gavin the Blacksmith NPC to village_square (opens late for adventurers)
      └── 15% markup (lower than traveling merchants)
      └── Sells: daggers, shortswords, longsword, leather armor, potions, torches, rope
  [x] Add Trader Mira merchant NPC to forest_clearing
  [x] Add shop system tests (28 tests in test_shop.py)
  [x] Stock Tracking Enhancement:
      └── shop_inventory supports Dict[str, int] for quantities
      └── check_stock(), decrement_stock() helpers
      └── get_shop_inventory_for_prompt() for AI accuracy
      └── Display shows quantities (x6) or (∞) for unlimited
      └── Buy prevents out-of-stock purchases

Priority 3.5 - Shop UX Enhancements (NEW): ✅ COMPLETE
  [x] Natural Language Shop Detection (MASSIVELY EXPANDED):
      └── 85+ phrase triggers for shop interaction
      └── Exact triggers: "shop", "store", "browse", "trade", "merchandise"
      └── "What do you have" variations: "whatcha got", "what you got"
      └── "Show me" variations: "show me your wares", "let me see"
      └── Buy intent: "want to buy", "wanna buy", "looking to buy"
      └── Roleplay: "peruse your wares", "interested in your wares"
      └── Casual/slang: "show me the goods", "any deals", "hook me up"
      └── First-person: "i want to buy", "i wanna shop"
      └── 32 new shop trigger tests
  [x] Quantity Purchasing:
      └── "buy 3 healing potions" → buys 3 items
      └── "buy 5x torch" → alternate format supported
      └── Validates sufficient gold and stock
      └── Shows affordable quantity when gold is insufficient
      └── Limits to 99 items per purchase (abuse prevention)
      └── 7 new tests added (67 total in test_shop.py)
  [ ] Price Comparison (future):
      └── "compare <item>" shows owned vs shop version
  [ ] Suggested Items (future):
      └── Based on player class/level, suggest relevant items
  
  Architecture:
  - Items defined centrally in ITEMS dict (inventory.py)
  - Merchants reference items by ID in shop_inventory
  - shop_inventory format:
    - Dict[str, int]: item_id → quantity (stock tracking)
    - List[str]: unlimited stock (backward compatible)
  - Scenarios create merchant NPCs via factory functions
  - haggle_state dict tracks discount/increase per merchant
  - Future: ITEMS dict → items.json (Phase 5)

Priority 4 - Quest System (MEDIUM): ✅ COMPLETE
  
  STEP 1: Core Quest Classes (src/quest.py) ✅
  [x] QuestStatus enum: NOT_STARTED, ACTIVE, COMPLETE, FAILED
  [x] QuestObjective dataclass:
      - id: str (e.g., "rescue_lily", "kill_goblins_3")
      - description: str (e.g., "Find and rescue Lily")
      - objective_type: ObjectiveType enum (KILL, FIND_ITEM, TALK_TO, REACH_LOCATION, COLLECT)
      - target: str (enemy id, item id, npc id, or location id)
      - required_count: int (for KILL/COLLECT types, default 1)
      - current_count: int (progress tracking)
      - completed: bool
      - optional: bool (for bonus objectives)
  [x] Quest dataclass:
      - id: str (e.g., "rescue_lily_main")
      - name: str (e.g., "Rescue Lily Greenfield")
      - description: str (story context)
      - giver_npc_id: str (NPC who gives quest)
      - status: QuestStatus
      - objectives: List[QuestObjective]
      - rewards: Dict[str, Any] - {"gold": 50, "xp": 100, "items": ["healing_potion"]}
      - prerequisites: List[str] - Quest IDs that must be complete first
      - time_limit: Optional[int] - Turns before failure (None = unlimited)
      - on_accept_dialogue: str - NPC dialogue when accepting
      - on_complete_dialogue: str - NPC dialogue when turning in
  [x] QuestManager class:
      - active_quests: Dict[str, Quest]
      - completed_quests: List[str]
      - failed_quests: List[str]
      - add_quest(quest_id) - Accept quest, set ACTIVE
      - get_active_quests() -> List[Quest]
      - get_quest(quest_id) -> Quest
      - check_objective(event_type, target_id, count=1) - Update progress
      - complete_quest(quest_id) - Grant rewards, set COMPLETE
      - fail_quest(quest_id) - Set FAILED
      - to_dict() / from_dict() - Serialization
  
  STEP 2: Objective Tracking Integration ✅
  [x] Hook into combat system: on enemy kill, call check_objective(KILL, enemy_id)
  [x] Hook into inventory: on item pickup, call check_objective(FIND_ITEM, item_id)
  [x] Hook into location: on arrive, call check_objective(REACH_LOCATION, location_id)
  [x] Hook into NPC dialogue: on talk, call check_objective(TALK_TO, npc_id)
  
  STEP 3: Game Commands (game.py) ✅
  [x] 'quests' / 'journal' - Show all active quests with progress
  [x] 'quest <name>' - Show detailed quest info and objectives
  [x] Quest auto-tracking messages when objectives complete
  
  STEP 4: NPC Quest Dialogue (npc.py) ✅
  [x] Add quest_giver role behavior
  [x] "quest" dialogue key triggers quest offer
  [x] Accept/decline flow for quest NPCs
  [x] Turn-in flow when objectives complete
  
  STEP 5: First Quests ✅
  [x] "Rescue Lily" main quest:
      - Giver: Old Bram (tavern)
      - Objectives: Reach cave, find Lily, return to village
      - Rewards: 100 XP, 50 gold, healing_potion
  [x] "Recover Heirlooms" side quest:
      - Giver: Bram (requires rescue_lily accepted first)
      - Objectives: Find silver_locket, find family_ring
      - Rewards: 50 XP, 25 gold
  [x] "Clear the Path" side quest:
      - Giver: Barkeep (tavern)
      - Objectives: Kill 2 wolves, 6 goblins
      - Rewards: 75 XP, 30 gold
  [x] "The Chief's Treasure" side quest:
      - Giver: Barkeep (tavern)
      - Objectives: Defeat goblin_chief, find treasure_nook
      - Rewards: 100 XP, 100 gold
  
  STEP 6: Save/Load Integration ✅
  [x] Add quest_manager to save_game() serialization
  [x] Add quest_manager to load_game() deserialization
  [x] Preserve objective progress across saves
  
  STEP 7: Tests ✅
  [x] tests/test_quest.py - 57 tests covering:
      - Quest creation, status transitions
      - Objective progress tracking
      - Quest completion and rewards
      - QuestManager operations
      - Serialization/deserialization
      - Integration hooks
  [x] tests/test_scenario.py - 5 new tests for quest integration
  [x] tests/test_save_system.py - 1 new test for quest save/load
  Total: 1006 tests passing

Priority 5 - Traveling Merchants (LOW): ✅ COMPLETE
  [x] Add spawn_chance: float to merchant NPCs
  [x] Random merchant spawn on location entry
  [x] Traveling merchant inventory rotation
  [x] Add Wandering Trader NPC (Zephyr the Wanderer)
  [x] Add traveling merchant tests (37 tests)
  [x] Integrate with game.py location change events
  New NPC fields: is_traveling, spawn_chance, possible_locations, inventory_pool
  Helper functions: check_traveling_merchant_spawn(), rotate_merchant_inventory()
  Helper functions: spawn_traveling_merchant(), despawn_traveling_merchant()

Priority 6 - NPC Relationships (LOW): ✅ COMPLETE

  Implementation Steps:
  
  Step 1 - Disposition Constants & Helper Functions: ✅ COMPLETE
    [x] Define threshold constants in npc.py:
        DISPOSITION_HOSTILE = -50, DISPOSITION_UNFRIENDLY = -10
        DISPOSITION_FRIENDLY = 10, DISPOSITION_TRUSTED = 50
        PRICE_MODIFIER_* constants for each level
    [x] get_disposition_level() → returns 'hostile'/'unfriendly'/'neutral'/'friendly'/'trusted'
    [x] get_disposition_label() → returns "🔴 Hostile (-75)", "🟢 Friendly (+35)", etc.
    [x] modify_disposition(amount) → change disposition with clamping to -100/+100
    [x] get_disposition_modifier() → returns price multiplier (0.0, 1.25, 1.0, 0.9, 0.8)
    [x] can_trade() → returns False if hostile, True otherwise
    [x] Added tests/test_reputation.py with 47 tests (all passing)
    [x] Added tests/test_reputation_hostile.py with 36 adversarial tests (all passing)
    [x] Updated test_dialogue.py: "allied" → "trusted" (2 tests fixed)
    Total: 1006 tests passing
  
  Step 2 - Action-Based Disposition Changes: ✅ COMPLETE
    [x] Trade actions:
        - Buy from merchant: +1 disposition
        - Sell to merchant: +1 disposition
        - Haggle success: +2 disposition
        - Haggle failure: -5 disposition (existing)
    [x] Quest actions:
        - Added QuestType enum (MAIN/SIDE/MINOR)
        - Complete quest: +25/+15/+10 based on type
        - Quest giver NPC gets disposition boost on turn-in
        - Serialization updated for quest_type
    [x] Gift system:
        - 'give <item> to <npc>' command
        - +5 to +20 disposition based on item value
        - calculate_gift_disposition() helper function
    [x] Combat/theft:
        - 'steal from <npc>' command (DEX DC 15)
        - Steal failure: -30 disposition
        - Steal critical failure: -50 disposition
    [ ] Favors/special actions (future):
        - Complete NPC-specific favor: +15
  
  Step 3 - Threshold-Based Behaviors:
    [x] Hostile (<-50):
        - Refuse to trade (can_trade() returns False)
        - Refuse dialogue - NOT IMPLEMENTED
        - Combat trigger - NOT IMPLEMENTED
    [x] Unfriendly (-50 to -10):
        - +25% prices (get_disposition_modifier() returns 1.25)
        - Limited dialogue - NOT IMPLEMENTED
    [x] Neutral (-10 to +10):
        - Normal prices and interactions
        - Standard dialogue access
    [x] Friendly (+10 to +50):
        - -10% price discount (modifier 0.9)
        - Extra dialogue - NOT IMPLEMENTED
    [x] Trusted (>+50):
        - -20% price discount (modifier 0.8)
        - Quest unlocks - NOT IMPLEMENTED
        - Recruitment DC reduction - NOT IMPLEMENTED
  
  Step 4 - Reputation Command: ✅ COMPLETE
    [x] 'reputation' or 'rep' command - GET /api/reputation endpoint
    [x] Display format with colored indicators - Emoji tier labels (🔴🟠🟡🟢💚)
    [x] 'reputation <npc>' for detailed view - GET /api/reputation/<npc_id>
    [x] Price modifier shown in detailed view
    [x] Available skill checks listed per NPC
    [x] Summary stats (total NPCs, counts by tier)
  
  Step 5 - Dialogue Integration:
    [x] AI prompt includes disposition level for tone adjustment (via get_context_for_dm)
    [ ] Threshold-locked dialogue topics - NOT IMPLEMENTED
    [ ] Hostile NPCs respond with threats/refusal only - NOT IMPLEMENTED
  
  Step 6 - Quest Unlocks:
    [ ] Add min_disposition field to quest requirements
    [ ] Some side quests require Friendly+ with NPC
    [ ] Special quests unlock at Trusted level
    [ ] Quest reward bonus based on disposition
  
  Step 7 - Persistence:
    [x] NPC.disposition field persists (NPC.to_dict/from_dict)
    [x] NPC state saved in game sessions
    [x] Load and apply on game restore
    [ ] Track dispositions in session state - PARTIAL
  
  Step 8 - Testing:
    [x] tests/test_reputation.py - 55 tests passing
    [x] tests/test_reputation_hostile.py - 36 adversarial tests
    [x] Test disposition threshold detection
    [x] Test modify_disposition clamping
    [x] Test action-based changes (trade, quest, gift)
    [x] Test threshold behaviors:
        - Price changes per level ✓
        - Trade refusal at Hostile ✓
    [x] Test reputation command display - API endpoints tested
    [x] Test save/load persistence of dispositions

Priority 7 - Party System (MEDIUM): ✅ COMPLETE

  Implementation Steps:
  
  Step 1 - PartyMember Data Structure:
    [x] Create src/party.py with PartyMember dataclass (723 lines)
    [x] Fields: id, name, char_class, description, portrait
    [x] Combat stats: level, max_hp, current_hp, armor_class, attack_bonus, damage_dice
    [x] Add special_ability: SpecialAbility dataclass per class
    [x] Recruitment fields: recruitment_location, recruitment_conditions, recruitment_dialogue
    [x] State fields: disposition, recruited (bool), is_dead, initiative
  
  Step 2 - Party Management in Game State:
    [x] Party class with members: List[PartyMember]
    [x] HP tracked per member (current_hp field)
    [x] Disposition tracked per member
    [x] Enforce party limit: 2 companions max (player + 2)
  
  Step 3 - Party Commands (API endpoints):
    [x] GET /api/party/view - show party roster with status/HP
    [x] POST /api/party/recruit - recruit NPC with conditions check
    [x] [RECRUIT: npc_id] DM tag for AI-driven recruitment
    [x] [PAY: amount, reason] DM tag for gold transactions
    [x] Party.remove_member() - dismiss affects disposition (-10)
  
  Step 4 - Recruitment System:
    [x] RecruitmentCondition.parse() - skill check, item, gold, objective
    [x] Skill check format: "skill:charisma:14" (CHA DC 14)
    [x] Item requirement: "item:eliras_bow"
    [x] Gold requirement: "gold:50"
    [x] Objective requirement: "objective:cleared_camp"
    [x] check_recruitment_condition() with OR logic (any condition met)
    [x] pay_recruitment_cost() handles gold/item costs
  
  Step 5 - Define Recruitable NPCs:
    [x] Elira the Ranger (forest_clearing)
        - Condition: CHA DC 12 OR objective:find_scout_body
        - Ability: Hunter's Mark (+1d4 damage to marked target)
        - Personality: Reserved, vengeful, knows goblin tactics
    [x] Marcus the Mercenary (tavern_main)
        - Condition: gold:20 OR CHA DC 15
        - Ability: Shield Wall (+2 AC to adjacent allies)
        - Personality: Gruff, practical, experienced
    [x] Shade the Rogue (goblin_camp_shadows)
        - Condition: skill:charisma:14
        - Ability: Sneak Attack (+2d6 if flanking)
        - Personality: Cryptic, hidden agenda
  
  Step 6 - Combat Integration:
    [x] Turn order defined (initiative system in party.py)
    [x] Party member combat stats (attack_bonus, damage_dice, AC)
    [x] Party member auto-actions (AI-controlled) - get_party_member_action()
    [x] Flanking bonus implementation - check_flanking(), advantage on attacks
    [x] Combined attacks display - format_party_member_attack() in combat results
    [x] One special ability use per combat per member (ability_uses_remaining)
  
  Step 7 - Class Abilities:
    [x] Fighter - Shield Wall: +2 AC to party for 1 round
    [x] Ranger - Hunter's Mark: +1d4 damage to marked target
    [x] Rogue - Sneak Attack: +2d6 damage if flanking
    [x] Cleric - Healing Word: Heal 1d8+2 HP to ally
    [x] Wizard - Magic Missile: Auto-hit 1d4+1 damage
  
  Step 8 - Persistence:
    [x] PartyMember.to_dict() / from_dict() serialization
    [x] Party.to_dict() / from_dict() serialization
    [x] Party state saved in session.to_dict()
    [x] HP persists (current_hp field)
    [x] Party member rest() method for full heal
  
  Step 9 - Testing:
    [x] tests/test_party.py - 72 tests all passing
    [x] Test PartyMember dataclass creation
    [x] Test recruitment condition parsing
    [x] Test recruitment success/failure
    [x] Test party add/remove members
    [x] Test special ability usage
    [x] Test party save/load serialization
```

**NPC System Features (3.3.1-3.3.2):**
```
NPC Dataclass:
- id, name, description, role (merchant, quest_giver, info, hostile, recruitable)
- dialogue: Dict[str, str] - Keyed responses ("greeting", "quest", "shop", "recruit")
- disposition: int - Attitude toward player (-100 to 100)
- location_id: str - Where NPC is found
- quests: List[str] - Quest IDs this NPC gives
- shop_inventory: List[str] - Items for sale (if merchant)
- is_recruitable: bool - Can join player's party

Dialogue System:
- AI-enhanced: NPC personality guides AI responses
- Key phrases trigger specific info (ask about "goblins", "cave", "Lily")
- Disposition affects dialogue tone
- 'talk <npc> about <topic>' command
```

**Party Member System (3.3.7):**
```
=== DATA STRUCTURE ===

PartyMember Dataclass:
- id: str                       # "elira_ranger"
- name: str                     # "Elira"  
- char_class: str               # "Ranger"
- description: str              # Personality/background
- portrait: str                 # ASCII/emoji for display

Combat Stats:
- level: int                    # Party member level
- max_hp: int                   # Health pool
- current_hp: int               # Current health
- armor_class: int              # Defense
- attack_bonus: int             # Combat accuracy
- damage_dice: str              # "1d8+2"
- special_ability: str          # Unique skill

Recruitment:
- recruitment_location: str     # Where to find them
- recruitment_condition: str    # "skill:charisma:14" or "objective:cleared_camp"
- recruitment_dialogue: Dict    # Conversation tree
- disposition: int              # Initial attitude
- recruited: bool = False       # In party?

=== RECRUITMENT FLOW ===

1. Player finds NPC in location (e.g., Elira in forest_clearing)
2. 'talk elira' - Opens dialogue with personality-driven AI responses
3. NPC explains motivation (tracking goblins, wants revenge, etc.)
4. Player can 'recruit elira' - Triggers recruitment check
5. Check conditions:
   - Skill check (CHA DC 14): Persuade to join
   - Item requirement: "has_item:eliras_bow" (return stolen item)
   - Objective: "objective:cleared_camp" (prove strength)
   - Gold: "gold:50" (mercenary fee)
6. Success: NPC joins party, adds to party roster
7. Failure: "Perhaps after you've proven yourself..."

=== PARTY MANAGEMENT ===

Commands:
- 'party' - Show current party members with status
- 'party stats' - Detailed party member statistics
- 'dismiss <name>' - Remove party member (may affect disposition)
- 'talk <party_member>' - Chat with party member (AI personality)

Display:
┌─────────────────────────────────────────────┐
│ 👥 YOUR PARTY                               │
├─────────────────────────────────────────────┤
│ 🧝 Elira (Ranger, Lvl 2) - HP: 18/18       │
│    "Ready to hunt some goblins."           │
│ ⚔️ Marcus (Fighter, Lvl 2) - HP: 22/24     │
│    "I've seen worse odds."                 │
└─────────────────────────────────────────────┘

Party Limit: 3 members (player + 2 companions)

=== COMBAT INTEGRATION ===

Turn Order:
1. Player acts
2. Party members act (AI-controlled or simple logic)
3. Enemies act

Party Member Actions (automatic):
- Attack nearest/weakest enemy
- Use special ability when appropriate
- Protect low-HP player
- Heal party (if healer class)

Combat Bonuses:
- Flanking: +2 attack when party member adjacent to same target
- Combined attacks: Party attacks same target player attacked
- Abilities: Each class has one special ability per combat

Party Member Classes:
┌──────────┬─────────────────┬───────────────────────────────┐
│ Class    │ Combat Role     │ Special Ability               │
├──────────┼─────────────────┼───────────────────────────────┤
│ Fighter  │ Tank/Damage     │ Shield Wall: +2 AC to party   │
│ Ranger   │ Ranged/Tracking │ Hunter's Mark: +1d4 to target │
│ Rogue    │ Damage/Utility  │ Sneak Attack: +2d6 if flank   │
│ Cleric   │ Healer/Support  │ Healing Word: 1d8+2 heal      │
│ Wizard   │ AoE Damage      │ Magic Missile: Auto-hit 1d4+1 │
└──────────┴─────────────────┴───────────────────────────────┘

=== GOBLIN CAVE RECRUITABLE NPCS ===

1. Elira the Ranger (forest_clearing):
   - Tracking the same goblin clan that killed her brother
   - Recruitment: CHA DC 12 OR complete "find scout body" objective
   - Ability: Hunter's Mark (+1d4 damage to marked target)
   - Dialogue: Reserved, vengeful, knows goblin tactics
   
2. Marcus the Mercenary (tavern_main):
   - Unemployed sellsword looking for work
   - Recruitment: Pay 25 gold OR CHA DC 15 (convince shared reward)
   - Ability: Shield Wall (+2 AC to adjacent allies)
   - Dialogue: Gruff, practical, experienced
   
3. Shade the Rogue (goblin_camp_shadows):
   - Mysterious figure who poisoned the scout
   - Recruitment: Find them first, then CHA DC 14
   - Ability: Sneak Attack (+2d6 if flanking)
   - Dialogue: Cryptic, has hidden agenda

=== PARTY MEMBER STATE ===

Saved to game state:
- party_members: List[str]      # IDs of recruited members
- party_hp: Dict[str, int]      # Current HP per member
- party_disposition: Dict[str, int]  # Relationship with player

Persistence:
- Party members persist across saves
- HP restores on long rest
- Disposition changes based on player choices
```

**Shop System Features (3.3.3):**
```
Commands:
- 'shop' or 'buy' - Open shop interface
- 'buy <item>' - Purchase item
- 'sell <item>' - Sell from inventory
- 'haggle' - Attempt better price (CHA check)

Mechanics:
- Buy price: item.value * merchant_markup (1.5x default)
- Sell price: item.value * 0.5
- Haggle success (CHA DC 12): 20% discount
- Haggle failure: merchant offended, prices +10%

Goblin Cave Integration:
- Add traveling merchant to forest_clearing
- Sells: healing_potions, torches, rations
- Buys: goblin loot at fair prices
```

**Quest System Features (3.3.4):**
```
Quest Dataclass:
- id, name, description, giver_npc_id
- objectives: List[str] - Objective IDs to complete
- rewards: Dict[str, int] - {"gold": 50, "xp": 100, "item": "magic_dagger"}
- status: NOT_STARTED, ACTIVE, COMPLETE, FAILED

Commands:
- 'quests' - Show active quests
- 'quest <name>' - Show quest details

Goblin Cave Integration:
- Main quest: "Rescue Lily" (from Bram)
- Side quest: "Recover the Heirlooms" (find 3 stolen items)
```

---

### Phase 3.4: Moral Choices & Consequences ✅ Complete
**Goal:** Meaningful player choices with lasting impact

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 3.4.1 | Choice System | Branching dialogue with consequences | ✅ Complete |
| 3.4.2 | Reputation System | Track player reputation with factions/NPCs | ✅ Complete |
| 3.4.3 | Alternative Resolutions | Non-combat solutions to encounters | ✅ Complete |
| 3.4.4 | Multiple Endings | Different outcomes based on choices | ⬜ (Future) |

**Success Criteria:**
- [x] Choice, ChoiceOption, ChoiceConsequence dataclasses
- [x] ChoiceManager class with full lifecycle management
- [x] 3 goblin cave moral choices implemented
- [x] 4 API endpoints for choices (/api/choices/*)
- [x] 35 new tests passing

**Choice System Features (3.4.1):**
```
Choice Dataclass:
- id, prompt, options: List[ChoiceOption]
- consequences: Dict[str, str] - Maps choice to outcome

ChoiceOption:
- id, text, requirements (skill check, item, reputation)
- outcome: str - What happens if chosen

Goblin Cave Integration:
- Captured goblin begs for life: spare/kill?
- Chief offers deal: take gold, leave Lily?
- Lily wants revenge: let her kill goblin?
```

**Alternative Resolutions (3.4.3):**
```
Boss Chamber Options:
1. Combat (default): Fight chief + bodyguards
2. Stealth: Sneak past, free Lily, escape
3. Negotiation: CHA DC 15, trade gold for Lily
4. Deception: Pretend to join goblins, betray later
5. Intimidation: STR DC 18, scare chief into surrender

Each option:
- Different XP rewards
- Different loot outcomes
- Different NPC reactions later
- Different ending narration
```

**Multiple Endings (3.4.4):**
```
Goblin Cave Endings:
1. Hero's Return: Full victory, chief dead, Lily saved
2. Mercenary: Took chief's bribe, left Lily (bad ending)
3. Peaceful: Negotiated release, chief alive (complex)
4. Vengeful: Let Lily kill goblins (dark hero)
5. Stealth Master: No combat, pure stealth escape

Ending affects:
- Reward amount
- Village reputation
- Available future quests
- NPC dialogue changes
```

**Phase 3 Success Criteria:**

*3.1-3.2 World & Persistence:*
- [x] Game state persists between sessions
- [x] Player can navigate between locations
- [x] Location system has comprehensive test coverage (200 tests)
- [x] Player can interact with items/NPCs in locations
- [x] AI generates immersive location descriptions
- [x] Locations can have locked doors requiring keys/puzzles
- [x] Random encounters add variety to exploration
- [x] Secret areas reward thorough exploration

*3.3 NPC System:*
- [x] NPCs have personalities that affect dialogue (Personality dataclass)
- [x] Player can buy/sell items at shops (shop.py + API)
- [x] Player can accept and track quests (quest.py + Quest Journal UI)
- [x] Traveling merchants add variety (traveling_merchant in npc.py)
- [x] Party members can be recruited via skill checks or objectives
- [x] Party members provide combat bonuses (abilities defined)
- [x] Party members persist across saves (to_dict/from_dict)
- [x] Player can interact with NPCs for quests/trading

*3.4 Moral Choices & Consequences:*
- [ ] Player choices have visible consequences
- [ ] Multiple ways to resolve encounters
- [ ] At least 3 distinct endings per scenario
- [x] Reputation affects NPC interactions (disposition system)

*3.4.1 LocationAtmosphere System (Complete):*
- [x] LocationAtmosphere dataclass for sensory/mood details
- [x] Integrate atmosphere into location context for DM
- [x] Add atmospheres to key Goblin Cave locations (4 locations)
- [x] DM prompts use atmosphere for consistent descriptions
- [x] stealth_dc and perception_dc fields for approach mechanics

*3.5 Campaign System:*
- [ ] Campaign dataclass to group scenarios as episodes
- [ ] Scenarios chain together with next_scenario_id
- [ ] Prerequisite system (require completing prior episodes)
- [ ] Persistent story flags carry across scenarios
- [ ] Campaign progress display
- [ ] JSON-based campaign format (enables modding in Phase 5)

---

### Phase 3.5: Campaign & Episode System ⬜ Not Started
**Goal:** Enable interconnected scenarios as chapters/episodes within campaigns

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 3.5.1 | Campaign Dataclass | Structure to group scenarios as episodes | ⬜ |
| 3.5.2 | Scenario Chaining | next_scenario_id, prerequisite_scenario | ⬜ |
| 3.5.3 | Persistent Story Flags | Flags that carry across scenarios | ⬜ |
| 3.5.4 | Unlock Conditions | Require completing prior scenarios | ⬜ |
| 3.5.5 | Campaign Manager | Track campaign progress and unlocks | ⬜ |

**Campaign System Implementation Plan:**
```
Priority 1 - Campaign Foundation (HIGH): ⬜ NOT STARTED
  [ ] Create Campaign dataclass in scenario.py
      - id: str - Unique campaign identifier
      - name: str - Display name ("The Goblin Menace Saga")
      - description: str - Campaign overview
      - author: str - Creator name (for modding)
      - version: str - Campaign version
      - scenario_order: List[str] - Ordered scenario IDs (episodes)
      - unlock_conditions: Dict[str, str] - {"episode_2": "completed:episode_1"}
      - persistent_flags: Dict[str, Any] - Story flags shared across scenarios
  [ ] Add to Scenario dataclass:
      - campaign_id: Optional[str] - Which campaign this belongs to
      - episode_number: int - Position in campaign (1, 2, 3...)
      - next_scenario_id: Optional[str] - Link to next episode
      - prerequisite_scenario_id: Optional[str] - Must complete first
      - scenario_flags: Dict[str, Any] - Flags set by this scenario
  [ ] Create CampaignManager class
      - available_campaigns: Dict[str, Campaign]
      - campaign_progress: Dict[str, int] - Last completed episode
      - unlocked_scenarios: List[str] - Scenarios player can access
  [ ] Add campaign selection to game flow
  [ ] Campaign progress persistence in saves
  [ ] Add campaign system tests

Priority 2 - Scenario Chaining (MEDIUM): ⬜ NOT STARTED
  [ ] Scenario completion triggers next_scenario prompt
  [ ] "Continue to Episode 2?" choice on completion
  [ ] Character data carries forward automatically
  [ ] Scenario-specific items/flags persist
  [ ] Episode restart on player death (confirmed decision)
  [ ] Allow returning to previous episodes via Campaign Browser
      └── Warning: "Progress will overwrite current save"

Priority 3 - Persistent Story Flags (MEDIUM): ⬜ NOT STARTED
  [ ] Flag system for cross-scenario consequences
      - "spared_goblin_chief": bool - Changes Episode 2 dialogue
      - "recruited_elira": bool - Elira available in Episode 2
      - "lily_saved": bool - Affects village reputation
  [ ] Flag auto-set triggers (TBD: needs brainstorming)
      └── 🔶 OPEN: On objective complete? NPC dialogue choice? Item pickup?
  [ ] Flag storage location: save_data.campaign_flags: Dict[str, Any]
  [ ] AI DM context injection format:
      └── "STORY FLAGS: spared_chief=true, recruited_elira=true"
  [ ] Flags affect NPC dialogue, quest availability
  [ ] Add flag check conditions: "flag:saved_lily:true"

Priority 4 - Unlock System (LOW): ⬜ NOT STARTED
  [ ] Lock Episode 2+ until Episode 1 complete
  [ ] Display locked scenarios with requirements
  [ ] Unlock conditions:
      - "completed:<scenario_id>" - Finished scenario
      - "level:<n>" - Character level requirement
      - "flag:<name>:<value>" - Specific flag state
      - 🔶 OPEN: "gold:<amount>" - Wealth gate? (for premium?)
  [ ] Unlock status in scenario selection menu
```

**Example Campaign Structure:**
```
Campaign: "The Goblin Menace" (Base Game)
├── Episode 1: "The Goblin Cave" (goblin_cave)
│   └── Objective: Rescue Lily, defeat or negotiate with chief
│   └── Flags Set: saved_lily, spared_chief, recruited_elira
│
├── Episode 2: "The Goblin Fortress" (goblin_fortress) [Future]
│   └── Prerequisite: completed:goblin_cave
│   └── If spared_chief: Chief warns of greater threat
│   └── If killed_chief: New chief more aggressive
│
└── Episode 3: "The Goblin King" (goblin_king) [Future]
    └── Prerequisite: completed:goblin_fortress
    └── Final confrontation with Goblin King
    └── Multiple endings based on accumulated flags
```

**Edge Cases & Decisions:**
```
┌─────────────────────────────────────────────────────────────────┐
│ DECIDED                                                         │
├─────────────────────────────────────────────────────────────────┤
│ Player dies mid-episode    │ Restart episode from beginning    │
│ Return to previous episode │ Allowed, with save overwrite warn │
│ Character data carryover   │ Stats, inventory, gold persist    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 🔶 OPEN QUESTIONS (To Be Discussed)                             │
├─────────────────────────────────────────────────────────────────┤
│ Inventory bloat            │ Soft cap? Stash between episodes? │
│ Level cap across episodes  │ Raise to 10? Prestige system?     │
│ Flag auto-set triggers     │ Objective? Dialogue? Item? All?   │
│ Premium unlock gates       │ Gold gate for DLC? Or separate?   │
└─────────────────────────────────────────────────────────────────┘
```

**Success Criteria:**
- [ ] Campaigns group multiple scenarios as episodes
- [ ] Completing Episode 1 unlocks Episode 2
- [ ] Character stats/inventory persist across episodes
- [ ] Story flags from Episode 1 affect Episode 2
- [ ] Campaign progress saved and loaded correctly
- [ ] Player death restarts current episode

---

### Phase 3.4.1: Location Atmosphere System ✅ Complete
**Goal:** Add structured sensory and mood data to locations for consistent, immersive descriptions

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 3.4.1.1 | LocationAtmosphere Dataclass | Sensory details and mood hints for DM | ✅ |
| 3.4.1.2 | Location Integration | Add atmosphere field to Location class | ✅ |
| 3.4.1.3 | DM Prompt Enhancement | Include atmosphere in location context | ✅ |
| 3.4.1.4 | Goblin Cave Atmospheres | Add atmospheres to scenario locations | ✅ |
| 3.4.1.5 | Tests | Unit tests for atmosphere serialization | ✅ |

**LocationAtmosphere Dataclass Design:**
```python
@dataclass
class LocationAtmosphere:
    """
    Atmospheric hints for the DM to create immersive location descriptions.
    These are suggestions, not scripts - the AI weaves them into narrative.
    """
    # Sensory palette (DM picks 2-3 to incorporate)
    sounds: List[str] = []       # ["dripping water", "distant echoes", "goblin chatter"]
    smells: List[str] = []       # ["musty earth", "torch smoke", "something rotting"]
    textures: List[str] = []     # ["damp stone walls", "slippery moss", "rough-hewn rock"]
    lighting: str = ""           # "dim torchlight", "pitch black", "dappled sunlight"
    temperature: str = ""        # "cold and damp", "uncomfortably warm", "chilly draft"
    
    # Mood guidance (not prescriptive emotion, just tone)
    mood: str = ""               # "tense", "eerie", "welcoming", "oppressive"
    danger_level: str = ""       # "safe", "uneasy", "threatening", "deadly"
    
    # Optional flavor pool (random small details DM can use)
    random_details: List[str] = []  # ["rat scurries past", "torch flickers", "shadow moves"]
```

**Example - Cave Entrance:**
```python
atmosphere=LocationAtmosphere(
    sounds=["wind howling at entrance", "distant dripping", "occasional screeching"],
    smells=["damp earth", "old bones", "something acrid"],
    textures=["cold rough stone", "slippery moss patches"],
    lighting="darkness beyond, faint daylight at entrance",
    temperature="cold draft from within",
    mood="ominous threshold",
    danger_level="uneasy",
    random_details=["crude goblin scratches on wall", "old campfire remains", 
                   "discarded broken weapon", "bones scattered near entrance"]
)
```

**Design Principles:**
```
1. LISTS NOT SCRIPTS - Give options, let AI choose what fits
2. MOOD OVER EMOTION - "tense" not "you feel scared" (player agency)
3. SENSORY VOCABULARY - Sounds, smells, textures (not just visual)
4. DANGER SIGNALING - Lets DM adjust tone appropriately
5. RANDOM DETAIL POOL - Small flavor elements AI can sprinkle in
6. CONSISTENCY - Same atmosphere on return visits for continuity
```

**DM Prompt Integration:**
```
Location context now includes:
{
  "name": "Cave Entrance",
  "description": "...",
  "atmosphere": {
    "sounds": ["dripping water", "distant echoes"],
    "smells": ["damp earth"],
    "mood": "ominous",
    "danger_level": "uneasy"
  }
}

DM instruction: "Use 2-3 sensory details from the atmosphere to create immersion.
The mood is [ominous] - let that inform your tone without stating emotions directly."
```

**Success Criteria:**
- [x] LocationAtmosphere dataclass with serialization (to_dict/from_dict)
- [x] Location class has optional atmosphere field
- [x] DM prompts include atmosphere data (build_location_context)
- [x] Key Goblin Cave locations have atmospheres (village_square, cave_entrance, main_tunnel, boss_chamber)
- [x] Descriptions feel consistent but not repetitive
- [x] AI maintains creative freedom while using hints
- [x] Added stealth_dc/perception_dc for travel menu approach mechanics

---

### Phase 3.6: Item Utility System ✅ COMPLETE
**Goal:** Give unused items mechanical purpose beyond flavor

| Step | Feature | Description | Priority | Status |
|------|---------|-------------|----------|--------|
| 3.6.1 | Goblin Ear Bounty | Quest to collect goblin ears for gold reward | HIGH | ✅ Complete |
| 3.6.2 | Gold Pouch Auto-Convert | Auto-add gold on pickup instead of item | HIGH | ✅ Complete |
| 3.6.3 | Mysterious Key Usage | Opens Hidden Hollow (alternative to Perception) | HIGH | ✅ Complete |
| 3.6.4 | Ancient Scroll Lore | Reading reveals secret tunnel location | HIGH | ✅ Complete |
| 3.6.5 | Lockpicks Mechanics | Alternative to getting cage key | MEDIUM | ✅ Complete |
| 3.6.6 | Poison Vial Combat | Apply for +1d4 poison damage | MEDIUM | ✅ Complete |
| 3.6.7 | Torch Darkness | Required in dark locations | LOW | ✅ Complete |
| 3.6.8 | Rope Utility | Climb/escape alternative routes | LOW | ✅ Complete |

**Item Analysis:**

| Item | Current State | Proposed Use | Effort | Status |
|------|--------------|--------------|--------|--------|
| `goblin_ear` | Drops, unused | Bounty quest: 5 ears → 25g | LOW | ✅ Done |
| `gold_pouch` | Says "contains gold" | Auto-convert on pickup | TRIVIAL | ✅ Done |
| `mysterious_key` | Opens nothing | Alt entry to Hidden Hollow | LOW | ✅ Done |
| `ancient_scroll` | Listed, unused | Reveals secret tunnel flag | LOW | ✅ Done |
| `lockpicks` | No lock system | Cage escape (DC 12 Sleight) | LOW | ✅ Done |
| `poison_vial` | Effect described | +1d4 damage on next hit | LOW | ✅ Done |
| `torch` | Flavor only | Required for dark cave areas | MEDIUM | ✅ Done |
| `rope` | Flavor only | Climb shortcut / cage escape | MEDIUM | ✅ Done |
| `rations` | No hunger system | Keep as flavor (no mechanics) | - | N/A |
| `bedroll` | No rest system | Keep as flavor (no mechanics) | - | N/A |

**Implementation Details:**

*3.6.1 Goblin Ear Bounty Quest:*
```python
Quest(
    id="thin_the_herd",
    name="Thin the Herd",
    description="The village offers a bounty for proof of goblin kills.",
    objectives=[("collect_ears", "Collect 5 goblin ears", "goblin_ear:5")],
    rewards={"gold": 25, "xp": 50}
)
# Quest giver: Barkeep or posted bounty board
# Condition check: has_item:goblin_ear:5
```

*3.6.2 Gold Pouch Auto-Convert:*
```python
# In item pickup handler:
if item_id.startswith("gold_pouch"):
    gold_amount = ITEMS[item_id].value  # 50 or 15
    add_gold(gold_amount)
    # Don't add item to inventory
    return f"[GOLD: {gold_amount}]"
```

*3.6.3 Mysterious Key → Hidden Hollow:*
```python
# Add to secret_cave location:
discovery_condition="skill:perception:14 OR has_item:mysterious_key"
# Alternative entry with the key
```

*3.6.4 Ancient Scroll → Secret Tunnel:*
```python
# Reading the scroll sets flag:
effect="flag:knows_secret_tunnel"
# Same flag as barkeep Persuasion DC 10
```

*3.6.5 Lockpicks → Cage Escape:*
```python
# Add to cage location:
LockedExit(
    id="cage_escape",
    condition="has_item:storage_key OR (has_item:lockpicks AND skill:sleight_of_hand:12)"
)
```

*3.6.6 Poison Vial Combat Bonus:*
```python
# New combat action: "use poison" or "apply poison"
# Sets flag: poison_applied_to_weapon
# Next attack: +1d4 poison damage
# One-time consumable, removes from inventory
```

**Keep as Flavor (No Mechanics):**
- `rations` - No hunger system (too complex for short scenario)
- `bedroll` - No fatigue system (too complex)
- AI DM can still roleplay using these items narratively

**Success Criteria:**
- [x] Goblin ears can be turned in for bounty reward
- [x] Gold pouches auto-convert to gold on pickup
- [x] Mysterious key opens Hidden Hollow
- [x] Ancient scroll reveals tunnel location
- [x] Lockpicks allow cage escape with skill check
- [x] Poison vial adds damage to next combat attack
- [x] Torch required in dark locations (disadvantage without)
- [x] Rope enables Athletics cage escape option
- [ ] All item effects documented in SCENARIO_REFERENCE.md

---

### Phase 4: Security & Testing ✅ COMPLETE
**Goal:** Comprehensive adversarial testing and security hardening

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 4.1 | Adversarial Testing | Hostile player exploit testing | ✅ |
| 4.2 | Prompt Injection Testing | Security against tag/command injection | ✅ |
| 4.3 | Flow Breaking Testing | Weird inputs, non-existent references | ✅ |
| 4.4 | Bug Fixes | Fix all discovered vulnerabilities | ✅ |

**Adversarial Testing Results (4.1-4.3):**
- **95 security tests** added across 3 test files
- **821 total tests** passing
- **5 bugs fixed**: negative damage, negative XP, empty item lookup, enemy.is_dead state, empty direction movement
- **Security architecture verified**: Parsers only process DM responses, not player input

**Bugs Fixed:**
| Bug | File | Exploit | Fix |
|-----|------|---------|-----|
| Negative damage heal | character.py | `take_damage(-100)` healed | Added `if amount <= 0: return` guard |
| Negative XP | character.py | `gain_xp(-1000)` reduced XP | Added `if amount <= 0: return` guard |
| Empty item lookup | inventory.py | `get_item("")` returned first item | Added empty/whitespace check |
| Enemy.is_dead state | combat.py | HP=0 didn't update is_dead | Changed to `@property` |
| Empty direction | scenario.py | `move("")` matched any exit | Added empty direction check |

---

### Phase 4.5: Interactive World Map UI ✅ Mostly Complete
**Goal:** Visual clickable map panel for intuitive travel and exploration

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 4.5.1 | Map Data Structures | Add coordinates, icons, connections to locations | ✅ |
| 4.5.2 | MapNode Dataclass | Visual representation of a location on the map | ✅ |
| 4.5.3 | WorldMap Class | Manages map rendering, connections, state | ✅ |
| 4.5.4 | Region System | Group locations into map regions/zones | ✅ |
| 4.5.5 | React Map Component | Clickable map with markers, connections, travel | ✅ |
| 4.5.6 | Map State Sync | Sync fog of war, visited, current location | ✅ |
| 4.5.7 | Scenario Map Definitions | Add map data to Goblin Cave scenario | ✅ |

**Why Map UI First:**
- Travel is the #1 pain point in text-based gameplay
- Visual map dramatically improves spatial understanding
- Reduces repetitive "go" commands and exit confusion
- Enables one-click travel to visible destinations
- Foundation for all future UI work (Flutter Phase 6)

---

#### 4.5.1 Map Data Structures (Backend)

**New Fields for Location Dataclass:**
```python
@dataclass
class Location:
    # ... existing fields ...
    
    # Map Visualization (Phase 4.5)
    map_x: float = 0.0              # X coordinate on map (0.0 to 1.0 normalized)
    map_y: float = 0.0              # Y coordinate on map (0.0 to 1.0 normalized)
    map_icon: str = "🏠"            # Emoji or icon ID for map marker
    map_label: str = ""             # Short label (defaults to name if empty)
    map_region: str = "default"     # Region/zone this location belongs to
    map_hidden: bool = False        # If True, not shown until visited or discovered
```

**MapNode Dataclass (Visual representation):**
```python
@dataclass
class MapNode:
    """Visual map representation of a location."""
    location_id: str                # References Location.id
    x: float                        # Normalized X (0-1)
    y: float                        # Normalized Y (0-1)
    icon: str                       # Display icon
    label: str                      # Display label
    
    # Visual State
    is_current: bool = False        # Player is here
    is_visited: bool = False        # Has been visited (full color)
    is_visible: bool = True         # Not hidden by fog of war
    is_accessible: bool = True      # Can travel to (not locked)
    
    # Status Indicators
    danger_level: str = "safe"      # safe/uneasy/threatening/deadly
    has_shop: bool = False          # Show shop icon
    has_quest: bool = False         # Show quest marker
    has_npc: bool = False           # Show NPC indicator
    
    def to_dict(self) -> dict:
        """Serialize for API/save."""
        return {
            "location_id": self.location_id,
            "x": self.x, "y": self.y,
            "icon": self.icon, "label": self.label,
            "is_current": self.is_current,
            "is_visited": self.is_visited,
            "is_visible": self.is_visible,
            "is_accessible": self.is_accessible,
            "danger_level": self.danger_level,
            "has_shop": self.has_shop,
            "has_quest": self.has_quest,
            "has_npc": self.has_npc
        }
```

**MapConnection Dataclass:**
```python
@dataclass
class MapConnection:
    """Visual line between two map nodes."""
    from_id: str                    # Source location ID
    to_id: str                      # Destination location ID
    is_bidirectional: bool = True   # Arrow on both ends?
    is_visible: bool = True         # Show this connection?
    is_locked: bool = False         # Dashed line for locked exits
    travel_time: str = ""           # Optional: "5 min", "1 hour"
```

---

#### 4.5.2 WorldMap Class (Map Manager)

```python
class WorldMap:
    """Manages the visual world map for a scenario."""
    
    def __init__(self, scenario_id: str):
        self.scenario_id = scenario_id
        self.nodes: Dict[str, MapNode] = {}          # location_id -> MapNode
        self.connections: List[MapConnection] = []    # All connections
        self.current_location: str = ""               # Current location ID
        self.regions: Dict[str, MapRegion] = {}       # region_id -> MapRegion
    
    def build_from_locations(self, locations: Dict[str, Location]):
        """Generate map from Location objects."""
        for loc_id, loc in locations.items():
            self.nodes[loc_id] = MapNode(
                location_id=loc_id,
                x=loc.map_x,
                y=loc.map_y,
                icon=loc.map_icon,
                label=loc.map_label or loc.name,
                is_visited=loc.visited,
                is_visible=not loc.map_hidden or loc.visited
            )
        
        # Build connections from exits
        for loc_id, loc in locations.items():
            for exit_name, dest_id in loc.exits.items():
                if dest_id in self.nodes:
                    self.connections.append(MapConnection(
                        from_id=loc_id,
                        to_id=dest_id
                    ))
    
    def update_current(self, location_id: str):
        """Update current location marker."""
        self.current_location = location_id
        for node in self.nodes.values():
            node.is_current = (node.location_id == location_id)
    
    def mark_visited(self, location_id: str):
        """Mark location as visited (reveal fog of war)."""
        if location_id in self.nodes:
            self.nodes[location_id].is_visited = True
            self.nodes[location_id].is_visible = True
    
    def reveal_adjacent(self, location_id: str, locations: Dict[str, Location]):
        """Reveal nodes adjacent to visited location."""
        if location_id in locations:
            loc = locations[location_id]
            for dest_id in loc.exits.values():
                if dest_id in self.nodes:
                    self.nodes[dest_id].is_visible = True
    
    def get_clickable_nodes(self) -> List[MapNode]:
        """Get nodes player can click to travel to."""
        current_loc = self.current_location
        # Find adjacent locations
        adjacent = set()
        for conn in self.connections:
            if conn.from_id == current_loc:
                adjacent.add(conn.to_id)
            if conn.to_id == current_loc and conn.is_bidirectional:
                adjacent.add(conn.from_id)
        
        return [
            node for node in self.nodes.values()
            if node.location_id in adjacent
            and node.is_visible
            and node.is_accessible
        ]
    
    def to_dict(self) -> dict:
        """Serialize entire map state for API."""
        return {
            "scenario_id": self.scenario_id,
            "current_location": self.current_location,
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "connections": [
                {"from": c.from_id, "to": c.to_id, "locked": c.is_locked}
                for c in self.connections if c.is_visible
            ]
        }
```

---

#### 4.5.3 MapRegion System

**MapRegion Dataclass:**
```python
@dataclass
class MapRegion:
    """A visual region/zone on the map (e.g., 'Village', 'Forest', 'Cave')."""
    id: str                         # "willowmere_village"
    name: str                       # "Willowmere Village"
    description: str                # "A peaceful farming village..."
    
    # Visual Properties
    background_color: str = "#2D5A3D"   # Region tint color
    border_color: str = "#1A3D1A"       # Border color
    icon: str = "🏘️"                    # Region icon
    
    # Bounds (normalized 0-1)
    bounds_x: float = 0.0           # Left edge
    bounds_y: float = 0.0           # Top edge
    bounds_width: float = 1.0       # Width
    bounds_height: float = 1.0      # Height
    
    # State
    is_unlocked: bool = True        # Can player enter this region?
    unlock_condition: str = ""      # "objective:rescue_lily"
```

---

#### 4.5.4 Goblin Cave Scenario Map Data

```
GOBLIN CAVE MAP LAYOUT (ASCII Preview):
╔═══════════════════════════════════════════════════════════╗
║                    WILLOWMERE REGION                       ║
║  ┌─────────┐     ┌─────────┐     ┌─────────┐              ║
║  │🍺Tavern │────→│🏛️Square │←────│🛠️Smithy │              ║
║  │  (YOU)  │     │    ✓    │     │    ✓    │              ║
║  └────┬────┘     └────┬────┘     └─────────┘              ║
║       │               │                                    ║
╠═══════│═══════════════│════════════════════════════════════╣
║       │    FOREST     │      REGION                        ║
║       │          ┌────┴────┐                              ║
║       └─────────→│🌲 Path  │                              ║
║                  │   ⚠️    │                              ║
║                  └────┬────┘                              ║
║                       │                                    ║
║                  ┌────┴────┐     ┌─────────┐              ║
║                  │🌳Clearing│────→│💀 Cave  │              ║
║                  │    ⚠️    │     │   ☠️    │              ║
║                  └─────────┘     └────┬────┘              ║
╠═════════════════════════════════════════════════════════════╣
║                    GOBLIN CAVE REGION                      ║
║                  ┌─────────┐     ┌─────────┐              ║
║                  │🕯️Tunnel │────→│⚔️ Camp  │              ║
║                  │    ⚠️    │     │   ⚠️    │              ║
║                  └────┬────┘     └────┬────┘              ║
║                       │               │                    ║
║                  ┌────┴────┐     ┌────┴────┐              ║
║                  │🔒Storage│     │👑 Boss  │              ║
║                  │  (key)  │     │   ☠️    │              ║
║                  └─────────┘     └─────────┘              ║
╚═════════════════════════════════════════════════════════════╝

LEGEND:
  ✓  Visited (full color)
  ⚠️  Threatening (yellow warning)
  ☠️  Deadly (red skull)
  🔒 Locked (requires key)
  →  Clickable connection
```

**Location Coordinates for Goblin Cave:**
```python
GOBLIN_CAVE_MAP_DATA = {
    # Willowmere Village Region (y: 0.0 - 0.25)
    "tavern_main":     {"x": 0.15, "y": 0.12, "icon": "🍺", "region": "village"},
    "village_square":  {"x": 0.50, "y": 0.12, "icon": "🏛️", "region": "village"},
    "blacksmith_shop": {"x": 0.85, "y": 0.12, "icon": "🛠️", "region": "village"},
    
    # Forest Region (y: 0.25 - 0.55)
    "forest_path":     {"x": 0.50, "y": 0.38, "icon": "🌲", "region": "forest"},
    "forest_clearing": {"x": 0.35, "y": 0.52, "icon": "🌳", "region": "forest"},
    "cave_entrance":   {"x": 0.65, "y": 0.52, "icon": "💀", "region": "forest"},
    
    # Goblin Cave Region (y: 0.55 - 1.0)
    "cave_tunnel":     {"x": 0.35, "y": 0.70, "icon": "🕯️", "region": "cave"},
    "goblin_camp":     {"x": 0.65, "y": 0.70, "icon": "⚔️", "region": "cave"},
    "storage_room":    {"x": 0.35, "y": 0.88, "icon": "📦", "region": "cave"},
    "boss_chamber":    {"x": 0.65, "y": 0.88, "icon": "👑", "region": "cave"}
}

GOBLIN_CAVE_REGIONS = {
    "village": {
        "name": "Willowmere Village",
        "color": "#4A7C59",
        "icon": "🏘️",
        "bounds": {"x": 0.0, "y": 0.0, "w": 1.0, "h": 0.25}
    },
    "forest": {
        "name": "Misty Forest",
        "color": "#2D5A3D",
        "icon": "🌲",
        "bounds": {"x": 0.0, "y": 0.25, "w": 1.0, "h": 0.30}
    },
    "cave": {
        "name": "Goblin Cave",
        "color": "#3D3D3D",
        "icon": "⛰️",
        "bounds": {"x": 0.0, "y": 0.55, "w": 1.0, "h": 0.45}
    }
}
```

---

#### 4.5.5 Flutter Map Widget (UI Component)

**Widget Architecture:**
```dart
// lib/widgets/world_map.dart

class WorldMapWidget extends StatefulWidget {
  final WorldMapData mapData;
  final Function(String locationId) onLocationTap;
  final Function(String locationId) onLocationHover;
  
  @override
  _WorldMapWidgetState createState() => _WorldMapWidgetState();
}

class _WorldMapWidgetState extends State<WorldMapWidget> {
  double _scale = 1.0;
  Offset _offset = Offset.zero;
  String? _hoveredNode;
  
  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onScaleUpdate: (details) {
        // Pinch to zoom
        setState(() => _scale = details.scale.clamp(0.5, 3.0));
      },
      onPanUpdate: (details) {
        // Drag to pan
        setState(() => _offset += details.delta);
      },
      child: CustomPaint(
        painter: MapPainter(
          mapData: widget.mapData,
          scale: _scale,
          offset: _offset,
          hoveredNode: _hoveredNode,
          theme: Theme.of(context),
        ),
        child: _buildInteractiveOverlay(),
      ),
    );
  }
  
  Widget _buildInteractiveOverlay() {
    // Invisible buttons over each node for tap detection
    return Stack(
      children: widget.mapData.nodes.map((node) {
        return Positioned(
          left: node.x * width * _scale + _offset.dx,
          top: node.y * height * _scale + _offset.dy,
          child: GestureDetector(
            onTap: () => widget.onLocationTap(node.locationId),
            onHover: (isHovering) {
              setState(() => _hoveredNode = isHovering ? node.locationId : null);
            },
            child: _buildNodeMarker(node),
          ),
        );
      }).toList(),
    );
  }
  
  Widget _buildNodeMarker(MapNode node) {
    return Container(
      width: 48,
      height: 48,
      decoration: BoxDecoration(
        color: _getNodeColor(node),
        shape: BoxShape.circle,
        border: Border.all(
          color: node.isCurrent ? Colors.gold : Colors.black54,
          width: node.isCurrent ? 3 : 1,
        ),
        boxShadow: [
          if (node.isCurrent) 
            BoxShadow(color: Colors.gold.withOpacity(0.5), blurRadius: 10)
        ],
      ),
      child: Center(
        child: Text(node.icon, style: TextStyle(fontSize: 24)),
      ),
    );
  }
  
  Color _getNodeColor(MapNode node) {
    if (!node.isVisible) return Colors.grey.shade800;  // Fog of war
    if (!node.isVisited) return Colors.grey.shade600;  // Unexplored
    
    switch (node.dangerLevel) {
      case 'deadly': return Colors.red.shade900;
      case 'threatening': return Colors.orange.shade800;
      case 'uneasy': return Colors.yellow.shade800;
      default: return Colors.green.shade800;
    }
  }
}
```

**Map Features:**
- **Fog of War**: Unvisited locations are greyed out
- **Current Location**: Gold ring + glow effect
- **Danger Indicators**: Color coding (green/yellow/orange/red)
- **Pinch to Zoom**: Scale from 0.5x to 3x
- **Pan/Drag**: Move map around
- **Tap to Travel**: Click visible adjacent node to auto-travel
- **Hover Tooltip**: Shows location name, description, danger level
- **Connection Lines**: Show paths between locations
- **Locked Exits**: Dashed lines with lock icon

---

#### 4.5.6 Implementation Steps

**Step 1 - Backend Data Structures (Python):**
```
[ ] Add map fields to Location dataclass (map_x, map_y, map_icon, map_region)
[ ] Create MapNode dataclass in scenario.py
[ ] Create MapConnection dataclass in scenario.py  
[ ] Create MapRegion dataclass in scenario.py
[ ] Create WorldMap class with build/update methods
[ ] Add WorldMap to game state (for API)
[ ] Update to_dict/from_dict for persistence
```

**Step 2 - Scenario Map Data:**
```
[ ] Add map coordinates to all Goblin Cave locations
[ ] Define Goblin Cave regions (village, forest, cave)
[ ] Assign icons to each location
[ ] Test map generation from locations
```

**Step 3 - API Endpoints (when backend ready):**
```
[ ] GET /api/map - Returns current map state
[ ] GET /api/map/nodes - Returns visible nodes only
[ ] POST /api/travel/{location_id} - Travel via map click
[ ] WebSocket: map_update event for real-time sync
```

**Step 4 - Flutter Map Widget:**
```
[ ] Create WorldMapWidget component
[ ] Implement MapPainter for custom rendering
[ ] Add zoom/pan gesture handlers
[ ] Implement node tap-to-travel
[ ] Add hover tooltip overlay
[ ] Implement connection line rendering
[ ] Add region background tinting
[ ] Theme integration (dark/light modes)
```

**Step 5 - Integration:**
```
[ ] Map panel in main game screen (side panel or overlay)
[ ] Toggle map visibility (keyboard: M, button: 🗺️)
[ ] Sync map state on location change
[ ] Update fog of war when visiting new locations
[ ] Show travel confirmation before moving
```

---

#### 4.5.7 Success Criteria

- [ ] Map displays all scenario locations with correct positions
- [ ] Connections between locations are visible as lines
- [ ] Current location has distinct visual marker (gold ring)
- [ ] Visited locations are full color, unvisited are greyed
- [ ] Fog of war hides unexplored distant areas
- [ ] Clicking adjacent location triggers travel
- [ ] Locked exits shown with dashed line + lock icon
- [ ] Danger levels indicated by node color
- [ ] Zoom and pan work smoothly on all platforms
- [ ] Map state persists with save/load
- [ ] Regions provide visual grouping with tinted backgrounds
- [ ] Works on mobile (touch), tablet, and desktop (mouse)

---

### Phase 5: Advanced AI DM Features ⬜ Not Started
**Goal:** Smarter, more immersive AI dungeon master

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 5.1 | Context Memory | AI remembers story events and player decisions | ⬜ |
| 5.2 | Dynamic Story Generation | AI creates encounters based on player actions | ⬜ |
| 5.3 | Rule Enforcement | AI validates actions against D&D rules | ⬜ |
| 5.4 | Faction System | Track relationships with different groups | ⬜ |
| 5.5 | Consequence Engine | Past choices affect future encounters | ⬜ |

**Context Memory Features (5.1):**
```
Memory System:
- Short-term: Last 10 exchanges (current)
- Long-term: Key events stored in game_state
- Semantic: Summarize past sessions for context

Key Events to Remember:
- NPCs met and relationships
- Quests accepted/completed
- Major choices made
- Enemies killed or spared
- Items acquired/lost

AI Prompt Enhancement:
"MEMORY: Player spared the captured goblin. Player chose stealth over combat.
Player has a reputation for mercy. Consider this in NPC reactions."
```

**Faction System Features (5.4):**
```
Factions:
- Village of Willowbrook (good)
- Goblin Clan (hostile, can become neutral)
- Forest Druids (neutral, can become ally)
- Thieves Guild (hidden, discoverable)

Reputation:
- Actions affect faction rep (-100 to +100)
- Killing goblins: -5 Goblin, +2 Village
- Sparing goblins: +5 Goblin, -2 Village
- Helping druid: +10 Druids

Effects:
- Shop prices affected by rep
- Quest availability
- NPC hostility/friendliness
- Hidden content unlocked at high rep
```

**Success Criteria:**
- [ ] AI references past events in narration
- [ ] Encounters feel unique and reactive

- [ ] Invalid actions are caught and explained

---

### Phase 5: Backend API & Community Modding 🔄 In Progress
**Goal:** Create API backend to support mobile app AND enable community campaign creation

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 5.0 | **DM Engine Extraction** | **Shared dm_engine.py module for all interfaces** | ✅ |
| 5.1 | REST API Setup | Flask backend for game logic | ✅ |
| 5.2 | Scenario Folder System | Organize scenarios in modular folder structure | ⬜ |
| 5.3 | Community Campaigns | Local modding support, campaign import/export | ⬜ |
| 5.4 | Authentication | User accounts, login, session management | ⬜ |
| 5.5 | Cloud Save | Database for persistent game saves | ⬜ |
| 5.6 | API Endpoints | Chat, character, inventory, combat endpoints | ✅ |
| 5.7 | Campaign Workshop | Cloud-hosted community campaign repository | ⬜ |

---

## 🏗️ ARCHITECTURE: Shared DM Engine (CRITICAL)

**The correct multiplatform architecture:**

```
                    dm_engine.py
                    (Pure Logic)
                         │
                         ▼
                  api_server.py      ← Production interface
                  (Flask REST)
                         │
           ┌─────────────┴─────────────┐
           │                           │
           ▼                           ▼
       React Web                   Godot/Flutter
       (localhost:3000)            (future clients)
```

**dm_engine.py contains (single source of truth):**
- `DM_SYSTEM_PROMPT` - Complete AI ruleset (~9600 chars)
- `build_full_dm_context()` - Constructs prompts with scenario/NPC/quest context
- `parse_roll_request()` - Extracts [ROLL: Skill DC X] tags
- `parse_combat_trigger()` - Extracts [COMBAT: enemy1, enemy2] tags  
- `parse_item_rewards()` - Extracts [ITEM: item_name] tags
- `parse_gold_rewards()` - Extracts [GOLD: amount] tags
- `parse_xp_rewards()` - Extracts [XP: amount | reason] tags
- `parse_buy_transactions()` - Extracts [BUY: item, price] tags
- `apply_rewards()` - Applies items/gold/XP to character
- `roll_skill_check()` - D20 + modifiers

**Why this matters:**
1. **Feature parity** - All interfaces get the same DM behavior
2. **No drift** - One change updates everything
3. **Testable** - Pure functions, no I/O side effects
4. **Extensible** - New frontends just import dm_engine

**Current Status:**
- `src/api_server.py` → ✅ Imports from dm_engine (production)
- `backup/legacy/game.py` → 📦 Archived terminal version (no longer maintained)

---

## 🛠️ DEVELOPMENT METHODOLOGY: Core-First Development

**Core Philosophy: Build features in core modules, test with pytest, expose via API to frontend.**

This project follows the "Core + Shell" pattern (also known as Hexagonal Architecture):

```
┌────────────────────────────────────────────────────────────────┐
│                      DEVELOPMENT FLOW                          │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. BUILD          2. TEST           3. EXPOSE      4. DISPLAY │
│  ─────────         ──────────        ─────────      ────────── │
│  dm_engine.py  →   pytest tests  →   api_server  →  React UI   │
│  character.py      (unit tests)      (Flask)        (frontend) │
│  combat.py                                                      │
│  inventory.py                                                   │
│                                                                 │
│  [Pure Logic]      [Fast Debug]      [REST API]    [Pretty UI] │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### Why This Works

| Benefit | Explanation |
|---------|-------------|
| **Faster Iteration** | Terminal: Type → Instant feedback (3-5x faster than UI debugging) |
| **Easier Debugging** | See raw DM output without React state, network, or SSE layers |
| **Forced Clean APIs** | If terminal can do it, API can expose it cleanly |
| **Single Source of Truth** | Logic lives in dm_engine.py, tested once, used everywhere |
| **Feature Parity** | All interfaces (terminal, web, mobile) get identical behavior |

### Development Workflow

**When adding a new feature:**

1. **Implement in Core** (`src/dm_engine.py`, `src/character.py`, etc.)
   - Write pure functions with no I/O dependencies
   - Example: `Character.roll_stat()`, `parse_xp_rewards()`

2. **Write Unit Tests** (`tests/test_*.py`)
   - Test the core logic in isolation
   - Run with pytest for fast feedback
   - Example: `test_quest_hooks.py`, `test_character.py`

3. **Expose via API** (`src/api_server.py`)
   - Create/update endpoint that uses the core logic
   - Handle serialization (e.g., `_serialize_character()` for enums)
   - Add proper error handling

4. **Display in Frontend** (`frontend/option1-react/`)
   - Call the API endpoint
   - Update state store (Zustand)
   - Render in React components

### Examples in Practice

| Feature | Core Module | Unit Tests | API Endpoint | Frontend |
|---------|-------------|------------|--------------|----------|
| Stat rolling | `Character.roll_stat()` | `test_character.py` | `POST /game/start` | CharacterCreation.jsx |
| Combat | `combat.py` | `test_combat.py` | `POST /game/action` | GameScreen.jsx |
| XP rewards | `dm_engine.parse_xp_rewards()` | `test_xp_system.py` | SSE streaming | XP bar in sidebar |
| Inventory | `inventory.py` | `test_inventory.py` | `game_state.inventory` | Inventory modal |
| Quest tracking | `quest.py` | `test_quest_hooks.py` | `game_state.quest_log` | Quest Journal modal |

### Testing Strategy

```
dm_engine.py  ←── Unit tests (tests/test_*.py) - Fast, reliable
     │
api_server.py ←── Integration tests (tests/test_api_integration.py)
     │
React frontend ←── Uses same tested API (no separate testing needed)
```

**Key Insight:** By testing the core and API thoroughly, the frontend inherits correctness automatically. The frontend is purely a display layer—it just shows what the API returns.

### Benefits of This Approach

1. **No Logic Duplication** - Frontend never recalculates stats, HP, or game rules
2. **Consistent Behavior** - React, Flutter, Godot all behave identically
3. **Easy Onboarding** - New devs can run tests to understand the system
4. **Safe Refactoring** - Change core logic, all interfaces update automatically
5. **Fast Iteration** - pytest runs in seconds, no UI needed

---

**Scenario Folder System Details (5.2):**
```
Structure (Pure Python):
src/
├── scenarios/
│   ├── __init__.py              # Scenario registry & loader
│   │
│   ├── goblin_menace/           # Campaign folder
│   │   ├── __init__.py          # Campaign registration
│   │   ├── chapter_1.py         # Goblin Cave (current scenario)
│   │   ├── chapter_2.py         # Return to the Village
│   │   └── chapter_3.py         # The Goblin King
│   │
│   └── haunted_manor/           # Another campaign
│       ├── __init__.py
│       ├── chapter_1.py         # Arrival at the Manor
│       └── chapter_2.py         # The Crypt Below

Benefits:
- Full Python power (procedural generation, conditionals)
- IDE autocomplete and type checking
- Multi-chapter campaigns with interconnected stories
- Easy to navigate (1 file = 1 chapter)
- Chapters can share NPCs, items, locations across files

Registry Pattern:
- Each campaign __init__.py registers its chapters
- ScenarioManager loads from registry
- Chapters can reference each other for story continuity

Migration Plan:
1. Create src/scenarios/ folder structure
2. Move goblin_cave from scenario.py to scenarios/goblin_menace/
3. Add scenario registry in __init__.py
4. Update ScenarioManager to use registry
5. Add campaign selection menu to game startup
```

**Community Campaign System (5.3):**
```
Priority 1 - JSON Schema Design: ⬜ NOT STARTED
  [ ] Define campaign.json schema:
      {
        "schema_version": "1.0",
        "id": "haunted_manor",
        "name": "The Haunted Manor",
        "author": "user123",
        "version": "1.2.0",
        "description": "A gothic horror adventure",
        "difficulty": "medium",
        "estimated_duration": "2-3 hours",
        "episodes": [...],
        "persistent_flags": [...],
        "required_base_version": "2.0.0",
        "tags": ["horror", "gothic", "mystery"]
      }
  [ ] Define episode.json schema (locations, scenes, npcs, items)
  [ ] JSON validation with helpful error messages
  [ ] Export Goblin Cave to JSON as reference implementation

Priority 2 - Local Modding Support: ⬜ NOT STARTED
  [ ] /data/campaigns/community/ folder scanning on startup
  [ ] Campaign Browser UI shows installed campaigns
  [ ] Import .zip campaign package (extract + validate)
  [ ] Schema validation on import with user-friendly errors
  [ ] "Invalid Campaign" graceful handling (don't crash)

Priority 3 - Creator Tools: ⬜ NOT STARTED
  [ ] Campaign export tool (Python → JSON)
  [ ] Minimal validation CLI (checks completeness)
  [ ] CAMPAIGN_TEMPLATE.json with documentation
  [ ] Debug mode for testing custom campaigns
  [ ] 🔶 OPEN: In-game campaign editor (future Flutter feature?)
```

**Campaign Workshop (5.7) - Future Cloud Feature:**
```
Priority 1 - Workshop Backend: ⬜ NOT STARTED
  [ ] Campaign upload endpoint (authenticated)
  [ ] Campaign download/search endpoint
  [ ] Version management (updates)
  [ ] Rating/review system
  [ ] Download counters

Priority 2 - Workshop UI: ⬜ NOT STARTED
  [ ] Browse community campaigns in-app
  [ ] One-click install/update
  [ ] Preview before install
  [ ] "Installed" indicator
  [ ] Sort by: Popular, New, Rating

Priority 3 - Moderation & Safety: ⬜ NOT STARTED
  [ ] JSON-only format (no code execution)
  [ ] Community reporting for inappropriate content
  [ ] "Verified Creator" badge for trusted modders
  [ ] Minimum content requirements (1+ episode, 3+ locations)
  [ ] 🔶 OPEN: Automated content scanning?
  [ ] 🔶 OPEN: Copyright/DMCA process?
```

**Campaign Browser UI Mockup:**
```
┌─────────────────────────────────────────────────────────────────┐
│ 📚 CAMPAIGN LIBRARY                           [Search: _____]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 🏆 OFFICIAL CAMPAIGNS                                           │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ⚔️ The Goblin Menace [3 Episodes]           ★★★☆☆ (Medium)  │ │
│ │    Rescue a farmer's daughter from goblins                  │ │
│ │    [Continue Episode 2] [Restart]                           │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ 🌍 COMMUNITY CAMPAIGNS                        [Sort: Popular ▼] │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🏚️ The Haunted Manor by user123             ★★★★★ (Hard)    │ │
│ │    Gothic horror. 2-3 hours. 1.2k downloads                 │ │
│ │    [Install] [Preview]                                      │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ 🐉 Dragon's Hoard by dragonlord             ★★★★☆ (Easy)    │ │
│ │    Classic treasure hunt. 1 hour. 856 downloads             │ │
│ │    [Installed ✓] [Play] [Update Available]                  │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ 📁 MY CAMPAIGNS                                                 │
│    [+ Create New Campaign]  [Import from File]                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Safety & Moderation Concerns:**
```
┌────────────────────────────────────────────────────────────────┐
│ Concern                │ Solution                              │
├────────────────────────┼───────────────────────────────────────┤
│ Malicious code         │ JSON-only (no code execution)         │
│ Inappropriate text     │ Community reporting + keyword scan    │
│ Copyright issues       │ Terms of service, DMCA process        │
│ Breaking changes       │ required_base_version field           │
│ Quality control        │ Rating system, "Verified" badge       │
│ Spam/low-effort        │ Minimum content requirements          │
└────────────────────────────────────────────────────────────────┘
```

**🔶 OPEN QUESTIONS for Phase 5:**
```
- In-game campaign editor vs external JSON editing?
- Revenue share with creators (Steam Workshop style)?
- Premium vs free community campaigns?
- Hot-reload campaigns without restart?
- Versioning/compatibility when base game updates?
- Offline-first or cloud-first for campaign storage?
```

**Success Criteria:**
- [ ] API accepts game commands and returns responses
- [ ] Content stored in JSON files
- [ ] Users can register and login
- [ ] Game state syncs between devices
- [ ] Community campaigns can be installed locally
- [ ] Campaign Browser shows official + community campaigns
- [ ] Workshop enables one-click install (future)

---

### Phase 6: Flutter App ⬜ Not Started
**Goal:** Cross-platform app for iOS, Android, Web, and Desktop

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 6.1 | Flutter Project Setup | Initialize Flutter project, dependencies | ⬜ |
| 6.2 | Theme System | 6 themes (Dark Fantasy, Light Parchment, Forest Green, Dungeon Stone, Royal Purple, Blood Crimson) + system default, theme persistence | ⬜ |
| 6.3 | Chat Interface | Text input, scrollable message history, typing indicator, styled bubbles | ⬜ |
| 6.4 | Character Screen | View stats, abilities, HP, AC in D&D-style layout | ⬜ |
| 6.5 | Inventory Screen | Equipped items, backpack, gold tracker | ⬜ |
| 6.6 | Dice Roller UI | Visual dice rolling animations, modifier support | ⬜ |
| 6.7 | Settings Screen | Theme selector gallery, save/load, API config | ⬜ |
| 6.8 | Push Notifications | Game events, session reminders | ⬜ |
| 6.9 | Offline Mode | Queue actions when offline | ⬜ |
| 6.10 | Web Build | Deploy to web hosting | ⬜ |
| 6.11 | Desktop Build | Windows/Mac/Linux packages | ⬜ |

**Success Criteria:**
- [ ] App runs on iOS and Android
- [ ] App runs in web browser
- [ ] 7 theme options with smooth transitions
- [ ] Theme persists between sessions
- [ ] Seamless gameplay experience across platforms
- [ ] Character management on the go
- [ ] Visual polish (themes, animations)

**Target Platforms:**
- 📱 iOS (App Store)
- 📱 Android (Play Store)
- 🌐 Web (Browser)
- 🖥️ Windows (Downloadable)
- 🖥️ macOS (Downloadable)
- 🐧 Linux (Downloadable)

**Design Documentation:**
- See [UI_DESIGN_SPEC.md](UI_DESIGN_SPEC.md) for complete UI/UX specifications
- See [THEME_SYSTEM_SPEC.md](THEME_SYSTEM_SPEC.md) for DLC-ready theme architecture

---

### Phase 7: Theme Store & Monetization ⬜ Not Started
**Goal:** Enable theme purchases as DLC

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 7.1 | Theme Registry | Central system to manage all themes | ⬜ |
| 7.2 | Unlock System | Track which themes user owns locally | ⬜ |
| 7.3 | Theme Store UI | Browse, preview, purchase themes | ⬜ |
| 7.4 | In-App Purchases | Google Play & App Store integration | ⬜ |
| 7.5 | Backend Sync | Cross-device unlock status | ⬜ |
| 7.6 | Purchase Verification | Validate purchases server-side | ⬜ |
| 7.7 | Theme Packs DLC | Nature, Dungeon, Arcane, Gothic packs | ⬜ |

**Success Criteria:**
- [ ] Users can browse all themes (locked + unlocked)
- [ ] Preview themes before buying
- [ ] Purchase themes via app stores
- [ ] Purchases sync across devices
- [ ] Free users get 2 core themes

**Pricing Strategy:**
- Core Pack (FREE): Dark Fantasy, Light Parchment
- Small Packs ($1.99): 3-4 themes each
- Large Packs ($2.99): 4-5 themes + special effects
- Premium Bundle ($7.99): All themes

**Technical Documentation:**
- See [THEME_SYSTEM_SPEC.md](THEME_SYSTEM_SPEC.md) for complete DLC architecture

---

## Technical Stack (Proposed)

| Component | Technology | Notes |
|-----------|------------|-------|
| Language (Backend) | Python 3.x | API and game logic |
| Language (Frontend) | Dart (Flutter) | Cross-platform UI |
| AI Provider | Google Gemini (GenAI) | gemini-2.0-flash default |
| Data Storage | JSON files → PostgreSQL | JSON for local, DB for cloud |
| Backend API | FastAPI | Fast, async, auto-docs |
| Frontend Framework | Flutter | iOS, Android, Web, Desktop |
| Authentication | JWT + OAuth | Secure user sessions |
| Cloud Hosting | TBD (Railway/Render/AWS) | For API + database |
| Config | .env file | All AI/system config |

---

## Testing Log

| Date | Phase | Test | Result | Notes |
|------|-------|------|--------|-------|
| 2024-12-15 | 1.1 | Simple Chat Loop | ✅ Pass | Gemini 2.0 Flash working, conversation flows naturally |

---

## Current Focus

**Current Phase:** 3.2.1 (Location & Navigation) + 3.2.2 (Balance Improvements) + 3.6 (Item Utility)

**Recently Completed:**
- ✅ Fixed loot drops with class-appropriate weapons
- ✅ Quality tiers (Common/Uncommon/Rare/Epic)
- ✅ Comprehensive scenario documentation
- ✅ SCENARIO_TEMPLATE.py for scenario authors
- ✅ **Priority 5: Conditional Exits** - Locked doors with key requirements!
- ✅ **SkillCheckOption System** - NPCs have persuasion/skill check opportunities
- ✅ **Chief Grotnak NPC** - Boss NPC with negotiation options
- ✅ **NPC Location Fixes** - Barkeep correctly describes NPC locations
- ✅ **Phase 3.6 Quick Wins** - Item utility improvements (6/8 complete)
  - ✅ Goblin Ear Bounty Quest ("Thin the Herd") - 5 ears → 25g + 50xp
  - ✅ Gold Pouch Auto-Convert - Adds gold on pickup, not item
  - ✅ Mysterious Key → Hidden Hollow - OR condition for secret_cave
  - ✅ Ancient Scroll → Secret Tunnel - Description reveals location
  - ✅ Lockpicks → Cage Escape (DC 12 Sleight of Hand, consumes lockpicks)
  - ✅ Poison Vial Combat Bonus (+1d4 damage, consumed after hit)
  - ✅ Torch Darkness Mechanics (Required in dark areas, disadvantage without)
  - ✅ Rope Utility (Athletics DC 14 cage escape)

**🎉 Phase 3.6 Item Utility System: COMPLETE (8/8 features)**
- ✅ **Phase 4.5: World Map UI** - React WorldMap.jsx with visual map, click-to-travel
- ✅ **Phase 3.3.7: Party System** - 72 tests, 3 recruitable NPCs, class abilities

**Next Priority Actions:**
1. **Phase 3.4: Moral Choices & Consequences** - Branching dialogue, multiple endings
2. **Phase 3.5: Campaign System** - Episode chaining, persistent flags
3. **Phase 5.2: Scenario Folder System** - Community modding support

**Remaining Party System Work:**
- Party member auto-actions in combat (AI-controlled)
- Flanking bonus implementation (+2 attack)
- Combined attacks display

---

## 📋 Low-Risk Work Queue (Safe to Implement)

Items that are **additive** and unlikely to break existing functionality:

### 🟢 Quick Wins (1-2 hours each)
| Task | Risk | Status | Notes |
|------|------|--------|-------|
| Add Party panel to React frontend | 🟢 Low | ✅ DONE | Already in GameScreen.jsx modal |
| Add secret cave location with perception check | 🟢 Low | ✅ DONE | 2 exist: secret_cave, treasure_nook |
| Add LocationAtmosphere dataclass | 🟢 Low | ✅ DONE | scenario.py lines 139-220 |
| Add 'reputation' API endpoint | 🟢 Low | ✅ DONE | GET /api/reputation added |

### 🟡 Medium Tasks (2-4 hours each)
| Task | Risk | Notes |
|------|------|------|
| LocationAtmosphere for all Goblin Cave locations | 🟡 Med | Update scenario.py |
| AI prompt includes disposition level | 🟡 Med | Update dm_engine.py |
| Add Party display in GameScreen sidebar | 🟡 Med | Frontend state changes |

### 🟠 Larger Features (4+ hours)
| Task | Risk | Notes |
|------|------|-------|
| Phase 3.4.1 Alternative Resolutions | 🟠 Med | New dialogue paths |
| Phase 3.5 Campaign dataclass | 🟠 Med | Foundation for episodes |

---

## RPG Feature Checklist

Track essential RPG features across phases:

| Feature | Phase | Status | Notes |
|---------|-------|--------|-------|
| **Core Combat** | | | |
| Turn-based combat | 2.3 | ✅ | Initiative, attack/defend |
| Multi-enemy encounters | 2.5.1 | ✅ | Group initiative |
| Surprise rounds | 2.5.2 | ✅ | Advantage on first attack |
| Boss encounters | 3.2.2 | ✅ | Scaled HP, better loot |
| **Progression** | | | |
| XP from combat | 2.6 | ✅ | Enemy-based rewards |
| Objective XP | 3.2.2 | ✅ | Quest milestone rewards |
| Level up (cap 5) | 2.6 | ✅ | HP, ability increases |
| **Loot & Items** | | | |
| Fixed drops | 3.2.2 | ✅ | Predictable loot |
| Class weapons | 3.2.2 | ✅ | Rogues get daggers, etc |
| Quality tiers | 3.2.2 | ✅ | Common → Epic |
| Gold economy | 2.5 | ✅ | Track gold |
| **Exploration** | | | |
| Multi-location maps | 3.2.1 | ✅ | 18+ locations |
| Scene transitions | 3.2.1 | ✅ | Event-driven |
| Locked doors | 3.2.1 | ✅ | ExitCondition, storage_key |
| Cardinal aliases | 3.2.1 | ✅ | n/s/e/w shortcuts |
| Random encounters | 3.2.1 | ✅ | Wolf, spider encounters |
| Secret areas | 3.2.1 | ✅ | 2 hidden locations with skill checks |
| **World Map UI** | | | |
| Visual map display | 4.5 | ✅ | React WorldMap.jsx |
| Click-to-travel | 4.5 | ✅ | One-click movement |
| Fog of war | 4.5 | ✅ | Hidden/visited locations |
| Current location marker | 4.5 | ✅ | Gold ring + animation |
| Connection lines | 4.5 | ✅ | Shows paths between |
| **NPCs & Dialogue** | | | |
| NPC definitions | 3.3.1 | ✅ | NPC dataclass with roles |
| Dialogue trees | 3.3.2 | ✅ | AI-enhanced with DM |
| Merchants/shops | 3.3.3 | ✅ | Shop module with haggling |
| Quest givers | 3.3.4 | ✅ | Quest system complete |
| **Party System** | | | |
| Party members | 3.3.7 | ✅ | Recruit companions |
| Recruitment checks | 3.3.7 | ✅ | Skill/item/objective |
| Party combat | 3.3.7 | ✅ | Turn order, bonuses |
| Special abilities | 3.3.7 | ✅ | Per-class unique skill |
| **Player Agency** | | | |
| Moral choices | 3.4.1 | ⬜ | Consequences |
| Alternative resolutions | 3.4.3 | ⬜ | Non-combat options |
| Multiple endings | 3.4.4 | ⬜ | 3+ per scenario |
| Faction reputation | 4.4 | ⬜ | Affects NPCs |

---

## Notes & Decisions

- Starting small to avoid past failures
- Each phase must be tested before moving to next
- Document learnings and issues in Testing Log

---
