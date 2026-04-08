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
