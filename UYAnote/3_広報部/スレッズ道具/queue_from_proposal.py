#!/usr/bin/env python3
"""スレッズの提案ファイルから、投稿をキュー(スプレッドシート)へ入れる。

順番: (1)qa_post_x.py --threads(ERRORがあれば中止) (2)CSVを作る (3)push_threads_queue.py (4)シートを読み戻して照合

使い方:
  python queue_from_proposal.py <提案.md> [番号 ...] [--dry-run] [--allow-past]

番号: 「## N本目」のN。省略すると全部。
--dry-run: (2)まで(シートに書かない)。

提案ファイルの読み方(3_広報部/スレッズ投稿の型.md の「保存と記録」):
  「## N本目(型・補足)」の次の行「予約日時: YYYY-MM-DD HH:MM」、その下のコードブロックの最初が本文。
  直前の行が「自己返信」で始まるコードブロックは、自己返信(リプライ1)。型は、見出しのかっこの中の「・」より前。
FWとトピックは空で入る(シートで手で入れてよい)。
"""
import csv
import datetime
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

TOOLS_DIR = Path(__file__).resolve().parent
UYANOTE = TOOLS_DIR.parent.parent
QA = UYANOTE / ".claude" / "hooks" / "qa_post_x.py"
PUSH = TOOLS_DIR / "push_threads_queue.py"
CREDS_FILE = TOOLS_DIR / "sheets_service_account.local.json"
CONFIG_FILE = TOOLS_DIR / "sheets_config.json"

FENCE = "`" * 3
HEAD_RE = re.compile(r"^##\s*(\d+)本目(?:[（(]([^）)]*)[）)])?")
DATE_RE = re.compile(r"^予約日時[:：]\s*(\d{4}-\d{2}-\d{2})\s+(\d{1,2}):(\d{2})")


def parse(md):
    posts, cur, lines, i, prev = [], None, md.split("\n"), 0, ""
    while i < len(lines):
        line = lines[i]
        m = HEAD_RE.match(line)
        if m:
            cur = {"n": int(m.group(1)), "type": (m.group(2) or "").split("・")[0].strip(),
                   "dt": "", "body": None, "replies": []}
            posts.append(cur)
            prev = ""
        elif cur is not None:
            d = DATE_RE.match(line.strip())
            if d:
                cur["dt"] = f"{d.group(1)} {int(d.group(2)):02d}:{d.group(3)}"
            if line.startswith(FENCE):
                j, body = i + 1, []
                while j < len(lines) and not lines[j].startswith(FENCE):
                    body.append(lines[j])
                    j += 1
                text = "\n".join(body).strip("\n")
                if prev.startswith("自己返信"):
                    cur["replies"].append(text)
                elif cur["body"] is None:
                    cur["body"] = text
                i = j
                prev = ""
            elif line.strip():
                prev = line.strip()
        i += 1
    return posts


def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    past = "--allow-past" in args
    args = [a for a in args if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(1)
    path = Path(args[0])
    want = {int(a) for a in args[1:]}
    posts = [p for p in parse(path.read_text(encoding="utf-8")) if p["body"] and (not want or p["n"] in want)]
    if not posts:
        print("ERROR: 対象の投稿が見つかりません。")
        sys.exit(1)
    for p in posts:
        if not p["dt"]:
            print(f"ERROR: {p['n']}本目に「予約日時: YYYY-MM-DD HH:MM」の行がありません。")
            sys.exit(1)
    print(f"対象 {len(posts)} 件:")
    for p in posts:
        print(f"  - {p['n']}本目 {p['dt']} {p['type']} (自己返信 {len(p['replies'])}本)")

    print("--- qa_post_x.py --threads ---", flush=True)
    if subprocess.run([sys.executable, str(QA), str(path), "--threads"]).returncode != 0:
        print("\n[ABORT] 機械チェックのERRORを直してから、もう一度実行してください。")
        sys.exit(1)

    csv_path = Path(tempfile.gettempdir()) / "queue_from_proposal.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["投稿日時", "本文", "リプライ1", "リプライ2", "リプライ3", "リプライ4", "型", "FW", "トピック"])
        for p in posts:
            reps = (p["replies"] + ["", "", "", ""])[:4]
            w.writerow([p["dt"], p["body"], *reps, p["type"], "", ""])
    print(f"\n[OK] CSV: {csv_path}")
    if dry:
        print("[DRY-RUN] ここで停止。シートには書きません。")
        return

    cmd = [sys.executable, str(PUSH), str(csv_path)] + (["--allow-past"] if past else [])
    if subprocess.run(cmd).returncode != 0:
        print("[ABORT] push_threads_queue.py が失敗しました。")
        sys.exit(1)

    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    creds = service_account.Credentials.from_service_account_file(
        str(CREDS_FILE), scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    rows = build("sheets", "v4", credentials=creds).spreadsheets().values().get(
        spreadsheetId=cfg["spreadsheet_id"], range=f"{cfg['queue_sheet_name']}!A2:O",
        valueRenderOption="UNFORMATTED_VALUE").execute().get("values", [])
    epoch = datetime.datetime(1899, 12, 30)
    by_key = {}
    for r in rows:
        if r and isinstance(r[0], (int, float)):
            dt = epoch + datetime.timedelta(days=r[0])
            by_key[dt.strftime("%Y-%m-%d %H:%M")] = r
    bad = 0
    for p in posts:
        r = by_key.get(p["dt"])
        if r is None:
            print(f"[NG] シートに見つからない: {p['dt']}")
            bad += 1
            continue
        body_ok = (r[1] if len(r) > 1 else "").strip() == p["body"].strip()
        reps = (p["replies"] + [""] * 4)[:4]
        reps_ok = all(((r[2 + i] if len(r) > 2 + i else "") or "").strip() == reps[i].strip() for i in range(4))
        status = r[8] if len(r) > 8 else ""
        print(f"[{'OK' if body_ok and reps_ok else 'NG'}] {p['dt']} 本文{'一致' if body_ok else '不一致'}・自己返信{'一致' if reps_ok else '不一致'}・状態「{status}」")
        bad += not (body_ok and reps_ok)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
