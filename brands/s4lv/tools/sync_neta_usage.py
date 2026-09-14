#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sync_neta_usage.py — 発信ネタ台帳（x_neta_daicho.md）の使用履歴を自動更新する。

posts_x.txt／posts_threads.txt を保存するたびに qa_gate フックから自動で呼ばれる。
見出し行（【① 9/14 夜20:45｜…（元ネタ＝台帳 K3）】等）から日付・媒体・K/A番号を
読み取り、台帳内の自動記録セクション（AUTO-USAGE-START〜END）へ書き足す。

人間が各K/A項目の中に書く手書きの「使用履歴」欄はそのまま残す（上書きしない）。
自動記録セクションが常に最新の「使ったかどうか」を反映するので、今後はここを見れば
使用履歴の記載漏れは起きない。

使い方:
  python sync_neta_usage.py <posts_x.txt または posts_threads.txt> [--platform x|threads]

台帳ファイル（x_neta_daicho.md）が投稿ファイルの1つ上の階層に無いアカウント
（MBTICODE等）の場合は何もせず終了する（s4lv専用の仕組みのため）。
"""
import argparse
import os
import re
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

AUTO_START = "<!-- AUTO-USAGE-START -->"
AUTO_END = "<!-- AUTO-USAGE-END -->"
SECTION_HEADING = "## 使用履歴・自動記録（sync_neta_usage.py が管理・手で編集しない）"
SECTION_INTRO = (
    "\nposts_x.txt／posts_threads.txt を保存するたびに自動で更新される。"
    "各K/A項目に使うネタを選ぶ前に、まずここで直近の使用履歴を確認する"
    "（各項目内の手書き「使用履歴」欄は当時のメモとして残るが、更新が漏れることがある"
    "ため、重複チェックはこちらを優先する）。\n"
)
MAX_ENTRIES_PER_CODE = 10
CODE_RE = re.compile(r"\b([KA]\d{1,2})\b")
HEADER_RE = re.compile(r"^【.*】")
DATE_RE = re.compile(r"(\d{1,2})/(\d{1,2})")
TIME_RE = re.compile(r"(\d{1,2}:\d{2})")
YEAR_RE = re.compile(r"(20\d{2})-\d{2}-\d{2}")
CIRCLED_RE = re.compile(r"【\s*([①②③④⑤⑥⑦⑧⑨⑩])")


def find_year_context(lines, idx):
    for i in range(idx, -1, -1):
        m = YEAR_RE.search(lines[i])
        if m:
            return m.group(1)
    for i in range(idx, len(lines)):
        m = YEAR_RE.search(lines[i])
        if m:
            return m.group(1)
    return "2026"


def parse_posts_file(path, platform):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    entries = {}  # code -> list of (sort_key, label)
    for idx, line in enumerate(lines):
        if not HEADER_RE.match(line.strip()):
            continue
        header = line.strip()
        codes = list(dict.fromkeys(CODE_RE.findall(header)))
        if not codes:
            continue

        date_m = DATE_RE.search(header)
        if not date_m:
            continue
        month, day = int(date_m.group(1)), int(date_m.group(2))
        year = find_year_context(lines, idx)
        time_m = TIME_RE.search(header)
        time_part = " " + time_m.group(1) if time_m else ""

        if platform == "x":
            slot_m = CIRCLED_RE.search(header)
            slot = slot_m.group(1) if slot_m else ""
            label = "X{} {}/{}{}".format(slot, month, day, time_part)
        else:
            label = "Threads {}/{}{}".format(month, day, time_part)

        sort_key = "{}-{:02d}-{:02d}{}".format(year, month, day, time_part.replace(":", ""))
        for code in codes:
            entries.setdefault(code, []).append((sort_key, label))

    return entries


def parse_existing_table(section_text):
    """既存の自動記録テーブルから {code: [entry_str, ...]} を復元する。"""
    existing = {}
    for line in section_text.splitlines():
        m = re.match(r"^\|\s*([KA]\d{1,2})\s*\|\s*(.*?)\s*\|\s*$", line)
        if not m:
            continue
        code, cell = m.group(1), m.group(2)
        parts = [p.strip() for p in cell.split("／") if p.strip()]
        existing[code] = parts
    return existing


def merge(existing, new_entries):
    """new_entries: {code: [(sort_key, label), ...]}。文字列表現で重複排除しつつ結合する。"""
    merged = {}
    all_codes = set(existing) | set(new_entries)
    for code in all_codes:
        seen = []
        seen_set = set()
        for label in existing.get(code, []):
            if label not in seen_set:
                seen.append(label)
                seen_set.add(label)
        for sort_key, label in new_entries.get(code, []):
            display = "{} {}".format(sort_key[:10], label)
            if display not in seen_set:
                seen.append(display)
                seen_set.add(display)
        seen.sort(reverse=True)
        merged[code] = seen[:MAX_ENTRIES_PER_CODE]
    return merged


def render_table(merged):
    lines = ["| コード | 直近の使用（新しい順） |", "|---|---|"]
    for code in sorted(merged, key=lambda c: (c[0], int(c[1:]))):
        cell = "／".join(merged[code])
        lines.append("| {} | {} |".format(code, cell))
    return "\n".join(lines)


def update_ledger(ledger_path, new_entries):
    with open(ledger_path, "r", encoding="utf-8") as f:
        content = f.read()

    if AUTO_START in content and AUTO_END in content:
        pre, rest = content.split(AUTO_START, 1)
        section_body, post = rest.split(AUTO_END, 1)
        existing = parse_existing_table(section_body)
        merged = merge(existing, new_entries)
        new_section = "\n" + render_table(merged) + "\n"
        content = pre + AUTO_START + new_section + AUTO_END + post
    else:
        merged = merge({}, new_entries)
        block = "\n---\n\n{}\n{}\n{}\n{}\n{}\n".format(
            SECTION_HEADING, SECTION_INTRO, AUTO_START,
            render_table(merged), AUTO_END,
        )
        anchor = "# 棚卸しの出どころ"
        if anchor in content:
            content = content.replace(anchor, block.strip("\n") + "\n\n---\n\n" + anchor, 1)
        else:
            content = content.rstrip("\n") + "\n" + block

    with open(ledger_path, "w", encoding="utf-8") as f:
        f.write(content)
    return merged


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("posts_file")
    parser.add_argument("--platform", choices=["x", "threads"], default=None)
    args = parser.parse_args()

    posts_file = args.posts_file
    base = os.path.basename(posts_file)
    platform = args.platform
    if platform is None:
        if base == "posts_x.txt":
            platform = "x"
        elif base == "posts_threads.txt":
            platform = "threads"
        else:
            print("[sync_neta_usage] 対象外のファイル名: {}".format(base))
            return 0

    ledger_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(posts_file))), "x_neta_daicho.md")
    if not os.path.isfile(ledger_path):
        print("[sync_neta_usage] 台帳が見つからないため対象外: {}".format(ledger_path))
        return 0

    new_entries = parse_posts_file(posts_file, platform)
    if not new_entries:
        print("[sync_neta_usage] 見出しからK/Aコードを検出できず。変更なし。")
        return 0

    merged = update_ledger(ledger_path, new_entries)
    touched = ", ".join(sorted(new_entries.keys()))
    print("[sync_neta_usage] 台帳を更新: {} （対象コード: {}）".format(ledger_path, touched))
    return 0


if __name__ == "__main__":
    sys.exit(main())
