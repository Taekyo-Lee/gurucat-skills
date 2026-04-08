# Resolution Strategies

Guidance for resolving conflicts when both the user and upstream have modified
the same file. These patterns cover the most common scenarios.

## Table of Contents

1. [SKILL.md frontmatter conflicts](#skillmd-frontmatter-conflicts)
2. [Instruction text conflicts](#instruction-text-conflicts)
3. [Script conflicts](#script-conflicts)
4. [Added vs removed content](#added-vs-removed-content)
5. [Structural reorganizations](#structural-reorganizations)

---

## SKILL.md frontmatter conflicts

Frontmatter fields have clear ownership rules:

| Field | Resolution | Rationale |
|---|---|---|
| `name` | Keep upstream | Skill identity should stay consistent |
| `description` | Keep upstream | Triggering accuracy depends on canonical description |
| `metadata.version` | Always use upstream | Version must reflect the upstream release |
| `metadata.author` | Keep upstream | Credit belongs to the skill author |
| Custom user fields | Preserve user's | User-added fields are their own config |

If the user added custom frontmatter fields that don't exist upstream, keep them.
They won't conflict with anything.

---

## Instruction text conflicts

These are the most common and most nuanced conflicts. The key is understanding
*why* each side made their change.

### User reworded a step, upstream also changed it

Ask: did the user change the *meaning* or just the *wording*?

- **Wording only** (e.g., "Review the PR" → "Look over the pull request"):
  Apply upstream's change. The user's rewording was cosmetic and the upstream
  change likely has substance.

- **Meaning changed** (e.g., user added extra criteria, changed a threshold):
  Merge both. Apply upstream's structural change but preserve the user's
  semantic modifications. If they truly conflict, ask the user.

### User added steps, upstream added different steps

This is usually safe to merge. Insert both sets of additions in logical order.
If the user added step 3a and upstream added step 3b, include both.

### User removed a step, upstream modified that step

This is tricky. The user deliberately removed something, but upstream thinks it's
important enough to update.

- If upstream's change is a **bug fix**: tell the user the step had a bug, and
  suggest re-adding the fixed version. Let them decide.
- If upstream's change is a **feature enhancement**: respect the user's removal.
  They chose to remove it for a reason.

### User changed tool/command preferences

Common: user swaps `rg` for `grep`, `bat` for `cat`, etc. These are preference
customizations.

- Preserve the user's tool choices.
- If upstream changed the command's *arguments* or *logic*, apply the logic
  change but keep the user's tool.

---

## Script conflicts

Scripts in `scripts/` require more caution — a bad merge can break execution.

### User modified a script, upstream also changed it

1. Read both diffs carefully.
2. If changes are in different functions/sections, merge them.
3. If changes overlap, prefer upstream for bug fixes and user for customizations.
4. After merging, verify the script is syntactically valid (run a syntax check
   if possible: `bash -n` for shell, `python -m py_compile` for Python).

### Upstream added a new script that replaces one the user modified

Don't auto-replace. Tell the user:
> Upstream replaced `old-script.sh` with `new-script.sh`. You had customizations
> in the old script. Want to migrate your changes to the new one, or keep yours?

---

## Added vs removed content

### Upstream added a new file

Always add it. New files don't conflict with anything.

### Upstream removed a file the user didn't modify

Safe to remove.

### Upstream removed a file the user DID modify

Don't remove it. Tell the user:
> Upstream removed `<file>`, but you have customizations in it. Keeping your
> version. You may want to review whether it's still needed.

### User added a new file that doesn't exist upstream

Always keep it. User's additions are their own.

---

## Structural reorganizations

The hardest case. Upstream reorganized sections, renamed files, or restructured
the skill folder.

### Upstream renamed a file

If the user didn't modify the file: apply the rename.
If the user modified it: apply the rename AND preserve their changes in the
renamed file.

### Upstream restructured SKILL.md sections

If the user lightly customized (a few tweaks): apply upstream's structure and
re-apply the user's tweaks in the new locations.

If the user heavily customized (rewrote sections, added major content): **pause
and ask the user.** Show them the new structure and their customizations, and let
them decide how to reorganize.

### Upstream changed the skill's folder structure

Example: moved `scripts/` to `tools/`, added `references/` directory.

Apply the structural changes, then move the user's customized files into the
new structure. Verify all internal references (paths mentioned in SKILL.md) still
point to the right places.
