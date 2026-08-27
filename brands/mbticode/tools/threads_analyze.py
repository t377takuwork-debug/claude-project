#!/usr/bin/env python3
"""Standard weekly-analysis breakdown for MBTICODE Threads posts.

Usage:
  python tools/threads_analyze.py                # window = since the last analysis
  python tools/threads_analyze.py --since 2026-08-14
  python tools/threads_analyze.py --out tools/_wk.txt
  python tools/threads_analyze.py --commit       # also stamp threads_analysis_log.json to today

Reads tools/_synced_observation_data.json (per-post insight rows synced from the
Google Sheet) and prints the fixed table the weekly analysis needs: n, Views
stats, outliers, 構造型別 / FW別 / トーン型別 / 冒頭フック別 breakdowns (with and
without outliers), external-reply total, and per-day counts.

This script does the arithmetic only. The 観測 / 反映 / 未解決 interpretation is
still written by hand into threads_insights_notes.md — the judgment stays with a
person, the number-crunching does not have to be re-derived each week.
"""
import argparse
import datetime
import json
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

TOOLS_DIR = Path(__file__).resolve().parent
DATA_FILE = TOOLS_DIR / "_synced_observation_data.json"
NOTES_FILE = TOOLS_DIR.parent / "threads_insights_notes.md"
LOG_FILE = TOOLS_DIR / "threads_analysis_log.json"
HEADING_RE = re.compile(r"^##\s*(\d{4}-\d{2}-\d{2})\s*週次分析", re.MULTILINE)
OUTLIER_MIN_VIEWS = 1000


def last_analysis_date():
    if not NOTES_FILE.exists():
        return None
    dates = sorted(HEADING_RE.findall(NOTES_FILE.read_text(encoding="utf-8")))
    return dates[-1] if dates else None


def norm_struct(t):
    if "リスト" in t:
        return "リスト型"
    for k in ("続き型", "URL事後型", "完結型"):
        if k in t:
            return k
    return t or "(型不明)"


def norm_tone(t):
    for k in ("型C'", "型C", "型B", "型A", "型D"):
        if k in t:
            return k
    return "型なし表記"


def norm_fw(f):
    if f.startswith("MBTI"):
        return "MBTI"
    for k in ("ラブタイプ", "DSKB", "タイプなし"):
        if k in f:
            return k
    return f or "(FW不明)"


def is_question_hook(body):
    head = body.split("\n", 1)[0]
    return any(m in head for m in ("？", "ありませんか", "いませんか", "だろう", "なんだろう"))


def stat_line(name, rows):
    if not rows:
        return f"  {name:<18} n=0"
    vs = [r["views"] for r in rows]
    return (f"  {name:<18} n={len(rows):>2}  mean={statistics.mean(vs):>7.1f}  "
            f"median={statistics.median(vs):>6.1f}  sum={sum(vs):>6d}  "
            f"likes={sum(r['likes'] for r in rows)}")


def grouped(rows, keyfn):
    g = defaultdict(list)
    for r in rows:
        g[keyfn(r)].append(r)
    return sorted(g.items(), key=lambda kv: -statistics.mean([r["views"] for r in kv[1]]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", metavar="YYYY-MM-DD",
                    help="集計ウィンドウの開始日（省略時は threads_insights_notes.md の最新見出し日付）")
    ap.add_argument("--out", metavar="FILE", help="結果をファイルにも書き出す")
    ap.add_argument("--commit", action="store_true",
                    help="threads_analysis_log.json の last_analysis_date を今日に更新する")
    args = ap.parse_args()

    if not DATA_FILE.exists():
        print(f"ERROR: {DATA_FILE} が見つかりません。先に Sheet 同期データを取得してください。")
        sys.exit(1)

    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    posts = sorted(data.get("posts", []), key=lambda p: p["datetime"])
    if not posts:
        print("ERROR: posts 配列が空です。")
        sys.exit(1)

    since = args.since or last_analysis_date()
    if not since:
        since = posts[0]["datetime"][:10]
    win = [p for p in posts if p["datetime"][:10] >= since]

    out = []

    def w(line=""):
        out.append(line)

    w(f"=== MBTICODE Threads 週次集計 ===")
    w(f"データ生成: {data.get('generated_at', '?')}  /  全posts: {len(posts)}"
      f"（{posts[0]['datetime']} 〜 {posts[-1]['datetime']}）")
    w(f"ウィンドウ: {since} 以降  →  n={len(win)}"
      + (f"（{win[0]['datetime']} 〜 {win[-1]['datetime']}）" if win else ""))
    if not win:
        w("対象投稿なし。--since を見直してください。")
        _emit(out, args)
        return

    vs = [p["views"] for p in win]
    med = statistics.median(vs)
    w("")
    w(f"Views: sum={sum(vs)}  mean={statistics.mean(vs):.1f}  median={med:.1f}  "
      f"min={min(vs)}  max={max(vs)}")
    w(f"エンゲージ合計: likes={sum(p['likes'] for p in win)}  "
      f"replies={sum(p['replies'] for p in win)}  reposts={sum(p['reposts'] for p in win)}  "
      f"quotes={sum(p['quotes'] for p in win)}")
    w("※ replies はインサイトタブ値＝自己リプライ除外済み（2026-08-14確認）。外部読者からの返信数")

    thr = max(OUTLIER_MIN_VIEWS, 3 * med)
    outliers = [p for p in win if p["views"] >= thr]
    base = [p for p in win if p["views"] < thr]
    w("")
    w(f"--- 外れ値（views >= {thr:.0f} = max({OUTLIER_MIN_VIEWS}, 3×median)）: {len(outliers)}件 ---")
    for p in outliers:
        w(f"  {p['datetime']}  views={p['views']} likes={p['likes']}  "
          f"[{norm_struct(p['type'])}]  {p['fw']}")
        w(f"      {p['body'][:70].replace(chr(10), ' / ')}")

    w("")
    w("--- 全体 ---")
    w(stat_line("ALL", win))
    w(stat_line("ALL(外れ値除く)", base))

    for title, rows in (("外れ値除く", base), ("全", win)):
        w("")
        w(f"--- 構造型別（{title}） ---")
        for k, rs in grouped(rows, lambda r: norm_struct(r["type"])):
            w(stat_line(k, rs))
        w(f"--- FW別（{title}） ---")
        for k, rs in grouped(rows, lambda r: norm_fw(r["fw"])):
            w(stat_line(k, rs))

    w("")
    w("--- トーン型別（外れ値除く） ---")
    for k, rs in grouped(base, lambda r: norm_tone(r["type"])):
        w(stat_line(k, rs))

    w("")
    w("--- 冒頭フック（外れ値除く） ---")
    w(stat_line("問いかけフック", [p for p in base if is_question_hook(p["body"])]))
    w(stat_line("非問いかけ", [p for p in base if not is_question_hook(p["body"])]))

    w("")
    w("--- 日別本数 ---")
    byday = defaultdict(int)
    for p in win:
        byday[p["datetime"][:10]] += 1
    for d in sorted(byday):
        w(f"  {d}  {byday[d]}本")

    _emit(out, args)

    if args.commit:
        LOG_FILE.write_text(
            json.dumps({"last_analysis_date": datetime.date.today().isoformat()},
                       ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        print(f"\n[commit] threads_analysis_log.json → {datetime.date.today().isoformat()}")


def _emit(out, args):
    text = "\n".join(out)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"\n[out] {args.out}")


if __name__ == "__main__":
    main()
