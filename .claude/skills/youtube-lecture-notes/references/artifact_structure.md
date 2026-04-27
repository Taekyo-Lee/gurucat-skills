# Artifact Structure — Full Template

This is the canonical structure for `<slug>-notes.md`. The skill's quality bar lives here as much as in `SKILL.md`.

## Filename and slug

- Slug: kebab-case, derived from the video title or — if title isn't easily fetchable — `lecture-<videoid>`. Keep it short.
- Output paths:
  - `<slug>-notes.md` (main artifact)
  - `<slug>-flashcards.csv` (sidecar, tab-separated, UTF-8 with BOM)
- Write into the user's current working directory unless they specify a target.

## Template

```markdown
# <Lecture title>

**Source:** `<youtube url>` · <duration> · <language> · auto/manual captions
**Lecturer / speaker:** <name if known, else "unknown">
**Slug:** <slug>

## TL;DR

<2–3 sentences. The thesis the lecturer wants you to walk away believing or
able to do. NOT a table of contents, NOT a paragraph about what the lecture
covers — what they want you to *take away*. If you wrote 4 sentences, cut.>

## How to use this artifact

1. **First pass** (5–10 min): TL;DR → section_map → mental_models. Get the shape.
2. **Second pass** (20–30 min for an hour-long lecture): key_claims → worked_examples → glossary. Get the substance.
3. **Active recall**: import `<slug>-flashcards.csv` into Anki and review daily. Do the self-quiz weekly for 4 weeks. Tackle one exercise from the track per week.

(Adjust the timings to lecture length. The point is to give the reader an
explicit ladder, not to leave them staring at a 200-line doc wondering where to start.)

## Section map

| Time | Topic |
|---|---|
| [00:00] | Intro & motivation |
| [hh:mm] | … |

## Concept index

A flat alphabetized list of substantive named concepts with first-mention
timestamps. **Distinct from the glossary**: this is a *jump table* — the
reader uses it to navigate. The glossary defines; the index locates.

- **Concept A** — [hh:mm:ss]
- **Concept B** — [hh:mm:ss]

## Glossary

Definitions, not just names. **Distinct from the concept index**: this is a
*definition table* — the reader uses it to recall meaning.

| Term | Definition (≤1 line) | First seen |
|---|---|---|
| Term A | one-line definition in the lecturer's framing | [hh:mm] |

## Mental models

The *transferable* ways of thinking the lecturer offers — frames that move
to other problems. Each one is a short paragraph.

- **<name of the model>** — explanation. *Why it matters:* one line.
  *When it breaks:* one line **iff the lecturer flagged a limit** — leave
  this out if forcing it (don't fabricate failure modes the lecturer didn't
  mention).

## Key claims & arguments

For each substantive assertion, capture the claim AND the lecturer's
reasoning. Bare claims aren't useful for review.

1. **Claim:** … *Reasoning:* … [hh:mm]

## Worked examples

Concrete examples / numbers / case studies. Preserve the actual numbers —
they're what makes abstractions stick.

- **<short title>** [hh:mm] — what the example was, what it showed.

## Flashcards

Count from the table in SKILL.md (≈ 1 card / 2 min, capped at 40).
Front-of-card: a question that requires *constructing* an answer, not just
retrieving a fact.

| # | Front | Back |
|---|---|---|
| 1 | <constructive question> | <answer with reasoning, ≥ one full sentence> |

> Sidecar: `<slug>-flashcards.csv` (tab-separated, UTF-8 with BOM, columns: Front, Back).
> Anki import: File → Import → set field separator to **Tab**, map columns 1→Front and 2→Back.

## Self-quiz

Open-ended questions, harder than flashcards. The reader should attempt
them before peeking. **Hide hints, not full answers** — collapse a *pointer*
in `<details>` so the reader can recover when stuck without simply reading
the answer.

1. <Question that requires synthesizing two or more sections.>

   <details><summary>Hint</summary>
   <a hint or pointer — not a full answer>
   </details>

## Exercise track

3–10 graded exercises (count from table). Each is something the reader has
to *do*, not just read. Aim for Bloom levels 3–5 (apply / analyze / create).
Tag each with `[apply|analyze|create, easy|medium|hard]`.

1. **[apply, easy]** Re-derive <X> from first principles.
2. **[analyze, medium]** Compare <X> to <Y>; under what regime does each win?
3. **[create, hard]** Implement a small program demonstrating the key mechanism.

## Open / hand-wavy parts

What the lecturer *touched on but glossed*. Strict criterion: the speaker
brought it up themselves and then waved at it / said "out of scope" /
contradicted later. Don't list "things adjacent to the topic the lecture
didn't cover" — that's an infinite list.

This section is mandatory and almost never empty. If you wrote "nothing was
hand-waved", you didn't read carefully enough.

- [hh:mm] *Topic.* What was waved at, why it's tricky, where to look next.

## References mentioned

**Substantive only**: papers, books, blog posts, datasets, software the
lecturer cited. Skip housekeeping: Patreon, sponsors, "subscribe", venue
thank-yous, "next video in this series." If nothing substantive was cited,
write "None explicitly cited." That's a real, fine entry.

- <title> — <author/source> [hh:mm]

## Quotable bits

Memorable framings, verbatim with timestamps. Keep selectively — these are
the lines worth remembering. Quote actually, don't paraphrase.

- "<quote>" [hh:mm]

## Walk-away

A single sentence the reader can carry around. Not a summary; a sticky idea.
If the TL;DR is the thesis, this is the bumper sticker.
```

## Per-section rationale (so you know what to cut)

| Section | Cut if… | Don't cut even if… |
|---|---|---|
| TL;DR | never | rambling lecture — extract the thesis anyway |
| How to use | never (cheap) | obvious — explicit ladder always helps |
| Section map | never (for talks > 20 min) | lecturer gave their own outline (re-derive) |
| Concept index | concepts < 5 | most are familiar — index is for *navigation* |
| Glossary | no new terms introduced | seems "standard" — readers may not know them |
| Mental models | no transferable frames offered (rare) | they feel obvious — they often aren't |
| Key claims | none made (essentially never) | lecturer "just describes" — separate description from claim |
| Worked examples | no examples given | the example was sloppy — keep it and note that |
| Flashcards | … never; lower the count to the band | tempted to fall back to trivia — push for *why* |
| Self-quiz | flashcards already cover everything (rare) | answers are uncertain — hints are still useful |
| Exercise track | the topic genuinely has no extension space | exercises feel low-quality — flag with (suggested) |
| Open / hand-wavy | the lecture truly glossed nothing | tempted to write "nothing" — re-read |
| References | nothing substantive cited (write "None explicitly cited") | lecturer "mentioned" Patreon (skip housekeeping) |
| Quotable bits | nothing memorable | one line was striking — keep it |
| Walk-away | never | the lecture is dry — find the bumper sticker anyway |

## Flashcard quality: side-by-side

For a Stanford GPU systems lecture:

| Bad (cut these) | Good (write these instead) |
|---|---|
| Q: How many SMs does an A100 have? A: 108. | Q: A 1792×1792 matmul fits in 98 tiles, but 1793×1793 takes 120 tiles. On an A100's 108 SMs, why does throughput drop catastrophically and what's it called? A: 98 tiles fit one wave; 120 require two, with the second using only 12 SMs and 96 idle. Wave quantization. |
| Q: What is L1 cache? A: A small fast memory on each SM. | Q: L1 and shared memory in CUDA are physically the same SRAM. What's the actual difference, and why does it matter when you're writing a fused softmax? A: L1 is hardware-managed (programmer can't control occupancy); shared memory is programmer-managed. The fused softmax kernel needs deterministic working-set placement, so you put the running max/denom in shared memory, not in cache. |
| Q: Define BF16. A: 16-bit float, 8 exp, 7 mantissa. | Q: Why does BF16 (8e/7m) dominate over FP16 (5e/10m) for ML training, despite FP16 having more precision? A: BF16's 8-bit exponent matches FP32's range, so gradient magnitudes don't underflow during training. The lost mantissa precision is acceptable; the lost dynamic range is not. |
| Q: What does FP8 do? A: Halves memory bytes. | Q: A pure-FP8 matmul on a tensor core would in principle double throughput vs FP16. Why is the actual end-to-end speedup closer to 1.3×? A: Quantization and dequantization aren't free, especially with per-block scale factors (MXFP8 stores both a matrix and its transpose to avoid re-quantizing on the fly). The matmul itself does double, but the overhead dilutes the gain. |

Pattern: bad cards retrieve a fact. Good cards force the reader to *connect* facts or reason through a chain.

## Worked example (excerpt of the artifact)

For a Stanford GPU/systems lecture covering hardware, six perf tricks, and flash attention:

- **TL;DR**: "Modern ML throughput is gated by memory bandwidth, not compute. The lecture builds the GPU mental model, teaches six perf tricks (control divergence, low precision, fusion, recomputation, coalescing, tiling) — all attacking memory — and synthesizes them into flash attention."
- **How to use this artifact**: First pass: TL;DR + section_map + mental_models (10 min). Second pass: key_claims + worked_examples + flashcards (~45 min). Spaced repetition: import flashcards into Anki, attempt self-quiz weekly for 4 weeks.
- **Mental model**: *Roofline plot.* Throughput = `min(peak_compute, arithmetic_intensity × bandwidth)`. Below ridge = memory-bound (slope); above = compute-bound (flat). All tricks try to live on the flat. *Why it matters:* tells you *which* optimization will help. *When it breaks:* the lecturer notes it's steady-state, so latency-bound regimes (e.g. inference decode) need a different model.
- **Self-quiz**: *"Why does padding nano-GPT's vocab from 50257 to 50304 give a 25% speedup despite adding work? Trace through which trick(s) explain it."* `<details>` *Hint: think about coalescing, tile boundaries, and burst windows. The new size is divisible by 64, so tile-row reads align with 128-byte burst sections of FP16 data.*
- **Exercise [analyze, medium]**: "Compute the operational intensity of a single FP32 ReLU on a vector of length N. Where does it sit on the roofline of an A100? What changes at FP8?"
- **Open / hand-wavy**: *[10:30] L1 vs shared memory distinction.* The lecturer says "the cache just operates on its own; you don't get to control it" — but doesn't explain how this affects programming a fused softmax. Worth chasing in the CUDA programming guide.
- **Walk-away**: "Compute is a faucet, memory is a hose: every perf trick is about not wasting water carried through the hose."

## Things to avoid

- **Hallucinated timestamps.** Cross-check 3 random ones against `transcript.txt`. If unsure, omit the timestamp rather than guess.
- **Padding the artifact** with generic boilerplate that wasn't in the lecture. Stay anchored.
- **Trivia flashcards.** "How many widgets in the foo?" is trivia. "Why is X true given Y?" is understanding. Default *why* over *what*.
- **Soft "open / hand-wavy"** that flags topics adjacent to the lecture. Only flag what the speaker themselves brought up and glossed.
- **Filler references.** Patreon, "subscribe", "next video" — skip. "None explicitly cited" is a fine, honest entry.
- **Mixing your interpretations with the lecturer's claims.** Mark commentary: *(my read:)* or *(extension:)*.
- **Going over the flashcard band.** More cards isn't more value. Cap at the band, push quality up.
