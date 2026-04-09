# Resume: skill-updater skill development

## Context

We're building a `skill-updater` skill at `.claude/skills/skill-updater/`.
The skill is **design-complete with a critical fix applied after Samsung
testing (2026-04-09).** Ready for re-testing.

## Current state (end of 2026-04-09)

### What's working

- **SKILL.md** — core instructions with 5-phase workflow, revert flow,
  `--check` flow, self-evolution mechanism. Uses progressive disclosure
  with 6 reference files.
- **Two-level versioning** — `metadata.version` (per-skill) + `metadata.source.repo_tag`
  (repo-wide). Both must be in YAML frontmatter.
- **Fetch chain** — 5 strategies: git → `gh` CLI → raw URL → local path → ask user.
  Each has documented failure modes and fallthrough triggers.
- **Origin classification** — 6 types (A–F). Inline decision tree in SKILL.md,
  detailed stamping workflow in reference file.
- **Self-evolution** — field-notes.md captures real-world failures. Has two
  entries: backup bug (2026-04-08) and source-of-truth bug (2026-04-09).

### Critical fix applied (2026-04-09)

**"The file on disk is the truth. Git history is just a reference."**

Samsung testing revealed that the skill was using local git tags and commit
history as source of truth. This caused incorrect merges when local tags were
stale or local history was messy (dummy commits, merge commits, reverts).

**Root cause:** `git show v1.1.0:SKILL.md` reads from the local object store.
If the local tag points to a wrong commit, the entire three-way comparison
uses wrong data.

**Fix applied across all files:**
- SKILL.md — added "Fundamental Principle" section; rewrote Phase 1.3 (read
  file on disk), Phase 1.5 (fetch from remote with `--tags --force`), Phase 3
  (base from remote, local from disk, upstream from remote)
- fetch-strategies.md — Strategy 1 now uses `--tags --force`
- field-notes.md — full writeup of the bug and principle
- TEST-PLAN.md — rewritten with principle baked in, added Test 5 (messy history)
  and Test 6 (idempotency)

### Previous fix (2026-04-08)

**Phase 2 backup bug:** `git branch` only captures committed state, not the
working tree. When user customizations are uncommitted, the backup branch
misses them. Fix: always do `cp -r` file backup first (captures working tree),
git branch is secondary. Logged in `references/field-notes.md`.

### Samsung testing observations (2026-04-09)

- `--check` works reliably (read-only, simple flow)
- Happy path update is not yet robust — sometimes metadata.version not updated,
  sometimes merge misses content
- AI agent sometimes misreads its own tool output (thought `git show` results
  were swapped when they weren't — got lucky with the "correction")
- All issues traced back to using local git objects instead of remote + file

## What needs to happen next

### 1. Re-test everything with the fix

All previous test results are discarded. The TEST-PLAN.md has been rewritten
with 6 tests, all results blank. Test at Samsung corporate environment.

**Test execution order:**
1. Test 2 (`--check`) — read-only, lowest risk
2. Test 1 (happy path) — full workflow with the fix
3. Test 6 (re-run after update) — idempotency
4. Test 3 (`--revert`) — undo
5. Test 5 (messy history) — the scenario that found the bug
6. Test 4 (no metadata) — interactive stamping

### 2. Samsung corporate edge cases

| Scenario | Expected |
|---|---|
| Corporate proxy | Fall through to local path |
| No `gh` CLI | Skip Strategy 2 silently |
| No PAT | Accept gracefully, offer local path |
| VPN-only | Timeout handling, fall through |

### 3. Open design questions (lower priority)

- Should skill-updater update ITSELF? (meta-update problem)
- CHANGELOG.md handling during merges
- `--all` flag to batch-update every skill

## Files to read

1. `.claude/skills/skill-updater/SKILL.md` — core workflow
2. `.claude/skills/skill-updater/tests/TEST-PLAN.md` — test scenarios (results pending)
3. `.claude/skills/skill-updater/references/field-notes.md` — real-world failures log
4. `.claude/skills/skill-updater/references/fetch-strategies.md` — per-strategy details
5. `.claude/skills/skill-updater/references/origin-classification.md` — origin types
6. `.claude/skills/skill-updater/references/environment-detection.md` — capability checks
7. `.claude/skills/skill-updater/references/error-handling.md` — error → action tables
8. `.claude/skills/skill-updater/references/resolution-strategies.md` — merge conflict patterns
9. `.claude/skills/skill-updater/docs/qna.md` — concepts and terminology for humans
10. `.claude/skills/skill-updater/docs/api-reference.md` — command usage reference
11. `.claude/skills/skill-updater/scripts/check-versions.sh` — version comparison script
