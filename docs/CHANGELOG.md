# Changelog

All notable changes to the AI D&D Text RPG project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Planned
- Phase 3: World & Persistence

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
