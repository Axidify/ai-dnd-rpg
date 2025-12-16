# AI D&D Text RPG - Development Plan

**Project:** Text-based D&D RPG with AI Dungeon Master  
**Status:** Phase 2 - Combat System Complete  
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

### Phase 2: Core Game Mechanics 🔄 In Progress
**Goal:** Add actual D&D gameplay rules

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| 2.1 | Dice Rolling System | d4, d6, d8, d10, d12, d20 with modifiers | ✅ Complete |
| 2.2 | Skill Checks | AI requests rolls, player rolls, outcome affects story | ✅ Complete |
| 2.3 | Combat System | Turn-based, HP tracking, attack/defend/flee actions | ✅ Complete |
| 2.4 | Inventory System | Pick up items, use items, equip gear | ⬜ |

**Success Criteria:**
- [x] Player can roll dice with proper modifiers
- [x] Skill checks affect story outcomes
- [x] Player can fight an enemy and win/lose
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
