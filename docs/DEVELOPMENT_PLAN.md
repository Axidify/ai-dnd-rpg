# AI D&D Text RPG - Development Plan

**Project:** Text-based D&D RPG with AI Dungeon Master  
**Status:** Phase 2 Complete - Ready for Phase 3  
**Created:** December 15, 2025  

---

## Project Overview

A text-based role-playing game where an AI acts as the Dungeon Master, narrating adventures, managing encounters, and responding to player actions in real-time. Built incrementally with testing at each phase.

---

## Development Phases

### Phase 1: Core Foundation ✅ Complete
**Goal:** Get a working conversation loop with basic game state

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 1.1 | Simple Chat Loop | Python script with player input → AI response loop | ✅ Complete |
| 1.2 | Basic Character Sheet | Name, class, HP, stats (STR, DEX, CON, INT, WIS, CHA) | ✅ Complete |
| 1.3 | Starting Scenario | Scene system with structured adventure | ✅ Complete |

**Success Criteria:**
- [x] Player can chat with AI DM
- [x] Player has a character with viewable stats
- [x] Player can take basic actions (look, move, talk)
- [x] Structured adventure with scene progression

---

### Phase 2: Core Game Mechanics ✅ Complete
**Goal:** Add actual D&D gameplay rules

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 2.1 | Dice Rolling System | d4, d6, d8, d10, d12, d20 with modifiers | ✅ Complete |
| 2.2 | Skill Checks | AI requests rolls, player rolls, outcome affects story | ✅ Complete |
| 2.3 | Combat System | Turn-based, HP tracking, attack/defend/flee actions | ✅ Complete |
| 2.4 | Combat Integration | Integrate combat into main game with AI triggers | ✅ Complete |
| 2.5 | Inventory System | Pick up items, use items, equip gear | ✅ Complete |
| 2.5.1 | Multi-Enemy Combat | Fight multiple enemies with proper turn order | ✅ Complete |
| 2.5.2 | Surprise & Advantage | Ambush attacks with surprise round and advantage | ✅ Complete |
| 2.6 | Leveling System | Simplified XP/milestone progression (cap at level 5) | ✅ Complete |

**Success Criteria:**
- [x] Player can roll dice with proper modifiers
- [x] Skill checks affect story outcomes
- [x] Player can fight an enemy and win/lose
- [x] Combat works seamlessly in main game
- [x] Player can collect and use items
- [x] Player can fight multiple enemies simultaneously
- [x] Player can ambush enemies with surprise round
- [x] Player can level up and gain abilities

**Leveling System Features (2.6):**
```
- Level cap: 5
- XP Thresholds: 0 → 100 → 300 → 600 → 1000
- Commands: 'xp' (view progress), 'levelup' (advance)
- DM awards XP with [XP: amount] or [XP: amount | reason]
- Milestone XP: minor=25, major=50, boss=100, adventure=150
- Benefits: +2 HP/level, stat boosts at L2/L4, abilities at L3/L5
- Proficiency bonus: +2 (L1-4), +3 (L5)
```

**Multi-Enemy Combat Features (2.5.1):**
```
- DM triggers with [COMBAT: enemy1, enemy2, enemy3]
- All enemies roll initiative individually
- Proper D&D turn order (sorted by initiative)
```

**Surprise & Advantage Features (2.5.2):**
```
- DM triggers with [COMBAT: enemy1, enemy2 | SURPRISE]
- Surprised enemies skip their turn in Round 1
- Player gets ADVANTAGE on first attack (2d20, take higher)
- Attack shows both dice: [8, 15→15]+5 = 20
```
- Target selection: "attack 1", "attack 2" or just "1", "2"
- Defend bonus (+2 AC) persists until player's next turn
- Victory when all enemies defeated
- Loot drops from each defeated enemy
```

**Skill Check System Features (2.2):**
```
- AI requests with [ROLL: SkillName DC X]
- Automatic stat modifier application (STR, DEX, etc.)
- Display: 🎲 Stealth (DEX): [14]+3 = 17 vs DC 15 = ✅ SUCCESS
- Natural 20 → CRITICAL SUCCESS: AI narrates legendary/epic outcomes
- Natural 1 → CRITICAL FAILURE: AI narrates dramatic/comedic disasters
- Enhanced context sent to AI for memorable critical narration
```

**Leveling System Design (Planned):**
```
Level Cap: 5
XP Source: Milestones only (no kill grinding)

Level 1 → 2 (100 XP): +2 HP, +1 to any stat
Level 2 → 3 (300 XP): +2 HP, Class ability
Level 3 → 4 (600 XP): +2 HP, +1 to any stat  
Level 4 → 5 (1000 XP): +2 HP, +1 proficiency, Class ability

Milestone XP: Minor=25, Major=50, Boss=100, Adventure=150
```

---

### Phase 3: World & Persistence 🔄 In Progress
**Goal:** Make it feel like a real adventure

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 3.1 | Save/Load System | JSON file for character + story progress | ✅ Complete |
| 3.2 | Location System | Multiple rooms/areas with movement | ✅ Complete |
| 3.2.1 | Location Enhancements | Tests, items/NPCs, events, narration | 🔄 In Progress |
| 3.3 | NPCs | Dialogue, quests, shop functionality | ⬜ |

**Save/Load System Features (3.1):**
```
- Save game to numbered slots (1-3) or timestamped files
- Load from main menu or in-game
- Preserves: character stats, HP, XP, inventory, gold, equipped items
- Preserves: scenario progress and story flags
- Commands: 'save', 'load', 'saves' (list all)
- Save directory: /saves/
```

**Location System Features (3.2):**
```
- Location dataclass with: id, name, description, exits, npcs, items, atmosphere
- LocationManager: handles movement, exit validation, context for AI
- Pre-defined locations per scenario scene (18 locations in Goblin Cave)
- Scene → Location binding: each scene unlocks specific locations
- Commands: 'look' (describe location), 'exits' (show available), 'go <direction>'
- Cardinal directions supported: north, south, east, west, n, s, e, w
- AI receives location context for immersive narration
- Location state persisted in save files (visited, current location)
```

**Location System Enhancements (3.2.1):** 🔄 In Progress
```
Priority 1 - Test Coverage (HIGH): ✅ COMPLETE
  [x] Create tests/test_location.py with comprehensive tests (80 tests)
  [x] Test Location.to_dict() / from_state() serialization
  [x] Test LocationManager.move() with valid/invalid directions
  [x] Test exit filtering by available_location_ids
  [x] Test save/load round-trip for location state
  [x] Test LocationEvent class and event methods

Priority 2 - Item/NPC Integration (MEDIUM): ✅ COMPLETE
  [x] Display items on 'look' command
  [x] Add 'take <item>' command for location items
  [x] Show NPCs present in location
  [x] Add 'talk <npc>' command for NPC dialogue

Priority 3 - Location Events (MEDIUM): ✅ COMPLETE
  [x] Created LocationEvent dataclass with EventTrigger enum
  [x] Implement events_triggered functionality
  [x] trigger_event(), has_event(), is_event_triggered(), add_event() methods
  [x] get_events_for_trigger() with first-visit detection
  [x] Updated move() to return triggered events
  [x] AI DM receives event context for narration
  [x] Added events to 6 Goblin Cave locations (traps, discoveries, confrontations)

Priority 4 - Movement Narration (MEDIUM): ✅ COMPLETE
  [x] LOCATION_NARRATION_PROMPT for immersive AI descriptions
  [x] build_location_context() - gathers items, NPCs, events, atmosphere
  [x] get_location_narration() - requests AI narrative prose
  [x] display_location_narration() - consistent output format
  [x] 'look' command now uses AI narration (not bullet points)
  [x] Movement triggers AI narration with event context
  [x] Added 'scan' command for mechanical item/NPC/exit list
  [x] User-friendly item display ("Healing Potion" not "healing_potion")
  [x] Normalized item matching (spaces work: "take healing potion")

Priority 5 - Conditional Exits (LOW):
  [ ] Add exit_requirements field for locked doors
  [ ] Support key-based requirements: {"door": "has:rusty_key"}
  [ ] Hidden passages revealed by perception checks

Priority 6 - Cardinal Aliases (LOW):
  [ ] Add direction_aliases to Location dataclass
  [ ] Map n/s/e/w to descriptive exits
```

**Success Criteria:**
- [x] Game state persists between sessions
- [x] Player can navigate between locations
- [x] Location system has comprehensive test coverage (80 tests)
- [x] Player can interact with items/NPCs in locations
- [x] AI generates immersive location descriptions
- [ ] Player can interact with NPCs for quests/trading

---

### Phase 4: Advanced AI DM Features ⬜ Not Started
**Goal:** Smarter, more immersive AI dungeon master

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 4.1 | Context Memory | AI remembers story events and player decisions | ⬜ |
| 4.2 | Dynamic Story Generation | AI creates encounters based on player actions | ⬜ |
| 4.3 | Rule Enforcement | AI validates actions against D&D rules | ⬜ |

**Success Criteria:**
- [ ] AI references past events in narration
- [ ] Encounters feel unique and reactive
- [ ] Invalid actions are caught and explained

---

### Phase 5: Backend API ⬜ Not Started
**Goal:** Create API backend to support mobile app

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 5.1 | REST API Setup | FastAPI/Flask backend for game logic | ⬜ |
| 5.2 | JSON Data Refactor | Move items, locations, scenarios to JSON files | ⬜ |
| 5.3 | Authentication | User accounts, login, session management | ⬜ |
| 5.4 | Cloud Save | Database for persistent game saves | ⬜ |
| 5.5 | API Endpoints | Chat, character, inventory, combat endpoints | ⬜ |

**JSON Data Refactor Details (5.2):**
```
Planned Structure:
data/
├── items.json              # All items from ITEMS dict
├── scenarios/
│   └── goblin_cave/
│       ├── scenario.json   # Metadata, scene order
│       ├── locations.json  # All 18+ locations
│       └── scenes.json     # Scene definitions

Benefits:
- Edit content without modifying Python code
- Hot-reload scenarios without restart
- Multiple scenarios as separate folders
- Modding support for community content
- Mobile app: download/update scenarios independently

Migration Plan:
1. Create JSON loader functions with Python fallback
2. Export existing dicts to JSON format
3. Add JSON validation on load
4. Deprecate Python dicts in Phase 7
```

**Success Criteria:**
- [ ] API accepts game commands and returns responses
- [ ] Content stored in JSON files
- [ ] Users can register and login
- [ ] Game state syncs between devices

---

### Phase 6: Flutter App ⬜ Not Started
**Goal:** Cross-platform app for iOS, Android, Web, and Desktop

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 6.1 | Flutter Project Setup | Initialize Flutter project, dependencies | ⬜ |
| 6.2 | Theme System | 6 themes (Dark Fantasy, Light Parchment, Forest Green, Dungeon Stone, Royal Purple, Blood Crimson) + system default, theme persistence | ⬜ |
| 6.3 | Chat Interface | Text input, scrollable message history, typing indicator, styled bubbles | ⬜ |
| 6.4 | Character Screen | View stats, abilities, HP, AC in D&D-style layout | ⬜ |
| 6.5 | Inventory Screen | Equipped items, backpack, gold tracker | ⬜ |
| 6.6 | Dice Roller UI | Visual dice rolling animations, modifier support | ⬜ |
| 6.7 | Settings Screen | Theme selector gallery, save/load, API config | ⬜ |
| 6.8 | Push Notifications | Game events, session reminders | ⬜ |
| 6.9 | Offline Mode | Queue actions when offline | ⬜ |
| 6.10 | Web Build | Deploy to web hosting | ⬜ |
| 6.11 | Desktop Build | Windows/Mac/Linux packages | ⬜ |

**Success Criteria:**
- [ ] App runs on iOS and Android
- [ ] App runs in web browser
- [ ] 7 theme options with smooth transitions
- [ ] Theme persists between sessions
- [ ] Seamless gameplay experience across platforms
- [ ] Character management on the go
- [ ] Visual polish (themes, animations)

**Target Platforms:**
- 📱 iOS (App Store)
- 📱 Android (Play Store)
- 🌐 Web (Browser)
- 🖥️ Windows (Downloadable)
- 🖥️ macOS (Downloadable)
- 🐧 Linux (Downloadable)

**Design Documentation:**
- See [UI_DESIGN_SPEC.md](UI_DESIGN_SPEC.md) for complete UI/UX specifications
- See [THEME_SYSTEM_SPEC.md](THEME_SYSTEM_SPEC.md) for DLC-ready theme architecture

---

### Phase 7: Theme Store & Monetization ⬜ Not Started
**Goal:** Enable theme purchases as DLC

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 7.1 | Theme Registry | Central system to manage all themes | ⬜ |
| 7.2 | Unlock System | Track which themes user owns locally | ⬜ |
| 7.3 | Theme Store UI | Browse, preview, purchase themes | ⬜ |
| 7.4 | In-App Purchases | Google Play & App Store integration | ⬜ |
| 7.5 | Backend Sync | Cross-device unlock status | ⬜ |
| 7.6 | Purchase Verification | Validate purchases server-side | ⬜ |
| 7.7 | Theme Packs DLC | Nature, Dungeon, Arcane, Gothic packs | ⬜ |

**Success Criteria:**
- [ ] Users can browse all themes (locked + unlocked)
- [ ] Preview themes before buying
- [ ] Purchase themes via app stores
- [ ] Purchases sync across devices
- [ ] Free users get 2 core themes

**Pricing Strategy:**
- Core Pack (FREE): Dark Fantasy, Light Parchment
- Small Packs ($1.99): 3-4 themes each
- Large Packs ($2.99): 4-5 themes + special effects
- Premium Bundle ($7.99): All themes

**Technical Documentation:**
- See [THEME_SYSTEM_SPEC.md](THEME_SYSTEM_SPEC.md) for complete DLC architecture

---

## Technical Stack (Proposed)

| Component | Technology | Notes |
|-----------|------------|-------|
| Language (Backend) | Python 3.x | API and game logic |
| Language (Frontend) | Dart (Flutter) | Cross-platform UI |
| AI Provider | Google Gemini (GenAI) | gemini-2.0-flash default |
| Data Storage | JSON files → PostgreSQL | JSON for local, DB for cloud |
| Backend API | FastAPI | Fast, async, auto-docs |
| Frontend Framework | Flutter | iOS, Android, Web, Desktop |
| Authentication | JWT + OAuth | Secure user sessions |
| Cloud Hosting | TBD (Railway/Render/AWS) | For API + database |
| Config | .env file | All AI/system config |

---

## Testing Log

| Date | Phase | Test | Result | Notes |
|------|-------|------|--------|-------|
| 2024-12-15 | 1.1 | Simple Chat Loop | ✅ Pass | Gemini 2.0 Flash working, conversation flows naturally |

---

## Current Focus

**Next Action:** Build Phase 1, Step 1 - Simple Chat Loop

---

## Notes & Decisions

- Starting small to avoid past failures
- Each phase must be tested before moving to next
- Document learnings and issues in Testing Log

---
