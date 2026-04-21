#!/usr/bin/env bash
# lab-notebook-gate.sh
# Pre-commit hook: blocks commits when LAB_NOTEBOOK.md exists but has no entry in the last 24h.
# Opt-in: projects without LAB_NOTEBOOK.md are completely unaffected.
#
# Usage: called automatically by the PreToolUse hook in hooks.json on git commit.
# Bypass: git commit --no-verify

set -euo pipefail

# Locate git root (works from any subdirectory)
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || {
  # Not a git repo or git unavailable — allow commit
  exit 0
}

NOTEBOOK="$GIT_ROOT/LAB_NOTEBOOK.md"

# Opt-in check: no notebook → no enforcement
if [ ! -f "$NOTEBOOK" ]; then
  exit 0
fi

# Check for an entry within the last 24 hours using file modification time as
# a fast proxy. If the file itself was modified within 24h, allow the commit.
# This is intentionally cheap (<1ms) to avoid annoying users on every commit.
NOW=$(date +%s)
MTIME=$(stat -c %Y "$NOTEBOOK" 2>/dev/null || stat -f %m "$NOTEBOOK" 2>/dev/null || echo 0)
AGE=$(( NOW - MTIME ))

if [ "$AGE" -le 86400 ]; then
  # File modified within 24 hours — entry is recent enough
  exit 0
fi

# File exists but hasn't been touched in >24h. One more check: scan for a
# date stamp in the last 24h inside the file content. This handles the case
# where someone edited the file days ago but added a timestamped entry today.
# Pattern: any ISO-style date (YYYY-MM-DD) in the last 24h anywhere in the file.
YESTERDAY=$(date -d "24 hours ago" +%Y-%m-%d 2>/dev/null || date -v-24H +%Y-%m-%d 2>/dev/null || echo "")
TODAY=$(date +%Y-%m-%d)

if [ -n "$TODAY" ] && grep -qE "$TODAY|$YESTERDAY" "$NOTEBOOK" 2>/dev/null; then
  # Found a date stamp from today or yesterday — allow commit
  exit 0
fi

echo ""
echo "LAB_NOTEBOOK.md exists but has no entry in the last 24 hours."
echo "Update it before committing (Rule 11 from lab-notebook CLAUDE.md section)."
echo ""
echo "To bypass: git commit --no-verify"
echo ""
exit 1
