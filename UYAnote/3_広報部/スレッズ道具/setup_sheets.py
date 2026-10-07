#!/usr/bin/env python3
"""スプレッドシートに、4つのタブと見出しの行を作る(すでにあるタブには触らない)。

使い方: python setup_sheets.py
タブ: Threads投稿キュー / 設定 / インサイト / 日次観測ログ
列の順番は threads_scheduler.gs の COL・ICOL・OCOL と一致させてある。変えない。
"""
import json
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from google.oauth2 import service_account
from googleapiclient.discovery import build

TOOLS_DIR = Path(__file__).resolve().parent
CREDS_FILE = TOOLS_DIR / "sheets_service_account.local.json"
CONFIG_FILE = TOOLS_DIR / "sheets_config.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

HEADERS = {
    "queue_sheet_name": ["投稿日時", "本文", "リプライ1本文", "リプライ2本文", "リプライ3本文", "リプライ4本文",
                         "型", "FW", "ステータス", "投稿ID", "リプライ1投稿ID", "リプライ2投稿ID",
                         "リプライ3投稿ID", "リプライ4投稿ID", "トピック"],
    "insights_sheet_name": ["投稿ID", "投稿日時", "型", "FW", "Views", "Likes", "Replies", "Reposts", "Quotes", "取得日時"],
    "obs_sheet_name": ["日付", "集計対象投稿数", "合計Views", "合計Likes", "合計Replies", "合計Reposts", "合計Quotes",
                       "エンゲージ率(%)", "返信率(%)", "いいね率(%)", "リポスト率(%)", "記録日時"],
}


def main():
    cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    creds = service_account.Credentials.from_service_account_file(str(CREDS_FILE), scopes=SCOPES)
    api = build("sheets", "v4", credentials=creds).spreadsheets()
    sid = cfg["spreadsheet_id"]
    meta = api.get(spreadsheetId=sid).execute()
    ids = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}
    print("既存のタブ:", sorted(ids))
    # 手で作ってあった「投稿キュー」を、仕組みが探す名前に直す
    q = cfg["queue_sheet_name"]
    if q not in ids and "投稿キュー" in ids:
        api.batchUpdate(spreadsheetId=sid, body={"requests": [{"updateSheetProperties": {
            "properties": {"sheetId": ids["投稿キュー"], "title": q}, "fields": "title"}}]}).execute()
        ids[q] = ids.pop("投稿キュー")
        print(f"[OK] 「投稿キュー」を「{q}」に名前変更")
    wanted = [(cfg[k], h) for k, h in HEADERS.items()] + [("設定", [["access_token", ""], ["threads_user_id", ""]])]
    adds = [{"addSheet": {"properties": {"title": t}}} for t, _ in wanted if t not in ids]
    if adds:
        api.batchUpdate(spreadsheetId=sid, body={"requests": adds}).execute()
    for title, header in wanted:
        a1 = api.values().get(spreadsheetId=sid, range=f"{title}!A1").execute().get("values")
        if a1:
            print(f"[SKIP] 「{title}」のA1に、すでに内容がある(書き換えない)")
            continue
        values = header if isinstance(header[0], list) else [header]
        api.values().update(spreadsheetId=sid, range=f"{title}!A1", valueInputOption="RAW",
                            body={"values": values}).execute()
        print(f"[OK] 「{title}」に見出しを書いた")


if __name__ == "__main__":
    main()
