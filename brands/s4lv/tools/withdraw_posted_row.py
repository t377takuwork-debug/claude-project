#!/usr/bin/env python3
"""Safely mark an already-posted Threads queue row as withdrawn-from-platform.

Use this when a post went out via postScheduled() (ステータス = 投稿済み) and was
then deleted directly on Threads (outside this automation's knowledge). The row
must NOT be re-queued by clearing ステータス — postScheduled() only skips rows
whose ステータス is exactly "投稿済み" or "エラー", so blanking it (or writing any
other value) would make the next trigger run re-publish the withdrawn text.

What this script does instead:
  - leaves 投稿日時 / 本文 / リプライ本文 / 型 / FW / ステータス untouched
  - clears 投稿ID and リプライ投稿ID only, so collectInsights() (which requires
    both ステータス == "投稿済み" and a non-empty 投稿ID) stops calling the Threads
    API for a post_id that no longer exists on the platform

Usage:
  python withdraw_posted_row.py "2026-08-03 12:00"

Refuses (exit 1) if the row's ステータス is not exactly "投稿済み" (e.g. not
found, still pending, or already an エラー row) — those cases don't need this
treatment and touching them would be the wrong operation.
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
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def main():
    if len(sys.argv) != 2:
        print('Usage: python withdraw_posted_row.py "YYYY-MM-DD HH:MM"')
        sys.exit(1)
    try:
        target = datetime.datetime.strptime(sys.argv[1].strip(), "%Y-%m-%d %H:%M")
    except ValueError:
        print(f"ERROR: 日時の形式が不正です（例: 2026-08-03 12:00）: {sys.argv[1]!r}")
        sys.exit(1)

    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    spreadsheet_id = config["spreadsheet_id"]
    sheet_name = config["queue_sheet_name"]
    creds = service_account.Credentials.from_service_account_file(str(CREDS_FILE), scopes=SCOPES)
    sheets = build("sheets", "v4", credentials=creds).spreadsheets()

    rows = sheets.values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A2:H",
        valueRenderOption="UNFORMATTED_VALUE",
    ).execute().get("values", [])

    EPOCH = datetime.datetime(1899, 12, 30)

    def serial_to_dt(serial):
        return EPOCH + datetime.timedelta(days=serial)

    for idx, r in enumerate(rows, start=2):
        if not r or not isinstance(r[0], (int, float)):
            continue
        if serial_to_dt(r[0]) != target:
            continue

        status = r[5] if len(r) > 5 else ""
        if status != "投稿済み":
            print(f"[ERROR] {target} 行のステータスは {status!r} です。"
                  f"「投稿済み」以外の行はこのスクリプトの対象外なので何もしていません。")
            sys.exit(1)

        sheets.values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {"range": f"{sheet_name}!G{idx}", "values": [[""]]},
                    {"range": f"{sheet_name}!H{idx}", "values": [[""]]},
                ],
            },
        ).execute()
        print(f"[OK] {target}: 投稿ID・リプライ投稿IDを空にしました（ステータス「投稿済み」は維持＝再投稿されません）")
        return

    print(f"[ERROR] {target} に一致する行がシート内に見つかりませんでした。")
    sys.exit(1)


if __name__ == "__main__":
    main()
