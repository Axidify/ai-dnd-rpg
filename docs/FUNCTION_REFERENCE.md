# Function Reference - Critical Internal Functions

**Last Updated:** December 25, 2025

This document describes the most critical internal functions that are frequently modified and prone to causing breaking changes. Always check this document before modifying these functions.

---

## Table of Contents

1. [Session Initialization Flow](#session-initialization-flow)
2. [Location System Functions](#location-system-functions)
3. [Party System Functions](#party-system-functions)
4. [API Endpoint Response Formats](#api-endpoint-response-formats)
5. [Data Flow Diagrams](#data-flow-diagrams)
6. [Breaking Change Checklist](#breaking-change-checklist)

---

## Session Initialization Flow

### `/api/game/start` - Game Startup Sequence

**File:** `src/api_server.py`, Function: `start_game()` (lines ~700-900)

```
POST /api/game/start
    │
    ├─→ Create GameSession object
    │     • session.character = Character(name, class, race)
    │     • session.scenario = ScenarioManager()
    │     • session.npc_manager = NPCManager()
    │     • session.quest_manager = QuestManager()
    │     • session.party = Party()
    │     • session.location_manager = LocationManager() ← EMPTY initially
    │
    ├─→ If scenario_id provided:
    │     │
    │     ├─→ session.scenario.start_scenario(scenario_id)
    │     │     └─→ Creates Scenario, calls scenario.start()
    │     │         └─→ Calls _setup_scene_locations()
    │     │             └─→ Sets location_manager.current_location_id
    │     │
    │     ├─→ scenario = session.scenario.active_scenario
    │     │
    │     ├─→ session.npc_manager = scenario.npc_manager ← REPLACES empty one
    │     │
    │     ├─→ session.location_manager = scenario.location_manager ← REPLACES empty one
    │     │     └─→ CRITICAL: Must sync session.current_location + session.current_location_id
    │     │         current_loc = session.location_manager.get_current_location()
    │     │         session.current_location = current_loc.name
    │     │         session.current_location_id = current_loc.id
    │     │
    │     └─→ session.choice_manager = scenario.choice_manager
    │
    └─→ Return session_id, opening_narration, character data
```

### Critical Variables Set During Startup

| Variable | Type | Purpose | Set By |
|----------|------|---------|--------|
| `session.location_manager` | LocationManager | Manages locations for travel | `scenario.location_manager` |
| `session.current_location` | str | Display name of current location | Synced from location_manager |
| `session.current_location_id` | str | ID for location lookups | Synced from location_manager |
| `session.npc_manager` | NPCManager | Manages NPCs for the scenario | `scenario.npc_manager` |

**⚠️ Common Bug Pattern:**
If `session.current_location_id` is not set but `session.location_manager` is, the World Map will show "No map data available" because `/api/locations` checks `session.location_manager` for data but uses `session.current_location_id` for context.

---

## Location System Functions

### `LocationManager.set_current_location(location_id)`

**File:** `src/scenario.py`, lines ~1437-1447

Sets the current location and marks it as visited.

```python
def set_current_location(self, location_id: str) -> Optional[Location]:
    if location_id in self.locations:
        self.current_location_id = location_id
        location = self.locations[location_id]
        location.visit_count += 1
        if not location.visited:
            location.visited = True
        return location
    return None  # Returns None if location_id not found
```

**⚠️ Callers must check return value for None!**

### `LocationManager.get_current_location()`

**File:** `src/scenario.py`, lines ~1449-1453

Returns the current Location object or None.

```python
def get_current_location(self) -> Optional[Location]:
    if self.current_location_id:
        return self.locations.get(self.current_location_id)
    return None
```

### `LocationManager.get_exits()`

**File:** `src/scenario.py`, lines ~1455-1480

Returns filtered dict of available exits from current location.

Filters out:
- Exits to locations not in `available_location_ids`
- Hidden locations that haven't been discovered

---

## Party System Functions

### `/api/party/view` Response Format

**File:** `src/api_server.py`, Function: `party_view()`

**⚠️ CRITICAL: Frontend expects specific field structure!**

```python
# CORRECT format (after fix):
{
    'name': member.name,
    'hp': member.current_hp,       # INTEGER
    'max_hp': member.max_hp,       # INTEGER
    'role': member.role,
    'status': member.status,
    'level': member.level,
    ...
}

# WRONG format (caused bug):
{
    'name': member.name,
    'hp': f"{member.current_hp}/{member.max_hp}",  # STRING - Frontend couldn't parse!
    ...
}
```

**Frontend expects:**
- `hp` → number (current HP)
- `max_hp` → number (maximum HP)

**NOT:**
- `hp` → string like "24/24" (causes display issues)

---

## API Endpoint Response Formats

### `/api/locations` Response

**File:** `src/api_server.py`, Function: `get_locations()`

```json
{
  "success": true,
  "current_location": {
    "id": "tavern_main",
    "name": "The Rusty Dragon - Main Room",
    "map_x": 0.15,
    "map_y": 0.08,
    "map_icon": "🍺",
    "map_region": "village"
  },
  "destinations": [
    {
      "id": "tavern_bar",
      "name": "The Rusty Dragon - Bar",
      "exit_name": "bar",
      "description": "A worn wooden bar...",
      "visited": false,
      "map_x": 0.15,
      "map_y": 0.02,
      "map_icon": "🍻"
    }
  ],
  "all_locations": [
    {
      "id": "tavern_main",
      "name": "The Rusty Dragon - Main Room",
      "map_x": 0.15,
      "map_y": 0.08,
      "map_icon": "🍺",
      "map_label": "Rusty Dragon",
      "map_region": "village",
      "visited": true,
      "hidden": false,
      "is_current": true,
      "reachable": false
    }
    // ... all other locations
  ]
}
```

**Frontend WorldMap.jsx expects:**
- `data.all_locations` - array of all map locations
- `data.current_location` - current location object

---

## Data Flow Diagrams

### World Map Data Flow

```
Frontend WorldMap.jsx
    │
    ├─→ Opens WorldMap modal
    │     └─→ loadMapData() called
    │           └─→ getDestinations() from gameStore.js
    │                 └─→ GET /api/locations?session_id=xxx
    │                       │
    │                       ▼
    │             api_server.py get_locations()
    │                       │
    │                       ├─→ Check session.location_manager exists
    │                       │
    │                       ├─→ location = session.location_manager.get_current_location()
    │                       │   (Returns None if current_location_id not set!)
    │                       │
    │                       ├─→ exits = session.location_manager.get_exits()
    │                       │
    │                       ├─→ Build all_locations array from session.location_manager.locations
    │                       │
    │                       └─→ Return JSON with all_locations, current_location, destinations
    │
    ├─→ setLocations(data.all_locations || [])
    │     └─→ If empty, shows "No map data available"
    │
    └─→ setCurrentLocation(data.current_location)
```

### Party View Data Flow

```
Frontend PartyMenu.jsx
    │
    └─→ GET /api/party/view?session_id=xxx
          │
          ▼
    api_server.py party_view()
          │
          ├─→ Get session.party
          │
          ├─→ For each member in party:
          │     └─→ Build member dict with hp, max_hp, name, etc.
          │
          └─→ Return JSON with members array
          │
          ▼
    Frontend receives:
    {
      "members": [
        {"name": "Marcus", "hp": 24, "max_hp": 24, ...}
      ]
    }
          │
          └─→ Renders HP bar with hp/max_hp
```

---

## Breaking Change Checklist

Before modifying any of these functions, check:

### API Response Changes

- [ ] Does the frontend component expect specific field names?
- [ ] Are field types (int vs string) correct for frontend parsing?
- [ ] Is the response structure documented in API_DOCUMENTATION.md?

### Session/Location Changes

- [ ] Is `session.current_location_id` being set when location changes?
- [ ] Is `session.current_location` (display name) being synced?
- [ ] Is `session.location_manager` assigned before calling its methods?

### Party Changes

- [ ] Are hp and max_hp returned as separate integers?
- [ ] Are all expected fields present in the member dict?

### General

- [ ] Did you run the unit tests? (`pytest tests/ -v`)
- [ ] Did you check the frontend component that consumes this data?
- [ ] Did you update API_DOCUMENTATION.md if response format changed?

---

## Files Most Likely to Cause Breakage

| File | Risk Area | Impact |
|------|-----------|--------|
| `src/api_server.py` | Response formats | Frontend display bugs |
| `src/scenario.py` | Location/Scene initialization | World Map, Travel |
| `src/dm_engine.py` | AI response parsing | Combat, Items, Gold |
| `gameStore.js` | API call handling | All frontend features |

---

## Quick Debug Commands

Check if session has location_manager:
```bash
curl "http://localhost:5000/api/locations?session_id=YOUR_SESSION" | jq
```

Check party member format:
```bash
curl "http://localhost:5000/api/party/view?session_id=YOUR_SESSION" | jq
```

View recent logs:
```bash
Get-Content notes.log -Tail 100
```
