# Skill Updater — Test Plan

## Test Environment

- **Repo:** `Taekyo-Lee/my-skills` (https://github.com/Taekyo-Lee/my-skills)
- **Test skill:** `brand-guidelines` at `.claude/skills/brand-guidelines/`
- **Tags on GitHub remote:**
  - `v1.0.0` — baseline release (brand-guidelines `metadata.version: "1.0.0"`)
  - `v1.1.0` — added Dark Mode section, variable font weight line (brand-guidelines `metadata.version: "1.1.0"`)
- **Upstream changes in v1.1.0 (compared to v1.0.0):**
  - Added new "Dark Mode" section (between Colors and Typography)
  - Added variable font weight line to Font Management section
  - Bumped `metadata.version` from `"1.0.0"` to `"1.1.0"`
- **Local user customization (uncommitted edits on top of v1.0.0 baseline):**
  - Blue accent color changed from `#6a9bcc` to `#1428a0` (Samsung Blue)

This setup creates a realistic three-way merge scenario: the user has local
edits (Samsung Blue) on v1.0.0, while upstream has moved to v1.1.0 with new
content. The updater must pull in the new content without losing the user's
customization.

---

## Test 1: Happy Path Update (Everything Goes Right)

### What it tests

The full 5-phase workflow end-to-end: pre-flight → backup → detect changes →
apply update → verify & report. "Happy path" means the ideal scenario where
all tools work, the network is available, and no errors occur. This is the most
important test — it exercises every phase of the skill.

### Pre-conditions

- `brand-guidelines/SKILL.md` is local with:
  - `metadata.version: "1.0.0"`
  - `metadata.source.repo_tag: "v1.0.0"`
  - User customization: Samsung Blue (`#1428a0`)
- Remote has `v1.1.0` tag with upstream changes
- Git is available, repo has remote pointing to source

### Invocation

```
/skill-updater brand-guidelines
```

### Expected workflow

1. **Phase 1 — Pre-flight:**
   - Locates skill at `.claude/skills/brand-guidelines/`
   - Classifies as **Origin A** (git-cloned, remote matches source URL)
   - Reads `metadata.version: "1.0.0"`, `repo_tag: "v1.0.0"`
   - Fetches tags via git, finds `v1.1.0` as latest
   - Diffs skill files between `v1.0.0` and `v1.1.0` — detects changes
   - Reads upstream `metadata.version: "1.1.0"` from v1.1.0 tag
   - Displays: "Update available: v1.0.0 → v1.1.0 (repo tag: v1.0.0 → v1.1.0)"

2. **Phase 1.7 — Confirm with user:**
   - Shows file-level preview of what will change
   - Asks user to confirm before proceeding

3. **Phase 2 — Backup:**
   - Creates file-based backup (`cp -r`) to capture working-tree state
   - Also creates backup branch: `pre-update-brand-guidelines-20260408`

4. **Phase 3 — Detect changes (three-way comparison):**
   - Gets base version (v1.0.0 content from git tag)
   - Compares base vs. local (user's edits) and base vs. upstream (v1.1.0)
   - Categorizes each change by section within SKILL.md:
     - Dark Mode section: **CLEAN** — only upstream added it, user didn't
       touch this area
     - Font Management line: **CLEAN** — only upstream added it
     - Blue accent color: **USER-ONLY** — only user changed it (upstream
       still has `#6a9bcc`)
     - `metadata.version`: **CLEAN** — only upstream bumped it

5. **Phase 4 — Apply update (merge based on categories):**
   - Dark Mode section: CLEAN → accept upstream. Add between Colors and
     Typography.
   - Font Management variable font line: CLEAN → accept upstream. Add the line.
   - Blue accent color: USER-ONLY → keep user's Samsung Blue (`#1428a0`).
   - `metadata.version`: CLEAN → accept upstream `"1.1.0"`
   - `metadata.source.repo_tag`: Update to `"v1.1.0"`
   - `metadata.source.updated_at`: Update to today's date

6. **Phase 5 — Verify and report:**
   - Validates frontmatter is valid YAML
   - Commits the result
   - Reports: "Updated brand-guidelines: v1.0.0 → v1.1.0"
   - Lists changes applied and customizations preserved

### Pass criteria

- [ ] Samsung Blue (`#1428a0`) is preserved in the merged file
- [ ] Dark Mode section is present in the merged file
- [ ] Variable font weight line is present in Font Management
- [ ] `metadata.version` is `"1.1.0"`
- [ ] `metadata.source.repo_tag` is `"v1.1.0"`
- [ ] `metadata.source.updated_at` is today's date
- [ ] Backup branch exists
- [ ] User was asked to confirm before changes were applied
- [ ] Final report clearly shows what changed and what was preserved

### Actual result

> **PASS** (2026-04-08)
>
> All criteria met:
> - [x] Samsung Blue (`#1428a0`) preserved in merged file
> - [x] Dark Mode section present
> - [x] Variable font weight line present in Font Management
> - [x] `metadata.version` is `"1.1.0"`
> - [x] `metadata.source.repo_tag` is `"v1.1.0"`
> - [x] `metadata.source.updated_at` is `"2026-04-08"`
> - [x] Backup branch `pre-update-brand-guidelines-20260408` exists
> - [x] User was asked to confirm before changes were applied
> - [x] Final report clearly shows changes applied and customizations preserved
>
> Note: All changes categorized correctly — user edits (Samsung Blue,
> metadata.source) were USER-ONLY, upstream additions (Dark Mode, variable
> font, version bump) were CLEAN. No CONFLICT files. Three-way merge
> worked as designed.

---

## Test 2: `--check` Scan (Read-Only Status Report)

### What it tests

The `--check` flow: scanning all skills, classifying their origins,
fetching upstream tags, and displaying a status table. This is read-only —
it reports what updates are available but changes nothing.

### Pre-conditions

- `brand-guidelines` has `metadata.source` with a known upstream repo
- `skill-updater` has `metadata.source` with the same upstream repo
- Other skills in the environment may or may not have `metadata.source`

### Invocation

```
/skill-updater --check
```

### Expected workflow

1. Scans all known skill locations (user-scope + project-scope)
2. Finds `brand-guidelines` and `skill-updater` (and possibly others)
3. Classifies each skill's origin
4. For skills with `metadata.source`, fetches latest repo tag
5. Groups skills from the same repo to avoid redundant API calls
6. Displays a status table showing version, repo tag, and status

### Pass criteria

- [ ] Finds both `brand-guidelines` and `skill-updater`
- [ ] Shows correct `metadata.version` for each
- [ ] Shows correct `metadata.source.repo_tag` for each
- [ ] brand-guidelines shows "Update available" (1.0.0 → 1.1.0)
- [ ] skill-updater shows "Up to date" (its files didn't change between repo tags v1.0.0 and v1.1.0)
- [ ] Skills without `metadata.source` show appropriate status
- [ ] Table is readable and well-formatted

### Actual result

> **PASS** (2026-04-08)
>
> All criteria met:
> - [x] Found both `brand-guidelines` and `skill-updater`
> - [x] Correct `metadata.version` for each (1.0.0)
> - [x] Correct `metadata.source.repo_tag` for each (v1.0.0)
> - [x] brand-guidelines shows "Update available" (1.0.0 → 1.1.0)
> - [x] skill-updater shows "Up to date" (its files didn't change between repo tags)
> - [x] Table is readable and well-formatted
> - [x] Grouped API calls — one tag fetch for the shared repo
>
> Note: skill-updater correctly identified that despite a new repo tag
> (v1.1.0), the skill-updater files didn't change between tags.

---

## Test 3: `--revert` After Update (Undo an Update)

### What it tests

The revert flow: restoring the skill to its pre-update state from the backup
created in Test 1. This tests whether the user can safely undo an update if
they're unhappy with the result.

### Pre-conditions

- Test 1 has been completed successfully (brand-guidelines was updated)
- Backup branch `pre-update-brand-guidelines-*` exists
- brand-guidelines is currently at v1.1.0 (post-update merged state)

### Invocation

```
/skill-updater --revert brand-guidelines
```

### Expected workflow

1. Finds the most recent backup branch for brand-guidelines
2. Restores skill folder from that branch
3. Commits the revert
4. Reports: "Reverted brand-guidelines to your pre-update version"

### Pass criteria

- [ ] brand-guidelines/SKILL.md is restored to pre-update state
- [ ] Samsung Blue customization is back
- [ ] Dark Mode section is gone (it was from upstream)
- [ ] `metadata.version` is back to `"1.0.0"`
- [ ] `metadata.source.repo_tag` is back to `"v1.0.0"`
- [ ] Revert commit exists in git log

### Actual result

> **FAIL → BUG FOUND → FIXED** (2026-04-08)
>
> The revert restored the wrong state. The backup branch contained the
> committed v1.0.0 upstream content (without Samsung Blue), not the user's
> actual pre-update state on disk (v1.0.0 + Samsung Blue customization).
>
> **Root cause:** `git branch` only captures committed state, not the
> working tree. The user's Samsung Blue customization was an uncommitted
> edit, so the backup branch missed it entirely.
>
> **Fix applied:** Rewrote Phase 2 backup to always do a file-based backup
> (`cp -r`) first, which captures the working tree. Git branch backup is
> now secondary. Also rewrote revert flow to prefer file-based backup.
> Logged in `references/field-notes.md`.
>
> **Self-evolution mechanism worked** — bug discovered during testing,
> logged, and promoted into a skill update in one pass.
>
> - [ ] Re-test after fix (needs fresh test scenario)

---

## Test 4: No Metadata (What Happens When Origin is Unknown)

### What it tests

The origin classification and interactive stamping workflow when a skill has
no `metadata.source` block. Without source metadata, skill-updater doesn't
know where to check for updates, so it must ask the user.

### Pre-conditions

- Create or find a skill with no `metadata.source` in its frontmatter
- (Can simulate by temporarily removing `metadata.source` from a skill)

### Invocation

```
/skill-updater <skill-without-source>
```

### Expected workflow

1. Locates the skill
2. Reads frontmatter — no `metadata.source` found
3. Triggers the interactive stamping workflow
4. Asks user where the skill came from (6 options)
5. Based on answer:
   - "I wrote it myself" → Reports "local skill, nothing to update"
   - "From a GitHub repo" → Asks for URL, stamps metadata, proceeds

### Pass criteria

- [ ] Detects missing `metadata.source`
- [ ] Asks the user about the skill's origin
- [ ] Handles "user-authored" response correctly (no update, no stamp)
- [ ] Handles "from GitHub" response correctly (stamps and proceeds)
- [ ] Does NOT crash or dead-end

### Actual result

> (to be filled after testing)

---

## Test 3b: Re-test `--revert` with Fixed Backup

### What it tests

Re-run of Test 3 after the backup bug fix. Verifies that the new file-based
backup (`cp -r`) correctly captures the full working-tree state — including
uncommitted user customizations that the old git-branch backup missed.

### Pre-conditions

Reset brand-guidelines to a state that simulates a user at v1.0.0 with
uncommitted customizations:
```
1. Restore brand-guidelines/SKILL.md to v1.0.0 base content
2. Add metadata.source block (pointing to Taekyo-Lee/my-skills, repo_tag v1.0.0)
3. Change Blue accent to Samsung Blue (#1428a0)
4. Do NOT commit these changes — they must be uncommitted
```

### Invocation

```
/skill-updater brand-guidelines        # should create file-based backup
/skill-updater --revert brand-guidelines  # should restore from file backup
```

### Pass criteria

- [ ] File-based backup `brand-guidelines.backup-*` is created before update
- [ ] The backup contains the user's uncommitted state (Samsung Blue + metadata.source)
- [ ] After revert, Samsung Blue (`#1428a0`) is restored
- [ ] After revert, `metadata.source` block is restored
- [ ] After revert, Dark Mode section is gone
- [ ] After revert, `metadata.version` is `"1.0.0"`

### Actual result

> (to be filled after testing)

---

## Test Execution Order

**Round 1 — Home environment (2026-04-08) — completed:**
1. **Test 2** (`--check` scan) — PASS
2. **Test 1** (happy path update) — PASS
3. **Test 3** (`--revert`) — FAIL → backup bug found → fixed in code

**Round 2 — Samsung corporate environment (2026-04-09):**
1. **Test 3b** (re-test `--revert` with fixed backup logic) — first priority
2. **Test 4** (no metadata / interactive origin classification)
3. Samsung-specific edge cases (proxy, no `gh`, auth failures)

---

## Future Tests (Samsung Corporate Environment — 2026-04-09)

These tests will be conducted at Samsung Electronics where strict security
policies apply. Expected failure areas:

| Scenario | What might fail | How skill-updater should handle it |
|---|---|---|
| Corporate proxy | `git fetch`, `curl` to GitHub blocked | Detect in environment check, skip to local path |
| No `gh` CLI | Can't install `gh` (no admin rights) | Skip Strategy 2 silently, fall through |
| No PAT available | Can't authenticate to private repos | Accept gracefully, offer local path |
| VPN-only network | Intermittent connectivity | Timeout handling, fall through |
| SSO/SAML required | Token exists but org requires SSO auth | Suggest authorization steps |

Each failure encountered will be logged to `references/field-notes.md` and
promoted into the main reference files via the self-evolution mechanism.
