# Skill Updater — Test Plan

## Test Environment

- **Repo:** `aiagent/experimental-skills` (https://github.samsungds.net/aiagent/experimental-skills)
- **Remote:** local repo has `origin` pointing to the same URL as
  `metadata.source.url` in the SKILL.md file on disk. This makes the skill
  **Origin A** (git-cloned, full git flow available).
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

### Key principle under test

**The file on disk is the truth. Git history is just a reference.**

- Local state = the actual SKILL.md file on disk (not `git show HEAD:...`)
- Base version = fetched from the **remote** (not local git tags)
- Upstream version = fetched from the **remote** (not local git tags)

The tests below verify that skill-updater works correctly regardless of
messy local git history (dummy commits, merges, reverts).

---

## Test 1: `--check` Scan (Read-Only Status Report)

### What it tests

The `--check` flow: scanning all skills, reading their SKILL.md files on disk,
classifying their origins, fetching upstream tags from the remote, and displaying
a status table. This is read-only — it reports what updates are available but
changes nothing. Run this first to verify the environment works.

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
2. **Reads each SKILL.md file on disk** to get version and repo_tag
3. Classifies each skill's origin
4. For skills with `metadata.source`, fetches latest repo tag from the remote
5. Groups skills from the same repo to avoid redundant API calls
6. Displays a status table showing version, repo tag, and status

### Pass criteria

- [ ] Finds both `brand-guidelines` and `skill-updater`
- [ ] Shows correct `metadata.version` for each (read from file on disk)
- [ ] Shows correct `metadata.source.repo_tag` for each (read from file on disk)
- [ ] brand-guidelines shows "Update available" (1.0.0 → 1.1.0)
- [ ] skill-updater shows "Up to date" (its files didn't change between repo tags v1.0.0 and v1.1.0)
- [x] Skills without `metadata.source` show appropriate status
- [x] Table is readable and well-formatted

### Actual result

> **PASS** (2026-04-09, Samsung corporate environment)
>
> All criteria met:
> - [x] Found both `brand-guidelines` and `skill-updater`
> - [x] Correct `metadata.version` for each (1.0.0, read from file on disk)
> - [x] Correct `metadata.source.repo_tag` for each (v1.0.0)
> - [x] brand-guidelines shows "Update available" (1.0.0 → 1.1.0)
> - [x] skill-updater shows "Up to date" (no changes between tags)
> - [x] No skills without `metadata.source` in this environment
> - [x] Table is readable and well-formatted
>
> Observations:
> - Remote name is `internal`, not `origin` — AI handled it correctly by
>   checking `git remote -v`. SKILL.md updated to not assume `origin`.
> - `gh` CLI not available — skipped silently, used git instead.
> - Used `git fetch internal --tags --force` (correct).
> - `git show v1.1.0:...` used after force-fetch — acceptable since tags
>   were just synced from remote.

---

## Test 2: Happy Path Update (Everything Goes Right)

### What it tests

The full 5-phase workflow end-to-end: pre-flight → backup → detect changes →
apply update → verify & report. "Happy path" means the ideal scenario where
all tools work, the network is available, and no errors occur. This is the most
important test — it exercises every phase of the skill.

### Pre-conditions

- `brand-guidelines/SKILL.md` file on disk has:
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
   - **Reads the SKILL.md file on disk** (not git history)
   - Classifies as **Origin A** (git-cloned, remote matches source URL)
   - Reads `metadata.version: "1.0.0"`, `repo_tag: "v1.0.0"` from the file
   - Fetches tags from remote via `git fetch --tags --force`
   - Finds `v1.1.0` as latest tag
   - Fetches upstream SKILL.md **from the remote** at v1.1.0 tag
   - Reads upstream `metadata.version: "1.1.0"`
   - Displays: "Update available: v1.0.0 → v1.1.0 (repo tag: v1.0.0 → v1.1.0)"

2. **Phase 1.7 — Confirm with user:**
   - Shows file-level preview of what will change
   - Asks user to confirm before proceeding

3. **Phase 2 — Backup:**
   - Creates file-based backup (`cp -r`) to capture working-tree state
   - Also creates backup branch: `pre-update-brand-guidelines-YYYYMMDD`

4. **Phase 3 — Detect changes (three-way comparison):**
   - Gets base version **from the remote** at v1.0.0 tag
   - Reads local version **from the file on disk**
   - Gets upstream version **from the remote** at v1.1.0 tag
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

- [x] Samsung Blue (`#1428a0`) is preserved in the merged file
- [x] Dark Mode section is present in the merged file
- [x] Variable font weight line is present in Font Management
- [x] `metadata.version` is `"1.1.0"`
- [x] `metadata.source.repo_tag` is `"v1.1.0"`
- [x] `metadata.source.updated_at` is today's date
- [x] File-based backup exists
- [x] User was asked to confirm before changes were applied
- [x] Final report clearly shows what changed and what was preserved
- [x] Base and upstream were fetched from the remote (not local git tags)

### Actual result

> **PASS** (2026-04-09, Samsung corporate environment, 2nd attempt)
>
> All criteria met. The AI used `diff -u` to compare the local file against
> the upstream file saved to a temp file — deterministic detection, no
> context rot risk.
>
> **1st attempt (FAIL):** AI read both files and "mentally" compared them,
> relied on `git diff v1.0.0 v1.1.0` between tags (which showed almost no
> diff due to misconfigured v1.0.0 tag on Samsung remote). Concluded
> "nothing to merge" and only updated metadata.
>
> **Fix applied:** Phase 1.5 and Phase 3 rewritten to:
> 1. Save upstream file to temp file
> 2. Run `diff -u local /tmp/upstream` (diff tool, not mental comparison)
> 3. Compare local vs upstream directly (not tag-vs-tag)
>
> **2nd attempt (PASS):** AI used diff tool, found all differences (Dark
> Mode, variable font weights, Samsung Blue), applied merge correctly,
> preserved user's internal source URL.
>
> User customization preserved: `metadata.source.url` kept as Samsung
> internal GitHub Enterprise URL.

---

## Test 3: Re-run After Successful Update (Idempotency)

### What it tests

Verifies that running skill-updater again after a successful update correctly
reports "up to date" — by reading the file on disk, not git history.

### Pre-conditions

- Test 2 completed successfully
- brand-guidelines SKILL.md on disk has `version: "1.1.0"`, `repo_tag: "v1.1.0"`

### Invocation

```
/skill-updater brand-guidelines
```

### Expected behavior

Skill-updater reads the file, sees `repo_tag: "v1.1.0"`, fetches tags from
remote, finds `v1.1.0` is the latest → reports "up to date."

### Pass criteria

- [x] Reads version info from the file on disk
- [x] Correctly reports "up to date"
- [x] Does NOT attempt to re-merge or modify files

### Actual result

> **PASS** (2026-04-09, Samsung corporate environment)
>
> All criteria met. AI read the file on disk (v1.1.0, repo_tag v1.1.0),
> fetched tags from remote (latest is v1.1.0), and reported "already up
> to date."
>
> Bonus: even though tags matched, the AI still ran `diff -u` between
> local and upstream to verify. The diff showed only user customizations
> (Samsung Blue, updated_at) — correctly identified as user changes, not
> missing upstream content. No files modified.

---

## Test 4: `--revert` After Update (Undo an Update)

### What it tests

The revert flow: restoring the skill to its pre-update state from the backup
created in Test 2. This tests whether the user can safely undo an update if
they're unhappy with the result.

### Pre-conditions

- Test 2 has been completed successfully (brand-guidelines was updated)
- File-based backup `brand-guidelines.backup-*` exists
- brand-guidelines is currently at v1.1.0 (post-update merged state)

### Invocation

```
/skill-updater --revert brand-guidelines
```

### Expected workflow

1. Finds the most recent file-based backup for brand-guidelines
2. Restores skill folder from the file backup (preferred over git branch)
3. Commits the revert
4. Reports: "Reverted brand-guidelines to your pre-update version"

### Pass criteria

- [x] brand-guidelines/SKILL.md is restored to pre-update state
- [x] Samsung Blue customization (`#1428a0`) is back
- [x] Dark Mode section is gone (it was from upstream)
- [x] `metadata.version` is back to `"1.0.0"`
- [x] `metadata.source.repo_tag` is back to `"v1.0.0"`
- [x] Revert commit exists in git log
- [x] File-based backup was used (not git branch)

### Actual result

> **PASS** (2026-04-09, Samsung corporate environment, 2nd attempt)
>
> All criteria met. Full revert flow executed correctly:
> - [x] Found file-based backup (`brand-guidelines.backup-20260409`)
> - [x] Restored with `cp -r` (full directory)
> - [x] Deleted backup directory after restore (cleanup)
> - [x] Deleted local v1.1.0 tag (cleanup)
> - [x] Committed the revert
> - [x] Clean report showing version reverted and cleanup done
>
> **Known issue:** Natural language revert requests (e.g., "스킬 원상복구
> 해줘") do NOT trigger the skill-updater skill automatically. The AI
> handles the restore manually without loading the skill. Adding
> "(skill-updater 스킬 사용해서)" to the request triggers the skill
> correctly. This is a platform-level limitation.

---

## Test 5: Messy Local History (Robustness Test)

### What it tests

Verifies that skill-updater works correctly even when the local git history is
messy — dummy commits, merge commits, reverts, stale local tags. This is the
scenario that exposed the "file on disk is the truth" principle.

### Pre-conditions

This test requires Tests 1-4 to have been run first. After those tests,
the local repo naturally has a messy git history:

- Multiple skill-updater update and revert commits
- Possibly dummy commits from earlier testing
- Local tags may have been deleted and re-fetched

The key condition: **brand-guidelines/SKILL.md on disk has `version: "1.0.0"`
and `repo_tag: "v1.0.0"`** (restored by Test 4), but `git log` shows previous
update commits (from Test 2) that say "update brand-guidelines v1.0.0 → v1.1.0".

This creates a contradiction: the file says v1.0.0, but git history says
the update already happened. Skill-updater must trust the file, not git history.

### Invocation

```
/skill-updater brand-guidelines
```

### Expected behavior

Skill-updater should:
1. **Read the SKILL.md file on disk** and see `version: "1.0.0"`
2. Offer the update (v1.0.0 → v1.1.0) — ignoring git history
3. Fetch base and upstream **from the remote** (not stale local tags)
4. Perform the merge correctly

It should NOT:
- Say "already up to date" based on git log
- Use stale local tag content for the three-way comparison
- Be confused by the messy commit history

### Pass criteria

- [x] Skill-updater reads the file on disk, not git history
- [x] Offers update despite git log showing a previous update commit
- [x] Fetches base/upstream from remote (uses `--tags --force`)
- [x] Produces correct merge result
- [x] `metadata.version` is `"1.1.0"` after merge
- [x] Samsung Blue preserved

### Actual result

> **PASS** (2026-04-09, Samsung corporate environment)
>
> All criteria met. Git log showed multiple update/revert cycles and
> dummy commits ("tttttt", "fdafsdfsdafsa", "123"), but the AI:
> - Read the file on disk (v1.0.0), not git history
> - Offered the update despite git log showing previous update commits
> - Used `git fetch --tags --force` and `diff -u` with temp files
> - Correctly applied Dark Mode, variable font weights, Samsung Blue
>
> The AI spent extra thinking time analyzing the confusing base version
> (v1.0.0 tag on remote had v1.1.0 content), but correctly fell back to
> local-vs-upstream comparison as the primary driver.

---

## Test 6: No Metadata (What Happens When Origin is Unknown)

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
2. **Reads the SKILL.md file on disk** — no `metadata.source` found
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

## Test Execution Order

Run the tests in order: 1 → 2 → 3 → 4 → 5 → 6.

| Test | What | Why this order |
|---|---|---|
| 1 | `--check` scan | Read-only, lowest risk — verifies environment first |
| 2 | Happy path update | Full workflow — the main test |
| 3 | Re-run after update | Idempotency — depends on Test 2 succeeding |
| 4 | `--revert` | Undo — depends on Test 2's backup |
| 5 | Messy history | Robustness — needs messy state after Tests 2-4 |
| 6 | No metadata | Interactive stamping — independent, run last |

After all tests, run Samsung-specific edge cases (proxy, no `gh`, auth failures).

---

## Future Tests (Samsung Corporate Environment)

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
