# Documentation Guide

**Purpose:** Reference guide for AI agents handling documentation tasks  
**Last Updated:** December 22, 2025  

---

## 📚 Documentation Files Overview

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `DEVELOPMENT_PLAN.md` | Feature roadmap, phase tracking, implementation details | After completing features |
| `CHANGELOG.md` | User-facing change log, version history | Every feature/fix |
| `DEVELOPER_GUIDE.md` | Technical docs for contributors | Major features only |
| `README.md` | Project overview, setup instructions | Major milestones |

---

## 🔄 Update Triggers

### When to Update DEVELOPMENT_PLAN.md
- [ ] Phase status changes (⬜ Planned → 🔄 In Progress → ✅ Complete)
- [ ] Feature implementation completed
- [ ] Test count significantly changes
- [ ] New tasks/priorities added
- [ ] Architecture decisions made

### When to Update CHANGELOG.md
- [ ] New feature added
- [ ] Bug fixed
- [ ] Breaking change introduced
- [ ] Security improvement made
- [ ] Test suite changes

### When to Update DEVELOPER_GUIDE.md
- [ ] New system/module added
- [ ] API changes
- [ ] New conventions established
- [ ] Architecture changes

---

## ✅ Documentation Checklist

After completing any task, verify these items are current:

### Accuracy Checks
- [ ] Test counts match actual (`pytest --collect-only | grep collected`)
- [ ] Phase statuses reflect implementation reality
- [ ] Code examples are runnable
- [ ] File paths are valid

### Consistency Checks
- [ ] Dates updated (Last Updated field)
- [ ] Emoji indicators match status (✅ ⬜ 🔄)
- [ ] Test file names match actual files in `tests/`
- [ ] Feature names match code

### Formatting Standards
- [ ] Markdown renders correctly
- [ ] Tables are aligned
- [ ] Code blocks have language tags
- [ ] Headers follow hierarchy (# → ## → ###)

---

## 📝 Common Update Patterns

### Adding a New Feature

```markdown
## CHANGELOG.md
- **Feature Name** - Brief description
  - Sub-feature detail
  - Another detail
  - Created `tests/test_feature.py` with X tests

## DEVELOPMENT_PLAN.md
| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| X.X | Feature Name | What it does | ✅ Complete |

## DEVELOPER_GUIDE.md
### Feature Name System
[Technical documentation of how it works]
```

### Updating Test Counts

1. Run: `pytest --collect-only | grep collected`
2. Update all occurrences in:
   - `DEVELOPMENT_PLAN.md` (search for "tests passing")
   - `CHANGELOG.md` (Test Suite Status section)

### Changing Phase Status

| Status | Emoji | Meaning |
|--------|-------|---------|
| ⬜ | Not Started | Planned but no work done |
| 🔄 | In Progress | Actively working |
| ✅ | Complete | Fully implemented and tested |

---

## 🎯 Quality Guidelines

### Good Documentation
- **Specific**: "Added 25 tests for skill checks" not "Added tests"
- **Actionable**: Include command examples
- **Current**: Match code reality
- **Scannable**: Use tables, bullets, headers

### Common Mistakes to Avoid
- ❌ Outdated test counts
- ❌ Phase marked complete when tests fail
- ❌ Missing changelog entries for user-visible changes
- ❌ Developer guide examples that don't compile
- ❌ "Last Updated" date not refreshed

---

## 🔍 Audit Commands

```powershell
# Count total tests
pytest --collect-only | Select-String "collected"

# Find outdated test counts in docs
Get-ChildItem docs/*.md | Select-String "tests passing"

# Find TODO/PLANNED markers
Get-ChildItem docs/*.md | Select-String "TODO|PLANNED|⬜"

# Git diff for verification
git diff docs/
```

---

## 📋 Templates

### New Feature Changelog Entry
```markdown
- **Feature Name** - One-line description
  - Implementation detail 1
  - Implementation detail 2
  - Created `tests/test_feature.py` with X tests
  - Total test count: XXX passing
```

### Phase Completion Checklist
```markdown
### Phase X.X: Feature Name ✅ Complete
**Goal:** What this phase achieves

| Step | Feature | Description | Status |
|------|---------|-------------|--------|
| X.X.1 | Sub-feature | Details | ✅ |

**Success Criteria:**
- [x] Criterion 1
- [x] Criterion 2
```

---

## � Documentation Gaps (To Address)

### Priority 1: Missing Documentation
| Document | Purpose | Status | Priority |
|----------|---------|--------|----------|
| `SCENARIO_REFERENCE.md` | Item effects, NPC skill checks, quest details | ⬜ Not Created | HIGH |
| `PLAYER_GUIDE.md` | How to play, commands, gameplay tips | ⬜ Not Created | MEDIUM |
| `API_REFERENCE.md` | OpenAPI/Swagger style endpoint docs | ⬜ Not Created | LOW |

### Priority 2: Outdated Sections to Watch
| File | Section | Issue |
|------|---------|-------|
| `DEVELOPER_GUIDE.md` | Test count references | May become stale (update on major test additions) |
| `DEVELOPMENT_PLAN.md` | Phase statuses | Update as features complete |
| `CHANGELOG.md` | "Unreleased" section | Move to versioned release when tagging |

### Priority 3: Documentation Debt
- [ ] Add "Last Updated" to all major docs
- [ ] Add table of contents to CHANGELOG.md
- [ ] Cross-reference between DEVELOPER_GUIDE.md and DEVELOPMENT_PLAN.md
- [ ] Add code examples to NPC personality documentation
- [ ] Document party member AI decision logic

---

## 🎯 Documentation Improvement Plan

### SCENARIO_REFERENCE.md (To Create)
```markdown
# Scenario Reference: Goblin Cave

## Items & Effects
| Item | Effect | How to Use |
|------|--------|------------|
| mysterious_key | Opens Hidden Hollow | Carry in inventory |
| poison_vial | +1d4 damage next attack | "use poison" command |
| ...

## NPC Skill Checks
| NPC | Skill Check | DC | Effect |
|-----|-------------|----|----|
| Bram | Persuasion (upfront_payment) | 14 | Get 25g advance |
| ...

## Quest Rewards
...
```

### PLAYER_GUIDE.md (To Create)
```markdown
# Player Guide

## Getting Started
- Character creation
- Basic commands

## Combat
- Attack, defend, flee
- Party combat

## Exploration
- Travel menu
- Secret areas

## NPCs
- Dialogue, trading, reputation
```

### API_REFERENCE.md (To Create)
```markdown
# API Reference

## Endpoints

### POST /api/game/start
Creates new game session...

### POST /api/game/action/stream
Processes player action with SSE streaming...
```

---

## 💡 Brainstorm Topics

*Add discussion points below:*

1. **Automated Doc Validation**
   - Script to verify test counts match docs?
   - CI check for outdated phase markers?

2. **Version Numbering**
   - When to bump version?
   - SemVer rules for this project?

3. **Architecture Decision Records**
   - Should we track ADRs?
   - Where to store design decisions?

4. **User-Facing Docs**
   - Player guide needed? ✅ YES - see improvement plan above
   - API documentation (OpenAPI/Swagger)? ✅ YES - see improvement plan above

5. **Localization**
   - Multi-language support planned?
   - Which docs need translation?

---

*This document is a living guide. Add sections as patterns emerge.*
