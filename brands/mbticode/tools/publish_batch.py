#!/usr/bin/env python3
"""Threads投稿バッチの「検品→シート投入→読み戻し照合」を1コマンドで行う（2026-09-30）。

Usage:
  python publish_batch.py <batch.txt>            # 確認だけ（検品＋シートとの突き合わせ。書き込まない）
  python publish_batch.py <batch.txt> --apply    # 検品OKなら投入し、読み戻して全行の一致を確認する

手順（cheatsheetのStep 3〜5を1本にしたもの。中身は既存ツールを呼ぶだけ）:
  1. qa_post.py（ERROR 0件が投入の条件。WARNは全文を表示する＝人間が判断する）
  2. threads_txt_to_csv.py → push_threads_queue.py（--apply のときだけ。過去時刻・重複は自動スキップ）
  3. 読み戻し：本文・自己リプライ・URL返信がファイルと一致し、ステータスが空（未投稿）であることを全行で確認

すでにシートにある未投稿の行を「差し替える」ときは、これではなく replace_queue_rows.py を使う。
"""
import argparse
import datetime
import json
import subprocess
import sys
import tempfile
from pathlib import Path

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent.parent.parent  # claude project/
QA = ROOT / "brands" / "tools" / "qa_post.py"

sys.path.insert(0, str(TOOLS))
import replace_queue_rows as rq  # noqa: E402


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def read_sheet():
    cfg = json.loads(rq.CONFIG_FILE.read_text(encoding="utf-8"))
    creds = rq.service_account.Credentials.from_service_account_file(str(rq.CREDS_FILE), scopes=rq.SCOPES)
    svc = rq.build("sheets", "v4", credentials=creds).spreadsheets()
    rows = svc.values().get(spreadsheetId=cfg["spreadsheet_id"], range=f"{cfg['queue_sheet_name']}!A2:K",
                            valueRenderOption="UNFORMATTED_VALUE").execute().get("values", [])
    by = {}
    for r in rows:
        if r and isinstance(r[0], (int, float)):
            by[rq.to_dt(r[0]).replace(second=0, microsecond=0)] = r
    return by


def compare(posts, by):
    """returns (match, mismatch, missing) lists of datetimes"""
    match, mismatch, missing = [], [], []
    for p in posts:
        r = by.get(p["dt"])
        if r is None:
            missing.append(p["dt"])
            continue
        c = lambda i: (r[i] if len(r) > i else "")
        ok = (str(c(1)).strip() == p["body"] and str(c(2)).strip() == p["reply"]
              and str(c(9)).strip() == p["url_reply"] and str(c(5)).strip() == "")
        (match if ok else mismatch).append(p["dt"])
    return match, mismatch, missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("batch")
    ap.add_argument("--apply", action="store_true", help="検品OKなら実際にシートへ投入する")
    ap.add_argument("--year", type=int, default=datetime.date.today().year)
    args = ap.parse_args()
    batch = Path(args.batch).resolve()

    posts = rq.parse_batch(batch.read_text(encoding="utf-8"), args.year)
    if not posts:
        print("[ERROR] 投稿ブロックが読み取れません。")
        sys.exit(2)

    # 1. 検品
    code, out = run([sys.executable, str(QA), str(batch), "--account", "mbticode", "--platform", "threads"])
    lines = [l for l in out.splitlines() if l.startswith(("[ERROR]", "[WARN]", "===", "[INFO]"))]
    print("--- 検品 (qa_post.py) ---")
    for l in lines:
        print(l)
    if code != 0:
        print(f"\n[ABORT] 検品にERRORがあります（exit={code}）。直してから再実行してください。何も書き込んでいません。")
        sys.exit(1)

    # 2. シートとの突き合わせ
    by = read_sheet()
    match, mismatch, missing = compare(posts, by)
    now = datetime.datetime.now()
    past = [p["dt"] for p in posts if p["dt"] < now]
    print(f"\n--- シートとの突き合わせ（{len(posts)}行）---")
    print(f"  シートに無い（新規）: {len(missing)}行 / すでにあって一致: {len(match)}行 / すでにあるが内容が違う: {len(mismatch)}行 / 過去時刻: {len(past)}行")
    for dt in mismatch:
        print(f"  [WARN] {dt:%m/%d %H:%M} はシートに別の内容で存在します（投入されません。差し替えるなら replace_queue_rows.py）")

    if not args.apply:
        print("\n確認のみ。投入するには --apply を付けて再実行してください。")
        return

    if not missing:
        print("\n投入する新規行はありません。")
    else:
        start = min(p["dt"] for p in posts if p["dt"] in missing)
        with tempfile.TemporaryDirectory() as td:
            csv_path = Path(td) / "queue.csv"
            c1, o1 = run([sys.executable, str(TOOLS / "threads_txt_to_csv.py"), f"{start:%Y-%m-%d}",
                          str(csv_path), "--src", str(batch)])
            if c1 != 0 or not csv_path.exists():
                print("[ERROR] CSV変換に失敗:\n" + o1)
                sys.exit(1)
            c2, o2 = run([sys.executable, str(TOOLS / "push_threads_queue.py"), str(csv_path)])
            print("\n--- 投入 (push_threads_queue.py) ---")
            print("\n".join(l for l in o2.splitlines() if l.strip())[:1500])
            if c2 != 0:
                print("[ERROR] 投入に失敗しました。")
                sys.exit(1)

    # 3. 読み戻し照合
    by = read_sheet()
    match, mismatch, missing = compare(posts, by)
    print(f"\n--- 読み戻し照合 ---\n  一致 {len(match)}/{len(posts)}")
    for dt in mismatch:
        print(f"  [NG] {dt:%m/%d %H:%M} 内容が違います")
    for dt in missing:
        print(f"  [NG] {dt:%m/%d %H:%M} シートにありません（過去時刻でスキップされた可能性）")
    if mismatch or missing:
        sys.exit(1)
    print("[OK] すべての行がシートと一致しました。")


if __name__ == "__main__":
    main()
