# AI D&D Text RPG - Development Plan

**Project:** Text-based D&D RPG with AI Dungeon Master  
**Status:** Planning Phase  
**Created:** December 15, 2025  

---

## Project Overview

A text-based role-playing game where an AI acts as the Dungeon Master, narrating adventures, managing encounters, and responding to player actions in real-time. Built incrementally with testing at each phase.

---

## Development Phases

### Phase 1: Core Foundation ⬜ Not Started
**Goal:** Get a working conversation loop with basic game state

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 1.1 | Simple Chat Loop | Python script with player input → AI response loop | ✅ Complete |
| 1.2 | Basic Character Sheet | Name, class, HP, stats (STR, DEX, CON, INT, WIS, CHA) | ⬜ |
| 1.3 | Starting Scenario | One room, one simple encounter (hardcoded) | ⬜ |

**Success Criteria:**
- [ ] Player can chat with AI DM
- [ ] Player has a character with viewable stats
- [ ] Player can take basic actions (look, move, talk)

---

### Phase 2: Core Game Mechanics ⬜ Not Started
**Goal:** Add actual D&D gameplay rules

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 2.1 | Dice Rolling System | d4, d6, d8, d10, d12, d20 with modifiers | ⬜ |
| 2.2 | Skill Checks | AI requests rolls, player rolls, outcome affects story | ⬜ |
| 2.3 | Combat System | Turn-based, HP tracking, attack/defend actions | ⬜ |
| 2.4 | Inventory System | Pick up items, use items, equip gear | ⬜ |

**Success Criteria:**
- [ ] Player can roll dice with proper modifiers
- [ ] Skill checks affect story outcomes
- [ ] Player can fight an enemy and win/lose
- [ ] Player can collect and use items

---

### Phase 3: World & Persistence ⬜ Not Started
**Goal:** Make it feel like a real adventure

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 3.1 | Save/Load System | JSON file for character + story progress | ⬜ |
| 3.2 | Location System | Multiple rooms/areas with movement | ⬜ |
| 3.3 | NPCs | Dialogue, quests, shop functionality | ⬜ |

**Success Criteria:**
- [ ] Game state persists between sessions
- [ ] Player can navigate between locations
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
| 5.2 | Authentication | User accounts, login, session management | ⬜ |
| 5.3 | Cloud Save | Database for persistent game saves | ⬜ |
| 5.4 | API Endpoints | Chat, character, inventory, combat endpoints | ⬜ |

**Success Criteria:**
- [ ] API accepts game commands and returns responses
- [ ] Users can register and login
- [ ] Game state syncs between devices

---

### Phase 6: Mobile App ⬜ Not Started
**Goal:** Native mobile experience for iOS and Android

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 6.1 | App Framework Setup | React Native / Flutter project | ⬜ |
| 6.2 | Chat Interface | Text input, scrollable message history | ⬜ |
| 6.3 | Character Screen | View stats, inventory, equipment | ⬜ |
| 6.4 | Dice Roller UI | Visual dice rolling animations | ⬜ |
| 6.5 | Push Notifications | Game events, session reminders | ⬜ |
| 6.6 | Offline Mode | Queue actions when offline | ⬜ |

**Success Criteria:**
- [ ] App runs on iOS and Android
- [ ] Seamless gameplay experience on mobile
- [ ] Character management on the go
- [ ] Visual polish (themes, animations)

---

## Technical Stack (Proposed)

| Component | Technology | Notes |
|-----------|------------|-------|
| Language | Python 3.x | Simple, fast iteration |
| AI Provider | Google Gemini (GenAI) | gemini-1.5-flash default |
| Data Storage | JSON files → PostgreSQL | JSON for local, DB for cloud |
| Backend API | FastAPI | Fast, async, auto-docs |
| Mobile Framework | React Native OR Flutter | Cross-platform iOS/Android |
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
