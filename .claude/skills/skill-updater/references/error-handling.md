# Error Handling Reference

Every error must produce a **clear message** and a **next step**. Never
dead-end. If one approach fails, offer the next one. If all approaches fail,
give the user an actionable summary (see Strategy 5 in fetch-strategies.md).

## Tool availability

| Error | Action |
|---|---|
| **Git not installed** | Use file-based flow for everything. No git commands. Note in report: "git not available — used file-based backup and `gh`/download for fetch." |
| **`gh` not installed** | Skip Strategy 2 silently. `gh` is a convenience, not a requirement. |
| **`gh` install keeps failing** | Don't attempt to install `gh`. It's the user's system — suggest they install it later if they want, but proceed without it. Never block on tool installation. |
| **`gh` too old** | If a `gh` command fails with an unknown flag/subcommand, note the version and suggest `gh upgrade`. Fall through to next strategy. |
| **Neither git nor `gh` available** | Use raw URL download (Strategy 3) or local path (Strategy 4). Both work without any tools beyond `curl` or the agent's built-in capabilities. |

## Authentication

| Error | Action |
|---|---|
| **`gh` not authenticated** | Suggest `gh auth login`. For GitHub Enterprise: `gh auth login --hostname <host>`. User can do this and retry, or skip to local path. |
| **`gh auth login` fails — device flow blocked** | Corporate proxies or security policies may block the OAuth device flow. Suggest: "Try setting a token directly: `export GH_TOKEN=<your-pat>` then retry." |
| **`gh auth login` fails — browser won't open** | Headless/SSH environments. Suggest: `gh auth login --with-token < token.txt` or the `GH_TOKEN` env var approach. |
| **User cannot obtain a PAT at all** | They may not have a GitHub account, or corporate policy blocks PAT creation, or the repo was shared second-hand. Don't push. Accept it: "No problem. Let's try another way." Fall through to local path or ask user. |
| **Token expired or revoked** | `gh api` returns `401 Bad credentials`. Suggest `gh auth refresh` or `gh auth login` to re-authenticate. |
| **Wrong scopes** | `gh api` returns `403 Resource not accessible`. Suggest `gh auth refresh -s repo`. |
| **SSO/SAML authorization required** | `gh api` returns `403` with SSO message. The token exists but hasn't been authorized for the org. Tell user: "Authorize your token for the `<org>` org at: GitHub → Settings → Applications → Authorized OAuth Apps." |
| **`GITHUB_TOKEN` / `GH_TOKEN` set but invalid** | Environment token doesn't work. Note this and fall through. Don't unset the user's env vars. |

## Network

| Error | Action |
|---|---|
| **No network at all (air-gapped)** | Detected in environment check (1.2). Skip all remote strategies immediately. Go straight to Strategy 4 (local path). |
| **Corporate proxy blocks GitHub** | Symptom: connection reset, SSL errors, or redirect to a login page. Tell user their network may be blocking GitHub. Suggest: try from a different network, VPN, or provide a local copy. |
| **DNS resolution failure** | `Could not resolve host`. Same handling as no network. |
| **GitHub is down** | API returns 5xx or times out. "GitHub appears to be experiencing issues. Try again later, or provide a local copy." |
| **Rate limited** | `403 API rate limit exceeded`. "GitHub API rate limit hit (resets hourly). Wait and retry, authenticate for higher limits, or provide a local copy." |
| **Partial download / corrupt response** | Truncated content. Retry once. If still corrupt, fall through to next strategy. |
| **Slow connection / timeout** | Set reasonable timeouts (15s for git fetch, 10s for API calls). If exceeded, fall through rather than hanging. |

## Source metadata

| Error | Action |
|---|---|
| **No `metadata.source`** | Ask user where the skill came from. Stamp it for future updates. |
| **`metadata.source.repo` incorrect** | 404 from API. Ask user to verify the repo name. It may have been renamed, transferred, or deleted. |
| **`metadata.source.path` incorrect** | Repo exists but path not found. Ask user to verify. The skill may have been moved within the repo. |
| **`metadata.source.url` is not GitHub** | If the URL points to GitLab, Bitbucket, or another platform, `gh` won't work. Fall through to raw URL download or local path. |

## Skill structure

| Error | Action |
|---|---|
| **Corrupt SKILL.md frontmatter** | Attempt to parse and fix. If unfixable, show the raw frontmatter and ask the user to correct it. |
| **No tags on upstream repo** | "No stable releases found (no version tags). The skill developers haven't tagged a release yet." Do NOT offer to update from untagged commits. |
| **Upstream skill missing `metadata.version`** | Use the repo tag as the display version. Note in report: "Upstream skill doesn't declare a per-skill version." |

## Safety

| Error | Action |
|---|---|
| **Backup fails** | **Stop immediately.** Never proceed without a backup. Diagnose: disk full? Permission denied? Tell user. |
| **Merge too complex** | Don't force it. Pause, show both versions, ask for guidance. It's better to pause than to produce a broken merge. |
| **Disk full during update** | If writes fail mid-update, revert from backup immediately. Report partial failure. |
| **Permission denied on skill files** | Can't write to the skill directory. Tell user to check file permissions. |
