#!/usr/bin/env python3
"""Show recent + upcoming rows of the Threads posting queue (read-only).

Usage:
  python show_queue_recent.py [--days N] [--full]

Purpose (2026-09-29): the spreadsheet is now the single source of truth for
Threads posts (posts_threads.txt is no longer appended to). The old
"使用済みネタ確認 = posts_threads.txt の直近7日＋未来分" step is replaced by this
listing: every queue row from N days ago (default 7) through the future.

Columns read (see threads_scheduler.gs header):
  A 投稿日時 | B 本文 | C リプライ本文 | D 型 | E FW | F ステータス | ... | J URL自己リプライ本文

Prints one line per row: 投稿日時 / ステータス / 型／FW / 本文の冒頭。
--full prints the whole 本文 and 自己リプライ (newlines flattened) so the
"主張の骨子" of near-duplicate topics can be compared.
Read-only (spreadsheets.readonly scope); writes nothing.
"""
import argparse
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
PREVIEW_CHARS = 40


def flat(s):
    return (s or "").replace("\r", "").replace("\n", " ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7, help="何日前の投稿から表示するか（既定7）")
    ap.add_argument("--full", action="store_true", help="本文・リプライを全文表示する")
    args = ap.parse_args()

    if not CREDS_FILE.exists():
        print(f"ERROR: credentials file not found: {CREDS_FILE}")
        sys.exit(1)

    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    creds = service_account.Credentials.from_service_account_file(str(CREDS_FILE), scopes=SCOPES)
    sheets = build("sheets", "v4", credentials=creds).spreadsheets()
    resp = sheets.values().get(
        spreadsheetId=config["spreadsheet_id"],
        range=f"{config['queue_sheet_name']}!A2:J",
        valueRenderOption="FORMATTED_VALUE",
    ).execute()
    rows = resp.get("values", [])

    since = datetime.datetime.now() - datetime.timedelta(days=args.days)
    picked = []
    for r in rows:
        if not r or not r[0].strip():
            continue
        try:
            dt = datetime.datetime.strptime(r[0].strip(), "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        if dt >= since:
            picked.append((dt, r))
    picked.sort(key=lambda x: x[0])

    def col(r, i):
        return r[i] if len(r) > i else ""

    print(f"=== Threads投稿キュー: {since:%Y-%m-%d} 以降 {len(picked)}行 ===")
    for dt, r in picked:
        status = col(r, 5).strip() or "未投稿"
        head = f"{dt:%m/%d %H:%M} [{status}] {col(r, 3)}／{col(r, 4)}"
        if args.full:
            print(head)
            print(f"  本文: {flat(col(r, 1))}")
            if col(r, 2).strip():
                print(f"  自己リプライ: {flat(col(r, 2))}")
            if col(r, 9).strip():
                print(f"  URL自己リプライ: {flat(col(r, 9))}")
        else:
            body = flat(col(r, 1))
            more = "…" if len(body) > PREVIEW_CHARS else ""
            print(f"{head}  {body[:PREVIEW_CHARS]}{more}")


if __name__ == "__main__":
    main()
