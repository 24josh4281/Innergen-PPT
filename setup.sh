#!/usr/bin/env sh
# Slide Master / INNerGEN skill set - macOS / Linux / Git Bash setup
# Creates .venv, installs dependencies and fonts, and syncs the Claude / GPT (Codex) / Gemini skill sets.
# Usage:  sh setup.sh [--skip-fonts] [--recreate] [--check]
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$ROOT/.claude/skills/ppt-master/scripts/setup_env.py"

for py in python3 python; do
    if command -v "$py" >/dev/null 2>&1 &&
       "$py" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
        exec "$py" "$SCRIPT" "$@"
    fi
done
echo "Python 3.10+ not found. Install it (https://www.python.org/downloads/) and re-run." >&2
exit 1
