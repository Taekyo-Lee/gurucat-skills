# Environment Detection

Build a capability profile of what's available on the user's machine. The
fetch chain (Phase 1.4) uses this profile to pick the right strategy.

## Checks

### 1. git

```bash
git --version
```
- If not found → set `has_git = false`. Use file-based flow for everything.
- If found → check if the skill is inside a repo:
  ```bash
  git rev-parse --is-inside-work-tree   # run from skill's directory
  ```
- If inside a repo → check for a remote:
  ```bash
  git remote -v
  ```
  Does the remote point to the same repo as `metadata.source.url`? If yes,
  Strategy 1 (git tags) is available. If the remote points elsewhere or is
  missing, skip Strategy 1.

### 2. `gh` CLI

```bash
gh --version
```
- **Not found** → set `has_gh = false`. This is fine — `gh` is not required.
  Skip Strategy 2 entirely.
- **Found** → check auth status for the correct host:
  ```bash
  gh auth status --hostname <source-host>
  ```
  Where `<source-host>` is derived from `metadata.source.url` (e.g.,
  `github.com` or `github.company.com`).

  Possible outcomes:
  - **Authenticated** → Strategy 2 is available. Record the auth method
    (`oauth_token`, `token`, etc.) for diagnostics.
  - **Not authenticated to this host** → `gh` is installed but can't reach
    this repo's host. Note this so the fetch chain can suggest `gh auth login`.
  - **Token expired or revoked** → `gh auth status` will show an error.
    Same handling as "not authenticated."
  - **Authenticated but wrong scopes** → rare, but `gh api` calls will fail
    with 403. Handled in the fetch chain fallthrough.

### 3. Environment tokens

Check for tokens even if `gh` is not installed — they can be used with raw
`curl` as a last-resort fallback:
```bash
echo $GITHUB_TOKEN
echo $GH_TOKEN
```
Record which (if any) are set. Do NOT print their values.

### 4. Network connectivity

Do a lightweight check:
```bash
gh api rate_limit 2>/dev/null   # if gh is available
# or
curl -sf --max-time 5 https://api.github.com/rate_limit >/dev/null 2>&1
```
- If neither works → set `has_network = false`. Only Strategies 4 (local path)
  and 5 (ask user) are viable. Skip all remote strategies immediately rather
  than failing through each one.

### 5. Source metadata

Does the skill have `metadata.source` in its frontmatter? If yes, we know
where upstream is regardless of git or `gh` state. If no, we'll need to ask
the user (see origin classification).

## Capability profile

Record these results for use in the fetch chain:

| Capability | Check | Impact |
|---|---|---|
| `has_git` | `git --version` | Enables Strategy 1 and git-based backup/diff |
| `in_repo` | `git rev-parse` | Enables git-based flows |
| `has_remote` | `git remote -v` | Enables Strategy 1 (git fetch) |
| `has_gh` | `gh --version` | Enables Strategy 2 |
| `gh_authed` | `gh auth status` | Strategy 2 can reach private repos |
| `has_token` | `$GITHUB_TOKEN` / `$GH_TOKEN` | Fallback auth for curl |
| `has_network` | API ping | If false, skip all remote strategies |
| `has_source` | frontmatter check | If false, ask user for origin |
