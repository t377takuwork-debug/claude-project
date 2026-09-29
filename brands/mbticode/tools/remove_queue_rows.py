#!/usr/bin/env python3
"""Safely REMOVE not-yet-posted rows from the Threads queue sheet (whole rows are deleted).

Usage:
  python remove_queue_rows.py "9/30 12:00" "9/30 19:00" ...            # dry-run (default): show what would be removed
  python remove_queue_rows.py "9/30 12:00" ... --apply                 # back up the rows, then delete them

Why (2026-09-30): Threads went from 5 to 3 posts/day (08:00・16:00・22:00). replace_queue_rows.py can only overwrite
rows, so the 12:00 / 19:00 rows had no way to be removed.

Safety rules (fail closed — any violation aborts the whole run, nothing is written):
  - every given 日時 must match exactly one sheet row
  - the row's ステータス(F), 投稿ID(G), リプライ投稿ID(H), URL自己リプライ投稿ID(K) must all be empty (not posted yet)
  - rows less than 60 minutes from now are refused (--allow-soon to override)
  - on --apply the full rows (A..K) are saved to posts/archive/queue_removed_<timestamp>.json first
  - after deleting, the queue is re-read: the removed 日時 must be gone and the row count must have dropped by exactly N
"""
import argparse
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
BACKUP_DIR = TOOLS_DIR.parent / "posts" / "archive"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
EPOCH = datetime.datetime(1899, 12, 30)
DT_RE = re.compile(r"^(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{2})$")


def to_dt(serial):
    return EPOCH + datetime.timedelta(days=serial)


def read_rows(svc, sid, sheet):
    return svc.values().get(spreadsheetId=sid, range=f"{sheet}!A2:K", valueRenderOption="UNFORMATTED_VALUE").execute().get("values", [])


def index_by_dt(rows):
    by_dt = {}
    for idx, r in enumerate(rows, start=2):
        if r and isinstance(r[0] if r else None, (int, float)):
            by_dt.setdefault(to_dt(r[0]).replace(second=0, microsecond=0), []).append(idx)
    return by_dt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("when", nargs="+", help='例："9/30 12:00"')
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--allow-soon", action="store_true")
    ap.add_argument("--year", type=int, default=datetime.date.today().year)
    args = ap.parse_args()

    targets = []
    for w in args.when:
        m = DT_RE.match(w.strip())
        if not m:
            print(f"[ERROR] 日時が読み取れません：{w}")
            sys.exit(2)
        mo, da, hh, mm = map(int, m.groups())
        targets.append(datetime.datetime(args.year, mo, da, hh, mm))

    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    sid, sheet = config["spreadsheet_id"], config["queue_sheet_name"]
    creds = service_account.Credentials.from_service_account_file(str(CREDS_FILE), scopes=SCOPES)
    api = build("sheets", "v4", credentials=creds)
    svc = api.spreadsheets()
    rows = read_rows(svc, sid, sheet)
    by_dt = index_by_dt(rows)

    def cell(r, i):
        return r[i] if len(r) > i else ""

    now = datetime.datetime.now()
    problems, plan = [], []
    for dt in targets:
        hits = by_dt.get(dt, [])
        if len(hits) != 1:
            problems.append(f"{dt:%m/%d %H:%M}：シートで一致する行が{len(hits)}件（1件のみ許可）")
            continue
        idx = hits[0]
        r = rows[idx - 2]
        posted = {"ステータス": cell(r, 5), "投稿ID": cell(r, 6), "リプライ投稿ID": cell(r, 7), "URL返信ID": cell(r, 10)}
        if any(str(v).strip() for v in posted.values()):
            problems.append(f"{dt:%m/%d %H:%M}：投稿済み・処理済みの印がある行は削除しません {posted}")
            continue
        if (dt - now) < datetime.timedelta(minutes=60) and not args.allow_soon:
            problems.append(f"{dt:%m/%d %H:%M}：投稿まで60分未満の行は削除しません（--allow-soonで許可）")
            continue
        plan.append({"row": idx, "dt": dt, "values": list(r)})
    if problems:
        print("[ABORT] 次の問題があるため、何も削除しません：")
        for m in problems:
            print("  -", m)
        sys.exit(1)

    mode = "削除" if args.apply else "確認（削除しません）"
    print(f"=== {mode}：{len(plan)}行 ===")
    for p in plan:
        v = p["values"]
        print(f"行{p['row']} {p['dt']:%m/%d %H:%M} [{cell(v, 3)}／{cell(v, 4)}] {str(cell(v, 1)).replace(chr(10), ' ')[:40]}")
    if not args.apply:
        print("\n削除するには --apply を付けて再実行してください（実行前に、行の内容を posts/archive/ にバックアップします）。")
        return

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bpath = BACKUP_DIR / f"queue_removed_{stamp}.json"
    bpath.write_text(json.dumps([{"row": p["row"], "dt": f"{p['dt']:%Y-%m-%d %H:%M}", "values": p["values"]} for p in plan],
                                ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] 削除する行をバックアップ：{bpath}")

    meta = svc.get(spreadsheetId=sid, fields="sheets.properties").execute()
    sheet_id = next(s["properties"]["sheetId"] for s in meta["sheets"] if s["properties"]["title"] == sheet)
    reqs = [{"deleteDimension": {"range": {"sheetId": sheet_id, "dimension": "ROWS",
                                            "startIndex": p["row"] - 1, "endIndex": p["row"]}}}
            for p in sorted(plan, key=lambda x: -x["row"])]  # bottom-up so indexes stay valid
    svc.batchUpdate(spreadsheetId=sid, body={"requests": reqs}).execute()

    after = read_rows(svc, sid, sheet)
    after_dt = index_by_dt(after)
    still = [f"{p['dt']:%m/%d %H:%M}" for p in plan if p["dt"] in after_dt]
    n_before = sum(1 for r in rows if r and isinstance(r[0], (int, float)))
    n_after = sum(1 for r in after if r and isinstance(r[0], (int, float)))
    if still or n_before - n_after != len(plan):
        print(f"[ERROR] 検証に失敗：残っている行={still} / 日時つき行数 {n_before}→{n_after}（期待 -{len(plan)}）")
        sys.exit(1)
    print(f"[OK] {len(plan)}行を削除し、読み直して確認しました（日時つき行数 {n_before}→{n_after}）。")


if __name__ == "__main__":
    main()
