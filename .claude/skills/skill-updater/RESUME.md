# Resume: skill-updater skill development

## Context

We're building a `skill-updater` skill at `.claude/skills/skill-updater/`. Read `plan.md` and `SKILL.md` in that directory to get up to speed.

## What's been done

- `plan.md` — design doc with problem statement, design decisions, workflow diagram, scenarios, and repo structure. Updated with real-world scenarios and repo-level tagging.
- `SKILL.md` — draft skill instructions covering all 5 phases (pre-flight, backup, detect changes, apply update, verify & report), plus revert flow, check-all flow, and error handling. Supports git flow and file flow, multi-tool directories, 6-strategy fetch chain, and PAT handling.
- `references/resolution-strategies.md` — conflict resolution guidance for common merge patterns.
- `scripts/check-versions.sh` — semver comparison helper script.

## What needs to happen next

### 1. Reconcile the two-level versioning model

The plan has **per-skill versions** in each SKILL.md frontmatter (`metadata.version: "1.2.0"`). We also added **repo-wide tags** (`v2.5.0`) as the stable release marker. The SKILL.md currently only uses `metadata.source.repo_tag` and dropped `metadata.version`. We need BOTH:

- `metadata.version` — per-skill version (e.g., `1.2.0`), set by skill authors
- `metadata.source.repo_tag` — repo-wide release tag the user last synced from (e.g., `v2.5.0`)

Update the SKILL.md to use both. The update flow should be:
1. Compare `repo_tag` against latest repo tag → "is there a new release?"
2. Diff the skill's files between tags → "did this skill actually change?"
3. If changed, show the user the per-skill version bump: `code-review: v1.0.0 → v1.2.0`

The `metadata.source` block in SKILL.md should look like:
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

### 2. After fixing versioning, consider test cases

The skill-creator workflow recommends writing 2-3 realistic test prompts and running them. Some scenarios to test:

- User has git + remote, skill has source metadata, upstream has new tag with changes to the skill
- User has no git, skill has source metadata pointing to a public GitHub repo
- User has a skill with no `metadata.source` (got it from a coworker via Slack)
- `/skill-updater --check` across multiple tools' skill directories
- `/skill-updater --revert` after an update

### 3. Open design questions

- Should skill-updater also update ITSELF? (meta-update problem)
- How should CHANGELOG.md be handled during merges? (append-only, so usually safe)
- Should we support `--all` to update every skill that has updates? (plan says per-skill only, but `--check` + `--all` could be a workflow)
- The `overrides.md` / layered override pattern from the plan — is this still relevant as a complementary approach?

## Files to read

1. `.claude/skills/skill-updater/plan.md` — full design doc
2. `.claude/skills/skill-updater/SKILL.md` — current skill draft (needs versioning fix)
3. `.claude/skills/skill-updater/references/resolution-strategies.md` — merge strategies
4. `.claude/skills/skill-updater/scripts/check-versions.sh` — version comparison script
