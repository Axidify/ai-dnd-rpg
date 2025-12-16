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
│   ├── save_system.py      # Save/Load persistence
│   └── scenario.py         # Adventure scenarios
└── tests/
    ├── test_combat_with_dm.py  # Combat integration tests
    ├── test_dice.py            # Dice rolling tests
    ├── test_dice_with_dm.py    # Dice + AI tests
    ├── test_multi_enemy.py     # Multi-enemy tests
    ├── test_save_system.py     # Save/Load tests
    └── test_xp_system.py       # XP/Leveling tests
```

---

## Current Features (Phase 1-3.1 Complete)

### ✅ AI Dungeon Master
- **Google Gemini 2.0 Flash** provides intelligent, contextual responses
- **Streaming Responses** - Text appears word-by-word as AI generates it
- **Conversation Memory** - Chat history maintained throughout session
- **Character-Aware** - AI knows your race, class, and stats
- **Scene-Aware** - AI follows structured scenario guidance
- **Configurable** - Model and API key stored in `.env` file

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
- **Equipment** - Equip weapons and armor
- **Loot Drops** - Random loot from defeated enemies
- **Gold Tracking** - Currency system

### ✅ Scenario System
- **Structured Adventures** - Scenes with objectives and transitions
- **First Adventure: "The Goblin Cave"** - Complete 6-scene rescue quest
- **Free Play Mode** - Unstructured play also available
- **Progress Tracking** - See where you are in the story
- **Pacing Control** - Minimum exchanges per scene

### ✅ Save/Load System (NEW!)
- **Save Games** - Save to numbered slots or timestamped files
- **Load Games** - Resume from main menu or during play
- **Persistent Progress** - Character, inventory, scenario state saved
- **Multi-Platform Ready** - API-ready for cloud saves

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
| Language (Backend) | Python 3.14 |
| Language (Frontend) | Dart (Flutter) |
| AI Provider | Google Gemini (gemini-2.0-flash) |
| AI Library | google-generativeai |
| Config | python-dotenv |
| Frontend Framework | Flutter (iOS, Android, Web, Desktop) |

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
| `GEMINI_MODEL` | AI model to use | `gemini-2.0-flash` |

### Available Models
- `gemini-2.0-flash` - Fast, cost-effective (recommended)
- `gemini-1.5-pro` - More capable, slower
- `gemini-1.5-flash-latest` - Latest flash version

---

## Roadmap

See [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) for full roadmap including:
- Phase 1: Core Foundation (1.1 ✅ Complete)
- Phase 2: Game Mechanics (dice, combat, inventory)
- Phase 3: World & Persistence (save/load, locations, NPCs)
- Phase 4: Advanced AI Features (memory, dynamic generation)
- Phase 5: Backend API
- Phase 6: Flutter App
- Phase 7: Theme Store & Monetization

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

### Known Limitations
- No persistent save (resets each session)
- No actual game mechanics (dice, HP, etc.)
- Character created by AI, not player customizable
- No structured inventory system

---

## Contributing

This is an incremental development project. Each phase builds on the previous one. See `docs/DEVELOPMENT_PLAN.md` for what's next.

---

## License

Private project - All rights reserved.
