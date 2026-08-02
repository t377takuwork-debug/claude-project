#!/usr/bin/env python3
"""Check how many days of Threads posting queue coverage remain.

Usage:
  python check_queue_coverage.py

Reads the 投稿日時 column of 「Threads投稿キュー」 and reports the gap between
today and the furthest-scheduled row. This is a read-only, advisory nudge
(exit code always 0).
"""
import datetime
import json
import sys
from pathlib import Path

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from google.oauth2 import service_account
from googleapiclient.discovery import build

TOOLS_DIR = Path(__file__).resolve().parent
CREDS_FILE = TOOLS_DIR / "sheets_service_account.local.json"
CONFIG_FILE = TOOLS_DIR / "sheets_config.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
WARN_BELOW_DAYS = 3


def main():
    if not CREDS_FILE.exists():
        print(f"ERROR: credentials file not found: {CREDS_FILE}")
        sys.exit(1)

    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    spreadsheet_id = config["spreadsheet_id"]
    sheet_name = config["queue_sheet_name"]

    creds = service_account.Credentials.from_service_account_file(str(CREDS_FILE), scopes=SCOPES)
    sheets = build("sheets", "v4", credentials=creds).spreadsheets()

    resp = sheets.values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A2:A",
        valueRenderOption="FORMATTED_VALUE",
    ).execute()
    rows = resp.get("values", [])

    latest = None
    for r in rows:
        if not r or not r[0].strip():
            continue
        try:
            dt = datetime.datetime.strptime(r[0].strip(), "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        if latest is None or dt > latest:
            latest = dt

    if latest is None:
        print("[REMINDER] 投稿キューに日時付きの行が1件もありません。次回投稿バッチの投入を確認してください。")
        return

    days_remaining = (latest - datetime.datetime.now()).total_seconds() / 86400.0

    if days_remaining < WARN_BELOW_DAYS:
        print(f"[REMINDER] 投稿キューの残りは約{days_remaining:.1f}日分です（最終予定: {latest}）。"
              f"push_threads_queue.pyで次のバッチを投入してください。")
    else:
        print(f"[OK] 投稿キューは約{days_remaining:.1f}日分残っています（最終予定: {latest}）。")


if __name__ == "__main__":
    main()
