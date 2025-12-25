# AI RPG API Documentation

**Version:** 1.0.0  
**Base URL:** `http://localhost:5000/api`  
**Authentication:** Session-based via `X-Session-ID` header  
**Last Updated:** December 25, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Endpoints](#endpoints)
   - [Health & Status](#health--status)
   - [Game Management](#game-management)
   - [Character](#character)
   - [Combat](#combat)
   - [Inventory](#inventory)
   - [Shop](#shop)
   - [Party](#party)
   - [Quests](#quests)
   - [Location & Travel](#location--travel)
   - [Reputation](#reputation)
   - [Moral Choices](#moral-choices)
4. [WebSocket/Streaming](#streaming)
5. [Error Handling](#error-handling)

---

## Overview

The AI RPG API provides a REST interface for the text-based D&D RPG game with an AI Dungeon Master.

### Key Features
- **40 API endpoints** covering all game functionality
- **Session-based state management** for multiple concurrent games
- **Streaming responses** for real-time AI narration
- **JSON request/response format**

---

## Authentication

All game endpoints require a session ID passed via the `X-Session-ID` header.

```http
X-Session-ID: your-session-id-here
```

Session IDs are returned by the `/api/game/start` endpoint when starting a new game.

---

## Endpoints

### Health & Status

#### GET /api/health
Check API server health.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-12-25T10:00:00.000000",
  "version": "1.0.0"
}
```

#### GET /api/sessions/stats
Get active session statistics.

**Response:**
```json
{
  "active_sessions": 5,
  "sessions": [
    {
      "session_id": "abc123",
      "character_name": "Thorin",
      "character_level": 3,
      "current_location": "forest_clearing"
    }
  ]
}
```

---

### Game Management

#### POST /api/game/start
Start a new game session.

**Request:**
```json
{
  "character_name": "Thorin",
  "character_class": "Fighter",
  "character_race": "Dwarf",
  "scenario_id": "goblin_cave"
}
```

**Response:**
```json
{
  "session_id": "abc123...",
  "message": "Welcome, Thorin the Dwarf Fighter!",
  "character": { ... },
  "location": { ... }
}
```

#### POST /api/game/action
Send a player action and get DM response.

**Headers:** `X-Session-ID: <session_id>`

**Request:**
```json
{
  "action": "I look around the tavern"
}
```

**Response:**
```json
{
  "message": "You see a cozy tavern...",
  "in_combat": false,
  "location_changed": false
}
```

#### POST /api/game/action/stream
Send action with streaming response.

**Headers:** `X-Session-ID: <session_id>`

**Request:**
```json
{
  "action": "I search for treasure"
}
```

**Response:** Server-Sent Events (SSE) stream
```
data: {"chunk": "You "}
data: {"chunk": "carefully "}
data: {"chunk": "search..."}
data: {"done": true, "full_response": "..."}
```

#### GET /api/game/state
Get current game state.

**Headers:** `X-Session-ID: <session_id>`

**Response:**
```json
{
  "character": { ... },
  "location": { ... },
  "in_combat": false,
  "quests": [ ... ]
}
```

#### POST /api/game/roll
Roll dice with modifiers.

**Headers:** `X-Session-ID: <session_id>`

**Request:**
```json
{
  "dice": "1d20",
  "modifier": 5,
  "purpose": "Stealth check"
}
```

**Response:**
```json
{
  "roll": 15,
  "modifier": 5,
  "total": 20,
  "dice": "1d20"
}
```

#### POST /api/game/save
Save current game.

**Headers:** `X-Session-ID: <session_id>`

**Request:**
```json
{
  "slot": 1,
  "description": "Before the boss fight"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Game saved to slot 1",
  "filepath": "saves/save_1.json"
}
```

#### POST /api/game/load
Load a saved game.

**Headers:** `X-Session-ID: <session_id>`

**Request:**
```json
{
  "filepath": "saves/save_1.json"
}
```

**Response:**
```json
{
  "success": true,
  "character": { ... },
  "location": { ... }
}
```

#### GET /api/game/saves
List all saved games.

**Response:**
```json
{
  "saves": [
    {
      "filepath": "saves/save_1.json",
      "character_name": "Thorin",
      "character_level": 3,
      "character_class": "Fighter",
      "description": "Before the boss fight"
    }
  ]
}
```

#### POST /api/game/end
End current game session.

**Headers:** `X-Session-ID: <session_id>`

**Response:**
```json
{
  "success": true,
  "message": "Session ended"
}
```

---

### Character

#### GET /api/game/character
Get detailed character information.

**Headers:** `X-Session-ID: <session_id>`

**Response:**
```json
{
  "name": "Thorin",
  "race": "Dwarf",
  "char_class": "Fighter",
  "level": 3,
  "hp": 25,
  "max_hp": 28,
  "stats": {
    "STR": 16, "DEX": 12, "CON": 14,
    "INT": 10, "WIS": 11, "CHA": 8
  },
  "experience": 350,
  "gold": 75,
  "inventory": [ ... ],
  "equipped": { ... }
}
```

#### POST /api/character/levelup
Level up the character.

**Headers:** `X-Session-ID: <session_id>`

**Response:**
```json
{
  "success": true,
  "new_level": 4,
  "hp_increase": 2,
  "message": "You are now level 4!"
}
```

#### POST /api/character/rest
Take a short or long rest.

**Headers:** `X-Session-ID: <session_id>`

**Request:**
```json
{
  "rest_type": "short"
}
```

**Response:**
```json
{
  "success": true,
  "hp_restored": 8,
  "current_hp": 28,
  "max_hp": 28,
  "hit_dice_used": 1
}
```

---

### Reference Data

#### GET /api/classes
Get available character classes.

**Response:**
```json
{
  "classes": ["Fighter", "Rogue", "Wizard", "Cleric", "Ranger"]
}
```

#### GET /api/races
Get available character races.

**Response:**
```json
{
  "races": ["Human", "Elf", "Dwarf", "Halfling", "Half-Orc"]
}
```

#### GET /api/scenarios
Get available scenarios.

**Response:**
```json
{
  "scenarios": [
    {
      "id": "goblin_cave",
      "name": "The Goblin Cave",
      "description": "Rescue Lily from the goblins"
    }
  ]
}
```

---

### Combat

#### GET /api/combat/status
Get current combat status.

**Headers:** `X-Session-ID: <session_id>`

**Response:**
```json
{
  "in_combat": true,
  "turn_order": [
    { "name": "Thorin", "initiative": 18, "is_player": true },
    { "name": "Goblin", "initiative": 12, "hp": 5, "max_hp": 7 }
  ],
  "current_turn": "Thorin",
  "round": 1
}
```

#### POST /api/combat/attack
Attack an enemy.

**Headers:** `X-Session-ID: <session_id>`

**Request:**
```json
{
  "target": 1
}
```

**Response:**
```json
{
  "attack_roll": 18,
  "hit": true,
  "damage": 8,
  "enemy_hp": 0,
  "enemy_defeated": true,
  "combat_ended": true,
  "victory": true,
  "xp_gained": 25
}
```

#### POST /api/combat/defend
Take defensive stance.

**Headers:** `X-Session-ID: <session_id>`

**Response:**
```json
{
  "success": true,
  "ac_bonus": 2,
  "message": "You take a defensive stance (+2 AC)"
}
```

#### POST /api/combat/flee
Attempt to flee combat.

**Headers:** `X-Session-ID: <session_id>`

**Response:**
```json
{
  "success": true,
  "fled": true,
  "message": "You successfully flee from combat!"
}
```

---

### Inventory

#### POST /api/inventory/use
Use an item from inventory.

**Headers:** `X-Session-ID: <session_id>`

**Request:**
```json
{
  "item_id": "healing_potion"
}
```

**Response:**
```json
{
  "success": true,
  "effect": "Restored 8 HP",
  "new_hp": 25
}
```

#### POST /api/inventory/equip
Equip an item.

**Headers:** `X-Session-ID: <session_id>`

**Request:**
```json
{
  "item_id": "longsword"
}
```

**Response:**
```json
{
  "success": true,
  "equipped": {
    "weapon": "longsword"
  }
}
```

---

### Shop

#### GET /api/shop/browse
Browse shop inventory at current location.

**Headers:** `X-Session-ID: <session_id>`

**Response:**
```json
{
  "merchant": "Gavin the Blacksmith",
  "items": [
    {
      "id": "healing_potion",
      "name": "Healing Potion",
      "price": 50,
      "stock": 5
    }
  ],
  "player_gold": 75
}
```

#### POST /api/shop/buy
Purchase an item.

**Headers:** `X-Session-ID: <session_id>`

**Request:**
```json
{
  "item_id": "healing_potion",
  "quantity": 2
}
```

**Response:**
```json
{
  "success": true,
  "item": "Healing Potion",
  "quantity": 2,
  "total_cost": 100,
  "remaining_gold": 75
}
```

#### POST /api/shop/sell
Sell an item.

**Headers:** `X-Session-ID: <session_id>`

**Request:**
```json
{
  "item_id": "goblin_dagger"
}
```

**Response:**
```json
{
  "success": true,
  "item": "Goblin Dagger",
  "gold_received": 5,
  "new_gold": 80
}
```

---

### Party

#### GET /api/party/view
View current party members.

**Headers:** `X-Session-ID: <session_id>`

**Response:**
```json
{
  "party": [
    {
      "id": "elira_ranger",
      "name": "Elira",
      "class": "Ranger",
      "level": 2,
      "hp": 18,
      "max_hp": 18
    }
  ],
  "available_recruits": [
    {
      "id": "marcus_mercenary",
      "name": "Marcus",
      "class": "Fighter",
      "location": "tavern_main",
      "requirements": "20 gold OR CHA DC 15"
    }
  ]
}
```

#### POST /api/party/recruit
Recruit an NPC to the party.

**Headers:** `X-Session-ID: <session_id>`

**Request:**
```json
{
  "npc_id": "marcus_mercenary",
  "method": "gold"
}
```

**Response:**
```json
{
  "success": true,
  "recruited": "Marcus",
  "party_size": 2,
  "gold_spent": 20
}
```

---

### Quests

#### GET /api/quests/list
List all quests.

**Alias:** `GET /api/quests`

**Headers:** `X-Session-ID: <session_id>`

**Response:**
```json
{
  "quests": [
    {
      "id": "rescue_lily_main",
      "name": "Rescue Lily",
      "quest_type": "MAIN",
      "status": "ACTIVE",
      "objectives": [
        {
          "id": "reach_cave",
          "description": "Reach the goblin cave",
          "completed": true
        },
        {
          "id": "find_lily",
          "description": "Find Lily",
          "completed": false
        }
      ],
      "rewards": {
        "gold": 100,
        "xp": 100
      }
    }
  ]
}
```

#### POST /api/quests/complete
Manually complete a quest (for testing).

**Headers:** `X-Session-ID: <session_id>`

**Request:**
```json
{
  "quest_id": "rescue_lily_main"
}
```

**Response:**
```json
{
  "success": true,
  "rewards_granted": {
    "gold": 100,
    "xp": 100
  }
}
```

---

### Location & Travel

#### GET /api/locations
Get all available locations.

**Headers:** `X-Session-ID: <session_id>`

**Response:**
```json
{
  "current_location": {
    "id": "tavern_main",
    "name": "The Rusty Dragon Tavern",
    "description": "A warm and welcoming tavern...",
    "exits": ["village_square", "tavern_rooms"]
  },
  "available_locations": [
    { "id": "village_square", "name": "Village Square" },
    { "id": "forest_path", "name": "Forest Path", "danger_level": "low" }
  ]
}
```

#### POST /api/travel
Travel to a new location.

**Headers:** `X-Session-ID: <session_id>`

**Request:**
```json
{
  "destination": "forest_path",
  "approach": "sneak"
}
```

**Response:**
```json
{
  "success": true,
  "new_location": { ... },
  "approach_result": {
    "skill_check": "Stealth",
    "roll": 18,
    "success": true,
    "surprise": true
  },
  "encounter": null
}
```

#### GET /api/location/scan
Scan current location for items, NPCs, and exits.

**Headers:** `X-Session-ID: <session_id>`

**Response:**
```json
{
  "location": "tavern_main",
  "items": ["torch", "old_note"],
  "npcs": ["Barkeep", "Old Bram"],
  "exits": {
    "north": "village_square",
    "upstairs": "tavern_rooms"
  }
}
```

---

### Reputation

#### GET /api/reputation
Get reputation with all NPCs.

**Headers:** `X-Session-ID: <session_id>`

**Response:**
```json
{
  "npcs": [
    {
      "npc_id": "old_bram",
      "name": "Old Bram",
      "disposition": 25,
      "level": "friendly",
      "label": "🟢 Friendly (+25)",
      "can_trade": true,
      "price_modifier": 0.9,
      "role": "quest_giver",
      "location": "tavern_main"
    }
  ],
  "summary": {
    "total": 8,
    "hostile": 0,
    "unfriendly": 1,
    "neutral": 3,
    "friendly": 3,
    "trusted": 1
  }
}
```

#### GET /api/reputation/{npc_id}
Get detailed reputation with specific NPC.

**Headers:** `X-Session-ID: <session_id>`

**Response:**
```json
{
  "npc_id": "old_bram",
  "name": "Old Bram",
  "description": "An elderly farmer...",
  "disposition": 25,
  "level": "friendly",
  "label": "🟢 Friendly (+25)",
  "price_modifier": 0.9,
  "available_skill_checks": [
    {
      "id": "upfront_payment",
      "skill": "Persuasion",
      "dc": 14,
      "description": "Convince Bram to pay 25g upfront"
    }
  ]
}
```

---

### Moral Choices

#### GET /api/choices/available
Get currently available moral choices.

**Headers:** `X-Session-ID: <session_id>`

**Response:**
```json
{
  "choices": [
    {
      "id": "goblin_prisoner",
      "prompt": "A captured goblin begs for its life. What do you do?",
      "type": "MORAL",
      "context": "You've captured a goblin scout...",
      "options": [
        {
          "id": "spare",
          "text": "Spare the goblin and let it go",
          "consequence_hint": "May gain information"
        },
        {
          "id": "kill",
          "text": "Execute the goblin",
          "consequence_hint": "No mercy for monsters"
        },
        {
          "id": "interrogate",
          "text": "Interrogate for information",
          "requirements": { "skill": "Intimidation", "dc": 12 }
        }
      ]
    }
  ]
}
```

#### POST /api/choices/select
Make a moral choice.

**Headers:** `X-Session-ID: <session_id>`

**Request:**
```json
{
  "choice_id": "goblin_prisoner",
  "option_id": "spare"
}
```

**Response:**
```json
{
  "success": true,
  "outcome": {
    "narrative": "You release the goblin...",
    "reputation_changes": { "goblin_tribe": +10 },
    "flag_set": "spared_goblin"
  }
}
```

#### GET /api/choices/history
Get history of choices made.

**Headers:** `X-Session-ID: <session_id>`

**Response:**
```json
{
  "choices_made": [
    {
      "choice_id": "goblin_prisoner",
      "option_selected": "spare",
      "timestamp": "2025-12-25T10:30:00"
    }
  ]
}
```

#### GET /api/choices/ending
Get potential ending based on choices.

**Headers:** `X-Session-ID: <session_id>`

**Response:**
```json
{
  "alignment_trend": "good",
  "key_choices": ["spared_goblin", "saved_lily"],
  "predicted_ending": "hero"
}
```

---

## Streaming

The `/api/game/action/stream` endpoint uses Server-Sent Events (SSE) for streaming responses.

### Event Format
```
event: message
data: {"chunk": "partial text..."}

event: message
data: {"done": true, "full_response": "complete text..."}
```

### JavaScript Example
```javascript
const eventSource = new EventSource('/api/game/action/stream', {
  headers: { 'X-Session-ID': sessionId }
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.done) {
    console.log('Complete:', data.full_response);
    eventSource.close();
  } else {
    console.log('Chunk:', data.chunk);
  }
};
```

---

## Error Handling

All errors return a consistent format:

```json
{
  "error": "Error message description",
  "code": "ERROR_CODE"
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `SESSION_NOT_FOUND` | 404 | Invalid or expired session ID |
| `INVALID_REQUEST` | 400 | Missing or invalid parameters |
| `NOT_IN_COMBAT` | 400 | Combat action outside of combat |
| `INSUFFICIENT_GOLD` | 400 | Not enough gold for purchase |
| `ITEM_NOT_FOUND` | 404 | Item not in inventory |
| `LOCATION_BLOCKED` | 400 | Cannot travel to location |
| `NPC_NOT_FOUND` | 404 | NPC not at current location |

### HTTP Status Codes

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 400 | Bad Request |
| 404 | Not Found |
| 500 | Server Error |

---

## Rate Limits

Currently no rate limits are enforced. For production deployment, consider:
- 60 requests/minute per session for general endpoints
- 10 requests/minute for AI-powered endpoints (action, action/stream)

---

*API Documentation generated December 25, 2025*
