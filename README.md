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
├── DEVELOPMENT_PLAN.md     # Phased development roadmap
├── README.md               # This file
├── requirements.txt        # Python dependencies
├── tasksync.md             # TaskSync protocol
└── src/
    ├── __init__.py         # Package initializer
    └── game.py             # Main game logic
```

---

## Current Features (Phase 1.1)

### ✅ Simple Chat Loop
- **AI Dungeon Master**: Google Gemini 2.0 Flash provides intelligent, contextual responses
- **Conversation Memory**: Chat history maintained throughout session
- **Immersive Narration**: AI creates detailed scenes, NPCs, and storylines
- **Interactive Gameplay**: Players type actions, AI responds naturally
- **Configurable**: Model and API key stored in `.env` file

### How It Works
1. Player launches the game
2. AI DM sets the scene with an opening narrative
3. Player types actions (e.g., "I search the room", "I talk to the innkeeper")
4. AI responds with story progression
5. Loop continues until player types "quit"

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.14 |
| AI Provider | Google Gemini (gemini-2.0-flash) |
| AI Library | google-generativeai |
| Config | python-dotenv |

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

## Game Commands

| Command | Action |
|---------|--------|
| Any text | Send action to DM |
| `quit`, `exit`, `q` | Exit the game |

---

## Files Description

### src/game.py
Main game file containing:
- `DM_SYSTEM_PROMPT`: Instructions that define AI behavior as a Dungeon Master
- `create_client()`: Initializes Gemini API with configuration
- `get_dm_response()`: Sends player input and receives AI response
- `main()`: Game loop handling input/output

### requirements.txt
```
google-generativeai>=0.8.0
python-dotenv>=1.0.0
```

### .env.example
Template for creating your `.env` file with required API configuration.

---

## Roadmap

See [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) for full roadmap including:
- Phase 1: Core Foundation (1.1 ✅ Complete)
- Phase 2: Game Mechanics (dice, combat, inventory)
- Phase 3: World & Persistence (save/load, locations, NPCs)
- Phase 4: Advanced AI Features (memory, dynamic generation)
- Phase 5: Backend API
- Phase 6: Mobile App

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

This is an incremental development project. Each phase builds on the previous one. See `DEVELOPMENT_PLAN.md` for what's next.

---

## License

Private project - All rights reserved.
