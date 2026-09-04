#!/usr/bin/env python3
"""One-shot: take posts from posts_threads.txt and put them in the Threads queue.

Runs, in order:
  1. qa_post.py on the selected blocks (aborts if ERROR > 0)
  2. builds the push CSV (投稿日時,本文,リプライ1-4,型,FW) from the blocks
  3. push_threads_queue.py <csv>          (append + duplicate-skip)
  4. verify_queue_matches_file.py         (sheet vs file consistency)

This replaces the manual "write temp file -> qa -> hand-build CSV -> push -> verify"
dance. For UPDATING rows that were already pushed, use update_threads_queue_body.py.

Usage:
  python queue_from_posts.py <posts_threads.txt> <header-prefix> [<header-prefix> ...] [--dry-run] [--allow-past]

<header-prefix> matches the 【...】 header text, e.g. "9/5" or "9/5 07:30".
--dry-run : stop after step 2, print the CSV path and QA result. No sheet writes.
--allow-past : forwarded to push_threads_queue.py (queue slots already in the past).

FW (column H, short topic label) is left blank — set it in the sheet by hand if wanted.
型 is taken from the header text between 】 and the first ／ (e.g. 型・思想 / AI実働).
"""
import csv
import datetime
import re
import subprocess
import sys
import tempfile
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

TOOLS_DIR = Path(__file__).resolve().parent
QA_POST = TOOLS_DIR.parent.parent / "tools" / "qa_post.py"
PUSH = TOOLS_DIR / "push_threads_queue.py"
VERIFY = TOOLS_DIR / "verify_queue_matches_file.py"

HEADER_RE = re.compile(r"^【(.+?)】(.*)$")
SEP_RE = re.compile(r"^-{10,}\s*$")
DATETIME_RE = re.compile(r"(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{2})")
REPLY_LABEL_RE = re.compile(r"^自己リプライ[^：]*：\s*")


def infer_year(month, day, now):
    dt = datetime.datetime(now.year, month, day)
    return now.year + 1 if (dt - now).days < -30 else now.year


def parse_blocks(text):
    """Yield {header, dt_str, body, replies[], type} for each 【header】 + ---- block."""
    lines = text.splitlines()
    now = datetime.datetime.now()
    i = 0
    while i < len(lines):
        m = HEADER_RE.match(lines[i])
        if not (m and "URL候補" not in m.group(1)):
            i += 1
            continue
        header = m.group(1) + m.group(2)
        after = m.group(2).strip()
        type_label = after.split("／")[0].split("/")[0].strip() if after else ""
        j = i + 1
        while j < len(lines) and not SEP_RE.match(lines[j]):
            if HEADER_RE.match(lines[j]):
                break
            j += 1
        if not (j < len(lines) and SEP_RE.match(lines[j])):
            i += 1
            continue
        k = j + 1
        body_lines = []
        while k < len(lines) and not SEP_RE.match(lines[k]):
            body_lines.append(lines[k])
            k += 1
        body = "\n".join(body_lines).strip()
        replies = []
        end = k
        if k < len(lines) and SEP_RE.match(lines[k]):
            m2 = k + 1
            if m2 < len(lines) and lines[m2].strip().startswith("自己リプライ"):
                cur = []
                while m2 < len(lines) and not HEADER_RE.match(lines[m2]):
                    if lines[m2].strip() == "":
                        if cur:
                            replies.append(REPLY_LABEL_RE.sub("", "\n".join(cur).strip(), count=1).strip())
                            cur = []
                    else:
                        cur.append(lines[m2])
                    m2 += 1
                if cur:
                    replies.append(REPLY_LABEL_RE.sub("", "\n".join(cur).strip(), count=1).strip())
                replies = replies[:4]
                end = m2
            else:
                end = m2
        dm = DATETIME_RE.search(header)
        dt_str = ""
        if dm:
            mo, da, hh, mm = (int(x) for x in dm.groups())
            yr = infer_year(mo, da, now)
            dt_str = f"{yr:04d}-{mo:02d}-{da:02d} {hh:02d}:{mm:02d}"
        yield {"header": header, "dt_str": dt_str, "body": body,
               "replies": replies, "type": type_label}
        i = end


def main():
    args = [a for a in sys.argv[1:]]
    dry_run = "--dry-run" in args
    allow_past = "--allow-past" in args
    args = [a for a in args if not a.startswith("--")]
    if len(args) < 2:
        print("Usage: python queue_from_posts.py <posts_threads.txt> <header-prefix> [...] [--dry-run] [--allow-past]")
        sys.exit(1)
    txt_path = Path(args[0])
    prefixes = args[1:]
    if not txt_path.exists():
        print(f"ERROR: file not found: {txt_path}")
        sys.exit(1)

    blocks = [b for b in parse_blocks(txt_path.read_text(encoding="utf-8"))
              if any(b["header"].startswith(p) for p in prefixes)]
    if not blocks:
        print("ERROR: 指定prefixに一致する投稿がありません。")
        sys.exit(1)
    for b in blocks:
        if not b["dt_str"]:
            print(f"ERROR: 投稿日時をヘッダーから取れません: 【{b['header']}】")
            sys.exit(1)

    print(f"対象 {len(blocks)} 件:")
    for b in blocks:
        print(f"  - {b['dt_str']}  {b['type']}  (自己リプライ {len(b['replies'])}本)")
    print("--- qa_post.py ---", flush=True)

    # 1. QA
    tmp_qa = Path(tempfile.gettempdir()) / "queue_from_posts_qa.txt"
    D = "-" * 32
    parts = ["s4lv Threads QA (queue_from_posts)\n" + "=" * 40 + "\n"]
    for b in blocks:
        blk = f"\n【{b['header']}】\n{D}\n{b['body']}\n{D}\n"
        for n, r in enumerate(b["replies"], 1):
            tag = "自己リプライ：" if len(b["replies"]) == 1 else f"自己リプライ{n}："
            blk += f"{tag}{r}\n\n"
        parts.append(blk.rstrip() + "\n")
    tmp_qa.write_text("".join(parts), encoding="utf-8")
    qa = subprocess.run([sys.executable, str(QA_POST), str(tmp_qa),
                         "--account", "s4lv", "--platform", "threads"])
    if qa.returncode != 0:
        print("\n[ABORT] qa_post.py が ERROR を検出しました。修正して再実行してください。")
        sys.exit(1)

    # 2. build CSV
    csv_path = Path(tempfile.gettempdir()) / "queue_from_posts.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["投稿日時", "本文", "リプライ1", "リプライ2", "リプライ3", "リプライ4", "型", "FW"])
        for b in blocks:
            reps = (b["replies"] + ["", "", "", ""])[:4]
            w.writerow([b["dt_str"], b["body"], *reps, b["type"], ""])
    print(f"\n[OK] CSV: {csv_path}")

    if dry_run:
        print("[DRY-RUN] ここで停止。シートへの書き込みは行いません。")
        return

    # 3. push
    push_cmd = [sys.executable, str(PUSH), str(csv_path)]
    if allow_past:
        push_cmd.append("--allow-past")
    if subprocess.run(push_cmd).returncode != 0:
        print("[ABORT] push_threads_queue.py が失敗しました。")
        sys.exit(1)

    # 4. verify
    subprocess.run([sys.executable, str(VERIFY), str(txt_path),
                    *[b["header"][:DATETIME_RE.search(b["header"]).end()] for b in blocks]])


if __name__ == "__main__":
    main()
