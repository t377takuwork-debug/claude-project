#!/usr/bin/env python3
"""
Shira Notes 番組表リサーチツール（ネタ発掘・オンデマンド実行専用）
Usage: python tools/research_tv_guide.py [--date YYYYMMDD] [--days N]

省略時は「翌日から3日分」（JST基準）、時間帯は18:00〜23:00を対象にする。
音楽番組かどうかで絞り込まず、東京エリアの全番組を概要文つきで取得する。
記事になりそうな人物・番組・話題をAIが本文（program_detail）を読んで判断するための
生データ出力であり、この時点では記事化の可否は判断しない。

収集先: bangumi.org（番組表.Gガイド） epg/td ページ
  https://bangumi.org/epg/td?broad_cast_date=YYYYMMDD&ggm_group_id=42
  番組タイトル・時間帯・概要文は素のHTMLに含まれており、JS実行は不要。
"""

import argparse
import os
import re
import time
from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

JST = timezone(timedelta(hours=9))

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

EPG_URL = "https://bangumi.org/epg/td?broad_cast_date={date_str}&ggm_group_id=42"

DEFAULT_START = "18:00"
DEFAULT_END = "23:00"
DEFAULT_DAYS = 3


def fetch_html(date_str: str) -> str:
    url = EPG_URL.format(date_str=date_str)
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    return resp.text


def parse_programs(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    # チャンネル名は #ch_area 内の <li class="js_channel topmost"> の並び順が
    # #program_area 内の <ul id="program_line_N"> の並び順（N=1,2,3...）と対応する
    channel_lis = soup.select("#ch_area li.js_channel.topmost")
    channel_names = []
    for li in channel_lis:
        name = li.get_text(strip=True)
        name = re.sub(r"\.+$", "", name)  # 末尾の省略記号「..」を除去
        channel_names.append(name)

    programs = []
    for idx, channel_name in enumerate(channel_names, start=1):
        ul = soup.find("ul", id=f"program_line_{idx}")
        if not ul:
            continue
        for li in ul.find_all("li", recursive=False):
            title_p = li.select_one(".program_title")
            if not title_p:
                continue
            title = title_p.get_text(strip=True)
            detail_p = li.select_one(".program_detail")
            detail = detail_p.get_text(strip=True) if detail_p else ""

            s = li.get("s", "")
            e = li.get("e", "")
            start_time = f"{s[8:10]}:{s[10:12]}" if len(s) >= 12 else ""
            end_time = f"{e[8:10]}:{e[10:12]}" if len(e) >= 12 else ""

            programs.append({
                "channel": channel_name,
                "start": start_time,
                "end": end_time,
                "title": title,
                "detail": detail,
            })

    programs.sort(key=lambda p: (p["start"], p["channel"]))
    return programs


def to_minutes(hhmm: str) -> int | None:
    m = re.match(r"^(\d{1,2}):(\d{2})$", hhmm)
    if not m:
        return None
    return int(m.group(1)) * 60 + int(m.group(2))


def filter_by_time(programs: list[dict], start: str, end: str) -> list[dict]:
    start_min = to_minutes(start)
    end_min = to_minutes(end)
    if start_min is None or end_min is None:
        return programs
    result = []
    for p in programs:
        pm = to_minutes(p["start"])
        if pm is not None and start_min <= pm < end_min:
            result.append(p)
    return result


def date_label(date_str: str) -> str:
    return f"{date_str[:4]}年{int(date_str[4:6])}月{int(date_str[6:8])}日"


def write_md(days: list[dict], output_path: str, time_range: str) -> None:
    now_str = datetime.now(JST).strftime("%Y年%m月%d日 %H:%M")
    first_label = date_label(days[0]["date_str"])
    last_label = date_label(days[-1]["date_str"])
    total = sum(len(d["programs"]) for d in days)

    lines = [
        f"# 番組表リサーチ（{first_label}〜{last_label}・東京エリア・{time_range}）",
        "",
        f"取得日時: {now_str} (JST)",
        f"合計件数: {total}件（" + " / ".join(
            f"{date_label(d['date_str'])} {len(d['programs'])}件" for d in days
        ) + "）",
        "",
        "このファイルは生データ。ジャンルによる絞り込みはしていない。"
        "記事になりそうな人物・番組・話題は、下の概要文をAIが実際に読んで判断すること"
        "（番組名だけで機械的に判定しない）。",
        "",
        "概要文は番組表サイトの短い紹介文であり、記事の事実確認としては使えない。"
        "候補を見つけたら、記事化の前に一次情報（公式サイト・公式SNS等）で必ず裏取りする。",
        "",
        "---",
    ]

    for d in days:
        lines += ["", f"## {date_label(d['date_str'])}（{len(d['programs'])}件）", ""]
        for p in d["programs"]:
            lines.append(f"### {p['start']}-{p['end']} ｜ {p['channel']} ｜ {p['title']}")
            if p["detail"]:
                lines.append(p["detail"])
            lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description="Shira Notes 番組表リサーチ（ネタ発掘）")
    parser.add_argument("--date", metavar="YYYYMMDD", help="開始日（例: 20260915）。省略時は翌日")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS, help=f"取得する日数（既定: {DEFAULT_DAYS}日分。開始日から連続）")
    parser.add_argument("--start", default=DEFAULT_START, help=f"絞り込み開始時刻 HH:MM（既定: {DEFAULT_START}）")
    parser.add_argument("--end", default=DEFAULT_END, help=f"絞り込み終了時刻 HH:MM（既定: {DEFAULT_END}）")
    parser.add_argument("--full", action="store_true", help="時間帯で絞り込まず1日分すべて出力する")
    args = parser.parse_args()

    if args.date:
        try:
            base = datetime.strptime(args.date, "%Y%m%d").replace(tzinfo=JST)
        except ValueError:
            print(f"[ERROR] 日付形式が正しくありません: {args.date}（YYYYMMDD形式で指定してください）")
            return
    else:
        base = datetime.now(JST) + timedelta(days=1)

    time_range = "全時間帯" if args.full else f"{args.start}〜{args.end}"

    print(f"=== Shira Notes 番組表リサーチ ===")
    print(f"対象: {date_label(base.strftime('%Y%m%d'))}から{args.days}日分（東京エリア・{time_range}）")

    days = []
    for offset in range(args.days):
        target = base + timedelta(days=offset)
        date_str = target.strftime("%Y%m%d")

        html = fetch_html(date_str)
        programs = parse_programs(html)
        total_count = len(programs)

        if not args.full:
            programs = filter_by_time(programs, args.start, args.end)

        days.append({"date_str": date_str, "programs": programs})
        print(f"  {date_label(date_str)}: 取得{total_count}件 → 絞り込み後{len(programs)}件")

        if offset < args.days - 1:
            time.sleep(1.5)  # サーバー負荷への配慮

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "tv_guide_research.md")
    write_md(days, output_path, time_range)

    grand_total = sum(len(d["programs"]) for d in days)
    print(f"合計: {grand_total}件")
    print(f"→ {output_path}")


if __name__ == "__main__":
    main()
