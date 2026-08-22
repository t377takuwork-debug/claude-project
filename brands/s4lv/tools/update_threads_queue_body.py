#!/usr/bin/env python3
"""Update existing Threads queue rows' body text (column B) and, when present,
chained self-reply text (columns C-F, up to 4) in place, matched by 投稿日時.

Unlike push_threads_queue.py (append + duplicate-skip), this OVERWRITES the 本文/
リプライ本文 cells of rows that already exist in the sheet. Use when a post was
already pushed to the queue but the local posts_threads.txt text was revised
afterward (e.g. wording fixes) and the post has not gone out yet.

Usage:
  python update_threads_queue_body.py <posts_threads.txt> <header-prefix> [<header-prefix> ...]

<header-prefix> matches against the 【...】 header text, e.g. "7/30" or "7/30 08:00".
Only posts matching a given prefix are updated. Rows with a non-empty ステータス
(already posted) are skipped and reported, never overwritten.

自己リプライ（2026-08-23: 単発1本から最大4本の連鎖対応へ拡張）: 本文の閉じ`----`の後・
次の見出しの前に書かれた「自己リプライ（〜）：」形式の行を検出する。複数のリプライを
連鎖させる場合は、それぞれ新しい「自己リプライN（〜）：」行から始め、空行で区切って
並べる（本文内の改行は空行で表現し、リプライ同士の区切りも空行のため、1つのリプライを
複数段落にしたい場合は同じリプライブロック内で改行のみ・空行を挟まないこと）。検出した
順にリプライ1〜4（列C〜F）へ書き込む。5本目以降は無視する。マッチした投稿は、リプライが
1〜3本しかない場合も残りの列を空で明示的に上書きする（古いリプライが残留しないように）。

型（2026-08-04追加）: 見出しの「型①」「型②」「型③」を検出し、シート側の列Gと食い違って
いれば同期する。FW（列H・短縮トピックラベル）は見出しの説明的なタイトルとは別物として
運用しているため対象外（トピック自体を差し替えた場合は列Hを手動更新すること）。
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
TYPE_RE = re.compile(r"^(型[①②③])")


def parse_posts(text):
    posts = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = HEADER_RE.match(lines[i])
        if m and "URL候補" not in m.group(1):
            header = m.group(1) + m.group(2)
            type_match = TYPE_RE.match(m.group(2).strip())
            type_label = type_match.group(1) if type_match else ""
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
                # 本文の閉じ`----`の直後（間に空行を挟まない）に「自己リプライ」で始まる行が
                # あるときだけ、そこから次の見出しの手前までを自己リプライ連鎖として拾う。
                # 空行はリプライ同士の区切りとして扱う（最大4本、5本目以降は無視）。
                # そうでない場合（末尾の「読者リプライへの返信」ログ等）は絶対に巻き込まない。
                replies = []
                end = k
                if k < len(lines) and SEP_RE.match(lines[k]):
                    m2 = k + 1
                    if m2 < len(lines) and lines[m2].strip().startswith("自己リプライ"):
                        current_lines = []
                        while m2 < len(lines) and not HEADER_RE.match(lines[m2]):
                            line = lines[m2]
                            if line.strip() == "":
                                if current_lines:
                                    raw = "\n".join(current_lines).strip()
                                    replies.append(REPLY_LABEL_RE.sub("", raw, count=1).strip())
                                    current_lines = []
                            else:
                                current_lines.append(line)
                            m2 += 1
                        if current_lines:
                            raw = "\n".join(current_lines).strip()
                            replies.append(REPLY_LABEL_RE.sub("", raw, count=1).strip())
                        replies = replies[:4]
                        end = m2
                    else:
                        end = m2
                posts.append({"header": header, "body": main_body, "replies": replies, "type": type_label})
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
        targets[key] = {"body": p["body"], "replies": p["replies"], "type": p["type"]}

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
        range=f"{sheet_name}!A2:N",
        valueRenderOption="UNFORMATTED_VALUE",
    ).execute().get("values", [])
    # 列: A投稿日時 B本文 C-Fリプライ1-4本文 G型 HFW Iステータス J投稿ID K-Nリプライ投稿ID1-4
    # NOTE: FW（列H・トピック短縮ラベル）はposts_threads.txtの見出し文言（人間向けの
    # 説明的なタイトル）とは別物として運用されているため自動同期しない。トピックその
    # ものを差し替えた場合は列Hを手動で更新すること。
    REPLY_COLS = ["C", "D", "E", "F"]

    EPOCH = datetime.datetime(1899, 12, 30)

    def serial_to_dt(serial):
        return EPOCH + datetime.timedelta(days=serial)

    data = []
    updated, updated_reply, updated_type, skipped_posted, not_found = [], [], [], [], list(targets.keys())
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
        status = r[8] if len(r) > 8 else ""
        if status:
            skipped_posted.append((key, status))
            if key in not_found:
                not_found.remove(key)
            continue
        data.append({
            "range": f"{sheet_name}!B{idx}",
            "values": [[targets[key]["body"]]],
        })
        updated.append(key)
        # リプライ1〜4を明示的に全列上書きする（古いリプライの残留を防ぐため、
        # 空スロットも""で上書きする）
        replies = targets[key]["replies"]
        padded_replies = replies + [""] * (4 - len(replies))
        for col, text in zip(REPLY_COLS, padded_replies):
            data.append({
                "range": f"{sheet_name}!{col}{idx}",
                "values": [[text]],
            })
        if replies:
            updated_reply.append(key)
        current_type = r[6] if len(r) > 6 else ""
        if targets[key]["type"] and targets[key]["type"] != current_type:
            data.append({
                "range": f"{sheet_name}!G{idx}",
                "values": [[targets[key]["type"]]],
            })
            updated_type.append(key)
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
    if updated_type:
        print(f"[OK] うち {len(updated_type)} 件は型（列D）も見出しと同期しました:")
        for k in updated_type:
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
