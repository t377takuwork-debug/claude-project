#!/bin/sh
# 作業の終わりの合図の起動ラッパー(Mac / Windows(Git Bash) 共通)。Pythonの探し方は run_guard.sh と同じ
if [ -n "$CLAUDE_PROJECT_DIR" ]; then cd "$CLAUDE_PROJECT_DIR"; else cd "$(dirname "$0")/../.."; fi 2>/dev/null

PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys" >/dev/null 2>&1; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ] && command -v py >/dev/null 2>&1 && py -3 -c "import sys" >/dev/null 2>&1; then
  PY="py -3"
fi
# Pythonが見つからない場合は何もしない(作業を止めない)
[ -z "$PY" ] && exit 0

exec $PY .claude/hooks/owari_signal.py
