# Changelog

All notable changes to the AI D&D Text RPG project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Planned
- Phase 1.2: Basic Character Sheet
- Phase 1.3: Starting Scenario

---

## [0.1.0] - 2024-12-15

### Added
- **Phase 1.1: Simple Chat Loop** - Core game functionality
  - Main game file (`src/game.py`) with AI Dungeon Master
  - Google Gemini 2.0 Flash integration via `google-generativeai`
  - System prompt defining DM behavior and narrative style
  - Interactive conversation loop with player input
  - Conversation history maintained throughout session
  
- **Project Configuration**
  - `.env` support for API keys and model selection via `python-dotenv`
  - `.env.example` template for configuration
  - `requirements.txt` with dependencies
  - `.gitignore` to protect sensitive files
  
- **Documentation**
  - `README.md` with setup instructions and project overview
  - `DEVELOPMENT_PLAN.md` with 6-phase roadmap
  - `CHANGELOG.md` (this file)

### Technical Details
- Python 3.14 virtual environment
- Google Gemini API for AI responses
- Configurable model via `GEMINI_MODEL` environment variable
- Default model: `gemini-2.0-flash`

### Tested
- ✅ AI DM creates immersive opening narrative
- ✅ Player actions receive contextual responses
- ✅ Conversation history maintains context
- ✅ Inventory queries answered naturally
- ✅ Quest/reward dialogue works properly
- ✅ Graceful exit with "quit" command

---

## Version History

| Version | Date | Phase | Description |
|---------|------|-------|-------------|
| 0.1.0 | 2024-12-15 | 1.1 | Simple Chat Loop - Initial working version |

---

## Upcoming Versions

| Version | Phase | Features |
|---------|-------|----------|
| 0.2.0 | 1.2 | Basic Character Sheet (name, class, stats) |
| 0.3.0 | 1.3 | Starting Scenario (hardcoded encounter) |
| 0.4.0 | 2.1-2.4 | Dice, Combat, Inventory mechanics |
| 0.5.0 | 3.1-3.3 | Save/Load, Locations, NPCs |
| 0.6.0 | 4.1-4.3 | Advanced AI features |
| 1.0.0 | 5.1-5.4 | Backend API |
| 2.0.0 | 6.1-6.6 | Mobile App |
