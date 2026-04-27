# youtube-lecture-notes

A Claude Code skill that turns a YouTube lecture or talk URL into a rich learning artifact built for active recall and spaced review — far beyond a summary.

For each lecture you give it, it produces:

- A **markdown study artifact** with 16 sections: TL;DR · reading plan · timestamped section map · concept index · glossary · transferable mental models · key claims with reasoning · worked examples · flashcards · self-quiz with hidden hints · Bloom-level 3–5 exercise track · open / hand-wavy parts the lecturer glossed · references · quotable bits · walk-away.
- An **Anki-importable flashcards CSV** (tab-separated, UTF-8 with BOM).

Output goes into a self-organizing `yt-lectures/<slug>/` subfolder of your current working directory:

```
yt-lectures/
  stanford-gpu-systems/
    notes.md
    flashcards.csv
  feynman-magnets/
    notes.md
    flashcards.csv
```

Two files per lecture, no clutter at the working-directory root.

---

## Install (3 steps, ~2 minutes)

```bash
# 1. Extract the bundle into your skills directory
mkdir -p ~/.claude/skills
unzip youtube-lecture-notes.skill -d ~/.claude/skills/

# 2. Run the one-shot setup checker (either form works)
~/.claude/skills/youtube-lecture-notes/setup.sh
# or, equivalently:
# python3 ~/.claude/skills/youtube-lecture-notes/scripts/setup_check.py

# 3. Restart Claude Code (or open a new session)
```

`setup_check.py` does everything you'd otherwise have to do by hand:

- Verifies you have Python 3.8+
- Installs `youtube-transcript-api` and `certifi` — preferring `uv` if you have it, falling back to `python -m venv`, falling back to `pip install --user`
- Tests SSL connectivity to youtube.com and auto-suggests the right `SSL_CERT_FILE` if your system CAs aren't picked up
- Prints `All checks passed.` when ready, or specific FAIL lines with the exact command to fix each problem

If you don't have `unzip`: `python3 -m zipfile -e youtube-lecture-notes.skill ~/.claude/skills/` works too — the `.skill` file is just a zip with a custom extension.

## Use it

Paste a YouTube URL with learning intent into Claude Code:

> "Help me actually learn from this lecture: https://www.youtube.com/watch?v=izZba4UA7iY"

Other phrasings that trigger the skill:

- "make me anki flashcards from <url>"
- "lecture notes from <url>"
- "deep-dive this video: <url>"
- "I want to study from <url>"

Claude will fetch the transcript, read it, produce both files, and self-lint the artifact before delivering. You'll get a short reply in chat with a suggested reading plan.

## What if a video has no captions?

The skill tells you explicitly and offers two fallbacks:

1. [Supadata](https://supadata.ai) — paid hosted API with AI-generated transcript fallback.
2. `yt-dlp -x` + a local Whisper / faster-whisper transcription.

It won't silently produce empty notes from a missing transcript.

## Bundled scripts

| Script | Purpose |
|---|---|
| `scripts/setup_check.py` | One-shot install verifier. Run after extracting. |
| `scripts/fetch_transcript.py` | Pulls captions; handles SSL, rate-limits, and disabled-captions errors with clear messages. |
| `scripts/format_transcript.py` | Re-renders a fetched `transcript.json` to text at a custom timestamp granularity. |
| `scripts/lint_artifact.py` | 23-check linter the skill itself runs before delivery. You can also run it manually on any artifact. |

## Troubleshooting

`setup_check.py` is the first stop — it auto-diagnoses most issues. For the long-form decision tree (rate-limit handling, missing captions, region locks, garbage auto-captions), see [`references/fetch_troubleshooting.md`](references/fetch_troubleshooting.md).

If the artifact ever feels off, lint it manually:

```bash
python3 ~/.claude/skills/youtube-lecture-notes/scripts/lint_artifact.py \
    your-notes.md --csv your-flashcards.csv --duration-seconds <video_secs>
```

It prints concrete `FAIL` / `ok` lines for every quality check the skill cares about.

## How the artifact is structured (and why)

Read [`references/artifact_structure.md`](references/artifact_structure.md) for the full template, per-section rationale, good-vs-bad flashcard examples, and a worked example. The flashcard count is scaled to video length:

| Video length | Flashcards | Self-quiz | Exercises |
|---|---|---|---|
| ≤ 10 min | 8–12 | 4–5 | 3–4 |
| 10–30 min | 12–20 | 5–7 | 4–6 |
| 30–60 min | 18–28 | 6–9 | 5–7 |
| 60–120 min | 25–35 | 8–12 | 6–9 |
| > 120 min | 30–40 | 10–14 | 7–10 |

Roughly one flashcard per two minutes of lecture, capped at 40. Going over usually produces paraphrased duplicates and trivia.

## Layout

```
youtube-lecture-notes/
├── README.md                          ← this file
├── SKILL.md                           ← the instructions Claude reads when triggered
├── scripts/
│   ├── setup_check.py                 ← install verifier (run once)
│   ├── fetch_transcript.py            ← transcript fetcher
│   ├── format_transcript.py           ← rerender JSON to text
│   └── lint_artifact.py               ← quality linter
├── references/
│   ├── artifact_structure.md          ← full output template + rationale
│   └── fetch_troubleshooting.md       ← network / SSL / missing-captions decision tree
└── evals/
    └── evals.json                     ← test prompts (used during skill development)
```
