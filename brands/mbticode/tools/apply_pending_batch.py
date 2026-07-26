#!/usr/bin/env python3
"""Apply a _pending_batch.json (from the Threads Phase3 weekly routine) into
the Google Sheets queue tab via Sheets API.

Usage:
  python apply_pending_batch.py <pending_batch.json> [--allow-past]

The weekly cloud routine (trig_011xykqfMBrvkzvnmUtrmjBa) generates next
week's batch, runs it through qa_post.py, and — since the cloud sandbox
cannot reach the Sheets API or push to GitHub (2026-07-26notekaigi Phase3,
confirmed by testing) — attaches the result as a downloadable
_pending_batch.json on the routine's run page instead of applying it itself.
Download that file and run this script once a week to finish the job.

JSON shape: {"rows": [{"datetime": "YYYY-MM-DD HH:MM", "body": "...",
"reply": "...", "type": "...", "fw": "..."}, ...]}

Safety behavior (mirrors push_threads_queue.py):
  - rows whose date is before now are skipped unless --allow-past is passed
  - rows whose 投稿日時 already exists in the sheet are skipped (duplicate guard)
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
EPOCH = datetime.datetime(1899, 12, 30)


def to_serial(dt):
    return (dt - EPOCH).total_seconds() / 86400.0


def get_service():
    creds = service_account.Credentials.from_service_account_file(str(CREDS_FILE), scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def read_batch_rows(path):
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    rows = []
    for r in data.get("rows", []):
        try:
            dt = datetime.datetime.strptime(str(r["datetime"]).strip(), "%Y-%m-%d %H:%M")
        except (ValueError, KeyError):
            print(f"[WARN] 日時をパースできない行をスキップ: {r}")
            continue
        rows.append({
            "dt": dt, "body": r.get("body", ""), "reply": r.get("reply", ""),
            "type": r.get("type", ""), "fw": r.get("fw", ""),
        })
    return rows


def main():
    if len(sys.argv) < 2:
        print("Usage: python apply_pending_batch.py <pending_batch.json> [--allow-past]")
        sys.exit(1)
    batch_path = Path(sys.argv[1])
    allow_past = "--allow-past" in sys.argv[2:]

    if not CREDS_FILE.exists():
        print(f"ERROR: credentials file not found: {CREDS_FILE}")
        sys.exit(1)
    if not batch_path.exists():
        print(f"ERROR: batch file not found: {batch_path}")
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
    rows = read_batch_rows(batch_path)

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
        [row["dt"].strftime("%Y-%m-%d %H:%M"), row["body"], row["reply"], row["type"], row["fw"], "", "", ""]
        for row in to_append
    ]
    sheets.values().append(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A1",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": values},
    ).execute()

    print(f"[OK] {len(to_append)} 件をスプレッドシートへ追加しました:")
    for row in to_append:
        print(f"  - {row['dt']} ({row['type']}/{row['fw']})")


if __name__ == "__main__":
    main()
