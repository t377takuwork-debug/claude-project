#!/usr/bin/env python3
"""シートで「投稿済み」になった投稿を、まだ記録していないものだけ、`スレッズ反響記録.md` の末尾に足す。

使い方: python record_posted.py [--dry-run]

目的: 「スレッズに出しました」と手で伝える手間をなくし、スレッズ投稿AIが重なりを避けるための記録を、いつも最新にする。
見分け方: 本文の1行目が、記録ファイルにすでにあれば、足さない。読み取りだけ(シートは変更しない)。
"""
import datetime
import json
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from google.oauth2 import service_account
from googleapiclient.discovery import build

TOOLS_DIR = Path(__file__).resolve().parent
RECORD = TOOLS_DIR.parent / "スレッズ反響記録.md"
CREDS_FILE = TOOLS_DIR / "sheets_service_account.local.json"
CONFIG_FILE = TOOLS_DIR / "sheets_config.json"
EPOCH = datetime.datetime(1899, 12, 30)
SEP = "-" * 32


def col(r, i):
    return r[i] if len(r) > i else ""


def main():
    dry = "--dry-run" in sys.argv
    cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    creds = service_account.Credentials.from_service_account_file(
        str(CREDS_FILE), scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    rows = build("sheets", "v4", credentials=creds).spreadsheets().values().get(
        spreadsheetId=cfg["spreadsheet_id"], range=f"{cfg['queue_sheet_name']}!A2:J",
        valueRenderOption="UNFORMATTED_VALUE").execute().get("values", [])
    text = RECORD.read_text(encoding="utf-8")
    new = []
    for r in rows:
        if col(r, 8) != "投稿済み" or not isinstance(col(r, 0), (int, float)):
            continue
        body = str(col(r, 1)).strip()
        first = body.splitlines()[0].strip() if body else ""
        if not first or first in text:
            continue
        dt = EPOCH + datetime.timedelta(days=r[0])
        replies = [str(col(r, i)).strip() for i in range(2, 6) if str(col(r, i)).strip()]
        block = [f"【{dt:%Y-%m-%d %H:%M}】型：{col(r, 6)} ／自動投稿で出した分", body]
        for t in replies:
            block += ["自己返信：", t]
        block.append(SEP)
        new.append("\n".join(block))
    if not new:
        print("[OK] 追記する投稿はありません(記録は最新です)")
        return
    print(f"[{'DRY-RUN' if dry else 'OK'}] {len(new)}件を{'追記する予定' if dry else '追記'}")
    for b in new:
        print(b.splitlines()[0])
    if not dry:
        RECORD.write_text(text.rstrip("\n") + "\n\n" + "\n\n".join(new) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
