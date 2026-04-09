# Resume: skill-updater skill development

## Context

We're building a `skill-updater` skill at `.claude/skills/skill-updater/`.
**First-stage testing complete at Samsung (2026-04-09). All 6 tests PASS.**

## Current state (end of 2026-04-09)

### Test results (Samsung corporate environment)

| Test | What | Result |
|---|---|---|
| 1 | `--check` scan | PASS |
| 2 | Happy path update | PASS (2nd attempt, after diff tool fix) |
| 3 | Idempotency (re-run after update) | PASS |
| 4 | `--revert` | PASS (with explicit skill trigger) |
| 5 | Messy git history | PASS |
| 6 | No metadata (local skill) | PASS |

### Key lessons learned and fixes applied (2026-04-09)

Three critical design principles emerged from Samsung testing:

**1. The file on disk is the truth. Git history is just a reference.**
- Local state = actual file on disk (never `git show HEAD:...` or `git log`)
- Base/upstream = fetched from remote (never local git tags)
- On shared corporate PCs, git history is unreliable — anyone could have
  run random git commands
- SKILL.md now has an explicit FORBIDDEN list and ALLOWED whitelist for git commands

**2. Always compare local file vs upstream file directly.**
- Tag-to-tag diff (`git diff v1.0.0 v1.1.0`) is irrelevant — it only shows
  what changed in the repo, not what the local file is missing
- The primary comparison is always: local file on disk vs upstream file at
  latest tag
- First attempt failed because AI relied on tag diff and missed all real
  differences

**3. Always use a diff tool — never compare files by reading them.**
- AI reading two files and "mentally" comparing them is error-prone (context
  rot, missed sections)
- Save upstream to temp file, run `diff -u local /tmp/upstream`
- Diff tool detects differences (deterministic). AI interprets differences
  (which to keep, which to merge).

### Other fixes applied

- Remote name is not always `origin` — use `git remote -v` to find the
  matching remote
- `git fetch --tags --force` — always force to avoid stale local tags
- Revert cleanup: delete backup directory + local tag + backup branch
- Skill description refined for natural language triggering

### Known limitations

- Natural language revert requests don't always trigger the skill-updater
  skill — the AI handles simple restores manually. Adding "(skill-updater
  스킬 사용해서)" to the request works as a workaround.
- "From GitHub" stamping flow (Test 6) not yet tested — only tested the
  "user-authored" path.

## What's working

- **SKILL.md** — core instructions with 5-phase workflow, revert flow,
  `--check` flow, self-evolution mechanism. Hardened with forbidden/allowed
  git command lists and diff tool requirements.
- **Two-level versioning** — `metadata.version` (per-skill) + `metadata.source.repo_tag`
  (repo-wide).
- **Fetch chain** — 5 strategies: git → `gh` CLI → raw URL → local path → ask user.
- **Origin classification** — 6 types (A–F).
- **Self-evolution** — field-notes.md has 3 entries from real-world failures.
- **Docs** — Q&A doc for humans, API reference for `--check` command.

## What needs to happen next

### 1. More testing

- Test "from GitHub" stamping flow (Test 6 alternate path)
- Test with skills that have multiple files (not just SKILL.md)
- Test with larger SKILL.md files (stress-test the diff tool approach)
- Samsung-specific edge cases: proxy, VPN, auth failures

### 2. Open design questions

- Should skill-updater update ITSELF? (meta-update problem)
- CHANGELOG.md handling during merges
- `--all` flag to batch-update every skill
- How to improve natural language trigger for revert flow

## Files to read

1. `.claude/skills/skill-updater/SKILL.md` — core workflow
2. `.claude/skills/skill-updater/tests/TEST-PLAN.md` — test scenarios and results
3. `.claude/skills/skill-updater/references/field-notes.md` — real-world failures log
4. `.claude/skills/skill-updater/references/fetch-strategies.md` — per-strategy details
5. `.claude/skills/skill-updater/references/origin-classification.md` — origin types
6. `.claude/skills/skill-updater/references/environment-detection.md` — capability checks
7. `.claude/skills/skill-updater/references/error-handling.md` — error → action tables
8. `.claude/skills/skill-updater/references/resolution-strategies.md` — merge conflict patterns
9. `.claude/skills/skill-updater/docs/qna.md` — concepts and terminology for humans
10. `.claude/skills/skill-updater/docs/api-reference.md` — command usage reference
11. `.claude/skills/skill-updater/scripts/check-versions.sh` — version comparison script
