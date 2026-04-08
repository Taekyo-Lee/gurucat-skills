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

## How it works (happy path)

In the common case — a skill cloned from a GitHub repo with `metadata.source`
intact — the flow looks like this:

1. **Find the skill** and read its frontmatter. Classify its origin.
2. **Check environment** — git, `gh`, network available?
3. **Fetch the latest repo tag** and diff the skill's files between tags.
4. **Show the user what changed** and ask to confirm before proceeding.
5. **Back up** the current skill (git branch or file copy).
6. **Compare three versions** — base (last sync), local (user's), upstream (new).
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

Parse the `SKILL.md` frontmatter to extract:

- **`metadata.version`** — the per-skill version the user currently has (e.g., `1.0.0`)
- **`metadata.source.repo_tag`** — the repo-wide release tag the skill was last synced from (e.g., `v2.3.0`)

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

### 1.5 Check if the skill actually changed

A new repo tag does NOT mean every skill changed. Compare the skill's files
between the user's `repo_tag` and the latest tag:

**Git flow:**
```bash
git diff <user-repo-tag> <latest-tag> -- <metadata.source.path>/
```

**`gh` / API flow:**
Fetch the skill's files at both the user's `repo_tag` and the latest tag,
then compare content:
```bash
# Fetch file listing at each tag
gh api repos/<owner>/<repo>/contents/<path>?ref=<user-repo-tag> --jq '.[].name'
gh api repos/<owner>/<repo>/contents/<path>?ref=<latest-tag> --jq '.[].name'

# Compare individual files
gh api repos/<owner>/<repo>/contents/<path>/SKILL.md?ref=<tag> --jq '.content' | base64 -d
```

If the skill's files are **identical** between tags:
> `<skill-name>` is up to date (repo tag `<latest-tag>`, no changes to this skill).

Then stop. Update `metadata.source.repo_tag` to the latest tag (so future
checks skip these intermediate tags) but don't touch any skill content.

If the skill's files **did change** between tags:

1. **Read the upstream skill's `metadata.version`** from its SKILL.md at the
   latest tag. This is the per-skill version the user will be updating to.
2. Display the version context to the user:
   > Update available for `<skill-name>`: v`<local-version>` → v`<upstream-version>`
   > (repo tag: `<user-repo-tag>` → `<latest-tag>`)
3. Proceed to Phase 2.

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

### Git flow (git available and skill is in a repo)

1. If there are uncommitted changes in the working tree, stash them:
   ```bash
   git stash push -m "skill-updater: stash before updating <skill-name>"
   ```

2. Create a backup branch from the current state:
   ```bash
   git branch pre-update-<skill-name>-<YYYYMMDD>
   ```
   Example: `pre-update-code-review-20260408`

### File flow (no git, or skill outside a repo)

1. Copy the entire skill folder to a backup location next to the skill:
   ```bash
   cp -r path/to/<skill-name> path/to/<skill-name>.backup-<YYYYMMDD>
   ```

Confirm the backup succeeded before proceeding. If backup fails, stop and tell
the user.

---

## Phase 3: Detect changes

Determine what the user customized and what upstream changed.

The goal is to compare three versions:
- **Base**: the skill's content at the user's `metadata.source.repo_tag`
  (what they originally installed or last updated from)
- **Local**: what the user has now (base + their customizations)
- **Upstream**: the skill's content at the latest repo tag

### 3.1 Get the base version

**Git flow:**
If the user's repo_tag is available locally:
```bash
git show <metadata.source.repo_tag>:<metadata.source.path>/
```

**`gh` / API flow:**
Fetch the skill's files from upstream at the user's `repo_tag`:
```bash
gh api repos/<owner>/<repo>/contents/<path>?ref=<metadata.source.repo_tag> \
  --jq '.[].name'
```
Then fetch each file's content with `--jq '.content' | base64 -d`.

If even this fails (e.g., tag was deleted, no network), treat every file as
potentially edited by the user (worst case: full CONFLICT categorization,
agent merges everything carefully).

### 3.2 Categorize each file

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

### Git flow

1. Find the backup branch:
   ```bash
   git branch --list "pre-update-<skill-name>-*" --sort=-creatordate
   ```
   Use the most recent one.

2. Restore the skill folder from that branch:
   ```bash
   git checkout <backup-branch> -- path/to/<skill-name>/
   ```

3. Commit the revert:
   ```bash
   git commit -m "skill-updater: revert <skill-name> to pre-update version

   Restored from backup branch <backup-branch>."
   ```

### File flow

1. Find the backup folder (most recent `<skill-name>.backup-*` sibling directory).
2. Replace the skill folder with the backup copy.

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
2. Classify each skill's origin (see 1.1).
3. For skills with `metadata.source`, fetch the latest upstream tag. Group
   skills from the same repo to avoid redundant API calls — one tag lookup
   per repo, not per skill.
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
