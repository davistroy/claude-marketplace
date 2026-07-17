#!/bin/bash
#
# install-hooks.sh — installs the claude-marketplace git hooks
#
# Copies scripts/pre-commit into .git/hooks/pre-commit and makes it
# executable. Safe to re-run at any time (idempotent) — e.g. after
# pulling hook updates from origin.
#
# Usage:
#   bash scripts/install-hooks.sh
#
# Verify installation:
#   test -x .git/hooks/pre-commit && echo "hook installed"
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SOURCE_HOOK="$REPO_ROOT/scripts/pre-commit"
GIT_HOOKS_DIR="$REPO_ROOT/.git/hooks"
TARGET_HOOK="$GIT_HOOKS_DIR/pre-commit"

if [ ! -f "$SOURCE_HOOK" ]; then
    echo "ERROR: $SOURCE_HOOK not found." >&2
    exit 1
fi

if [ ! -d "$GIT_HOOKS_DIR" ]; then
    echo "ERROR: $GIT_HOOKS_DIR not found. Is this a git repository?" >&2
    exit 1
fi

cp "$SOURCE_HOOK" "$TARGET_HOOK"
chmod +x "$TARGET_HOOK"

echo "Pre-commit hook installed at $TARGET_HOOK"
