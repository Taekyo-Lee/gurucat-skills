# Field Notes

Real-world failures encountered during skill-updater runs and how they were
resolved. This file grows over time — each new failure teaches the skill
something.

When you encounter a failure not covered in `error-handling.md` or
`fetch-strategies.md`, append it here with the date, environment, what
happened, and how it was resolved. Periodically promote recurring patterns
into the main reference files.

## Format

```
### YYYY-MM-DD — <short description>
**Environment:** <what was available — git, gh, network, proxy, etc.>
**What happened:** <the failure>
**Root cause:** <why it failed>
**Resolution:** <what worked>
**Update needed:** <which reference file should be updated, if any>
```

## Notes

### 2026-04-08 — Git branch backup doesn't capture uncommitted user customizations
**Environment:** git available, skill in repo, user customizations are uncommitted
**What happened:** Phase 2 created backup branch `pre-update-brand-guidelines-20260408` from HEAD. But the user's customizations (Samsung Blue color, `metadata.source` block) were uncommitted working-tree changes. The backup branch captured the last committed state (upstream v1.1.0), not the user's actual pre-update state. When `--revert` restored from this branch, it restored the wrong content.
**Root cause:** `git branch <name>` creates a branch from the current commit, not from the working tree. Uncommitted changes are invisible to it. The stash/pop cycle in Phase 2 was designed to preserve changes during the update, but the backup branch still points at the wrong commit.
**Resolution:** Phase 2 must capture the user's full working-tree state before any modifications. The fix: **commit the user's current state first** (a temporary "pre-update snapshot" commit), create the backup branch from that commit, then proceed with the update. Alternatively, always do a file-based backup (`cp -r`) alongside the git branch — file copy captures the working tree regardless of git state.
**Update needed:** SKILL.md Phase 2 backup logic must be rewritten.

### 2026-04-09 — Skill-updater must use files on disk as source of truth, not git history

**Environment:** Samsung corporate, git available, local repo has messy history (dummy commits, merge commits, previous skill-updater runs)

**What happened:** The AI used `git show v1.1.0:SKILL.md` to read upstream content, but the local v1.1.0 tag pointed to a stale commit — returning `version: "1.0.0"` when the remote's v1.1.0 actually has `version: "1.1.0"`. The entire three-way merge was based on wrong upstream data. In one run, `metadata.version` was not updated to "1.1.0". In another, the AI misread its own `git show` outputs and got lucky.

**Root cause:** The skill-updater treated local git objects (tags, commits) as the source of truth. But local tags can be stale, local history can be messy with dummy commits and merges, and `git show <tag>:...` reads from the local object store — not the remote. The SKILL.md file on disk is the only reliable source of truth for the local state.

**Key principle: The file on disk is the truth. Git is just a reference.**

- **Local state** → read the actual SKILL.md file on disk, not `git show HEAD:...`
- **Local version** → `metadata.version` inside SKILL.md, not git tags or commit messages
- **Local repo_tag** → `metadata.source.repo_tag` inside SKILL.md, not local git tags
- **Upstream content** → fetch from the REMOTE (via `gh api`, raw URL, or `git fetch` + `git show origin/tag:...`), not from local git objects (`git show v1.1.0:...`)

**Example scenario proving this:** User runs skill-updater (perfect merge, committed). Then user reverts all files but doesn't commit. `git log` says "update already done" — but the files on disk are back to v1.0.0. Skill-updater must see the file, read `version: "1.0.0"`, and offer the update again. If it trusted git history, it would incorrectly say "already up to date."

**Resolution:** Rewrite Phase 1 and Phase 3 instructions to enforce file-on-disk as primary source. For upstream content, always fetch from remote — never use `git show <local-tag>:...`.

**Update needed:** SKILL.md Phase 1 (local version reading), Phase 3 (base version retrieval), and the overall design principle section.
