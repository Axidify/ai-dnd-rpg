# Project Assessment Guide

**Purpose:** Framework for AI agents to assess project implementation, rate quality, and identify gaps  
**Last Updated:** December 22, 2025  

---

## 🎯 Assessment Overview

This guide provides a structured approach to evaluate the project's current state against the DEVELOPMENT_PLAN.md roadmap.

---

## 📊 Phase Status Assessment

### How to Assess Phase Completion

1. **Read DEVELOPMENT_PLAN.md** - Find all phases and their features
2. **Verify Implementation** - Check if code exists in `src/`
3. **Verify Tests** - Check if tests exist in `tests/`
4. **Verify Integration** - Check if API endpoints expose the feature

### Completion Scoring

| Score | Meaning | Criteria |
|-------|---------|----------|
| 100% | Complete | All features implemented, tested, and documented |
| 75-99% | Nearly Complete | Minor features or edge cases missing |
| 50-74% | Partial | Core features done, some missing |
| 25-49% | Started | Foundation exists, major work remaining |
| 0-24% | Not Started | No meaningful implementation |

### Quick Commands for Verification

```powershell
# Check if module exists
Test-Path "src/module_name.py"

# Count tests for a feature
Get-ChildItem tests/*.py | Select-String "def test_feature"

# Check API endpoints
Get-Content src/api_server.py | Select-String "@app.route"

# Verify code is used
Get-ChildItem src/*.py | Select-String "from module import"
```

---

## ⭐ Quality Rating Framework

### Rating Categories

| Category | Weight | What to Check |
|----------|--------|---------------|
| **Core Mechanics** | 30% | Combat, dice, inventory, skills |
| **World/Persistence** | 20% | Locations, save/load, events |
| **NPC/Social** | 15% | Dialogue, quests, reputation |
| **Security/Testing** | 15% | Test coverage, exploit prevention |
| **Advanced Features** | 10% | Campaigns, modding, cloud features |
| **Documentation** | 10% | Guides, changelogs, API docs |

### Rating Scale

| Score | Grade | Meaning |
|-------|-------|---------|
| 5/5 | Excellent | Complete, well-tested, polished |
| 4/5 | Good | Working well, minor gaps |
| 3/5 | Adequate | Functional, notable limitations |
| 2/5 | Needs Work | Partially functional, issues |
| 1/5 | Poor | Barely functional or broken |
| 0/5 | Missing | Not implemented |

### Evidence Required for Ratings

| Rating | Evidence |
|--------|----------|
| 5/5 | Tests passing, API working, documented |
| 4/5 | Tests passing, minor features incomplete |
| 3/5 | Core tests passing, edge cases failing |
| 2/5 | Some tests failing, bugs present |
| 1/5 | Many tests failing, critical bugs |

---

## 🔍 Gap Finding Process

### Step 1: Compare Plan vs Implementation

```powershell
# Find all planned features
Get-Content docs/DEVELOPMENT_PLAN.md | Select-String "⬜|NOT IMPLEMENTED|\[ \]"
```

### Step 2: Check for Orphaned Code

```powershell
# Find functions not called anywhere
# (Manual review needed - look for dead code)
```

### Step 3: Check Test Coverage

```powershell
# List test files
Get-ChildItem tests/test_*.py | Measure-Object

# Compare to modules
Get-ChildItem src/*.py | Measure-Object
```

### Step 4: API Completeness

```powershell
# Count endpoints
Get-Content src/api_server.py | Select-String "@app.route" | Measure-Object

# Check if all core features have endpoints
```

---

## 📋 Assessment Template

Use this template when performing an assessment:

```markdown
# Project Assessment - [Date]

## Phase Completion Summary

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 1: Core Foundation | ✅/🔄/⬜ | X% |
| Phase 2: Game Mechanics | ✅/🔄/⬜ | X% |
| [Continue for all phases...] |

## Detailed Ratings

### Category: [Name] (X/5)
- **Evidence:** [What you verified]
- **Gaps:** [What's missing]
- **Strengths:** [What's working well]

### [Repeat for each category...]

## Critical Gaps

| Gap | Priority | Impact |
|-----|----------|--------|
| [Missing feature] | HIGH/MED/LOW | [Effect on gameplay] |

## Overall Grade

| Category | Weight | Score | Weighted |
|----------|--------|-------|----------|
| [Category] | X% | X/5 | X.X |
| [Total] | 100% | - | XX.X/100 |

## Recommended Next Steps

1. [Priority 1 action]
2. [Priority 2 action]
3. [Priority 3 action]
```

---

## 🚦 Priority Classification

### Gap Priority Levels

| Priority | Criteria | Action |
|----------|----------|--------|
| 🔴 HIGH | Blocks core gameplay, security risk, or user-visible bug | Fix immediately |
| 🟠 MEDIUM | Affects gameplay quality, limits features | Fix soon |
| 🟡 LOW | Nice to have, polish, optimization | When time allows |
| 🟢 OPTIONAL | Future enhancement, not in current scope | Track for later |

### Impact Assessment

| Impact Level | Description |
|--------------|-------------|
| **Critical** | Game unplayable without this |
| **Major** | Significantly affects player experience |
| **Minor** | Noticeable but workaround exists |
| **Cosmetic** | Visual or text issue only |

---

## 📈 Trend Tracking

When performing regular assessments, track:

| Metric | How to Measure | Target Trend |
|--------|----------------|--------------|
| Test count | `pytest --collect-only` | ↑ Increasing |
| Pass rate | `pytest` output | ≥ 95% |
| Open gaps | Count from assessment | ↓ Decreasing |
| Phase completion | % complete | → 100% |

---

## 🔄 Assessment Frequency

| Trigger | Assessment Type |
|---------|-----------------|
| After major feature | Quick rating of affected area |
| End of development session | Full gap check |
| Before release/demo | Complete assessment |
| User requests | Full assessment with recommendations |

---

*This guide provides the framework for project assessment. Use DEVELOPMENT_PLAN.md as the source of truth for planned features.*
