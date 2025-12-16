# Developer Documentation

## AI D&D Text RPG - Technical Guide

This document provides comprehensive technical documentation for developers who want to understand, maintain, or contribute to the AI D&D Text RPG project.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [AI Integration](#ai-integration)
5. [Configuration System](#configuration-system)
6. [Game Loop Logic](#game-loop-logic)
7. [Save/Load System](#saveload-system)
8. [Extending the Game](#extending-the-game)
9. [Testing Guidelines](#testing-guidelines)
10. [Deployment](#deployment)
11. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### Current Architecture (Phase 1)

```
┌─────────────────────────────────────────────────────────────┐
│                      Terminal (CLI)                         │
│                   Player Input/Output                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      game.py                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   main()    │→ │  Chat Loop  │→ │   Output    │         │
│  │  Initialize │  │   Process   │  │  Response   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 Google Gemini API                           │
│              (generativeai library)                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  System Prompt (DM_SYSTEM_PROMPT)                   │   │
│  │  + Chat History (maintained in session)             │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Planned Architecture (Phase 5-6)

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  Flutter App  │     │  Flutter App  │     │  Flutter App  │
│    Mobile     │     │     Web       │     │   Desktop     │
│  (iOS/Android)│     │   (Browser)   │     │ (Win/Mac/Lin) │
└───────┬───────┘     └───────┬───────┘     └───────┬───────┘
        │                     │                     │
        └──────────────┬──────┴──────────────┬──────┘
                       │                     │
                       ▼                     ▼
        ┌─────────────────────────────────────────────┐
        │              FastAPI Backend                │
        │  ┌───────────────┐  ┌───────────────┐      │
        │  │  Auth Service │  │  Game Logic   │      │
        │  │  AI Handler   │  │  Save/Load    │      │
        │  └───────────────┘  └───────────────┘      │
        └──────────────────────┬──────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
  ┌──────────┐          ┌──────────┐          ┌──────────┐
  │ Gemini   │          │ Database │          │  Redis   │
  │   API    │          │ Postgres │          │  Cache   │
  └──────────┘          └──────────┘          └──────────┘
```

**Flutter Target Platforms:**
- 📱 iOS (App Store)
- 📱 Android (Play Store)
- 🌐 Web (Any browser)
- 🖥️ Windows (Downloadable)
- 🖥️ macOS (Downloadable)
- 🐧 Linux (Downloadable)

---

## Project Structure

```
ai-dnd-rpg/
│
├── .env                    # Environment variables (NEVER COMMIT)
├── .env.example            # Template for environment setup
├── .gitignore              # Git ignore patterns
├── .venv/                  # Python virtual environment
│
├── docs/
│   ├── CHANGELOG.md            # Version history
│   ├── DEVELOPER_GUIDE.md      # This file
│   ├── DEVELOPMENT_PLAN.md     # Project roadmap with phases
│   ├── FLUTTER_SETUP.md        # Flutter installation guide
│   ├── THEME_SYSTEM_SPEC.md    # DLC-ready theme architecture
│   └── UI_DESIGN_SPEC.md       # UI/UX specifications
│
├── saves/                  # Game save files (auto-created)
│   └── save_*.json             # Individual save files
│
├── README.md               # User-facing documentation
├── requirements.txt        # Python dependencies
├── task.py                 # TaskSync task input helper
├── task.txt                # TaskSync task queue file
├── tasksync.md             # Development protocol
│
├── src/
│   ├── __init__.py         # Package marker
│   ├── character.py        # Character system (stats, creation, XP/leveling)
│   ├── combat.py           # Combat system (attacks, damage, multi-enemy)
│   ├── game.py             # Main game logic, AI integration
│   ├── inventory.py        # Item and inventory management
│   ├── save_system.py      # Save/Load system (Phase 3.1)
│   └── scenario.py         # Scenario and scene management
│
└── tests/
    ├── test_character.py       # Character system tests (26 tests)
    ├── test_combat.py           # Combat mechanics tests (28 tests)
    ├── test_combat_with_dm.py   # Interactive combat tests
    ├── test_dice.py             # Dice rolling tests
    ├── test_dice_with_dm.py     # Dice + AI tests
    ├── test_inventory.py        # Inventory system tests (35 tests)
    ├── test_inventory_with_dm.py # Interactive inventory tests
    ├── test_multi_enemy.py      # Multi-enemy combat tests
    ├── test_save_system.py      # Save/Load system tests (6 tests)
    ├── test_scenario.py         # Scenario system tests (26 tests)
    └── test_xp_system.py        # XP and leveling tests (10 tests)
```

### File Responsibilities

| File | Purpose | Modify When |
|------|---------|-------------|
| `src/game.py` | Core game logic, AI integration | Adding game features |
| `src/character.py` | Character class, stats, XP/leveling | Adding character features |
| `src/combat.py` | Combat mechanics, multi-enemy | Modifying combat |
| `src/inventory.py` | Items, equipment, loot | Adding items/equipment |
| `src/save_system.py` | Save/Load persistence | Changing save format |
| `src/scenario.py` | Story scenarios, scenes | Adding scenarios |
| `.env` | API keys, configuration | Changing providers/models |
| `requirements.txt` | Dependencies | Adding libraries |
| `docs/DEVELOPMENT_PLAN.md` | Roadmap | Planning new phases |
| `docs/CHANGELOG.md` | Version tracking | Releasing versions |
| `docs/THEME_SYSTEM_SPEC.md` | Theme/DLC architecture | Theme system changes |

---

## Core Components

### 1. System Prompt (`DM_SYSTEM_PROMPT_BASE`)

The system prompt is **critical** - it defines how the AI behaves as a Dungeon Master.

```python
DM_SYSTEM_PROMPT_BASE = """You are an experienced Dungeon Master...

Your responsibilities:
- Narrate the story in an engaging, immersive way
- Describe environments, NPCs, and events vividly
...
"""
```

The prompt is combined with character context when a player creates a character, so the AI knows:
- Player's name, race, and class
- Their ability scores
- HP and AC values

**Best Practices for Modifying:**
- Keep instructions clear and specific
- Test changes thoroughly - small wording changes can significantly affect behavior
- Add examples if the AI doesn't understand a concept
- Use bullet points for lists of behaviors

**When to Modify:**
- Adding new game mechanics
- Changing narrative style
- Adding constraints or rules

### 2. Client Initialization (`create_client()`)

```python
def create_client(character: Character = None):
    """Configure and return the Gemini model with character context."""
    api_key = os.getenv("GOOGLE_API_KEY")
    # ... validation ...
    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    
    # Build system prompt with character context
    system_prompt = DM_SYSTEM_PROMPT_BASE
    if character:
        system_prompt += "\n" + character.get_context_for_dm()
    
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt
    )
    return model
```

**Key Points:**
- Always read API key from environment, never hardcode
- Default model is `gemini-2.0-flash` (fast, cost-effective)
- System instruction includes character context when provided
- Character's race, class, and stats are passed to AI

### 3. Response Handler (`get_dm_response()`)

```python
def get_dm_response(chat, player_input, stream=True):
    """Get a response from the AI Dungeon Master."""
    try:
        if stream:
            response = chat.send_message(player_input, stream=True)
            full_response = ""
            for chunk in response:
                if chunk.text:
                    print(chunk.text, end="", flush=True)
                    full_response += chunk.text
            print()  # Final newline
            return full_response
        else:
            response = chat.send_message(player_input)
            return response.text
    except Exception as e:
        return f"[DM Error: {str(e)}]"
```

**Streaming Mode (Default):**
- Prints text as it arrives from the API
- Creates a "typing" effect for better UX
- Uses `flush=True` to force immediate display
- Reduces perceived latency

**Non-Streaming Mode:**
- Set `stream=False` if you need the full response before displaying
- Useful for processing/parsing responses before showing

**Important:**
- Uses Gemini's chat sessions (maintains history automatically)
- Error handling prevents crashes
- Returns error message to user for debugging

### 4. Game Loop (`main()`)

```python
def main():
    # 1. Character creation
    character = create_character_interactive()  # or quick_create()
    
    # 2. Initialize with character context
    model = create_client(character)
    chat = model.start_chat(history=[])
    
    # 3. Opening narration (streamed)
    print("🎲 Dungeon Master:")
    get_dm_response(chat, f"Welcome {character.name}...")
    
    # 4. Game loop with commands
    while True:
        player_input = input("⚔️  Your action: ").strip()
        
        # Handle special commands
        if player_input.lower() in ["quit", "exit", "q"]:
            break
        if player_input.lower() in ["stats", "character", "sheet"]:
            print(character.get_stat_block())
            continue
        if player_input.lower() == "hp":
            print(f"HP: {character.current_hp}/{character.max_hp}")
            continue
        
        # Get AI response (streams to terminal)
        print("🎲 Dungeon Master:")
        get_dm_response(chat, player_input)
```

### 5. Character System (`character.py`)

```python
@dataclass
class Character:
    # Basic Info
    name: str
    race: str           # Human, Elf, Dwarf, etc.
    char_class: str     # Fighter, Wizard, Rogue, etc.
    level: int = 1
    
    # Ability Scores (D&D 5e)
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int
    
    # Derived Stats
    max_hp: int         # Calculated from class + CON
    current_hp: int
    armor_class: int    # 10 + DEX modifier (unarmored)
```

**Key Methods:**
- `Character.create_random(name)` - Generate random character
- `create_character_interactive()` - Full creation flow with choices
- `character.get_stat_block()` - ASCII art character sheet
- `character.get_context_for_dm()` - Formatted info for AI prompt

**D&D Rules Implemented:**
- 4d6-drop-lowest stat rolling
- HP = Hit die + CON modifier (varies by class)
- AC = 10 + DEX modifier (unarmored)
- Modifier = (score - 10) // 2

### Starting Equipment System

When a character is created with `create_random()` or `create_character_interactive()`, the `_add_starting_equipment()` method is called automatically.

**Universal Starting Gear (all classes):**

| Item | Quantity | Purpose |
|------|----------|--------|
| Gold | 10-25 gp | Starting currency |
| Healing Potion | 1 | Emergency healing |
| Rations | 3 | Food supplies |
| Torch | 2 | Light source |

**Class-Specific Gear:**

| Class | Weapon | Armor | Special |
|-------|--------|-------|--------|
| Fighter | Longsword | Chain Shirt | — |
| Paladin | Longsword | Chain Shirt | — |
| Ranger | Shortbow | Leather Armor | — |
| Barbarian | Greataxe | Leather Armor | — |
| Wizard | Quarterstaff | — | — |
| Sorcerer | Dagger | — | — |
| Rogue | Shortsword | Leather Armor | Lockpicks |
| Bard | Shortsword | Leather Armor | — |
| Warlock | Dagger | Leather Armor | — |
| Monk | Quarterstaff | — | — |
| Cleric | Mace | Chain Shirt | — |
| Druid | Quarterstaff | Leather Armor | — |

**Code Location:** `character.py` → `Character._add_starting_equipment()`

**Note:** Armor is automatically equipped and AC is adjusted when adding armor with `ac_bonus`.

---

## AI Integration

### Google Gemini Setup

**Library:** `google-generativeai`

**Authentication:**
1. Get API key from [Google AI Studio](https://aistudio.google.com/)
2. Add to `.env`: `GOOGLE_API_KEY=your-key`

**Available Models:**

| Model | Speed | Quality | Cost | Use Case |
|-------|-------|---------|------|----------|
| `gemini-2.0-flash` | Fast | Good | Low | Default, testing |
| `gemini-1.5-flash-latest` | Fast | Good | Low | Alternative |
| `gemini-1.5-pro` | Slower | Best | Higher | Production |

### Chat Sessions

Gemini maintains conversation history automatically via chat sessions:

```python
chat = model.start_chat(history=[])  # New session
chat.send_message("Player action")    # History auto-updated
```

**Limitations:**
- History is in-memory only (lost on restart)
- No built-in persistence (planned for Phase 3)
- Context window limit depends on model

### Prompt Engineering Tips

1. **Be Specific**: "Describe the room in 2-3 sentences" vs "Describe the room"
2. **Use Examples**: Show the AI what good output looks like
3. **Set Constraints**: "Do not reveal the enemy's HP directly"
4. **Define Behaviors**: "When player asks to roll dice, describe the result narratively"

---

## Inventory System

The inventory system (`src/inventory.py`) manages items, equipment, and loot.

### Item Types

| Type | Value | Examples |
|------|-------|----------|
| `WEAPON` | `"weapon"` | Longsword, Dagger, Shortbow |
| `ARMOR` | `"armor"` | Leather Armor, Chain Shirt |
| `CONSUMABLE` | `"consumable"` | Healing Potion, Rations |
| `QUEST` | `"quest"` | Mysterious Key, Ancient Scroll |
| `MISC` | `"misc"` | Torch, Rope, Lockpicks |

### Item Rarity

| Rarity | Value | Color (UI) |
|--------|-------|------------|
| `COMMON` | `"common"` | White |
| `UNCOMMON` | `"uncommon"` | Green |
| `RARE` | `"rare"` | Blue |

### Key Functions

| Function | Purpose |
|----------|---------|
| `get_item(name)` | Get item from database by name (case-insensitive) |
| `add_item_to_inventory(inv, item)` | Add item, stacks if stackable |
| `remove_item_from_inventory(inv, name, qty)` | Remove item or reduce stack |
| `find_item_in_inventory(inv, name)` | Search inventory for item |
| `use_item(item, character)` | Use consumable on character |
| `format_inventory(inv, gold)` | Display formatted inventory |
| `generate_loot(enemy_name)` | Generate random loot from enemy |
| `gold_from_enemy(enemy_name)` | Get gold drop amount |

### Item Database (ITEMS)

Pre-defined items in `ITEMS` dict:

```python
# Weapons
"dagger", "shortsword", "longsword", "rapier", "greataxe"
"quarterstaff", "mace", "shortbow", "longbow"

# Armor  
"leather_armor", "studded_leather", "chain_shirt", "chain_mail", "plate_armor"

# Consumables
"healing_potion", "greater_healing_potion", "antidote", "rations"

# Quest/Misc
"torch", "rope", "lockpicks", "bedroll", "mysterious_key", "goblin_ear"
```

### In-Game Commands

| Command | Description |
|---------|-------------|
| `inventory`, `inv`, `i` | View inventory |
| `use <item>` | Use consumable item |
| `equip <item>` | Equip weapon or armor |
| `inspect <item>` | View item details |

---

## Configuration System

### Environment Variables

All configuration lives in `.env`:

```env
# Required
GOOGLE_API_KEY=your-api-key-here

# Optional
GEMINI_MODEL=gemini-2.0-flash
```

### Loading Configuration

Using `python-dotenv`:

```python
from dotenv import load_dotenv
load_dotenv()  # Loads .env file
api_key = os.getenv("GOOGLE_API_KEY")  # Read value
```

### Adding New Configuration

1. Add to `.env.example` with description:
   ```env
   # New feature toggle
   ENABLE_DICE_ROLLS=true
   ```

2. Read in code:
   ```python
   enable_dice = os.getenv("ENABLE_DICE_ROLLS", "false").lower() == "true"
   ```

3. Document in README

---

## Skill Check System

The skill check system handles ability checks with critical success/failure narration.

### How It Works

1. **AI Requests Roll**: DM ends message with `[ROLL: SkillName DC X]`
2. **System Rolls**: `roll_skill_check()` rolls d20 + modifier
3. **Display Result**: Shows roll, modifier, total, and success/failure
4. **Send Context to AI**: Enhanced context for criticals

### Critical Success/Failure

| Roll | Context Sent to AI | Expected Narration |
|------|-------------------|-------------------|
| Natural 20 | `CRITICAL SUCCESS - NATURAL 20! Narrate something EXTRAORDINARY...` | Legendary, epic, exceeds expectations |
| Natural 1 | `CRITICAL FAILURE - NATURAL 1! Narrate a DISASTROUS or COMEDIC failure...` | Dramatic disaster, comedic mishap |
| Normal | `SUCCESS` or `FAILURE` | Standard outcome narration |

### Key Functions

```python
# game.py
roll_skill_check(character, skill_name, dc)  # Returns result dict
format_roll_result(result)                    # Formats for display
parse_roll_request(dm_response)              # Parses [ROLL: ...] tags

# Result dict contains:
{
    'skill': 'Stealth',
    'ability': 'DEX',
    'roll': 14,           # Raw d20 roll
    'modifier': 3,
    'total': 17,
    'dc': 15,
    'success': True,
    'is_nat_20': False,
    'is_nat_1': False
}
```

### Display Format

```
🎲 Stealth (DEX): [14]+3 = 17 vs DC 15 = ✅ SUCCESS
🎲 Athletics (STR): [1]+2 = 3 vs DC 12 = ❌ FAILURE 💀 NAT 1!
🎲 Perception (WIS): [20]+1 = 21 vs DC 10 = ✅ SUCCESS ✨ NAT 20!
```

---

## Game Loop Logic

### State Machine (Current)

```
┌─────────────┐
│  INIT       │ Initialize AI, load config
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  OPENING    │ AI generates opening narration
└──────┬──────┘
       │
       ▼
┌─────────────┐     quit/exit/q      ┌─────────────┐
│  PLAYING    │ ─────────────────────▶│    EXIT     │
│  (loop)     │                       └─────────────┘
└──────┬──────┘
       │
       │ (player input)
       ▼
┌─────────────┐
│  AI RESPOND │ Send to Gemini, display response
└──────┬──────┘
       │
       └─────────────▶ (back to PLAYING)
```

### Future State Machine (Planned)

```
INIT → CHARACTER_CREATE → SCENARIO_SELECT → PLAYING ⇄ COMBAT → INVENTORY → SAVE/LOAD → EXIT
```

---

## Save/Load System

The save system (`src/save_system.py`) handles game state persistence. It's designed to be multi-platform ready for Phase 5 (Backend API) and Phase 6 (Flutter App).

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Save/Load System                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐     ┌─────────────────┐                │
│  │  SaveManager    │────▶│ StorageBackend  │  (abstract)    │
│  │                 │     │                 │                │
│  │  - save_game()  │     └────────┬────────┘                │
│  │  - load_game()  │              │                          │
│  │  - list_saves() │     ┌────────┴────────┐                │
│  └─────────────────┘     │                 │                │
│                          ▼                 ▼                │
│              ┌─────────────────┐  ┌─────────────────┐       │
│              │LocalFileBackend │  │ CloudBackend    │       │
│              │   (Phase 3)     │  │   (Phase 5)     │       │
│              │ saves/*.json    │  │  REST API       │       │
│              └─────────────────┘  └─────────────────┘       │
└──────────────────────────────────────────────────────────────┘
```

### Key Components

#### SaveManager Class

Main interface for save/load operations:

```python
from save_system import SaveManager

save_manager = SaveManager()

# Save game
filepath = save_manager.save_game(
    character,           # Required: Character object
    scenario_manager,    # Optional: ScenarioManager
    chat_history=None,   # Optional: List of chat messages
    slot=1,              # Optional: 1-3 for slots, None for timestamp
    description="My save"
)

# Load game
result = save_manager.load_game(filepath, Character, ScenarioManager)
character = result['character']
scenario_manager = result['scenario_manager']

# List all saves
saves = save_manager.list_saves()
for save in saves:
    print(f"{save['character_name']} L{save['character_level']}")
```

#### Serialization Functions

These convert game objects to/from dictionaries:

| Function | Purpose |
|----------|---------|
| `character_to_dict(char)` | Character → JSON-ready dict |
| `dict_to_character(data, Character)` | Dict → Character object |
| `item_to_dict(item)` | Item → dict |
| `dict_to_item(data)` | Dict → Item object |
| `scenario_to_dict(manager)` | Scenario state → dict |
| `restore_scenario(manager, data)` | Dict → Scenario state |

#### Storage Backend Abstraction

The `StorageBackend` abstract class allows swapping storage implementations:

```python
from save_system import StorageBackend, set_storage_backend

# For Phase 5: Implement a cloud backend
class CloudBackend(StorageBackend):
    def save(self, save_id: str, data: dict) -> bool:
        # POST to /api/saves/{save_id}
        response = requests.post(f"{API_URL}/saves/{save_id}", json=data)
        return response.ok
    
    def load(self, save_id: str) -> dict:
        # GET from /api/saves/{save_id}
        response = requests.get(f"{API_URL}/saves/{save_id}")
        return response.json()
    
    def delete(self, save_id: str) -> bool:
        # DELETE /api/saves/{save_id}
        ...
    
    def list_saves(self) -> list:
        # GET /api/saves
        ...

# Swap backend globally
set_storage_backend(CloudBackend())
```

### Save File Format

Saves are stored as JSON in `/saves/`:

```json
{
  "version": "1.0",
  "timestamp": "2024-12-17T14:30:00",
  "description": "After defeating the goblin boss",
  
  "character": {
    "name": "Aldric",
    "race": "Human",
    "char_class": "Fighter",
    "level": 3,
    "strength": 16,
    "dexterity": 12,
    "constitution": 14,
    "intelligence": 10,
    "wisdom": 13,
    "charisma": 11,
    "max_hp": 24,
    "current_hp": 18,
    "armor_class": 14,
    "weapon": "longsword",
    "equipped_armor": "chain_shirt",
    "inventory": [...],
    "gold": 75,
    "experience": 350
  },
  
  "scenario": {
    "id": "goblin_cave",
    "current_scene_index": 3,
    "choices_made": ["helped_villager", "spared_goblin"],
    "story_flags": {"has_key": true},
    "completed": false
  },
  
  "chat_history": [
    {"role": "user", "content": "I attack the goblin"},
    {"role": "model", "content": "You swing your sword..."}
  ]
}
```

### In-Game Commands

| Command | Description |
|---------|-------------|
| `save` | Save game (choose slot 1-3) |
| `load` | Load a saved game |
| `saves` | List all saved games |

### Testing

Run save system tests:

```bash
cd tests
python test_save_system.py
```

Tests cover:
- Character serialization/deserialization
- Item serialization/deserialization  
- Full save/load cycle
- Save listing functionality
- Error handling and validation

### Error Handling

The save system includes comprehensive error handling with custom exceptions:

**Exception Hierarchy:**

| Exception | When Raised | Recovery Hint |
|-----------|-------------|---------------|
| `SaveSystemError` | Base class for all save errors | — |
| `SaveFileNotFoundError` | Save file doesn't exist | Check file path, create new save |
| `SaveFileCorruptedError` | JSON parse failed | Delete and recreate save |
| `SaveVersionMismatchError` | Incompatible save version | Upgrade save or use compatible version |
| `SavePermissionError` | Can't read/write file | Check file permissions |
| `SaveValidationError` | Invalid save data | Fix or delete corrupted save |
| `SaveDiskSpaceError` | Disk full | Free space and retry |

**Validation Functions:**

```python
from save_system import validate_character_data, validate_save_data

# Validate character data before loading
errors = validate_character_data(char_dict)
if errors:
    print(f"Validation failed: {errors}")

# Validate entire save file
errors = validate_save_data(save_dict)
```

**Atomic Saves:**

The system uses atomic saves (temp file → rename) to prevent corruption:
1. Write to temporary file
2. Verify file integrity
3. Rename to final destination
4. Only then delete temp file

**Error Recovery:**

```python
from save_system import SaveManager

save_manager = SaveManager()
filepath, message = save_manager.save_game(character, scenario)

if filepath:
    print(f"Saved: {filepath}")
else:
    print(f"Save failed: {message}")
    
# Check error log
errors = save_manager.get_last_errors()
for error in errors:
    print(f"  - {error}")
```

---

## Extending the Game

### Adding a New Feature

**Example: Adding a "help" command**

1. **Identify insertion point** in `main()`:
   ```python
   while True:
       player_input = input("⚔️  Your action: ").strip()
       
       # ADD HERE - before quit check
       if player_input.lower() == "help":
           print_help()
           continue
       
       if player_input.lower() in ["quit", "exit", "q"]:
           break
   ```

2. **Create helper function**:
   ```python
   def print_help():
       print("""
       Available Commands:
       - quit/exit/q : Exit the game
       - help : Show this message
       - Any text : Send action to DM
       """)
   ```

3. **Update documentation**

### Adding Game Mechanics

**Example: Dice rolling**

1. **Create new module** `src/dice.py`:
   ```python
   import random
   
   def roll(notation: str) -> dict:
       """Roll dice in standard notation (e.g., '2d6+3')"""
       # Parse notation, roll, return result
   ```

2. **Modify system prompt** to use dice:
   ```python
   DM_SYSTEM_PROMPT = """...
   When a player attempts an action requiring skill, respond with:
   [ROLL: 1d20+{modifier}] - {skill name}
   Then wait for the player to report their roll result.
   """
   ```

3. **Add to game loop**:
   ```python
   from dice import roll
   
   # Detect roll requests in AI response
   if "[ROLL:" in response:
       notation = extract_roll_notation(response)
       result = roll(notation)
       print(f"🎲 You rolled: {result['total']} ({result['dice']})")
   ```

### Creating New Modules

```
src/
├── __init__.py
├── game.py          # Main entry point
├── ai/
│   ├── __init__.py
│   ├── client.py    # AI client setup
│   └── prompts.py   # System prompts
├── mechanics/
│   ├── __init__.py
│   ├── dice.py      # Dice rolling
│   ├── combat.py    # Combat system
│   └── character.py # Character management
└── utils/
    ├── __init__.py
    └── helpers.py   # Utility functions
```

---

## Combat System

### DM Combat Triggers

The AI DM triggers combat using special tags in responses:

| Tag Format | Description |
|------------|-------------|
| `[COMBAT: goblin]` | Single enemy combat |
| `[COMBAT: goblin, goblin]` | Multiple enemies |
| `[COMBAT: wolf, wolf, wolf]` | Pack encounter |
| `[COMBAT: goblin, orc \| SURPRISE]` | Surprise attack (player ambushes) |

### Combat Flow

```
DM Response with [COMBAT: enemy_types] or [COMBAT: enemies | SURPRISE]
           │
           ▼
┌──────────────────────────────┐
│  parse_combat_request()      │ → Returns (enemy_list, surprise_flag)
└──────────────────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  run_combat(surprise_player) │
└──────────────────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  Roll Initiative (all)       │ → Each combatant rolls d20+DEX
└──────────────────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  Build Turn Order            │ → Sorted by initiative (high first)
└──────────────────────────────┘
           │
           ▼
  [If SURPRISE: Round 1 enemies skip, player has advantage]
           │
           ▼
┌──────────────────────────────┐
│  Combat Loop by Turn Order   │ → Each combatant acts in order
└──────────────────────────────┘
           │
           ▼
  [Victory / Defeat / Fled]
```

### Key Combat Functions (combat.py)

| Function | Purpose |
|----------|---------|
| `roll_attack(char, ac, weapon)` | Standard attack roll |
| `roll_attack_with_advantage(char, ac, weapon)` | 2d20 take higher (surprise) |
| `roll_damage(char, weapon, is_crit)` | Damage calculation |
| `enemy_attack(enemy, player_ac)` | Enemy attack against player |
| `roll_initiative(dex_mod)` | d20 + DEX modifier |
| `create_enemy(enemy_type)` | Create enemy from template |

### Surprise & Advantage System

When player ambushes enemies:
1. DM uses `[COMBAT: enemies | SURPRISE]`
2. `parse_combat_request()` returns `surprise_player=True`
3. In Round 1:
   - Enemies skip their turn (shown as "😵 SURPRISED")
   - Player gets ADVANTAGE on first attack
4. `roll_attack_with_advantage()` rolls 2d20, takes higher
5. Display shows both dice: `[8, 15→15]+5 = 20`

### Available Enemies

| Type | HP | AC | Attack | Damage |
|------|-----|-----|--------|--------|
| `goblin` | 7 | 15 | +4 | 1d6+2 |
| `goblin_boss` | 21 | 17 | +4 | 2d6+2 |
| `orc` | 15 | 13 | +5 | 1d12+3 |
| `wolf` | 11 | 13 | +4 | 2d4+2 |
| `skeleton` | 13 | 13 | +4 | 1d6+2 |
| `bandit` | 11 | 12 | +3 | 1d6+1 |
| `giant_spider` | 26 | 14 | +5 | 1d8+3 |

### Combat Narration System

The combat system integrates AI-generated narration to bring combat to life. The mechanics remain deterministic while the AI DM provides immersive descriptions.

#### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PLAYER/ENEMY ATTACKS                        │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  MECHANICS LAYER (Deterministic)                                │
│  • Dice rolls happen first                                      │
│  • Damage calculated                                            │
│  • HP deducted, win/lose determined                             │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  NARRATION LAYER (AI-Generated)                                 │
│  • DM receives final results                                    │
│  • Describes what happened                                      │
│  • Cannot change outcomes                                       │
│  • Pure flavor/immersion                                        │
└─────────────────────────────────────────────────────────────────┘
```

#### Key Principle

**Mechanics are authoritative.** The AI DM narrates combat outcomes but cannot change results. Numbers are calculated first, then narration is generated based on those results.

#### Combat Narration Functions (game.py)

| Function | Purpose |
|----------|---------|
| `build_combat_context()` | Creates context dict from attack/damage results |
| `get_combat_narration(chat, context)` | Sends context to AI, returns narrative prose |
| `display_combat_narration(narration)` | Displays 📖 narration with proper formatting |
| `COMBAT_NARRATION_PROMPT` | Prompt template for AI narration requests |

#### Combat Context Structure

```python
combat_context = {
    'attacker': 'Kira',           # Who is attacking
    'target': 'Goblin 1',         # Target of attack
    'weapon': 'longsword',        # Weapon used
    'outcome': 'hit',             # 'hit', 'miss', 'critical_hit', 'critical_miss'
    'damage': 8,                  # Damage dealt (if hit)
    'damage_type': 'slashing',    # Damage type
    'target_killed': False,       # Did target die?
    'is_player_attack': True,     # Player attacking enemy or vice versa
}
```

#### Example Output

```
🗡️ Attack (Longsword): [17]+5 = 22 vs AC 15 = ✅ HIT!
💥 Damage: [6]+3 = 9 slashing damage

📖 Your blade arcs through the air in a deadly silver flash. The goblin 
   tries to raise its rusty dagger to parry, but you're too fast—steel 
   bites deep, and the creature crumples with a gurgling cry.
```

#### Extending Combat Narration

To add narration to a new combat action:

```python
# 1. Build context after mechanics resolve
combat_ctx = build_combat_context(
    attacker_name=character.name,
    target_name=enemy.name,
    weapon=weapon,
    attack_result=attack,
    damage_result=damage,
    target_died=enemy.current_hp <= 0,
    is_player_attacking=True
)

# 2. Request narration from AI
narration = get_combat_narration(chat, combat_ctx)

# 3. Display narration
display_combat_narration(narration)
```

---

## Leveling System

### XP and Level Progression

Characters can advance from Level 1 to Level 5:

| Level | XP Threshold | Cumulative XP | Proficiency |
|-------|-------------|---------------|-------------|
| 1 | 0 | 0 | +2 |
| 2 | 100 | 100 | +2 |
| 3 | 200 | 300 | +2 |
| 4 | 300 | 600 | +2 |
| 5 | 400 | 1000 | +3 |

### XP Reward System

DM awards XP using tags in responses:

| Tag Format | Description |
|------------|-------------|
| `[XP: 50]` | Award 50 XP |
| `[XP: 50 \| Defeated goblin]` | Award 50 XP with reason |

### Milestone XP Values

| Milestone Type | XP Value |
|----------------|----------|
| `minor` | 25 XP |
| `major` | 50 XP |
| `boss` | 100 XP |
| `adventure` | 150 XP |

### Player Commands

| Command | Description |
|---------|-------------|
| `xp`, `level` | View current level and XP progress |
| `levelup` | Advance to next level (if eligible) |

### Level Up Benefits

| Level | Benefits |
|-------|----------|
| 2 | +2 HP, +1 stat boost |
| 3 | +2 HP, class ability |
| 4 | +2 HP, +1 stat boost |
| 5 | +2 HP, class ability, +1 proficiency |

### Key Functions (character.py)

| Function | Purpose |
|----------|---------|
| `gain_xp(amount, source)` | Add XP, check level up |
| `can_level_up()` | Check if XP threshold met |
| `level_up()` | Apply level up benefits |
| `xp_to_next_level()` | XP needed for next level |
| `xp_progress()` | Progress toward next level |
| `get_proficiency_bonus()` | Get current proficiency |

---

## Testing Guidelines

### Manual Testing Checklist

Before committing changes:

- [ ] Game starts without errors
- [ ] AI responds to player input
- [ ] Conversation context is maintained
- [ ] Quit command works
- [ ] Error handling works (try invalid API key)
- [ ] Environment variables load correctly

### Test Scenarios

| Test | Steps | Expected Result |
|------|-------|-----------------|
| Fresh start | Run game with valid .env | Opening narration appears |
| Invalid API key | Set wrong key in .env | Error message displayed |
| Empty input | Press Enter without typing | Prompt shown again |
| Long conversation | 10+ exchanges | Context maintained |
| Exit commands | Type quit/exit/q | Game ends gracefully |

### Future: Automated Testing

```python
# tests/test_game.py
import pytest
from src.game import create_client, get_dm_response

def test_client_creation():
    """Test that client initializes with valid config."""
    client = create_client()
    assert client is not None

def test_dm_response():
    """Test that DM responds to input."""
    client = create_client()
    chat = client.start_chat(history=[])
    response = get_dm_response(chat, "I look around")
    assert len(response) > 0
```

---

## Deployment

### Local Development

```bash
# Clone
git clone https://github.com/Axidify/ai-dnd-rpg.git
cd ai-dnd-rpg

# Setup
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API key

# Run
python src/game.py
```

### Production Considerations (Future)

| Concern | Solution |
|---------|----------|
| API Key Security | Use secrets manager (AWS Secrets, etc.) |
| Rate Limiting | Implement request throttling |
| Cost Control | Set usage quotas, use cheaper models |
| Logging | Add structured logging |
| Monitoring | Add health checks, error tracking |

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "GOOGLE_API_KEY not set" | Missing .env | Create .env from .env.example |
| "404 model not found" | Invalid model name | Check GEMINI_MODEL in .env |
| "Invalid API key" | Wrong/expired key | Get new key from AI Studio |
| Import errors | Missing deps | `pip install -r requirements.txt` |
| "Context window exceeded" | Long conversation | Restart game (future: implement summarization) |

### Debug Mode

Add to `game.py` for verbose output:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# In get_dm_response:
logging.debug(f"Sending: {player_input}")
logging.debug(f"Received: {response.text[:100]}...")
```

### Getting Help

1. Check this documentation
2. Review CHANGELOG for recent changes
3. Check GitHub Issues
4. Contact maintainer

---

## Contributing

### Workflow

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes
3. Test thoroughly
4. Update CHANGELOG.md
5. Commit with descriptive message
6. Push and create PR

### Commit Message Format

```
[Phase X.Y] Brief description

- Detail 1
- Detail 2

Closes #issue-number
```

### Code Style

- Use descriptive function/variable names
- Add docstrings to functions
- Keep functions focused and small
- Handle errors gracefully
- Log important events

---

## References

- [Google Gemini API Docs](https://ai.google.dev/docs)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [D&D 5e SRD](https://www.5esrd.com/) (for game mechanics reference)
- [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) (project roadmap)
