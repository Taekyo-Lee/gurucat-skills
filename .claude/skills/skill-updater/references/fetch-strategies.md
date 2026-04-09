# Fetch Strategies

Detailed per-strategy reference for Phase 1.4. Each strategy lists prerequisites,
commands, success criteria, and failure modes with fallthrough triggers.

The strategies are tried in order: 1 → 2 → 3 → 4 → 5. Move to the next when
one fails.

---

## Strategy 1 — git tags via remote

*Prerequisites:* `has_git`, `in_repo`, `has_remote` (pointing to source)

```bash
git fetch origin --tags --force
git tag --list "v*" --sort=-version:refname | head -1
```

**Important:** Always use `--force` with `--tags`. Without it, local tags that
already exist won't be updated even if the remote tag points to a different
commit. Stale local tags cause wrong content to be used in the three-way merge.

*Success:* Returns the latest semver tag (e.g., `v2.5.0`).

*Failure modes → fall to Strategy 2:*

| Failure | Symptom | What to tell the user |
|---|---|---|
| Credential prompt hang | `git fetch` blocks waiting for username/password | Kill the process after 15s timeout. Falling through to `gh`. |
| SSH key failure | `Permission denied (publickey)` | Note: git SSH not configured. Trying `gh` instead. |
| Remote unreachable | `Could not resolve host` / connection timeout | Network issue or host down. Trying `gh` (may use different auth path). |
| Remote points elsewhere | URL mismatch with `metadata.source.url` | Skip — this remote isn't the upstream source. |
| No semver tags | `git tag --list "v*"` returns empty | Upstream has no version tags yet. Report this and stop. |

---

## Strategy 2 — `gh` CLI

*Prerequisites:* `has_gh`, `metadata.source.repo` is set

```bash
# Preferred: list releases (intentional stable markers)
gh release list --repo <owner>/<repo> --limit 10

# Fallback: list tags if repo uses tags without releases
gh api repos/<owner>/<repo>/tags --jq '.[].name' | head -10
```

Pick the latest semver tag from the output.

To fetch a file at a specific tag:
```bash
gh api repos/<owner>/<repo>/contents/<path>?ref=<tag> --jq '.content' | base64 -d
```

*Success:* Returns tag list and can fetch file contents.

*Failure modes → fall to Strategy 3:*

| Failure | Symptom | What to tell the user |
|---|---|---|
| `gh` not installed | `has_gh = false` | Skip silently. `gh` is optional — the updater works without it. |
| Not authenticated | `gh auth status` shows no login for this host | "You need to authenticate `gh` to access this repo. Run: `gh auth login`" (or `gh auth login --hostname <host>` for GHE). User can do this now and retry, or skip to Strategy 4. |
| Token expired/revoked | `401 Bad credentials` from `gh api` | "Your GitHub token has expired. Run `gh auth refresh` (or `gh auth login` to re-authenticate)." Fall through if user can't fix now. |
| Wrong scopes / SSO required | `403 Resource not accessible` or `403 SSO authorization required` | "Your token doesn't have access to this repo. This can happen with SSO-protected orgs. Run `gh auth refresh -s repo` to request the right scopes, or authorize the token for your org in GitHub Settings → Applications." |
| Repo not found | `404 Not Found` | Check if `metadata.source.repo` is correct. May be renamed or deleted. Ask user to verify. |
| Rate limited | `403 API rate limit exceeded` | "GitHub API rate limit hit. Wait a few minutes and retry, or provide a local copy (Strategy 4)." |
| Network failure | Connection refused / timeout | Same as no network. Fall through. |
| `gh` too old | Missing subcommand or flag | `gh` version doesn't support the commands used. Suggest upgrade: `gh upgrade` or reinstall. Fall through. |
| `gh auth login` itself fails | Device flow blocked by corporate policy, browser can't open | "If device flow login isn't working, you can set a token directly: `export GH_TOKEN=<your-pat>` and retry. Or provide a local copy (Strategy 4)." |
| User cannot obtain a PAT at all | Corporate policy, no GitHub account, repo was shared second-hand | Don't push — accept this and fall through. "No worries, let's try another way." |

---

## Strategy 3 — Raw URL download

*Prerequisites:* `has_network`, `metadata.source.url` is set

Attempt to fetch files directly via HTTPS. This works for public repos and
some corporate setups with anonymous read access.

```bash
# GitHub raw content URL pattern
curl -fsSL "https://raw.githubusercontent.com/<owner>/<repo>/<tag>/<path>/SKILL.md"

# Or use the agent's web fetch tool if curl isn't available
```

If `has_token` is true (from environment check), add the Authorization header:
```bash
curl -fsSL -H "Authorization: token $GITHUB_TOKEN" \
  "https://raw.githubusercontent.com/<owner>/<repo>/<tag>/<path>/SKILL.md"
```

*Success:* Returns file content.

*Failure modes → fall to Strategy 4:*

| Failure | Symptom | What to tell the user |
|---|---|---|
| 404 Not Found | Repo is private, or path/tag is wrong | If private: "This repo requires authentication. See Strategy 2." If path wrong: verify `metadata.source.path`. |
| 401/403 | Auth required, token missing or invalid | "This repo requires authentication that I can't provide via URL. Provide a local copy." |
| Corporate proxy blocks raw.githubusercontent.com | Connection reset or SSL error | "Your network may be blocking direct GitHub access. Provide a local copy." |
| Partial download / corrupt content | Truncated response | Retry once. If still corrupt, fall through. |

---

## Strategy 4 — Local path

*Prerequisites:* none (always available)

Ask the user:
> "I couldn't reach the upstream source remotely. Do you have a copy of the
> updated skill files? Point me to the folder or file path."

Accept:
- A local directory containing the updated skill
- A downloaded zip/tar that the user extracted
- A path to a colleague's checkout of the skills repo

Read the upstream files from that local path. Verify it looks like a valid
skill (has SKILL.md with frontmatter).

*Failure modes → fall to Strategy 5:*

| Failure | Symptom | What to tell the user |
|---|---|---|
| User doesn't have a local copy | They say no | Fall through to Strategy 5. |
| Path doesn't exist | File not found | "That path doesn't exist. Double-check and try again, or I'll ask for another option." |
| Path has no SKILL.md | Missing expected files | "This doesn't look like a skill folder (no SKILL.md found). Check the path?" |
| Permission denied | Can't read the directory | "I don't have permission to read that path." |

---

## Strategy 5 — Ask the user (last resort)

*Prerequisites:* none

All automated methods have failed. Present a clear summary of what was tried
and offer actionable next steps:

> **I couldn't fetch the latest version of `<skill-name>`.**
>
> What I tried:
> - ~~git fetch~~ [reason it failed]
> - ~~gh CLI~~ [reason it failed]
> - ~~Direct download~~ [reason it failed]
> - ~~Local path~~ [user didn't have one]
>
> **Options:**
> 1. Get the updated skill files from whoever shared the skill with you
>    and point me to the folder.
> 2. If you can get network access or `gh` working later, run
>    `/skill-updater <skill-name>` again.
> 3. Skip this update for now.

Never dead-end. Always give the user a path forward, even if it's "try again
later."
