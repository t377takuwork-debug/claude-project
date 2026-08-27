#!/usr/bin/env python3
"""Convert posts_threads.txt blocks into the CSV that push_threads_queue.py consumes.

Usage:
  python tools/threads_txt_to_csv.py 2026-08-29                       # -> tools/_queue_from_txt.csv
  python tools/threads_txt_to_csv.py 2026-08-29 tools/mybatch.csv
  python tools/threads_txt_to_csv.py 8/29 --year 2026

Parses `posts/posts_threads.txt` blocks whose header date is on/after <since>,
strips the `自己リプライ（…）：` annotation prefix (that line is a file note, not
part of the posted text), keeps `→ URL` lines in the reply, and writes columns
  投稿日時,本文,リプライ本文,型,FW
Then:  python tools/push_threads_queue.py <that csv>

Replaces the ~40-line bespoke parser that used to be written inline for every batch.
"""
import argparse
import csv
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

TOOLS_DIR = Path(__file__).resolve().parent
POSTS_FILE = TOOLS_DIR.parent / "posts" / "posts_threads.txt"
HEAD_RE = re.compile(r"^【(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{2})】(.*)$")
SEP_RE = re.compile(r"^-{10,}\s*$")
REPLY_PREFIX_RE = re.compile(r"^自己リプライ[^：]*：\s*")


def parse_since(s):
    s = s.strip()
    if "-" in s:
        y, m, d = (int(x) for x in s.split("-"))
        return y, m, d
    m, d = (int(x) for x in s.split("/"))
    return None, m, d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("since", help="開始日 YYYY-MM-DD または M/D")
    ap.add_argument("out", nargs="?", default=str(TOOLS_DIR / "_queue_from_txt.csv"),
                    help="出力CSVパス（省略時 tools/_queue_from_txt.csv）")
    ap.add_argument("--year", type=int, help="M/D 指定時の基準年（省略時は since の年、なければ今年）")
    args = ap.parse_args()

    since_y, since_m, since_d = parse_since(args.since)
    base_year = args.year or since_y
    if base_year is None:
        import datetime
        base_year = datetime.date.today().year

    if not POSTS_FILE.exists():
        print(f"ERROR: {POSTS_FILE} が見つかりません。")
        sys.exit(1)

    lines = POSTS_FILE.read_text(encoding="utf-8").split("\n")
    rows = []
    i = 0
    while i < len(lines):
        m = HEAD_RE.match(lines[i])
        if not m:
            i += 1
            continue
        mo, da, hh, mm, rest = m.groups()
        mo, da, hh = int(mo), int(da), int(hh)
        # year wrap: a month well before the since-month means next year
        year = base_year + 1 if (since_m - mo) > 6 else base_year
        dt = f"{year:04d}-{mo:02d}-{da:02d} {hh:02d}:{mm}"
        typ, _, fw = rest.partition("／")

        j = i + 1
        if j >= len(lines) or not SEP_RE.match(lines[j]):
            i += 1
            continue
        k = j + 1
        body = []
        while k < len(lines) and not SEP_RE.match(lines[k]):
            body.append(lines[k])
            k += 1
        reply_lines = []
        r = k + 1
        while r < len(lines) and not HEAD_RE.match(lines[r]):
            reply_lines.append(lines[r])
            r += 1
        body_txt = "\n".join(body).strip()
        reply_txt = "\n".join(reply_lines).strip()
        reply_txt = REPLY_PREFIX_RE.sub("", reply_txt, count=1).strip()

        keep = (mo, da) >= (since_m, since_d) or (since_m - mo) > 6
        if keep:
            rows.append({"dt": dt, "body": body_txt, "reply": reply_txt,
                         "type": typ.strip(), "fw": fw.strip()})
        i = r

    if not rows:
        print(f"[INFO] {args.since} 以降の投稿ブロックが posts_threads.txt に見つかりません。")
        sys.exit(0)

    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["投稿日時", "本文", "リプライ本文", "型", "FW"])
        for r in rows:
            w.writerow([r["dt"], r["body"], r["reply"], r["type"], r["fw"]])

    empties = [r["dt"] for r in rows
              if not r["body"] or ("続き型" in r["type"] or "URL事後型" in r["type"] or "リスト型" in r["type"]) and not r["reply"]]
    print(f"[OK] {len(rows)} 行 → {args.out}")
    for r in rows:
        mark = " (本文/リプライ欠落?)" if r["dt"] in empties else ""
        print(f"  {r['dt']}  {r['type']}／{r['fw']}  reply={len(r['reply'])}字{mark}")
    if empties:
        print(f"\n[WARN] {len(empties)} 行で本文またはリプライが空です。確認してください。")
    print(f"\n次: python tools/push_threads_queue.py {args.out}")


if __name__ == "__main__":
    main()
