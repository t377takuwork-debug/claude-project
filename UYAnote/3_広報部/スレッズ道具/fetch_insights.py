#!/usr/bin/env python3
"""Fetch the Threads Insights tab from the queue spreadsheet via Sheets API.

Usage:
  python fetch_insights.py

Prints every row of the インサイト tab (投稿ID|投稿日時|型|FW|Views|Likes|Replies|
Reposts|Quotes|取得日時) as a markdown table, read-only. This replaces the manual
copy-paste step for weekly analysis; the analysis judgment itself still happens
in conversation, not in this script.
"""
import json
import sys
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

TOOLS_DIR = Path(__file__).resolve().parent
CREDS_FILE = TOOLS_DIR / "sheets_service_account.local.json"
CONFIG_FILE = TOOLS_DIR / "sheets_config.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

HEADER = ["投稿ID", "投稿日時", "型", "FW", "Views", "Likes", "Replies", "Reposts", "Quotes", "取得日時"]


def main():
    if not CREDS_FILE.exists():
        print(f"ERROR: credentials file not found: {CREDS_FILE}")
        sys.exit(1)

    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    spreadsheet_id = config["spreadsheet_id"]
    sheet_name = config["insights_sheet_name"]

    creds = service_account.Credentials.from_service_account_file(str(CREDS_FILE), scopes=SCOPES)
    sheets = build("sheets", "v4", credentials=creds).spreadsheets()

    resp = sheets.values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A2:J",
        valueRenderOption="FORMATTED_VALUE",
    ).execute()
    rows = resp.get("values", [])

    if not rows:
        print("インサイトタブにデータがありません。")
        return

    print("| " + " | ".join(HEADER) + " |")
    print("|" + "---|" * len(HEADER))
    for row in rows:
        padded = row + [""] * (len(HEADER) - len(row))
        print("| " + " | ".join(padded) + " |")
    print(f"\n{len(rows)}件取得しました。")


if __name__ == "__main__":
    main()
