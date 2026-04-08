#!/usr/bin/env bash
# check-versions.sh — Compare two semver strings
# Usage: check-versions.sh <local-version> <upstream-version>
# Exit codes:
#   0 = update available (upstream is newer)
#   1 = up to date (versions equal)
#   2 = local is newer than upstream
#   3 = usage error

set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "Usage: check-versions.sh <local-version> <upstream-version>"
    exit 3
fi

LOCAL="$1"
UPSTREAM="$2"

# Strip leading 'v' if present
LOCAL="${LOCAL#v}"
UPSTREAM="${UPSTREAM#v}"

# Split into major.minor.patch
IFS='.' read -r L_MAJOR L_MINOR L_PATCH <<< "$LOCAL"
IFS='.' read -r U_MAJOR U_MINOR U_PATCH <<< "$UPSTREAM"

# Default missing parts to 0
L_MAJOR="${L_MAJOR:-0}"; L_MINOR="${L_MINOR:-0}"; L_PATCH="${L_PATCH:-0}"
U_MAJOR="${U_MAJOR:-0}"; U_MINOR="${U_MINOR:-0}"; U_PATCH="${U_PATCH:-0}"

compare() {
    if [[ "$1" -lt "$2" ]]; then echo "older"; return; fi
    if [[ "$1" -gt "$2" ]]; then echo "newer"; return; fi
    echo "equal"
}

RESULT=$(compare "$L_MAJOR" "$U_MAJOR")
if [[ "$RESULT" == "equal" ]]; then
    RESULT=$(compare "$L_MINOR" "$U_MINOR")
    if [[ "$RESULT" == "equal" ]]; then
        RESULT=$(compare "$L_PATCH" "$U_PATCH")
    fi
fi

case "$RESULT" in
    older)
        echo "update_available|${LOCAL}|${UPSTREAM}"
        exit 0
        ;;
    equal)
        echo "up_to_date|${LOCAL}|${UPSTREAM}"
        exit 1
        ;;
    newer)
        echo "local_newer|${LOCAL}|${UPSTREAM}"
        exit 2
        ;;
esac
