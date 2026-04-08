# Resume: skill-updater skill development

## Context

We're building a `skill-updater` skill at `.claude/skills/skill-updater/`. Read `plan.md` and `SKILL.md` in that directory to get up to speed.

## What's been done

- `plan.md` — design doc with problem statement, design decisions, workflow diagram, scenarios, and repo structure. Updated with real-world scenarios and repo-level tagging. Versioning decision updated to reflect two-level model.
- `SKILL.md` — full skill instructions covering all 5 phases (pre-flight, backup, detect changes, apply update, verify & report), plus revert flow, check-all flow, and error handling. Supports git flow and file flow, multi-tool directories, 6-strategy fetch chain, and PAT handling.
- `SKILL.md` versioning model reconciled — uses both `metadata.version` (per-skill, set by author) and `metadata.source.repo_tag` (repo-wide, managed by skill-updater). Flow: compare repo_tag for new releases → diff skill files between tags → read upstream `metadata.version` for per-skill version bump.
- Fetch chain simplified from 6 strategies to 5 by integrating `gh` CLI. `gh` replaces the two separate curl-based GitHub API strategies (with/without PAT) — it handles auth transparently via credential store, `GH_TOKEN`, and device flow. Supports GitHub Enterprise. Chain: git → `gh` CLI → raw URL → local path → ask user.
- Comprehensive environment detection (Phase 1.2) — builds a full capability profile (`has_git`, `has_gh`, `gh_authed`, `has_token`, `has_network`, `has_source`) so the fetch chain can skip unavailable strategies immediately.
- Hardened fetch chain (Phase 1.4) — each strategy now has documented prerequisites, failure modes with symptoms, user-facing messages, and explicit fallthrough triggers. Covers: credential hangs, SSH failures, token expiry/revocation, SSO/SAML, wrong scopes, rate limits, corporate proxies, air-gapped environments, partial downloads, `gh` too old, and all-strategies-failed terminal state.
- Expanded error handling section — organized by category (tool availability, auth, network, source metadata, skill structure, safety) with specific error → action mappings for every known edge case.
- Origin classification system (Phase 1.1) — classifies skills into 9 origin types (A through I) covering: git-cloned, downloaded, coworker-shared with/without metadata, found online, user-authored, AI-generated, forked/diverged, and non-GitHub sources. Each type has a defined update strategy. Includes interactive stamping workflow for skills with unknown origins.
- Early-exit gates in fetch chain for origins with no upstream (user-authored, AI-generated, unknown source that user can't identify).
- `--check` table updated to show origin-aware status values (Local, Unknown source, Non-GitHub source, Check failed).
- plan.md expanded with Scenarios 9–12: user-authored skills, non-GitHub sources, unknown-source skills, and heavily-diverged forks.
- SKILL.md refactored from 847 → 586 lines (down from 847) by extracting detailed reference material into 4 new reference files, then refined with skill-creator review improvements.
- Skill-creator review applied: added happy-path overview at top, user confirmation step (Phase 1.7), simplified origins from 9 → 6 types, beefed up Phase 4 with inline merge guidance for top 3 patterns, improved description for aggressive triggering, added single-skill repo handling, tightened `--check` flow (batch API calls, partial failure resilience).
- `references/origin-classification.md` — 9 origin types (A–I), 3-step classification flow, interactive stamping workflow for unknown origins.
- `references/environment-detection.md` — full capability profile procedure, per-check commands, capability table.
- `references/fetch-strategies.md` — per-strategy prerequisites, commands, failure mode tables, and fallthrough triggers.
- `references/error-handling.md` — error → action lookup tables organized by category (tools, auth, network, metadata, structure, safety).
- `references/resolution-strategies.md` — conflict resolution guidance for common merge patterns.
- `scripts/check-versions.sh` — semver comparison helper script.

## What needs to happen next

### ~~1. Reconcile the two-level versioning model~~ DONE

Completed. SKILL.md now uses both `metadata.version` (per-skill) and
`metadata.source.repo_tag` (repo-wide). The update flow checks repo_tag first,
diffs specific skill files between tags, then reads upstream `metadata.version`
for the per-skill version bump display. Plan.md updated to match.

### 2. Real-world testing at Samsung (2026-04-09)

Minimal testing at home, then real-world testing at Samsung Electronics corporate
environment. Samsung has strict security policies — expect failures around:
- Corporate proxy blocking GitHub
- `gh` CLI not installable
- PAT restrictions
- SSO/SAML requirements
- VPN-only network access

**Testing plan:** Run the skill against real skills in the corporate environment.
Each failure gets logged to `references/field-notes.md`, resolved with the user,
and promoted into the main reference files. The skill self-evolves with each run.

### 3. Open design questions (lower priority — resolve during testing)

- Should skill-updater also update ITSELF? (meta-update problem)
- How should CHANGELOG.md be handled during merges? (append-only, so usually safe)
- Should we support `--all` to update every skill that has updates?

## Files to read

1. `.claude/skills/skill-updater/SKILL.md` — core skill instructions (586 lines, compact with pointers to references)
2. `.claude/skills/skill-updater/references/origin-classification.md` — origin types and stamping workflow
3. `.claude/skills/skill-updater/references/environment-detection.md` — capability profile procedure
4. `.claude/skills/skill-updater/references/fetch-strategies.md` — per-strategy details and failure modes
5. `.claude/skills/skill-updater/references/error-handling.md` — error → action lookup tables
6. `.claude/skills/skill-updater/references/resolution-strategies.md` — merge conflict resolution
7. `.claude/skills/skill-updater/scripts/check-versions.sh` — version comparison script
