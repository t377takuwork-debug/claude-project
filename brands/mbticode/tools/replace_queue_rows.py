#!/usr/bin/env python3
"""Safely REPLACE not-yet-posted rows of the Threads queue with a new batch file.

Usage:
  python replace_queue_rows.py <batch.txt>            # dry-run (default): show what would change, write nothing
  python replace_queue_rows.py <batch.txt> --apply    # back up the old rows, then overwrite

Why this exists (2026-09-29): update_threads_queue_body.py leaves the OLD self-reply (column C) when the new
post has none, cannot touch the URL self-reply (column J), and infers the 型 label. Replacing a whole batch with it
would publish stale replies / stale URLs. This tool always rewrites B, C, D, E and J for each target row
(empty string when the new post has no reply), so nothing stale survives.

Safety rules (fail closed — any violation aborts the whole run, nothing is written):
  - every batch post must match exactly one sheet row by 投稿日時
  - the row's ステータス(F), 投稿ID(G), リプライ投稿ID(H), URL自己リプライ投稿ID(K) must all be empty (not posted yet)
  - rows less than 60 minutes from now are refused (--allow-soon to override)
  - on --apply the old B..E and J values are saved to posts/archive/queue_backup_<timestamp>.json first
  - after writing, the rows are re-read and compared with what was intended

Batch file format: same as posts_threads.txt / _batch_*.txt
  【M/D HH:MM】型ラベル／FW  →  ---- 本文 ----  →  自己リプライ（…）：… / 自己リプライ2（…）：…（URL）
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
HEAD_RE = re.compile(r"^【(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{2})】(.*)$")
SEP_RE = re.compile(r"^-{10,}\s*$")
REPLY_PREFIX_RE = re.compile(r"^自己リプライ[^：]*：\s*")
REPLY2_MARKER_RE = re.compile(r"^自己リプライ2[^：]*：")
REPLY2_PREFIX_RE = re.compile(r"^自己リプライ2[^：]*：\s*")


def parse_batch(text, year):
    lines = text.split("\n")
    posts, i = [], 0
    while i < len(lines):
        m = HEAD_RE.match(lines[i])
        if not m:
            i += 1
            continue
        mo, da, hh, mm, rest = m.groups()
        j = i + 1
        if j >= len(lines) or not SEP_RE.match(lines[j]):
            i += 1
            continue
        k, body = j + 1, []
        while k < len(lines) and not SEP_RE.match(lines[k]):
            body.append(lines[k])
            k += 1
        reply_lines, r = [], k + 1
        while r < len(lines) and not HEAD_RE.match(lines[r]):
            reply_lines.append(lines[r])
            r += 1
        split_idx = next((n for n, ln in enumerate(reply_lines) if REPLY2_MARKER_RE.match(ln.strip())), None)
        if split_idx is not None:
            reply = "\n".join(reply_lines[:split_idx]).strip()
            url_reply = REPLY2_PREFIX_RE.sub("", "\n".join(reply_lines[split_idx:]).strip(), count=1).strip()
        else:
            reply, url_reply = "\n".join(reply_lines).strip(), ""
        reply = REPLY_PREFIX_RE.sub("", reply, count=1).strip()
        # 続き型でない・URL事後型（1本目の返信にURL）の場合は、1本目の返信がそのままC列になる（従来どおり）
        typ, _, fw = rest.partition("／")
        dt = datetime.datetime(year, int(mo), int(da), int(hh), int(mm))
        posts.append({"dt": dt, "body": "\n".join(body).strip(), "reply": reply, "url_reply": url_reply,
                      "type": typ.strip(), "fw": fw.strip()})
        i = r
    return posts


def to_dt(serial):
    return EPOCH + datetime.timedelta(days=serial)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("batch")
    ap.add_argument("--apply", action="store_true", help="実際に書き込む（省略時は確認表示だけ）")
    ap.add_argument("--allow-soon", action="store_true", help="60分以内に投稿される行の差し替えを許可する")
    ap.add_argument("--year", type=int, default=datetime.date.today().year)
    args = ap.parse_args()

    posts = parse_batch(Path(args.batch).read_text(encoding="utf-8"), args.year)
    if not posts:
        print("[ERROR] 投稿ブロックが読み取れません。")
        sys.exit(2)

    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    sid, sheet = config["spreadsheet_id"], config["queue_sheet_name"]
    creds = service_account.Credentials.from_service_account_file(str(CREDS_FILE), scopes=SCOPES)
    svc = build("sheets", "v4", credentials=creds).spreadsheets()
    rows = svc.values().get(spreadsheetId=sid, range=f"{sheet}!A2:K", valueRenderOption="UNFORMATTED_VALUE").execute().get("values", [])

    def cell(r, i):
        return r[i] if len(r) > i else ""

    by_dt = {}
    for idx, r in enumerate(rows, start=2):
        if r and isinstance(cell(r, 0), (int, float)):
            key = to_dt(cell(r, 0)).replace(second=0, microsecond=0)
            by_dt.setdefault(key, []).append(idx)

    now = datetime.datetime.now()
    problems, plan = [], []
    for p in posts:
        hits = by_dt.get(p["dt"], [])
        if len(hits) != 1:
            problems.append(f"{p['dt']:%m/%d %H:%M}：シートで一致する行が{len(hits)}件（1件のみ許可）")
            continue
        idx = hits[0]
        r = rows[idx - 2]
        posted = {"ステータス": cell(r, 5), "投稿ID": cell(r, 6), "リプライ投稿ID": cell(r, 7), "URL返信ID": cell(r, 10)}
        if any(str(v).strip() for v in posted.values()):
            problems.append(f"{p['dt']:%m/%d %H:%M}：投稿済み・処理済みの印がある行は差し替えません {posted}")
            continue
        if (p["dt"] - now) < datetime.timedelta(minutes=60) and not args.allow_soon:
            problems.append(f"{p['dt']:%m/%d %H:%M}：投稿まで60分未満の行は差し替えません（--allow-soonで許可）")
            continue
        plan.append({"row": idx, "post": p,
                     "old": {"B": cell(r, 1), "C": cell(r, 2), "D": cell(r, 3), "E": cell(r, 4), "J": cell(r, 9)}})
    if problems:
        print("[ABORT] 次の問題があるため、何も書き込みません：")
        for m in problems:
            print("  -", m)
        sys.exit(1)

    print(f"=== {'適用' if args.apply else '確認（書き込みなし）'}：{len(plan)}行 ===")
    for it in plan:
        p, o = it["post"], it["old"]
        chg = []
        if str(o["C"]).strip() and not p["reply"]:
            chg.append("古い自己リプライ(C)を消す")
        if str(o["J"]).strip() and not p["url_reply"]:
            chg.append("古いURL返信(J)を消す")
        if p["reply"]:
            chg.append(f"自己リプライ{len(p['reply'])}字")
        if p["url_reply"]:
            chg.append("URL返信あり")
        print(f"行{it['row']} {p['dt']:%m/%d %H:%M} 旧[{str(o['D'])[:18]}／{str(o['E'])[:14]}] → 新[{p['type'][:22]}／{p['fw'][:14]}]"
              f"  本文{len(p['body'])}字  " + "・".join(chg))

    if not args.apply:
        print("\n書き込むには --apply を付けて再実行してください（実行前に、旧内容を posts/archive/ にバックアップします）。")
        return

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    bpath = BACKUP_DIR / f"queue_backup_{now:%Y%m%d_%H%M%S}.json"
    bpath.write_text(json.dumps([{"row": it["row"], "datetime": f"{it['post']['dt']:%Y-%m-%d %H:%M}", **it["old"]} for it in plan],
                                ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[OK] 旧内容をバックアップ：{bpath}")

    data = []
    for it in plan:
        r, p = it["row"], it["post"]
        data += [{"range": f"{sheet}!B{r}", "values": [[p["body"]]]},
                 {"range": f"{sheet}!C{r}", "values": [[p["reply"]]]},
                 {"range": f"{sheet}!D{r}:E{r}", "values": [[p["type"], p["fw"]]]},
                 {"range": f"{sheet}!J{r}", "values": [[p["url_reply"]]]}]
    svc.values().batchUpdate(spreadsheetId=sid, body={"valueInputOption": "RAW", "data": data}).execute()

    # 検証：読み直して、意図した内容と一致するか確認する
    chk = svc.values().get(spreadsheetId=sid, range=f"{sheet}!A2:K", valueRenderOption="UNFORMATTED_VALUE").execute().get("values", [])
    bad = []
    for it in plan:
        r, p = it["row"], it["post"]
        row = chk[r - 2]
        got = (cell(row, 1), cell(row, 2), cell(row, 3), cell(row, 4), cell(row, 9))
        want = (p["body"], p["reply"], p["type"], p["fw"], p["url_reply"])
        if got != want:
            bad.append(f"行{r} {p['dt']:%m/%d %H:%M}")
    if bad:
        print("[ERROR] 書き込み後の検証で不一致：", bad)
        sys.exit(1)
    print(f"[OK] {len(plan)}行を書き込み、読み直して一致を確認しました。")


if __name__ == "__main__":
    main()
