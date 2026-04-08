# Skill Distribution & Update Strategy

## Problem Statement

Our team publishes skills to company employees via a "Skill Browser" GitHub repo.
Coworkers download/clone skills and customize them to their preferences. When we
release updates (bug fixes, new features), coworkers can't `git pull` because
their local customizations conflict with our upstream changes.

This is the **fork maintenance problem** applied to Agent Skills.

## Constraints

- Coworkers use various AI tools (Claude Code, Gemini CLI, Cursor, etc.)
- Skills follow the Agent Skills open standard (folder + SKILL.md)
- Coworkers WILL customize skills — this is expected and encouraged
- Updates must be frictionless — most coworkers won't resolve merge conflicts
- Coworkers ARE using coding agents — the update mechanism itself is a skill

---

## Solution: `skill-updater` Skill

Ship a **`skill-updater` skill** alongside the company skills. When the team
releases updates, coworkers invoke `/skill-updater <skill-name>` in their coding
agent. The agent handles everything: fetching upstream, detecting user
customizations via `git diff`, merging intelligently, and committing the result.

The coding agent IS the merge tool.

### Design Decisions

| Decision | Answer | Rationale |
|---|---|---|
| Granularity | Per-skill (`/skill-updater code-review`) | Updating all at once is too dangerous. Users choose what to update, when. |
| Breaking changes | Best-effort + pause | Agent tries to merge. If too complex/dangerous, pauses and asks user. |
| Versioning | Git tags (e.g., `v1.2.0`) on the **repo**, not per-skill | The skills repo contains many skills. Tags are repo-wide releases. A new tag doesn't mean every skill changed — skill-updater diffs the specific skill's files between the user's last-synced tag and the latest tag. If unchanged, "already up to date." Skill authors don't maintain per-skill versions. |
| Dirty working tree | Stash + fallback to file backup | Git stash/pop when git available. File-level backup/ when not. |
| Change detection | `git diff` against upstream | No markers needed. Users edit freely, agent figures out the rest. |
| Rollback | `/skill-updater --revert <skill-name>` | Restores user's pre-update version from backup. One command undo. |
| Source tracking | `metadata.source` in SKILL.md frontmatter | Skills remember where they came from (repo URL, path, last-synced tag). Enables updates even without git remotes. |
| Fetch strategy | Chain: git → GitHub API w/ PAT → API w/o auth → raw URL → local path → ask user | Degrades gracefully. Works whether user has git, PAT, network, or none of the above. |
| Multi-tool support | Scan `~/.claude/`, `~/.opencode/`, `~/.gemini/`, `~/.agent/` + project-scope equivalents | Skills can live in any AI tool's directory. Skill-updater finds them all. |

---

## Workflow

```
                         /skill-updater code-review
                                    │
                    ┌───────────────┘
                    ▼
    ┌───────────────────────────────┐
    │  Phase 1: PRE-FLIGHT          │
    │                               │
    │  1. Check target skill exists │
    │  2. Detect environment:       │
    │     - Git repo with remote?   │
    │       → git-based flow        │
    │     - No git / no remote?     │
    │       → file-based flow       │
    │  3. Fetch upstream versions   │
    │  4. Compare metadata.version  │
    │     local vs upstream         │
    │                               │
    │  Gate: If up to date → STOP   │
    │  Report "v1.2 — already       │
    │  up to date" and exit.        │
    └───────────────┬───────────────┘
                    │ Update available
                    ▼
    ┌───────────────────────────────┐
    │  Phase 2: BACKUP              │
    │                               │
    │  Git flow:                    │
    │  1. Stash uncommitted changes │
    │  2. Create backup tag/branch  │
    │     (e.g., pre-update-        │
    │      code-review-20260408)    │
    │                               │
    │  File flow (no git):          │
    │  1. Copy skill folder to      │
    │     backup/code-review-       │
    │     20260408/                  │
    │                               │
    │  Gate: Backup confirmed       │
    └───────────────┬───────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │  Phase 3: DETECT CHANGES      │
    │                               │
    │  Git flow:                    │
    │  1. git diff origin/main --  │
    │     skills/code-review/       │
    │  2. Categorize:               │
    │     - No local edits          │
    │       → CLEAN UPDATE          │
    │     - Local edits + upstream  │
    │       changes in same files   │
    │       → CONFLICT              │
    │     - Local edits only in     │
    │       files upstream didn't   │
    │       touch → CLEAN UPDATE    │
    │                               │
    │  File flow (no git):          │
    │  1. Diff local files against  │
    │     freshly downloaded        │
    │     upstream version          │
    │  2. Same categorization       │
    └───────────────┬───────────────┘
                    │
            ┌───────┴───────┐
            ▼               ▼
    ┌──────────────┐ ┌──────────────┐
    │ CLEAN UPDATE │ │   CONFLICT   │
    │              │ │              │
    │ Fast-forward │ │ Agent reads: │
    │ or overwrite │ │ - Upstream   │
    │ — no user    │ │   change     │
    │ edits to     │ │   (what &    │
    │ preserve     │ │    why)      │
    └──────┬───────┘ │ - User's     │
           │         │   edit       │
           │         │   (what &    │
           │         │    why)      │
           │         │              │
           │         │ Then:        │
           │         │ - Merge both │
           │         │   if safe    │
           │         │ - Pause &    │
           │         │   ask user   │
           │         │   if risky   │
           │         └──────┬───────┘
           │                │
           └────────┬───────┘
                    ▼
    ┌───────────────────────────────┐
    │  Phase 4: VERIFY & REPORT     │
    │                               │
    │  1. Validate skill structure  │
    │     (SKILL.md exists, front-  │
    │      matter valid, scripts    │
    │      intact)                  │
    │  2. Commit the result         │
    │  3. Pop stash (git flow)      │
    │  4. Report to user:           │
    │     - Updated: v1.0 → v1.2   │
    │     - User customizations     │
    │       preserved: [list]       │
    │     - Backup location         │
    │                               │
    │  Recovery:                    │
    │  "If anything looks wrong,    │
    │   run /skill-updater --revert  │
    │   code-review to restore      │
    │   your previous version."     │
    └───────────────────────────────┘


                /skill-updater --revert code-review
                                    │
                    ┌───────────────┘
                    ▼
    ┌───────────────────────────────┐
    │  REVERT FLOW                  │
    │                               │
    │  Git flow:                    │
    │  1. Find backup tag/branch    │
    │     (pre-update-code-review-  │
    │      20260408)                │
    │  2. Restore skill folder      │
    │     from that ref             │
    │  3. Commit the revert         │
    │                               │
    │  File flow (no git):          │
    │  1. Find backup/code-review-  │
    │     20260408/                 │
    │  2. Replace skill folder      │
    │     with backup copy          │
    │                               │
    │  Report: "Reverted            │
    │  code-review to your          │
    │  pre-update version (v1.0     │
    │  + your customizations).      │
    │  Upstream update discarded."  │
    └───────────────────────────────┘
```

---

## Real-World Scenarios

The skill-updater must handle all of these gracefully:

### Scenario 1: Skill downloaded from corporate GitHub repo

The skill lives in either:
- **User scope**: `~/.claude/skills/`, `~/.opencode/skills/`, `~/.gemini/skills/`, `~/.agent/skills/`
- **Project scope**: `./.claude/skills/`, `./.opencode/skills/`, etc.

Sub-scenarios:
- **1a. Git repo with remote** — ideal case. `git fetch` + tag lookup works.
- **1b. Git repo, no remote** — user deleted remote, or cloned then disconnected. Fall back to `metadata.source` URL + GitHub API or raw download.
- **1c. No git at all** — user copied files manually, or git not installed. Pure file-based flow using `metadata.source` to fetch upstream.

### Scenario 2: Skill received from a coworker

User is a git stranger. Git may not be installed. They received files via Slack, email, USB, shared drive, etc.
- If `metadata.source` exists in the skill's frontmatter → use it to fetch upstream via GitHub API / raw URL.
- If no source metadata → ask user where the skill came from, stamp the metadata for next time.

### Scenario 3: Corporate repo behind PAT

The upstream repo requires authentication. The user who received the skill second-hand has no PAT.
- Try GitHub API without auth first.
- If 401/403 → ask user for PAT.
- If no PAT available → ask user to get updated files from whoever shared the skill, and point skill-updater at a local folder.

### Scenario 4: Upstream has unstable commits

Skill developers commit and push frequently, but only stable commits are tagged with a version (e.g., `v1.2.0`). Skill-updater must:
- Only offer updates for **tagged releases**, never untagged commits.
- Compare the user's `metadata.version` against the **latest semver tag** on upstream.
- Fetch the skill content at that specific tagged commit, not HEAD of main.

---

## Why This Works

1. **The agent understands intent.** Unlike `git merge`, the coding agent can
   read both the upstream change (bug fix? new feature? restructure?) and the
   user's customization (preference tweak? added step? different tool choice?)
   and make a judgment call about how to combine them.

2. **Per-skill resolution strategy.** `skill-updater` can have a per-skill
   strategy table describing what users typically customize and how to
   preserve it.

3. **Git diff for detection.** The agent runs `git diff` against the upstream
   version to see exactly what the user changed. No markers or conventions
   needed from the user — just edit freely, the agent figures out the rest.

4. **Backup before anything.** User's customizations are always backed up
   before any merge attempt. Recovery is one command away.

---

## Skill Repo Structure

### The Skill Browser Repo

```
skill-browser-repo/
├── skills/
│   ├── code-review/
│   │   ├── SKILL.md              # metadata.version: "1.2.0"
│   │   ├── CHANGELOG.md
│   │   ├── scripts/
│   │   └── references/
│   ├── deploy/
│   │   ├── SKILL.md              # metadata.version: "2.0.1"
│   │   └── ...
│   ├── data-pipeline/
│   │   ├── SKILL.md              # metadata.version: "1.0.0"
│   │   └── ...
│   └── ...
│
├── skill-updater/                  # The meta-skill (lives alongside others)
│   ├── SKILL.md                   # Update instructions for the agent
│   ├── references/
│   │   └── resolution-strategies.md
│   └── scripts/
│       └── check-versions.sh
│
└── README.md                      # Skill browser landing page
```

### Skill Template (For Skill Authors)

Every skill follows the Agent Skills standard with versioned frontmatter:

```yaml
---
name: code-review
description: Reviews code for best practices and potential issues.
metadata:
  version: "1.2.0"
  author: "DevTools Team"
---
```

Skills are just standard Agent Skills folders. Users customize SKILL.md
directly (or any file). The `skill-updater` skill handles merging their
changes with upstream updates.

### Layered Override (Complementary)

For skills with well-defined configuration knobs, the layered pattern can
be used as a **complementary** approach — not the primary mechanism:

```
skill-name/
├── SKILL.md                # Core (can also be edited by user)
├── overrides.md            # Optional: user preferences (gitignored)
├── overrides.example.md    # Optional: shows available overrides
└── .gitignore              # Optional: ignores overrides.md
```

When both exist, skill-updater:
- Updates SKILL.md (resolving any user edits via agent merge)
- Leaves overrides.md untouched (gitignored, never conflicts)
- Updates overrides.example.md (so users see new options)

---

## Alternative Approaches Considered (And Why Not)

### A: Layered Override Only (No Agent)
Separate core (SKILL.md) from user config (overrides.md + .gitignore).
- Pro: Zero conflicts on `git pull`
- Con: Limits what users can customize; if they edit SKILL.md anyway, back to
  square one. Good as complementary approach, not primary.

### B: "Don't Customize Core" Policy
Tell coworkers not to modify SKILL.md.
- Pro: Simple
- Con: People won't follow it; no enforcement

### C: Fork-Per-User
Each coworker forks the skill repo.
- Pro: Full freedom
- Con: Unmanageable at scale, no easy path to pull updates

### D: Claude Code Plugin Marketplace Only
Package skills as plugins, use marketplace auto-update.
- Pro: Built-in versioning and auto-update
- Con: Auto-update overwrites customizations; doesn't solve THE problem

### E: Manual Merge Conflicts
Just let coworkers deal with `git pull` conflicts.
- Pro: No extra tooling
- Con: Most coworkers won't do it; skills stay outdated forever

---

## Next Steps

- [x] Decide on design decisions (granularity, versioning, backup, etc.)
- [ ] Draft the `skill-updater` SKILL.md
- [ ] Define the per-skill resolution strategy table format
- [ ] Build a prototype: one example skill + skill-updater + test scenario
- [ ] Test with Claude Code, Gemini CLI, and at least one other agent
- [ ] Write a "skill author guide" — how to write update-friendly skills
- [ ] Write a "skill user guide" — how to customize and update skills
