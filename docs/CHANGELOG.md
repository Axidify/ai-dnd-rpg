# Changelog

All notable changes to the AI D&D Text RPG project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- **SkillCheckOption System** - Comprehensive skill check framework for NPCs!
  - New `SkillCheckOption` dataclass in `npc.py` with:
    * `id`, `skill`, `dc` - Check identification and difficulty
    * `description` - Player-facing prompt for the action
    * `success_effect` - Effect on success (e.g., "gold:25", "flag:paid_upfront", "disposition:+15")
    * `success_dialogue` / `failure_dialogue` - NPC response based on outcome
    * `one_time` / `attempted` - Track repeatable vs one-shot checks
    * `requires_disposition` - Minimum disposition needed to attempt
  - NPC helper methods: `get_available_skill_checks()`, `get_skill_check_option()`, `mark_skill_check_attempted()`, `has_available_skill_checks()`
  - Full serialization support in `NPC.to_dict()` / `from_dict()`
  - Integrated into `get_dm_context()` for AI visibility

- **Bram Persuasion Options** - Quest giver now supports negotiation!
  - `upfront_payment` (Persuasion DC 14): Get 25g advance before mission
  - `better_reward` (Persuasion DC 16): Negotiate 75g total reward

- **Barkeep Intel Options** - Get information through persuasion!
  - `secret_intel` (Persuasion DC 10): Learn about hidden tunnel entrance
  - `free_drink` (Persuasion DC 8): Talk your way into a free ale

- **Marcus the Mercenary Options** - Alternative recruitment paths!
  - `appeal_to_honor` (Persuasion DC 15): Reduce recruitment cost to 10g
  - `impress_with_knowledge` (History DC 14): Recognize his military unit for +15 disposition

- **Elira the Ranger Options** - Multiple ways to connect!
  - `share_tracking_knowledge` (Survival DC 12): Demonstrate tracking skills for +15 disposition
  - `empathize_with_loss` (Persuasion DC 12): Bond over shared loss for +10 disposition
  - `notice_brother_truth` (Insight DC 16): Learn the truth about her brother's death

- **Shade the Rogue Options** - Earn the assassin's trust!
  - `prove_stealth` (Stealth DC 12): Demonstrate stealth ability for +20 disposition
  - `read_intentions` (Insight DC 16): Discover Shade is an assassin

- **Lily (Prisoner) Options** - Learn rescue secrets!
  - `encourage_escape_help` (Persuasion DC 8): Learn about loosened cage bar
  - `learn_deep_secret` (Insight DC 12): Discover the "Old One" in deep tunnels

- **Chief Grotnak** - NEW BOSS NPC with negotiation options!
  - Full NPC with cunning personality and unique dialogue
  - `intimidate_release` (Intimidation DC 16): Force Lily's release without combat
  - `deceive_distraction` (Deception DC 18): Lie about reinforcements
  - `negotiate_ransom` (Persuasion DC 14): Pay 50g for peaceful resolution

- **Gavin the Blacksmith Options** - Shop and lore interactions!
  - `haggle_discount` (Persuasion DC 12): Get 10% off purchases
  - `soldier_bond` (History DC 14): Recognize insignia for +20 disposition
  - `masterwork_reveal` (Persuasion DC 18): Learn about hidden masterwork blade

- **Phase 3.6 Item Utility Quick Wins** - Unused items now have mechanical purpose!
  - **Gold Pouch Auto-Convert** - Gold pouch items now automatically convert to gold on pickup
    * Uses item's `value` field (50g for gold_pouch, 15g for small_gold_pouch)
    * Added in `dm_engine.py` `apply_rewards()` function
  - **"Thin the Herd" Bounty Quest** - New side quest for goblin_ear collection!
    * Collect 5 goblin ears → 25g + 50 XP
    * Given by Barkeep (village bounty board)
    * Prerequisites: None (available from start)
  - **Ancient Scroll Tunnel Revelation** - Updated item description and effect
    * Now states scroll reveals secret tunnel entrance location
    * Effect field: "Reading this scroll reveals the secret tunnel entrance"
  - **Mysterious Key Usage** - Key now opens Hidden Hollow location!
    * Added OR condition support to `check_discovery()` method
    * Secret cave discoverable via: Perception DC 14 OR possessing mysterious_key
    * New `_check_single_condition()` helper for OR logic parsing

- **Phase 3.6 Integration Tests** - Comprehensive gameplay tests for item utility!
  * 11 new tests in `tests/test_phase36_quick_wins.py`
  * Tests gold pouch auto-convert (3 tests)
  * Tests goblin ear bounty quest (3 tests)
  * Tests mysterious key discovery with OR logic (3 tests)
  * Tests ancient scroll description and effect (2 tests)
  * Total test count: 918 passing

- **Phase 3.6.5 Lockpicks Cage Escape** - Lockpicks now provide alternative rescue path!
  * Added `requires_item` and `consumes_item` fields to SkillCheckOption dataclass
  * New `pick_cage_lock` skill check on Lily NPC (Sleight of Hand DC 12)
  * Requires lockpicks item, consumed on attempt
  * Success sets `freed_lily_lockpicks` flag
  * Updated lockpicks item description with "use for Sleight of Hand checks"
  * Full serialization support in to_dict/from_dict

- **Phase 3.6.6 Poison Vial Combat Bonus** - Poison now enhances next attack!
  * New `weapon_poisoned` field on Character dataclass
  * Using Poison Vial via `use_item()` sets weapon_poisoned=True
  * Modified `roll_damage()` adds +1d4 poison damage when poisoned
  * Poison consumed after one hit (single-use buff)
  * Cannot double-apply poison (returns error if already poisoned)
  * Format damage result shows poison damage separately
  * Serialization support for save/load persistence

- **Phase 3.6.5/3.6.6 Integration Tests** - Tests for lockpicks and poison!
  * 9 new tests added to `test_phase36_quick_wins.py`
  * Lockpicks: Lily skill check, SkillCheckOption fields, item description
  * Poison: Character field, use_item application, damage bonus, consumption
  * Total test count: 927 passing

### Fixed
- **Barkeep NPC Location Dialogue** - Barkeep no longer implies all recruitable NPCs are in tavern!
  - Updated DM system prompt to include NPC locations with recruitable list
  - Added explicit warning: "NPCs can only be interacted with at their actual locations"
  - Added `about_help` dialogue to barkeep that correctly says Marcus is here but Elira is in the forest
  - AI now knows: Marcus → TAVERN, Elira → FOREST, Shade → CAVE

- **NPC Location Filtering** - NPCs now appear only at their assigned locations!
  - Fixed bug where all recruitable NPCs (Marcus, Elira, Shade) appeared in tavern perception checks
  - `build_npc_context()` now accepts `location_npc_ids` parameter
  - NPCs are marked as "PRESENT AT THIS LOCATION" or "NOT HERE" in AI context
  - Added NPCs to their correct `Location.npcs` lists in scenario:
    * Marcus → tavern_main
    * Elira → forest_clearing  
    * Shade → goblin_camp_shadows
  - Maintains awareness of all NPCs while correctly showing who's present

- **System-Controlled XP Rewards** - XP is now consistent and predictable!
  - Removed "Give the [XP: ...] reward" instructions from scene dm_instructions
  - AI DM no longer randomly generates XP amounts for quests/objectives
  - All quest/objective XP comes from `Scene.objective_xp` field
  - Combat XP comes from `Enemy.xp_reward` field
  - Prevents double XP and inconsistent reward amounts (was 25-50, now always 15)

### Added
- **SCENARIO_REFERENCE.md** - Comprehensive user-readable scenario documentation!
  - Complete location details with NPCs, items, and connections
  - All NPC profiles with recruitment requirements
  - Full item catalog with shops and prices
  - Quest details with objectives and rewards
  - XP reward breakdown by source type
  - ASCII art map of Goblin Cave scenario
  - Located at `docs/SCENARIO_REFERENCE.md`

- **Exceptional Roleplay XP Guidelines** - Clear criteria for AI discretionary XP!
  - Detailed examples in DM_SYSTEM_PROMPT for when to award XP
  - Three categories: Creative Puzzle Solving, Brilliant Negotiation, Unexpected Ingenuity
  - Explicit ✅ AWARD and ❌ DON'T AWARD examples
  - Exclusion list: No XP for quests, combat, normal dialogue, following obvious paths
  - Maximum 25 XP per exceptional action

### Improved
- **DM System Prompt XP Guidelines** - More explicit XP rules for AI DM
  - Added "WHEN TO AWARD XP" section with specific criteria
  - Added "WHEN NOT TO AWARD XP" exclusion list
  - Added real gameplay examples with ✅/❌ markers
  - Prevents AI from awarding XP for routine actions

### Documentation
- Updated `DEVELOPER_GUIDE.md` with system-controlled XP explanation
- Updated `DEVELOPMENT_PLAN.md` Leveling System section with XP sources
- Added exceptional roleplay criteria tables to documentation

---

### Security
- **Comprehensive Security Testing (125 Tests Passing)** - Full hostile player testing complete!
  - 5 testing rounds covering 125 unique security test cases
  - All 16 identified vulnerabilities have been fixed
  - Categories: Input validation, prompt injection, state manipulation, API abuse, edge cases
  - Extended testing: Combat exploits, save/load manipulation, inventory exploits, party/NPC abuse
  - Advanced testing: Session hijacking, header injection, resource exhaustion, concurrent attacks
  
- **Input Validation Hardening** - Stricter input validation across all endpoints!
  - Character name validation: Required, max 50 characters, trimmed
  - Action type validation: Must be string, prevents 500 errors
  - Quantity validation: Positive integers only, max 99
  - Save name sanitization: Path traversal blocked, dangerous chars removed
  - Dice notation validation: Zero-sided dice rejected, negative counts blocked

- **Session Security** - Improved session management!
  - Sessions now expire after 60 minutes of inactivity
  - Background cleanup thread runs every 5 minutes
  - `/api/game/end` endpoint for explicit session termination
  - `/api/sessions/stats` endpoint for monitoring session count
  - UUID isolation prevents session hijacking

- **Combat Exploit Fixes** - Combat system hardened!
  - Travel blocked during active combat
  - Combat endpoints properly validate combat state
  - "Not in combat" error for attack/flee/defend when not in combat

### Fixed
- **Character.from_dict() Method** - Save/load now works correctly!
  - Added missing classmethod to reconstruct Character from saved data
  - Cross-session save loading now functional
  
- **Party.is_full Property Bug** - Recruitment endpoint fixed!
  - Changed from `is_full()` method call to `is_full` property access
  
- **Shop Buy API** - Critical bug fix!
  - Fixed wrong function signature that caused all buy operations to fail
  - Proper parameter order: character, shop, item_id, quantity, npc_disposition

- **Quest System Fixes** - Multiple quest-related fixes!
  - Quest ID type validation added
  - get_completed_quests method implemented
  - Quest list error handling improved

- **Dice System Fix** - Zero-sided dice validation!
  - Added check: "Dice must have at least 1 side"

- **Emoji Encoding (Mojibake Fix)** - Emojis now display correctly!
  - Fixed double-encoded UTF-8 emojis appearing as garbled text (e.g., `ðŸ"` instead of `📍`)
  - Root cause: Source file `api_server.py` had corrupted emoji bytes
  - Used `ftfy` library to detect and fix mojibake in Python source files
  - Added `app.json.ensure_ascii = False` to Flask for proper JSON UTF-8 output
  - All API responses now contain proper Unicode emojis
  - Fixed `notes.log` encoding issue

- **Quest Journal Tracking** - Quests now properly activate and track!
  - Fixed quests not appearing in journal (were registered but never accepted)
  - Auto-accept "rescue_lily" and "clear_the_path" quests on scenario start
  - Combat kills now trigger `on_enemy_killed()` for quest objective tracking
  - Frontend handles both `COMPLETE`/`completed` status formats
  - Frontend handles both `current_count`/`current` objective field names
  - Fixed duplicate Flask endpoint causing startup error (`combat_status` → `combat_status_v2`)

### Changed
- **Architecture: API-First Design** - Terminal version archived!
  - `game.py` moved to `backup/legacy/game.py` (no longer maintained)
  - `api_server.py` is now the only entry point
  - `dm_engine.py` contains all shared DM logic
  - All new development follows Core-First methodology
  - React frontend is the primary UI

### Added
- **Quest Journal Updates** - Real-time quest tracking in frontend!
  - Quest objectives update when items acquired, NPCs talked to
  - Location travel triggers quest updates
  - SSE `quest_update` events sent to frontend
  - NPC talk detection from player actions ("talk to bram")
  - Tests added in `tests/test_quest_hooks.py`

- **Phase 4.5: Interactive World Map UI** - New development priority!
  - Comprehensive plan for visual clickable map navigation
  - MapNode, MapConnection, MapRegion data structures defined
  - Location dataclass extended with map coordinates (map_x, map_y)
  - WorldMap class for managing fog of war and node state
  - Flutter WorldMapWidget component architecture
  - Goblin Cave scenario map layout with 10 locations across 3 regions
  - Development plan updated with 7 implementation steps

- **Shop Purchase Tag [BUY:]** - New DM tag for shop transactions!
  - `[BUY: item_name, price]` - Deducts gold and adds item to inventory
  - Distinguishes purchases from free loot/rewards (`[ITEM:]` tag)
  - DM system prompt updated with clear usage instructions
  - Example: `[BUY: studded_leather, 25]` deducts 25g and adds armor

- **Armor Auto-Equip on Purchase** - Purchased armor is automatically equipped!
  - When buying armor via `[BUY:]`, old armor is unequipped
  - Old armor's AC bonus is removed and item removed from inventory
  - New armor's AC bonus is applied
  - Confirmation messages show equipment changes

- **Weapon Auto-Equip** - Better weapons are automatically equipped!
  - When receiving a weapon via `[BUY:]` or `[ITEM:]` tags
  - Auto-equips if new weapon has higher max damage than current
  - Compares damage dice (e.g., 1d8 > 1d4, 2d6 > 1d10)
  - Old weapon stays in inventory for later use
  - Confirmation message shows new weapon damage

- **Anti-Reroll Protection** - Prevents skill check farming exploit!
  - DM instructed to deny repeated attempts at same failed action
  - Players cannot spam "search again" or "try once more" after failures
  - Requires meaningful change (new location, info, approach) to retry
  - Maintains gameplay challenge and fair rolling

- **Stats Display in Shop & Inventory** - Players can now see item stats!
  - Shop display shows: `[DMG: 1d8]` for weapons, `[AC: +2]` for armor
  - Inventory display shows same stats inline with item names
  - Healable items show: `[HEAL: 2d4+2]`
  - Affordability markers: ✓ (can afford) and ✗ (too expensive)

### Improved
- **Shop Display Format** - Enhanced item listings with stats
  - Example: `Longsword (x2) [DMG: 1d8].................17g ✓`
  - Example: `Studded Leather (x1) [AC: +2].............51g ✗`

- **Inventory Display Format** - Stats shown inline with items
  - Example: `• Longsword [DMG: 1d8]`
  - Example: `• Studded Leather [AC: +2]`

- **Party/Companion System (Phase 3.3.7)** - Full party management implemented!
  - New `src/party.py` module with PartyMember dataclass and Party class
  - PartyMemberClass enum: FIGHTER, RANGER, ROGUE, CLERIC, WIZARD
  - SpecialAbility system with per-class abilities:
    * Fighter: Shield Wall (+2 AC to party)
    * Ranger: Hunter's Mark (+1d4 damage)
    * Rogue: Sneak Attack (+2d6 when flanking)
    * Cleric: Healing Word (1d8+2 heal)
    * Wizard: Magic Missile (auto-hit 1d4+1)
  - Max 2 companions per party
  - Recruitment conditions: skill checks, gold, items, objectives (OR logic)
  - Predefined recruitable NPCs: Elira (Ranger), Marcus (Fighter), Shade (Rogue)
  - 72 comprehensive tests in tests/test_party.py
  
- **Party Combat Integration** - Party members fight alongside player!
  - Party members added to initiative order
  - Automatic party member turns with simple AI:
    * Attacks weakest enemy
    * Uses special ability when appropriate
    * Cleric heals player when below 50% HP
  - Flanking bonus: +2 to attack when attacking same target as player
  - Enemies can target party members (30% chance)
  - Party member damage and death tracking

- **Party Commands** - New game commands for party management!
  - `party` / `companions` / `allies` - Show current party roster
  - `recruit <name>` - Attempt to recruit NPC at current location
  - `dismiss <name>` - Remove companion from party

- **Recruitable NPCs in Scenario** - Three new companions added!
  - Marcus the Mercenary (tavern_main): Gold-based recruitment (25g) or CHA DC 15
  - Elira the Ranger (forest_clearing): CHA DC 12 or quest objective
  - Shade the Rogue (goblin_camp_shadows): CHA DC 14, hidden agenda

- **Party Save/Load** - Full persistence for party state!
  - Party data included in save files
  - Restores HP, ability uses, recruited status
  - New test: test_party_save_load

- **AI DM Stress Test Suite** - Comprehensive AI security testing!
  - New `tests/test_ai_stress.py` with 23 stress test cases
  - Tests prompt injection attacks, NPC hallucination, format compliance
  - Detects instruction leakage, rule violation acceptance
  - Interactive mode for manual testing (`--interactive` flag)
  - Rate-limited API calls with detailed result analysis

- **Travel Menu System** - Streamlined navigation with two-phase travel!
  - New `travel` command shows numbered destination menu
  - Danger indicators: ⚠️ threatening, ☠️ deadly, ❓ uneasy, ✓ visited
  - Two-phase travel for dangerous areas:
    * Phase 1: Select numbered destination
    * Phase 2: "How do you approach?" (Enter = walk normally)
  - Approach keywords: sneak (Stealth), carefully (Perception), run (narrative)
  - Successful stealth approach grants SURPRISE in subsequent combat
  - Accepts: numbers, cardinal directions (n/s/e/w), or exit names
  - 42 new tests in tests/test_travel_menu.py
  - Alternative triggers: "leave", "exit", "explore", "where can i go"
  - Location-based DCs: Each area has custom stealth_dc and perception_dc

- **Blacksmith Shop Location** - Proper location architecture!
  - Created `blacksmith_shop` as a separate location
  - Village Square now has exit to forge (west/forge/blacksmith)
  - Gavin the Blacksmith NPC is inside the shop
  - Entering the shop triggers shop interaction

- **Quest Creation Guide** - Comprehensive documentation!
  - Step-by-step guide for creating quests in DEVELOPER_GUIDE.md
  - Objective type reference with factory functions
  - Quest types and disposition rewards explained
  - Prerequisites, optional/hidden objectives covered
  - Testing patterns and checklist included

### Improved
- **AI DM Security - Prompt Hardening** - Stronger security constraints!
  - Added SECURITY section at top of DM system prompt
  - AI now refuses to reveal/discuss system instructions
  - Stays in character when asked about "prompts" or "system"
  - Added explicit "NEVER VIOLATE" markers for critical rules

- **AI DM Security - NPC Hallucination Prevention** - Stronger constraints!
  - Clearer WRONG/CORRECT examples in prompt
  - AI now properly denies knowledge of non-existent NPCs like "Elara"
  - Added explicit warnings against inventing shops, temples, healers
  - Improved redirection to existing scenario NPCs/locations

- **Code Quality - Variable Naming Standardization** - Consistent manager variables!
  - Standardized to `location_manager` and `npc_manager` throughout main loop
  - Removed redundant manager extractions from conditional blocks
  - Variables now defined once at start of each loop iteration
  - Function parameters still use `loc_mgr`/`npc_mgr` for brevity

- **Code Quality - DRY Refactoring** - Reduced code duplication in game.py!
  - Created shared `perform_travel()` function for all movement logic
  - Extracted `get_approach_dcs()` for location-based difficulty
  - Travel menu and "go" command now use same shared functions
  - Added `stealth_dc` and `perception_dc` fields to LocationAtmosphere
  - Updated LocationAtmosphere `to_dict()` and `from_dict()` for persistence

- **Exit Display Cleanup** - Removed duplicate exits!
  - Village square now shows single "forge" exit instead of "forge" and "blacksmith"
  - "blacksmith" is now an alias that maps to "forge"

### Fixed
- **NameError: location_manager not defined** - Variable scope issue resolved
- **Test Import Paths** - Fixed relative imports in test_character.py, test_inventory.py
  - Changed from `sys.path.insert(0, '../src')` to absolute path using `os.path.dirname(__file__)`

- **Rest & Hit Dice System** - Strategic healing between encounters!
  - New `rest` command (aliases: "short rest", "heal", "bandage")
  - Consumes 1 Hit Die per rest (pool = character level)
  - Heals 1d6 + CON modifier per rest
  - Hit Dice restore on: Boss kills, Level up (NOT after normal combat)
  - Prevents rest spam while rewarding major victories
  - Cannot rest during combat or at full HP

### Changed
- **Combat Balance Overhaul** - Enemies retuned for better survivability!
  - Goblin: HP 7→5, AC 15→12, Attack +4→+3, Damage 1d6+2→1d6+1
  - Wolf: HP 11→8, AC 13→11
  - Giant Spider: HP 26→18, AC 14→13
  - Boss Encounter: Reduced from 1 boss + 2 goblins to 1 boss + 1 goblin
  - Philosophy: 2-3 hits to kill standard enemies, survive 3-4 hits

- **Scenario Folder Architecture** - Planned modular structure for campaigns!
  - Campaigns organized in `src/scenarios/<campaign_name>/` folders
  - Each campaign can have multiple chapters (chapter_1.py, chapter_2.py, etc.)
  - Replaced JSON Data Refactor plan with pure Python approach
  - Benefits: Full Python power, IDE support, procedural generation
  - Updated DEVELOPER_GUIDE.md and DEVELOPMENT_PLAN.md with new architecture

### Fixed
- **Shop Interaction Bug** - "go to blacksmith" now works properly!
  - Previously showed only a brief hint when already at merchant location
  - Now automatically displays full shop inventory when merchant is present
  - Shows helpful commands: buy, haggle, talk
  - Added proper `continue` to prevent dead-end loop

- **test_shop.py Import Error** - Tests now run correctly
  - Added missing `sys.path` setup for src imports
  - All 72 shop tests now passing

### Changed
- **Development Plan Phase 5.2** - JSON Data Refactor → Scenario Folder System
  - Pure Python approach maintains full feature flexibility
  - Multi-chapter campaigns supported in organized folder structure

### Test Suite Status
- **821+ unit tests passing** (December 2025)
- **125 security tests passing** (Hostile Player Testing - 5 rounds)
- Key test file updates:
  - `test_location.py`: 200 tests (location system)
  - `test_party.py`: 72 tests (companion system)
  - `test_quest.py`: 57 tests (quest tracking)
  - `test_npc.py`: 55 tests (NPC interactions)
  - `test_reputation.py`: 55 tests (disposition system)
  - `hostile_final.py`: 75 tests (final security round)
  - `test_combat_travel_block.py`: 3 tests (combat exploit prevention)

---

### Added (Previous)
- **Action-Based Disposition System** - Your actions now affect NPC relationships!
  - Trade actions: +1 disposition per buy/sell, +2 for successful haggle
  - Quest completion: +25 (main), +15 (side), +10 (minor) to quest giver NPC
  - Gift system: `give <item> to <npc>` command, +5 to +20 based on item value
  - Theft system: `steal from <npc>` command (DEX DC 15), -30 or -50 on failure
  - QuestType enum (MAIN/SIDE/MINOR) for categorizing quests
  - 15 new reputation tests (62 total in test_reputation.py)
  - **782 total tests passing** (up from 750)

- **Massively Expanded Shop Natural Language** - 85+ shop trigger phrases!
  - Direct requests: "shop", "store", "browse", "trade", "merchandise"
  - "What do you have" variations: "whatcha got", "what you got", "what're you selling"
  - "Show me" variations: "show me your wares", "let me see", "can i see"
  - Buy intent: "want to buy", "wanna buy", "looking to buy", "interested in buying"
  - Roleplay: "peruse your wares", "interested in your wares", "examine your wares"
  - Browse/check/view: "browse items", "check stock", "view inventory"
  - Casual/slang: "whatcha got", "show me the goods", "any deals", "hook me up"
  - First-person: "i want to buy", "i wanna shop", "i'd like to trade"
  - 32 new shop trigger tests

- **Enhanced Shop Interaction System** - More natural shopping experience!
  - Natural language shop triggers: "what do you have for sale", "show me your wares", "can i buy something"
  - 25+ conversational phrases now open the shop menu
  - Quantity purchasing: "buy 3 healing potions" or "buy 5x torch"
  - Shows affordable quantity when gold is insufficient: "💡 You can afford 4"
  - Stock validation prevents over-buying: "only has 5 left!"
  - Multi-item purchase summary with per-unit cost
  - Limit of 99 items per purchase (abuse prevention)
  - 7 new shop tests (35 total in test_shop.py)

- **Enhanced Skill Check System** - More frequent and contextual skill checks!
  - DM now prompted when to call for each skill type (Perception, Stealth, Persuasion, etc.)
  - Automatic hints injected for exploration words ("look", "search", "examine")
  - Stealth hints for sneaking actions ("sneak", "hide", "quietly")
  - Social hints for Persuasion ("convince", "negotiate", "request")
  - Social hints for Intimidation ("threaten", "demand", "scare")
  - Social hints for Deception ("lie", "bluff", "deceive", "trick")
  - Social hints for Insight ("read", "sense motive", "lying", "trust")
  - Physical hints for climbing, jumping, breaking actions
  - Clear DC guidelines: Easy=10, Medium=13, Hard=15, Very Hard=18

- **Flexible Travel System** - More forgiving movement commands!
  - Natural language support: "go to the village square", "head to the tavern"
  - First-person support: "i go east", "i walk north", "i head outside"
  - Destination matching: "village square" matches exit leading to village_square
  - Filler word stripping: "to the", "towards the", "into the", etc.
  - Fuzzy matching: underscores and spaces interchangeable
  - Smart shop redirect: "go to blacksmith" → hints to use `shop` command
  - 25 new tests in `test_flexible_travel.py`

- **Village Blacksmith NPC** - Gavin the Blacksmith now available in the Village Square!
  - Opens late for adventurers ("I keep my forge burning late for folk like you")
  - Shop inventory: daggers, shortswords, longsword, leather armor, healing potions, torches, rope
  - 15% markup (cheaper than traveling merchants)
  - Gruff dialogue with warnings about goblins
  - Village Square description and atmosphere updated to reflect open forge

- **Gold Command** - Quick way to check your gold!
  - New commands: `gold`, `g`, `money`, `coins`, `purse`
  - Shows current gold amount
  - When at a shop location, provides merchant hints

- **XP Progress Display** - See your progress to the next level!
  - After receiving XP, shows: `📈 Level 2: 50/100 XP (50 needed)`
  - At max level shows: `📈 Max Level reached! (1250 total XP)`
  - Works for both combat XP and quest XP rewards

- **Richer Travel Narratives** - More immersive location descriptions!
  - Enhanced LOCATION_NARRATION_PROMPT for 5-7 sentences (was 3-5)
  - Travel transitions for first visits
  - Multi-sensory descriptions (sounds, smells, temperature, textures)
  - 80-150 word descriptions for richer storytelling

### Fixed
- **NPCManager AttributeError** - Fixed `'NPCManager' object has no attribute 'npcs'`
  - Changed `npc_mgr.npcs.values()` to `npc_mgr.get_all_npcs()` in game.py
- **QuestManager method name** - Fixed `on_npc_talk` to `on_npc_talked`
  - Corrected method call in talk command handler

---

## [Previous Changes]

### NPC Relationship System - Step 1 (Phase 3.3 - Priority 6)
- Disposition foundations added!
  - New disposition threshold constants in `npc.py`:
    - `DISPOSITION_HOSTILE = -50` - Below this: hostile behavior
    - `DISPOSITION_UNFRIENDLY = -10` - Below this: unfriendly behavior  
    - `DISPOSITION_FRIENDLY = 10` - Above this: friendly behavior
    - `DISPOSITION_TRUSTED = 50` - Above this: trusted behavior
  - New price modifier constants:
    - `PRICE_MODIFIER_HOSTILE = 0.0` - Cannot trade
    - `PRICE_MODIFIER_UNFRIENDLY = 1.25` - 25% markup
    - `PRICE_MODIFIER_NEUTRAL = 1.0` - Normal prices
    - `PRICE_MODIFIER_FRIENDLY = 0.9` - 10% discount
    - `PRICE_MODIFIER_TRUSTED = 0.8` - 20% discount
  - Enhanced NPC methods:
    - `get_disposition_level()` - Returns 'hostile'/'unfriendly'/'neutral'/'friendly'/'trusted'
    - `get_disposition_label()` - Returns formatted label with emoji (e.g., "🟢 Friendly (+35)")
    - `get_disposition_modifier()` - Returns price multiplier for current level
    - `can_trade()` - Returns False if hostile, True otherwise
  - Test suites:
    - `test_reputation.py` (47 tests) - Core disposition functionality
    - `test_reputation_hostile.py` (36 tests) - Adversarial/security testing
  - Total test count: **703 tests passing**

### Traveling Merchants System (Phase 3.3 - Priority 5) - Dynamic NPCs that roam the world!
  - New NPC fields: `is_traveling`, `spawn_chance`, `possible_locations`, `inventory_pool`
  - New NPC fields: `inventory_rotation_size`, `last_spawn_location`, `visits_since_spawn`, `spawn_cooldown`
  - Helper functions in `npc.py`:
    - `check_traveling_merchant_spawn()` - Probabilistic spawn check with cooldown
    - `rotate_merchant_inventory()` - Randomize shop inventory from pool
    - `spawn_traveling_merchant()` - Place merchant at location with fresh inventory
    - `despawn_traveling_merchant()` - Remove merchant after cooldown
    - `update_traveling_merchant_visits()` - Track visits since spawn
  - Zephyr the Wanderer NPC in goblin_cave scenario:
    - 25% spawn chance at forest_clearing, cave_entrance, cave_tunnel, goblin_storage
    - Pool of 11 items including rare enchanted_dagger and ancient_amulet
    - Rotates 5 items per spawn with 15% markup
  - Game loop integration in `game.py` for automatic spawn/despawn on location change
  - Test suite: `test_traveling_merchant.py` (37 tests)

- **Adversarial Testing Suite (Phase 4.1)** - 95 security and exploit tests!
  - `test_hostile_player.py` (44 tests):
    - Negative value exploits (damage, XP, gold)
    - Boundary condition tests (0 HP, max HP, max level)
    - Item system exploits (empty names, special chars)
    - Combat system exploits (multi-enemy, death state)
    - Save system manipulation tests
  - `test_prompt_injection.py` (22 tests):
    - Tag injection defenses ([GOLD:], [XP:], [ITEM:], [COMBAT:], [ROLL:])
    - Command injection tests (directions, items)
    - NPC dialogue manipulation tests
    - Save file injection tests
    - Encoding attack tests (unicode, long input)
    - Security architecture verification (static analysis test)
  - `test_flow_breaking.py` (29 tests):
    - Weird input handling (empty, whitespace, unicode, special chars)
    - Non-existent reference tests (fake locations, items, NPCs)
    - Scenario manipulation tests
    - Direction alias exploits
    - Item/Quest/Event system exploits
    - Save state manipulation tests
    - Edge case tests (rapid movement, concurrent changes)
  - Total test count: 583 tests passing

### Fixed
- **Negative Damage Exploit** - `Character.take_damage()` now ignores negative values
  - Previously: `take_damage(-100)` healed beyond max HP
  - Now: Negative amounts are silently ignored
- **Negative XP Exploit** - `Character.gain_xp()` now ignores negative values
  - Previously: `gain_xp(-1000)` could reduce XP
  - Now: Negative amounts are silently ignored
- **Empty String Item Lookup** - `get_item("")` now returns None
  - Previously: Empty string matched first item via substring search
  - Now: Empty/whitespace-only names return None immediately
- **Enemy.is_dead State Bug** - Changed from field to property
  - Previously: Setting `enemy.current_hp = 0` didn't update `is_dead`
  - Now: `is_dead` is a `@property` that checks `self.current_hp <= 0`
- **Empty Direction Movement** - `LocationManager.move("")` now fails gracefully
  - Previously: Empty/whitespace directions matched any exit via partial matching
  - Now: Returns error message "You need to specify a direction."

### Security
- **Verified Security Architecture**: Tag parsers only process DM responses, not player input
  - Player input → AI model → DM response → Parsers → Game state
  - Static analysis test ensures no code path passes player_input to parsers
  - Remaining attack vector is AI prompt injection (inherent LLM risk)

- **Quest System (Phase 3.3.4)** - Full quest tracking and management!
  - New `src/quest.py` module (~830 lines):
    - `QuestStatus` enum: NOT_STARTED, ACTIVE, COMPLETE, FAILED
    - `ObjectiveType` enum: KILL, FIND_ITEM, TALK_TO, REACH_LOCATION, COLLECT, CUSTOM
    - `QuestObjective` dataclass: progress tracking for each objective
    - `Quest` dataclass: objectives, rewards, prerequisites, time limits, giver NPC
    - `QuestManager` class: complete lifecycle management
    - Factory helpers: `create_kill_objective()`, `create_find_objective()`, etc.
  - New game commands:
    - `quests` / `journal` - View quest log with active/completed/failed sections
    - `quest <name>` - View detailed quest information and objectives
  - Quest integration in game.py:
    - Quest accept/turn-in flow via NPC dialogue
    - Kill objectives track combat victories
    - Location objectives trigger on arrival
    - Item objectives trigger on pickup
    - Talk objectives trigger on NPC conversation
    - Quest completion awards XP, gold, and items
  - Four starter quests in Goblin Cave scenario:
    - **Rescue Lily** (Main): Save farmer's daughter from goblins
    - **Recover Heirlooms** (Side): Find stolen family items
    - **Clear the Path** (Side): Eliminate threats on the road
    - **The Chief's Treasure** (Side): Defeat the goblin chief
  - New quest items: silver_locket, family_ring
  - Save/Load integration: quest state persists across sessions
  - 57 new tests in test_quest.py, 5 new scenario tests
  - Total test count: 488 tests passing

- **Shop Stock Tracking System** - Merchants now have limited inventory!
  - `shop_inventory` supports both formats:
    - `Dict[str, int]`: item_id → quantity (stock tracking)
    - `List[str]`: unlimited stock (backward compatible)
  - New helper functions in npc.py:
    - `check_stock(merchant, item_id)` - Returns quantity (-1 = unlimited, 0 = out of stock)
    - `decrement_stock(merchant, item_id)` - Reduces stock after purchase
    - `get_shop_inventory_for_prompt(merchant, items_db)` - Generates inventory text for AI prompts
  - Shop display now shows quantities: "Healing Potion (x6)" or "(∞)" for unlimited
  - Buy command prevents purchasing out-of-stock items
  - Purchase feedback shows remaining stock: "Purchased X! (3 left)" or "(LAST ONE!)"
  - AI prompt includes actual inventory quantities to prevent hallucination
  - Trader Mira now has realistic stock:
    - 6 healing potions, 20 rations, 2 leather armor, 3 shortswords, 15 torches, 5 rope

- **Shop System (Phase 3.3.3)** - Buy, sell, and haggle with merchants!
  - Price calculation functions in npc.py:
    - `calculate_buy_price(base_value, markup, discount)` - Applies merchant markup and discounts
    - `calculate_sell_price(base_value, sell_rate)` - Default 50% of item value
    - `format_shop_display()` - Beautiful formatted shop UI with prices
    - `get_merchant_at_location()` - Find merchants at player's current location
  - New game commands:
    - `shop` / `browse` / `wares` - View merchant inventory
    - `buy <item>` - Purchase items using gold
    - `sell <item>` - Sell inventory items for gold
    - `haggle` - CHA DC 12 check for 20% discount (or +10% price increase on failure!)
  - Trader Mira merchant NPC added to forest_clearing
    - Sells: healing_potion, rations, leather_armor, shortsword, torch, rope
    - 20% markup on base prices
    - Full dialogue tree about wares, danger, and the village
  - Session-based haggle state tracking per merchant
  - 28 new tests in test_shop.py
  - Total test count: 425 tests passing

- **Hidden/Secret Locations (Phase 3.2.1 Priority 8)** - Rewarding exploration
  - `hidden` field on Location dataclass - marks exits as secret until discovered
  - `discovery_condition` field - how to reveal: skill checks, items, level, visited
  - `discovery_hint` field - clue for players ("The vines look suspicious...")
  - `discovered_secrets` tracking on LocationManager (persists in save/load)
  - Key methods added:
    - `discover_secret(location_id)` - Reveal a hidden location
    - `is_secret_discovered(location_id)` - Check if discovered
    - `get_hidden_exits()` - Get undiscovered hidden exits from current location
    - `get_discovery_hints()` - Get hints for hidden exits
    - `check_discovery(location_id, game_state)` - Check if conditions met
  - `get_exits()` now filters out hidden locations until discovered
  - Condition formats supported:
    - `skill:perception:14` - Requires skill check
    - `has_item:treasure_map` - Requires item
    - `level:5` - Requires player level
    - `visited:cave_entrance` - Requires visiting another location first
  - Added secret_cave to forest_clearing (perception DC 14, contains ancient_amulet)
  - Added treasure_nook to boss_chamber (investigation DC 12, contains enchanted_dagger)
  - 33 new unit tests (174 total location tests)
  - Example usage:
    ```python
    Location(
        id="secret_cave",
        name="Hidden Hollow",
        description="A hidden cave with treasure",
        hidden=True,
        discovery_condition="skill:perception:14",
        discovery_hint="The vines along the cliff look unusually thick...",
        items=["ancient_amulet", "gold_coins"]
    )
    ```

- **Random Encounter System (Phase 3.2.1 Priority 7)** - Travel variety through random combat
  - `RandomEncounter` dataclass: id, enemies, chance, condition, cooldown, max_triggers
  - `random_encounters` field on Location dataclass
  - `check_random_encounter()` method: Rolls dice, respects limits
  - Features:
    - Percentage-based trigger chance (1-100)
    - `min_visits` - Delay encounters until Nth visit
    - `max_triggers` - Limit how many times encounter can happen (-1 = unlimited)
    - `cooldown` - Visits before can trigger again after triggering
    - `condition` - Optional prerequisite (uses same format as exit conditions)
    - `narration` - AI DM hint for encounter introduction
  - `visit_count` tracking on locations (persists in save/load)
  - Added wolf encounter to forest_path (20% chance, max 2x)
  - Added giant_spider encounter to cave_tunnel (25% chance, not first visit)
  - Added `giant_spider` enemy to combat.py
  - 20 new unit tests (141 total location tests)
  - Example usage:
    ```python
    Location(
        id="forest",
        name="Forest Path",
        random_encounters=[
            RandomEncounter(
                id="wolf_ambush",
                enemies=["wolf"],
                chance=20,
                max_triggers=2,
                cooldown=3,
                narration="A hungry wolf emerges from the underbrush!"
            )
        ]
    )
    ```

- **Cardinal Direction Aliases (Phase 3.2.1 Priority 6)** - Classic text adventure navigation
  - `direction_aliases` field on Location dataclass
  - Maps n/s/e/w/ne/nw/se/sw/u/d to descriptive exit names
  - `resolve_direction_alias()` helper: expands 'n' → 'north', etc.
  - `CARDINAL_ALIASES` constant: all supported shortcuts
  - Updated `move()` to check aliases before exit name matching
  - Added aliases to all Goblin Cave scenario locations
  - Players can now type 'n' or 'north' instead of 'forest_path'
  - 18 new unit tests (121 total location tests)
  - Example usage:
    ```python
    Location(
        id="village",
        exits={"forest_path": "forest", "tavern_door": "tavern"},
        direction_aliases={"n": "forest_path", "e": "tavern_door"}
    )
    # Player can type: 'go n', 'n', 'north', or 'forest_path'
    ```

- **Conditional Exit System (Phase 3.2.1 Priority 5)** - Locked doors and gated progression
  - `ExitCondition` dataclass: exit_name, condition, fail_message, consume_item
  - `check_exit_condition()` function: Validates all condition types
  - Condition types supported:
    - `has_item:<key>` - Requires item in inventory
    - `gold:<amount>` - Requires minimum gold
    - `visited:<location>` - Requires visiting another location first
    - `skill:<ability>:<dc>` - Triggers skill check
    - `objective:<id>` - Requires completed objective
    - `flag:<name>` - Custom game flags
  - `exit_conditions` field on Location dataclass
  - `unlocked_exits` tracking - Doors stay open after first unlock
  - `get_exit_condition()`, `is_exit_unlocked()`, `unlock_exit()` methods
  - Updated `move()` to check conditions before allowing movement
  - Updated game.py to pass game_state and handle CONSUME_ITEM markers
  - Added locked storage room to Goblin Cave (requires storage_key)
  - Added storage_key and rusty_key items to inventory.py
  - 23 new unit tests (103 total location tests)
  - 5 new interactive tests (13 total in test_location_with_dm.py)

- **Complete Scenario API Documentation** - 95%+ coverage of scenario system
  - Location API Reference: all methods (has_item, remove_item, has_npc, etc.)
  - Event Condition Formats: has_item, skill, visited, objective patterns
  - Event Effect Formats: damage, heal, add_item, add_exit, skill_check
  - Scenario Runtime API: start, move, complete_objective, transition
  - ScenarioManager methods: check_transition, get_dm_context, list_available
  - Save/Load Integration: what's saved, how to save/restore state
  - Advanced Patterns: branching paths, optional objectives, hidden areas, multi-visit

- **Scenario Creation Documentation** - Comprehensive guides for building scenarios
  - `docs/SCENARIO_TEMPLATE.py`: Complete template with all fields and comments
  - Step-by-step walkthrough in DEVELOPER_GUIDE.md
  - Detailed Location, Event, Scene examples
  - DM instructions best practices
  - Combat encounter balancing guide
  - Enemy reference table with HP/XP/Gold
  - Complete mini-scenario example

- **Class-Appropriate Weapon Drops (Phase 3.2.2)** - Balanced, class-matched loot
  - `CLASS_WEAPON_POOLS`: Maps each class to appropriate weapon types
  - `QUALITY_TIERS`: Common (60%), Uncommon (25%), Rare (12%), Epic (3%)
  - `generate_class_weapon()`: Returns class-appropriate weapon with random quality
  - `get_enemy_loot_for_class()`: Replaces weapon drops with class-matched weapons
  - Quality weapons have enhanced damage (e.g., "Fine Longsword" = 1d8+1)
  - `parse_quality_weapon()` and `create_quality_weapon()` in inventory.py
  - Fighters get swords/axes, Rogues get daggers/rapiers, Wizards get staves, etc.

- **Fixed Loot System (Phase 3.2.2)** - Predictable, balanced combat rewards
  - `loot: List[str]` field on Enemy: Specifies exact items dropped
  - `gold_drop: int` field on Enemy: Fixed gold amount per enemy type
  - `get_enemy_loot()` function: Returns `(loot_items, gold)` tuple
  - Replaces random `generate_loot()` and `gold_from_enemy()` functions
  - Goblin Cave loot balanced: goblin=3g, goblin_boss=20g+healing_potion+shortsword
  - Ensures consistent economy and inventory progression

- **Automatic Combat XP System (Phase 3.2.2)** - Mechanics-First XP rewards
  - `xp_reward` field on Enemy dataclass: Each enemy type has fixed XP value
  - `get_enemy_xp()` function: Returns XP reward for enemy type
  - Automatic XP award after combat victory (no DM involvement)
  - XP values balanced for Goblin Cave: goblin=25, goblin_boss=100, orc=50
  - Level up notification shown immediately after XP award
  - DM prompt updated: Combat XP is automatic, DM only awards non-combat XP

- **Objective XP System (Phase 3.2.2)** - Milestone rewards
  - `objective_xp` dict on Scene: Maps objective IDs to XP rewards
  - `complete_objective()` now returns `(success, xp_reward)` tuple
  - Goblin Cave objectives: meet_bram=10, accept_quest=15, find_lily=50, defeat_chief=50
  - Ensures consistent XP progression throughout scenarios

- **Fixed Encounter System (Phase 3.2.2)** - Predictable, balanced combat difficulty
  - `encounter` field on Location: Specifies exact enemy types for combat
  - `encounter_triggered` field: Tracks whether encounter has occurred
  - DM context shows fixed encounter instructions with exact `[COMBAT: ...]` tag
  - Prevents AI DM from spawning random enemy counts (e.g., "4-5 goblins")
  - Goblin Cave encounters now fixed: 4 goblins at camp, boss + 2 at throne room
  - Encounter state saved/loaded with game progress
  - Updated DM system prompt with "FIXED ENCOUNTERS" rules

- **Developer Guide: Scenario System Documentation**
  - Full Scene and Scenario dataclass documentation
  - Hierarchy diagram: ScenarioManager → Scenario → Scene → Location
  - The Goblin Cave scenario structure with all locations/scenes
  - Fixed Encounter System documentation with examples
  - How to create new scenarios guide

- **Location Narration System (Phase 3.2.1 Priority 4)** - AI-generated immersive location descriptions
  - `build_location_context()`: Creates context dict with location, items, NPCs, events
  - `get_location_narration()`: Requests narrative prose from AI DM
  - `display_location_narration()`: Displays 📍 narration with consistent format
  - `LOCATION_NARRATION_PROMPT`: Specialized prompt for atmospheric descriptions
  - Follows "Mechanics First, Narration Last" architecture pattern
  - Items, NPCs, and events woven naturally into prose (no bullet points)

- **Location Event System (Phase 3.2.1 Priority 3)** - Dynamic events at locations
  - `EventTrigger` enum: ON_ENTER, ON_FIRST_VISIT, ON_LOOK, ON_ITEM_TAKE
  - `LocationEvent` dataclass: id, trigger, narration, effect, condition, one_time
  - Location methods: `get_events_for_trigger()`, `trigger_event()`, `has_event()`, `is_event_triggered()`, `add_event()`
  - `move()` now returns events as 4th tuple element
  - Events passed to AI DM for contextual narration
  - 6 Goblin Cave locations now have events (traps, discoveries, confrontations)

- **Event Tests** - 16 new tests in `test_location.py` (80 total)
  - `TestLocationEventBasics`: creation, serialization, trigger types
  - `TestLocationEventMethods`: add/has/trigger/get events
  - `TestLocationManagerEvents`: move integration with events

- **Unified Test Runner** - `run_interactive_tests.py`
  - Single entry point for all 8 interactive test modules
  - Menu-driven selection with unit test + interactive modes
  - Shop marked as "Coming Soon" placeholder

- **New Commands**
  - `scan` command: Shows mechanical list of items, NPCs, exits (for players who want details)
  - `take <item>` now works with spaces: "take healing potion" works like "take healing_potion"

### Changed
- `look` command now generates AI narrative descriptions instead of bullet points
- Movement to new locations triggers AI narration (with events if any)
- Items display with friendly names: "Healing Potion" instead of "healing_potion"
- `has_item()` and `remove_item()` now normalize spaces to underscores
- Interactive tests updated to use new location narration system
- Help menu updated with new navigation commands
- Test count: 228 tests total

### Planned
- Phase 3.3: NPCs

---

## [0.9.1] - 2024-12-16

### Added
- **Combat Narration System** - AI-generated immersive combat descriptions
  - `build_combat_context()`: Creates context dict from attack/damage results
  - `get_combat_narration()`: Requests narrative prose from AI DM
  - `display_combat_narration()`: Displays 📖 narration with formatting
  - `COMBAT_NARRATION_PROMPT`: Specialized prompt for combat narration
  - Mechanics-first architecture: dice resolve, then AI narrates
  - Supports hits, misses, critical hits, fumbles, and enemy attacks
  - Contextual details: weapon, damage type, target status, kills

- **Combat Narration Tests** - New test suite in `test_combat_with_dm.py`
  - `test_combat_context_building()`: Validates context dict creation
  - `test_display_combat_narration()`: Tests output formatting
  - `test_combat_narration_with_ai()`: End-to-end AI narration tests
  - `run_narration_tests()`: Runs all narration unit tests
  - Test menu: Choose between unit tests and interactive combat

### Changed
- Combat flow now includes AI narration after each attack (player and enemy)
- Removed hardcoded flavor text for crits/fumbles (now AI-generated)
- `test_combat_with_dm.py` now imports game.py narration functions
- Updated Developer Guide with Combat Narration System documentation

### Technical Notes
- Zero breaking changes: narration is purely additive
- Mechanics layer unchanged: all 31 combat tests still pass
- Narration fails gracefully (returns empty string on error)

---

## [0.9.0] - 2024-12-16

### Added
- **Phase 3.2: Location System** - Physical locations with navigation
  - `Location` dataclass: id, name, description, exits, npcs, items, atmosphere
  - `LocationManager`: handles movement, exit validation, AI context
  - 18 pre-defined locations for The Goblin Cave scenario
  - Scene → Location binding: each scene unlocks specific locations
  - Commands: `look`, `exits`, `go <direction>`
  - Cardinal directions: north, south, east, west (and n/s/e/w shortcuts)
  - AI receives location context for immersive narration
  - Location state saved/loaded with game progress

### Changed
- Scenes now have `location_ids` and `starting_location_id` fields
- `Scenario` class includes `LocationManager` with automatic initialization
- Save system now preserves location state (current location, visited flags)
- Help menu updated with navigation commands

---

## [0.8.2] - 2024-12-16

### Added
- **Critical Success/Failure Narration** - Enhanced skill check system
  - Natural 20 triggers "CRITICAL SUCCESS" context for AI
  - AI prompted to narrate legendary/epic outcomes for nat 20s
  - Natural 1 triggers "CRITICAL FAILURE" context for AI
  - AI prompted to narrate dramatic/comedic disasters for nat 1s
  - Enhanced system prompt with detailed critical guidance

### Changed
- Skill check result messages now include explicit narration hints for AI
- System prompt expanded with critical success/failure examples

---

## [0.8.1] - 2024-12-16

### Added
- **Comprehensive Test Suite** - 137 unit tests across all systems
  - `test_character.py` - 26 tests (creation, modifiers, HP, healing, XP)
  - `test_combat.py` - 28 tests (dice, enemies, attacks, initiative)
  - `test_inventory.py` - 35 tests (items, management, consumables, loot)
  - `test_scenario.py` - 26 tests (scenes, progression, objectives)
  - Total coverage: 41% overall, 95% inventory, 74% character

- **Interactive Inventory Test** - `test_inventory_with_dm.py`
  - Shop system with AI merchant personalities
  - Loot generation from defeated enemies
  - Item use with AI narration
  - Full inventory management testing

- **Enhanced Save System Error Handling**
  - Custom exception hierarchy (7 exception types)
  - Data validation functions
  - Atomic saves (temp file + rename)
  - Input sanitization for save names
  - Value clamping for data integrity
  - Error logging and tracking

### Changed
- Updated `DEVELOPER_GUIDE.md` with:
  - Starting equipment documentation
  - Inventory system reference
  - Error handling documentation
  - Updated test file listing

---

## [0.8.0] - 2024-12-17

### Added
- **Save/Load System (Phase 3.1)** - Complete game persistence
  - New `src/save_system.py` module
  - Save games to numbered slots (1-3) or timestamped files
  - Load games from main menu or during gameplay
  - List all saved games with character info
  - Creates `/saves/` directory automatically

- **Save Data Includes**
  - Full character state (stats, HP, XP, level)
  - Inventory with all item details
  - Equipped weapon and armor
  - Gold balance
  - Scenario progress and story flags
  - Chat history (last 20 messages)

- **In-Game Commands**
  - `save` - Save current game to slot
  - `load` - Load a saved game
  - `saves` - List all saved games

- **Main Menu Integration**
  - Option [3] to load saved game on startup
  - Shows number of available saves

- **Multi-Platform Architecture**
  - `StorageBackend` abstraction for local/cloud storage
  - `LocalFileBackend` for CLI (current)
  - API-ready serialization (Phase 5 compatible)
  - JSON format compatible with Flutter (Phase 6)

- **Unit Tests**
  - New `tests/test_save_system.py`
  - Character serialization tests
  - Item serialization tests
  - Full save/load cycle tests

- **TaskSync Updates**
  - File-based polling to avoid terminal timeouts
  - `python task.py --poll` (non-blocking)
  - `python task.py --write "task"` to queue tasks

### Changed
- Updated help menu with save/load commands
- Updated DEVELOPER_GUIDE.md with save system documentation
- Updated project structure in documentation

---

## [0.7.0] - 2024-12-17

### Added
- **Leveling System (Phase 2.6)** - Character progression with XP and levels
  - Level cap: 5, XP thresholds: 0 → 100 → 300 → 600 → 1000
  - `xp` command - View current level, XP, and progress bar
  - `levelup` command - Advance level when XP threshold met
  - +2 HP per level, stat boosts at L2/L4, class abilities at L3/L5
  - Proficiency bonus: +2 (L1-4), +3 (L5)

- **XP Reward System**
  - DM can award XP with `[XP: amount]` or `[XP: amount | reason]` tags
  - Milestone XP: minor=25, major=50, boss=100, adventure=150
  - XP rewards shown in game with level up notifications

- **Combat XP Integration**
  - `test_combat_with_dm.py` now awards XP after victory
  - XP breakdown by enemy type shown on win

- **Unit Tests**
  - New `tests/test_xp_system.py` with 10 test cases
  - Covers: initial state, XP gain, thresholds, level up, max cap

---

## [0.6.2] - 2024-12-16

### Added
- **Surprise Round & Advantage System** - Ambush mechanics for stealth attacks
  - DM triggers surprise with `[COMBAT: goblin, wolf | SURPRISE]` format
  - Surprised enemies cannot act in Round 1
  - Player gets ADVANTAGE on first attack (roll 2d20, take higher)
  - Turn order shows `(SURPRISED)` next to affected enemies
  - Attack display: `🗡️ ⬆️ ADV Attack (Longsword): [8, 15→15]+5 = 20`

- **Roll Attack with Advantage**
  - New `roll_attack_with_advantage()` function in combat.py
  - Shows both dice rolls in output format
  - Only fumbles if BOTH dice are 1

- **Combat Test Updates**
  - New options 7 & 8: Pre-configured multi-enemy + surprise tests
  - Add 's' to any option for surprise (e.g., '2s', '4s')

---

## [0.6.1] - 2024-12-16

### Added
- **Multi-Enemy Combat System** - Fight multiple enemies simultaneously
  - DM triggers multi-enemy combat with `[COMBAT: goblin, goblin, wolf]` format
  - All enemies roll initiative individually
  - Proper D&D turn order - each combatant acts in initiative order
  - Target selection with `attack 1`, `attack 2`, or just type the number
  - All enemies displayed with numbered targeting: `[1] Goblin 1`, `[2] Goblin 2`

- **Improved Turn Order**
  - Initiative sorted by roll (highest first)
  - Player wins ties
  - Turn order displayed with initiative values: `[1] Goblin 2 [22]`
  - Round counter shown at start of each round

- **Combat Test Script**
  - `tests/test_combat_with_dm.py` updated with enemy selection menu
  - Options: Single, 2 goblins, mixed enemies, 3 wolves, boss+minions, custom

### Fixed
- **Enemy Naming**: Multiple same-type enemies now correctly named "Goblin 1", "Goblin 2"
- **Bare Number Input**: Typing just "1" or "2" after target prompt now works
- **Defend Timing**: Defend bonus (+2 AC) now correctly persists until player's next turn

---

## [0.6.0] - 2024-12-16

### Added
- **Phase 2.5: Inventory System** - Complete item management
  - `src/inventory.py` module with full inventory mechanics
  
- **Item Types**
  - **Weapons**: Dagger, Shortsword, Longsword, Greataxe, Rapier, Quarterstaff, Mace, Longbow, Shortbow
  - **Armor**: Leather, Studded Leather, Chain Shirt, Chain Mail, Plate
  - **Consumables**: Healing Potion, Greater Healing Potion, Antidote, Rations
  - **Misc**: Torch, Rope, Thieves' Tools, Bedroll
  - **Quest Items**: Mysterious Key, Ancient Scroll, Goblin Ear
  
- **Inventory Commands**
  - `inventory` / `inv` / `i` - View inventory and gold
  - `use <item>` - Use consumable items (healing potions, etc.)
  - `equip <item>` - Equip weapons or armor (updates stats)
  - `inspect <item>` - View detailed item information

- **DM Item Rewards**
  - DM can give items with `[ITEM: item_name]` tag
  - DM can give gold with `[GOLD: amount]` tag
  - Items automatically added to player inventory

- **Combat Loot**
  - Enemies now drop loot on defeat
  - Loot tables based on enemy type
  - Gold drops from most humanoid enemies

- **Starting Equipment**
  - Characters start with class-appropriate gear
  - 10-25 starting gold
  - Basic supplies: Healing Potion, 3x Rations, 2x Torch
  - Class gear: Fighter/Paladin/Cleric get Chain Shirt, Rogues get Thieves' Tools, etc.

- **Equipment System**
  - Armor now affects AC when equipped
  - Weapons can be swapped mid-game
  - Character sheet shows gold and item count

---

## [0.5.1] - 2024-12-16

### Added
- **Phase 2.4: Combat Integration**
  - Combat fully integrated into main game.py
  - DM triggers combat with `[COMBAT: enemy_type]` tag
  - Combat results feed back to DM for narrative continuation
  - Class-based default weapons in Character class

---

## [0.5.0] - 2024-12-16

### Added
- **Phase 2.3: Combat System** - Full D&D-style turn-based combat
  - `src/combat.py` module with complete combat mechanics
  - **Initiative System**: d20 + DEX modifier, determines turn order
  - **Attack Rolls**: d20 + STR/DEX + proficiency vs AC
  - **Damage Rolls**: Weapon-specific dice + ability modifier
  - **Critical Hits**: Natural 20 doubles damage dice
  - **Fumbles**: Natural 1 always misses
  
- **Combat Actions**
  - `attack` - Roll to hit and damage enemy
  - `defend` - +2 AC bonus for the round
  - `flee` - DEX check vs DC (10 + enemy DEX), opportunity attack on fail
  - `status` - View current combat state

- **Weapons System** (14 weapons)
  - Simple: Dagger, Handaxe, Light Hammer, Mace, Quarterstaff, Sickle
  - Martial: Longsword, Shortsword, Battleaxe, Greataxe, Greatsword, Warhammer
  - Ranged: Shortbow, Longbow
  - Finesse property for DEX-based attacks

- **Enemies System** (6 preset enemies)
  - Goblin, Goblin Boss, Skeleton, Orc, Bandit, Wolf
  - Each with HP, AC, attack bonus, damage dice, DEX modifier

- **Enhanced Combat UI**
  - Detailed status panel with HP bars (visual ████░░░░)
  - Round counter tracking
  - Weapon damage display
  - AC comparison info

- **AI DM Combat Integration**
  - DM narrates combat cinematically
  - Strict output filtering (prevents DM from generating fake roll results)
  - Victory narration on enemy defeat
  - Death narration on player defeat

- **Combat Test Suite**
  - `tests/test_combat_with_dm.py` - Full integration test with AI DM
  - Typo tolerance (unknown commands don't skip turns)

### Changed
- Character class now has `get_ability_modifier(ability_name)` method
- Improved error handling for unrecognized combat commands

---

## [0.4.0] - 2024-12-16

### Added
- **Phase 2.1: Skill Check System** - Integrated dice rolling with AI DM
  - Automatic dice rolling when DM requests checks
  - DM uses `[ROLL: SkillName DC X]` format to request rolls
  - Full D&D 5e skill-to-ability mapping (18 skills)
  - Press Enter to roll mechanic for player engagement
  - Natural 20 and Natural 1 special handling
  - Visual roll results with success/failure indicators
  
- **New Character Method**
  - `get_ability_modifier(ability_name)` - Get modifier by ability name

- **Skill Mappings**
  - STR: Athletics
  - DEX: Acrobatics, Sleight of Hand, Stealth
  - INT: Arcana, History, Investigation, Nature, Religion
  - WIS: Animal Handling, Insight, Medicine, Perception, Survival
  - CHA: Deception, Intimidation, Performance, Persuasion

### Changed
- Updated DM system prompt with skill check instructions
- Game loop now parses DM responses for roll requests
- Multiple consecutive rolls supported (DM can chain checks)
- Help command updated with dice rolling info

---

## [0.3.0] - 2024-12-15

### Added
- **Phase 1.3: Scene/Scenario System** - Structured adventures with story progression
  - New `src/scenario.py` module with Scene and Scenario classes
  - ScenarioManager for tracking adventure state
  - Scene transitions with objective tracking
  - Minimum exchange count for pacing control
  - AI receives scene context for guided narration

- **First Adventure: "The Goblin Cave"**
  - 6-scene complete adventure (~20-40 minutes)
  - Rescue quest: Save a farmer's daughter from goblins
  - Scenes: Tavern Hook → Journey → Cave Entrance → Goblin Camp → Boss Fight → Resolution
  - Objectives and transition triggers for each scene
  - Detailed DM instructions for consistent storytelling

- **New Commands**
  - `progress` - Show current scenario progress with visual bar
  - Adventure selection menu at game start
  - Free Play mode option (no structured scenario)

### Changed
- Game now offers scenario selection before starting
- AI receives scene-specific context for better narration
- `create_client()` now accepts scenario context parameter
- `get_dm_response()` injects scene context into prompts
- Updated help command to show scenario-specific commands

---

## [0.2.1] - 2024-12-15

### Added
- **Streaming AI Responses** - DM text now appears word-by-word as it's generated
  - Reduced perceived latency - user sees text immediately
  - More immersive typing effect
  - Uses Gemini's native streaming API

### Changed
- `get_dm_response()` now streams by default (optional `stream` parameter)
- Improved user experience during AI response generation

---

## [0.2.0] - 2024-12-15

### Added
- **Phase 1.2: Basic Character Sheet** - Full character system
  - New `src/character.py` module with `Character` dataclass
  - Interactive character creation (name, race, class, stats)
  - Quick start option for random character generation
  - 9 D&D races: Human, Elf, Dwarf, Halfling, Half-Orc, Tiefling, Dragonborn, Gnome, Half-Elf
  - 12 D&D classes: Fighter, Wizard, Rogue, Cleric, Ranger, Barbarian, Paladin, Warlock, Bard, Monk, Druid, Sorcerer
  - 4d6-drop-lowest stat rolling
  - ASCII character sheet display with HP bar
  - HP and AC calculation based on class and stats

- **New In-Game Commands**
  - `stats` / `character` / `sheet` - View character sheet
  - `hp` - Quick HP check with visual bar
  - `help` / `?` - Show available commands

- **AI Integration**
  - DM receives character context (race, class, stats)
  - Opening narrative tailored to character

- **Error Handling**
  - Graceful exit on KeyboardInterrupt
  - Graceful exit on EOFError

### Changed
- Updated `src/game.py` to integrate character system
- DM system prompt now includes character context
- Opening narration customized per character

### Documentation
- Updated README with gameplay section
- Added terminal usage warning (use dedicated terminal)
- Documented new commands and character creation
- Updated DEVELOPMENT_PLAN.md with Phase 1.2 complete

---

## [0.1.0] - 2024-12-15

### Added
- **Phase 1.1: Simple Chat Loop** - Core game functionality
  - Main game file (`src/game.py`) with AI Dungeon Master
  - Google Gemini 2.0 Flash integration via `google-generativeai`
  - System prompt defining DM behavior and narrative style
  - Interactive conversation loop with player input
  - Conversation history maintained throughout session
  
- **Project Configuration**
  - `.env` support for API keys and model selection via `python-dotenv`
  - `.env.example` template for configuration
  - `requirements.txt` with dependencies
  - `.gitignore` to protect sensitive files
  
- **Documentation**
  - `README.md` with setup instructions and project overview
  - `DEVELOPMENT_PLAN.md` with 6-phase roadmap
  - `CHANGELOG.md` (this file)

### Technical Details
- Python 3.14 virtual environment
- Google Gemini API for AI responses
- Configurable model via `GEMINI_MODEL` environment variable
- Default model: `gemini-2.0-flash`

### Tested
- ✅ AI DM creates immersive opening narrative
- ✅ Player actions receive contextual responses
- ✅ Conversation history maintains context
- ✅ Inventory queries answered naturally
- ✅ Quest/reward dialogue works properly
- ✅ Graceful exit with "quit" command

---

## Version History

| Version | Date | Phase | Description |
|---------|------|-------|-------------|
| 0.1.0 | 2024-12-15 | 1.1 | Simple Chat Loop - Initial working version |

---

## Upcoming Versions

| Version | Phase | Features |
|---------|-------|----------|
| 0.2.0 | 1.2 | Basic Character Sheet (name, class, stats) |
| 0.3.0 | 1.3 | Starting Scenario (hardcoded encounter) |
| 0.4.0 | 2.1-2.4 | Dice, Combat, Inventory mechanics |
| 0.5.0 | 3.1-3.3 | Save/Load, Locations, NPCs |
| 0.6.0 | 4.1-4.3 | Advanced AI features |
| 1.0.0 | 5.1-5.4 | Backend API |
| 2.0.0 | 6.1-6.8 | Flutter App (iOS, Android, Web, Desktop) |
