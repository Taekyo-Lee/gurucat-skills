---
name: youtube-lecture-notes
description: Turn a YouTube lecture/talk URL into a rich learning artifact — far beyond a summary. Produces timestamped study notes, a concept index, glossary, mental models, key claims, flashcards (Anki-ready CSV), self-quiz, an exercise track, and a list of hand-wavy/open parts the lecturer glossed. Trigger this whenever the user shares a YouTube URL with learning intent or says things like 'study this lecture', 'make notes for this talk', 'lecture notes from', 'flashcards from this video', 'help me learn from this YouTube link', 'deep-dive this video', 'I want to actually understand this video'. Prefer this skill over generic summarization whenever the source is a YouTube video and the user wants to learn from it.
---

# YouTube Lecture Notes

Convert a YouTube lecture, talk, or tutorial into a structured learning artifact built for **active recall and spaced review**, not passive consumption. The artifact is one markdown document plus an Anki-importable flashcards CSV.

The job isn't to summarize the video. It's to leave the reader with: (a) a fast way to navigate back to any moment, (b) the lecturer's *transferable mental models*, (c) graduated active-recall material from recognition through application, and (d) an honest list of things the lecturer didn't quite explain. A summary fails at all four.

## When to use

- User shares a YouTube URL and wants to learn from it (not just skim it).
- User asks for "lecture notes", "flashcards", "study notes", or "deep dive" on a video.
- User wants to capture a talk for later reference / spaced repetition.

If the user only wants a 3-paragraph summary, this skill is overkill — a plain summary is fine. Use this skill when the user has signalled they want to *learn* the material, even if they ask for one piece of it (e.g. "just give me anki flashcards"). Producing the full artifact in addition is the right move — flashcards out of context are weaker than flashcards anchored to notes you can re-read.

## Workflow

### 0. First-time setup (run only if needed)

If this is the first time the skill is being used on this machine, the Python deps may not be installed. Check first:

```bash
test -d ~/.claude/skills/youtube-lecture-notes/.venv-yt-notes/lib && echo READY || echo NEEDS_SETUP
```

(The path may differ if the user installed the skill elsewhere — adjust to wherever this `SKILL.md` lives.)

If it prints `NEEDS_SETUP`, run the bundled setup checker before doing anything else:

```bash
bash ~/.claude/skills/youtube-lecture-notes/setup.sh
```

That script self-diagnoses Python version, installs `youtube-transcript-api` + `certifi` via the best available installer (uv → venv → pip --user), tests SSL connectivity, and prints `All checks passed.` when ready. If it prints any `FAIL` line, surface it to the user verbatim with the suggested fix — don't try to silently work around install failures, since the user's machine state determines what's actually fixable.

Once setup is confirmed (or the venv directory already exists), continue to step 1. **Don't re-run setup on subsequent invocations** — it's idempotent but wastes time.

### 1. Get the transcript

Use `scripts/fetch_transcript.py`. It handles SSL CAs on uv-managed Pythons, bootstraps `youtube-transcript-api`, and gives a clean error message on rate-limit / disabled-captions. It emits two **working files** the user shouldn't have to think about — write them into a hidden subdirectory so they don't clutter the working directory:

```bash
mkdir -p .yln
python scripts/fetch_transcript.py "<URL or 11-char video ID>" \
    --json .yln/transcript.json --text .yln/transcript.txt
```

These are intermediate. Step 7 cleans them up. The user is *only* meant to be left with `<slug>-notes.md` and `<slug>-flashcards.csv` in their working directory — nothing else.

If captions are disabled (`TranscriptsDisabled` / `NoTranscriptFound`), tell the user explicitly and offer fallbacks: Supadata (paid, AI fallback), or `yt-dlp -x` followed by Whisper. Don't proceed silently with an empty transcript.

### 2. Read the transcript into context

`transcript.txt` for an N-minute video runs roughly N×1k characters. The Read tool caps near 25k tokens (~80–90k chars), so for talks longer than ~75 min, read in slices via `offset`/`limit`. Minute-level timestamp markers in `transcript.txt` make slicing safe — never split mid-sentence on the JSON.

For very long videos (> 2 h), produce the artifact section-by-section: read 30 min, draft the corresponding section_map / concepts / quotes, then continue. Merge into the final artifact at the end.

### 3. Plan the size of the artifact

Match artifact density to lecture length. Use these defaults; deviate only if the lecture clearly needs it:

| Video length | Flashcards | Self-quiz | Exercises |
|---|---|---|---|
| ≤ 10 min | 8–12 | 4–5 | 3–4 |
| 10–30 min | 12–20 | 5–7 | 4–6 |
| 30–60 min | 18–28 | 6–9 | 5–7 |
| 60–120 min | 25–35 | 8–12 | 6–9 |
| > 120 min | 30–40 (cap at 40) | 10–14 | 7–10 |

Rule of thumb: roughly one flashcard per 2 minutes of lecture, one self-quiz question per 8–10 minutes, one exercise per 15–20 minutes. Going over feels comprehensive but produces low-value cards (paraphrased duplicates, trivia). Going under is fine if a lecture is genuinely thin.

### 4. Produce the artifact

Output goes into `yt-lectures/<slug>/` — one folder per lecture, two files inside:

```
yt-lectures/
  <slug>/
    notes.md
    flashcards.csv
```

The slug is kebab-case, derived from the video title; if the title isn't easily fetchable, use `lecture-<videoid>`. Inside the slug folder the filenames are unprefixed (`notes.md`, `flashcards.csv`) — the folder *is* the slug, so prefixing the files with it would be redundant.

Create `yt-lectures/` at the user's current working directory unless they specified a different target. If `yt-lectures/<slug>/` already exists from a previous run, overwrite — don't append a suffix.

The structure (read `references/artifact_structure.md` for the full template, anti-patterns, and a worked example) — 14 sections, in order:

1. **Header / metadata** — title, URL, duration, language, lecturer if known
2. **TL;DR** — *strictly 2–3 sentences*. The thesis the lecturer wants you to walk away with — not a table of contents. If you wrote more than 3 sentences, cut.
3. **How to use this artifact** — a 3–5 line "reading plan" telling the reader the order to consume sections in (e.g. *first pass: TL;DR + section_map + mental models; second pass: key_claims + worked_examples; ongoing: flashcards in Anki, self-quiz weekly*)
4. **Section map** — `[hh:mm:ss] → topic` table for navigation
5. **Concept index** — flat alphabetized list of named concepts with first-mention timestamps; a *jump table*, distinct from the glossary
6. **Glossary** — every introduced term + one-line definition + first timestamp; a *definition table*, distinct from the concept index
7. **Mental models** — the *transferable ways of thinking* the lecturer offers. For each: one paragraph, then **Why it matters:** and (only if the lecturer flagged a limit) **When it breaks:**. Don't force "when it breaks" — leave it out when honest.
8. **Key claims & arguments** — substantive assertions, each with the lecturer's *reasoning*, not just the claim. Cite timestamps. A bare claim isn't a claim.
9. **Worked examples** — concrete examples / numbers / case studies. Preserve the actual numbers; they make the abstractions stick.
10. **Flashcards** — count from the table above. Format: numbered markdown table (Front, Back) AND `<slug>-flashcards.csv` sidecar. See "Flashcard quality bar" below — this is the most-skipped quality check.
11. **Self-quiz** — open-ended questions, harder than flashcards. Hide *hints* (not full answers) in `<details><summary>Hint</summary>`. Forces the reader to attempt before peeking. Hints, not answers.
12. **Exercise track** — graded exercises that go *beyond* what was lectured. Bloom levels 3–5 (apply / analyze / create). Tag each with `[apply|analyze|create, easy|medium|hard]`. Aim for exercises that *can't* be done by re-reading — they require doing.
13. **Open / hand-wavy parts** — what the lecturer *touched on but glossed*. Strict rule: only flag things the speaker themselves brought up and then waved at, said "out of scope", or contradicted later. Don't list "things the speaker didn't cover" — that's an infinite list. *This section is mandatory and almost never empty.* If you wrote "nothing was hand-waved", you didn't read carefully enough.
14. **References mentioned** — *substantive* references only: papers, books, blog posts, datasets, software the lecturer cited. **Skip housekeeping** (Patreon, sponsors, "subscribe", venue thank-yous, "next video"). If nothing substantive was cited, write "None explicitly cited" — that's a fine entry.
15. **Quotable bits** — selectively kept memorable lines, verbatim with timestamps. Quote actually, don't paraphrase.
16. **Walk-away** — a single sentence the reader can carry around in their head. Not a summary; a sticky idea. If the TL;DR is the thesis, this is the bumper sticker.

(Sections 3 and 16 are the two added in v2 — they're cheap to write and dramatically improve usability.)

### 5. Flashcard quality bar

This is the most common failure mode of similar artifacts: producing 30 cards that all test recognition. Treat the count from the table as a *budget* you have to spend wisely.

**Good front-of-card patterns** (each requires *constructing* an answer, not retrieving a fact):

- "Why is X true given Y?" — forces causal reasoning
- "What would change if Z were different?" — counterfactual
- "How does X relate to Y?" — connective
- "When does mental-model M break, and why?" — limit-finding
- "Re-derive the formula for X starting from Y" — generative
- "What's wrong with the analogy 'A is like B'?" — critique

**Bad patterns to avoid** (cut these even at the cost of card count):

- "What is X?" with a one-word answer — pure recall
- "How many widgets are in the foo?" — trivia
- Cards that paraphrase each other (test once, not five times)
- "Pop-quiz" cards that re-ask earlier-card content
- Cards whose answers are ≤ 5 words (collapse them into the glossary instead)

Concrete example pair:
- *Bad*: "Front: How many SMs does an A100 have?" → "Back: 108." (Trivia; belongs in glossary at most.)
- *Good*: "Front: A 1792×1792 matmul fits in 98 tiles, but a 1793×1793 matmul takes 120 tiles. On an A100's 108 SMs, why does the throughput drop catastrophically — and what's this called?" → "Back: 98 tiles fit in one wave (108 SMs ≥ 98); 120 tiles require two waves, with the second using only 12 SMs and 96 sitting idle. Wave quantization."

### 6. Sanity-check before delivering

A short verification pass. Don't skip these — they're the difference between a skill that's slightly better than a baseline and one that earns trust.

**Run the bundled linter first:**

```bash
python scripts/lint_artifact.py yt-lectures/<slug>/notes.md \
    --csv yt-lectures/<slug>/flashcards.csv \
    --duration-seconds <video_duration_in_seconds>
```

The linter checks all 16 sections are present, TL;DR length, walk-away length, self-quiz uses `Hint` not `Answer` summaries, references is filler-free, flashcard count is in the band, and timestamps fall within the lecture duration. Exit 0 = clean, exit 1 = fix and re-lint. Don't deliver until the linter is clean.

**Then do these manual passes the linter can't automate:**

1. **Flashcard quality scan.** Re-read the flashcards. If more than ~20% are "trivia" or paraphrases of each other, cut and replace with construction-pattern cards (see "Flashcard quality bar" above for good/bad examples).
2. **Timestamp accuracy.** Linter only checks they're within the lecture's duration. Pick 3 timestamps and confirm they appear in `transcript.txt` near the content you cited. Hallucinated timestamps destroy trust.
3. **Internal-consistency check.** Scan the transcript for *contradictions* the lecturer might have made (e.g. "A100 has 128 SMs" at one point, "A100 has 108 SMs" later). If you find one, flag it in **Open / hand-wavy parts** with both timestamps. This is the single most-valuable thing the skill can catch that summarizers miss.
4. **Honest-empty check.** If "Open / hand-wavy parts" feels thin, re-read. Real lectures always have at least one glossed point.

If a check fails, fix it before delivering. Don't deliver a draft with known flaws and explain them — the reader trusts what they see.

## Output conventions

- One markdown file, GitHub-flavored. Tables for section_map, glossary, flashcards.
- `<details><summary>Hint</summary>` for self-quiz; `<details><summary>Sketch</summary>` is also fine for exercises if you want to give a hint.
- Cite timestamps as `[hh:mm:ss]` (or `[mm:ss]` for talks under an hour). Inline next to claims, definitions, and examples.
- Quote selectively but actually quote — preserve the lecturer's voice. Use `>` blockquotes or `"..."` with timestamps.
- Flashcards CSV: tab-separated, UTF-8 with BOM (Excel/Anki play nicely), header row `Front\tBack` (optionally `\tTags`).

### 7. Clean up working files

After the lint passes and you're about to deliver, remove the `.yln/` working directory:

```bash
rm -rf .yln
```

The user's working directory should now contain `yt-lectures/<slug>/notes.md` and `yt-lectures/<slug>/flashcards.csv`, and nothing else this skill produced. If you wrote any other intermediate files (an extracted slug helper, an exploratory grep result), delete those too.

If the user *explicitly* asked to keep the transcript ("save the transcript too", "I want the raw text"), move it into the slug folder as `yt-lectures/<slug>/transcript.txt` instead of deleting — clearly associated, easy to delete in one move.

## Reply to the user

After writing the files, send a short message in chat:

```
Wrote yt-lectures/<slug>/notes.md (X.Y KB) and yt-lectures/<slug>/flashcards.csv (N cards).
Suggested reading plan:
1. TL;DR + section map + mental models — 5–10 min
2. Key claims + worked examples — 20–30 min
3. Import flashcards.csv into Anki, attempt the self-quiz weekly for 4 weeks
```

Keep it that short — the artifact itself is the product.

## Bundled scripts

- `scripts/fetch_transcript.py` — robust transcript fetcher (handles SSL, rate-limit, disabled captions)
- `scripts/format_transcript.py` — re-render `transcript.json` to text at custom granularity
- `scripts/lint_artifact.py` — verify the artifact before delivery (run as the first step of the sanity-check pass)

## Deeper references

- `references/artifact_structure.md` — full template, anti-patterns, a worked example of every section, good/bad flashcards side-by-side
- `references/fetch_troubleshooting.md` — SSL / rate-limit / missing-captions decision tree
