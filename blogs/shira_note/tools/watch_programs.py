#!/usr/bin/env python3
"""
Shira Notes 番組情報 差分監視ツール（watch_programs.py）

bangumi.org の番組表を今日〜N日先までスキャンし、前回実行時のスナップショットと
比較して「新規に載った音楽番組・特番」「消えた番組」「時間変更」を検出する。

Usage:
  python tools/watch_programs.py            # 今日から7日先までスキャン
  python tools/watch_programs.py --days 14  # 14日先まで

出力:
  tools/output/watch_report.md            差分レポート（毎回上書き）
  tools/output/snapshots/YYYYMMDD.json    日付ごとのスナップショット

運用: 1日1回（朝）実行するだけで、新しく発表された特番・タイテ変更を検知できる。
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collect_news import scrape_bangumi, JST  # noqa: E402

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
SNAP_DIR = os.path.join(OUTPUT_DIR, "snapshots")


def load_snapshot(date_str: str) -> list[dict] | None:
    path = os.path.join(SNAP_DIR, f"{date_str}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_snapshot(date_str: str, programs: list[dict]) -> None:
    os.makedirs(SNAP_DIR, exist_ok=True)
    path = os.path.join(SNAP_DIR, f"{date_str}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(programs, f, ensure_ascii=False, indent=1)


def diff_programs(prev: list[dict], curr: list[dict]) -> dict:
    prev_by_url = {p["url"]: p for p in prev}
    curr_by_url = {p["url"]: p for p in curr}
    new = [p for u, p in curr_by_url.items() if u not in prev_by_url]
    removed = [p for u, p in prev_by_url.items() if u not in curr_by_url]
    changed = []
    for u, p in curr_by_url.items():
        if u in prev_by_url:
            old = prev_by_url[u]
            diffs = []
            for key in ("time", "title", "channel"):
                if old.get(key) != p.get(key):
                    diffs.append(f"{key}: {old.get(key)} → {p.get(key)}")
            if diffs:
                changed.append({**p, "diffs": diffs})
    return {"new": new, "removed": removed, "changed": changed}


def fmt_program(p: dict) -> str:
    parts = [f"**{p['title']}**"]
    if p.get("date"):
        parts.append(f"{p['date']} {p.get('time', '')}".strip())
    if p.get("channel"):
        parts.append(p["channel"])
    parts.append(f"[{p['type']}]")
    return " / ".join(parts) + f"\n  - {p['url']}"


def main():
    parser = argparse.ArgumentParser(description="番組情報の差分監視")
    parser.add_argument("--days", type=int, default=7, help="今日から何日先までスキャンするか（既定: 7）")
    args = parser.parse_args()

    now = datetime.now(JST)
    print(f"=== 番組情報 差分監視（{now.strftime('%Y-%m-%d %H:%M')} JST / {args.days}日先まで）===\n")

    report_lines = [
        "# 番組情報 差分レポート",
        "",
        f"実行日時: {now.strftime('%Y年%m月%d日 %H:%M')} (JST)",
        f"スキャン範囲: 今日〜{args.days}日先",
        "",
    ]
    any_change = False
    first_runs = []

    for offset in range(args.days + 1):
        target = now + timedelta(days=offset)
        date_str = target.strftime("%Y%m%d")
        label = target.strftime("%m月%d日").lstrip("0").replace("月0", "月")

        print(f"[{date_str}] 取得中...")
        programs = scrape_bangumi(target)
        time.sleep(1.5)  # サーバー負荷への配慮

        prev = load_snapshot(date_str)
        save_snapshot(date_str, programs)

        if prev is None:
            first_runs.append(f"{label}（{len(programs)}件）")
            continue

        d = diff_programs(prev, programs)
        if not (d["new"] or d["removed"] or d["changed"]):
            continue

        any_change = True
        report_lines += [f"## {label}（{date_str}）", ""]
        if d["new"]:
            report_lines.append("### 🆕 新規検出")
            for p in d["new"]:
                report_lines.append(f"- {fmt_program(p)}")
            report_lines.append("")
        if d["changed"]:
            report_lines.append("### 🔄 変更")
            for p in d["changed"]:
                report_lines.append(f"- {fmt_program(p)}")
                for diff in p["diffs"]:
                    report_lines.append(f"  - {diff}")
            report_lines.append("")
        if d["removed"]:
            report_lines.append("### ❌ 消失（放送中止・改編の可能性）")
            for p in d["removed"]:
                report_lines.append(f"- {fmt_program(p)}")
            report_lines.append("")

    if first_runs:
        report_lines += [
            "## 初回スキャン（ベースライン保存のみ・次回から差分検出）",
            "",
            "- " + " / ".join(first_runs),
            "",
        ]
    if not any_change and not first_runs:
        report_lines += ["## 変化なし", "", "前回スキャンから新規・変更・消失はありません。", ""]

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report_path = os.path.join(OUTPUT_DIR, "watch_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\n=== 完了 ===")
    print(f"レポート: {report_path}")
    if any_change:
        print("★ 差分が検出されました。watch_report.md を確認してください。")
    elif first_runs:
        print("初回スキャン: ベースラインを保存しました。次回実行から差分を検出します。")
    else:
        print("変化なし。")


if __name__ == "__main__":
    main()
