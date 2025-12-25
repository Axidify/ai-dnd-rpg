# Project Assessment Guide

**Purpose:** Framework for AI agents to assess project implementation, rate quality, and identify gaps  
**Last Updated:** December 25, 2025  
**Gap Analysis:** See [ASSESSMENT_GUIDE_GAP_ANALYSIS.md](ASSESSMENT_GUIDE_GAP_ANALYSIS.md)  

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
| **Frontend Quality** | 5% | React builds, responsive, accessible |
| **Documentation** | 5% | Guides, changelogs, API docs |

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

## � Code Coverage Metrics

```powershell
# Generate coverage report
python -m pytest tests/ --cov=src --cov-report=term-missing
```

| Coverage Level | Target | Rating Impact |
|----------------|--------|---------------|
| >90% | Core modules | +0.5 to category |
| 80-90% | API/utilities | No impact |
| <80% | Any module | -0.5 to category |

---

## 🌐 Frontend Assessment (React)

| Check | How to Verify | Pass Criteria |
|-------|---------------|---------------|
| Builds | `npm run build` | No errors |
| Tests | `npm test` | All pass |
| Console | Browser DevTools | No errors |
| Responsive | Test 320px, 768px, 1024px | Usable at all |
| Accessibility | Lighthouse audit | Score >70 |

---

## 🔌 API Health Check

```powershell
# Test core endpoints
$endpoints = @("/api/health", "/api/scenarios", "/api/game/start")
foreach ($ep in $endpoints) {
    try {
        $r = Invoke-RestMethod "http://localhost:5000$ep" -TimeoutSec 5
        Write-Host "✅ $ep - OK"
    } catch {
        Write-Host "❌ $ep - FAILED: $($_.Exception.Message)"
    }
}
```

| Status | Meaning |
|--------|---------|
| All ✅ | API fully functional |
| Some ❌ | Investigate failures |
| All ❌ | Server not running or broken |

---

## ⚡ Performance Baseline

| Metric | Target | How to Measure |
|--------|--------|----------------|
| API response | <200ms | `Measure-Command { Invoke-RestMethod ... }` |
| Test suite | <5 min | pytest timing |
| Startup time | <5s | Time to first response |

**Track in each assessment for trend analysis.**

---

## �🔍 Gap Finding Process

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

## ✅ Complete Assessment Checklist

### Pre-Assessment
- [ ] Read previous assessment (if exists)
- [ ] Pull latest code (`git pull`)
- [ ] Ensure test environment is clean

### Data Collection
- [ ] Run full test suite (`pytest tests/ -v`)
- [ ] Count API endpoints (`Select-String "@app.route"`)
- [ ] Check frontend builds (`npm run build`)
- [ ] Verify API health (endpoints responding)
- [ ] Collect performance metrics (response times)
- [ ] Check code coverage if available

### Evaluation
- [ ] Score each category (0-5)
- [ ] Document evidence for each rating
- [ ] Identify all gaps
- [ ] Classify gap priorities (HIGH/MED/LOW)

### Comparison (if previous assessment exists)
- [ ] Compare test counts
- [ ] Calculate pass rate trend
- [ ] Note closed gaps
- [ ] Identify new gaps
- [ ] Calculate grade change

### Documentation
- [ ] Create `PROJECT_ASSESSMENT_YYYY-MM-DD.md`
- [ ] Update `DEVELOPMENT_PLAN.md` if needed
- [ ] Create issues for HIGH priority gaps
- [ ] Update `CHANGELOG.md`

### Post-Assessment Validation
- [ ] Verify all claimed metrics
- [ ] Ensure all links work
- [ ] Proofread for accuracy

---

## 📈 Diff Comparison Template

Include this in assessments when comparing to previous:

```markdown
## Changes Since Last Assessment

| Metric | Previous | Current | Change |
|--------|----------|---------|--------|
| Tests | XXX | YYY | +/-N |
| Pass Rate | XX% | YY% | +/-N% |
| API Endpoints | XX | YY | +/-N |
| Open Gaps | X | Y | +/-N |
| Overall Grade | X% | Y% | +/-N% |

### New Gaps
- [ ] Gap description

### Closed Gaps
- [x] Gap description (resolved in commit/PR)
```

---

*This guide provides the framework for project assessment. Use DEVELOPMENT_PLAN.md as the source of truth for planned features.*
