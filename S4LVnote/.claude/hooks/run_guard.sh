#!/bin/sh
# ブラウザガードの起動ラッパー(Mac / Windows(Git Bash) 共通)
# python3 → python → py -3 の順に「実際に動くもの」を探して browser_guard.py を実行する
# (Windowsでは python3 がストアの案内用の空コマンドになっていることがあるため、存在確認だけでは足りない)
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
# Pythonが見つからない場合はガード無しで通す(作業を止めない)
[ -z "$PY" ] && exit 0

exec $PY .claude/hooks/browser_guard.py "$@"
