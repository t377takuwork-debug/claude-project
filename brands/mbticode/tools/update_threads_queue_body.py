#!/usr/bin/env python3
"""Update existing Threads queue rows' body text (column B) in place, matched by 投稿日時.

Unlike push_threads_queue.py (append + duplicate-skip), this OVERWRITES the 本文 cell
of rows that already exist in the sheet. Use when a post was already pushed to the
queue but the local posts_threads.txt text was revised afterward (e.g. wording fixes)
and the post has not gone out yet.

Usage:
  python update_threads_queue_body.py <posts_threads.txt> <header-prefix> [<header-prefix> ...]

<header-prefix> matches against the 【...】 header text, e.g. "7/30" or "7/30 08:00".
Only posts matching a given prefix are updated. Rows with a non-empty ステータス
(already posted) are skipped and reported, never overwritten.
"""
import datetime
import json
import re
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

HEADER_RE = re.compile(r"^【(.+?)】(.*)$")
SEP_RE = re.compile(r"^-{10,}\s*$")
DATETIME_RE = re.compile(r"(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{2})")


def parse_posts(text):
    posts = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = HEADER_RE.match(lines[i])
        if m and "URL候補" not in m.group(1):
            header = m.group(1) + m.group(2)
            j = i + 1
            while j < len(lines) and not SEP_RE.match(lines[j]):
                if HEADER_RE.match(lines[j]):
                    break
                j += 1
            if j < len(lines) and SEP_RE.match(lines[j]):
                k = j + 1
                body_lines = []
                while k < len(lines) and not SEP_RE.match(lines[k]):
                    body_lines.append(lines[k])
                    k += 1
                body = "\n".join(body_lines).strip()
                # 続き型: 本文は最初の === より前（自己リプライは別セル管理・ここでは触らない）
                main_body = re.split(r"^===+\s*$", body, flags=re.M)[0].strip()
                posts.append({"header": header, "body": main_body})
                i = k + 1
                continue
        i += 1
    return posts


def infer_year(month, day, now):
    dt = datetime.datetime(now.year, month, day)
    if (dt - now).days < -30:
        return now.year + 1
    return now.year


def main():
    if len(sys.argv) < 3:
        print("Usage: python update_threads_queue_body.py <posts_threads.txt> <header-prefix> [...]")
        sys.exit(1)
    txt_path = Path(sys.argv[1])
    prefixes = sys.argv[2:]

    posts = parse_posts(txt_path.read_text(encoding="utf-8"))
    now = datetime.datetime.now()
    targets = {}
    for p in posts:
        if not any(p["header"].startswith(pref) for pref in prefixes):
            continue
        m = DATETIME_RE.match(p["header"])
        if not m:
            continue
        month, day, hh, mm = (int(x) for x in m.groups())
        year = infer_year(month, day, now)
        key = f"{year:04d}-{month:02d}-{day:02d} {hh}:{mm:02d}"
        targets[key] = p["body"]

    if not targets:
        print("[ERROR] 指定prefixに一致する投稿がposts_threads.txt内に見つかりません。")
        sys.exit(1)

    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    spreadsheet_id = config["spreadsheet_id"]
    sheet_name = config["queue_sheet_name"]
    creds = service_account.Credentials.from_service_account_file(str(CREDS_FILE), scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds).spreadsheets()

    rows = service.values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A2:F",
        valueRenderOption="UNFORMATTED_VALUE",
    ).execute().get("values", [])

    EPOCH = datetime.datetime(1899, 12, 30)

    def serial_to_dt(serial):
        return EPOCH + datetime.timedelta(days=serial)

    data = []
    updated, skipped_posted, not_found = [], [], list(targets.keys())
    for idx, r in enumerate(rows, start=2):
        if not r:
            continue
        serial = r[0]
        if not isinstance(serial, (int, float)):
            continue
        dt = serial_to_dt(serial)
        key = f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d} {dt.hour}:{dt.minute:02d}"
        if key not in targets:
            continue
        status = r[5] if len(r) > 5 else ""
        if status:
            skipped_posted.append((key, status))
            if key in not_found:
                not_found.remove(key)
            continue
        data.append({
            "range": f"{sheet_name}!B{idx}",
            "values": [[targets[key]]],
        })
        updated.append(key)
        if key in not_found:
            not_found.remove(key)

    if data:
        service.values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"valueInputOption": "USER_ENTERED", "data": data},
        ).execute()

    print(f"[OK] {len(updated)} 件の本文を上書きしました:")
    for k in updated:
        print(f"  - {k}")
    if skipped_posted:
        print(f"[SKIP] 投稿済みのため {len(skipped_posted)} 件はスキップ:")
        for k, s in skipped_posted:
            print(f"  - {k} (ステータス: {s})")
    if not_found:
        print(f"[WARN] シート内に見つからなかった日時: {len(not_found)} 件:")
        for k in not_found:
            print(f"  - {k}")


if __name__ == "__main__":
    main()
