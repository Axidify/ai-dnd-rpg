# AI D&D Text RPG - Project Documentation

## Overview
A text-based Dungeons & Dragons style RPG where Google Gemini AI acts as the Dungeon Master, creating an interactive storytelling experience.

**Architecture**: API-first design with Flask backend and React frontend.

**Security**: 🛡️ 75/75 security tests passing (16 vulnerabilities identified and fixed)

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend)
- Google Gemini API key

### Backend Setup
```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Start backend
python src/api_server.py
```

### Frontend Setup
```bash
cd frontend/option1-react
npm install
npm run dev
```

### Play the Game
- Backend API: http://localhost:5000
- React Frontend: http://localhost:3000

---

## Project Structure

```
AI RPG V2/
├── .env                    # Environment variables (API keys) - DO NOT COMMIT
├── .venv/                  # Python virtual environment
├── README.md               # This file
├── requirements.txt        # Python dependencies
├── tasksync.md             # TaskSync protocol
├── saves/                  # Game save files (auto-created)
├── docs/
│   ├── API_DOCUMENTATION.md    # REST API endpoint reference
│   ├── ASSESSMENT_GUIDE.md     # Project assessment framework
│   ├── CHANGELOG.md            # Version history
│   ├── DEVELOPER_GUIDE.md      # Technical documentation (5000+ lines)
│   ├── DEVELOPMENT_PLAN.md     # Phased development roadmap
│   ├── DM_TESTING_COMPLETE_SUMMARY.md # AI DM test results (95.5% pass)
│   ├── DOCUMENTATION_GUIDE.md  # Meta-guide for all documentation
│   ├── FLUTTER_SETUP.md        # Flutter installation guide
│   ├── FUNCTION_REFERENCE.md   # Critical internal function docs
│   ├── SCENARIO_REFERENCE.md   # Goblin Cave scenario reference
│   ├── THEME_SYSTEM_SPEC.md    # DLC-ready theme architecture
│   ├── UI_DESIGN_SPEC.md       # UI/UX specifications
│   ├── *_REPORT.md             # Various test reports
│   └── archive/                # Superseded/historical docs
├── src/                    # Backend (Flask API)
│   ├── api_server.py       # Flask REST API (main entry point, 40 endpoints)
│   ├── dm_engine.py        # Shared DM logic (prompts, parsing)
│   ├── character.py        # Character system (stats, XP, leveling)
│   ├── combat.py           # Combat system (multi-enemy, surprise)
│   ├── inventory.py        # Items and inventory
│   ├── npc.py              # NPC system (dialogue, shops, relationships)
│   ├── party.py            # Party/companion system
│   ├── quest.py            # Quest tracking system
│   ├── save_system.py      # Save/Load persistence
│   ├── scenario.py         # Adventure scenarios
│   ├── shop.py             # Shop/merchant system
│   └── templates/          # Scenario templates for modders
│       └── SCENARIO_TEMPLATE.py
├── frontend/
│   └── option1-react/      # React + Vite + Tailwind frontend
│       ├── src/
│       │   ├── App.jsx
│       │   ├── components/
│       │   │   ├── CharacterCreation.jsx
│       │   │   ├── GameScreen.jsx
│       │   │   ├── WorldMap.jsx
│       │   │   └── DiceRoller.jsx
│       │   └── store/
│       │       └── gameStore.js   # Zustand state management
│       └── package.json
├── backup/
│   └── legacy/
│       └── game.py         # Archived terminal version
└── tests/                  # 1006 unit tests + security tests
    ├── test_api_integration.py  # API integration tests
    ├── test_character.py        # Character system (26 tests)
    ├── test_combat.py           # Combat mechanics (31 tests)
    ├── test_location.py         # Location system (200 tests)
    ├── test_party.py            # Party system (72 tests)
    ├── test_quest.py            # Quest tracking (57 tests)
    ├── hostile_final.py         # Security stress test (75 tests)
    └── ...
```

---

## API Architecture

The game uses an **API-first architecture**:

| Layer | Technology | Port |
|-------|------------|------|
| Backend API | Flask | 5000 |
| Frontend | React + Vite | 3000 |
| AI Model | Gemini 2.5 Pro | - |
| State | Zustand (React) | - |

### Key API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/scenarios` | GET | List available adventures |
| `/api/classes` | GET | List available character classes |
| `/api/races` | GET | List available character races |
| `/api/game/start` | POST | Create character & start game |
| `/api/game/action/stream` | POST | Send action (SSE streaming) |
| `/api/game/state` | GET | Get current game state |
| `/api/game/save` | POST | Save game |
| `/api/game/load` | POST | Load game |
| `/api/game/saves` | GET | List available saves |
| `/api/game/end` | POST | End session |
| `/api/travel` | POST | Travel to location |
| `/api/locations` | GET | Get available locations |
| `/api/combat/status` | GET | Get combat state |
| `/api/combat/attack` | POST | Attack in combat |
| `/api/combat/defend` | POST | Defend in combat |
| `/api/combat/flee` | POST | Flee from combat |
| `/api/character/levelup` | POST | Level up character |
| `/api/character/rest` | POST | Rest to heal |
| `/api/inventory/use` | POST | Use an item |
| `/api/inventory/equip` | POST | Equip weapon/armor |
| `/api/shop/browse` | GET | Browse shop inventory |
| `/api/shop/buy` | POST | Buy from shop |
| `/api/shop/sell` | POST | Sell to shop |
| `/api/party/view` | GET | View party members |
| `/api/party/recruit` | POST | Recruit companion |
| `/api/quests/list` | GET | List active/completed quests |
| `/api/reputation` | GET | Get NPC relationships |
| `/api/sessions/stats` | GET | Session monitoring |

---

## Features

### ✅ AI Dungeon Master
- **Google Gemini 2.5 Pro** provides intelligent, contextual responses
- **SSE Streaming** - Text appears word-by-word as AI generates
- **Conversation Memory** - Chat history maintained throughout session
- **Character-Aware** - AI knows your race, class, and stats
- **Scene-Aware** - AI follows structured scenario guidance
- **NPC Context** - AI uses correct NPC names from scenarios

### ✅ Character System
- **Character Creation** - Choose name, race (9 options), class (12 options)
- **Stat Rolling** - 4d6-drop-lowest for authentic D&D feel
- **Starting Equipment** - Class-based starting gear
- **Starting Gold** - Random 10-25 gold
- **HP/AC Calculation** - Based on class and constitution/dexterity
- **XP & Leveling** - Level 1-5 with milestone XP (100/300/600/1000)
- **Proficiency Bonus** - Scales with level (+2 to +3)

### ✅ Frontend Features
- **React + Tailwind CSS** - Modern, responsive UI
- **Character Sidebar** - Shows HP, XP, AC, ATK, ability scores, gold
- **Inventory Modal** - View items with stats and descriptions
- **Quest Journal** - Track active/completed quests with objectives
- **World Map** - Interactive location navigation
- **Quick Actions** - One-click buttons for common actions
- **Save/Load** - Persist game progress

### ✅ Combat System
- **D&D 5e Rules** - Initiative, attack rolls, damage
- **Multi-Enemy Combat** - Fight multiple enemies simultaneously
- **Surprise Rounds** - Ambush mechanics with advantage
- **Turn Order** - Initiative-based combat sequence
- **Defend Action** - +2 AC bonus until next turn
- **Flee Option** - Escape combat with DEX check

### ✅ Inventory System
- **Item Types** - Weapons, armor, consumables, quest items
- **Stats Display** - Damage dice, AC bonus, heal amount shown
- **Equipment** - Weapons and armor affect combat
- **Loot Drops** - Random loot from defeated enemies
- **Gold Tracking** - Currency system

### ✅ Scenario System
- **Structured Adventures** - Scenes with objectives and transitions
- **"The Goblin Cave"** - Complete rescue quest with 6 scenes
- **NPC System** - Named NPCs with roles (Bram, Lily, Barkeep, etc.)
- **Quest Tracking** - Objectives with progress percentages

### ✅ Shop System
- **Browse & Buy** - Purchase items from merchant NPCs
- **Sell Loot** - Sell items for 50% of base value
- **Haggle Mechanic** - CHA check for discount
- **Stock Tracking** - Merchants have limited quantities

### ✅ NPC Relationships
- **Disposition System** - NPCs remember how you treat them (-100 to +100)
- **Gift Giving** - Improve relationships with gifts
- **Reputation** - Actions affect how NPCs perceive you
- **Dialogue Variety** - NPCs respond based on relationship

### ✅ Party System
- **Companion Recruitment** - Recruit NPCs to join your party (max 2)
- **Party Combat** - Companions fight alongside you with their own abilities
- **Class Abilities** - Fighter (Shield Wall), Ranger (Hunter's Mark), Rogue (Sneak Attack), Cleric (Heal), Wizard (Magic Missile)
- **Flanking Bonus** - +2 to attack when you and companion target same enemy
- **Party Persistence** - Party saved/loaded with game state

### ✅ Travel System  
- **Travel Menu** - Numbered destination selection with danger indicators
- **Two-Phase Travel** - Approach selection for dangerous areas (sneak, carefully, run)
- **Surprise Mechanics** - Successful stealth grants combat advantage
- **Natural Language** - "go to the tavern", "head north", etc.

### ✅ Rest & Healing
- **Hit Dice System** - Pool = character level, restored on boss kills/level up
- **Short Rest** - Spend Hit Die for 1d6 + CON healing
- **Strategic Resource** - Prevents rest spam, rewards major victories

---

## Testing

### Run API Integration Tests
```bash
python tests/test_api_integration.py
```

### Run All Unit Tests
```bash
pytest tests/ -v
```

### Test Coverage
- **1006 unit tests** across all game systems
- **75 security tests** (hostile player testing)
- All 16 identified vulnerabilities fixed

---

## Development

### VS Code Tasks
The workspace includes predefined tasks:
- **🎮 Start Backend (Flask)** - Start API server on port 5000
- **🌐 Start Frontend (React)** - Start dev server on port 3000
- **🚀 Start Full Stack** - Start both simultaneously

### Key Files
- `src/api_server.py` - Main Flask application
- `src/dm_engine.py` - DM system prompt and parsing logic
- `frontend/option1-react/src/store/gameStore.js` - Frontend state
- `frontend/option1-react/src/components/GameScreen.jsx` - Main game UI

---

## Credits
- AI: Google Gemini 2.5 Pro
- Game System: D&D 5e (simplified)
- Frontend: React + Vite + Tailwind CSS
- Backend: Python Flask

---

## License
This project is for educational purposes.
