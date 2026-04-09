# Q&A

Common questions about skill-updater concepts, design decisions, and terminology.

---

## Versioning

### What's the difference between `version` and `repo_tag`?

`version` is a **per-skill** version number (e.g., `"1.1.0"`). It tells you
what version of *this specific skill* you have.

`repo_tag` is a **repo-wide** release tag (e.g., `"v1.1.0"`). It marks a
point-in-time snapshot of the *entire repository*, which may contain multiple
skills.

A single repo can hold many skills. When the repo owner creates a release, the
tag covers everything in the repo. Some skills may have changed in that release,
others may not.

### Why do we need `repo_tag` if we already have `version`?

`repo_tag` tells skill-updater **where to look in git history**. It's the
bookmark used to fetch and diff files. Without it, skill-updater wouldn't know
which point in the repo's history corresponds to the user's current skill state.

The update check is a two-step process:

1. Compare `repo_tag` against the latest tag on the remote — if they differ,
   *something* in the repo changed. This is a cheap check.
2. Diff the files under this skill's `path` between those two tags — if the
   skill's own files changed, an update is available. This is the accurate check.

### Can `version` and `repo_tag` have different values?

Yes, and they often will. Example with a repo containing two skills:

| Event | repo_tag | skill-A version | skill-B version |
|---|---|---|---|
| Initial release | `v1.0.0` | `1.0.0` | `1.0.0` |
| Only skill-A updated | `v1.1.0` | `1.1.0` | `1.0.0` |
| Only skill-B updated | `v1.2.0` | `1.1.0` | `1.1.0` |

At `v1.2.0`, skill-A's `version` is `1.1.0` (unchanged since `v1.1.0`), but
its `repo_tag` is `v1.2.0` (the latest release it was checked against).

### Which metadata fields are required and which are optional?

```yaml
metadata:
  version: "1.0.0"            # REQUIRED — the skill's own version
  author: "DevTools Team"     # optional — credit for the skill author
  source:                     # REQUIRED for updates (without this block,
                              #   skill-updater doesn't know where to look)
    repo: "owner/repo"        # REQUIRED — GitHub owner/repo identifier
    url: "https://github.com/..."  # REQUIRED — full URL to the repo
    path: ".claude/skills/x"  # REQUIRED — path to this skill within the repo
    repo_tag: "v1.0.0"        # REQUIRED — which repo tag this skill was
                              #   installed/updated from
    updated_at: "2026-04-08"  # optional — date of last update (informational)
```

Summary:

| Field | Required? | Why |
|---|---|---|
| `metadata.version` | Yes | Displayed to user, used in update reports |
| `metadata.author` | No | Informational only, not used by skill-updater |
| `metadata.source` (entire block) | Yes, for updates | Without it, skill-updater triggers the interactive stamping workflow to ask the user where the skill came from |
| `metadata.source.repo` | Yes | Used by `gh` CLI to fetch tags and files |
| `metadata.source.url` | Yes | Used to match git remotes and classify origin |
| `metadata.source.path` | Yes | Tells skill-updater which files in the repo belong to this skill |
| `metadata.source.repo_tag` | Yes | The baseline for three-way comparison — without it, skill-updater can't diff |
| `metadata.source.updated_at` | No | Informational; auto-set after each update |

If `metadata.source` is missing entirely, skill-updater won't crash — it will
ask the user about the skill's origin and offer to stamp it (see Test 4 in the
test plan).

---

## Testing

### What is a "happy path" test?

A standard software testing term meaning the **ideal scenario where everything
goes right** — no errors, no missing tools, no network failures, no unexpected
inputs. The user does exactly what's expected and every step succeeds.

The opposite is sometimes called the "sad path" or "rainy day" scenario, where
things go wrong and error handling is tested.

In the test plan:
- **Test 1 (Happy Path)** — metadata exists, remote is reachable, tags exist,
  git works, merge is straightforward.
- **Tests 3, 4** — edge cases where things are not ideal (revert flow, missing
  metadata).

### Why test `--check` before the happy path update?

`--check` is read-only — it scans and reports but changes nothing. Running it
first verifies the environment detection and tag-fetching logic without risk.
If `--check` fails, there's no point running the full update.

---

## Origins

### Why are there 6 origin types? Isn't that over-engineered?

Each origin type maps to a different **set of available tools and strategies**.
The classification determines what skill-updater can and cannot do:

| Origin | What's available | What's NOT available |
|---|---|---|
| A (git-cloned) | Full git flow, tags, diff | — |
| B (has metadata, no git) | `gh` CLI, raw download | git fetch, git diff |
| C (unknown source) | Nothing until user provides info | Everything |
| D (user-authored) | Nothing needed | No upstream exists |
| E (heavily forked) | Same as A/B, but expect conflicts | Clean merges |
| F (non-GitHub) | git (if cloned), raw URL | `gh` CLI |

Without classification, skill-updater would blindly try git commands on a
downloaded skill and fail with confusing errors.

### What does "stamping" mean?

Writing `metadata.source` into a skill's frontmatter for the first time. It's
like putting a return address on a package — once stamped, skill-updater knows
where to check for updates in the future.

---

## Backup and Safety

### Why file-based backup instead of just a git branch?

A git branch only captures **committed** state. If the user has uncommitted
customizations (which is common — users edit skills and don't always commit),
a git branch backup misses those changes entirely.

File-based backup (`cp -r`) captures the **working tree** — exactly what the
user sees on disk, committed or not. This was a bug found during testing
(Test 3) and fixed.

The current approach: file-based backup first (primary), git branch second
(supplementary).

### Why does skill-updater stop immediately if backup fails?

No backup means no undo. If the update goes wrong (bad merge, corrupt file,
unexpected error mid-write), there's no way to recover the user's previous
state. The risk of proceeding without a safety net outweighs the inconvenience
of stopping.

---

## Fetch Strategies

### Why 5 strategies instead of just using git?

Not every environment has git connected to the source, and not every user has
the same tools available. Corporate environments are especially constrained:

- No `gh` CLI (can't install without admin rights)
- Git SSH not configured (only HTTPS, or only internal mirrors)
- GitHub blocked by corporate proxy
- No personal access token (security policy)

The 5-strategy chain ensures skill-updater works in as many environments as
possible, gracefully degrading from the best method to simpler fallbacks.

### What's the difference between Strategy 2 (gh) and Strategy 3 (raw URL)?

`gh` uses GitHub's **API** with authentication. It works for private repos and
has higher rate limits.

Raw URL uses GitHub's **public content URLs** (`raw.githubusercontent.com`).
It only works for public repos (or with a token), and is more likely to be
blocked by corporate proxies.

---

## Three-Way Merge

### What is a "three-way" comparison?

It compares three versions of each file:

1. **Base** — the upstream content at the user's current `repo_tag` (what the
   user originally started with)
2. **Local** — the user's current file on disk (base + user's edits)
3. **Upstream** — the latest version from the remote (base + upstream's changes)

By comparing local and upstream independently against the base, skill-updater
can tell *who changed what*:

- Only upstream changed a section → safe to overwrite (CLEAN)
- Only the user changed a section → keep the user's version (USER-ONLY)
- Both changed the same section → needs intelligent merge (CONFLICT)
- Neither changed → skip (UNCHANGED)

### Why not just diff local vs upstream directly?

A two-way diff can't tell *who* made a change. If the user changed line 10 and
upstream didn't, a two-way diff sees a difference but doesn't know whether to
keep the user's version or take upstream's. The base version provides the
reference point to answer "who changed this?"
