#!/usr/bin/env python3
"""One-shot install checker / bootstrapper.

Run this once after extracting the skill. It tries to set up the Python deps
the skill needs, then tells you in plain language whether you're ready and —
if not — exactly what to do. Cross-platform, no Bash required.

Usage:
    python3 scripts/setup_check.py
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
VENV_DIR = SKILL_DIR / ".venv-yt-notes"
DEPS = ["youtube-transcript-api", "certifi"]


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def ok(msg: str) -> None:
    print(f"  ok  {msg}")


def warn(msg: str) -> None:
    print(f"  ?   {msg}")


def fail(msg: str) -> None:
    print(f"FAIL  {msg}")


def run(cmd: list[str], **kw) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, **kw)
        return r.returncode, (r.stdout + r.stderr)
    except FileNotFoundError as e:
        return 127, str(e)


def find_venv_python() -> Path | None:
    p = VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    return p if p.exists() else None


def can_import_in(python_exe: Path) -> bool:
    code, _ = run([str(python_exe), "-c", "import youtube_transcript_api, certifi"])
    return code == 0


def install_via_uv(uv_path: str) -> bool:
    print(f"  using uv at {uv_path}")
    if not VENV_DIR.exists():
        c, out = run([uv_path, "venv", str(VENV_DIR), "-q"])
        if c != 0:
            fail(f"uv venv failed: {out.strip()[:200]}")
            return False
    py = find_venv_python()
    if not py:
        fail("uv created venv but python binary missing — odd")
        return False
    c, out = run([uv_path, "pip", "install", "-q", "-p", str(py), *DEPS])
    if c != 0:
        fail(f"uv pip install failed: {out.strip()[:200]}")
        return False
    return can_import_in(py)


def install_via_system_venv() -> bool:
    print(f"  using system python at {sys.executable}")
    c, out = run([sys.executable, "-m", "venv", str(VENV_DIR)])
    if c != 0:
        fail(f"python -m venv failed: {out.strip()[:200]}")
        return False
    py = find_venv_python()
    if not py:
        fail("venv created but python binary missing — odd")
        return False
    c, out = run([str(py), "-m", "pip", "install", "-q", *DEPS])
    if c != 0:
        fail(f"pip install in venv failed: {out.strip()[:200]}")
        return False
    return can_import_in(py)


def install_user_site() -> bool:
    print("  falling back to: pip install --user (no venv)")
    c, out = run([sys.executable, "-m", "pip", "install", "--user", "-q", *DEPS])
    if c != 0:
        fail(f"pip install --user failed: {out.strip()[:200]}")
        return False
    c, _ = run([sys.executable, "-c", "import youtube_transcript_api, certifi"])
    return c == 0


def diagnose_python() -> None:
    section("Python")
    ok(f"python: {sys.executable} ({platform.python_version()})")
    if sys.version_info < (3, 8):
        fail("Python 3.8+ is required. Install a newer Python from python.org.")


def diagnose_install() -> Path | None:
    """Returns the python interpreter to use for the skill, or None on failure."""
    section("Skill dependencies")
    py = find_venv_python()
    if py and can_import_in(py):
        ok(f"venv already set up at {VENV_DIR}")
        return py

    uv = shutil.which("uv")
    if uv:
        if install_via_uv(uv):
            ok("installed via uv")
            return find_venv_python()

    # try built-in venv
    if install_via_system_venv():
        ok("installed via python -m venv")
        return find_venv_python()

    # last resort
    if install_user_site():
        ok("installed to user site-packages (no venv)")
        return Path(sys.executable)

    return None


def diagnose_ssl(py: Path) -> bool:
    section("SSL / network")
    code = (
        "import os, sys, ssl, socket;"
        "import urllib.request;"
        "ctx = ssl.create_default_context();"
        "u = urllib.request.urlopen('https://www.youtube.com/', context=ctx, timeout=10);"
        "print('status', u.status)"
    )
    c, out = run([str(py), "-c", code])
    if c == 0 and "status 200" in out:
        ok("can reach https://www.youtube.com (SSL OK)")
        return True
    if "CERTIFICATE_VERIFY_FAILED" in out:
        warn("SSL certificate verification failed — checking system CA bundles...")
        candidates = [
            "/etc/ssl/certs/ca-certificates.crt",
            "/etc/pki/tls/certs/ca-bundle.crt",
            "/etc/ssl/cert.pem",
        ]
        found = next((p for p in candidates if Path(p).exists()), None)
        if found:
            os.environ["SSL_CERT_FILE"] = found
            os.environ["REQUESTS_CA_BUNDLE"] = found
            c2, out2 = run([str(py), "-c", code], env={**os.environ})
            if c2 == 0 and "status 200" in out2:
                ok(f"SSL works with system CA bundle at {found}")
                print(f"  → set SSL_CERT_FILE={found} in your shell rc to make this permanent")
                return True
        # try certifi
        c3, out3 = run([str(py), "-c", "import certifi; print(certifi.where())"])
        if c3 == 0:
            cafile = out3.strip().splitlines()[-1]
            os.environ["SSL_CERT_FILE"] = cafile
            os.environ["REQUESTS_CA_BUNDLE"] = cafile
            c4, out4 = run([str(py), "-c", code], env={**os.environ})
            if c4 == 0 and "status 200" in out4:
                ok(f"SSL works with certifi at {cafile}")
                print(f"  → set SSL_CERT_FILE={cafile} in your shell rc to make this permanent")
                return True
        fail(
            "SSL still failing. On Debian/Ubuntu/WSL: `sudo apt install ca-certificates`. "
            "On macOS with python.org Python: run `/Applications/Python\\ 3.x/Install\\ Certificates.command`. "
            "Otherwise: `pip install --upgrade certifi` then re-run this checker."
        )
        return False
    fail(f"connectivity check failed:\n{out.strip()[:400]}")
    return False


def diagnose_fetch(py: Path) -> bool:
    section("Library import")
    c, out = run([str(py), "-c",
                  "from youtube_transcript_api import YouTubeTranscriptApi; print('ok')"])
    if c == 0 and "ok" in out:
        ok("youtube_transcript_api imports cleanly")
        return True
    fail(f"import failed:\n{out.strip()[:400]}")
    return False


def print_summary(ready: bool) -> None:
    section("Summary")
    if ready:
        print("  All checks passed. The skill is ready to use.")
        print("  Test it from Claude Code by pasting a YouTube URL with learning intent,")
        print("  e.g. \"make me lecture notes for https://www.youtube.com/watch?v=izZba4UA7iY\".")
    else:
        print("  Setup is NOT complete. Address the FAIL lines above and re-run me.")
        print("  If you're stuck, check references/fetch_troubleshooting.md for the full decision tree.")


def main() -> int:
    print("youtube-lecture-notes  ·  setup checker")
    print(f"skill dir: {SKILL_DIR}")
    diagnose_python()
    py = diagnose_install()
    if not py:
        print_summary(False)
        return 1
    libs_ok = diagnose_fetch(py)
    ssl_ok = diagnose_ssl(py)
    print_summary(libs_ok and ssl_ok)
    return 0 if (libs_ok and ssl_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
