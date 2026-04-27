#!/usr/bin/env python3
"""Re-render transcript.json to timestamped text at custom granularity.

Useful when the default 60s markers are too dense or too sparse for the lecture.

Usage:
    python format_transcript.py transcript.json --every 30 --out transcript-30s.txt
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def fmt_ts(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{sec:02d}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("json_path")
    ap.add_argument("--every", type=int, default=60, help="seconds between markers")
    ap.add_argument("--out", default="transcript.txt")
    args = ap.parse_args()

    data = json.loads(Path(args.json_path).read_text(encoding="utf-8"))
    snippets = data["snippets"]

    chunks: list[str] = []
    last = -args.every
    for s in snippets:
        if s["start"] - last >= args.every:
            chunks.append(f"\n[{fmt_ts(s['start'])}] ")
            last = s["start"]
        chunks.append(s["text"].replace("\n", " ").strip() + " ")
    Path(args.out).write_text("".join(chunks).lstrip(), encoding="utf-8")
    print(f"wrote {args.out} ({sum(len(c) for c in chunks)} chars, every {args.every}s)")


if __name__ == "__main__":
    main()
