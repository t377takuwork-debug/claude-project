#!/usr/bin/env python3
"""
PageSpeed Insights 解析ツール（perf_audit.py の後段）
Usage:
  python analyze_psi.py <json_path> [json_path ...]
  python analyze_psi.py --day YYYYMMDD   # output/psi/<day>/ 配下の全JSONを解析

出力:
  各JSONについて「コアウェブバイタル」「改善余地ランキング（スコアを下げている要因）」を
  表形式で表示し、同じフォルダに {元ファイル名}_ranking.md として保存する。
"""

import argparse
import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
OUTPUT_ROOT = TOOLS_DIR / "output" / "psi"

CORE_METRICS = [
    ("largest-contentful-paint", "LCP"),
    ("cumulative-layout-shift", "CLS"),
    ("total-blocking-time", "TBT"),
    ("first-contentful-paint", "FCP"),
    ("speed-index", "Speed Index"),
    ("interactive", "TTI"),
]


def score_pct(score: float | None) -> str:
    if score is None:
        return "-"
    return f"{round(score * 100)}"


def build_core_table(audits: dict) -> list[tuple]:
    rows = []
    for key, label in CORE_METRICS:
        a = audits.get(key)
        if not a:
            continue
        rows.append((label, a.get("score"), a.get("displayValue", "-")))
    rows.sort(key=lambda r: (r[1] if r[1] is not None else 1))
    return rows


def build_opportunity_ranking(audits: dict) -> list[tuple]:
    """scoreDisplayMode が metricSavings かつ score<1 の監査項目 = スコアを下げている改善余地"""
    rows = []
    for key, a in audits.items():
        if a.get("scoreDisplayMode") != "metricSavings":
            continue
        score = a.get("score")
        if score is None or score >= 1:
            continue
        rows.append((a.get("title", key), score, a.get("displayValue", "-")))
    rows.sort(key=lambda r: r[1])
    return rows


def render_report(url: str, strategy: str, overall_score, core_rows, opp_rows) -> str:
    lines = [
        "# PageSpeed Insights 解析結果",
        "",
        f"- URL: {url}",
        f"- strategy: {strategy}",
        f"- Performance score: {score_pct(overall_score)}",
        "",
        "## コアウェブバイタル（スコアが低い順）",
        "",
        "| 指標 | スコア | 実測値 |",
        "|---|---|---|",
    ]
    for label, score, display in core_rows:
        lines.append(f"| {label} | {score_pct(score)} | {display} |")

    lines += ["", "## 改善余地ランキング（スコアを下げている要因・影響が大きい順）", ""]
    if not opp_rows:
        lines.append("(スコアを下げている改善項目なし)")
    else:
        lines.append("| # | 項目 | スコア | 推定改善量 |")
        lines.append("|---|---|---|---|")
        for i, (title, score, display) in enumerate(opp_rows, 1):
            lines.append(f"| {i} | {title} | {score_pct(score)} | {display} |")
    lines.append("")
    return "\n".join(lines)


def analyze_file(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    lr = data.get("lighthouseResult", {})
    audits = lr.get("audits", {})
    url = lr.get("requestedUrl") or data.get("id", "-")
    strategy = lr.get("configSettings", {}).get("formFactor", "-")
    overall_score = lr.get("categories", {}).get("performance", {}).get("score")

    core_rows = build_core_table(audits)
    opp_rows = build_opportunity_ranking(audits)

    report_md = render_report(url, strategy, overall_score, core_rows, opp_rows)
    out_path = path.with_name(path.stem + "_ranking.md")
    out_path.write_text(report_md, encoding="utf-8")

    print(f"=== {path.name} ===")
    print(f"URL: {url} [{strategy}] performance: {score_pct(overall_score)}")
    print("-- 改善余地ランキング --")
    if not opp_rows:
        print("  (なし)")
    for i, (title, score, display) in enumerate(opp_rows, 1):
        print(f"  {i}. {title} (score {score_pct(score)}) - {display}")
    print(f"  詳細レポート: {out_path}")
    print()

    return {
        "path": path,
        "url": url,
        "strategy": strategy,
        "overall_score": overall_score,
        "opp_rows": opp_rows,
    }


def main():
    parser = argparse.ArgumentParser(description="PageSpeed Insights 解析ツール")
    parser.add_argument("json_paths", nargs="*", help="解析対象のJSONファイル")
    parser.add_argument("--day", help="output/psi/<day>/ 配下の全JSONを解析")
    args = parser.parse_args()

    paths = [Path(p) for p in args.json_paths]
    if args.day:
        day_dir = OUTPUT_ROOT / args.day
        paths += sorted(day_dir.glob("*.json"))

    if not paths:
        print("解析対象のJSONがありません。--day YYYYMMDD かファイルパスを指定してください。", file=sys.stderr)
        sys.exit(1)

    for p in paths:
        if not p.exists():
            print(f"見つかりません: {p}", file=sys.stderr)
            continue
        analyze_file(p)


if __name__ == "__main__":
    main()
