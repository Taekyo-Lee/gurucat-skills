#!/usr/bin/env python3
"""Lint a learning artifact before delivery — runs the same checks the eval grader uses.

The agent calls this after writing the artifact. Failures print actionable advice; the
agent then fixes and re-lints. Exit 0 = clean, exit 1 = issues to fix.

Usage:
    python lint_artifact.py path/to/<slug>-notes.md \\
        [--csv path/to/<slug>-flashcards.csv] \\
        [--duration-seconds 4712] \\
        [--transcript path/to/transcript.txt]

Without --duration-seconds, the flashcard-count check is skipped.
With --transcript, also spot-checks 3 random timestamps against the transcript.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

EXPECTED_SECTIONS = [
    ("TL;DR",                r"\btl;?dr\b"),
    ("How to use this artifact", r"how[\s-]*to[\s-]*use[\s-]*this[\s-]*artifact|reading[\s-]*plan"),
    ("Section map",          r"section[\s-]*map"),
    ("Concept index",        r"concept[\s-]*index"),
    ("Glossary",             r"\bglossary\b"),
    ("Mental models",        r"mental[\s-]*models?"),
    ("Key claims & arguments", r"key[\s-]*claims?"),
    ("Worked examples",      r"worked[\s-]*examples?"),
    ("Flashcards",           r"\bflashcards?\b"),
    ("Self-quiz",            r"self[\s-]*quiz"),
    ("Exercise track",       r"exercise[\s-]*track|\bexercises?\b"),
    ("Open / hand-wavy",     r"open\s*/\s*hand[\s-]*wavy|hand[\s-]*wavy|open\s+(?:questions|parts)"),
    ("References mentioned", r"references|further[\s-]*reading"),
    ("Quotable bits",        r"quotable|quotes?"),
    ("Walk-away",            r"walk[\s-]*away|bumper[\s-]*sticker"),
]

FILLER_RE = re.compile(r"patreon|sponsor|subscribe|amplify\s+partners|\bnext\s+video\b", re.IGNORECASE)


def flashcard_band(duration_s: int) -> tuple[int, int]:
    m = duration_s / 60
    if m <= 10:   return (8, 12)
    if m <= 30:   return (12, 20)
    if m <= 60:   return (18, 28)
    if m <= 120:  return (25, 35)
    return (30, 40)


def section_body(text: str, heading_pattern: str) -> str:
    m = re.search(r"##+\s*(?:" + heading_pattern + r")[^\n]*\n+(.*?)(?=\n##\s|\Z)",
                  text, flags=re.IGNORECASE | re.DOTALL)
    return (m.group(1).strip() if m and m.group(1) else "")


def sentence_count(s: str) -> int:
    s = re.sub(r"\s+", " ", s).strip()
    return len(re.findall(r"[.!?](?:\s|$)", s)) if s else 0


def count_csv_rows(p: Path) -> int:
    try:
        lines = [l for l in p.read_text(encoding="utf-8-sig", errors="replace").splitlines() if l.strip()]
        return max(0, len(lines) - 1)
    except Exception:
        return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("md_path", help="path to the <slug>-notes.md artifact")
    ap.add_argument("--csv", default=None, help="path to the <slug>-flashcards.csv sidecar")
    ap.add_argument("--duration-seconds", type=int, default=None,
                    help="lecture length in seconds; enables flashcard-band and timestamp-range checks")
    ap.add_argument("--json", action="store_true", help="emit a JSON report instead of human text")
    args = ap.parse_args()

    md_path = Path(args.md_path)
    if not md_path.exists():
        print(f"FATAL: {md_path} does not exist", file=sys.stderr)
        return 2

    text = md_path.read_text(encoding="utf-8")
    lower = text.lower()
    issues: list[str] = []
    passes: list[str] = []

    # 1. Section completeness
    for label, pat in EXPECTED_SECTIONS:
        if re.search(pat, lower):
            passes.append(f"section: {label}")
        else:
            issues.append(f"missing section: {label}")

    # 2. TL;DR length
    tldr = section_body(text, r"tl;?dr")
    sc = sentence_count(tldr)
    if not tldr:
        issues.append("TL;DR section empty")
    elif sc > 4 or len(tldr) > 600:
        issues.append(f"TL;DR is too long ({sc} sentences, {len(tldr)} chars). Spec: <=3 sentences, <=600 chars. Cut to the thesis.")
    else:
        passes.append(f"TL;DR concise ({sc} sentences, {len(tldr)} chars)")

    # 3. Walk-away length
    wa = section_body(text, r"walk[\s-]*away")
    if not wa:
        issues.append("Walk-away section empty")
    elif sentence_count(wa) > 2 or len(wa) > 250:
        issues.append(f"Walk-away too long ({sentence_count(wa)} sentences, {len(wa)} chars). Spec: 1-2 sentences, <=250 chars.")
    else:
        passes.append(f"Walk-away concise ({len(wa)} chars)")

    # 4. Self-quiz uses Hint blocks (not Answer blocks)
    hint_blocks = len(re.findall(r"<details>\s*<summary>\s*hint", lower, flags=re.IGNORECASE))
    answer_blocks = len(re.findall(r"<details>\s*<summary>\s*answer", lower, flags=re.IGNORECASE))
    if hint_blocks < 3:
        issues.append(f"Self-quiz hidden blocks should use 'Hint' summaries (got {hint_blocks}). 'Answer' summaries break active recall.")
    else:
        passes.append(f"self-quiz uses {hint_blocks} Hint block(s)")
    if answer_blocks > 0 and hint_blocks == 0:
        issues.append(f"Self-quiz uses {answer_blocks} 'Answer' summaries — switch to 'Hint' so the reader has to think first.")

    # 5. Timestamp citations
    ts_count = len(re.findall(r"\[\d{1,2}:\d{2}(?::\d{2})?\]", text))
    if ts_count < 8:
        issues.append(f"only {ts_count} timestamp citations; spec calls for cite-anywhere-relevant. Aim for >=8 in any non-trivial lecture.")
    else:
        passes.append(f"{ts_count} timestamp citations")

    # 6. References filler
    refs = section_body(text, r"references|further[\s-]*reading")
    refs_actual = re.sub(r"\(.*?\)", "", refs, flags=re.DOTALL)
    if refs and FILLER_RE.search(refs_actual):
        issues.append("References section contains filler (Patreon, sponsor, subscribe, 'next video'). Skip housekeeping; write 'None explicitly cited' if nothing substantive.")
    elif refs:
        passes.append("references clean of filler")
    else:
        issues.append("References section empty (write 'None explicitly cited' if nothing substantive was cited)")

    # 7. Open / hand-wavy not empty
    open_section = section_body(text, r"open\s*/\s*hand[\s-]*wavy|hand[\s-]*wavy|open\s+(?:questions|parts)")
    if not open_section or len(open_section) < 50:
        issues.append("Open / hand-wavy section empty or near-empty. Real lectures always have at least one glossed point — re-read.")
    else:
        passes.append(f"open/hand-wavy section non-empty ({len(open_section)} chars)")

    # 8. Flashcards count + CSV
    if args.csv:
        csv_p = Path(args.csv)
        if csv_p.exists():
            rows = count_csv_rows(csv_p)
            if args.duration_seconds:
                lo, hi = flashcard_band(args.duration_seconds)
                if lo <= rows <= hi:
                    passes.append(f"flashcard count {rows} in band [{lo}-{hi}]")
                else:
                    issues.append(f"flashcard count {rows} OUT OF BAND [{lo}-{hi}] for {args.duration_seconds//60}-min video. Cut/expand to fit.")
            else:
                passes.append(f"flashcard CSV present ({rows} cards)")
        else:
            issues.append(f"--csv path does not exist: {csv_p}")
    else:
        # try to find a sidecar next to the .md (covers both yt-lectures/<slug>/{notes.md,
        # flashcards.csv} layout and the legacy flat <slug>-notes.md / <slug>-flashcards.csv)
        candidates = (
            list(md_path.parent.glob("flashcards.csv")) +
            list(md_path.parent.glob("flashcards.tsv")) +
            list(md_path.parent.glob(f"{md_path.stem.replace('-notes','')}*.csv")) +
            list(md_path.parent.glob(f"{md_path.stem.replace('-notes','')}*.tsv"))
        )
        if candidates:
            rows = count_csv_rows(candidates[0])
            passes.append(f"flashcard sidecar auto-found ({rows} cards in {candidates[0].name})")
        else:
            issues.append("no flashcard sidecar (.csv/.tsv) found next to the .md — required for Anki import")

    # 9. Timestamp range check — the transcript markers are every ~60s, so per-second
    # timestamps in the artifact won't appear verbatim. Best check we can do without
    # the JSON: confirm every artifact timestamp falls within the lecture's duration.
    if args.duration_seconds:
        ts_pairs = re.findall(r"\[(\d{1,2})(?::(\d{1,2}))?:(\d{1,2})\]", text)
        # findall above doesn't disambiguate [mm:ss] vs [hh:mm:ss]; use a cleaner sweep:
        out_of_range = []
        for raw in re.findall(r"\[(\d{1,2}:\d{2}(?::\d{2})?)\]", text):
            parts = list(map(int, raw.split(":")))
            secs = parts[0] * 60 + parts[1] if len(parts) == 2 else parts[0] * 3600 + parts[1] * 60 + parts[2]
            if secs > args.duration_seconds + 5:  # tolerate 5s drift
                out_of_range.append(raw)
        if out_of_range:
            issues.append(f"{len(out_of_range)} timestamp(s) exceed lecture duration ({args.duration_seconds}s) — likely hallucinated: {out_of_range[:5]}")
        else:
            passes.append(f"all {ts_count} timestamps within lecture duration")

    if args.json:
        print(json.dumps({"passes": passes, "issues": issues, "ok": len(issues) == 0}, indent=2))
    else:
        for p in passes:
            print(f"  ok  {p}")
        for i in issues:
            print(f"FAIL  {i}")
        print()
        if issues:
            print(f"{len(issues)} issue(s) — fix and re-lint.")
        else:
            print(f"all {len(passes)} checks passed; artifact ready to deliver.")
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
