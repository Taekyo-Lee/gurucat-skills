---
name: skill-updater
description: >
  Updates locally-customized Agent Skills to the latest upstream version while
  preserving user customizations. Use this skill whenever the user wants to update
  a skill, sync a skill with upstream, pull the latest version of a skill, check
  if skills are outdated, or revert a skill update. Also use when the user mentions
  "skill-updater", "update skills", "sync skills", "pull latest skill", "get the
  latest version", or asks about skill versions. This skill should also be used when
  someone says things like "is my skill up to date?", "there's a new version of X",
  "my coworker updated the skill", "pull changes from the skill repo", or "I want
  to check for skill updates". Even if the user doesn't say "skill" explicitly but
  is clearly talking about updating agent instructions or tool configurations that
  follow the SKILL.md standard, use this skill. Handles the fork maintenance
  problem — users freely customize skills, and this skill intelligently merges
  upstream updates without losing those customizations.
metadata:
  version: "1.0.0"
  author: "DevTools Team"
  source:
    repo: "Taekyo-Lee/my-skills"
    url: "https://github.com/Taekyo-Lee/my-skills"
    path: ".claude/skills/skill-updater"
    repo_tag: "v1.0.0"
    updated_at: "2026-04-08"
---

# Skill Updater

You are helping the user update an Agent Skill to its latest upstream version
while preserving their local customizations. The coding agent (you) is the merge
tool — you understand intent behind both upstream changes and user edits, and can
make intelligent merge decisions that `git merge` cannot.

## Invocation

```
/skill-updater <skill-name>              # Update a skill
/skill-updater --revert <skill-name>     # Revert to pre-update version
/skill-updater --check                   # Check all skills for available updates
```

If the user says something like "update the code-review skill" or "sync my skills
with upstream", parse the intent and proceed accordingly.

---

## Fundamental Principle: The File on Disk is the Truth

**The SKILL.md file on disk is the single source of truth. Git history is
just a reference.**

This principle governs every phase of skill-updater:

| What | Where to look | NEVER use |
|---|---|---|
| Local state | Read the actual SKILL.md file on disk | `git show HEAD:...`, `git log`, commit history |
| Local version | `metadata.version` inside the SKILL.md file | Git tags, commit messages |
| Local repo_tag | `metadata.source.repo_tag` inside the SKILL.md file | Local git tags |
| Base version | Fetch from the **remote** at the user's `repo_tag` | `git show <tag>:...` (local tag, potentially stale) |
| Upstream version | Fetch from the **remote** at the latest tag | `git show <tag>:...` (local tag, potentially stale) |

**Why this matters:** Users make commits, reverts, merges, and messy edits.
Local git tags can become stale and point to wrong commits. Even if a perfect
merge was committed a minute ago, the user may have reverted the files without
committing. If skill-updater trusted git history, it would incorrectly say
"already up to date" — but the file on disk says otherwise.

The SKILL.md file is what the user actually sees and uses. That is the truth.
Git is a tool for fetching remote content and creating backups, nothing more.

---

## How it works (happy path)

In the common case — a skill cloned from a GitHub repo with `metadata.source`
intact — the flow looks like this:

1. **Find the skill** and read its SKILL.md file on disk. Classify its origin.
2. **Check environment** — git, `gh`, network available?
3. **Fetch the latest repo tag from the remote** and fetch the upstream skill
   files at that tag from the remote.
4. **Show the user what changed** and ask to confirm before proceeding.
5. **Back up** the current skill files (file copy, then optional git branch).
6. **Compare three versions** — base (fetched from remote at user's repo_tag),
   local (the actual file on disk), upstream (fetched from remote at latest tag).
7. **Apply the update** — overwrite clean files, intelligently merge conflicts.
8. **Verify and report** — validate structure, commit, show summary.

If anything goes wrong, fall back gracefully. If the merge is too complex,
pause and ask the user. Recovery is always one command away:
`/skill-updater --revert <name>`.

---

## Versioning Model

Skills use a **two-level versioning model**:

1. **`metadata.version`** — per-skill version (e.g., `1.2.0`), set by the skill
   author. This is what users see: "code-review v1.0.0 → v1.2.0".
2. **`metadata.source.repo_tag`** — repo-wide release tag (e.g., `v2.5.0`),
   covering the entire skills repo. A single tag includes all skills, but not
   every skill changes between tags.

The update flow uses both:
1. Compare `repo_tag` against the latest repo tag → "is there a new release?"
2. Diff the skill's files between those tags → "did this skill actually change?"
3. If changed, read the upstream skill's `metadata.version` → show the per-skill
   version bump to the user.

## Source Metadata

Every skill should carry its origin and version in the SKILL.md frontmatter so
the updater knows where to fetch from — even without git, remotes, or network
context:

```yaml
metadata:
  version: "1.2.0"
  source:
    repo: "company/skill-browser"
    url: "https://github.company.com/company/skill-browser"
    path: "skills/code-review"
    repo_tag: "v2.5.0"
    updated_at: "2026-04-01"
```

| Field | Set by | Purpose |
|---|---|---|
| `metadata.version` | Skill author | Per-skill version. What users see in update reports. |
| `metadata.source.repo_tag` | skill-updater | Repo-wide release tag the user last synced from. |
| `metadata.source.repo` | Skill author | GitHub `owner/repo` slug. |
| `metadata.source.url` | Skill author | Full URL to the source repo (supports GitHub Enterprise). |
| `metadata.source.path` | Skill author | Path to this skill within the repo. |
| `metadata.source.updated_at` | skill-updater | Date of last successful update. |

**Key concept:** `repo_tag` is a repo-wide release tag, NOT a per-skill version.
The skills repo contains many skills, and a single tag covers the whole repo. A
new repo tag doesn't mean every skill changed — the updater diffs the specific
skill's files between the user's `repo_tag` and the latest tag to determine if
that skill actually has updates.

**Single-skill repos:** If the repo contains only one skill, `repo_tag` and
`metadata.version` may track the same value — that's fine. The two-level
model is designed for mono-repos with many skills but degrades gracefully to
the single-skill case.

If a skill has no `metadata.source`, ask the user where it came from and stamp
it for future updates. If it has `metadata.source` but no `metadata.version`,
treat the per-skill version as unknown (`0.0.0`) and note it in the report.

---

## Phase 1: Pre-flight

Before doing anything, establish context.

### 1.1 Locate the skill

Find the target skill folder. Skills follow the Agent Skills standard — a folder
containing a `SKILL.md` file with YAML frontmatter.

Scan these locations (both user-scope and project-scope):

**User scope:**
- `~/.claude/skills/<skill-name>/`
- `~/.opencode/skills/<skill-name>/`
- `~/.gemini/skills/<skill-name>/`
- `~/.agent/skills/<skill-name>/`

**Project scope:**
- `./.claude/skills/<skill-name>/`
- `./.opencode/skills/<skill-name>/`
- `./.gemini/skills/<skill-name>/`
- `./.agent/skills/<skill-name>/`

**Other:**
- `./skills/<skill-name>/`
- The current working directory if it contains `SKILL.md`

If the skill isn't found, tell the user and list available skills found across
all locations.

Once found, **read the SKILL.md frontmatter** and classify the skill's origin.
This determines the entire update strategy.

**Classify the origin** by answering three questions:

1. **Does `metadata.source` exist?**
   - Yes → source is known. Go to question 2.
   - No → ask the user where the skill came from (see `references/origin-classification.md`
     for the interactive stamping workflow). If they wrote it themselves or an AI
     generated it, there's **no upstream — nothing to update.** Stop here.

2. **Is `metadata.source.url` a GitHub URL?**
   - Yes → `gh` CLI and git strategies are available.
   - No → non-GitHub source. Skip `gh`, use git (if cloned) or raw URL / local path.

3. **Is the skill inside a git repo whose remote matches the source URL?**
   - Yes → **Origin A** (git-cloned). Full git flow — best case.
   - No → **Origin B** (has metadata, no git connection). Use `gh` or download.

Read `references/origin-classification.md` for the full origin type table and
the stamping workflow for skills with unknown origins.

### 1.2 Detect environment

Build a capability profile: check for `git`, `gh` (+ auth status), environment
tokens (`GITHUB_TOKEN`/`GH_TOKEN`), network connectivity, and source metadata.
The fetch chain (1.4) uses this profile to skip unavailable strategies.

Key flags: `has_git`, `in_repo`, `has_remote`, `has_gh`, `gh_authed`,
`has_token`, `has_network`, `has_source`.

Read `references/environment-detection.md` for the full detection procedure,
commands, and capability profile table.

### 1.3 Read local version info

**Read the actual SKILL.md file on disk** (not from git history) and parse the
frontmatter to extract:

- **`metadata.version`** — the per-skill version the user currently has (e.g., `1.0.0`)
- **`metadata.source.repo_tag`** — the repo-wide release tag the skill was last synced from (e.g., `v2.3.0`)

**Important:** These values come from the file the user has right now, not from
`git log`, `git show HEAD:...`, or any commit. The file on disk may differ from
what git history says — the file is the truth.

If `repo_tag` is missing, treat the skill as unversioned — it needs a full
comparison against upstream (skip to Phase 3 with worst-case assumptions).

If `metadata.version` is missing, set it to `0.0.0` for display purposes and
note this in the report. The upstream version will be read in Phase 1.5.

### 1.4 Fetch the latest stable repo tag

Skill developers commit frequently, but only stable releases get repo-wide
version tags (e.g., `v2.5.0`). The skill-updater only works with tagged
releases — never raw HEAD commits.

**Early-exit gates:**

- **Origin D (local — user-authored or AI-generated):** Stop here. Report:
  "This is a local skill with no upstream source. Nothing to update." Exit.
- **Origin C (no metadata, user couldn't identify source):** Stop here.
  Report: "I don't know where this skill came from, so I can't check for
  updates. If you learn the source later, run `/skill-updater <name>` again
  and I'll stamp it." Exit.
- **Origin F (non-GitHub source):** Skip Strategy 2 (`gh` only works with
  GitHub). Strategy 1 (git) still works if the user has the repo cloned
  with a matching remote. Otherwise go to Strategy 3 (raw URL) or 4
  (local path).
- **`has_network = false`:** Skip all remote strategies (1, 2, 3). Go
  straight to Strategy 4 (local path).

Try strategies in order: **1. git tags** → **2. `gh` CLI** → **3. raw URL** →
**4. local path** → **5. ask user**. Each strategy falls through to the next
on failure. Strategy 5 summarizes what was tried and offers actionable next
steps — never dead-end.

Read `references/fetch-strategies.md` for per-strategy prerequisites, commands,
failure mode tables, and user-facing messages.

### 1.5 Fetch the upstream file and compare against local

**The core job of skill-updater: make the local file match the upstream version
at the latest tag, while preserving user customizations.**

The trigger for an update is simple: the user's `repo_tag` (from the file on
disk) differs from the latest tag on the remote. Once triggered, the skill-updater
must compare the **local file on disk** against the **upstream file from the
remote** — this is the primary comparison that determines what to do.

**Important:** The remote name may not be `origin` — find the remote whose URL
matches `metadata.source.url` by checking `git remote -v`, then use that remote
name in all git commands.

**Step 1: Fetch tags from remote:**
```bash
git remote -v
# Find the remote matching metadata.source.url

git fetch <remote> --tags --force
```

**Step 2: Fetch the upstream SKILL.md from the remote at the latest tag:**
```bash
git show <latest-tag>:<metadata.source.path>/SKILL.md
```
(This is safe because `--tags --force` was just run, so local tags match remote.)

**Step 3: Compare the local file on disk against the upstream file.**

Read both files and identify the differences. This is the comparison that
matters — NOT `git diff` between tags. The `git diff` between tags only tells
you what changed in the repo between releases. But the local file may be very
different from both tags due to user customizations.

If the local file and upstream file are **identical** (except possibly for
`metadata.source` fields):
> `<skill-name>` is up to date.

Then stop. Update `metadata.source.repo_tag` to the latest tag if needed.

If there are **meaningful differences** between local and upstream:

1. **Read the upstream `metadata.version`** from the fetched file.
2. Display the version context to the user:
   > Update available for `<skill-name>`: v`<local-version>` → v`<upstream-version>`
   > (repo tag: `<user-repo-tag>` → `<latest-tag>`)
3. Show a summary of the differences between local and upstream.
4. Proceed to Phase 2.

### 1.6 Compare versions (helper)

Use the helper script to compare repo-level semver tags:
```bash
bash <skill-updater-path>/scripts/check-versions.sh <user-repo-tag> <latest-repo-tag>
```

Per-skill versions (`metadata.version`) are compared by reading the upstream
skill's SKILL.md frontmatter at the latest tag (done in step 1.5). The helper
script is only for repo-tag comparison.

If the `--check` flag was used, repeat 1.3–1.5 for every skill found and display
a summary table (see "Checking all skills" section below), then stop.

### 1.7 Confirm with user

Before modifying anything, present a summary and ask for confirmation:

> **Update available for `<skill-name>`: v`<old>` → v`<new>`**
>
> Files that will change:
>   - `SKILL.md` — upstream modified (you also edited this → will merge)
>   - `scripts/deploy.sh` — upstream modified (you didn't edit → clean update)
>   - `references/new-guide.md` — new file from upstream (will add)
>
> Your customizations will be preserved. A backup will be created first.
> Proceed? (y/n)

If the user says no, stop and report that the update was skipped. If they say
yes, proceed to Phase 2. This step is important because updating modifies the
user's files — always get explicit consent.

---

## Phase 2: Backup

Never modify the user's skill without a backup. This is non-negotiable.

**Important:** The backup must capture the user's actual working-tree state,
including uncommitted changes. A `git branch` only captures committed state —
it will miss uncommitted user customizations. Always do a file-based backup
to be safe.

### Step 1: File-based backup (always do this)

Regardless of whether git is available, copy the skill folder:
```bash
cp -r path/to/<skill-name> path/to/<skill-name>.backup-<YYYYMMDD>
```
This captures the exact working-tree state, including uncommitted edits.
Verify the backup succeeded before proceeding. If it fails, stop.

### Step 2: Git snapshot (if git is available)

If the skill is in a git repo AND there are uncommitted changes:
```bash
# Commit the user's current state as a snapshot
git add path/to/<skill-name>/
git commit -m "skill-updater: pre-update snapshot of <skill-name>"

# Create the backup branch from this snapshot
git branch pre-update-<skill-name>-<YYYYMMDD>
```

If the working tree is clean (no uncommitted changes), just create the branch:
```bash
git branch pre-update-<skill-name>-<YYYYMMDD>
```

The file-based backup (Step 1) is the primary recovery mechanism. The git
branch is a convenience for `--revert` but is not sufficient on its own when
the user has uncommitted changes.

---

## Phase 3: Detect changes

**The goal: make the local file match the upstream version while preserving
user customizations.**

The primary comparison is **local file on disk vs upstream file from remote**.
This is always done. The base version (from the user's `repo_tag`) is optional
context that helps determine which differences are user customizations — but
even without a correct base, the local-vs-upstream comparison drives the merge.

### 3.1 Get the local version (from disk)

**Read the actual file on disk.** This is the user's current state — including
any uncommitted edits, reverts, or manual changes. Do NOT use `git show HEAD:...`
or any git command. Just read the file:

```
Read the file at: <skill-path>/SKILL.md
```

This is what the user actually sees and uses. This is the truth.

### 3.2 Get the upstream version (from remote)

This was already fetched in Phase 1.5. The upstream file at the latest tag is
the **target** — this is what the local file should look like after the update,
minus user customizations.

### 3.3 Compare local vs upstream (primary comparison)

**This is the most important step.** Read both files and identify every
difference between them. This tells you exactly what needs to change.

Do NOT skip this step based on `git diff` between tags. The `git diff` between
tags only shows what changed in the repo — the local file may be very different
from both tags.

### 3.4 Get the base version (optional, helps classify differences)

The base version helps answer: "Is this difference a user customization or
missing upstream content?" Fetch from the remote at the user's `repo_tag`:

```bash
git show <metadata.source.repo_tag>:<metadata.source.path>/SKILL.md
```

**Sanity check:** Verify the base version's `metadata.version` matches what
the user's `repo_tag` implies. If the base file at tag `v1.0.0` says
`metadata.version: "1.1.0"`, the tag is misconfigured — warn and proceed
without a base (fall back to two-way comparison with user input).

If the base is unavailable or unreliable, present the local-vs-upstream
differences to the user and ask which to keep and which to update.

### 3.5 Categorize each difference

Compare base→local (user's edits) and base→upstream (new changes).

For every file across all three versions:

| User edited? (base→local) | Upstream changed? (base→upstream) | Category |
|---|---|---|
| No | Yes | **CLEAN** — safe to overwrite with upstream |
| Yes | No | **USER-ONLY** — keep user's version as-is |
| No | No | **UNCHANGED** — no action needed |
| Yes | Yes | **CONFLICT** — needs intelligent merge |

Also check for:
- **New upstream files** — files in upstream that don't exist in base. Add them.
- **User-added files** — files the user created that aren't in base or upstream.
  Always keep them.
- **Deleted upstream files** — files in base but not in upstream. If the user
  also didn't modify them, remove. If user modified them, flag to user.

---

## Phase 4: Apply update

### Clean files (no conflict)

For files categorized as CLEAN, replace the local version with the upstream
version. For USER-ONLY files, leave them untouched. For new upstream files,
add them.

### Conflict files (both sides changed)

This is where you earn your keep. For each conflicted file, read both diffs
(base→upstream and base→local) and understand the *intent* behind each change.

**The three most common patterns:**

1. **Changes in different sections** — both sides edited the file, but in
   separate areas. Apply both changes. This is the most common case and is
   usually safe. Just verify they don't interact (e.g., one added a step that
   references something the other removed).

2. **Upstream bug fix + user's preference tweak in same area** — apply the
   bug fix AND preserve the user's customization. These almost always coexist.
   For example, upstream fixed a broken command while the user changed which
   tool to use — apply the fix with the user's tool choice.

3. **Genuine conflict — both sides changed the same thing differently** —
   pause and ask the user. Present both versions side by side and let them
   decide. Don't guess. Show something like:
   > Upstream changed this section to: `[upstream version]`
   > You changed it to: `[your version]`
   > Which do you want to keep, or should I merge them somehow?

Read `references/resolution-strategies.md` for additional patterns: script
conflicts, structural reorganizations, renamed files, and deleted-vs-modified
files.

**Guiding principles:**

- User customizations are sacred. When in doubt, preserve the user's version
  and add the upstream change alongside it.
- If upstream restructured a section the user heavily customized, ask the user.
  Don't silently reorganize their work.
- After merging, always update `metadata.version` (to the upstream skill's
  version), `metadata.source.repo_tag`, and `metadata.source.updated_at`.

---

## Phase 5: Verify and report

### 5.1 Validate skill structure

After applying changes, verify the skill is still well-formed:

- `SKILL.md` exists and has valid YAML frontmatter
- `metadata.version` is updated to the upstream skill's version
- `metadata.source.repo_tag` is updated to the new repo tag
- `metadata.source.updated_at` is set to today's date
- No syntax errors in frontmatter (parse it)
- Referenced files (scripts, references) still exist
- No duplicate or orphaned files

If validation fails, diagnose and fix. If unfixable, revert and tell the user.

### 5.2 Commit the result (git flow only)

Only if the skill lives inside a git repo:
```bash
git add path/to/<skill-name>/
git commit -m "skill-updater: update <skill-name> v<old-version> → v<new-version>

Repo tag: <user-repo-tag> → <latest-tag>
Upstream changes applied. User customizations preserved.
Backup branch: pre-update-<skill-name>-<YYYYMMDD>"
```

Use the per-skill `metadata.version` for `<old-version>` and `<new-version>`,
not the repo tags. The repo tag goes on its own line for context.

### 5.3 Restore stashed changes (git flow only)

If you stashed changes in Phase 2:
```bash
git stash pop
```

If the pop causes conflicts, tell the user and help resolve them.

### 5.4 Report to user

Present a clear summary showing the per-skill version bump prominently, with
the repo tag as context:

```
Updated <skill-name>: v<old-version> → v<new-version>
(repo: <user-repo-tag> → <latest-tag>)

Changes applied:
  - <upstream change 1>
  - <upstream change 2>

Your customizations preserved:
  - <user edit 1>
  - <user edit 2>

Backup: <backup-branch or backup-folder-path>

If anything looks wrong, run:
  /skill-updater --revert <skill-name>
```

Use `metadata.version` values for the version line. The repo tag line is
secondary context — most users only care about the per-skill version.

---

## Revert flow

When the user runs `/skill-updater --revert <skill-name>`:

### Step 1: Find the backup

Check for backups in this order (file-based is preferred because it always
captures the full working-tree state):

1. **File-based backup** — look for `<skill-name>.backup-*` sibling directory:
   ```bash
   ls -d path/to/<skill-name>.backup-* 2>/dev/null | sort -r | head -1
   ```

2. **Git backup branch** — if no file backup found:
   ```bash
   git branch --list "pre-update-<skill-name>-*" --sort=-creatordate | head -1
   ```

### Step 2: Restore

**From file backup (preferred):**
```bash
rm -rf path/to/<skill-name>
cp -r path/to/<skill-name>.backup-<YYYYMMDD> path/to/<skill-name>
```

**From git branch (fallback):**
```bash
git checkout <backup-branch> -- path/to/<skill-name>/
```

### Step 3: Commit (git flow only)

```bash
git add path/to/<skill-name>/
git commit -m "skill-updater: revert <skill-name> to pre-update version

Restored from backup."
```

### Report

```
Reverted <skill-name> to your pre-update version
(v<old-version> + your customizations).
Upstream update discarded.
```

---

## Checking all skills

When the user runs `/skill-updater --check`:

1. Scan all known skill locations (user-scope + project-scope, all AI tools).
2. **Read each SKILL.md file on disk** to get `metadata.version` and
   `metadata.source.repo_tag`. The file is the truth — not git history.
3. For skills with `metadata.source`, fetch the latest upstream tag **from the
   remote**. Group skills from the same repo to avoid redundant API calls — one
   tag lookup per repo, not per skill.
4. If any fetches fail (auth, network), mark those skills as
   `Check failed: <reason>` and continue checking the rest. Don't let one
   failure block the entire check.
5. Display a table:

```
Skill            Location                     Version        Repo Tag          Status
code-review      ~/.claude/skills/            1.0.0 → 1.2.0  v2.3.0 → v2.5.0  Update available
deploy           ./.claude/skills/            2.0.1          v2.5.0            Up to date
data-pipeline    ~/.opencode/skills/          1.0.0 → 1.1.0  v2.3.0 → v2.5.0  Update available
my-helper        ~/.claude/skills/            0.5.0          —                 Local (no upstream)
shared-skill     ~/.claude/skills/            —              —                 Unknown source
gitlab-skill     ./.claude/skills/            1.0.0          —                 Non-GitHub source (check manually)
```

The "Version" column shows `metadata.version` (per-skill). The "Repo Tag"
column shows `metadata.source.repo_tag` (repo-wide). Skills that are up to
date show only the current value. Skills with updates show `old → new`.

**Status values by origin:**

| Origin | Status |
|---|---|
| A/B with upstream tag available | `Update available` or `Up to date` |
| D (local — user-authored / AI-generated) | `Local (no upstream)` |
| C (no metadata, unknown source) | `Unknown source` — suggest stamping |
| F (non-GitHub source) | `Non-GitHub source` — can't check automatically, suggest manual check or local path |
| E (forked, diverged) | Same as A/B, but note if heavy divergence expected |
| Any with fetch failure | `Check failed: <reason>` — e.g., "auth required", "network error" |

---

## Error handling

Every error must produce a **clear message** and a **next step**. Never
dead-end.

Categories: tool availability, authentication, network, source metadata,
skill structure, safety. The two non-negotiable rules:

- **Backup fails → stop immediately.** Never proceed without a backup.
- **Merge too complex → pause and ask.** Never force a risky merge.

Read `references/error-handling.md` for the full error → action lookup tables
covering all known edge cases.

---

## Self-evolution

This skill is designed to improve itself over time. Corporate environments,
locked-down machines, and unusual setups will produce failures not yet covered
in the reference files. When that happens:

1. **Resolve the immediate problem** — help the user get unstuck using
   whatever workaround works.
2. **Record the lesson** — append the failure, root cause, and resolution to
   `references/field-notes.md` with today's date.
3. **Suggest a skill update** — tell the user: "I ran into something new
   that this skill didn't cover. I've logged it in field-notes.md. Want me
   to update the error handling or fetch strategies to handle this
   automatically next time?"
4. **If the user agrees, update the reference files** — promote the field
   note into the appropriate reference file (`error-handling.md`,
   `fetch-strategies.md`, `environment-detection.md`, etc.) so future runs
   handle it without human intervention.

The goal is that every failure makes the skill smarter. After a few real-world
runs in a restrictive environment, the skill should handle that environment
flawlessly.

Read `references/field-notes.md` for the running log of real-world failures
and resolutions.
