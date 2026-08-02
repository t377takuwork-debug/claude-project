#!/usr/bin/env python3
"""Check whether the weekly Threads insight analysis is overdue.

Usage:
  python check_analysis_due.py

Reads threads_analysis_log.json (last_analysis_date, updated manually whenever
a weekly analysis is completed) and reports how many days have passed. Exit
code is always 0; this is an advisory nudge, not a hard gate.
"""
import datetime
import json
import sys
from pathlib import Path

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

TOOLS_DIR = Path(__file__).resolve().parent
LOG_FILE = TOOLS_DIR / "threads_analysis_log.json"
DUE_AFTER_DAYS = 7


def main():
    if not LOG_FILE.exists():
        print("[REMINDER] 分析ログが見つかりません。週次分析を一度も実施していない可能性があります。")
        return

    data = json.loads(LOG_FILE.read_text(encoding="utf-8"))
    last = data.get("last_analysis_date")

    if not last:
        print("[REMINDER] 週次分析がまだ一度も記録されていません。「週次分析して」と依頼することをおすすめします。")
        return

    last_date = datetime.date.fromisoformat(last)
    days_since = (datetime.date.today() - last_date).days

    if days_since >= DUE_AFTER_DAYS:
        print(f"[REMINDER] 前回の分析から{days_since}日経過しています（最終分析日: {last}）。週次分析をおすすめします。")
    else:
        print(f"[OK] 前回の分析から{days_since}日目です（最終分析日: {last}）。")


if __name__ == "__main__":
    main()
