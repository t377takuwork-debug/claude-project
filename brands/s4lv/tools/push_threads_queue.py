#!/usr/bin/env python3
"""Push a Threads post-queue CSV into the Google Sheets queue tab via Sheets API.

Usage:
  python push_threads_queue.py <csv_file> [--allow-past]

CSV columns (header row optional, auto-detected by date-parse failure):
  投稿日時,本文,リプライ1,リプライ2,リプライ3,リプライ4,型,FW
投稿日時 must parse as "YYYY-MM-DD HH:MM". リプライ2〜4は省略可（末尾から空でよい）。
2026-08-23: 単発の自己リプライ1本から、連続スレッド（最大4本連鎖）対応へ拡張。
リプライ1は前の投稿(本文)へ、リプライ2はリプライ1へ、…と順に連鎖して投稿される
（threads_scheduler.gs側の実装）。

Safety behavior:
  - rows whose date is before now are skipped unless --allow-past is passed
  - rows whose 投稿日時 already exists in the sheet are skipped (duplicate guard)
  - after appending, all data rows (A2:N) are re-sorted by 投稿日時 ascending, so
    the sheet stays in chronological order regardless of insertion order
    (2026-08-04: appending a slot out of order once left the queue visibly
    out of sequence until manually re-sorted; sorting is now automatic)
"""
import csv
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
EPOCH = datetime.datetime(1899, 12, 30)


def to_serial(dt):
    return (dt - EPOCH).total_seconds() / 86400.0


def get_service():
    creds = service_account.Credentials.from_service_account_file(str(CREDS_FILE), scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


ROW_WIDTH = 14  # 投稿日時,本文,リプライ1-4,型,FW,ステータス,投稿ID,リプライ投稿ID1-4


def sort_queue_by_date(sheets, spreadsheet_id, sheet_name):
    """Re-sort all data rows (A2:N) by 投稿日時 ascending, in place."""
    resp = sheets.values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A2:N",
        valueRenderOption="UNFORMATTED_VALUE",
    ).execute()
    rows = resp.get("values", [])
    if not rows:
        return
    padded = [r + [""] * (ROW_WIDTH - len(r)) for r in rows]
    padded.sort(key=lambda r: r[0] if isinstance(r[0], (int, float)) else float("inf"))
    sheets.values().update(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A2:N{len(padded) + 1}",
        valueInputOption="USER_ENTERED",
        body={"values": padded},
    ).execute()


def read_csv_rows(path):
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.reader(f):
            if not row or not row[0].strip():
                continue
            try:
                dt = datetime.datetime.strptime(row[0].strip(), "%Y-%m-%d %H:%M")
            except ValueError:
                continue  # header row or malformed date, skip silently
            rows.append({
                "dt": dt,
                "body": row[1] if len(row) > 1 else "",
                "replies": [row[i] if len(row) > i else "" for i in range(2, 6)],
                "type": row[6] if len(row) > 6 else "",
                "fw": row[7] if len(row) > 7 else "",
            })
    return rows


def main():
    if len(sys.argv) < 2:
        print("Usage: python push_threads_queue.py <csv_file> [--allow-past]")
        sys.exit(1)
    csv_path = Path(sys.argv[1])
    allow_past = "--allow-past" in sys.argv[2:]

    if not CREDS_FILE.exists():
        print(f"ERROR: credentials file not found: {CREDS_FILE}")
        sys.exit(1)
    if not csv_path.exists():
        print(f"ERROR: csv file not found: {csv_path}")
        sys.exit(1)

    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    spreadsheet_id = config["spreadsheet_id"]
    sheet_name = config["queue_sheet_name"]

    sheets = get_service().spreadsheets()

    existing = sheets.values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A2:A",
        valueRenderOption="UNFORMATTED_VALUE",
    ).execute().get("values", [])
    existing_serials = {round(r[0], 6) for r in existing if r and isinstance(r[0], (int, float))}

    now = datetime.datetime.now()
    rows = read_csv_rows(csv_path)

    to_append, skipped_past, skipped_dupe = [], [], []
    for row in rows:
        serial = round(to_serial(row["dt"]), 6)
        if row["dt"] < now and not allow_past:
            skipped_past.append(row)
        elif serial in existing_serials:
            skipped_dupe.append(row)
        else:
            to_append.append(row)

    if skipped_past:
        print(f"[SKIP] 時刻超過のため {len(skipped_past)} 件をスキップ（--allow-past で強制投入可）:")
        for row in skipped_past:
            print(f"  - {row['dt']}")
    if skipped_dupe:
        print(f"[SKIP] 既にシートに存在するため {len(skipped_dupe)} 件をスキップ（正常な動作です）:")
        for row in skipped_dupe:
            print(f"  - {row['dt']}")

    if not to_append:
        print("追加対象の行はありません。")
        return

    values = [
        [row["dt"].strftime("%Y-%m-%d %H:%M"), row["body"], *row["replies"],
         row["type"], row["fw"], "", "", "", "", "", ""]
        for row in to_append
    ]
    sheets.values().append(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A1",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": values},
    ).execute()
    sort_queue_by_date(sheets, spreadsheet_id, sheet_name)

    print(f"[OK] {len(to_append)} 件をスプレッドシートへ追加し、日時順に並べ直しました:")
    for row in to_append:
        print(f"  - {row['dt']} ({row['type']}/{row['fw']})")


if __name__ == "__main__":
    main()
