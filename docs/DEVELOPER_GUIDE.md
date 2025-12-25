# Developer Documentation

## AI D&D Text RPG - Technical Guide

**Last Updated:** December 25, 2025

This document provides comprehensive technical documentation for developers who want to understand, maintain, or contribute to the AI D&D Text RPG project.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
   - [Core Design Principle: Mechanics First, Narration Last](#core-design-principle-mechanics-first-narration-last)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [AI Integration](#ai-integration)
5. [Configuration System](#configuration-system)
6. [Game Loop Logic](#game-loop-logic)
7. [Save/Load System](#saveload-system)
8. [Location System](#location-system-phase-32)
9. [World Map System](#world-map-system-phase-45) ← **NEW**
10. [NPC System](#npc-system-phase-33)
11. [Shop System](#shop-system-phase-333)
12. [Traveling Merchants](#traveling-merchants-phase-33---priority-5)
13. [Party System](#party-system-phase-337)
14. [Quest System](#quest-system-phase-334)
15. [Extending the Game](#extending-the-game)
16. [Testing Guidelines](#testing-guidelines)
17. [Security](#security) ← **125 tests passing**
18. [Deployment](#deployment)
19. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### Current Architecture (API-First Design)

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  React Web    │     │  Godot Client │     │ Flutter App   │
│  (Vite)       │     │   (Future)    │     │   (Future)    │
│ localhost:3000│     │               │     │               │
└───────┬───────┘     └───────┬───────┘     └───────┬───────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 api_server.py (Flask REST API)              │
│                    localhost:5000/api/*                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Endpoints  │→ │ dm_engine   │→ │  Response   │         │
│  │  /game/*    │  │  (logic)    │  │  SSE Stream │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 dm_engine.py (Shared Logic)                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  DM_SYSTEM_PROMPT - Complete AI ruleset             │   │
│  │  parse_*() - Tag parsing functions                  │   │
│  │  roll_skill_check() - Dice mechanics                │   │
│  │  build_full_dm_context() - Prompt construction      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Google Gemini API                           │
│              (google-generativeai library)                  │
└─────────────────────────────────────────────────────────────┘
```

### Legacy Architecture (Archived)

The original terminal-based game (`backup/legacy/game.py`) has been archived.
The current architecture uses API-first design where `api_server.py` is the
only entry point and all game logic is shared via `dm_engine.py`.

### Planned Extensions (Phase 5-6)

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

### Core Design Principle: Mechanics First, Narration Last

This is the **fundamental architectural pattern** that governs all systems in the game.

```
┌─────────────────────────────────────────────────────────────────┐
│                    PLAYER ACTION                                │
│         "attack goblin" / "go north" / "pick lock"              │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: MECHANICS LAYER (Deterministic, Python)                │
│  ─────────────────────────────────────────────────              │
│  • Parse command                                                │
│  • Roll dice (if applicable)                                    │
│  • Calculate results (damage, movement, success/fail)           │
│  • Update game state (HP, location, inventory)                  │
│  • Determine outcome FIRST                                      │
│                                                                 │
│  OUTPUT: Concrete result + context for AI                       │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: AI NARRATION LAYER (Creative, Gemini)                  │
│  ─────────────────────────────────────────────────              │
│  • Receives final results (cannot change them!)                 │
│  • Describes what happened in vivid prose                       │
│  • Adds atmosphere, NPC reactions, sensory details              │
│  • Never contradicts mechanical outcome                         │
│                                                                 │
│  OUTPUT: Immersive narration for player                         │
└─────────────────────────────────────────────────────────────────┘
```

**Why This Matters:**

| Aspect | Mechanics Layer | AI Layer |
|--------|-----------------|----------|
| **Role** | Authoritative - determines outcomes | Decorative - describes outcomes |
| **Consistency** | Deterministic, reproducible | Creative, varied |
| **Fairness** | Rules-based, fair to player | Cannot cheat or fudge results |
| **Testing** | Unit testable | Subjective quality |

**Example: Combat Attack**
```
1. Player: "attack goblin"
2. MECHANICS: Roll d20+5 = 18 vs AC 13 → HIT, Roll 1d8+3 = 7 damage
3. AI receives: "Player hit Goblin for 7 damage (18 vs AC 13)"
4. AI narrates: "Your blade arcs through the air, catching the goblin 
   across the shoulder! It shrieks in pain, dark blood spattering the stones."
```

**Example: Location Movement**
```
1. Player: "go north"
2. MECHANICS: Check exits → valid, Move player, Check events → first visit
3. AI receives: "Player entered Boss Chamber (first visit). Event: chief_roars"
4. AI narrates: "You step into the torch-lit chamber and a thunderous 
   roar shakes the very stones..."
```

This pattern applies to: **Combat, Movement, Skill Checks, Item Interaction, NPC Dialogue, Save/Load, and all future systems.**
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
│   ├── DEVELOPER_GUIDE.md      # This file (5000+ lines)
│   ├── DEVELOPMENT_PLAN.md     # Project roadmap with phases
│   ├── FLUTTER_SETUP.md        # Flutter installation guide
│   ├── HOSTILE_PLAYER_TESTING.md # Security testing (160 tests, 16 fixes)
│   ├── THEME_SYSTEM_SPEC.md    # DLC-ready theme architecture
│   └── UI_DESIGN_SPEC.md       # UI/UX specifications
│
├── saves/                  # Game save files (auto-created)
│   └── save_*.json             # Individual save files
│
├── README.md               # User-facing documentation
├── requirements.txt        # Python dependencies
├── tasksync.md             # Development protocol
│
├── src/
│   ├── __init__.py         # Package marker
│   ├── api_server.py       # Flask REST API (main entry point, 35 endpoints)
│   ├── dm_engine.py        # Shared DM logic (prompts, parsing)
│   ├── character.py        # Character system (stats, creation, XP/leveling)
│   ├── combat.py           # Combat system (attacks, damage, multi-enemy)
│   ├── inventory.py        # Item and inventory management
│   ├── npc.py              # NPC system (dialogue, roles, managers)
│   ├── party.py            # Party/companion system
│   ├── quest.py            # Quest tracking system
│   ├── save_system.py      # Save/Load system
│   ├── scenario.py         # Scenario and scene management
│   └── shop.py             # Shop system (buy/sell/haggle)
│
├── frontend/
│   └── option1-react/      # React + Vite + Tailwind frontend
│       ├── src/
│       │   ├── App.jsx
│       │   ├── components/
│       │   │   ├── CharacterCreation.jsx
│       │   │   ├── GameScreen.jsx
│       │   │   ├── WorldMap.jsx
│       │   │   └── DiceRoller.jsx
│       │   └── store/gameStore.js
│       └── package.json
│
├── backup/
│   └── legacy/
│       └── game.py         # Archived terminal version (no longer maintained)
│
└── tests/                       # 821+ unit tests + 125 security tests
    ├── run_interactive_tests.py  # Unified test runner (all test modes)
    ├── hostile_final.py        # Security stress tests (75 tests - Round 5)
    ├── test_ai_stress.py       # AI security stress tests (23 cases)
    ├── test_character.py       # Character system tests (26 tests)
    ├── test_combat.py          # Combat mechanics tests (31 tests)
    ├── test_combat_travel_block.py # Combat exploit prevention (3 tests)
    ├── test_combat_with_dm.py  # Interactive combat tests (3 tests)
    ├── test_dice.py            # Dice rolling manual tests (standalone)
    ├── test_dice_with_dm.py    # Dice + AI tests
    ├── test_dialogue.py        # NPC dialogue system tests (24 tests)
    ├── test_flexible_travel.py # Flexible travel input tests (25 tests)
    ├── test_flow_breaking.py   # Flow breaking/weird input tests (29 tests)
    ├── test_hostile_player.py  # Adversarial exploit tests (44 tests)
    ├── test_inventory.py       # Inventory system tests (35 tests)
    ├── test_inventory_with_dm.py # Interactive inventory tests (AI)
    ├── test_location.py        # Location system tests (200 tests)
    ├── test_location_with_dm.py # Interactive location tests (13 tests)
    ├── test_multi_enemy.py     # Multi-enemy combat tests (3 tests)
    ├── test_npc.py             # NPC system tests (55 tests)
    ├── test_party.py           # Party/companion tests (72 tests)
    ├── test_prompt_injection.py # Security/injection tests (22 tests)
    ├── test_quest.py           # Quest system tests (57 tests)
    ├── test_quest_hooks.py     # Quest event hooks tests
    ├── test_reputation.py      # Disposition system tests (55 tests)
    ├── test_reputation_hostile.py # Disposition adversarial tests (36 tests)
    ├── test_save_system.py     # Save/Load system tests (8 tests)
    ├── test_scenario.py        # Scenario system tests (31 tests)
    ├── test_shop.py            # Shop system tests (72 tests)
    ├── test_travel_menu.py     # Travel menu system tests (42 tests)
    └── test_xp_system.py       # XP and leveling tests (10 tests)
```

### File Responsibilities

| File | Purpose | Modify When |
|------|---------|-------------|
| `src/api_server.py` | Flask REST API, SSE streaming | Adding API endpoints |
| `src/dm_engine.py` | Shared DM logic, prompts, parsing | Adding new DM tags or parsing |
| `src/character.py` | Character class, stats, XP/leveling | Adding character features |
| `src/combat.py` | Combat mechanics, multi-enemy | Modifying combat |
| `src/inventory.py` | Items, equipment, loot | Adding items/equipment |
| `src/npc.py` | NPC system, dialogue, disposition | Adding NPC features |
| `src/party.py` | Party/companion system | Adding party features |
| `src/quest.py` | Quest tracking and objectives | Adding quests |
| `src/save_system.py` | Save/Load persistence | Changing save format |
| `src/scenario.py` | Story scenarios, scenes | Adding scenarios |
| `src/shop.py` | Shop system, merchants | Adding shop features |
| `.env` | API keys, configuration | Changing providers/models |
| `requirements.txt` | Dependencies | Adding libraries |
| `docs/DEVELOPMENT_PLAN.md` | Roadmap | Planning new phases |
| `docs/CHANGELOG.md` | Version tracking | Releasing versions |
| `docs/THEME_SYSTEM_SPEC.md` | Theme/DLC architecture | Theme system changes |

> **⚠️ IMPORTANT NOTE:** This document contains historical references to `game.py` (the 
> terminal version). The terminal version has been **archived to `backup/legacy/game.py`**.
> All new development should use **`api_server.py`** (Flask REST API) as the entry point.
> Logic that was previously in `game.py` now lives in **`dm_engine.py`** (shared logic)
> and **`api_server.py`** (request handling). When reading code examples below that 
> reference `game.py`, mentally substitute with the appropriate API-first equivalent.

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
| `format_inventory(inv, gold)` | Display formatted inventory with stats |
| `generate_loot(enemy_name)` | Generate random loot from enemy |
| `gold_from_enemy(enemy_name)` | Get gold drop amount |

### Inventory Display

Items now show stats inline in the inventory display:

```
╔══════════════════════════════════════════════════════════╗
║                      INVENTORY                           ║
╠══════════════════════════════════════════════════════════╣
║  💰 Gold: 25                                            ║
╠══════════════════════════════════════════════════════════╣
║  ⚔️ Weapons                                            ║
║    • Longsword [DMG: 1d8]                                ║
║    • Dagger [DMG: 1d4]                                   ║
║  🛡️ Armor                                              ║
║    • Studded Leather [AC: +2]                            ║
║  🧪 Consumables                                         ║
║    • Healing Potion [HEAL: 2d4+2]                        ║
╚══════════════════════════════════════════════════════════╝
```

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

### AI Skill Selection Rules

The DM prompt includes extensive guidance for selecting the correct skill. Key distinctions:

| Action Type | Correct Skill | Example |
|-------------|---------------|---------|
| Notice/spot/hear/sense | **Perception** | "I look for hidden threats" |
| Analyze/deduce/figure out/examine | **Investigation** | "I examine the tracks to deduce their origin" |
| Move quietly/avoid detection | **Stealth** | "I move through the area without being noticed" |
| Convince someone (requires NPC) | **Persuasion** | "I negotiate with the merchant for a better price" |

**Perception vs Investigation (Critical Distinction):**
- **Perception** = Passive/active noticing: see, hear, spot, detect, notice
- **Investigation** = Mental analysis: figure out, deduce, analyze, examine closely, investigate

**Stealth Rules:**
- ANY quiet movement = Stealth check (not Perception)
- Keywords: sneak, creep, quietly, unseen, unnoticed

**Persuasion Requirements:**
- Persuasion requires an existing NPC to convince
- The AI does NOT create NPCs for Persuasion checks

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

> **NOTE:** The terminal game loop has been replaced with an API-first architecture.
> The sections below describe the legacy terminal flow for historical reference.
> See `api_server.py` for the current request/response flow.

### API Request Flow (Current)

```
┌─────────────────────────────────────────────────────────────────┐
│                    React Frontend                                │
│    [CharacterCreation.jsx] → [GameScreen.jsx] → [Modals]        │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/SSE
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    api_server.py (Flask)                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  POST /api/game/start      → Create session, character  │   │
│  │  POST /api/game/action/stream → Process action, SSE     │   │
│  │  POST /api/travel           → Change location           │   │
│  │  GET  /api/game/state       → Get current state         │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    dm_engine.py (Shared Logic)                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  build_full_dm_context() → Construct AI prompt           │   │
│  │  parse_*() → Extract tags from DM response               │   │
│  │  roll_skill_check() → Handle dice mechanics              │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Google Gemini API                             │
│                    (Streaming responses)                         │
└─────────────────────────────────────────────────────────────────┘
```

### Legacy Terminal State Machine (Archived)

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

## DM Response Tags Reference

The AI Dungeon Master uses special tags to trigger game mechanics. These tags are parsed from DM responses and processed by the game system.

### All DM Tags

| Tag | Purpose | Example |
|-----|---------|---------|
| `[ROLL: Skill DC X]` | Request skill check | `[ROLL: Stealth DC 14]` |
| `[COMBAT: enemies]` | Initiate combat | `[COMBAT: goblin, orc]` |
| `[COMBAT: enemies \| SURPRISE]` | Combat with surprise | `[COMBAT: goblin \| SURPRISE]` |
| `[ITEM: item_name]` | Give FREE item (loot/reward) | `[ITEM: healing_potion]` |
| `[BUY: item_name, price]` | Shop purchase (deducts gold) | `[BUY: studded_leather, 25]` |
| `[GOLD: amount]` | Give gold | `[GOLD: 50]` |
| `[XP: amount]` | Award experience (RARE - see note) | `[XP: 25]` |
| `[XP: amount \| reason]` | Award XP with reason | `[XP: 50 \| Solved puzzle]` |

> **⚠️ XP Tag Usage:** Most XP is awarded automatically by the system (combat, objectives, quests). The AI should only use `[XP:]` tags for **exceptional** roleplay like creative puzzle solutions. See [XP System](#xp-system-controlled) for details.

### Item vs Buy Tags

**Critical Distinction:**
- `[ITEM:]` - For FREE items: loot, quest rewards, gifts, treasure
- `[BUY:]` - For PURCHASES: shop transactions (gold is deducted)

```python
# Parser functions in game.py
parse_item_rewards(dm_response)      # Returns list of item names
parse_buy_transactions(dm_response)  # Returns list of (item, price) tuples
parse_gold_rewards(dm_response)      # Returns total gold amount
parse_xp_rewards(dm_response)        # Returns list of (amount, reason) tuples (AI-awarded only)
```

### Auto-Equip on Purchase

When armor is purchased via `[BUY:]`:
1. Gold is deducted from player
2. Item is added to inventory
3. If armor: old armor is unequipped and removed from inventory
4. New armor is equipped and AC is recalculated

When weapons are received via `[BUY:]` or `[ITEM:]`:
1. Item is added to inventory
2. New weapon's max damage is compared to current weapon
3. If new weapon is better: it is auto-equipped
4. Old weapon stays in inventory

```python
# Helper function for weapon damage comparison
get_weapon_max_damage("1d8")   # Returns 8
get_weapon_max_damage("2d6")   # Returns 12
get_weapon_max_damage("1d12+2") # Returns 12 (ignores bonus)
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
| `roll_attack_with_disadvantage(char, ac, weapon)` | 2d20 take lower (darkness) |
| `roll_damage(char, weapon, is_crit)` | Damage calculation (+1d4 if poisoned) |
| `enemy_attack(enemy, player_ac)` | Enemy attack against player |
| `roll_initiative(dex_mod)` | d20 + DEX modifier |
| `create_enemy(enemy_type)` | Create enemy from template |
| `determine_turn_order(player, enemies, party_members)` | Unified initiative with allies |
| `party_member_attack(member, target, has_flanking)` | Party member attack roll |
| `get_party_member_action(member, enemies, allies_hp)` | AI decision for party action |
| `check_flanking(attackers_on_target)` | True if 2+ allies on target |
| `format_party_member_attack(attack, damage, class)` | Format party attack display |

### Surprise & Advantage System

When player ambushes enemies:
1. DM uses `[COMBAT: enemies | SURPRISE]`
2. `parse_combat_request()` returns `surprise_player=True`
3. In Round 1:
   - Enemies skip their turn (shown as "😵 SURPRISED")
   - Player gets ADVANTAGE on first attack
4. `roll_attack_with_advantage()` rolls 2d20, takes higher
5. Display shows both dice: `[8, 15→15]+5 = 20`

### Darkness & Disadvantage System (Phase 3.6.7)

When player attacks in darkness without light:
1. `/api/combat/attack` checks `check_darkness_penalty(location, character)`
2. If `in_darkness=True`:
   - Player attacks use `roll_attack_with_disadvantage()` (2d20, take lower)
   - Warning message prepended to combat result
3. Darkness + Surprise cancel out = normal roll
4. Torch or other light source prevents disadvantage
5. Display shows: `⬇️ DIS [15, 8→8]+5 = 13`

### Poison Damage Bonus (Phase 3.6.6)

When weapon is poisoned via Poison Vial:
1. `character.weapon_poisoned = True` set by `use_item()`
2. On next hit, `roll_damage()` adds +1d4 poison damage
3. Poison consumed after single use (weapon_poisoned = False)
4. Display shows: `💥 Damage: [6]+3 + 🧪[3] poison = 12`

### Party Combat Integration (Phase 3.6.8)

Party members participate in combat as AI-controlled allies:

#### Turn Order
```python
# All combatants roll initiative together
turn_order = determine_turn_order(player, enemies, party_members=[marcus, elira])
# Returns list of Combatant objects sorted by initiative (highest first)
```

#### Party Member Actions
Each turn after the player attacks, party members execute:
1. **AI Decision**: `get_party_member_action()` chooses attack/heal/ability
2. **Flanking Check**: If 2+ allies attack same target, grant advantage
3. **Attack Roll**: `party_member_attack()` with optional flanking bonus
4. **Display**: `format_party_member_attack()` with class-specific emoji

#### AI Decision Logic
```python
action = get_party_member_action(member, enemies, allies_hp)
# Returns: "attack", "ability", or "heal"
# - "attack": Always if no ability or allies healthy
# - "ability": Use special ability if available  
# - "heal": Cleric uses Healing Word if ally HP < 50%
```

#### Flanking Bonus
```python
if check_flanking(num_attackers_on_target):  # >= 2
    attack, damage = party_member_attack(member, target, has_flanking=True)
    # Rolls 2d20, takes higher (advantage)
```

#### Display Format
```
🛡️ Marcus attacks Goblin: [17]+5 = 22 vs AC 12 → ✅ HIT! 8 damage!
🏹 Elira ⚔️ FLANKING attacks Goblin: [11, 14→14]+5 = 19 vs AC 12 → ✅ HIT! 10 damage!
```

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

### Location System (Phase 3.2)

The location system provides a structured way to define explorable areas with items, NPCs, and navigation.

#### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       LOCATION FLOW                             │
├─────────────────────────────────────────────────────────────────┤
│  Scenario → Scene → LocationManager → Location                 │
│                                                                 │
│  Scene.location_ids = ["tavern_main", "tavern_bar", "street"]  │
│  Scene.starting_location_id = "tavern_main"                    │
│                           ↓                                     │
│  LocationManager.set_available_locations([...])                │
│  LocationManager.set_current_location("tavern_main")           │
│                           ↓                                     │
│  Player: "go door" → LocationManager.move("door")              │
│                           ↓                                     │
│  Location.exits = {"door": "street"}                           │
│  → Move to "street" if in available_location_ids               │
└─────────────────────────────────────────────────────────────────┘
```

#### Location Dataclass (scenario.py)

```python
@dataclass
class Location:
    id: str                  # Unique identifier ("tavern_main")
    name: str                # Display name ("The Rusty Dragon")
    description: str         # Full description for AI
    exits: Dict[str, str]    # {"door": "street", "stairs": "upstairs"}
    npcs: List[str]          # NPC IDs present ["barkeep", "bram"]
    items: List[str]         # Item keys that can be found ["torch", "sword"]
    atmosphere: str          # AI guidance ("dim lighting, rowdy crowd")
    enter_text: str          # First-time entry description
    events: List[LocationEvent]  # Phase 3.2.1: Triggered events (traps, discoveries)
    encounter: List[str]     # Phase 3.2.2: Fixed enemy types for combat
    encounter_triggered: bool  # Runtime: has encounter occurred?
    visited: bool            # Runtime: has player been here?
    events_triggered: List[str]  # Runtime: one-time events fired
```

#### Fixed Encounter System (Phase 3.2.2)

The `encounter` field ensures **predictable, balanced difficulty** by specifying exact enemy counts for combat at each location.

**Problem Solved:** Without fixed encounters, the AI DM could spawn varying numbers of enemies (e.g., "4-5 goblins"), making difficulty unpredictable and sometimes unfair.

**How It Works:**

```python
# Define location with fixed encounter
"goblin_camp_main": Location(
    id="goblin_camp_main",
    name="Goblin Warren - Main Camp",
    description="A large cavern with exactly 4 goblins around a fire.",
    encounter=["goblin", "goblin", "goblin", "goblin"],  # EXACTLY 4 goblins
    ...
)

# Boss fight with minions
"boss_chamber": Location(
    id="boss_chamber",
    name="Chief's Throne Room",
    encounter=["goblin_boss", "goblin", "goblin"],  # 1 boss + 2 bodyguards
    ...
)
```

**DM Context Integration:**
When the player is at a location with an untriggered encounter, the AI DM receives:
```
⚔️ FIXED ENCOUNTER (not yet triggered): 4 goblins
When combat starts here, you MUST use EXACTLY: [COMBAT: goblin, goblin, goblin, goblin]
Do NOT vary the enemy count - this ensures fair, balanced difficulty.
```

**State Tracking:**
- `encounter_triggered = False` → DM sees fixed encounter instructions
- After combat starts → `encounter_triggered = True`
- DM now sees "✓ Encounter already completed at this location."

#### Location Methods (Phase 3.2.1)

| Method | Description |
|--------|-------------|
| `get_exits_display()` | Returns "You can go: door, stairs or window" |
| `get_items_display()` | Returns "🎒 Items here: torch, sword" |
| `get_npcs_display()` | Returns "👤 Present: Barkeep, Bram" |
| `has_item(item_key)` | Check if item is present (case-insensitive) |
| `remove_item(item_key)` | Remove item when player picks it up |
| `has_npc(npc_id)` | Check if NPC is present (case-insensitive) |
| `to_dict()` | Serialize state for saving |
| `from_state(location, state)` | Restore state from save |

#### LocationManager (scenario.py)

```python
class LocationManager:
    locations: Dict[str, Location]       # All registered locations
    current_location_id: Optional[str]   # Where player is now
    available_location_ids: List[str]    # Unlocked by current scene
    
    def move(direction: str) -> tuple[bool, Location, str]:
        """Attempt to move. Returns (success, new_location, message)"""
        
    def get_context_for_dm() -> str:
        """Get current location context for AI prompts"""
```

---

### Location API Reference

Complete reference for Location methods and properties.

#### Location Methods

```python
# Check if an item exists in this location
# Normalizes spaces to underscores: "healing potion" matches "healing_potion"
location.has_item("healing_potion")  # Returns: bool

# Remove an item from location (when player picks it up)
location.remove_item("healing_potion")  # Returns: bool (True if removed)

# Check if an NPC is present
location.has_npc("bram")  # Returns: bool

# Get formatted display strings
location.get_exits_display()  # "You can go: north, door or stairs"
location.get_items_display()  # "🎒 Items here: Healing Potion, Torch"
location.get_npcs_display()   # "👤 Present: Bram, Barkeep"

# Event management
location.get_events_for_trigger(EventTrigger.ON_ENTER, is_first_visit=True)
location.trigger_event("event_id")     # Mark event as triggered
location.has_event("event_id")         # Check if event exists
location.is_event_triggered("event_id")  # Check if already fired
location.add_event(LocationEvent(...))  # Add new event at runtime

# Exit condition management (Phase 3.2.1 Priority 5)
location.get_exit_condition("door")   # Returns ExitCondition or None
location.is_exit_unlocked("door")     # Check if door was unlocked
location.unlock_exit("door")          # Permanently unlock an exit

# Serialization (for save/load)
state = location.to_dict()  # Returns state dict
Location.from_state(location, state)  # Restore from saved state
```

#### Random Encounters

Locations can have random encounters that trigger with a percentage chance when the player enters. This adds variety to exploration.

**RandomEncounter Dataclass:**

```python
from scenario import RandomEncounter

encounter = RandomEncounter(
    id="wolf_ambush",           # Unique identifier
    enemies=["wolf"],           # Enemy types to spawn
    chance=20,                  # 20% chance to trigger
    condition=None,             # Optional prerequisite
    min_visits=0,               # Trigger from first visit
    max_triggers=2,             # Can happen twice total
    cooldown=3,                 # Wait 3 visits between triggers
    narration="A wolf emerges!" # AI DM narration hint
)
```

**Adding to a Location:**

```python
Location(
    id="forest_path",
    name="Forest Path",
    description="A winding forest trail",
    random_encounters=[
        RandomEncounter(
            id="wolf_ambush",
            enemies=["wolf"],
            chance=20,
            max_triggers=2,
            cooldown=3,
            narration="A hungry wolf emerges from the underbrush, teeth bared!"
        ),
        RandomEncounter(
            id="bandit_gang",
            enemies=["bandit", "bandit"],
            chance=10,
            min_visits=3,  # Only after 3rd visit
            narration="Bandits step out from behind trees, blocking your path!"
        )
    ]
)
```

**RandomEncounter Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `id` | required | Unique identifier for tracking |
| `enemies` | required | List of enemy type strings |
| `chance` | 20 | Percentage (1-100) to trigger |
| `condition` | None | Prerequisite (same format as ExitCondition) |
| `min_visits` | 0 | Only trigger after N visits |
| `max_triggers` | 1 | Max times this can trigger (-1 = unlimited) |
| `cooldown` | 0 | Visits to wait before can trigger again |
| `narration` | "" | Hint for AI DM to narrate encounter start |

**Checking for Random Encounters (in game.py):**

```python
# After successful movement
success, new_location, message, events = loc_manager.move(direction, game_state)

if success:
    # Check for random encounter
    encounter = loc_manager.check_random_encounter(game_state)
    if encounter:
        # Start combat with encounter.enemies
        print(f"⚔️ {encounter.narration}")
        for enemy_type in encounter.enemies:
            enemy = create_enemy(enemy_type)
            combat_manager.add_enemy(enemy)
```

**State Tracking:**

The system automatically tracks:
- `visit_count` - How many times player has entered this location
- `random_encounter_triggers` - How many times each encounter has triggered
- `random_encounter_last_visit` - When each encounter last triggered (for cooldown)

All state is saved/loaded automatically with the location.

#### Direction Aliases (Cardinal Navigation)

Locations can define cardinal direction shortcuts (n/s/e/w) that map to descriptive exit names. This gives players the classic text adventure experience of typing 'n' to go north.

**Adding Direction Aliases:**

```python
from scenario import Location

location = Location(
    id="village_square",
    name="Village Square",
    description="A village square with paths in all directions.",
    exits={
        "forest_path": "forest",
        "tavern_door": "tavern",
        "blacksmith": "smithy"
    },
    direction_aliases={
        "n": "forest_path",      # 'n' or 'north' → forest_path
        "north": "forest_path",
        "e": "tavern_door",      # 'e' or 'east' → tavern_door
        "east": "tavern_door",
        "w": "blacksmith",       # 'w' or 'west' → blacksmith
        "west": "blacksmith"
    }
)
```

**Supported Direction Shortcuts:**

| Shortcut | Expands To | Shortcut | Expands To |
|----------|------------|----------|------------|
| `n` | `north` | `ne` | `northeast` |
| `s` | `south` | `nw` | `northwest` |
| `e` | `east` | `se` | `southeast` |
| `w` | `west` | `sw` | `southwest` |
| `u` | `up` | `d` | `down` |

**Player Input Examples:**

With the location above, all of these work:
- `go n` → Goes to forest
- `north` → Goes to forest  
- `go forest_path` → Goes to forest
- `e` → Goes to tavern

**Helper Function:**

```python
from scenario import resolve_direction_alias, CARDINAL_ALIASES

# Expand shorthand to full direction
resolve_direction_alias("n")     # → "north"
resolve_direction_alias("nw")    # → "northwest"
resolve_direction_alias("door")  # → "door" (unchanged)

# Access all aliases
print(CARDINAL_ALIASES)  # {"n": "north", "s": "south", ...}
```

#### Exit Conditions (Locked Doors)

Locations can have conditional exits that require items, gold, skill checks, or other prerequisites.

**ExitCondition Dataclass:**

```python
from scenario import ExitCondition

# Create an exit condition
condition = ExitCondition(
    exit_name="storage",              # Which exit this applies to
    condition="has_item:storage_key", # Requirement to pass
    fail_message="The door is locked.",  # Message when blocked
    consume_item=False                # If True, key is consumed on use
)
```

**Adding to a Location:**

```python
Location(
    id="guard_room",
    name="Guard Room",
    description="A small room with a locked door marked STORAGE.",
    exits={"outside": "street", "storage": "storage_room"},
    exit_conditions=[
        ExitCondition(
            exit_name="storage",
            condition="has_item:key",
            fail_message="The storage door is locked. You need a key.",
            consume_item=False
        )
    ]
)
```

#### Hidden/Secret Locations

Locations can be marked as hidden, meaning they don't appear in exit lists until the player discovers them. This rewards exploration and perception.

**Creating a Hidden Location:**

```python
from scenario import Location

# A secret cave that requires perception to find
secret_cave = Location(
    id="secret_cave",
    name="Hidden Hollow",
    description="A natural cave hidden behind overgrown vines.",
    exits={"out": "forest_clearing"},
    
    # Mark as hidden
    hidden=True,
    
    # How to discover (skill check, item, level, or visited condition)
    discovery_condition="skill:perception:14",
    
    # Hint for observant players
    discovery_hint="The vines along the cliff face seem unusually thick...",
    
    # Reward for finding it
    items=["ancient_amulet", "gold_coins"]
)
```

**Adding the Exit (in parent location):**

```python
forest_clearing = Location(
    id="forest_clearing",
    name="Forest Clearing",
    description="A peaceful clearing.",
    exits={
        "path": "village",
        "hidden path": "secret_cave"  # Exit exists but is hidden until discovered
    }
)
```

**Discovery Condition Formats:**

| Format | Description | Example |
|--------|-------------|---------|
| `skill:<name>:<dc>` | Requires skill check | `skill:perception:14` |
| `has_item:<key>` | Requires specific item | `has_item:treasure_map` |
| `level:<n>` | Requires player level | `level:5` |
| `visited:<location_id>` | Requires visiting another location | `visited:library` |

**How get_exits() Works:**

```python
manager = LocationManager()
manager.add_location(forest_clearing)
manager.add_location(secret_cave)

manager.set_available_locations(["forest_clearing", "secret_cave"])
manager.set_current_location("forest_clearing")

# Before discovery - hidden exit is filtered out
exits = manager.get_exits()
print(exits)  # {"path": "village"} - no "hidden path"!

# After discovery
manager.discover_secret("secret_cave")
exits = manager.get_exits()
print(exits)  # {"path": "village", "hidden path": "secret_cave"}
```

**Checking Discovery Conditions (in game.py):**

```python
# Player tries to search the area
location_id = manager.get_hidden_exits().get("hidden path")
if location_id:
    can_discover, requirement = manager.check_discovery(location_id, game_state)
    
    if can_discover:
        manager.discover_secret(location_id)
        print("You discovered a hidden location!")
    elif requirement.startswith("skill_check:"):
        # Parse: "skill_check:perception:14"
        parts = requirement.split(":")
        skill, dc = parts[1], int(parts[2])
        # Roll skill check...
```

**Discovery Hints:**

```python
# Get hints for all hidden exits from current location
hints = manager.get_discovery_hints()
for hint in hints:
    print(f"💡 {hint}")  # "The vines look unusually thick..."
```

**Key Methods:**

| Method | Description |
|--------|-------------|
| `discover_secret(id)` | Mark a hidden location as discovered |
| `is_secret_discovered(id)` | Check if location has been discovered |
| `get_hidden_exits()` | Get undiscovered hidden exits from current location |
| `get_discovery_hints()` | Get hint strings for hidden exits |
| `check_discovery(id, state)` | Check if discovery conditions are met |

**Persistence:**

The `discovered_secrets` list is automatically saved and restored with the LocationManager:

```python
# Saving
state = manager.to_dict()
# state["discovered_secrets"] = ["secret_cave", "treasure_nook"]

# Loading
manager.restore_state(saved_state)
# Discovered secrets are preserved
```

**Goblin Cave Secret Locations:**

The Goblin Cave scenario includes two hidden locations:

1. **secret_cave** (in forest_clearing)
   - Discovery: Perception DC 14
   - Hint: "The vines along the cliff face seem unusually thick..."
   - Loot: ancient_amulet, healing_potion, gold_coins

2. **treasure_nook** (in boss_chamber)
   - Discovery: Investigation DC 12
   - Hint: "One section of the wall behind the throne looks different..."
   - Loot: enchanted_dagger, ruby_ring, gold_pile, rare_scroll

**Supported Condition Types:**

| Format | Meaning | Example |
|--------|---------|---------|
| `has_item:KEY` | Requires item in inventory | `"has_item:rusty_key"` |
| `gold:AMOUNT` | Requires minimum gold | `"gold:50"` |
| `visited:LOCATION` | Must have visited location | `"visited:cave_entrance"` |
| `skill:ABILITY:DC` | Triggers skill check | `"skill:strength:15"` |
| `objective:ID` | Requires completed objective | `"objective:defeat_guard"` |
| `flag:NAME` | Custom game flag is set | `"flag:bridge_repaired"` |

**How It Works:**
1. Player tries to move through an exit with a condition
2. `check_exit_condition()` evaluates the condition against game_state
3. If failed: Movement blocked with fail_message
4. If passed: Exit is permanently unlocked, movement succeeds
5. Future visits don't require the condition (door stays open)

**Example: Goblin Cave Storage Room (Complete Story Flow)**

```python
# 1. Place the key in a discoverable location
Location(
    id="goblin_camp_shadows",
    name="Goblin Warren - Shadows",
    items=["poison_vial", "dagger", "storage_key"],  # Key is here!
    events=[
        LocationEvent(
            id="shadow_discovery",
            trigger=EventTrigger.ON_FIRST_VISIT,
            narration="You find a dead goblin scout - poisoned. A brass key hangs from his belt.",
            one_time=True
        )
    ]
)

# 2. Create the locked door with exit condition
Location(
    id="goblin_camp_main",
    exits={"storage": "goblin_storage", "back": "entrance"},
    exit_conditions=[
        ExitCondition(
            exit_name="storage",
            condition="has_item:storage_key",
            fail_message="The storage door is locked. You need a key.",
            consume_item=False
        )
    ]
)

# 3. Reward the player for finding the key
Location(
    id="goblin_storage",
    items=["healing_potion", "gold_pouch", "longsword"],
    events=[
        LocationEvent(
            id="storage_discovery",
            trigger=EventTrigger.ON_FIRST_VISIT,
            narration="You've found the goblins' loot stash!",
            effect="xp:25",  # Bonus XP for exploring
            one_time=True
        )
    ]
)
```

**Story Flow for Player:**
1. Player explores shadows → sees "brass key on dead goblin" narration
2. Player types `take storage_key` → key added to inventory
3. Player goes to main camp → sees "door marked STORAGE"
4. Player types `go storage` → "You use the Storage Key." → enters storage
5. Player gets bonus loot + 25 XP for discovering the hidden room

#### Event Condition Formats

The `condition` field in LocationEvent supports these formats:

| Format | Meaning | Example |
|--------|---------|---------|
| `has_item:KEY` | Player has item | `"has_item:torch"` |
| `!has_item:KEY` | Player lacks item | `"!has_item:trap_kit"` |
| `skill:SKILL:DC` | Skill check required | `"skill:perception:15"` |
| `visited:LOCATION` | Location visited | `"visited:boss_room"` |
| `objective:ID` | Objective complete | `"objective:find_key"` |

**Example Events with Conditions:**

```python
# Trap only triggers if player lacks disarm tool
LocationEvent(
    id="arrow_trap",
    trigger=EventTrigger.ON_ENTER,
    narration="An arrow shoots from the wall!",
    effect="damage:1d6",
    condition="!has_item:trap_disarm_kit",
    one_time=True
)

# Secret door requires perception check
LocationEvent(
    id="secret_door",
    trigger=EventTrigger.ON_LOOK,
    narration="You notice a hidden door behind the bookshelf!",
    effect="add_exit:library:secret_room",
    condition="skill:perception:14",
    one_time=True
)
```

#### Event Effect Formats

The `effect` field supports these actions:

| Format | Action | Example |
|--------|--------|---------|
| `damage:DICE` | Deal damage | `"damage:1d4"`, `"damage:2d6+2"` |
| `heal:DICE` | Restore HP | `"heal:1d8+4"` |
| `add_item:KEY` | Add to inventory | `"add_item:rusty_key"` |
| `remove_item:KEY` | Remove from inventory | `"remove_item:lockpick"` |
| `objective:ID` | Complete objective | `"objective:find_clue"` |
| `add_exit:LOC:DEST` | Reveal new exit | `"add_exit:library:secret_room"` |
| `skill_check:SKILL:DC\|FAIL` | Check or fail effect | `"skill_check:dex:12\|damage:1d4"` |

---

### Travel Menu System (Phase 3.2.1 Priority 9)

The travel menu system provides an improved navigation experience with numbered destinations, danger indicators, and approach style detection.

#### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRAVEL MENU FLOW                             │
├─────────────────────────────────────────────────────────────────┤
│  Player: "travel" / "where" / "destinations"                   │
│                           ↓                                     │
│  show_travel_menu() displays:                                  │
│    [1] Forest Path ⚠️                                          │
│    [2] Village Square ✓                                        │
│    [3] Dark Cave ☠️                                            │
│                           ↓                                     │
│  Player: "1" (or "go forest path")                             │
│                           ↓                                     │
│  is_destination_dangerous() → True for threatening/deadly/new  │
│                           ↓                                     │
│  prompt_approach_style(): "How do you approach?"               │
│                           ↓                                     │
│  Player: "sneak quietly" / "run" / "carefully"                 │
│                           ↓                                     │
│  parse_approach_intent() → "stealth" / "urgent" / "cautious"   │
│                           ↓                                     │
│  Skill check (Stealth DC or Perception DC from location)       │
│                           ↓                                     │
│  perform_travel() → Movement, quests, merchants, encounters    │
└─────────────────────────────────────────────────────────────────┘
```

#### Danger Indicators

Each destination displays a danger indicator based on its threat level:

| Indicator | Level | Description |
|-----------|-------|-------------|
| ⚠️ | Threatening | Known dangerous, has untriggered encounter |
| ☠️ | Deadly | Very dangerous atmosphere |
| ❓ | Uneasy | Unexplored or has random encounters |
| ✓ | Safe | Previously visited, no threats |

**Danger Level Calculation (`get_destination_danger_level()`):**

```python
def get_destination_danger_level(location: Location) -> str:
    """Returns: 'safe', 'uneasy', 'threatening', or 'deadly'"""
    
    # Check atmosphere threat level
    if location.atmosphere:
        threat = location.atmosphere.threat_level.lower()
        if threat == "deadly":
            return "deadly"
        if threat in ("threatening", "hostile", "dangerous"):
            return "threatening"
    
    # Untriggered encounter = threatening
    if location.encounter and not location.encounter_triggered:
        return "threatening"
    
    # Random encounters possible = uneasy
    if location.random_encounters and any(
        re.triggers_left > 0 for re in location.random_encounters
    ):
        return "uneasy"
    
    return "safe"
```

#### Approach Intent Detection

The `parse_approach_intent()` function detects player approach style from natural language:

```python
APPROACH_KEYWORDS = {
    "stealth": ["sneak", "quietly", "creep", "silently", "stealthily", 
                "shadow", "shadows", "unseen", "unnoticed", "hide"],
    "urgent": ["run", "rush", "sprint", "dash", "hurry", "quickly", 
               "fast", "flee", "bolt", "charge"],
    "cautious": ["carefully", "cautiously", "slowly", "wary", "watchful",
                 "alert", "look around", "check", "scout", "observe"]
}

def parse_approach_intent(player_input: str) -> str:
    """Returns: 'stealth', 'urgent', 'cautious', or 'normal'"""
    text_lower = player_input.lower()
    
    # Priority: stealth > cautious > urgent > normal
    for approach, keywords in APPROACH_KEYWORDS.items():
        if any(keyword in text_lower for keyword in keywords):
            return approach
    
    return "normal"
```

#### Location-Based DCs

Each location can define custom difficulty for approach skill checks via `LocationAtmosphere`:

```python
@dataclass
class LocationAtmosphere:
    description: str = ""
    lighting: str = "normal"
    sounds: str = ""
    smells: str = ""
    threat_level: str = "none"
    stealth_dc: int = 12    # DC for stealth approach
    perception_dc: int = 10 # DC for cautious approach
```

**Getting Approach DCs:**

```python
def get_approach_dcs(location: Location) -> tuple[int, int]:
    """Returns (stealth_dc, perception_dc) for a location"""
    if location and location.atmosphere:
        return (location.atmosphere.stealth_dc, 
                location.atmosphere.perception_dc)
    return (12, 10)  # Default DCs
```

#### Skill Check Integration

When approaching dangerous locations with stealth or caution:

**Stealth Approach:**
- Player triggers Stealth check vs location's `stealth_dc`
- **Success:** Normal travel, narration mentions stealthy arrival
- **Failure:** Enemy may get SURPRISE round (if encounter exists)

**Cautious Approach:**
- Player triggers Perception check vs location's `perception_dc`  
- **Success:** Player spots potential threats, gets advantage info
- **Failure:** Normal travel (no penalty, just missed info)

**Urgent Approach:**
- No skill check required
- Narrative mentions rushed travel

#### Shared Travel Function

All travel logic is consolidated in `perform_travel()`:

```python
def perform_travel(
    exit_name: str,
    loc_mgr: LocationManager,
    character: Character,
    chat: ChatSession,
    quest_manager: QuestManager,
    scenario_manager: ScenarioManager,
    approach_type: str = "normal",
    surprise_player: bool = False
) -> tuple[bool, Optional[Location], Optional[str]]:
    """
    Shared travel logic for both menu selections and 'go' commands.
    
    Returns:
        (success, new_location, combat_result)
        - success: True if movement completed
        - new_location: The destination Location if moved
        - combat_result: "victory"/"defeat" if combat occurred, None otherwise
    """
```

**Travel Sequence:**
1. Build game_state with character, inventory, flags
2. Attempt movement via `loc_mgr.move()`
3. Handle item consumption (keys used on locked doors)
4. Trigger location-entry quest objectives
5. Update traveling merchant spawns
6. Check for random encounters (with surprise if applicable)
7. Get AI narration for new location
8. Display location with context menu

#### Usage Examples

**Displaying the Travel Menu:**

```python
# In game.py command handler
if player_input.lower() in ["travel", "where", "destinations", "exits"]:
    current = loc_mgr.get_current_location()
    show_travel_menu(current, loc_mgr)
```

**Handling Number Selection:**

```python
# Player typed "1", "2", etc.
if player_input.isdigit():
    selection = int(player_input)
    exits = list(current_location.exits.keys())
    if 1 <= selection <= len(exits):
        destination = exits[selection - 1]
        dest_location = loc_mgr.locations.get(current_location.exits[destination])
        
        if is_destination_dangerous(dest_location):
            approach = prompt_approach_style()
            approach_type = parse_approach_intent(approach)
            # Handle skill check based on approach...
        
        perform_travel(destination, loc_mgr, character, ...)
```

---

### World Map System (Phase 4.5)

The Interactive World Map provides visual navigation through clickable map nodes.

#### Overview

The map system transforms travel from text commands ("go tavern") to visual click-to-travel on a stylized map. Each location becomes a node with coordinates, icons, and visual states.

#### Data Structures

**Location Map Fields (new fields on Location dataclass):**
```python
@dataclass
class Location:
    # ... existing fields ...
    
    # Map Visualization (Phase 4.5)
    map_x: float = 0.0              # X coordinate (0.0 to 1.0)
    map_y: float = 0.0              # Y coordinate (0.0 to 1.0)
    map_icon: str = "🏠"            # Emoji/icon for marker
    map_label: str = ""             # Short label (defaults to name)
    map_region: str = "default"     # Region this belongs to
    map_hidden: bool = False        # Hidden until discovered
```

**MapNode (visual representation):**
```python
@dataclass
class MapNode:
    location_id: str
    x: float                        # Normalized X (0-1)
    y: float                        # Normalized Y (0-1)
    icon: str
    label: str
    
    # Visual State
    is_current: bool = False        # Player is here
    is_visited: bool = False        # Has been visited
    is_visible: bool = True         # Not hidden by fog of war
    is_accessible: bool = True      # Can travel to
    
    # Status Indicators
    danger_level: str = "safe"      # safe/uneasy/threatening/deadly
    has_shop: bool = False
    has_quest: bool = False
    has_npc: bool = False
```

**WorldMap Class:**
```python
class WorldMap:
    """Manages the visual world map for a scenario."""
    
    def build_from_locations(self, locations: Dict[str, Location]):
        """Generate map from Location objects."""
        
    def update_current(self, location_id: str):
        """Update current location marker."""
        
    def mark_visited(self, location_id: str):
        """Mark location as visited (reveal fog of war)."""
        
    def get_clickable_nodes(self) -> List[MapNode]:
        """Get nodes player can click to travel to."""
        
    def to_dict(self) -> dict:
        """Serialize map state for API."""
```

#### Usage Example

```python
# Build map from scenario locations
world_map = WorldMap(scenario_id="goblin_cave")
world_map.build_from_locations(location_manager.locations)

# Update on player movement
world_map.update_current("village_square")
world_map.mark_visited("village_square")
world_map.reveal_adjacent("village_square", location_manager.locations)

# Get data for frontend
map_data = world_map.to_dict()
# Send to Flutter widget via API
```

#### Goblin Cave Map Coordinates

```python
GOBLIN_CAVE_MAP_DATA = {
    # Village Region (y: 0.0 - 0.25)
    "tavern_main":     {"x": 0.15, "y": 0.12, "icon": "🍺"},
    "village_square":  {"x": 0.50, "y": 0.12, "icon": "🏛️"},
    "blacksmith_shop": {"x": 0.85, "y": 0.12, "icon": "🛠️"},
    
    # Forest Region (y: 0.25 - 0.55)
    "forest_path":     {"x": 0.50, "y": 0.38, "icon": "🌲"},
    "forest_clearing": {"x": 0.35, "y": 0.52, "icon": "🌳"},
    "cave_entrance":   {"x": 0.65, "y": 0.52, "icon": "💀"},
    
    # Cave Region (y: 0.55 - 1.0)
    "cave_tunnel":     {"x": 0.35, "y": 0.70, "icon": "🕯️"},
    "goblin_camp":     {"x": 0.65, "y": 0.70, "icon": "⚔️"},
    "storage_room":    {"x": 0.35, "y": 0.88, "icon": "📦"},
    "boss_chamber":    {"x": 0.65, "y": 0.88, "icon": "👑"}
}
```

#### Frontend Integration

See [UI_DESIGN_SPEC.md](UI_DESIGN_SPEC.md#world-map-panel) for Flutter widget details.

---

### NPC System (Phase 3.3)

The NPC system provides structured NPCs with dialogue, roles, disposition tracking, and AI-enhanced conversations.

#### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       NPCManager                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Dict[str, NPC] _npcs                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│    ┌──────────────────────┼──────────────────────┐             │
│    ▼                      ▼                      ▼             │
│ ┌──────────┐        ┌──────────┐          ┌──────────┐        │
│ │   NPC    │        │   NPC    │          │   NPC    │        │
│ │  Bram    │        │  Greth   │          │  Elira   │        │
│ └──────────┘        └──────────┘          └──────────┘        │
│  QUEST_GIVER            INFO              RECRUITABLE          │
│  tavern_main          tavern_bar        forest_clearing        │
└─────────────────────────────────────────────────────────────────┘
```

#### NPC Dataclass

```python
from npc import NPC, NPCRole

npc = NPC(
    id="bram",                          # Unique identifier
    name="Bram",                        # Display name
    description="A worried farmer...",  # For AI context
    role=NPCRole.QUEST_GIVER,           # Behavior type
    location_id="tavern_main",          # Current location
    dialogue={                          # Keyed responses
        "greeting": "Please, help me!",
        "quest": "My daughter Lily...",
        "about_goblins": "Wicked creatures.",
        "farewell": "Please hurry..."
    },
    disposition=30,                     # -100 to +100
    quests=["rescue_lily"],             # Quest IDs offered
    shop_inventory=[],                  # For merchants
    merchant_markup=1.5,                # Buy price multiplier
    is_recruitable=False,               # Can join party?
    recruitment_condition="",           # e.g., "skill:charisma:14"
    recruited=False                     # Already in party?
)
```

#### NPCRole Enum

| Role | Description | Special Behavior |
|------|-------------|------------------|
| `MERCHANT` | Sells items | Has shop_inventory, merchant_markup |
| `QUEST_GIVER` | Offers quests | Has quests list |
| `INFO` | Provides gossip/lore | Extensive dialogue options |
| `HOSTILE` | Enemy NPC | May trigger combat |
| `RECRUITABLE` | Can join party | Has recruitment_condition |
| `NEUTRAL` | Generic NPC | No special behavior |

#### Disposition System

NPCs track their attitude toward the player using a robust disposition system.

**Disposition Constants (npc.py):**

```python
# Threshold constants
DISPOSITION_HOSTILE = -50      # Below this: hostile behavior
DISPOSITION_UNFRIENDLY = -10   # Below this: unfriendly behavior  
DISPOSITION_FRIENDLY = 10      # Above this: friendly behavior
DISPOSITION_TRUSTED = 50       # Above this: trusted behavior

# Price modifier constants
PRICE_MODIFIER_HOSTILE = 0.0       # Cannot trade at all
PRICE_MODIFIER_UNFRIENDLY = 1.25   # +25% prices
PRICE_MODIFIER_NEUTRAL = 1.0       # Normal prices
PRICE_MODIFIER_FRIENDLY = 0.9      # -10% discount
PRICE_MODIFIER_TRUSTED = 0.8       # -20% discount
```

**Disposition Levels:**

| Level | Range | Emoji | Behavior |
|-------|-------|-------|----------|
| `hostile` | < -50 | 🔴 | Refuses trade, may attack |
| `unfriendly` | -50 to -10 | 🟠 | +25% prices, limited dialogue |
| `neutral` | -10 to +10 | 🟡 | Normal prices and interactions |
| `friendly` | +10 to +50 | 🟢 | -10% discount, extra dialogue |
| `trusted` | > +50 | 🔵 | -20% discount, special quests |

**NPC Disposition Methods:**

```python
# Get disposition level as string
npc.get_disposition_level()     # Returns: "hostile", "unfriendly", "neutral", "friendly", or "trusted"

# Get formatted label with emoji
npc.get_disposition_label()     # Returns: "🟢 Friendly (+35)"

# Get price multiplier based on disposition
npc.get_disposition_modifier()  # Returns: 0.0, 1.25, 1.0, 0.9, or 0.8

# Check if NPC will trade
npc.can_trade()                 # Returns: False if hostile, True otherwise

# Modify disposition (with clamping to -100/+100)
npc.modify_disposition(10)      # Increases by 10
npc.modify_disposition(-25)     # Decreases by 25
```

**Testing:**

The disposition system has comprehensive test coverage:
- `test_reputation.py` - 62 core functionality tests
- `test_reputation_hostile.py` - 36 adversarial/security tests

Tests cover: boundary values, type confusion, numeric edge cases (NaN, infinity), 
state manipulation, label injection, serialization attacks, and more.

#### Action-Based Disposition System

Player actions now dynamically affect NPC relationships beyond just talking to them.

**Trade Actions:**
```python
# Buying/selling affects disposition slightly
# +1 disposition per buy/sell transaction
# +2 for successful haggle (on top of the discount)
```

**Gift System:**
```python
from npc import calculate_gift_disposition

# Give items to NPCs to improve relationships
# Command: give <item> to <npc>

# Disposition bonus scales with item value:
item_value <= 0:    +0   (invalid gift)
item_value <= 10:   +5   (cheap gift)
item_value <= 25:   +8   (modest gift)
item_value <= 50:   +12  (nice gift)
item_value <= 100:  +15  (generous gift)
item_value > 100:   +20  (extravagant gift)

# Calculate bonus programmatically:
bonus = calculate_gift_disposition(item.value)  # Returns 5-20
```

**Theft System:**
```python
# Command: steal from <npc>
# DEX (Sleight of Hand) check DC 15

# Outcomes:
# - Natural 1 (Critical Failure): -50 disposition, caught red-handed
# - Failure (< 15): -30 disposition, noticed stealing
# - Success (>= 15): Steal 2d10 gold, no disposition change
```

**Quest Completion Rewards:**

Quest completion grants disposition bonuses to the quest giver NPC based on quest importance:

```python
from quest import QuestType

# QuestType enum determines disposition reward:
QuestType.MAIN   # +25 disposition on completion
QuestType.SIDE   # +15 disposition on completion  
QuestType.MINOR  # +10 disposition on completion

# Quest failure penalties (optional):
QuestType.MAIN   # -15 disposition on failure
QuestType.SIDE   # -10 disposition on failure
QuestType.MINOR  # -5 disposition on failure
```

**Quest Type Usage:**
```python
from quest import Quest, QuestType

# Creating quests with types:
main_quest = Quest(
    id="rescue_lily",
    name="Rescue Lily",
    description="Save the farmer's daughter",
    quest_type=QuestType.MAIN,  # +25 to giver on complete
    giver_npc_id="bram"
)

side_quest = Quest(
    id="clear_path",
    name="Clear the Path",
    quest_type=QuestType.SIDE,  # +15 to giver on complete
    giver_npc_id="bram"
)

# Default is QuestType.SIDE if not specified
```

#### Dialogue System

**Getting Dialogue:**

```python
# Basic dialogue retrieval
npc.get_dialogue("greeting")        # "Hello, traveler!"
npc.get_dialogue("about_goblins")   # "Those wretched creatures..."
npc.has_dialogue("quest")           # True/False
```

**Player Commands:**

```python
# In-game talk command
talk bram                    # Gets greeting + AI-enhanced response
talk barkeep about goblins   # Gets about_goblins dialogue
speak to elira about cave    # Asks about specific topic
```

**AI-Enhanced Dialogue:**

The `NPC_DIALOGUE_PROMPT` in game.py generates immersive NPC responses:

```python
from game import get_npc_dialogue

response = get_npc_dialogue(
    chat,           # AI chat session
    npc,            # NPC object
    topic="goblins", # Optional topic
    scenario_context="Player is in tavern..."
)
```

The AI uses:
- NPC's role and description for personality
- Dialogue keys as base responses (expands with detail)
- Disposition level to adjust tone
- Scenario context for relevance

#### NPCManager

Manages all NPCs in a scenario:

```python
from npc import NPCManager, create_goblin_cave_npcs

# Create manager with pre-defined NPCs
manager = create_goblin_cave_npcs()

# Get NPCs
manager.get_npc("bram")                    # By ID
manager.get_npc_by_name("Barkeep")         # By name (case-insensitive)
manager.get_npcs_at_location("tavern_main") # At location
manager.get_npcs_by_role(NPCRole.MERCHANT)  # By role

# Special getters
manager.get_merchants()     # All MERCHANT role NPCs
manager.get_quest_givers()  # All QUEST_GIVER role NPCs
manager.get_recruitable()   # Recruitable NPCs not yet recruited

# Modify NPCs
manager.move_npc("elira", "cave_entrance")  # Change location
manager.remove_npc("dead_guard")             # Remove from game
```

#### Serialization

NPCs persist in save files:

```python
# Save
npc_state = npc.to_dict()
manager_state = manager.to_dict()

# Load
npc = NPC.from_dict(npc_state)
manager.from_dict(manager_state)

# Partial state update (disposition, recruited, location only)
manager.update_npc_states({
    "bram": {"disposition": 50},
    "elira": {"recruited": True, "location_id": "party"}
})
```

#### Adding NPCs to Scenarios (DLC-Ready Pattern)

NPCs are defined per-scenario using factory functions. The core NPC classes (`NPC`, `NPCRole`, `NPCManager`) 
are reusable across all scenarios/DLCs, while each scenario defines its own NPCs.

**Pattern for new scenarios/DLCs:**

```python
# In scenario.py (or a separate DLC file)
from npc import NPC, NPCRole, NPCManager

def create_my_dlc_npcs() -> NPCManager:
    """Factory function for My DLC scenario NPCs."""
    manager = NPCManager()
    
    # Define NPCs for this scenario
    manager.add_npc(NPC(
        id="new_character",
        name="Sir Example",
        role=NPCRole.QUEST_GIVER,
        location_id="starting_town",
        dialogue={"greeting": "Hello, adventurer!"},
        quests=["main_quest"]
    ))
    
    return manager

def create_my_dlc_scenario() -> Scenario:
    # Create locations...
    # Create scenes...
    
    npc_manager = create_my_dlc_npcs()  # Use the factory function
    
    return Scenario(
        id="my_dlc",
        name="My DLC Adventure",
        npc_manager=npc_manager,
        # ...
    )
```

**Core Classes (npc.py - Reusable):**
- `NPC` - Dataclass with all NPC fields
- `NPCRole` - Enum (MERCHANT, QUEST_GIVER, INFO, HOSTILE, RECRUITABLE, NEUTRAL)
- `NPCManager` - Manager for tracking and querying NPCs
- `format_npc_for_display()` - Display formatting helper

**Scenario-Specific Content (scenario.py or DLC file):**
- `create_goblin_cave_npcs()` - NPCs for Goblin Cave scenario
- `create_my_dlc_npcs()` - NPCs for your new DLC

#### Starter NPCs (Goblin Cave Scenario)

The Goblin Cave scenario includes NPCs spread across multiple locations:

**Tavern Locations:**

| NPC | Role | Location ID | Purpose |
|-----|------|-------------|---------|
| **Bram** | QUEST_GIVER | `tavern_main` | Desperate farmer, offers main quest "Rescue Lily" |
| **Marcus** | RECRUITABLE | `tavern_main` | Mercenary, recruitable (25g) |
| **Greth the Barkeep** | INFO | `tavern_bar` | Tavern keeper, provides gossip/lore about goblins and village |

> **Note:** The tavern has two sub-locations:
> - `tavern_main` - Main Room with hearth, tables, and most patrons
> - `tavern_bar` - Bar area where Greth the Barkeep works

**Village Locations:**

| NPC | Role | Location ID | Purpose |
|-----|------|-------------|---------|
| **Gavin the Blacksmith** | MERCHANT | `blacksmith_shop` | Sells weapons/armor |

**Forest Locations:**

| NPC | Role | Location ID | Purpose |
|-----|------|-------------|---------|
| **Elira** | RECRUITABLE | `forest_clearing` | Elf ranger, recruitable (CHA DC 12) |
| **Trader Mira** | MERCHANT | `forest_clearing` | Traveling merchant, sells supplies |

**Cave Locations:**

| NPC | Role | Location ID | Purpose |
|-----|------|-------------|---------|
| **Shade** | RECRUITABLE | `goblin_camp_shadows` | Rogue, recruitable (CHA DC 14) |
| **Lily** | INFO | `goblin_camp_main` | Rescue target (Bram's daughter) |

**NPC Location Query Examples:**

```python
from scenario import create_goblin_cave_scenario

scenario = create_goblin_cave_scenario()
npc_manager = scenario.npc_manager

# Get NPCs at specific locations
tavern_main_npcs = npc_manager.get_npcs_at_location("tavern_main")
# Returns: [Bram, Marcus]

bar_npcs = npc_manager.get_npcs_at_location("tavern_bar")
# Returns: [Greth the Barkeep]

# Get all recruitable NPCs
recruitable = npc_manager.get_recruitable()
# Returns: [Marcus, Elira, Shade]

# Find NPC by name (case-insensitive)
barkeep = npc_manager.get_npc_by_name("Greth")
# Returns: Greth the Barkeep NPC
```

---

### Shop System (Phase 3.3.3)

The shop system allows players to buy items from merchants, sell their loot, and haggle for better prices. Implemented in `src/shop.py` with full integration into game commands.

#### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      SHOP SYSTEM FLOW                           │
└─────────────────────────────────────────────────────────────────┘

  Player: "shop"              Player: "buy healing potion"
        │                            │
        ▼                            ▼
┌───────────────┐            ┌───────────────┐
│ ShopManager.  │            │ ITEMS dict    │
│ get_shop_at_  │            │ (inventory.py)│
│ location()    │            └───────┬───────┘
└───────┬───────┘                    │
        │                            ▼
        ▼                    ┌───────────────┐
┌───────────────┐            │ calculate_    │
│ format_shop_  │            │ buy_price()   │
│ display()     │            └───────┬───────┘
└───────────────┘                    │
                                     ▼
                             ┌───────────────┐
                             │ Shop.has_item()│
                             │ decrement_    │
                             │ stock()       │
                             └───────┬───────┘
                                     │
                                     ▼
                             ┌───────────────┐
                             │ buy_item()    │
                             │ Returns       │
                             │ Transaction-  │
                             │ Result        │
                             └───────────────┘
```

#### Core Classes

**Shop Dataclass** (`src/shop.py`):
```python
from shop import Shop, ShopType, ShopInventoryItem

shop = Shop(
    id="gavins_forge",
    name="Gavin's Forge",
    owner_npc_id="gavin",           # NPC who runs the shop
    location_id="blacksmith_shop",  # Where shop is located
    shop_type=ShopType.BLACKSMITH,  # GENERAL, BLACKSMITH, ALCHEMIST, TRAVELING
    base_markup=1.15,               # 15% above base value
    accepts_haggle=True,
    haggle_dc=12
)

# Add items to shop
shop.add_item("dagger", stock=-1)      # Unlimited stock
shop.add_item("longsword", stock=2)    # Limited: 2 in stock
shop.add_item("leather_armor", stock=3, max_stock=3)  # Restockable
```

**ShopManager Class** (`src/shop.py`):
```python
from shop import ShopManager

shop_manager = ShopManager()
shop_manager.add_shop(shop)

# Lookup methods
shop = shop_manager.get_shop("gavins_forge")
shop = shop_manager.get_shop_at_location("blacksmith_shop")
shop = shop_manager.get_shop_by_owner("gavin")

# Haggle state tracking (persists per-shop)
state = shop_manager.get_haggle_state("gavins_forge")
# {"discount": 0.0, "increase": 0.0, "attempted": False}

shop_manager.set_haggle_result("gavins_forge", discount=0.2)  # 20% discount
shop_manager.reset_haggle_state()  # Reset all shops
```

#### Price Calculation

Prices are affected by multiple factors:

```python
from shop import calculate_buy_price, calculate_sell_price, get_disposition_price_modifier

# Buying: base * shop_markup * item_markup * disposition * (1 - haggle + failed_haggle)
buy_price = calculate_buy_price(
    base_value=50,              # Item's base gold value
    shop_markup=1.2,            # Shop's general markup (20%)
    item_markup=1.0,            # Per-item markup
    disposition_modifier=0.9,   # Friendly NPC = 10% discount
    haggle_discount=0.2,        # Successful haggle = 20% off
    haggle_increase=0.0         # Failed haggle = 10% increase
)

# Selling: base * sell_rate * inverse_disposition
sell_price = calculate_sell_price(
    base_value=50,
    sell_rate=0.5,              # Default 50% of value
    disposition_modifier=0.9    # Friendly = better sell price
)

# Get disposition modifier from NPC
modifier = get_disposition_price_modifier("hostile")    # None (won't trade)
modifier = get_disposition_price_modifier("unfriendly") # 1.25 (+25%)
modifier = get_disposition_price_modifier("neutral")    # 1.0
modifier = get_disposition_price_modifier("friendly")   # 0.9 (-10%)
modifier = get_disposition_price_modifier("trusted")    # 0.8 (-20%)
```

#### Transaction Functions

```python
from shop import buy_item, sell_item, attempt_haggle

# Buying
result = buy_item(
    character,                  # Player character with gold and inventory
    shop,                       # Shop object
    "healing_potion",           # Item ID
    quantity=2,                 # How many to buy
    shop_manager,               # For haggle state
    "friendly"                  # NPC disposition label
)
# Returns TransactionResult with success, message, prices

# Selling
result = sell_item(
    character,
    shop,
    "dagger",
    quantity=1,
    "neutral"
)

# Haggling (Charisma check DC vs shop.haggle_dc)
result = attempt_haggle(
    character,                  # Needs character.charisma
    shop,
    shop_manager,
    npc                         # Optional: for disposition penalty on failure
)
# Returns HaggleResult with roll, success, discount/increase
```

#### Display Functions

```python
from shop import format_shop_display, format_transaction_result, format_haggle_result

# Shop display
display = format_shop_display(
    shop,
    player_gold=100,
    disposition_level="friendly",
    haggle_discount=0.2,
    haggle_increase=0.0
)
print(display)
```

**Example Output:**
```
┌──────────────────────────────────────────────────────────┐
│ 🛒 Gavin's Forge                                        │
│ 💰 Your Gold: 100                                       │
├──────────────────────────────────────────────────────────┤
│ ✨ Haggle Discount: 20% off!                            │
│ 🤝 Friendly Discount: 10% off                           │
│                                                          │
│ FOR SALE:                                                │
│   1. Dagger [DMG: 1d4]..............................2g ✓ │
│      (A simple blade for close combat.)                  │
│   2. Longsword (x2) [DMG: 1d8].....................10g ✓ │
│      (A versatile one-handed sword.)                     │
│   3. Studded Leather [AC: +2]......................51g ✗ │
│      (Leather reinforced with metal rivets.)             │
├──────────────────────────────────────────────────────────┤
│ Commands: buy <item>, sell <item>, haggle, leave         │
└──────────────────────────────────────────────────────────┘
```

**Stats Display:** Items now show stats inline:
- **Weapons:** `[DMG: 1d8]` - Damage dice
- **Armor:** `[AC: +2]` - AC bonus
- **Consumables:** `[HEAL: 2d4+2]` - Healing amount
- **Affordability:** ✓ (can afford) or ✗ (too expensive)

#### Shop Commands (game.py)

| Command | Description | Example |
|---------|-------------|---------|
| `shop` / `browse` / `store` | View shop inventory | `shop` |
| `buy <item> [qty]` | Purchase item | `buy dagger`, `buy 3 potions` |
| `sell <item> [qty]` | Sell item | `sell goblin ear 5` |
| `haggle` / `bargain` | Negotiate prices | `haggle` |

#### Factory Functions

```python
from shop import create_blacksmith_shop, create_traveling_merchant_shop, create_general_shop

# Blacksmith (fair prices, weapons & armor)
forge = create_blacksmith_shop(
    id="test_forge",
    name="Test Forge",
    owner_npc_id="smith",
    location_id="forge",
    weapons={"dagger": -1, "longsword": 2},
    armor={"leather_armor": 2},
    markup=1.15
)

# Traveling merchant (higher prices, shrewd)
trader = create_traveling_merchant_shop(
    id="wanderer",
    name="Wandering Trader",
    owner_npc_id="trader",
    items={"healing_potion": 3, "rare_gem": 1},
    markup=1.5  # 50% above base
)

# General store
store = create_general_shop(
    id="general",
    name="Village Supplies",
    owner_npc_id="shopkeep",
    location_id="village",
    items={"torch": -1, "rations": 20}
)
```

#### Creating Merchant NPCs

Merchants use the `NPCRole.MERCHANT` role:

```python
from npc import NPC, NPCRole, Personality

gavin = NPC(
    id="gavin",
    name="Gavin the Blacksmith",
    description="A burly man with soot-stained apron...",
    role=NPCRole.MERCHANT,          # IMPORTANT: Must be MERCHANT role
    location_id="blacksmith_shop",
    dialogue={
        "greeting": "*wipes hands* Welcome to me forge!",
        "about_weapons": "Everything I make is battle-tested.",
        "haggle_success": "*chuckles* Fine, I can work with that.",
        "haggle_fail": "*frowns* Price is what it is.",
        "farewell": "May your steel stay sharp!"
    },
    disposition=10,                  # Neutral-friendly
    personality=Personality(
        traits=["gruff", "honest", "proud of craft"],
        speech_style="direct, forge metaphors"
    )
)
```

#### Scenario Integration

Shops are created when a scenario starts in `game.py`:

```python
from scenario import create_goblin_cave_shops

# In main game loop, after scenario starts:
if scenario_id == "goblin_cave":
    create_goblin_cave_shops(shop_manager)
```

The function in `scenario.py` creates shops for that scenario:

```python
def create_goblin_cave_shops(shop_manager: ShopManager) -> None:
    gavins_forge = create_blacksmith_shop(
        id="gavins_forge",
        name="Gavin's Forge",
        owner_npc_id="gavin",
        location_id="blacksmith_shop",
        weapons={"dagger": -1, "shortsword": 3, "longsword": 2},
        armor={"leather_armor": 2, "shield": 3}
    )
    shop_manager.add_shop(gavins_forge)
```

#### Shop System Tests

The shop system has 70 comprehensive tests in `tests/test_shop.py`:

```bash
# Run shop tests
python -m pytest tests/test_shop.py -v

# Test categories:
# - TestShopInventoryItem (8 tests)
# - TestShop (12 tests)
# - TestShopManager (7 tests)
# - TestPriceCalculation (12 tests)
# - TestBuyItem (8 tests)
# - TestSellItem (3 tests)
# - TestHaggle (4 tests)
# - TestFactoryFunctions (3 tests)
# - TestDisplayFunctions (7 tests)
# - TestShopIntegration (4 tests)
```

---

### Traveling Merchants (Phase 3.3 - Priority 5)

The traveling merchant system allows NPCs to dynamically spawn and despawn at various locations, offering rotating inventory that changes with each appearance.

#### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 TRAVELING MERCHANT FLOW                         │
└─────────────────────────────────────────────────────────────────┘

  Player enters location
          │
          ▼
  ┌───────────────────┐
  │ For each traveling│
  │ merchant (NPC)    │
  └─────────┬─────────┘
            │
  ┌─────────┴─────────┐
  │ Is spawned?       │
  └─────────┬─────────┘
            │
     No     │     Yes
     ┌──────┴──────┐
     ▼             ▼
┌─────────┐  ┌─────────────┐
│ check_  │  │ Different   │
│ spawn() │  │ location?   │
└────┬────┘  └──────┬──────┘
     │              │
     ▼              ▼
┌─────────┐  ┌─────────────┐
│ spawn() │  │ visits >=   │
│ + rotate│  │ cooldown?   │
│ inv     │  └──────┬──────┘
└─────────┘         │
                    ▼
             ┌─────────────┐
             │ despawn()   │
             │ merchant    │
             └─────────────┘
```

#### NPC Traveling Fields

```python
from npc import NPC, NPCRole

traveling_merchant = NPC(
    id="wanderer",
    name="Zephyr the Wanderer",
    description="A mysterious traveler...",
    role=NPCRole.MERCHANT,
    location_id="",  # Empty = not currently spawned
    
    # Traveling Merchant Configuration
    is_traveling=True,              # Marks as traveling merchant
    spawn_chance=0.25,              # 25% chance per location entry
    possible_locations=[            # Where can spawn (empty = anywhere)
        "forest_clearing",
        "cave_entrance",
        "cave_tunnel",
        "goblin_storage"
    ],
    inventory_pool={                # Full pool of possible items
        "healing_potion": 4,        # item_key: max_quantity
        "torch": 8,
        "enchanted_dagger": 1,      # Rare items have lower quantity
    },
    inventory_rotation_size=5,      # How many items shown per spawn
    spawn_cooldown=4,               # Visits before respawning at same spot
    
    # State tracking (managed by system)
    last_spawn_location="",         # Where last spawned
    visits_since_spawn=0,           # Visits since last spawn
    
    # Standard merchant fields
    shop_inventory={},              # Filled by rotation on spawn
    merchant_markup=1.15            # 15% markup
)
```

#### Helper Functions

```python
from npc import (
    check_traveling_merchant_spawn,
    rotate_merchant_inventory,
    spawn_traveling_merchant,
    despawn_traveling_merchant,
    update_traveling_merchant_visits
)

# Check if merchant should spawn at location
# Returns True if: is_traveling, location valid, cooldown passed, spawn_chance roll succeeds
if check_traveling_merchant_spawn(npc, "forest_clearing"):
    spawn_traveling_merchant(npc, "forest_clearing")

# Rotate inventory - picks random items from pool
new_inventory = rotate_merchant_inventory(npc)
# Returns: {"healing_potion": 2, "torch": 4, "dagger": 1}

# Spawn at location - sets location_id, rotates inventory, resets counters
success = spawn_traveling_merchant(npc, "forest_clearing")
# Returns: True if spawned, False if not is_traveling

# Despawn - clears location_id
success = despawn_traveling_merchant(npc)
# Returns: True if despawned, False if not is_traveling

# Update visit counter (called on every location change)
update_traveling_merchant_visits(npc)
# Increments visits_since_spawn if is_traveling and location_id set
```

#### Game Loop Integration

The traveling merchant system is integrated into `game.py` on location changes:

```python
# In game.py, after player moves to new_location:

# 1. Update visit counters for all traveling merchants
for npc in npc_manager.npcs.values():
    if npc.is_traveling:
        update_traveling_merchant_visits(npc)

# 2. Check for new spawns (merchants not currently spawned)
for npc in npc_manager.npcs.values():
    if npc.is_traveling and not npc.location_id:
        if check_traveling_merchant_spawn(npc, new_location.id):
            spawn_traveling_merchant(npc, new_location.id)
            new_location.npcs.append(npc.id)
            print("✨ A traveling merchant catches your eye...")

# 3. Despawn merchants at other locations after cooldown
for npc in npc_manager.npcs.values():
    if npc.is_traveling and npc.location_id != new_location.id:
        if npc.visits_since_spawn >= npc.spawn_cooldown:
            old_loc = location_manager.locations.get(npc.location_id)
            despawn_traveling_merchant(npc)
            if old_loc and npc.id in old_loc.npcs:
                old_loc.npcs.remove(npc.id)
```

#### Example: Zephyr the Wanderer

The goblin_cave scenario includes a pre-configured traveling merchant:

```python
# Zephyr the Wanderer - defined in scenario.py
# 25% spawn chance
# Appears at: forest_clearing, cave_entrance, cave_tunnel, goblin_storage
# Pool of 11 items including rare enchanted_dagger and ancient_amulet
# Shows 5 random items per spawn with 15% markup

# Player can interact normally:
> shop                    # View Zephyr's wares
> buy healing potion      # Purchase items
> talk zephyr             # Get mysterious dialogue
```

#### Traveling Merchant Tests

```bash
# Run traveling merchant tests
python -m pytest tests/test_traveling_merchant.py -v

# Test categories:
# - TestTravelingMerchantDataclass (7 tests)
# - TestSpawnMechanics (8 tests)
# - TestInventoryRotation (6 tests)
# - TestSpawnDespawnLifecycle (7 tests)
# - TestVisitTracking (3 tests)
# - TestScenarioIntegration (6 tests)
# Total: 37 tests
```

---

### Party System (Phase 3.3.7)

The party system allows players to recruit NPC companions who fight alongside them in combat.

#### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PARTY SYSTEM FLOW                           │
└─────────────────────────────────────────────────────────────────┘

  ┌─────────────┐     ┌─────────────────┐     ┌───────────────┐
  │ Find NPC at │ --> │ Check Recruit   │ --> │  Add to Party │
  │   Location  │     │   Conditions    │     │   (Max 2)     │
  └─────────────┘     └─────────────────┘     └───────────────┘
         │                    │
         ▼                    ▼
  ┌─────────────┐     ┌─────────────────┐
  │ talk <npc>  │     │ Skill Check OR  │
  │   Command   │     │ Gold OR Item OR │
  └─────────────┘     │   Quest Obj     │
                      └─────────────────┘
```

#### Party Member Classes

| Class | Combat Role | Special Ability |
|-------|-------------|-----------------|
| FIGHTER | Tank/Damage | Shield Wall (+2 AC to party for 1 round) |
| RANGER | Ranged/Tracking | Hunter's Mark (+1d4 damage to target) |
| ROGUE | Damage/Utility | Sneak Attack (+2d6 if flanking) |
| CLERIC | Healer/Support | Healing Word (1d8+2 heal) |
| WIZARD | AoE Damage | Magic Missile (auto-hit 1d4+1) |

#### Creating a Recruitable NPC

```python
from party import PartyMember, PartyMemberClass, SpecialAbility, PARTY_ABILITIES

# Create a new recruitable companion
companion = PartyMember(
    id="my_companion",
    name="Theron",
    char_class=PartyMemberClass.CLERIC,
    description="A traveling priest seeking to help those in need.",
    portrait="✝️",
    level=2,
    max_hp=16,
    armor_class=15,
    attack_bonus=3,
    damage_dice="1d8+1",
    dex_modifier=1,
    recruitment_location="temple_ruins",  # Where they can be found
    recruitment_conditions=["skill:charisma:12", "gold:10"],  # OR logic
    recruitment_dialogue={
        "greeting": "The light guides us both to this place.",
        "motivation": "These lands need healing. Perhaps together...",
        "recruit_success": "I will join your cause. May we bring hope.",
        "recruit_fail": "I sense your spirit is not yet ready."
    }
)
```

#### Recruitment Conditions

Conditions use OR logic - meeting ANY one condition allows recruitment:

| Format | Example | Description |
|--------|---------|-------------|
| `skill:<name>:<dc>` | `skill:charisma:14` | Pass skill check |
| `gold:<amount>` | `gold:25` | Pay gold fee |
| `item:<item_id>` | `item:sacred_symbol` | Have item in inventory |
| `objective:<obj_id>` | `objective:cleared_camp` | Quest objective complete |

#### Party Commands

| Command | Description |
|---------|-------------|
| `party` | Show current party roster with HP/status |
| `recruit <name>` | Attempt to recruit NPC at current location |
| `dismiss <name>` | Remove companion from party |

#### Combat Integration

Party members fight automatically during combat:

1. **Initiative**: Party members roll initiative and join turn order
2. **AI Actions**: Simple AI selects targets (weakest enemy)
3. **Flanking**: +2 attack when attacking same target as player
4. **Abilities**: Uses special ability when appropriate
5. **Targeting**: Enemies have 30% chance to attack party members

#### Party Save/Load

Party state is persisted in save files:

```python
# Included in save_game()
save_data['party'] = party.to_dict()

# Restored in load_game()
party = Party.from_dict(save_data.get('party'))
```

#### Testing

Party system tests (`tests/test_party.py`):
- TestPartyMemberCreation (3 tests)
- TestPartyMemberCombat (8 tests)
- TestPartyMemberAbilities (5 tests)
- TestPartyMemberStatus (5 tests)
- TestPartyMemberSerialization (3 tests)
- TestPartyManagement (13 tests)
- TestPartyDisplay (2 tests)
- TestPartySerialization (3 tests)
- TestRecruitmentConditionParsing (6 tests)
- TestRecruitmentConditionChecks (5 tests)
- TestRecruitmentPayment (4 tests)
- TestCanAttemptRecruitment (2 tests)
- TestPredefinedNPCs (6 tests)
- TestSpecialAbilities (5 tests)
- **Total: 72 tests**

---

### Quest System (Phase 3.3.4)

The quest system provides full quest tracking, objective management, and reward distribution.

#### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     QUEST SYSTEM FLOW                           │
└─────────────────────────────────────────────────────────────────┘

  Available Quests          Active Quests           Completed
  ┌─────────────┐          ┌─────────────┐        ┌─────────────┐
  │ rescue_lily │ ──accept──▶│ rescue_lily │ ─turn─in─▶│ rescue_lily │
  │ clear_path  │          │ Objectives:  │        │ Rewards:    │
  │ heirlooms   │          │ [✓] reach   │        │ +100 XP     │
  └─────────────┘          │ [ ] find    │        │ +50 gold    │
        │                  │ [ ] return  │        └─────────────┘
        │                  └─────────────┘
        ▼
   NPC Talk → Show Quest Options → Player Chooses

  Objective Hooks:
  ┌────────────────┐     ┌────────────────┐     ┌────────────────┐
  │ on_enemy_killed│     │ on_item_found  │     │ on_location_   │
  │ ("goblin")     │     │ ("silver_      │     │ entered        │
  └───────┬────────┘     │  locket")      │     │ ("cave")       │
          │              └───────┬────────┘     └───────┬────────┘
          ▼                      ▼                      ▼
  ┌──────────────────────────────────────────────────────────────┐
  │              QuestManager.check_all_objectives()             │
  │                  Updates progress on active quests           │
  └──────────────────────────────────────────────────────────────┘
```

#### Quest Components

```python
from quest import (
    Quest, QuestObjective, QuestManager, QuestStatus, ObjectiveType,
    create_kill_objective, create_find_objective, create_talk_objective,
    create_location_objective, create_collect_objective
)

# Create objectives using factory helpers
obj1 = create_kill_objective("kill_goblins", "Defeat 5 goblins", "goblin", count=5)
obj2 = create_find_objective("find_locket", "Find the silver locket", "silver_locket")
obj3 = create_location_objective("reach_cave", "Enter Darkhollow Cave", "cave_entrance")
obj4 = create_talk_objective("talk_lily", "Rescue Lily", "lily")

# Create quest
quest = Quest(
    id="rescue_lily",
    name="Rescue Lily",
    description="Save the farmer's daughter from the goblins.",
    giver_npc_id="bram",
    objectives=[obj1, obj3, obj4],
    rewards={"xp": 100, "gold": 50, "items": ["healing_potion"]},
    prerequisites=[]  # No prerequisites
)
```

#### Using QuestManager

```python
# Create and populate manager
quest_manager = QuestManager()
quest_manager.register_quest(quest)  # Add to available_quests

# Accept a quest (moves from available to active)
quest_manager.accept_quest("rescue_lily")

# Track progress via hooks (called from game loop)
quest_manager.on_enemy_killed("goblin")      # Updates kill objectives
quest_manager.on_item_found("silver_locket") # Updates find objectives
quest_manager.on_location_entered("cave")    # Updates location objectives
quest_manager.on_npc_talk("lily")            # Updates talk objectives

# Check progress
progress = quest_manager.get_quest_progress("rescue_lily")  # Returns 0-100%

# Check if ready to turn in
ready_quests = quest_manager.get_ready_to_complete()

# Complete quest (returns rewards dict)
rewards = quest_manager.complete_quest("rescue_lily")
if rewards:
    character.gain_xp(rewards.get("xp", 0))
    character.gold += rewards.get("gold", 0)
```

#### Quest Commands

| Command | Description | Example |
|---------|-------------|---------|
| `quests` / `journal` | View quest log | `quests` |
| `quest <name>` | View quest details | `quest rescue lily` |

#### NPC Quest Integration

Quests are accepted/turned-in through NPC dialogue:

```python
# When talking to an NPC who gives quests:
available = quest_manager.get_available_quests_for_npc(npc.id)
ready_to_complete = [q for q in quest_manager.get_ready_to_complete() 
                     if q.giver_npc_id == npc.id]

# Show options to player:
# [1] ✅ Turn in: Rescue Lily
# [2] 📋 Accept: Clear the Path
# [0] Continue conversation
```

#### Starter Quests (Goblin Cave)

| Quest | Type | Giver | Objectives | Rewards |
|-------|------|-------|------------|---------|
| Rescue Lily | Main | Bram | Reach cave, find Lily, return | 100 XP, 50g, potion |
| Recover Heirlooms | Side | Bram | Find locket, find ring | 50 XP, 25g |
| Clear the Path | Side | Barkeep | Kill 2 wolves, 6 goblins | 75 XP, 30g |
| The Chief's Treasure | Side | Barkeep | Defeat chief, find treasure | 100 XP, 100g |

#### Quest Tests

```bash
# Run quest tests
python -m pytest tests/test_quest.py -v

# Test categories:
# - TestQuestObjective (10 tests)
# - TestObjectiveHelpers (5 tests)
# - TestQuest (17 tests)
# - TestQuestManager (22 tests)
# - TestQuestIntegration (3 tests)
# Total: 57 tests
```

---

### Quest Creation Guide

Step-by-step guide to creating new quests for your scenarios.

#### Quick Start: Creating a Quest

```python
from quest import (
    Quest, QuestType, QuestManager,
    create_kill_objective, create_find_objective, 
    create_talk_objective, create_location_objective
)

# 1. Create objectives first
objectives = [
    create_location_objective("reach_dungeon", "Enter the Ancient Dungeon", "dungeon_entrance"),
    create_kill_objective("slay_dragon", "Defeat the Dragon", "dragon", count=1),
    create_find_objective("get_artifact", "Retrieve the Sacred Artifact", "sacred_artifact"),
    create_location_objective("return_home", "Return to the Village", "village_square")
]

# 2. Create the quest
dragon_quest = Quest(
    id="slay_the_dragon",
    name="Slay the Dragon",
    description="A fearsome dragon threatens the village. Enter its lair, defeat it, and bring back the Sacred Artifact.",
    giver_npc_id="village_elder",
    quest_type=QuestType.MAIN,
    objectives=objectives,
    rewards={
        "xp": 200,
        "gold": 100,
        "items": ["dragon_scale_armor"]
    }
)

# 3. Register with quest manager
quest_manager.register_quest(dragon_quest)
```

#### Objective Types Reference

| Type | Factory Function | Target | Use Case |
|------|------------------|--------|----------|
| KILL | `create_kill_objective()` | enemy_id | "Defeat 5 goblins" |
| FIND_ITEM | `create_find_objective()` | item_id | "Find the silver locket" |
| TALK_TO | `create_talk_objective()` | npc_id | "Speak with the wizard" |
| REACH_LOCATION | `create_location_objective()` | location_id | "Enter the cave" |
| COLLECT | `create_collect_objective()` | item_id | "Gather 10 herbs" |

#### Objective Factory Functions

```python
# Kill objective - defeat enemies
obj = create_kill_objective(
    obj_id="kill_wolves",           # Unique ID
    description="Slay the wolves",  # Display text
    enemy_id="wolf",                # Enemy type to count
    count=3,                        # Number required (default 1)
    optional=False,                 # Required for completion?
    hidden=False                    # Show in quest log?
)

# Find objective - pick up specific item
obj = create_find_objective(
    obj_id="find_key",
    description="Find the dungeon key",
    item_id="dungeon_key",
    optional=False
)

# Talk objective - speak with NPC
obj = create_talk_objective(
    obj_id="meet_wizard",
    description="Consult with the wizard",
    npc_id="wizard_aldric"
)

# Location objective - reach a place
obj = create_location_objective(
    obj_id="reach_tower",
    description="Reach the Wizard's Tower",
    location_id="wizard_tower"
)

# Collect objective - gather multiple items
obj = create_collect_objective(
    obj_id="gather_herbs",
    description="Collect healing herbs",
    item_id="healing_herb",
    count=5
)
```

#### Quest Types and Disposition Rewards

| Quest Type | Disposition Bonus | Use Case |
|------------|-------------------|----------|
| `QuestType.MAIN` | +25 | Main story quests |
| `QuestType.SIDE` | +15 | Optional story content |
| `QuestType.MINOR` | +10 | Fetch quests, simple tasks |

The disposition bonus is given to the `giver_npc_id` when the quest is completed.

#### Quest Rewards

```python
rewards={
    "xp": 100,                          # Experience points
    "gold": 50,                         # Gold coins
    "items": ["healing_potion", "sword_of_valor"],  # Item IDs to give
    "reputation": {"guild": 10}         # Custom rewards (handle in game.py)
}
```

#### Quest Prerequisites

Require other quests to be completed first:

```python
secret_quest = Quest(
    id="hidden_treasure",
    name="The Hidden Treasure",
    description="Now that you've proven yourself...",
    prerequisites=["rescue_lily", "clear_the_path"],  # Both must be complete
    ...
)
```

#### Optional and Hidden Objectives

```python
quest = Quest(
    id="explore_dungeon",
    name="Explore the Dungeon",
    objectives=[
        # Required objectives
        create_location_objective("enter", "Enter the dungeon", "dungeon"),
        create_location_objective("exit", "Find the exit", "dungeon_exit"),
        
        # Optional bonus objective
        create_find_objective(
            "bonus_treasure",
            "Find the hidden treasure (optional)",
            "hidden_chest",
            optional=True  # Not required for completion
        ),
        
        # Hidden objective (revealed later)
        create_kill_objective(
            "secret_boss",
            "Defeat the Shadow Guardian",
            "shadow_guardian",
            hidden=True  # Doesn't show until discovered
        )
    ]
)
```

#### Adding Quests to a Scenario

Create a quest setup function in your scenario file:

```python
# In src/scenario.py or scenarios/your_campaign/quests.py

def create_your_scenario_quests(quest_manager: QuestManager) -> None:
    """Register all quests for your scenario."""
    
    # Main quest
    main_quest = Quest(
        id="main_story",
        name="The Main Quest",
        giver_npc_id="quest_giver",
        quest_type=QuestType.MAIN,
        objectives=[...],
        rewards={"xp": 200, "gold": 100}
    )
    quest_manager.register_quest(main_quest)
    
    # Side quests
    side_quest = Quest(
        id="side_mission",
        name="A Side Adventure",
        giver_npc_id="innkeeper",
        quest_type=QuestType.SIDE,
        objectives=[...],
        rewards={"xp": 50, "gold": 25}
    )
    quest_manager.register_quest(side_quest)
```

Then call it during scenario creation:

```python
def create_your_scenario():
    scenario = Scenario(...)
    quest_manager = QuestManager()
    
    create_your_scenario_quests(quest_manager)
    
    scenario.quest_manager = quest_manager
    return scenario
```

#### Quest Hooks in game.py

The game loop automatically calls quest hooks:

```python
# When player kills an enemy
quest_manager.on_enemy_killed(enemy.id)  # Updates KILL objectives

# When player picks up an item
quest_manager.on_item_found(item_id)     # Updates FIND_ITEM objectives

# When player enters a location
quest_manager.on_location_entered(location_id)  # Updates REACH_LOCATION objectives

# When player talks to an NPC
quest_manager.on_npc_talk(npc_id)        # Updates TALK_TO objectives
```

#### Testing Your Quests

```python
# In tests/test_your_quests.py
import pytest
from quest import Quest, QuestManager, QuestType, create_kill_objective

class TestYourQuests:
    def test_quest_creation(self):
        """Quest can be created with valid data."""
        quest = Quest(
            id="test_quest",
            name="Test Quest",
            description="A test quest",
            objectives=[create_kill_objective("kill", "Kill stuff", "goblin")]
        )
        assert quest.id == "test_quest"
        assert quest.status.name == "NOT_STARTED"
    
    def test_quest_completion(self):
        """Quest completes when all objectives done."""
        manager = QuestManager()
        quest = Quest(
            id="kill_quest",
            name="Kill Goblins",
            description="Kill 2 goblins",
            objectives=[create_kill_objective("kill", "Kill goblins", "goblin", count=2)]
        )
        manager.register_quest(quest)
        manager.accept_quest("kill_quest")
        
        # Kill 2 goblins
        manager.on_enemy_killed("goblin")
        manager.on_enemy_killed("goblin")
        
        # Should be ready to complete
        ready = manager.get_ready_to_complete()
        assert len(ready) == 1
        assert ready[0].id == "kill_quest"
```

#### Quest Checklist

Before adding a quest, verify:

- [ ] Quest has unique `id` (snake_case)
- [ ] Quest has display `name` 
- [ ] Quest has meaningful `description`
- [ ] `giver_npc_id` matches an NPC in your scenario
- [ ] All objective `target` values match existing entities:
  - Kill targets match enemy types in combat.py
  - Find targets match item keys in scenario
  - Talk targets match NPC IDs
  - Location targets match location IDs
- [ ] `rewards` contains valid item keys if giving items
- [ ] `prerequisites` list valid quest IDs if used
- [ ] Quest is registered with `quest_manager.register_quest()`

---

### Scenario Runtime API

How to interact with scenarios programmatically.

#### Starting a Scenario

```python
from scenario import create_scenario_manager

# Create manager with all available scenarios
manager = create_scenario_manager()

# List available scenarios
scenarios = manager.list_available()
# Returns: [{"id": "goblin_cave", "name": "The Goblin Cave", ...}, ...]

# Start a scenario
first_scene = manager.start_scenario("goblin_cave")
print(first_scene.name)  # "The Rusty Dragon Tavern"
```

#### During Gameplay

```python
# Get current active scenario
scenario = manager.active_scenario

# Get current scene
scene = scenario.get_current_scene()

# Record player action
scenario.record_exchange()

# Complete an objective (returns XP)
success, xp = scenario.complete_objective("meet_bram")
if success and xp > 0:
    character.gain_xp(xp, "Objective complete")

# Get DM context (for AI prompts)
dm_context = manager.get_dm_context()
# Includes scene instructions, location, available actions

# Check if scene can transition
if scenario.can_transition():
    # Player met min_exchanges and completed all objectives
    next_scene = scenario.transition_to_next()
    if next_scene is None:
        print("Scenario complete!")
```

#### Movement API

```python
# Get location manager from active scenario
loc_manager = manager.active_scenario.location_manager

# Attempt to move
success, new_location, message, events = loc_manager.move("north")

if success:
    print(f"Moved to {new_location.name}")
    # Process any triggered events
    for event in events:
        print(f"Event: {event.narration}")
        if event.effect:
            process_effect(event.effect)
else:
    print(f"Can't go that way: {message}")
```

#### Automatic Transition Detection

```python
# check_transition() analyzes player/DM text for scene transitions
result = manager.check_transition(player_input, dm_response)
# Returns: "transition" | "needs_progress" | None

if result == "transition":
    next_scene = manager.active_scenario.transition_to_next()
    # Announce new scene to player
```

---

### Save/Load Integration

Scenarios preserve full state across game saves.

#### What Gets Saved

| Component | Saved Data |
|-----------|------------|
| **Scenario** | current_scene_id, is_complete |
| **Scenes** | status, exchange_count, objectives_complete |
| **Locations** | visited, events_triggered, items (after pickup), encounter_triggered |
| **LocationManager** | current_location_id, available_location_ids |

#### Saving Scenario State

```python
from save_system import SaveManager

# Save includes scenario automatically
save_manager.save_game(
    filename="slot1",
    character=character,
    game_state=game_state,
    scenario_manager=manager  # Scenario state included
)
```

#### Loading Scenario State

```python
# Load restores scenario completely
result = save_manager.load_game("slot1", Character, ScenarioManager)

character = result['character']
game_state = result['game_state']
manager = result['scenario_manager']

# Player returns to exact scenario position
current_scene = manager.active_scenario.get_current_scene()
current_location = manager.active_scenario.location_manager.get_current_location()
```

---

### Advanced Scenario Patterns

#### Branching Paths

Create scenarios with player choice affecting story:

```python
# Two possible scenes based on player choice
scenes = {
    "decision_point": Scene(
        id="decision_point",
        dm_instructions="""
Player must choose:
- Help the merchant → complete "help_merchant" objective
- Help the thief → complete "help_thief" objective
Only one can be chosen.
""",
        objectives=["make_choice"],  # Umbrella objective
        next_scene_id=None,  # Set dynamically
    ),
    "merchant_path": Scene(...),
    "thief_path": Scene(...),
}

# In game.py, when objective complete:
if "help_merchant" in scene.objectives_complete:
    scenario.scenes["decision_point"].next_scene_id = "merchant_path"
elif "help_thief" in scene.objectives_complete:
    scenario.scenes["decision_point"].next_scene_id = "thief_path"
```

#### Optional Objectives

Objectives that give bonuses but aren't required:

```python
Scene(
    objectives=["main_objective"],  # Required
    objective_xp={
        "main_objective": 50,
        "optional_explore": 25,  # Bonus XP
        "optional_stealth": 25,  # Bonus XP
    },
    dm_instructions="""
Main objective: Defeat the boss
Optional: 
- Explore all rooms before boss (+25 XP)
- Defeat boss without alerting guards (+25 XP)
""",
)
```

#### Hidden/Secret Areas

Locations revealed by player actions:

```python
# Location initially NOT in scene's location_ids
"secret_vault": Location(
    id="secret_vault",
    name="Hidden Vault",
    description="A secret treasure room!",
    exits={"back": "library"},
    items=["legendary_sword", "gold_pile"],
)

# Event that reveals the location
LocationEvent(
    id="find_secret",
    trigger=EventTrigger.ON_LOOK,
    narration="You find a hidden switch!",
    effect="add_exit:library:secret_vault",  # Adds exit dynamically
    condition="skill:investigation:15",
    one_time=True
)

# In game code, when effect processed:
if effect.startswith("add_exit:"):
    _, source, dest = effect.split(":")
    location = loc_manager.locations[source]
    location.exits["secret passage"] = dest
    # Also add to available_location_ids
    loc_manager.available_location_ids.append(dest)
```

#### Multi-Visit Locations

Locations that change on return visits:

```python
"camp_before": Location(
    id="camp_before",
    name="Goblin Camp",
    description="Four goblins guard the camp.",
    npcs=["goblins"],
    encounter=["goblin", "goblin", "goblin", "goblin"],
)

# After combat, the encounter_triggered flag is set
# DM context will show "✓ Encounter already completed"
# Update location description for subsequent visits:
if location.encounter_triggered:
    # In dm_context, include this information
    context += "\nThe camp is now empty of goblins."
```

---

#### Player Commands (game.py)

| Command | Aliases | Description |
|---------|---------|-------------|
| `look` | `look around`, `where am i` | Describe current location, items, NPCs |
| `exits` | `directions`, `where can i go` | Show available exits |
| `go <direction>` | `move`, `walk`, `head`, `enter` | Move to new location |
| `n/s/e/w` | `north`, `south`, `east`, `west` | Cardinal direction shortcuts |
| `take <item>` | `pick up`, `grab` | Pick up item from location |
| `talk <npc>` | `speak`, `talk to` | Initiate dialogue with NPC |
| `talk <npc> about <topic>` | `speak to ... about` | Ask NPC about specific topic |

#### Adding Items to Locations

Items in locations must exist in the ITEMS database (inventory.py):

```python
# 1. Ensure item exists in inventory.py ITEMS dict
"torch": Item(
    name="Torch",
    item_type=ItemType.MISC,
    description="Provides light in dark places.",
    value=1
)

# 2. Add item key to location in scenario.py
"tavern_main": Location(
    id="tavern_main",
    items=["torch", "rope"],  # Must match ITEMS keys
    ...
)
```

**Special: Gold Pouches**
Items with "gold_pouch" in the name or "gold pieces" in the effect are automatically converted to character gold:

```python
"gold_pouch": Item(
    name="Gold Pouch",
    value=50,  # Adds 50 gold to character.gold
    effect="Contains 50 gold pieces"
)
```

#### Defining New Locations

```python
"new_location": Location(
    id="new_location",           # Unique ID (snake_case)
    name="Display Name",         # Shown to player
    description="Long description for AI context and look command.",
    exits={"door": "other_loc", "path": "another_loc"},
    npcs=["npc_id"],             # Match NPCs defined elsewhere
    items=["item_key"],          # Match ITEMS database keys
    atmosphere="Mood/sensory details for AI",
    enter_text="Text shown when player first enters.",
    events=[...]                 # Optional: LocationEvent list
)
```

#### Location Event System (Phase 3.2.1)

Events trigger dynamically when players interact with locations.

**EventTrigger Enum:**
- `ON_ENTER` - Triggers every time player enters
- `ON_FIRST_VISIT` - Only triggers on first visit
- `ON_LOOK` - Triggers on look command
- `ON_ITEM_TAKE` - Triggers when picking up items

**Creating Events:**

```python
from scenario import LocationEvent, EventTrigger

event = LocationEvent(
    id="cave_trap",                  # Unique event ID
    trigger=EventTrigger.ON_FIRST_VISIT,
    narration="A tripwire! You barely spot it before stepping on it.",
    effect="skill_check:dex:12|damage:1d4",  # Optional mechanical effect
    condition=None,                  # Optional: condition to trigger
    one_time=True                    # False = repeatable event
)
```

**Using Events in Locations:**

```python
cave = Location(
    id="cave",
    name="Goblin Cave",
    events=[
        LocationEvent(
            id="cave_discovery",
            trigger=EventTrigger.ON_FIRST_VISIT,
            narration="Among the bones, you notice a glint of gold.",
            one_time=True
        )
    ]
)
```

**Event Methods:**

```python
location.add_event(event)              # Add event dynamically
location.has_event("event_id")         # Check if event exists
location.is_event_triggered("event_id") # Check if already triggered
location.trigger_event("event_id")     # Mark event as triggered
location.get_events_for_trigger(       # Get applicable events
    trigger=EventTrigger.ON_FIRST_VISIT,
    is_first_visit=True
)
```

**Movement Returns Events:**

```python
success, new_location, message, events = manager.move("north")

if events:
    for event in events:
        print(f"Event: {event.narration}")
        if event.effect:
            # Parse and apply effect
            pass
```

**Event Effects (Planned):**
- `skill_check:ability:dc` - Require skill check
- `damage:dice` - Apply damage on failure
- `add_item:item_id` - Give item to player
- `start_combat:enemy_id` - Begin combat
- `objective:objective_id` - Mark objective complete

#### Test Coverage

Location tests are in `tests/test_location.py` (80 tests):
- `TestLocationBasics` - Dataclass creation
- `TestLocationExitsDisplay` - Exit formatting
- `TestLocationSerialization` - Save/load
- `TestLocationItemsAndNPCs` - Item/NPC methods (Phase 3.2.1)
- `TestLocationEventBasics` - Event creation, serialization
- `TestLocationEventMethods` - add/has/trigger/get events
- `TestLocationManagerBasics` - Manager initialization
- `TestLocationManagerSetters` - Set methods
- `TestLocationManagerGetters` - Get methods, exit filtering
- `TestLocationManagerMovement` - move() with all edge cases
- `TestLocationManagerEvents` - move() returning events
- `TestLocationManagerContext` - DM context generation
- `TestLocationManagerSerialization` - Manager save/load

---

### Scene and Scenario System

The Scenario system structures the game's story into manageable chapters.

#### Scenario Folder Architecture (Planned Phase 5.2)

Scenarios are organized in a modular folder structure supporting multi-chapter campaigns:

```
src/
├── scenario.py                  # Base classes (Scene, Location, Scenario, etc.)
│
├── scenarios/                   # All campaigns live here
│   ├── __init__.py              # Scenario registry & loader
│   │
│   ├── goblin_menace/           # Campaign 1: "The Goblin Menace"
│   │   ├── __init__.py          # Campaign registration & metadata
│   │   ├── chapter_1.py         # "The Goblin Cave" (current scenario)
│   │   ├── chapter_2.py         # "Return to the Village"
│   │   └── chapter_3.py         # "The Goblin King"
│   │
│   └── haunted_manor/           # Campaign 2: "The Haunted Manor"
│       ├── __init__.py          # Campaign registration
│       ├── chapter_1.py         # "Arrival at the Manor"
│       └── chapter_2.py         # "The Crypt Below"
```

**Key Concepts:**
- **Campaign**: A multi-chapter adventure (folder with `__init__.py`)
- **Chapter**: A single scenario/episode (one `.py` file)
- **Registry**: Central `__init__.py` that auto-discovers campaigns

**Campaign `__init__.py` Example:**
```python
# scenarios/goblin_menace/__init__.py
from .chapter_1 import create_goblin_cave_scenario
from .chapter_2 import create_village_return_scenario

CAMPAIGN_INFO = {
    "id": "goblin_menace",
    "name": "The Goblin Menace",
    "description": "Protect the village from a growing goblin threat.",
    "chapters": [
        {"id": "chapter_1", "name": "The Goblin Cave", "factory": create_goblin_cave_scenario},
        {"id": "chapter_2", "name": "Return to the Village", "factory": create_village_return_scenario},
    ]
}
```

**Benefits of Pure Python:**
- Full procedural generation (random loot, scaling difficulty)
- IDE autocomplete and type checking
- Chapters can share NPCs, items, and state
- Complex conditionals and custom logic
- No external tooling required

#### Hierarchy Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      ScenarioManager                            │
│   - Loads and tracks available scenarios                        │
│   - Manages active scenario                                     │
│   - Provides DM context                                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                       Scenario                                  │
│   - The full adventure ("The Goblin Cave")                      │
│   - Contains multiple Scenes in order                           │
│   - Tracks overall progress                                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                        Scene                                    │
│   - A story chapter ("The Rusty Dragon Tavern")                 │
│   - Has DM instructions, mood, objectives                       │
│   - References multiple Locations                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                       Location                                  │
│   - Physical places ("tavern_main", "tavern_bar")               │
│   - Items, NPCs, exits, events, encounters                      │
└─────────────────────────────────────────────────────────────────┘
```

#### Scene Dataclass (scenario.py)

```python
@dataclass
class Scene:
    id: str                  # Unique ID: "tavern", "goblin_camp"
    name: str                # Display name: "The Rusty Dragon Tavern"
    description: str         # What this scene is about
    
    # AI Guidance
    setting: str             # Physical setting description
    mood: str                # "tense", "mysterious", "lighthearted"
    dm_instructions: str     # Detailed guidance for AI DM
    
    # Pacing & Progression
    min_exchanges: int       # Minimum player actions before transition allowed
    objectives: List[str]    # Goals to complete: ["meet_bram", "accept_quest"]
    objectives_complete: List[str]  # Runtime: completed objectives
    transition_hint: str     # When to move to next scene
    next_scene_id: str       # ID of the next scene (None if final)
    
    # Location System
    location_ids: List[str]  # Locations accessible in this scene
    starting_location_id: str  # Where player starts in this scene
    
    # Runtime State
    exchanges: int           # Player actions taken in this scene
    status: SceneStatus      # LOCKED, ACTIVE, COMPLETED
```

#### Scenario Dataclass (scenario.py)

```python
@dataclass
class Scenario:
    id: str                  # "goblin_cave"
    name: str                # "The Goblin Cave"
    description: str         # Player-facing description for selection
    difficulty: str          # "easy", "medium", "hard"
    estimated_time: str      # "30-60 minutes"
    
    # Structure
    scenes: Dict[str, Scene]    # All scenes by ID
    scene_order: List[str]      # Scene progression order
    
    # Location Management
    location_manager: LocationManager  # Handles player movement
    
    # Runtime State
    current_scene_id: str
    is_complete: bool
```

#### The Goblin Cave Scenario

The starter scenario demonstrates the full system:

```
SCENE FLOW:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   tavern    │ →  │   journey   │ →  │cave_entrance│
│ (Meet Bram) │    │(Forest path)│    │(Enter cave) │
└─────────────┘    └─────────────┘    └─────────────┘
                                             ↓
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ resolution  │ ←  │boss_chamber │ ←  │ goblin_camp │
│(Hero return)│    │(Fight chief)│    │(4 goblins)  │
└─────────────┘    └─────────────┘    └─────────────┘
```

**Locations per Scene:**

| Scene | Locations |
|-------|-----------|
| `tavern` | `tavern_main`, `tavern_bar`, `village_square` |
| `journey` | `forest_path`, `forest_clearing`, `darkhollow_approach` |
| `cave_entrance` | `cave_entrance`, `cave_tunnel` |
| `goblin_camp` | `goblin_camp_entrance`, `goblin_camp_main`, `goblin_camp_shadows`, `goblin_camp_cages` |
| `boss_chamber` | `chief_tunnel`, `boss_chamber` |
| `resolution` | `cave_exit`, `return_path`, `village_return`, `tavern_celebration` |

**Fixed Encounters:**

| Location | Encounter | Difficulty |
|----------|-----------|------------|
| `goblin_camp_main` | 4 goblins | Medium |
| `boss_chamber` | 1 goblin_boss + 2 goblins | Hard |

#### Creating a New Scenario

```python
def create_new_scenario() -> Scenario:
    # 1. Define locations
    locations = {
        "location_id": Location(...),
        ...
    }
    
    # 2. Define scenes
    scenes = {
        "scene_id": Scene(
            id="scene_id",
            name="Scene Name",
            dm_instructions="...",
            location_ids=["loc1", "loc2"],
            starting_location_id="loc1",
            next_scene_id="next_scene",
            ...
        ),
        ...
    }
    
    # 3. Create location manager and add all locations
    location_manager = LocationManager()
    for loc in locations.values():
        location_manager.add_location(loc)
    
    # 4. Create scenario
    scenario = Scenario(
        id="new_scenario",
        name="My New Adventure",
        scenes=scenes,
        scene_order=["scene1", "scene2", "scene3"],
        location_manager=location_manager,
        ...
    )
    
    return scenario
```

---

### Creating a Scenario: Step-by-Step Walkthrough

This walkthrough guides you through creating a complete scenario from scratch.

> 📄 **Template Available**: Copy `docs/SCENARIO_TEMPLATE.py` to `src/` as your starting point.

#### Step 1: Plan Your Scenario

Before coding, outline:

1. **Story premise**: What's the adventure about?
2. **Scenes** (chapters): 3-6 story beats
3. **Locations**: Physical places per scene
4. **Combat encounters**: Where and how many enemies
5. **Objectives**: What must players accomplish?

**Example Planning:**
```
Scenario: "The Haunted Manor"
- Scene 1: Village (get quest, gather info)
- Scene 2: Manor exterior (explore, find entry)  
- Scene 3: Manor interior (combat, puzzles)
- Scene 4: Crypt (boss fight)
- Scene 5: Resolution (return, reward)
```

#### Step 2: Define Locations

Create all locations with proper connections:

```python
locations = {
    "village_square": Location(
        id="village_square",
        name="Willowbrook Village Square",
        description="A quaint village square with a well in the center. Worried villagers whisper about the haunted manor on the hill.",
        exits={
            "north": "manor_gates",
            "inn": "village_inn",
            "path": "manor_gates"  # Multiple names for same exit
        },
        npcs=["elder_martha"],
        items=["torch", "holy_water"],
        atmosphere="Nervous energy, hushed whispers, people avoiding eye contact",
        enter_text="You arrive in Willowbrook. The villagers eye you with a mix of fear and hope.",
        events=[
            LocationEvent(
                id="elder_approaches",
                trigger=EventTrigger.ON_FIRST_VISIT,
                narration="An elderly woman rushes toward you. 'A stranger! Please, we need help!'",
                effect=None,
                one_time=True
            )
        ]
    ),
    
    "manor_entrance": Location(
        id="manor_entrance",
        name="Haunted Manor - Grand Foyer",
        description="A dusty entrance hall with cobwebs everywhere. Portraits watch you with unsettling eyes.",
        exits={"outside": "manor_gates", "upstairs": "upper_hall", "basement": "crypt_stairs"},
        npcs=[],
        items=["rusty_key", "candle"],
        atmosphere="Creaking floorboards, cold drafts, distant moaning",
        enter_text="The door creaks open. Dust motes dance in pale moonlight.",
        
        # Combat encounter - exactly 2 skeletons guard the foyer
        encounter=["skeleton", "skeleton"],
        
        events=[
            LocationEvent(
                id="door_slams",
                trigger=EventTrigger.ON_FIRST_VISIT,
                narration="The front door slams shut behind you! You hear the lock click.",
                effect=None,
                one_time=True
            )
        ]
    ),
}
```

**Key Location Fields:**

| Field | Purpose | Example |
|-------|---------|---------|
| `id` | Unique identifier | `"manor_entrance"` |
| `name` | Display name | `"Haunted Manor - Grand Foyer"` |
| `description` | AI DM context | Full scene description |
| `exits` | Navigation | `{"door": "next_room"}` |
| `npcs` | Characters present | `["ghost_lord"]` |
| `items` | Lootable items | `["healing_potion"]` |
| `atmosphere` | Mood/sensory | `"Cold, eerie, dark"` |
| `encounter` | Fixed combat | `["skeleton", "skeleton"]` |
| `events` | Triggered events | See below |

#### Step 3: Create Events

Events add dynamic content to locations:

```python
# Trap event (deals damage)
LocationEvent(
    id="poison_dart_trap",
    trigger=EventTrigger.ON_ENTER,
    narration="Click! A dart shoots from the wall!",
    effect="damage:1d4",
    condition="!has_item:trap_disarm_kit",  # Only if player lacks item
    one_time=True
)

# Discovery event (atmospheric)
LocationEvent(
    id="ghostly_whispers",
    trigger=EventTrigger.ON_FIRST_VISIT,
    narration="Whispers echo from nowhere: 'Turn back... turn back...'",
    effect=None,
    one_time=True
)

# Objective event (story progress)
LocationEvent(
    id="find_diary",
    trigger=EventTrigger.ON_LOOK,
    narration="You find a diary hidden under the pillow!",
    effect="objective:discover_secret",
    one_time=True
)
```

**Event Triggers:**
| Trigger | When It Fires |
|---------|---------------|
| `ON_ENTER` | Every time player enters |
| `ON_FIRST_VISIT` | Only first time |
| `ON_LOOK` | When player uses 'look' |
| `ON_ITEM_TAKE` | When taking specific item |

**Event Effects:**
| Effect Format | What It Does |
|---------------|--------------|
| `"damage:1d4"` | Deal 1d4 damage |
| `"damage:2d6+2"` | Deal 2d6+2 damage |
| `"add_item:key"` | Add item to inventory |
| `"objective:find_clue"` | Complete objective |
| `"skill_check:dex:12\|damage:1d4"` | Pass DEX DC 12 or take damage |

#### Step 4: Define Scenes

Scenes group locations and provide AI guidance:

```python
scenes = {
    "village_intro": Scene(
        id="village_intro",
        name="The Plea for Help",
        description="Players receive the quest in Willowbrook",
        
        setting="A fearful village overshadowed by a haunted manor on the hill",
        mood="anxious, desperate",
        
        # CRITICAL: Detailed AI DM instructions
        dm_instructions="""
You are the DM for a village seeking help with their haunted manor problem.

ELDER MARTHA:
- Elderly woman, speaks with urgency
- Her grandson Tommy went into the manor on a dare and never returned
- She offers the village's treasury (100 gold) as reward
- Knows the manor belonged to Lord Ravencrest who practiced dark magic
- Warns about undead and traps

INFORMATION AVAILABLE:
- Manor has been abandoned for 50 years
- Strange lights seen at night
- Those who enter never return
- A secret passage might exist in the crypt

PLAYER OBJECTIVES:
1. meet_elder - Talk to Elder Martha
2. accept_quest - Agree to investigate the manor

When player accepts the quest, describe them leaving toward the manor.

⚔️ NO COMBAT in this scene - it's roleplay only.
""",
        
        min_exchanges=3,  # At least 3 player actions
        objectives=["meet_elder", "accept_quest"],
        objective_xp={"meet_elder": 10, "accept_quest": 20},
        
        transition_hint="Player accepts the quest and heads to manor",
        next_scene_id="manor_exploration",
        
        location_ids=["village_square", "village_inn"],
        starting_location_id="village_square",
        status=SceneStatus.LOCKED,
    ),
    
    "manor_exploration": Scene(
        id="manor_exploration",
        name="Into the Darkness",
        description="Exploring the haunted manor",
        
        setting="The decrepit interior of a haunted manor",
        mood="tense, spooky, dangerous",
        
        dm_instructions="""
The player explores the haunted manor. This is where combat happens.

⚔️ FIXED ENCOUNTERS (use EXACTLY these enemies):
- manor_entrance: [COMBAT: skeleton, skeleton]
- upper_hall: [COMBAT: skeleton, skeleton, skeleton]

Do NOT change enemy counts. These are balanced for difficulty.

COMBAT XP IS AUTOMATIC - the game awards XP when enemies die.
You only describe the combat narratively.

EXPLORATION:
- Let player search rooms for clues
- The crypt key is hidden in the library
- Ghostly manifestations can appear but don't attack
- Guide player toward the crypt for the boss fight

When player finds the crypt and has the key, they can proceed to boss.
""",
        
        min_exchanges=2,
        objectives=["clear_manor", "find_crypt_key"],
        objective_xp={"clear_manor": 25, "find_crypt_key": 15},
        
        transition_hint="Player enters the crypt",
        next_scene_id="boss_fight",
        
        location_ids=["manor_entrance", "upper_hall", "library", "crypt_stairs"],
        starting_location_id="manor_entrance",
        status=SceneStatus.LOCKED,
    ),
}
```

**Key DM Instructions Elements:**

1. **NPC personalities**: How they speak, what they know
2. **Information available**: What player can learn
3. **Objectives list**: What player must accomplish  
4. **Combat rules**: Use `[COMBAT: enemy, enemy]` format
5. **Transition trigger**: When to move to next scene

#### Step 5: Balance Combat Encounters

Use fixed encounters for fair difficulty:

```python
# Phase 3.2.2: Balanced Encounters

# Easy: 2-3 minor enemies (50-75 XP)
encounter=["skeleton", "skeleton"]  # 50 XP

# Medium: 4 minor enemies (100 XP)  
encounter=["goblin", "goblin", "goblin", "goblin"]  # 100 XP

# Hard: Boss + minions (150+ XP)
encounter=["goblin_boss", "goblin", "goblin"]  # 150 XP

# Level Progression:
# - Level 1 → Level 2: 100 XP needed
# - Level 2 → Level 3: 200 XP needed
# - Players should level up at least once per scenario
```

**Enemy Reference:**

| Enemy | HP | XP | Gold | Notes |
|-------|----|----|------|-------|
| `goblin` | 7 | 25 | 3 | Fast, low damage |
| `goblin_boss` | 21 | 100 | 20 | Drops class weapon |
| `skeleton` | 13 | 25 | 0 | Undead, no gold |
| `orc` | 15 | 50 | 10 | Hits hard |

#### Step 6: Register Your Scenario

Add your scenario to `ScenarioManager`:

```python
# In scenario.py, in create_scenario_manager():

def create_scenario_manager() -> ScenarioManager:
    manager = ScenarioManager()
    
    # Existing scenarios
    manager.register_scenario("goblin_cave", create_goblin_cave_scenario)
    
    # Your new scenario
    from my_scenario import create_haunted_manor
    manager.register_scenario("haunted_manor", create_haunted_manor)
    
    return manager
```

#### Step 7: Test Your Scenario

Run the game and test:

```bash
python src/game.py
# Select your scenario
# Test all paths, combat, objectives
```

**Testing Checklist:**
- [ ] All locations accessible
- [ ] Exits work correctly
- [ ] NPCs appear where expected
- [ ] Items can be picked up
- [ ] Events trigger properly
- [ ] Combat uses correct enemy counts
- [ ] XP awards correctly
- [ ] Objectives complete as expected
- [ ] Scene transitions work
- [ ] Scenario ends properly

---

### Example: Complete Small Scenario

Here's a minimal but complete scenario:

```python
def create_quick_dungeon() -> Scenario:
    """A quick dungeon crawl for testing."""
    
    locations = {
        "entrance": Location(
            id="entrance",
            name="Dungeon Entrance",
            description="A dark cave mouth leads into an old dungeon.",
            exits={"enter": "guard_room"},
            items=["torch"],
            atmosphere="Damp, echoing, ominous",
            enter_text="You stand before the dungeon entrance.",
        ),
        "guard_room": Location(
            id="guard_room",
            name="Guard Room",
            description="An ancient guard room. Two skeletons animate as you enter!",
            exits={"back": "entrance", "forward": "treasure_room"},
            items=["shortsword"],
            encounter=["skeleton", "skeleton"],  # Fixed: 2 skeletons
        ),
        "treasure_room": Location(
            id="treasure_room", 
            name="Treasure Chamber",
            description="A room filled with ancient gold!",
            exits={},  # No exits = end
            items=["gold_pile", "healing_potion"],
        ),
    }
    
    scenes = {
        "dungeon": Scene(
            id="dungeon",
            name="Quick Dungeon",
            description="A simple dungeon",
            setting="An old dungeon",
            mood="dangerous",
            dm_instructions="""
Simple dungeon crawl:
- Entrance: Safe, describe the ominous darkness
- Guard Room: Combat with 2 skeletons [COMBAT: skeleton, skeleton]  
- Treasure Room: Victory! Describe the treasure

COMBAT XP IS AUTOMATIC.
""",
            min_exchanges=1,
            objectives=["defeat_guards"],
            objective_xp={"defeat_guards": 50},
            next_scene_id=None,  # End after this
            location_ids=["entrance", "guard_room", "treasure_room"],
            starting_location_id="entrance",
            status=SceneStatus.LOCKED,
        ),
    }
    
    location_manager = LocationManager()
    for loc in locations.values():
        location_manager.add_location(loc)
    
    return Scenario(
        id="quick_dungeon",
        name="Quick Dungeon",
        description="A fast dungeon for testing",
        hook="Explore a quick dungeon!",
        estimated_duration="5-10 minutes",
        scenes=scenes,
        scene_order=["dungeon"],
        location_manager=location_manager,
    )
```

---

#### ScenarioManager (scenario.py)

```python
class ScenarioManager:
    scenarios: Dict[str, Callable]  # Factory functions by ID
    active_scenario: Optional[Scenario]
    
    def register(id: str, factory: Callable)  # Register a scenario
    def list_available() -> List[dict]        # Get scenario list for UI
    def start(id: str) -> bool                # Begin a scenario
    def is_active() -> bool                   # Check if scenario running
    def get_current_scene() -> Scene          # Get active scene
    def advance_scene() -> bool               # Move to next scene
    def get_dm_context() -> str               # Get context for AI DM
```

---

### Fixed Encounter System (Phase 3.2.2)

Encounters are defined on Locations to ensure balanced, predictable combat.

#### Location Encounter Fields

```python
@dataclass
class Location:
    # ... other fields ...
    
    # Fixed Encounters (Phase 3.2.2)
    encounter: List[str] = field(default_factory=list)  # Enemy types: ["goblin", "goblin", "goblin", "goblin"]
    encounter_triggered: bool = False  # Has combat occurred here?
```

#### How It Works

1. **Define encounters in Location**:
```python
Location(
    id="goblin_camp_main",
    name="Goblin Camp",
    encounter=["goblin", "goblin", "goblin", "goblin"],  # Exactly 4 goblins
    ...
)
```

2. **DM receives exact encounter info**:
```
[COMBAT: 4 enemies - goblin, goblin, goblin, goblin]
Trigger combat ONLY with the exact enemies listed above.
```

3. **After combat, mark triggered**:
```python
location.encounter_triggered = True
```

#### Predefined Encounters (Goblin Cave)

| Location | Encounter | Total XP |
|----------|-----------|----------|
| `goblin_camp_main` | 4× goblin | 100 XP |
| `boss_chamber` | 1× goblin_boss + 2× goblin | 150 XP |

---

### XP and Leveling System (Phase 3.2.2)

XP is awarded **automatically by the system** following **Mechanics First** principles.

> ⚠️ **Important:** The AI DM should NOT use `[XP:]` tags for normal gameplay. XP is awarded automatically for combat, objectives, and quests. AI XP tags are reserved only for **exceptional** roleplay (creative puzzle solutions, brilliant negotiations).

#### XP Sources (All System-Controlled)

| Source | Controller | Example |
|--------|-----------|---------|
| Combat kills | `combat.py` → `get_enemy_xp()` | goblin = 25 XP |
| Scene objectives | `scenario.py` → `objective_xp` | accept_quest = 15 XP |
| Quest completion | `quest.py` → `rewards["xp"]` | Rescue Lily = 100 XP |
| AI discretion | `dm_engine.py` (RARE) | Creative puzzle = 25 XP |

#### Enemy XP Rewards

```python
@dataclass
class Enemy:
    # ... other fields ...
    xp_reward: int = 25  # XP awarded when defeated
```

**Default XP Values:**
| Enemy Type | XP Reward |
|------------|-----------|
| `goblin` | 25 |
| `goblin_boss` | 100 |
| `skeleton` | 25 |
| `orc` | 50 |

#### Objective XP Rewards

Scenes can award XP for completing story objectives:

```python
@dataclass
class Scene:
    # ... other fields ...
    objective_xp: Dict[str, int] = field(default_factory=dict)  # {"meet_bram": 10, "accept_quest": 15}
```

**Goblin Cave Objective XP:**
| Objective | XP Reward |
|-----------|-----------|
| `meet_bram` | 10 |
| `accept_quest` | 15 |
| `find_lily` | 50 |
| `defeat_chief` | 50 |

#### XP Functions

```python
# Get XP for an enemy type
def get_enemy_xp(enemy_type: str) -> int

# After combat victory (in game.py)
for enemy_type in enemy_types:
    xp_drop = get_enemy_xp(enemy_type)
    total_xp += xp_drop

character.gain_xp(total_xp, "Combat victory")
```

---

### Fixed Loot System (Phase 3.2.2)

Loot is defined on Enemies to ensure balanced item/gold distribution.

#### Enemy Loot Fields

```python
@dataclass
class Enemy:
    # ... other fields ...
    loot: List[str] = field(default_factory=list)  # Item IDs dropped
    gold_drop: int = 0  # Gold amount dropped
```

**Default Loot Values:**
| Enemy Type | Gold | Items |
|------------|------|-------|
| `goblin` | 3 | *(none)* |
| `goblin_boss` | 20 | `healing_potion`, weapon drop |
| `skeleton` | 0 | *(none)* |
| `orc` | 10 | *(none)* |

#### Loot Functions

```python
# Get raw loot (Phase 3.2.2)
def get_enemy_loot(enemy_type: str) -> Tuple[List[str], int]:
    """Returns (loot_items, gold)"""

# Get class-appropriate loot with quality weapons
def get_enemy_loot_for_class(enemy_type: str, player_class: str) -> Tuple[List[str], int]:
    """Replaces weapon drops with class-matched weapons of random quality"""
```

---

### Class-Appropriate Weapon System (Phase 3.2.2)

Boss weapon drops match the player's class for better gameplay.

#### Class Weapon Pools

```python
CLASS_WEAPON_POOLS = {
    "Fighter": ["longsword", "greatsword", "warhammer", "greataxe"],
    "Paladin": ["longsword", "warhammer", "greatsword", "mace"],
    "Ranger": ["shortbow", "longbow", "shortsword", "light_crossbow"],
    "Barbarian": ["greataxe", "greatsword", "warhammer", "handaxe"],
    "Wizard": ["quarterstaff", "dagger"],
    "Sorcerer": ["quarterstaff", "dagger"],
    "Rogue": ["shortsword", "dagger", "rapier"],
    "Bard": ["rapier", "shortsword", "dagger"],
    "Warlock": ["quarterstaff", "dagger"],
    "Monk": ["quarterstaff", "shortsword"],
    "Cleric": ["mace", "warhammer", "quarterstaff"],
    "Druid": ["quarterstaff", "spear"],
}
```

#### Quality Tiers

Weapons drop with random quality, adding excitement while maintaining balance:

| Tier | Roll (1-100) | Bonus | Prefix | Damage Example |
|------|-------------|-------|--------|----------------|
| Common | 1-60 (60%) | +0 | *(none)* | 1d8 |
| Uncommon | 61-85 (25%) | +1 | Fine | 1d8+1 |
| Rare | 86-97 (12%) | +2 | Superior | 1d8+2 |
| Epic | 98-100 (3%) | +3 | Legendary | 1d8+3 |

#### Functions

```python
# Generate a class-appropriate weapon with random quality
def generate_class_weapon(player_class: str) -> Tuple[str, str, int]:
    """
    Returns (base_weapon_id, display_name, bonus)
    Example: ("longsword", "Fine Longsword", 1)
    """

# Get loot with class-appropriate weapons
def get_enemy_loot_for_class(enemy_type: str, player_class: str) -> Tuple[List[str], int]:
    """
    Replaces weapon drops with class-matched weapons.
    Fighter gets swords, Rogue gets daggers, Wizard gets staves, etc.
    """
```

#### Inventory Integration

Quality weapons are automatically handled by `get_item()`:

```python
# These all work automatically:
item = get_item("Fine Longsword")      # → Item with 1d8+1 damage
item = get_item("Superior Dagger")      # → Item with 1d4+2 damage
item = get_item("Legendary Greataxe")   # → Item with 1d12+3 damage
```

---

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

### Location Narration System

The location system integrates AI-generated narration to bring exploration to life. The mechanics remain deterministic while the AI DM provides immersive descriptions.

#### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PLAYER LOOKS/MOVES                          │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  MECHANICS LAYER (Deterministic)                                │
│  • Location data retrieved                                      │
│  • Items, NPCs, exits computed                                  │
│  • Events triggered (if any)                                    │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  CONTEXT BUILDER: build_location_context()                      │
│  • Gathers location name, description, atmosphere               │
│  • Lists items with friendly names                              │
│  • Lists NPCs present                                           │
│  • Includes triggered events                                    │
│  • Notes if first visit                                         │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  AI NARRATION: get_location_narration()                         │
│  • AI receives structured context                               │
│  • Generates immersive 3-5 sentence description                 │
│  • Weaves items, NPCs, events naturally into prose              │
│  • No bullet points or lists                                    │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  DISPLAY: display_location_narration()                          │
│  • Shows location name as header                                │
│  • Displays AI narrative                                        │
│  • Appends exits mechanically (for gameplay clarity)            │
└─────────────────────────────────────────────────────────────────┘
```

#### Key Functions

```python
# LOCATION_NARRATION_PROMPT - in game.py
# Specialized prompt for atmospheric, immersive location descriptions

def build_location_context(location, is_first_visit=False, events=None) -> dict:
    """Build context dict for location narration."""
    # Returns dict with: name, description, atmosphere, items_present, 
    # npcs_present, available_directions, events, enter_text

def get_location_narration(chat, context: dict) -> str:
    """Request AI narration for a location description."""
    # Sends context to AI, returns narrative prose

def display_location_narration(location_name: str, narration: str, exits: dict = None):
    """Display the AI-generated location narration."""
    # Prints formatted output with header, narration, and exits
```

#### Context Structure

```python
{
    'name': 'The Rusty Dragon',        # Location display name
    'description': 'A cozy tavern...', # Raw description for AI
    'atmosphere': 'Warm firelight...',  # Mood/sensory details
    'is_first_visit': True,            # First time here?
    'items_present': ['Torch', 'Healing Potion'],  # Friendly names
    'npcs_present': ['Barkeep', 'Bram'],           # Friendly names
    'available_directions': ['door', 'bar'],        # Exit options
    'events': ['You notice rustling in the shadows...'],  # If any
    'enter_text': 'You push open the door...'      # First-visit text
}
```

#### Example Output

```
📍 The Rusty Dragon

  You push through the heavy oak door into welcoming warmth. A crackling 
  hearth bathes worn wooden tables in dancing firelight. The gruff barkeep 
  polishes a glass behind the counter, eyeing you with practiced indifference. 
  In a corner booth, a worried farmer named Bram stares into his ale. A torch 
  flickers on the wall, and you notice a healing potion on a nearby table.

  🚪 Exits: door, bar
```

#### Commands

| Command | Description |
|---------|-------------|
| `look` | AI-generated narrative description |
| `scan` | Mechanical list of items, NPCs, exits |

#### Extending Location Narration

To add narration when entering a location:

```python
# 1. Build context after mechanics resolve
context = build_location_context(
    location=new_location,
    is_first_visit=is_first,
    events=triggered_events
)

# 2. Request narration from AI
narration = get_location_narration(chat, context)

# 3. Display narration
display_location_narration(location.name, narration, exits)
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

### XP Reward System (System-Controlled)

> ⚠️ **XP is primarily awarded automatically by the system, not the AI DM.**

| XP Source | Controller | When |
|-----------|------------|------|
| **Combat** | `combat.py` | Automatic per enemy killed |
| **Objectives** | `scenario.py` | Automatic when objective completed |
| **Quests** | `quest.py` | Automatic when quest completed |
| **AI (RARE)** | DM's `[XP:]` tag | Only for exceptional roleplay |

### AI XP Tags (Rare - Exceptional Only)

The AI DM can award 25 XP for **truly exceptional** roleplay:

| Tag Format | Description |
|------------|-------------|
| `[XP: 25]` | Award 25 XP (exceptional only) |
| `[XP: 25 \| Creative trap]` | Award with reason |

**✅ When AI SHOULD use XP tags (award 25 XP):**
1. **Creative Puzzle Solving** - Player thinks outside the box
   - Using environment unexpectedly (rope + oil = trap)
   - Connecting clues from earlier conversations
2. **Brilliant Negotiation** - Exceptional diplomacy
   - Convincing hostile enemies to switch sides
   - Finding non-obvious win-win solutions
3. **Unexpected Ingenuity** - Surprising clever actions
   - Combining items creatively (mirror + sunlight)
   - Using environment in unexpected ways

**❌ When AI should NEVER use XP tags:**
- Accepting quests (handled by objective XP)
- Reaching locations (handled by objective XP)
- Defeating enemies (handled by combat XP)
- Completing quests (handled by quest rewards)
- Using items as intended
- Normal dialogue or investigation
- Following obvious paths

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

### Running Tests

**Unit Tests (821+ tests total):**
```bash
# Run all unit tests
cd tests
python -m pytest . -v

# Run specific test file
python -m pytest test_location.py -v

# Run with coverage
python -m pytest . --cov=../src --cov-report=html

# Use the interactive test runner
python run_interactive_tests.py
```

**Security Tests (125 tests):**
```bash
# Run hostile player final test suite
python tests/hostile_final.py

# Results documented in docs/HOSTILE_PLAYER_TESTING.md
```

**Interactive Tests (require AI API key):**
```bash
# Unified test runner - menu-driven interface
python tests/run_interactive_tests.py

# Individual interactive tests
python tests/test_combat_with_dm.py
python tests/test_location_with_dm.py
python tests/test_inventory_with_dm.py
python tests/test_dice_with_dm.py
```

**E2E Tests (Playwright):**
```bash
cd frontend/option1-react

# Run all E2E tests (headless)
npm run test:e2e

# Run with visible browser
npm run test:e2e:headed

# Run with Playwright UI (interactive)
npm run test:e2e:ui

# View last HTML report
npx playwright show-report
```

### Playwright E2E Testing

The project uses Playwright for browser-based end-to-end testing.

**Location:** `frontend/option1-react/e2e/`

**Configuration:** `frontend/option1-react/playwright.config.ts`

**Test Files:**
- `e2e/game.spec.ts` - Basic game flow tests

**What E2E Tests Cover:**
- Page loading and initial render
- Character creation screen
- Game UI elements detection
- Player action submission
- Screenshot capture

**Screenshots:** `e2e/screenshots/` - Captured during test runs

**Maintaining Playwright Tests:**

1. **Updating Selectors:**
   When UI changes, update selectors in test files:
   ```typescript
   // Before: page.locator('button').filter({ hasText: /start/i })
   // After: page.getByRole('button', { name: 'Begin Adventure' })
   ```

2. **Adding New Tests:**
   ```typescript
   test('should open inventory modal', async ({ page }) => {
     await page.goto('/');
     await page.getByRole('button', { name: /inventory/i }).click();
     await expect(page.locator('.inventory-modal')).toBeVisible();
     await page.screenshot({ path: 'e2e/screenshots/inventory.png' });
   });
   ```

3. **Debugging Failed Tests:**
   ```bash
   # Run single test with visible browser
   npx playwright test --headed -g "test name"
   
   # Debug mode (step through)
   npx playwright test --debug
   
   # Show trace viewer
   npx playwright show-trace trace.zip
   ```

4. **Updating Browser:**
   ```bash
   npx playwright install chromium
   ```

5. **Common Issues:**
   | Issue | Solution |
   |-------|----------|
   | "Timeout waiting for element" | Increase timeout or add `waitFor` |
   | "Element not visible" | Check if modal/overlay blocks it |
   | "Test flaky" | Add `waitForLoadState('networkidle')` |
   | "Screenshot differs" | Update expected screenshot |

### Test Coverage Summary

| Module | Tests | Description |
|--------|-------|-------------|
| test_character.py | 26 | Character creation, stats, XP |
| test_combat.py | 31 | Combat mechanics, attacks |
| test_combat_travel_block.py | 3 | Combat exploit prevention |
| test_dialogue.py | 25 | NPC dialogue system |
| test_flexible_travel.py | 25 | Flexible travel input normalization |
| test_flow_breaking.py | 29 | Flow breaking/weird input |
| test_hostile_player.py | 44 | Adversarial exploit testing |
| test_inventory.py | 35 | Items, inventory management |
| test_location.py | 200 | Location system, movement, events |
| test_location_with_dm.py | 13 | Interactive location unit tests |
| test_multi_enemy.py | 3 | Multi-enemy combat |
| test_npc.py | 55 | NPC system, roles, serialization |
| test_party.py | 72 | Party/companion system |
| test_prompt_injection.py | 22 | Security/injection testing |
| test_quest.py | 57 | Quest tracking system |
| test_reputation.py | 55 | Disposition system |
| test_reputation_hostile.py | 36 | Disposition adversarial tests |
| test_save_system.py | 7 | Save/load persistence |
| test_scenario.py | 31 | Scenarios, scenes, objectives |
| test_shop.py | 72 | Shop system, buy/sell/haggle |
| test_travel_menu.py | 42 | Travel menu system |
| test_xp_system.py | 10 | XP and leveling |
| hostile_final.py | 75 | Security stress tests (Round 5) |
| **TOTAL** | **821+** | All unit tests |

### Security Testing Summary

| Round | Tests | Pass | Issues Fixed |
|-------|-------|------|--------------|
| 1-3 | 25 | 25 | 8 issues |
| 4 | 25 | 25 | 3 issues |
| 5 | 75 | 75 | 5 issues |
| **Total** | **125** | **125** | **16 issues** |

**All 16 security vulnerabilities have been identified and fixed.**

See [HOSTILE_PLAYER_TESTING.md](HOSTILE_PLAYER_TESTING.md) for detailed results.

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

## Security

### Security Testing Results

The game has undergone comprehensive hostile player testing with **160 unique security tests** across 7 rounds:

| Round | Tests | Focus Areas |
|-------|-------|-------------|
| 1-3 | 25 | Input validation, prompt injection, state manipulation, API abuse |
| 4 | 25 | Combat exploits, save/load manipulation, session hijacking |
| 5 | 75 | Header injection, resource exhaustion, inventory exploits |
| 6 | 25 | Reputation endpoints, SkillCheckOption, poison, darkness, rope/lockpick |
| 7 | 10 | Darkness combat integration, light source manipulation |

| Category | Description |
|----------|-------------|
| Input Validation | Empty/long names, SQL injection, unicode attacks |
| Prompt Injection | System prompt override, roleplay escape, delimiter injection |
| State Manipulation | Invalid sessions, negative values, inventory overflow |
| API Abuse | Missing/wrong type parameters, method override attempts |
| Edge Cases | Combat during travel, non-present NPCs, rapid action spam |
| Combat Exploits | Attack/flee outside combat, invalid targets |
| Save/Load Manipulation | Path traversal, corrupted saves, cross-session loading |
| Session Hijacking | UUID guessing, JWT injection, admin flag injection |
| Header Injection | Host/X-Forwarded-For spoof, XSS in User-Agent |
| Resource Exhaustion | Rapid session creation, 1MB payloads, concurrent attacks |

### Security Fixes Applied (16 total)

1. **Character name validation** - Required, max 50 chars, trimmed
2. **Action type validation** - Must be string, prevents 500 errors
3. **Shop buy API** - Fixed broken function signature
4. **Quantity validation** - Positive integers only, max 99
5. **Unicode/SSE encoding** - `ensure_ascii=False` for proper emoji support
6. **Session cleanup** - 60-minute timeout, background cleanup thread
7. **Travel during combat** - Blocked with proper error message
8. **Party.is_full property** - Fixed method vs property access
9. **Character.from_dict()** - Added missing method for save/load
10. **Save name sanitization** - Path traversal blocked, dangerous chars removed
11. **Quest ID type validation** - Proper type checking
12. **Zero-sided dice** - Validation added
13. **NPCManager access** - Fixed method calls
14. **QuestManager get_completed_quests** - Method implemented
15. **Quest list error handling** - Improved error responses
16. **Action string type** - Proper type validation before .strip()

### Security Best Practices

- All user input is validated before processing
- Session IDs use UUID4 (128-bit random, brute-force infeasible)
- AI DM resists prompt injection (tested with 25+ attack vectors)
- Save files are sanitized to prevent path traversal
- Combat state is checked before allowing travel
- Unknown API parameters are ignored (no cheat_mode, god_mode)

---

## Deployment

### Local Development

```bash
# Clone
git clone https://github.com/Axidify/ai-dnd-rpg.git
cd ai-dnd-rpg

# Setup Backend
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY

# Start Backend API
python src/api_server.py

# In a new terminal - Setup and Start Frontend
cd frontend/option1-react
npm install
npm run dev
```

### VS Code Tasks (Recommended)
The workspace includes predefined tasks for easy development:
- **🎮 Start Backend (Flask)** - Start API server on port 5000
- **🌐 Start Frontend (React)** - Start dev server on port 3000
- **🚀 Start Full Stack** - Start both simultaneously

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
| Garbled emojis (ðŸ" instead of 📍) | Mojibake - double-encoded UTF-8 | Run `pip install ftfy` then `python -c "import ftfy; f=open('file.py'); open('file.py','w').write(ftfy.fix_text(f.read()))"` |
| Emojis as `\u1F4CD` in JSON | Flask JSON encoding | Add `app.json.ensure_ascii = False` after Flask app creation |

### Encoding / Emoji Issues

Emojis in Python source files or API responses may become corrupted ("mojibake") when:
- Files are saved with wrong encoding (Latin-1 instead of UTF-8)
- Copy-paste from browser to editor with encoding mismatch
- Git or editor auto-converts line endings with wrong charset

**Detecting Mojibake:**
```python
# Common mojibake patterns (UTF-8 interpreted as Latin-1):
# 📍 → ðŸ" | 🔥 → ðŸ"¥ | ⭐ → â­ | 💰 → ðŸ'°
```

**Fixing Mojibake in Files:**
```bash
pip install ftfy
python -c "import ftfy; content=open('file.py','r',encoding='utf-8').read(); open('file.py','w',encoding='utf-8').write(ftfy.fix_text(content))"
```

**Flask UTF-8 JSON Configuration:**
```python
app = Flask(__name__)
app.json.ensure_ascii = False  # Required for proper emoji in JSON responses
```

### Debug Mode

Add to `game.py` for verbose output:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# In get_dm_response:
logging.debug(f"Sending: {player_input}")
logging.debug(f"Received: {response.text[:100]}...")
```

### Verbose Game Logging System

The API server includes a comprehensive logging system that writes to both console and `notes.log`:

**Configuration (environment variables):**
- `VERBOSE_LOGGING=true` - Enable/disable verbose logging (default: true)
- `LOG_TO_FILE=true` - Enable/disable file logging to notes.log (default: true)

**Log Categories:**

| Category | Icon | Description |
|----------|------|-------------|
| ACTION | 🎮 | Player actions submitted |
| DM | 🎲 | DM responses generated |
| PARSE | 🔍 | Tag parsing operations |
| ROLL | 🎯 | Skill checks and dice rolls |
| COMBAT | ⚔️ | Combat events and damage |
| ITEM | 📦 | Item transactions |
| GOLD | 💰 | Gold gained/spent |
| XP | ⭐ | Experience gains |
| QUEST | 📜 | Quest acceptance/completion |
| RECRUIT | 👥 | Party recruitment attempts |
| PARTY | 🛡️ | Party changes |
| LOCATION | 🗺️ | Travel and location changes |
| NPC | 🗣️ | NPC interactions |
| SAVE | 💾 | Save/load operations |
| ERROR | ❌ | Errors and failures |
| API | 📡 | API requests |
| SESSION | 🔑 | Session lifecycle events |

**Example Log Output:**
```
[14:30:15] 📡 [API] POST /api/action/streaming
    ↳ {"session": "41b2a41f", "from": "127.0.0.1"}
[14:30:15] 🎮 [ACTION] Player: I talk to Marcus about joining my party
[14:30:17] 🎲 [DM] Response length: 847 chars
[14:30:17] 👥 [RECRUIT] Attempting to recruit: marcus
[14:30:17] 👥 [RECRUIT] Recruitment result: Marcus has joined!
    ↳ {"success": true, "npc_id": "marcus_mercenary", "party_size": 2}
```

**Using game_log() in Code:**
```python
from api_server import game_log, VERBOSE_LOGGING

if VERBOSE_LOGGING:
    game_log('QUEST', 'Quest accepted: Rescue Lily', {'quest_id': 'rescue_lily'})
```

**Monitoring Logs:**
```bash
# Watch logs in real-time (PowerShell)
Get-Content notes.log -Wait -Tail 50

# Watch logs in real-time (Linux/Mac)
tail -f notes.log
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

### Variable Naming Conventions

**Manager Variables in Main Loop:**
```python
# ✅ CORRECT - Use full names at loop scope
location_manager = scenario_manager.active_scenario.location_manager
npc_manager = scenario_manager.active_scenario.npc_manager

if location_manager:
    location = location_manager.get_current_location()
```

```python
# ❌ WRONG - Don't re-extract managers in each block
if scenario_manager.is_active():
    loc_mgr = scenario_manager.active_scenario.location_manager  # Redundant!
```

**Function Parameters:**
```python
# ✅ OK - Short names acceptable as function parameters
def show_travel_menu(location, loc_mgr) -> dict:
    """loc_mgr is acceptable here since it's a parameter."""
    exits = loc_mgr.get_exits()
```

**Key Principle:** Define managers once at the start of each loop iteration, then reference the persistent variables throughout the loop.

---

## References

- [Google Gemini API Docs](https://ai.google.dev/docs)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [D&D 5e SRD](https://www.5esrd.com/) (for game mechanics reference)
- [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) (project roadmap)
