#!/usr/bin/env python3
"""Fetch a YouTube video transcript and emit JSON + timestamped text.

Handles three common gotchas:
  - youtube_transcript_api not installed  → bootstraps a venv via uv (or pip).
  - SSL CA bundle missing on uv-managed Python → tries system CAs then certifi.
  - Captions disabled / missing → exits with a clear message + fallback advice.

Usage:
    python fetch_transcript.py "<URL or 11-char video ID>" \\
        --json transcript.json --text transcript.txt [--lang en] [--every 60]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

VIDEO_ID_RE = re.compile(r"(?:v=|/shorts/|/embed/|youtu\.be/)([A-Za-z0-9_-]{11})")
SCRIPT_DIR = Path(__file__).resolve().parent
VENV_DIR = SCRIPT_DIR.parent / ".venv-yt-notes"


def extract_video_id(s: str) -> str:
    s = s.strip()
    if len(s) == 11 and re.fullmatch(r"[A-Za-z0-9_-]{11}", s):
        return s
    m = VIDEO_ID_RE.search(s)
    if not m:
        sys.exit(f"could not parse a video id from: {s!r}")
    return m.group(1)


def ensure_dependency() -> None:
    """Make sure youtube_transcript_api + certifi are importable. Re-exec under
    a venv if not — keeps the user's global Python clean."""
    try:
        import youtube_transcript_api  # noqa: F401
        import certifi  # noqa: F401
        return
    except ImportError:
        pass

    if not VENV_DIR.exists():
        print(f"bootstrapping venv at {VENV_DIR} ...", file=sys.stderr)
        installer = shutil.which("uv")
        if installer:
            subprocess.check_call(["uv", "venv", str(VENV_DIR), "-q"])
            subprocess.check_call([
                "uv", "pip", "install", "-q",
                "-p", str(VENV_DIR / "bin" / "python"),
                "youtube-transcript-api", "certifi",
            ])
        else:
            subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])
            subprocess.check_call([
                str(VENV_DIR / "bin" / "pip"), "install", "-q",
                "youtube-transcript-api", "certifi",
            ])

    venv_python = VENV_DIR / "bin" / "python"
    if Path(sys.executable).resolve() == venv_python.resolve():
        # already inside the venv but import failed — surface the real error
        import youtube_transcript_api  # noqa
        return

    os.execv(str(venv_python), [str(venv_python), __file__, *sys.argv[1:]])


def configure_ssl() -> None:
    """uv-managed CPython doesn't see system CAs by default. Try the system
    bundle first (works on Debian/Ubuntu/WSL), then fall back to certifi."""
    if os.environ.get("SSL_CERT_FILE") and os.environ.get("REQUESTS_CA_BUNDLE"):
        return
    candidates = [
        "/etc/ssl/certs/ca-certificates.crt",   # Debian/Ubuntu/WSL
        "/etc/pki/tls/certs/ca-bundle.crt",     # RHEL/Fedora
        "/etc/ssl/cert.pem",                    # macOS / Alpine
    ]
    for path in candidates:
        if Path(path).exists():
            os.environ.setdefault("SSL_CERT_FILE", path)
            os.environ.setdefault("REQUESTS_CA_BUNDLE", path)
            return
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())


def fmt_ts(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{sec:02d}"


def write_text(snippets: list[dict], out_path: Path, every: int) -> int:
    chunks: list[str] = []
    last_mark = -every
    for s in snippets:
        if s["start"] - last_mark >= every:
            chunks.append(f"\n[{fmt_ts(s['start'])}] ")
            last_mark = s["start"]
        chunks.append(s["text"].replace("\n", " ").strip() + " ")
    text = "".join(chunks).lstrip()
    out_path.write_text(text, encoding="utf-8")
    return len(text)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="YouTube URL or 11-char video ID")
    ap.add_argument("--json", default="transcript.json", help="raw JSON output path")
    ap.add_argument("--text", default="transcript.txt", help="readable timestamped text path")
    ap.add_argument("--lang", action="append", default=None,
                    help="preferred language code(s), repeatable. default tries en variants")
    ap.add_argument("--every", type=int, default=60,
                    help="seconds between timestamp markers in --text output")
    args = ap.parse_args()

    ensure_dependency()
    configure_ssl()

    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api import _errors as yte

    video_id = extract_video_id(args.source)
    languages = args.lang or ["en", "en-US", "en-GB", "a.en"]

    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=languages)
    except yte.TranscriptsDisabled:
        sys.exit(
            f"video {video_id}: captions are disabled by the uploader.\n"
            "fallbacks: (1) Supadata (AI-generated, paid), (2) yt-dlp -x then whisper."
        )
    except yte.NoTranscriptFound:
        sys.exit(
            f"video {video_id}: no transcript found in {languages}.\n"
            "try --lang for a different language, or fall back to whisper."
        )
    except yte.VideoUnavailable:
        sys.exit(f"video {video_id}: unavailable (private, deleted, region-locked, or wrong id).")
    except (getattr(yte, "RequestBlocked", Exception),
            getattr(yte, "IpBlocked", Exception)) as e:
        sys.exit(
            f"video {video_id}: youtube blocked the request ({type(e).__name__}).\n"
            "this is usually IP-based rate limiting. wait a few minutes and retry, "
            "or route through a proxy via youtube_transcript_api.proxies.GenericProxyConfig."
        )

    snippets = [
        {"start": float(s.start), "duration": float(s.duration), "text": s.text}
        for s in fetched
    ]

    Path(args.json).write_text(
        json.dumps({
            "video_id": video_id,
            "language": fetched.language_code,
            "snippets": snippets,
        }, ensure_ascii=False),
        encoding="utf-8",
    )
    chars = write_text(snippets, Path(args.text), args.every)
    duration = snippets[-1]["start"] + snippets[-1]["duration"] if snippets else 0.0

    print(
        f"video_id={video_id} language={fetched.language_code} "
        f"snippets={len(snippets)} chars={chars} duration={fmt_ts(duration)} "
        f"json={args.json} text={args.text}"
    )


if __name__ == "__main__":
    main()
