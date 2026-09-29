#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_similarity.py — 投稿案と元ネタ（参考にした外部の投稿）の文章の重なりを機械で確かめる

使い方:
  python brands/tools/check_similarity.py <投稿案ファイル> --sources <元ネタの本文ファイル>

投稿案ファイル: 【ヘッダー】＋ ---- 区切りの本文ブロック（posts_x.txt / _batch_*.txt と同じ形式）
元ネタの本文ファイル: 元ネタごとに `=== ID` の行で区切って本文を書いたテキスト
  （**リポジトリには保存しない**。変換のたびに、投稿IDから本文をChromeで取得して、一時ファイルに書く）

各投稿本文 × 各元ネタについて、最長の連続一致（空白を除く）の文字数を出す。
  - 10字以上：WARN（近すぎないか、言い換えたか確認する）
  - 20字以上：ERROR（そのまま使えない。書き直す。exit=1）
「ですよね。」のような一般的な語尾で3〜6字は出る（正常）。
**機械が見るのは表現の重なりだけ。着想の近さ（同じ主張・同じ構造の置き換えになっていないか）は、
人が「元ネタの核」と「自分の核」を1行ずつ書いて判定する**（手順は `.claude/commands/mbticode-neta.md`）。
"""
import argparse
import difflib
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

WARN_LEN = 10
ERROR_LEN = 20
BLOCK_RE = re.compile(r"(【[^】\n]*】[^\n]*)\n-{10,}\s*\n(.+?)\n-{10,}\s*(?:\n|$)", re.S)


def norm(s):
    return re.sub(r"\s+", "", s)


def parse_sources(text):
    out, cur, buf = {}, None, []
    for line in text.splitlines():
        m = re.match(r"^===\s*(.+?)\s*$", line)
        if m:
            if cur is not None:
                out[cur] = "\n".join(buf)
            cur, buf = m.group(1), []
        else:
            buf.append(line)
    if cur is not None:
        out[cur] = "\n".join(buf)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("draft")
    ap.add_argument("--sources", required=True)
    args = ap.parse_args()
    posts = BLOCK_RE.findall(Path(args.draft).read_text(encoding="utf-8"))
    sources = parse_sources(Path(args.sources).read_text(encoding="utf-8"))
    if not posts or not sources:
        print("[ERROR] 投稿ブロックまたは元ネタが読み取れません。")
        sys.exit(2)
    print(f"=== check_similarity: 投稿{len(posts)}本 × 元ネタ{len(sources)}件（最長の連続一致・空白除く）===")
    worst = 0
    warn = err = 0
    for header, body in posts:
        a = norm(body)
        label = header[:30]
        row = []
        for sid, stext in sources.items():
            b = norm(stext)
            m = difflib.SequenceMatcher(None, a, b, autojunk=False).find_longest_match(0, len(a), 0, len(b))
            worst = max(worst, m.size)
            mark = ""
            if m.size >= ERROR_LEN:
                mark, err = " [ERROR]", err + 1
            elif m.size >= WARN_LEN:
                mark, warn = " [WARN]", warn + 1
            row.append(f"{sid}:{m.size}字{mark}")
            if m.size >= WARN_LEN:
                print(f"  ({label}) × {sid}: 「{a[m.a:m.a + m.size]}」")
        print(f"{label} → " + " / ".join(row))
    print(f"=== 結果: 最長一致 {worst}字 / WARN {warn}件 / ERROR {err}件 ===")
    print("機械が見るのは表現の重なりだけ。着想の近さ（核の比較）は人が判定する。")
    sys.exit(1 if err else 0)


if __name__ == "__main__":
    main()
