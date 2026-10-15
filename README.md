# By Lamplight — AI Text RPG

A text-based tabletop-style fantasy RPG where an LLM (Google Gemini, or any
OpenAI-compatible server such as vLLM) acts as the Game Master. A Flask API
runs the game rules; a React frontend renders the story, map and character.

The rules engine, not the LLM, decides when you roll and what the result is:
each action goes through an **arbiter** (keyword rules, then a JSON-only LLM
call) that picks the skill check and DC, the dice are rolled in code, and the
**narrator** LLM only describes the outcome. Rewards and other effects come from
control tags in the DM's reply (`[GOLD: 10]`, `[ITEM: torch]`, ...), which are
applied by the server and stripped before the player sees the text.

---

## Quick start

Prerequisites: Python 3.10+, Node.js 18+, and either a Gemini API key or an
OpenAI-compatible LLM server.

```bash
# Backend
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/macOS
pip install -r requirements.txt
cp .env.example .env            # then set GOOGLE_API_KEY, or the VLLM_* settings
python src/api_server.py        # http://127.0.0.1:5000

# Frontend (second terminal)
cd frontend/option1-react
npm install
npm run dev                     # http://localhost:3000 (proxies /api to :5000)
```

The server binds to `127.0.0.1` with debug off by default. The API has no
authentication, so only set `API_HOST=0.0.0.0` on a network you trust, and never
enable `DEBUG` on a reachable host. See `.env.example` for all settings.

---

## Project layout

```
src/
  api_server.py       Flask app: routes, sessions, combat/shop/travel endpoints
  turn_service.py     One player turn: guards → arbiter → (narrator) → mechanics
  dm_arbiter.py       Decides whether an action needs a skill check
  dm_scene.py         Scene rules (free first look, roll-outcome fallbacks)
  dm_engine.py        DM system prompt, control-tag parsing, skill rolls
  llm_client.py       Gemini / vLLM behind one chat interface
  game_mechanics.py   Defeat, hostile-action combat gate, travel pipeline
  text_match.py       Whole-word keyword matching used by every rule
  character.py  combat.py  inventory.py  party.py  quest.py  npc.py  shop.py
  scenario.py         Scene / location / world-map engine
  scenario_loader.py  Loads scenario content from data/scenarios/
  data_codec.py       Dataclass <-> plain-data conversion for content files
  save_system.py      Save/load (JSON files in saves/)

data/scenarios/goblin_cave/   The Goblin Cave adventure (YAML content)
frontend/option1-react/       React + Vite + Tailwind + Zustand frontend
tests/                        Offline pytest suite
tests/live/                   Scripts needing a real LLM or running server
docs/                         CHANGELOG, scenario format; docs/archive/ is historical
```

---

## Adding a scenario

Create `data/scenarios/<your_id>/` with `scenario.yaml`, `locations.yaml`,
`npcs.yaml`, `quests.yaml` and `shops.yaml`. It is picked up automatically, with
no code changes. See [docs/SCENARIOS.md](docs/SCENARIOS.md) and use
`data/scenarios/goblin_cave/` as the reference.

---

## What's in the game

- **Characters:** 9 races and 12 classes, 4d6-drop-lowest stats, class starting gear,
  XP levels 1–5.
- **Skill checks:** arbiter-decided with a d20 + modifier vs DC. Failed social checks
  have consequences (retries with the same approach are blocked, and three failures
  end the game).
- **Combat:** structured turns with initiative, multiple enemies, surprise, attack /
  defend / flee, companion attacks, and loot and XP on victory. Hostile actions
  ("I attack the guard") start combat instead of free-form narration.
- **World:** locations with exits, conditional exits (items, skills, objectives),
  hidden locations, location events, random encounters and an interactive map.
- **Inventory and shops:** equip, use and buy/sell at merchants.
- **Quests and party:** quest journal with objectives; recruit up to 2 companions.
- **Rest:** short rests spend hit dice, which are restored on level-up and boss kills.
- **Save/load:** 3 save slots in the UI, including scenario, quest, party and location state.

Engine code exists for a few features the web game doesn't expose yet:
shop haggling, NPC gifts, companion class abilities and flanking, and
"approach" choices for dangerous travel.

---

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/classes`, `/api/races`, `/api/scenarios` | Character and adventure options |
| POST | `/api/game/start` | Create a character and start a session |
| POST | `/api/game/action/stream` | Player action, streamed as Server-Sent Events |
| POST | `/api/game/action` | Player action, single JSON response |
| GET | `/api/game/state`, `/api/game/character` | Current state |
| POST | `/api/game/roll` | Manual dice roll |
| POST | `/api/game/save`, `/api/game/load` · GET `/api/game/saves` | Saves |
| POST | `/api/game/end` | End a session |
| GET | `/api/locations`, `/api/location/scan` · POST `/api/travel` | Travel and map |
| GET | `/api/combat/status` · POST `/api/combat/attack`, `/defend`, `/flee` | Combat |
| POST | `/api/character/levelup`, `/api/character/rest` | Character |
| POST | `/api/inventory/use`, `/api/inventory/equip` | Inventory |
| GET | `/api/shop/browse` · POST `/api/shop/buy`, `/api/shop/sell` | Shops |
| GET | `/api/party/view` · POST `/api/party/recruit` | Party |
| GET | `/api/quests/list` · POST `/api/quests/complete` | Quests |
| GET | `/api/reputation` | NPC relationships |
| GET | `/api/sessions/stats` | Session monitoring |

Sessions are kept in memory and expire after 60 minutes of inactivity.

---

## Testing

```bash
pip install -r requirements-dev.txt
pytest                 # offline suite; never calls an LLM
ruff check src tests   # syntax errors and undefined names
```

CI (`.github/workflows/ci.yml`) runs both, plus the frontend build.

`tests/live/` holds DM-behaviour and security scripts that need a configured LLM
and/or a running API server. Run them directly, e.g.
`python tests/live/test_dm_adversarial.py`, or include them with `pytest --live`.

---

## License

This project is for educational purposes.
