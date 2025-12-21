# AI D&D Text RPG - Project Documentation

## Overview
A text-based Dungeons & Dragons style RPG where Google Gemini AI acts as the Dungeon Master, creating an interactive storytelling experience.

---

## Project Structure

```
AI RPG V2/
├── .env                    # Environment variables (API keys) - DO NOT COMMIT
├── .env.example            # Template for .env file
├── .gitignore              # Git ignore patterns
├── .venv/                  # Python virtual environment
├── README.md               # This file
├── requirements.txt        # Python dependencies
├── task.py                 # TaskSync helper script
├── tasksync.md             # TaskSync protocol
├── saves/                  # Game save files (auto-created)
├── docs/
│   ├── CHANGELOG.md            # Version history
│   ├── DEVELOPER_GUIDE.md      # Technical documentation
│   ├── DEVELOPMENT_PLAN.md     # Phased development roadmap
│   ├── FLUTTER_SETUP.md        # Flutter installation guide
│   ├── THEME_SYSTEM_SPEC.md    # DLC-ready theme architecture
│   └── UI_DESIGN_SPEC.md       # UI/UX specifications
├── src/
│   ├── __init__.py         # Package initializer
│   ├── character.py        # Character system (stats, XP, leveling)
│   ├── combat.py           # Combat system (multi-enemy, surprise)
│   ├── game.py             # Main game logic
│   ├── inventory.py        # Items and inventory
│   ├── npc.py              # NPC system (dialogue, shops, relationships)
│   ├── quest.py            # Quest tracking system
│   ├── save_system.py      # Save/Load persistence
│   └── scenario.py         # Adventure scenarios
└── tests/                   # 821 tests total
    ├── test_character.py      # Character system tests (26 tests)
    ├── test_combat.py          # Combat unit tests (31 tests)
    ├── test_combat_with_dm.py  # Combat integration tests (3 tests)
    ├── test_dialogue.py        # NPC dialogue tests (24 tests)
    ├── test_flexible_travel.py # Flexible travel input tests (25 tests)
    ├── test_flow_breaking.py   # Flow breaking tests (29 tests)
    ├── test_hostile_player.py  # Adversarial tests (44 tests)
    ├── test_inventory.py       # Inventory tests (35 tests)
    ├── test_location.py        # Location system tests (200 tests)
    ├── test_location_with_dm.py # Location integration tests (13 tests)
    ├── test_multi_enemy.py     # Multi-enemy tests (3 tests)
    ├── test_npc.py             # NPC system tests (55 tests)
    ├── test_party.py           # Party/companion tests (72 tests)
    ├── test_prompt_injection.py # Security tests (22 tests)
    ├── test_quest.py           # Quest system tests (57 tests)
    ├── test_reputation.py      # Disposition system tests (55 tests)
    ├── test_reputation_hostile.py # Disposition adversarial tests (36 tests)
    ├── test_save_system.py     # Save/Load tests (8 tests)
    ├── test_scenario.py        # Scenario tests (31 tests)
    ├── test_travel_menu.py     # Travel menu system tests (42 tests)
    ├── test_xp_system.py       # XP/Leveling tests (10 tests)
    └── run_interactive_tests.py # Unified test runner
```

---

## Current Features (Phase 1-4 Complete)

### ✅ AI Dungeon Master
- **Google Gemini 2.0 Flash** provides intelligent, contextual responses
- **Streaming Responses** - Text appears word-by-word as AI generates it
- **Conversation Memory** - Chat history maintained throughout session
- **Character-Aware** - AI knows your race, class, and stats
- **Scene-Aware** - AI follows structured scenario guidance
- **Configurable** - Model and API key stored in `.env` file
- **Enhanced Skill Checks** - DM prompted for Perception, Stealth, Persuasion, etc.
- **Smart Skill Hints** - Automatic hints for exploration, stealth, and social actions

### ✅ Character System
- **Character Creation** - Choose name, race (9 options), class (12 options)
- **Stat Rolling** - 4d6-drop-lowest for authentic D&D feel
- **Quick Start** - Random character generation available
- **Character Sheet** - ASCII art display with all stats
- **HP/AC Calculation** - Based on class and constitution/dexterity
- **XP & Leveling** - Level 1-5 with milestone XP rewards
- **Proficiency Bonus** - Scales with level (+2 to +3)

### ✅ Combat System
- **D&D 5e Rules** - Initiative, attack rolls, damage
- **Multi-Enemy Combat** - Fight multiple enemies simultaneously
- **Surprise Rounds** - Ambush mechanics with advantage
- **Turn Order** - Initiative-based combat sequence
- **Defend Action** - +2 AC bonus until next turn
- **Flee Option** - Escape combat with DEX check

### ✅ Inventory System
- **Item Types** - Weapons, armor, consumables, quest items
- **Stats Display** - See `[DMG: 1d8]` for weapons, `[AC: +2]` for armor inline
- **Equipment** - Equip weapons and armor with `equip <item>`
- **Auto-Equip** - Purchased armor automatically replaces old armor
- **Loot Drops** - Random loot from defeated enemies
- **Gold Tracking** - Currency system

### ✅ Scenario System
- **Structured Adventures** - Scenes with objectives and transitions
- **First Adventure: "The Goblin Cave"** - Complete 6-scene rescue quest
- **Free Play Mode** - Unstructured play also available
- **Progress Tracking** - See where you are in the story
- **Pacing Control** - Minimum exchanges per scene

### ✅ Save/Load System
- **Save Games** - Save to numbered slots or timestamped files
- **Load Games** - Resume from main menu or during play
- **Persistent Progress** - Character, inventory, scenario, location state saved
- **Multi-Platform Ready** - API-ready for cloud saves

### ✅ Location System (NEW!)
- **Explorable World** - 18+ locations in Goblin Cave adventure
- **Cardinal Movement** - Move north/south/east/west (n/s/e/w shortcuts)
- **Flexible Travel** - Natural language like "go to the village square" works!
- **Interactive Locations** - Items to pick up, NPCs to encounter
- **Location Events** - Traps, discoveries, and confrontations
- **AI Narration** - Immersive, atmospheric location descriptions
- **Conditional Exits** - Locked doors requiring keys/items/skill checks
- **Secret Areas** - Hidden locations discoverable via skill checks
- **Random Encounters** - Chance-based enemy spawns
- **Visit Tracking** - Locations remember when you've been there

### ✅ Shop System (NEW!)
- **Browse & Buy** - Purchase items from merchant NPCs
- **Stats in Shop** - See item stats: `Longsword [DMG: 1d8]...17g ✓`
- **Affordability Markers** - ✓ (can afford) and ✗ (too expensive)
- **Auto Gold Deduction** - `[BUY: item, price]` tag handles shop purchases
- **Sell Loot** - Sell items for 50% of base value
- **Haggle Mechanic** - CHA DC 12 check for 20% discount (or +10% penalty!)
- **Stock Tracking** - Merchants have limited quantities of items
- **Quantity Purchasing** - Buy multiple items: "buy 3 healing potions"
- **Natural Language** - 85+ trigger phrases: "what do you have", "show me your wares"
- **Gold Command** - Quick `gold` or `g` to check your coins
- **Village Blacksmith** - Gavin sells weapons/armor (opens late for adventurers)
- **Trader Mira** - Traveling merchant in forest clearing
- **AI Narration** - Immersive shopping experience with AI responses

### ✅ Traveling Merchants (NEW!)
- **Dynamic Spawning** - Merchants appear randomly at locations
- **Zephyr the Wanderer** - Mysterious traveling merchant with rare items
- **Inventory Rotation** - Different items each time they appear
- **Spawn Cooldown** - Won't reappear at same spot too quickly
- **Rare Items** - Enchanted weapons and ancient relics available

### ✅ NPC Relationships (NEW!)
- **Disposition System** - NPCs remember how you treat them (-100 to +100)
- **Reputation Levels** - Hostile, Unfriendly, Neutral, Friendly, Trusted
- **Price Modifiers** - Better prices from friendly NPCs (up to 20% discount!)
- **Trade Restrictions** - Hostile NPCs refuse to trade
- **Visual Indicators** - Color-coded labels (🔴 Hostile → 🔵 Trusted)
- **Action-Based Disposition** - Your actions affect NPC relationships:
  - **Trade Actions** - +1 disposition per buy/sell, +2 for successful haggle
  - **Gift System** - `give <item> to <npc>` for +5 to +20 disposition based on value
  - **Theft System** - `steal from <npc>` with DEX DC 15 check (risk -30 to -50!)
  - **Quest Completion** - +25 (main), +15 (side), +10 (minor) to quest giver
- **Robust System** - Handles edge cases, tested with 98 reputation tests

### ✅ Enhanced Skill Checks (NEW!)
- **Contextual Hints** - DM receives hints when to call for skill checks
- **Exploration Triggers** - "look", "search", "examine" → Perception hints
- **Stealth Triggers** - "sneak", "hide", "quietly" → Stealth hints
- **Social Triggers** - Persuasion, Intimidation, Deception, Insight based on context
- **Physical Triggers** - Climbing, jumping, breaking actions detected
- **Clear DC Guidelines** - Easy=10, Medium=13, Hard=15, Very Hard=18

### ✅ Flexible Travel (NEW!)
- **Natural Language** - "go to the village square", "head to the tavern"
- **First-Person Support** - "I go east", "I walk north", "I head outside"
- **Destination Matching** - "village square" matches exit leading to village_square
- **Filler Word Stripping** - "to the", "towards the", "into the" removed
- **Fuzzy Matching** - Underscores and spaces interchangeable
- **Smart Shop Redirect** - "go to blacksmith" hints to use `shop` command

### ✅ XP Progress Display (NEW!)
- **Visual Progress** - After XP gain: `📈 Level 2: 50/100 XP (50 needed)`
- **Max Level Indicator** - At max: `📈 Max Level reached! (1250 total XP)`
- **Works Everywhere** - Combat XP and quest XP rewards tracked

### ✅ Travel Menu System (NEW!)
- **Numbered Destinations** - Type `travel` or `where` to see available exits with numbers
- **Quick Selection** - Type just the number (e.g., "1", "2") to travel instantly
- **Danger Indicators** - Visual cues for location safety:
  - ⚠️ Threatening - Known dangerous location
  - ☠️ Deadly - Very dangerous area
  - ❓ Uneasy - Unexplored or may have random encounters
  - ✓ Safe - Previously visited safe location
- **Two-Phase Travel** - Dangerous destinations prompt "How do you approach?"
- **Approach Styles** - Detected from natural language:
  - **Stealth** - "sneak", "quietly", "in shadows" → Stealth check
  - **Cautious** - "carefully", "look around", "wary" → Perception check
  - **Urgent** - "run", "rush", "sprint" → Quick travel narrative
- **Skill Check Integration** - Failed stealth can trigger SURPRISE combat
- **Location-Based DCs** - Each area has custom stealth/perception difficulty

### ✅ Party/Companion System (NEW!)
- **Recruit Companions** - Find and recruit NPCs to join your party
- **Max 2 Companions** - Strategic party composition matters
- **Party Combat** - Companions fight alongside you with their own turns
- **Class Abilities** - Each companion class has unique special abilities:
  - **Fighter** - Shield Wall (+2 AC to party)
  - **Ranger** - Hunter's Mark (+1d4 damage)
  - **Rogue** - Sneak Attack (+2d6 when flanking)
  - **Cleric** - Healing Word (1d8+2 heal)
  - **Wizard** - Magic Missile (auto-hit 1d4+1)
- **Flanking Bonus** - +2 attack when you and companion target same enemy
- **Recruitment Conditions** - Skill checks, gold, items, or quest objectives
- **Predefined Companions** - Marcus (Fighter), Elira (Ranger), Shade (Rogue)
- **Full Persistence** - Party state saves/loads with game

### How It Works
1. Player launches the game and creates a character (or loads a save)
2. Player selects an adventure or Free Play mode
3. AI DM sets the scene tailored to your character
4. Player types actions (e.g., "I search the room", "I talk to the innkeeper")
5. AI responds with streaming text following scene guidance
6. Combat, skill checks, and loot are handled automatically
7. Player can save progress at any time
8. Adventure concludes with resolution scene

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language (Backend) | Python 3.10+ |
| Language (Frontend) | Dart (Flutter) - Planned |
| AI Provider | Google Gemini |
| AI Model | Configurable via `.env` (default: gemini-2.5-pro) |
| AI Library | google-generativeai (0.8.x) |
| Config | python-dotenv |
| Frontend Framework | Flutter (iOS, Android, Web, Desktop) - Planned |

---

## Setup Instructions

### Prerequisites
- Python 3.10+
- Google AI API key (get from [Google AI Studio](https://aistudio.google.com/))

### Installation

1. **Clone/Navigate to project**
   ```bash
   cd "AI RPG V2"
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Mac/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

5. **Run the game**
   ```bash
   python src/game.py
   ```

> **⚠️ Important:** Run the game in its own dedicated terminal window. If using VS Code, open a new terminal (Ctrl+Shift+`) specifically for gameplay to avoid conflicts with other terminal sessions.

---

## Gameplay

### Character Creation
When you start the game, you can:
1. **Create character** - Choose name, race, class, and roll stats
2. **Quick start** - Generate a random character instantly
3. **Load saved game** - Continue a previous adventure (if saves exist)

### In-Game Commands

| Command | Action |
|---------|--------|
| `stats`, `character`, `sheet` | View your character sheet |
| `hp` | Quick HP check with visual bar |
| `xp`, `level` | View XP progress and level |
| `levelup` | Level up when ready |
| `inventory`, `inv`, `i` | View your inventory |
| `use <item>` | Use a consumable item |
| `equip <item>` | Equip a weapon or armor |
| `travel`, `where` | Show travel menu with numbered destinations |
| `go <direction>` | Move to another location |
| `look`, `scan` | Examine current location |
| `shop` | Browse merchant inventory |
| `buy <item>` | Purchase from merchant |
| `sell <item>` | Sell item to merchant |
| `gold`, `g` | Check your gold |
| `talk <npc>` | Talk to an NPC |
| `party`, `companions` | View party roster |
| `recruit <name>` | Attempt to recruit NPC |
| `quests`, `journal` | View active quests |
| `rest` | Short rest to heal (uses Hit Dice) |
| `save` | Save your game |
| `load` | Load a saved game |
| `saves` | List all saved games |
| `help`, `?` | Show all commands |
| `quit`, `exit`, `q` | Exit the game gracefully |
| Any other text | Send your action to the Dungeon Master |

### Example Session
```
⚔️  Your action: I search the room for hidden doors
🎲 Dungeon Master: You run your hands along the stone walls...

⚔️  Your action: stats
╔═══════════════════════════════════════════════════╗
║                 CHARACTER SHEET                   ║
║  Name:  Amir          Level: 1                    ║
║  Race:  Human         Class: Fighter              ║
...

⚔️  Your action: quit
```

---

## Files Description

### src/game.py
Main game file containing:
- `DM_SYSTEM_PROMPT_BASE`: Instructions that define AI behavior as a Dungeon Master
- `create_client()`: Initializes Gemini API with character context
- `get_dm_response()`: Sends player input and receives AI response
- `show_help()`: Display available commands
- `main()`: Game loop with character creation and command handling

### src/character.py
Character system containing:
- `Character`: Dataclass with stats, HP, AC, and display methods
- `create_character_interactive()`: Full character creation flow
- `quick_create_character()`: Random character generation
- D&D races and classes lists

### requirements.txt
```
google-generativeai>=0.8.0
python-dotenv>=1.0.0
```

### .env.example
Template for creating your `.env` file with required API configuration.

---

## Configuration

### Environment Variables (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Your Google AI API key | Required |
| `GEMINI_MODEL` | AI model to use | `gemini-2.5-pro` |
| `SAVES_DIR` | Directory for save files | `./saves` |

### Available Models
- `gemini-2.5-pro` - Latest, most capable (recommended)
- `gemini-2.5-flash` - Fast and capable
- `gemini-1.5-pro` - Previous generation
- `gemini-1.5-flash` - Previous gen, fast

---

## Roadmap

See [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) for full roadmap including:
- Phase 1: Core Foundation ✅ Complete
- Phase 2: Game Mechanics ✅ Complete (dice, combat, inventory, XP/leveling)
- Phase 3: World & Persistence ✅ Complete
  - 3.1 Save/Load ✅ Complete
  - 3.2 Location System ✅ Complete (200 tests)
  - 3.3 NPC System ✅ Complete (Dialogue, Shops, Quests, Party)
  - 3.4 Moral Choices & Consequences ⬜
- Phase 4: Security & Testing ✅ Complete (131 security tests, 5 bugs fixed)
- Phase 5: Advanced AI Features (memory, dynamic generation)
- Phase 6: Backend API
- Phase 7: Flutter App
- Phase 8: Theme Store & Monetization

---

## Documentation

| Document | Description |
|----------|-------------|
| [DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) | Full development roadmap |
| [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) | Technical implementation details |
| [CHANGELOG.md](docs/CHANGELOG.md) | Version history |
| [UI_DESIGN_SPEC.md](docs/UI_DESIGN_SPEC.md) | UI/UX specifications |
| [THEME_SYSTEM_SPEC.md](docs/THEME_SYSTEM_SPEC.md) | DLC-ready theme architecture |
| [FLUTTER_SETUP.md](docs/FLUTTER_SETUP.md) | Flutter installation guide |

---

## Development Notes

### What Works Well
- Gemini creates engaging, contextual narratives
- Maintains conversation history within session
- Responds naturally to varied player inputs
- Provides character backstory and inventory organically
- Full D&D 5e combat with multi-enemy and surprise mechanics
- Comprehensive location system with 174 passing tests
- AI-driven immersive location narration

### Current Focus
- NPC System (Phase 3.3) - Dialogue, shops, quests, party members
- See [DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) for detailed task breakdown

---

## Contributing

This is an incremental development project. Each phase builds on the previous one. See `docs/DEVELOPMENT_PLAN.md` for what's next.

---

## License

Private project - All rights reserved.
