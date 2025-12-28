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
9. [World Map System](#world-map-system-phase-45) â† **NEW**
10. [NPC System](#npc-system-phase-33)
11. [Shop System](#shop-system-phase-333)
12. [Traveling Merchants](#traveling-merchants-phase-33---priority-5)
13. [Party System](#party-system-phase-337)
14. [Quest System](#quest-system-phase-334)
15. [Extending the Game](#extending-the-game)
16. [Testing Guidelines](#testing-guidelines)
17. [Security](#security) â† **75 tests passing**
18. [Deployment](#deployment)
19. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### Current Architecture (API-First Design)

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  React Web    â”‚     â”‚  Godot Client â”‚     â”‚ Flutter App   â”‚
â”‚  (Vite)       â”‚     â”‚   (Future)    â”‚     â”‚   (Future)    â”‚
â”‚ localhost:3000â”‚     â”‚               â”‚     â”‚               â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜
        â”‚                     â”‚                     â”‚
        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                              â”‚
                              â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                 api_server.py (Flask REST API)              â”‚
â”‚                    localhost:5000/api/*                     â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”         â”‚
â”‚  â”‚  Endpoints  â”‚â†’ â”‚ dm_engine   â”‚â†’ â”‚  Response   â”‚         â”‚
â”‚  â”‚  /game/*    â”‚  â”‚  (logic)    â”‚  â”‚  SSE Stream â”‚         â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜         â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                              â”‚
                              â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                 dm_engine.py (Shared Logic)                 â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚
â”‚  â”‚  DM_SYSTEM_PROMPT - Complete AI ruleset             â”‚   â”‚
â”‚  â”‚  parse_*() - Tag parsing functions                  â”‚   â”‚
â”‚  â”‚  roll_skill_check() - Dice mechanics                â”‚   â”‚
â”‚  â”‚  build_full_dm_context() - Prompt construction      â”‚   â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                              â”‚
                              â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                 Google Gemini API                           â”‚
â”‚              (google-generativeai library)                  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### Legacy Architecture (Archived)

The original terminal-based game (`backup/legacy/game.py`) has been archived.
The current architecture uses API-first design where `api_server.py` is the
only entry point and all game logic is shared via `dm_engine.py`.

### Planned Extensions (Phase 5-6)

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Flutter App  â”‚     â”‚  Flutter App  â”‚     â”‚  Flutter App  â”‚
â”‚    Mobile     â”‚     â”‚     Web       â”‚     â”‚   Desktop     â”‚
â”‚  (iOS/Android)â”‚     â”‚   (Browser)   â”‚     â”‚ (Win/Mac/Lin) â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜
        â”‚                     â”‚                     â”‚
        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
                       â”‚                     â”‚
                       â–¼                     â–¼
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â”‚              FastAPI Backend                â”‚
        â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”      â”‚
        â”‚  â”‚  Auth Service â”‚  â”‚  Game Logic   â”‚      â”‚
        â”‚  â”‚  AI Handler   â”‚  â”‚  Save/Load    â”‚      â”‚
        â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜      â”‚
        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                               â”‚
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â–¼                      â–¼                      â–¼
  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”          â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”          â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
  â”‚ Gemini   â”‚          â”‚ Database â”‚          â”‚  Redis   â”‚
  â”‚   API    â”‚          â”‚ Postgres â”‚          â”‚  Cache   â”‚
  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜          â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜          â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

**Flutter Target Platforms:**
- ðŸ“± iOS (App Store)
- ðŸ“± Android (Play Store)

### Core Design Principle: Mechanics First, Narration Last

This is the **fundamental architectural pattern** that governs all systems in the game.

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    PLAYER ACTION                                â”‚
â”‚         "attack goblin" / "go north" / "pick lock"              â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                            â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  STEP 1: MECHANICS LAYER (Deterministic, Python)                â”‚
â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€              â”‚
â”‚  â€¢ Parse command                                                â”‚
â”‚  â€¢ Roll dice (if applicable)                                    â”‚
â”‚  â€¢ Calculate results (damage, movement, success/fail)           â”‚
â”‚  â€¢ Update game state (HP, location, inventory)                  â”‚
â”‚  â€¢ Determine outcome FIRST                                      â”‚
â”‚                                                                 â”‚
â”‚  OUTPUT: Concrete result + context for AI                       â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                            â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  STEP 2: AI NARRATION LAYER (Creative, Gemini)                  â”‚
â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€              â”‚
â”‚  â€¢ Receives final results (cannot change them!)                 â”‚
â”‚  â€¢ Describes what happened in vivid prose                       â”‚
â”‚  â€¢ Adds atmosphere, NPC reactions, sensory details              â”‚
â”‚  â€¢ Never contradicts mechanical outcome                         â”‚
â”‚                                                                 â”‚
â”‚  OUTPUT: Immersive narration for player                         â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
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
2. MECHANICS: Roll d20+5 = 18 vs AC 13 â†’ HIT, Roll 1d8+3 = 7 damage
3. AI receives: "Player hit Goblin for 7 damage (18 vs AC 13)"
4. AI narrates: "Your blade arcs through the air, catching the goblin 
   across the shoulder! It shrieks in pain, dark blood spattering the stones."
```

**Example: Location Movement**
```
1. Player: "go north"
2. MECHANICS: Check exits â†’ valid, Move player, Check events â†’ first visit
3. AI receives: "Player entered Boss Chamber (first visit). Event: chief_roars"
4. AI narrates: "You step into the torch-lit chamber and a thunderous 
   roar shakes the very stones..."
```

This pattern applies to: **Combat, Movement, Skill Checks, Item Interaction, NPC Dialogue, Save/Load, and all future systems.**
- ðŸŒ Web (Any browser)
- ðŸ–¥ï¸ Windows (Downloadable)
- ðŸ–¥ï¸ macOS (Downloadable)
- ðŸ§ Linux (Downloadable)

---

## Project Structure

```
ai-dnd-rpg/
â”‚
â”œâ”€â”€ .env                    # Environment variables (NEVER COMMIT)
â”œâ”€â”€ .env.example            # Template for environment setup
â”œâ”€â”€ .gitignore              # Git ignore patterns
â”œâ”€â”€ .venv/                  # Python virtual environment
â”‚
â”œâ”€â”€ docs/
â”‚   â”œâ”€â”€ CHANGELOG.md            # Version history
â”‚   â”œâ”€â”€ DEVELOPER_GUIDE.md      # This file (5000+ lines)
â”‚   â”œâ”€â”€ DEVELOPMENT_PLAN.md     # Project roadmap with phases
â”‚   â”œâ”€â”€ FLUTTER_SETUP.md        # Flutter installation guide
â”‚   â”œâ”€â”€ HOSTILE_PLAYER_TESTING.md # Security testing (160 tests, 16 fixes)
â”‚   â”œâ”€â”€ THEME_SYSTEM_SPEC.md    # DLC-ready theme architecture
â”‚   â””â”€â”€ UI_DESIGN_SPEC.md       # UI/UX specifications
â”‚
â”œâ”€â”€ saves/                  # Game save files (auto-created)
â”‚   â””â”€â”€ save_*.json             # Individual save files
â”‚
â”œâ”€â”€ README.md               # User-facing documentation
â”œâ”€â”€ requirements.txt        # Python dependencies
â”œâ”€â”€ tasksync.md             # Development protocol
â”‚
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ __init__.py         # Package marker
â”‚   â”œâ”€â”€ api_server.py       # Flask REST API (main entry point, 35 endpoints)
â”‚   â”œâ”€â”€ dm_engine.py        # Shared DM logic (prompts, parsing)
â”‚   â”œâ”€â”€ character.py        # Character system (stats, creation, XP/leveling)
â”‚   â”œâ”€â”€ combat.py           # Combat system (attacks, damage, multi-enemy)
â”‚   â”œâ”€â”€ inventory.py        # Item and inventory management
â”‚   â”œâ”€â”€ npc.py              # NPC system (dialogue, roles, managers)
â”‚   â”œâ”€â”€ party.py            # Party/companion system
â”‚   â”œâ”€â”€ quest.py            # Quest tracking system
â”‚   â”œâ”€â”€ save_system.py      # Save/Load system
â”‚   â”œâ”€â”€ scenario.py         # Scenario and scene management
â”‚   â””â”€â”€ shop.py             # Shop system (buy/sell/haggle)
â”‚
â”œâ”€â”€ frontend/
â”‚   â””â”€â”€ option1-react/      # React + Vite + Tailwind frontend
â”‚       â”œâ”€â”€ src/
â”‚       â”‚   â”œâ”€â”€ App.jsx
â”‚       â”‚   â”œâ”€â”€ components/
â”‚       â”‚   â”‚   â”œâ”€â”€ CharacterCreation.jsx
â”‚       â”‚   â”‚   â”œâ”€â”€ GameScreen.jsx
â”‚       â”‚   â”‚   â”œâ”€â”€ WorldMap.jsx
â”‚       â”‚   â”‚   â””â”€â”€ DiceRoller.jsx
â”‚       â”‚   â””â”€â”€ store/gameStore.js
â”‚       â””â”€â”€ package.json
â”‚
â”œâ”€â”€ backup/
â”‚   â””â”€â”€ legacy/
â”‚       â””â”€â”€ game.py         # Archived terminal version (no longer maintained)
â”‚
â””â”€â”€ tests/                       # 985 unit tests + 75 security tests
    â”œâ”€â”€ run_interactive_tests.py  # Unified test runner (all test modes)
    â”œâ”€â”€ hostile_final.py        # Security stress tests (75 tests - Round 5)
    â”œâ”€â”€ test_ai_stress.py       # AI security stress tests (23 cases)
    â”œâ”€â”€ test_character.py       # Character system tests (26 tests)
    â”œâ”€â”€ test_combat.py          # Combat mechanics tests (31 tests)
    â”œâ”€â”€ test_combat_travel_block.py # Combat exploit prevention (3 tests)
    â”œâ”€â”€ test_combat_with_dm.py  # Interactive combat tests (3 tests)
    â”œâ”€â”€ test_dice.py            # Dice rolling manual tests (standalone)
    â”œâ”€â”€ test_dice_with_dm.py    # Dice + AI tests
    â”œâ”€â”€ test_dialogue.py        # NPC dialogue system tests (24 tests)
    â”œâ”€â”€ test_flexible_travel.py # Flexible travel input tests (25 tests)
    â”œâ”€â”€ test_flow_breaking.py   # Flow breaking/weird input tests (29 tests)
    â”œâ”€â”€ test_hostile_player.py  # Adversarial exploit tests (44 tests)
    â”œâ”€â”€ test_inventory.py       # Inventory system tests (35 tests)
    â”œâ”€â”€ test_inventory_with_dm.py # Interactive inventory tests (AI)
    â”œâ”€â”€ test_location.py        # Location system tests (200 tests)
    â”œâ”€â”€ test_location_with_dm.py # Interactive location tests (13 tests)
    â”œâ”€â”€ test_multi_enemy.py     # Multi-enemy combat tests (3 tests)
    â”œâ”€â”€ test_npc.py             # NPC system tests (55 tests)
    â”œâ”€â”€ test_party.py           # Party/companion tests (72 tests)
    â”œâ”€â”€ test_prompt_injection.py # Security/injection tests (22 tests)
    â”œâ”€â”€ test_quest.py           # Quest system tests (57 tests)
    â”œâ”€â”€ test_quest_hooks.py     # Quest event hooks tests
    â”œâ”€â”€ test_reputation.py      # Disposition system tests (55 tests)
    â”œâ”€â”€ test_reputation_hostile.py # Disposition adversarial tests (36 tests)
    â”œâ”€â”€ test_save_system.py     # Save/Load system tests (8 tests)
    â”œâ”€â”€ test_scenario.py        # Scenario system tests (31 tests)
    â”œâ”€â”€ test_shop.py            # Shop system tests (72 tests)
    â”œâ”€â”€ test_travel_menu.py     # Travel menu system tests (42 tests)
    â””â”€â”€ test_xp_system.py       # XP and leveling tests (10 tests)
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

> **âš ï¸ IMPORTANT NOTE:** This document contains historical references to `game.py` (the 
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
    print("ðŸŽ² Dungeon Master:")
    get_dm_response(chat, f"Welcome {character.name}...")
    
    # 4. Game loop with commands
    while True:
        player_input = input("âš”ï¸  Your action: ").strip()
        
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
        print("ðŸŽ² Dungeon Master:")
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
| Fighter | Longsword | Chain Shirt | â€” |
| Paladin | Longsword | Chain Shirt | â€” |
| Ranger | Shortbow | Leather Armor | â€” |
| Barbarian | Greataxe | Leather Armor | â€” |
| Wizard | Quarterstaff | â€” | â€” |
| Sorcerer | Dagger | â€” | â€” |
| Rogue | Shortsword | Leather Armor | Lockpicks |
| Bard | Shortsword | Leather Armor | â€” |
| Warlock | Dagger | Leather Armor | â€” |
| Monk | Quarterstaff | â€” | â€” |
| Cleric | Mace | Chain Shirt | â€” |
| Druid | Quarterstaff | Leather Armor | â€” |

**Code Location:** `character.py` â†’ `Character._add_starting_equipment()`

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
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘                      INVENTORY                           â•‘
â• â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•£
â•‘  ðŸ’° Gold: 25                                            â•‘
â• â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•£
â•‘  âš”ï¸ Weapons                                            â•‘
â•‘    â€¢ Longsword [DMG: 1d8]                                â•‘
â•‘    â€¢ Dagger [DMG: 1d4]                                   â•‘
â•‘  ðŸ›¡ï¸ Armor                                              â•‘
â•‘    â€¢ Studded Leather [AC: +2]                            â•‘
â•‘  ðŸ§ª Consumables                                         â•‘
â•‘    â€¢ Healing Potion [HEAL: 2d4+2]                        â•‘
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
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
ðŸŽ² Stealth (DEX): [14]+3 = 17 vs DC 15 = âœ… SUCCESS
ðŸŽ² Athletics (STR): [1]+2 = 3 vs DC 12 = âŒ FAILURE ðŸ’€ NAT 1!
ðŸŽ² Perception (WIS): [20]+1 = 21 vs DC 10 = âœ… SUCCESS âœ¨ NAT 20!
```

---

## Game Loop Logic

> **NOTE:** The terminal game loop has been replaced with an API-first architecture.
> The sections below describe the legacy terminal flow for historical reference.
> See `api_server.py` for the current request/response flow.

### API Request Flow (Current)

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    React Frontend                                â”‚
â”‚    [CharacterCreation.jsx] â†’ [GameScreen.jsx] â†’ [Modals]        â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                            â”‚ HTTP/SSE
                            â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    api_server.py (Flask)                         â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚
â”‚  â”‚  POST /api/game/start      â†’ Create session, character  â”‚   â”‚
â”‚  â”‚  POST /api/game/action/stream â†’ Process action, SSE     â”‚   â”‚
â”‚  â”‚  POST /api/travel           â†’ Change location           â”‚   â”‚
â”‚  â”‚  GET  /api/game/state       â†’ Get current state         â”‚   â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                            â”‚
                            â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    dm_engine.py (Shared Logic)                   â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”‚
â”‚  â”‚  build_full_dm_context() â†’ Construct AI prompt           â”‚   â”‚
â”‚  â”‚  parse_*() â†’ Extract tags from DM response               â”‚   â”‚
â”‚  â”‚  roll_skill_check() â†’ Handle dice mechanics              â”‚   â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                            â”‚
                            â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    Google Gemini API                             â”‚
â”‚                    (Streaming responses)                         â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### Legacy Terminal State Machine (Archived)

```
INIT â†’ CHARACTER_CREATE â†’ SCENARIO_SELECT â†’ PLAYING â‡„ COMBAT â†’ INVENTORY â†’ SAVE/LOAD â†’ EXIT
```

---

## Save/Load System

The save system (`src/save_system.py`) handles game state persistence. It's designed to be multi-platform ready for Phase 5 (Backend API) and Phase 6 (Flutter App).

### Architecture

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    Save/Load System                          â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚                                                              â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”                â”‚
â”‚  â”‚  SaveManager    â”‚â”€â”€â”€â”€â–¶â”‚ StorageBackend  â”‚  (abstract)    â”‚
â”‚  â”‚                 â”‚     â”‚                 â”‚                â”‚
â”‚  â”‚  - save_game()  â”‚     â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜                â”‚
â”‚  â”‚  - load_game()  â”‚              â”‚                          â”‚
â”‚  â”‚  - list_saves() â”‚     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”                â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â”‚                 â”‚                â”‚
â”‚                          â–¼                 â–¼                â”‚
â”‚              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”       â”‚
â”‚              â”‚LocalFileBackend â”‚  â”‚ CloudBackend    â”‚       â”‚
â”‚              â”‚   (Phase 3)     â”‚  â”‚   (Phase 5)     â”‚       â”‚
â”‚              â”‚ saves/*.json    â”‚  â”‚  REST API       â”‚       â”‚
â”‚              â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜       â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
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
| `character_to_dict(char)` | Character â†’ JSON-ready dict |
| `dict_to_character(data, Character)` | Dict â†’ Character object |
| `item_to_dict(item)` | Item â†’ dict |
| `dict_to_item(data)` | Dict â†’ Item object |
| `scenario_to_dict(manager)` | Scenario state â†’ dict |
| `restore_scenario(manager, data)` | Dict â†’ Scenario state |

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
| `SaveSystemError` | Base class for all save errors | â€” |
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

The system uses atomic saves (temp file â†’ rename) to prevent corruption:
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
       player_input = input("âš”ï¸  Your action: ").strip()
       
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
       print(f"ðŸŽ² You rolled: {result['total']} ({result['dice']})")
   ```

### Creating New Modules

```
src/
â”œâ”€â”€ __init__.py
â”œâ”€â”€ game.py          # Main entry point
â”œâ”€â”€ ai/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ client.py    # AI client setup
â”‚   â””â”€â”€ prompts.py   # System prompts
â”œâ”€â”€ mechanics/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ dice.py      # Dice rolling
â”‚   â”œâ”€â”€ combat.py    # Combat system
â”‚   â””â”€â”€ character.py # Character management
â””â”€â”€ utils/
    â”œâ”€â”€ __init__.py
    â””â”€â”€ helpers.py   # Utility functions
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

> **âš ï¸ XP Tag Usage:** Most XP is awarded automatically by the system (combat, objectives, quests). The AI should only use `[XP:]` tags for **exceptional** roleplay like creative puzzle solutions. See [XP System](#xp-system-controlled) for details.

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

---

## Combat System

> **📖 Full documentation moved to: [COMBAT_SYSTEM.md](COMBAT_SYSTEM.md)**
> 
> This section covers:
> - DM Combat Triggers and tag parsing
> - Combat initialization and turn order
> - Attack, defense, and damage calculations
> - Multi-enemy encounters
> - Surprise rounds and advantage system
> - Combat resolution and XP rewards

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

> âš ï¸ **XP is primarily awarded automatically by the system, not the AI DM.**

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

**âœ… When AI SHOULD use XP tags (award 25 XP):**
1. **Creative Puzzle Solving** - Player thinks outside the box
   - Using environment unexpectedly (rope + oil = trap)
   - Connecting clues from earlier conversations
2. **Brilliant Negotiation** - Exceptional diplomacy
   - Convincing hostile enemies to switch sides
   - Finding non-obvious win-win solutions
3. **Unexpected Ingenuity** - Surprising clever actions
   - Combining items creatively (mirror + sunlight)
   - Using environment in unexpected ways

**âŒ When AI should NEVER use XP tags:**
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

**Unit Tests (985 tests total):**
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

**Security Tests (75 tests):**
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
| **TOTAL** | **985** | All unit tests |

### Security Testing Summary

| Round | Tests | Pass | Issues Fixed |
|-------|-------|------|--------------|
| 1-3 | 25 | 25 | 8 issues |
| 4 | 25 | 25 | 3 issues |
| 5 | 75 | 75 | 5 issues |
| **Total** | **75** | **75** | **16 issues** |

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
- **ðŸŽ® Start Backend (Flask)** - Start API server on port 5000
- **ðŸŒ Start Frontend (React)** - Start dev server on port 3000
- **ðŸš€ Start Full Stack** - Start both simultaneously

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
| Garbled emojis (Ã°Å¸" instead of ðŸ“) | Mojibake - double-encoded UTF-8 | Run `pip install ftfy` then `python -c "import ftfy; f=open('file.py'); open('file.py','w').write(ftfy.fix_text(f.read()))"` |
| Emojis as `\u1F4CD` in JSON | Flask JSON encoding | Add `app.json.ensure_ascii = False` after Flask app creation |

### Encoding / Emoji Issues

Emojis in Python source files or API responses may become corrupted ("mojibake") when:
- Files are saved with wrong encoding (Latin-1 instead of UTF-8)
- Copy-paste from browser to editor with encoding mismatch
- Git or editor auto-converts line endings with wrong charset

**Detecting Mojibake:**
```python
# Common mojibake patterns (UTF-8 interpreted as Latin-1):
# ðŸ“ â†’ Ã°Å¸" | ðŸ”¥ â†’ Ã°Å¸"Â¥ | â­ â†’ Ã¢Â­ | ðŸ’° â†’ Ã°Å¸'Â°
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
| ACTION | ðŸŽ® | Player actions submitted |
| DM | ðŸŽ² | DM responses generated |
| PARSE | ðŸ” | Tag parsing operations |
| ROLL | ðŸŽ¯ | Skill checks and dice rolls |
| COMBAT | âš”ï¸ | Combat events and damage |
| ITEM | ðŸ“¦ | Item transactions |
| GOLD | ðŸ’° | Gold gained/spent |
| XP | â­ | Experience gains |
| QUEST | ðŸ“œ | Quest acceptance/completion |
| RECRUIT | ðŸ‘¥ | Party recruitment attempts |
| PARTY | ðŸ›¡ï¸ | Party changes |
| LOCATION | ðŸ—ºï¸ | Travel and location changes |
| NPC | ðŸ—£ï¸ | NPC interactions |
| SAVE | ðŸ’¾ | Save/load operations |
| ERROR | âŒ | Errors and failures |
| API | ðŸ“¡ | API requests |
| SESSION | ðŸ”‘ | Session lifecycle events |

**Example Log Output:**
```
[14:30:15] ðŸ“¡ [API] POST /api/action/streaming
    â†³ {"session": "41b2a41f", "from": "127.0.0.1"}
[14:30:15] ðŸŽ® [ACTION] Player: I talk to Marcus about joining my party
[14:30:17] ðŸŽ² [DM] Response length: 847 chars
[14:30:17] ðŸ‘¥ [RECRUIT] Attempting to recruit: marcus
[14:30:17] ðŸ‘¥ [RECRUIT] Recruitment result: Marcus has joined!
    â†³ {"success": true, "npc_id": "marcus_mercenary", "party_size": 2}
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
# âœ… CORRECT - Use full names at loop scope
location_manager = scenario_manager.active_scenario.location_manager
npc_manager = scenario_manager.active_scenario.npc_manager

if location_manager:
    location = location_manager.get_current_location()
```

```python
# âŒ WRONG - Don't re-extract managers in each block
if scenario_manager.is_active():
    loc_mgr = scenario_manager.active_scenario.location_manager  # Redundant!
```

**Function Parameters:**
```python
# âœ… OK - Short names acceptable as function parameters
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
