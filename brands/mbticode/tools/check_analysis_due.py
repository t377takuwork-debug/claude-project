#!/usr/bin/env python3
"""Check whether the weekly Threads insight analysis is overdue.

Usage:
  python check_analysis_due.py

The authoritative record of "when was the last weekly analysis" is the newest
`## YYYY-MM-DD 週次分析` heading in ../threads_insights_notes.md. threads_analysis_log.json
(last_analysis_date) is a secondary record that threads_analyze.py --commit stamps;
it is kept so the s4lv/vivant copies of this script stay structurally identical.
This script uses whichever of the two is more recent, so a forgotten json update
(the 2026-08-28 drift: json said 8/2 while the notes file already had an 8/14 entry)
can no longer produce a false "overdue".
Exit code is always 0; this is an advisory nudge, not a hard gate.
"""
import datetime
import json
import re
import sys
from pathlib import Path

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

TOOLS_DIR = Path(__file__).resolve().parent
LOG_FILE = TOOLS_DIR / "threads_analysis_log.json"
NOTES_FILE = TOOLS_DIR.parent / "threads_insights_notes.md"
DUE_AFTER_DAYS = 7
HEADING_RE = re.compile(r"^##\s*(\d{4}-\d{2}-\d{2})\s*週次分析", re.MULTILINE)


def date_from_log():
    if not LOG_FILE.exists():
        return None
    try:
        last = json.loads(LOG_FILE.read_text(encoding="utf-8")).get("last_analysis_date")
        return datetime.date.fromisoformat(last) if last else None
    except (ValueError, json.JSONDecodeError):
        return None


def date_from_notes():
    if not NOTES_FILE.exists():
        return None
    dates = [datetime.date.fromisoformat(m) for m in HEADING_RE.findall(NOTES_FILE.read_text(encoding="utf-8"))]
    return max(dates) if dates else None


def main():
    candidates = [d for d in (date_from_log(), date_from_notes()) if d]
    if not candidates:
        print("[REMINDER] 週次分析の記録が見つかりません。「週次分析して」と依頼することをおすすめします。")
        return

    last_date = max(candidates)
    days_since = (datetime.date.today() - last_date).days
    if days_since >= DUE_AFTER_DAYS:
        print(f"[REMINDER] 前回の分析から{days_since}日経過しています（最終分析日: {last_date}）。"
              f"`python tools/threads_analyze.py` で集計してから週次分析を書くのがおすすめです。")
    else:
        print(f"[OK] 前回の分析から{days_since}日目です（最終分析日: {last_date}）。")


if __name__ == "__main__":
    main()
