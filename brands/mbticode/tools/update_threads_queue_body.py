#!/usr/bin/env python3
"""Update existing Threads queue rows' body text (column B) and, when present,
self-reply text (column C) in place, matched by 投稿日時.

Unlike push_threads_queue.py (append + duplicate-skip), this OVERWRITES the 本文/
リプライ本文 cells of rows that already exist in the sheet. Use when a post was
already pushed to the queue but the local posts_threads.txt text was revised
afterward (e.g. wording fixes) and the post has not gone out yet.

Usage:
  python update_threads_queue_body.py <posts_threads.txt> <header-prefix> [<header-prefix> ...]

<header-prefix> matches against the 【...】 header text, e.g. "7/30" or "7/30 08:00".
Only posts matching a given prefix are updated. Rows with a non-empty ステータス
(already posted) are skipped and reported, never overwritten.

自己リプライ（続き型／URL事後型等の場合のみ）: 本文の閉じ`----`の後・次の見出しの前に
書かれた「自己リプライ（〜）：」行を検出し、ラベル接頭辞を取り除いた本文をリプライ列
（column C）へ書き込む。リプライ行が存在しない投稿はcolumn Cを触らない
（2026-07-30追加。以前はcolumn Bのみ対応で、リプライ文言だけ変更した際にシート側が
古いまま取り残される問題があった）。

型（column D）・FW（column E）も本文と同時に上書きする（2026-08-02追加。以前はcolumn B/Cのみ
更新しD/Eが更新前のまま残り、本文の内容とシート上のFWラベルが食い違う不具合があった）。
型はリプライの有無・URL含有で推定（リプライなし=完結型／URLありのリプライ=URL事後型／
それ以外=続き型）、FWは見出し内の「／」以降のラベルをそのまま使う。
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
REPLY_LABEL_RE = re.compile(r"^自己リプライ[^：]*：\s*")


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
                main_body = re.split(r"^===+\s*$", body, flags=re.M)[0].strip()
                # 本文の閉じ`----`の後・次の見出しの前にある自己リプライ行を拾う
                reply = ""
                end = k
                if k < len(lines) and SEP_RE.match(lines[k]):
                    m2 = k + 1
                    reply_lines = []
                    while m2 < len(lines) and not HEADER_RE.match(lines[m2]):
                        reply_lines.append(lines[m2])
                        m2 += 1
                    reply_raw = "\n".join(reply_lines).strip()
                    reply = REPLY_LABEL_RE.sub("", reply_raw, count=1).strip()
                    end = m2
                label = m.group(2)
                if reply:
                    qtype = "URL事後型" if ("http" in reply or "→" in reply) else "続き型"
                else:
                    qtype = "完結型"
                fw = label.rsplit("／", 1)[-1].strip() if "／" in label else "タイプなし"
                posts.append({
                    "header": header, "body": main_body, "reply": reply,
                    "qtype": qtype, "fw": fw,
                })
                i = end
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
        targets[key] = {
            "body": p["body"], "reply": p["reply"],
            "qtype": p["qtype"], "fw": p["fw"],
        }

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
    updated, updated_reply, skipped_posted, not_found = [], [], [], list(targets.keys())
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
            "values": [[targets[key]["body"]]],
        })
        data.append({
            "range": f"{sheet_name}!D{idx}:E{idx}",
            "values": [[targets[key]["qtype"], targets[key]["fw"]]],
        })
        updated.append(key)
        if targets[key]["reply"]:
            data.append({
                "range": f"{sheet_name}!C{idx}",
                "values": [[targets[key]["reply"]]],
            })
            updated_reply.append(key)
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
    if updated_reply:
        print(f"[OK] うち {len(updated_reply)} 件は自己リプライも上書きしました:")
        for k in updated_reply:
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
