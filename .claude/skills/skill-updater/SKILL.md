---
name: skill-updater
description: >
  Updates locally-customized Agent Skills to the latest upstream version while
  preserving user customizations. Use this skill whenever the user wants to update
  a skill, sync a skill with upstream, pull the latest version of a skill, check
  if skills are outdated, or revert a skill update. Also use when the user mentions
  "skill-updater", "update skills", "sync skills", "pull latest skill", or asks
  about skill versions. Handles the fork maintenance problem — users freely
  customize skills, and this skill intelligently merges upstream updates without
  losing those customizations.
metadata:
  version: "0.1.0"
  author: "DevTools Team"
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

## Source Metadata

Every skill should carry its origin in the SKILL.md frontmatter so the updater
knows where to fetch from — even without git, remotes, or network context:

```yaml
metadata:
  source:
    repo: "company/skill-browser"
    url: "https://github.company.com/company/skill-browser"
    path: "skills/code-review"
    repo_tag: "v2.5.0"
    updated_at: "2026-04-01"
```

Key concept: **`repo_tag` is a repo-wide release tag, not a per-skill version.**
The skills repo contains many skills, and a single tag (e.g., `v2.5.0`) covers
the whole repo. A new repo tag doesn't mean every skill changed — the updater
diffs the specific skill's files between the user's `repo_tag` and the latest
tag to determine if that skill actually has updates.

If a skill has no `metadata.source`, ask the user where it came from and stamp
it for future updates.

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

### 1.2 Detect environment

Check what's available on this machine:

1. **Is git installed?** Run `git --version`. If not found, use file-based flow
   for everything.
2. **Is the skill inside a git repo?** Run `git rev-parse --is-inside-work-tree`
   from the skill's directory.
3. **Does the repo have a remote?** Run `git remote -v`. If yes, does it point
   to the same repo as `metadata.source.url`?
4. **Does the skill have `metadata.source`?** If yes, we know where upstream is
   regardless of git state.

This determines which fetch strategy to use (see 1.4).

### 1.3 Read local source tag

Parse the `SKILL.md` frontmatter to extract `metadata.source.repo_tag`. This is
the repo-wide release tag the skill was last synced from.

If there is no `repo_tag` field, treat the skill as unversioned — it needs a
full comparison against upstream (skip to Phase 3 with worst-case assumptions).

### 1.4 Fetch the latest stable repo tag

Skill developers commit frequently, but only stable releases get repo-wide
version tags (e.g., `v2.5.0`). The skill-updater only works with tagged
releases — never raw HEAD commits.

Try these strategies in order. Move to the next if one fails:

**Strategy 1 — git tags via remote:**
If git is available and the repo has a remote pointing to the source:
```bash
git fetch origin --tags
git tag --list "v*" --sort=-version:refname | head -1
```
This gives the latest semver tag on the repo.

**Strategy 2 — GitHub API with PAT:**
If `metadata.source.url` points to a GitHub instance:
```bash
curl -H "Authorization: token <PAT>" \
  "https://api.github.com/repos/<owner>/<repo>/tags"
```
Find the latest semver tag. Check environment variables `GITHUB_TOKEN` and
`GH_TOKEN` first before asking the user.

**Strategy 3 — GitHub API without auth:**
Same as Strategy 2 but without the Authorization header. Works for public repos.

**Strategy 4 — Raw URL download:**
If the source URL is accessible via HTTPS, try fetching the tags page or a
known file at a tag ref.

**Strategy 5 — Local path:**
Ask the user: "Do you have a copy of the updated skill? Point me to the folder."
Then read the upstream files from that local path.

**Strategy 6 — Ask the user:**
Last resort. "I can't reach the upstream source. Can you get the latest version
from whoever shared this skill with you?"

**When auth fails (401/403):**
Tell the user: "This repo requires authentication. Do you have a GitHub Personal
Access Token?" If they don't have one (e.g., got the skill from a coworker),
fall through to Strategy 5 or 6.

### 1.5 Check if the skill actually changed

A new repo tag does NOT mean every skill changed. Compare the skill's files
between the user's `repo_tag` and the latest tag:

**Git flow:**
```bash
git diff <user-repo-tag> <latest-tag> -- <metadata.source.path>/
```

**API flow:**
Fetch the skill's files at both the user's `repo_tag` and the latest tag,
then compare content.

If the skill's files are **identical** between tags:
> `<skill-name>` is up to date (repo tag `<latest-tag>`, no changes to this skill).

Then stop. Update `metadata.source.repo_tag` to the latest tag (so future
checks skip these intermediate tags) but don't touch any skill content.

If the skill's files **did change** between tags: proceed to Phase 2.

### 1.6 Compare versions (helper)

Use the helper script to compare semver tags:
```bash
bash <skill-updater-path>/scripts/check-versions.sh <user-repo-tag> <latest-repo-tag>
```

If the `--check` flag was used, repeat 1.3–1.5 for every skill found and display
a summary table (see "Checking all skills" section below), then stop.

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

**API flow:**
Fetch the skill's files from upstream at the user's `repo_tag`:
```bash
curl -fsSL ".../contents/<path>?ref=<metadata.source.repo_tag>"
```

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

This is where you earn your keep. For each conflicted file:

1. **Read the upstream diff** (base→upstream) — understand what changed and why.
   Look at commit messages, changelogs, or the diff itself. Is it a bug fix?
   New feature? Restructure?

2. **Read the user's diff** (base→local) — understand what they customized and
   why. Is it a preference tweak? Added workflow step? Different tool choice?
   Removed section?

3. **Decide on a merge strategy:**

   - **Both changes are in different sections** — apply both. Straightforward.
   - **Changes overlap but are compatible** — merge intelligently. For example,
     upstream added a step and user reworded a different step in the same section.
   - **Changes are genuinely conflicting** — pause and ask the user. Present both
     versions clearly and let them decide. Don't guess on risky merges.

4. **Apply the merge.** Write the merged content to the file.

Read `references/resolution-strategies.md` for guidance on common conflict
patterns and how to resolve them.

**Important principles for conflict resolution:**

- User customizations are sacred. When in doubt, preserve the user's version and
  add the upstream change alongside it.
- Bug fixes from upstream should almost always be applied, even if the user
  modified the same area. A bug fix + user's preference tweak can usually coexist.
- If upstream restructured a section the user heavily customized, ask the user.
  Don't silently reorganize their work.
- Always update `metadata.source.repo_tag` and `metadata.source.updated_at`
  after merging.

---

## Phase 5: Verify and report

### 5.1 Validate skill structure

After applying changes, verify the skill is still well-formed:

- `SKILL.md` exists and has valid YAML frontmatter
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
git commit -m "skill-updater: update <skill-name> to v<new-version>

Upstream changes applied. User customizations preserved.
Backup branch: pre-update-<skill-name>-<YYYYMMDD>"
```

### 5.3 Restore stashed changes (git flow only)

If you stashed changes in Phase 2:
```bash
git stash pop
```

If the pop causes conflicts, tell the user and help resolve them.

### 5.4 Report to user

Present a clear summary:

```
Updated <skill-name>: v<old> -> v<new>

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
2. For each skill with `metadata.source`, fetch the latest upstream tag.
3. Display a table:

```
Skill            Location                     Local    Latest Tag   Status
code-review      ~/.claude/skills/            1.0.0    v1.2.0       Update available
deploy           ./.claude/skills/            2.0.1    v2.0.1       Up to date
data-pipeline    ~/.opencode/skills/          1.0.0    v1.1.0       Update available
my-custom-skill  ~/.claude/skills/            0.0.0    —            No source metadata
```

For skills without `metadata.source`, note that no upstream is configured and
suggest the user provide the source.

---

## Error handling

- **Git not installed**: Use file-based flow for everything. No git commands.
- **No git remote**: Fall back to `metadata.source` URL + API/download strategies.
- **Auth failure (401/403)**: Ask for PAT. If unavailable, suggest local path or
  getting updated files from whoever shared the skill.
- **Network unreachable**: Try local path strategy. If unavailable, tell the user.
- **No `metadata.source`**: Ask user where the skill came from. Stamp it for
  future updates.
- **Corrupt SKILL.md frontmatter**: Attempt to fix. If unfixable, show the error
  and ask the user.
- **Backup fails**: Stop immediately. Never proceed without a backup.
- **No tags on upstream repo**: Tell user "No stable releases found (no version
  tags). The skill developers haven't tagged a release yet." Do not offer to
  update from untagged commits.
- **Merge too complex**: Don't force it. Pause, show both versions to the user,
  and ask for guidance. It's better to pause than to produce a broken merge.
