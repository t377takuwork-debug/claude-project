#!/usr/bin/env python3
"""Read-only verification: compare the live Threads queue sheet against
posts_threads.txt for a given date-prefix range, and report any mismatches
in body text, self-reply text, or type.

Usage:
  python verify_queue_matches_file.py <posts_threads.txt> <header-prefix> [<header-prefix> ...]

Does not write anything. Exit code 0 always; prints [OK]/[MISMATCH]/[NOT FOUND IN SHEET]
per targeted post.
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
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

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
                # 本文の閉じ`----`の直後（間に空行を挟まない）に「自己リプライ」で始まる行が
                # あるときだけ自己リプライ連鎖として拾う（末尾の読者リプライログ等を巻き込まない）。
                # 空行はリプライ同士の区切り（最大4本、2026-08-23連鎖対応）。
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
                posts.append({"header": header, "body": body, "replies": replies, "type": type_label})
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
        print("Usage: python verify_queue_matches_file.py <posts_threads.txt> <header-prefix> [...]")
        sys.exit(1)
    txt_path = Path(sys.argv[1])
    prefixes = sys.argv[2:]

    posts = parse_posts(txt_path.read_text(encoding="utf-8"))
    now = datetime.datetime.now()
    targets = {}
    order = []
    for p in posts:
        if not any(p["header"].startswith(pref) for pref in prefixes):
            continue
        m = DATETIME_RE.match(p["header"])
        if not m:
            continue
        month, day, hh, mm = (int(x) for x in m.groups())
        year = infer_year(month, day, now)
        key = f"{year:04d}-{month:02d}-{day:02d} {hh}:{mm:02d}"
        targets[key] = {"body": p["body"], "replies": p["replies"], "type": p["type"], "header": p["header"]}
        order.append(key)

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

    EPOCH = datetime.datetime(1899, 12, 30)

    def serial_to_dt(serial):
        return EPOCH + datetime.timedelta(days=serial)

    sheet_by_key = {}
    for r in rows:
        if not r:
            continue
        serial = r[0]
        if not isinstance(serial, (int, float)):
            continue
        dt = serial_to_dt(serial)
        key = f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d} {dt.hour}:{dt.minute:02d}"
        sheet_by_key[key] = {
            "body": r[1] if len(r) > 1 else "",
            "replies": [r[i] if len(r) > i else "" for i in range(2, 6)],
            "type": r[6] if len(r) > 6 else "",
            "status": r[8] if len(r) > 8 else "",
        }

    n_ok = n_mismatch = n_missing = 0
    for key in order:
        t = targets[key]
        s = sheet_by_key.get(key)
        if s is None:
            print(f"[NOT FOUND IN SHEET] {key} ({t['header']})")
            n_missing += 1
            continue
        diffs = []
        if s["body"].strip() != t["body"].strip():
            diffs.append("本文")
        t_replies = (t["replies"] + [""] * 4)[:4]
        s_replies = (s["replies"] + [""] * 4)[:4]
        if [x.strip() for x in s_replies] != [(x or "").strip() for x in t_replies]:
            diffs.append("リプライ")
        if t["type"] and s["type"] != t["type"]:
            diffs.append("型")
        if diffs:
            print(f"[MISMATCH] {key} ({t['header']}) — 差異: {', '.join(diffs)}")
            if "本文" in diffs:
                print(f"    file : {t['body'][:80]!r}")
                print(f"    sheet: {s['body'][:80]!r}")
            n_mismatch += 1
        else:
            print(f"[OK] {key} ({t['header']})")
            n_ok += 1

    print(f"\n=== 結果: OK {n_ok} / MISMATCH {n_mismatch} / NOT FOUND {n_missing} ===")


if __name__ == "__main__":
    main()
