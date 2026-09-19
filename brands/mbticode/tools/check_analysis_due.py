#!/usr/bin/env python3
"""Report how long it has been since the last Threads insight analysis.

Usage:
  python check_analysis_due.py

The authoritative record of "when was the last analysis" is the newest
`## YYYY-MM-DD 週次分析` heading in ../threads_insights_notes.md. threads_analysis_log.json
(last_analysis_date) is a secondary record that threads_analyze.py --commit stamps;
it is kept so the s4lv/vivant copies of this script stay structurally identical.
This script uses whichever of the two is more recent, so a forgotten json update
(the 2026-08-28 drift: json said 8/2 while the notes file already had an 8/14 entry)
can no longer produce a stale reading.

2026-09-19: analysis frequency is no longer fixed to "weekly" (a 22-day gap
proved the fixed cadence wasn't being followed anyway). This script now only
reports elapsed days as neutral information -- it does not judge anything as
"overdue" or nudge the user to run it. Analysis happens when the user asks.
Exit code is always 0.
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
        print("[INFO] 分析の記録がまだありません。")
        return

    last_date = max(candidates)
    days_since = (datetime.date.today() - last_date).days
    print(f"[INFO] 前回の分析から{days_since}日経過しています（最終分析日: {last_date}）。"
          f"分析が必要なタイミングであれば `python tools/threads_analyze.py` で集計できます。")


if __name__ == "__main__":
    main()
