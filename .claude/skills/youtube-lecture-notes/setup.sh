#!/usr/bin/env bash
# One-line setup for the youtube-lecture-notes skill.
#
# Usage (from anywhere):
#     bash ~/.claude/skills/youtube-lecture-notes/setup.sh
# or, if executable:
#     ~/.claude/skills/youtube-lecture-notes/setup.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$HERE/scripts/setup_check.py" "$@"
