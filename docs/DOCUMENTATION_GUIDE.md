# Documentation Guide

**Purpose:** Reference guide for AI agents handling documentation tasks  
**Last Updated:** December 25, 2025  

---

## 📚 Documentation Files Overview

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `README.md` | Project overview, quick start, feature list | Major releases |
| `DEVELOPMENT_PLAN.md` | Phase roadmap, milestones, progress tracking | After each phase/feature |
| `CHANGELOG.md` | User-facing change log, version history | Every feature/fix/commit |
| `DEVELOPER_GUIDE.md` | Technical docs, architecture, API reference | Major features/architecture |
| `PROJECT_ASSESSMENT_*.md` | Point-in-time quality assessments | Periodic reviews |
| `ASSESSMENT_GUIDE.md` | Framework for conducting assessments | Rarely |
| `UI_DESIGN_SPEC.md` | Frontend design specifications | UI changes |
| `THEME_SYSTEM_SPEC.md` | Theme/styling specifications | Theme updates |
| `*_REPORT.md` | Test reports and findings | After testing sessions |
| `DOCUMENTATION_GUIDE.md` | This file - meta instructions | When processes change |

---

## 🔄 Synchronization Rules

### After Implementing a Feature

**Files to update:**
1. `DEVELOPMENT_PLAN.md` - Mark phase/task as complete with date
2. `CHANGELOG.md` - Add entry under current version
3. `README.md` - Update feature list if user-facing
4. `DEVELOPER_GUIDE.md` - Add API/architecture docs if applicable

**Template for DEVELOPMENT_PLAN.md:**
```markdown
- [x] Task name ✅ (YYYY-MM-DD)
```

**Template for CHANGELOG.md:**
```markdown
### [Version] - YYYY-MM-DD

#### Added
- Feature description

#### Changed
- Modification description

#### Fixed
- Bug fix description
```

### After Adding New Tests

**Update:**
- `DEVELOPMENT_PLAN.md` - Update test count in relevant phase
- `PROJECT_ASSESSMENT_*.md` - Update test statistics if assessment exists

### After Adding API Endpoints

**Update:**
- `DEVELOPER_GUIDE.md` - Add endpoint documentation
- `README.md` - Update API endpoint count if mentioned

### After Completing a Phase

**Full sync required:**
1. `DEVELOPMENT_PLAN.md` - Mark phase complete, add completion date
2. `CHANGELOG.md` - Add phase summary
3. `README.md` - Update project status/progress
4. Consider creating new `PROJECT_ASSESSMENT_*.md`

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

## 📊 Key Metrics to Track

Keep these metrics current across documentation:

| Metric | Location(s) | How to Verify |
|--------|-------------|---------------|
| Test Count | DEVELOPMENT_PLAN, README, ASSESSMENT | `pytest --collect-only -q` |
| Test Pass Rate | ASSESSMENT, CHANGELOG | `pytest` exit code |
| API Endpoints | README, DEVELOPER_GUIDE | `grep "@app.route"` count |
| Phase Completion | DEVELOPMENT_PLAN | Manual review |
| LOC/File Count | ASSESSMENT | `find . -name "*.py" \| wc -l` |

---

## � Assessment Process

Periodic assessments ensure the project stays on track. Use [ASSESSMENT_GUIDE.md](ASSESSMENT_GUIDE.md) for the full framework.

### When to Create an Assessment

| Trigger | Assessment Type | File Name |
|---------|-----------------|-----------|
| Major milestone complete | Full Assessment | `PROJECT_ASSESSMENT_YYYY-MM-DD.md` |
| Phase complete | Phase Review | Update existing assessment |
| Before major refactor | Gap Analysis | `GAP_ANALYSIS_YYYY-MM-DD.md` |
| Post-incident | Retrospective | `RETROSPECTIVE_YYYY-MM-DD.md` |

### Assessment Workflow

```
1. Read ASSESSMENT_GUIDE.md for evaluation criteria
2. Run test suite: pytest tests/ -v
3. Count metrics: tests, endpoints, files
4. Evaluate each phase (0-100 scoring)
5. Calculate weighted average
6. Identify gaps and priorities
7. Create PROJECT_ASSESSMENT_YYYY-MM-DD.md
8. Update DEVELOPMENT_PLAN.md with findings
```

### Quick Assessment Metrics

```powershell
# Gather all key metrics at once
Write-Host "=== PROJECT METRICS ===" -ForegroundColor Cyan

# Test count
$tests = (python -m pytest tests/ --collect-only -q 2>&1 | Select-String "test").Count
Write-Host "Tests: $tests"

# API endpoints
$endpoints = (Select-String -Path "src/api_server.py" -Pattern "@app.route").Count
Write-Host "API Endpoints: $endpoints"

# Python files
$pyFiles = (Get-ChildItem -Recurse -Filter "*.py" | Where-Object { $_.FullName -notlike "*\.venv*" }).Count
Write-Host "Python Files: $pyFiles"

# Lines of code (rough)
$loc = (Get-ChildItem -Recurse -Filter "*.py" | Where-Object { $_.FullName -notlike "*\.venv*" } | Get-Content | Measure-Object -Line).Lines
Write-Host "Lines of Code: $loc"
```

### Assessment Grade Scale

| Grade | Score | Meaning |
|-------|-------|---------|
| A+ | 97-100 | Exceptional, production-ready |
| A | 93-96 | Excellent, minor polish needed |
| A- | 90-92 | Very good, few issues |
| B+ | 87-89 | Good, some gaps |
| B | 83-86 | Satisfactory, needs work |
| B- | 80-82 | Acceptable, significant gaps |
| C+ | 77-79 | Below expectations |
| C | 70-76 | Major issues |
| F | <70 | Critical problems |

### Post-Assessment Actions

1. **Update DEVELOPMENT_PLAN.md** - Add findings to relevant phase
2. **Create Issues** - Track identified gaps as tasks
3. **Prioritize** - Order gaps by impact and effort
4. **Schedule** - Assign gaps to upcoming phases
5. **Archive** - Keep assessment for historical reference

---

## �🔍 Audit Commands

```powershell
# Count total tests
pytest --collect-only | Select-String "collected"

# Count Python files (excluding venv)
Get-ChildItem -Recurse -Filter "*.py" | Where-Object { $_.FullName -notlike "*\.venv*" } | Measure-Object

# Count API routes
Select-String -Path "src/api_server.py" -Pattern "@app.route" | Measure-Object

# Find outdated test counts in docs
Get-ChildItem docs/*.md | Select-String "tests passing"

# Find TODO/PLANNED markers
Get-ChildItem docs/*.md | Select-String "TODO|PLANNED|⬜"

# Git diff for verification
git diff docs/

# List all doc files with dates
Get-ChildItem docs/*.md | Select-Object Name, LastWriteTime
```

---

## 🤖 AI Agent Pre-Commit Checklist

After completing any task, verify these items are current:

```
□ Code changes tested and passing
□ CHANGELOG.md updated with changes
□ DEVELOPMENT_PLAN.md updated if phase/task completed
□ README.md updated if user-facing features changed
□ New tests documented with count
□ API changes documented in DEVELOPER_GUIDE.md
□ "Last Updated" dates refreshed in modified docs
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

### Scenario Reference Entry
```markdown
## Item: item_name
- **Effect:** What happens when used
- **Trigger:** How to use it ("use item", passive, etc.)
- **Location:** Where to find it
- **Tests:** Link to relevant test file
```

### API Endpoint Entry
```markdown
### METHOD /api/endpoint
**Purpose:** What this endpoint does

**Request:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|

**Response:**
| Field | Type | Description |
|-------|------|-------------|

**Example:**
[code block]
```

---

## 📂 Document Types & When to Create

| Document Type | Create When | Template |
|---------------|-------------|----------|
| `*_REFERENCE.md` | New scenario or complex feature needing lookup tables | Scenario Reference Entry |
| `*_GUIDE.md` | User/developer audience needs walkthrough | Step-by-step sections |
| `*_SPEC.md` | Technical design before implementation | Design doc format |
| `*_REPORT.md` | Test results or analysis complete | Summary + details |

---

## 💡 Brainstorm Topics

*Discussion points for future consideration:*

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
   - Player guide needed?
   - API documentation (OpenAPI/Swagger)?

5. **Localization**
   - Multi-language support planned?
   - Which docs need translation?

---

*This document is a living guide for documentation instructions only. Implementation tracking belongs in DEVELOPMENT_PLAN.md.*
