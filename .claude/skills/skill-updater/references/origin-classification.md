# Origin Classification

How to determine where a skill came from and what update strategy to use.

## Origin types

| Origin | How to detect | Update strategy |
|---|---|---|
| **A. Git-cloned from source repo** | Inside a git repo whose remote matches `metadata.source.url` | Full git flow: fetch tags, diff, merge. Best case. |
| **B. Has metadata, no git connection** (downloaded, copied from coworker, etc.) | Has `metadata.source` but NOT in a git repo connected to it | `gh` CLI or raw URL to fetch upstream. File-based backup. |
| **C. No metadata (unknown source)** | No `metadata.source` at all — received from coworker, found online, etc. | Need to interview user to stamp origin (see stamping workflow below). |
| **D. Local (user-authored or AI-generated)** | No `metadata.source`. User wrote it or an AI generated it. | **Nothing to update.** No upstream exists. |
| **E. Forked and heavily modified** | Has `metadata.source`, but user has diverged significantly from upstream | Proceed normally, but expect more CONFLICT files. May need more user input during merge. |
| **F. Non-GitHub source** | `metadata.source.url` points to GitLab, Bitbucket, self-hosted, etc. | `gh` CLI won't work. Use git (if cloned), raw URL download, or local path. |

## Classification flow

1. **Check `metadata.source`** — does it exist in the frontmatter?
   - **Yes** → Origin A, B, E, or F (source is known). Proceed to step 2.
   - **No** → Origin C or D (source is unknown). Jump to the
     **stamping workflow** below.

2. **Check `metadata.source.url`** — is it a GitHub URL?
   - Matches `github.com` or `github.<company>.com` → GitHub-hosted.
   - Does NOT match → **Origin F** (non-GitHub). Note that `gh` won't work for
     this source. Git (if cloned), raw URL, or local path only.

3. **Check git state** — is the skill inside a git repo connected to the source?
   - Remote matches `metadata.source.url` → **Origin A**. Full git flow.
   - No matching remote (or not in a git repo) → **Origin B**. `gh` or
     download flow.

## Stamping workflow (no `metadata.source`)

When a skill has no source metadata, guide the user through an interactive
flow to determine what it is. Ask:

> "This skill doesn't have source metadata, so I don't know where it came
> from. Can you help me figure out its origin?"
>
> 1. **"I wrote it myself"** → Mark as user-authored. No upstream to update.
>    Do NOT stamp `metadata.source`. Report: "This is a local skill. If you
>    later publish it and want to track updates, re-run skill-updater to add
>    source metadata."
>
> 2. **"An AI generated it"** → Same as "I wrote it myself." No upstream.
>
> 3. **"I got it from a GitHub repo"** → Ask for the repo URL and path
>    within the repo. Stamp `metadata.source` with that info. Then proceed
>    with the update flow.
>
> 4. **"A coworker shared it with me"** → Ask: "Do you know which repo it
>    came from?" If yes, stamp and proceed. If no, ask: "Can you check with
>    them? Or do you have an updated copy I can compare against?"
>
> 5. **"I found it online"** → Ask for the URL. If it's a GitHub repo, stamp
>    and proceed. If it's a blog/tutorial, ask if the author has a repo.
>    If no repo exists, note: "No trackable upstream source. I can compare
>    against a local copy if you have one."
>
> 6. **"I don't remember"** → Offer: "I can try to search your git history
>    or the file's content for clues. Or if you have an updated version
>    somewhere, point me to it and I'll do a direct comparison."

After stamping, set `metadata.source.repo_tag` to the latest tag (or omit if
unknown) and `metadata.source.updated_at` to today. This makes future updates
automatic.
