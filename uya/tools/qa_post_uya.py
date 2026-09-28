#!/usr/bin/env python3
"""UYA. X/スレッズ投稿ドラフトの機械チェック（軽量版）。

今日までに実際に繰り返し発生した問題（文末の過去形言い切り・『』の使いすぎ・
AI感フレーズ・段落文末の連続重複・読点過多・X/スレッズ書き出しの重複）だけを
検知する。文体・当たり前チェック・人間らしさ等の判断が必要なものは対象外
（uya-post.md Step 3 の自己チェックで人間が見る）。

使い方:
    python uya/tools/qa_post_uya.py <X本文ファイル> <スレッズ本文ファイル>

ERROR が1件でもあれば exit code 1。WARN のみなら exit code 0（自分で判断）。
"""
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

AI_PHRASES = [
    "と思います", "と感じます", "という感じ", "が大切です", "が重要です",
    "以上のように", "このように、まとめると", "ではないでしょうか",
]


def split_paragraphs(text):
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def split_sentences(paragraph):
    return [s for s in re.split(r"(?<=[。？])", paragraph) if s.strip()]


def check_dakatta_hardstop(paragraphs):
    errors = []
    for p in paragraphs:
        for s in split_sentences(p):
            s = s.strip()
            if re.search(r"(だった|かった)。$", s):
                errors.append(f"[ERROR] 文末が過去形の言い切り: 「...{s[-14:]}」")
    return errors


def check_bracket_overuse(text):
    count = text.count("『")
    if count > 2:
        return [f"[WARN] 『』の使用が{count}回（目安1〜2回まで）"]
    return []


def check_ai_phrases(text):
    return [f"[ERROR] AI感フレーズ「{phrase}」を検出" for phrase in AI_PHRASES if phrase in text]


def check_repeated_endings(paragraphs):
    endings = []
    for p in paragraphs:
        m = re.search(r"([^\s。？]{2,6})[。？]?$", p)
        endings.append(m.group(1)[-3:] if m else "")
    warns = []
    for i in range(len(endings) - 1):
        if endings[i] and endings[i] == endings[i + 1]:
            warns.append(f"[WARN] 連続する段落の文末が同じ語尾「{endings[i]}」")
    return warns


def check_comma_count(paragraphs, limit=2):
    warns = []
    for p in paragraphs:
        for s in split_sentences(p):
            c = s.count("、")
            if c > limit:
                warns.append(f"[WARN] 読点が{c}個: 「{s.strip()[:24]}...」")
    return warns


def run_checks(text, label):
    print(f"=== {label} ===")
    paragraphs = split_paragraphs(text)
    msgs = (
        check_dakatta_hardstop(paragraphs)
        + check_bracket_overuse(text)
        + check_ai_phrases(text)
        + check_repeated_endings(paragraphs)
        + check_comma_count(paragraphs)
    )
    if not msgs:
        print("[OK] 検知した問題なし")
    else:
        for m in msgs:
            print(m)
    print()
    return msgs


def check_cross_platform_duplication(text_x, text_threads):
    x_paras = split_paragraphs(text_x)
    t_paras = split_paragraphs(text_threads)
    if not x_paras or not t_paras:
        return []
    x_first = split_sentences(x_paras[0])[0].strip() if split_sentences(x_paras[0]) else ""
    t_first = split_sentences(t_paras[0])[0].strip() if split_sentences(t_paras[0]) else ""
    if x_first and x_first == t_first:
        return [f"[ERROR] X・スレッズの書き出しの一文が完全一致: 「{x_first[:30]}...」"]
    return []


def main():
    if len(sys.argv) < 3:
        print("使い方: python qa_post_uya.py <X本文ファイル> <スレッズ本文ファイル>")
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f:
        text_x = f.read()
    with open(sys.argv[2], encoding="utf-8") as f:
        text_threads = f.read()

    msgs_x = run_checks(text_x, "X版")
    msgs_t = run_checks(text_threads, "スレッズ版")

    print("=== X・スレッズ間の重複チェック ===")
    dup_msgs = check_cross_platform_duplication(text_x, text_threads)
    if not dup_msgs:
        print("[OK] 書き出しの重複なし")
    else:
        for m in dup_msgs:
            print(m)

    total_errors = sum(1 for m in msgs_x + msgs_t + dup_msgs if m.startswith("[ERROR]"))
    total_warns = sum(1 for m in msgs_x + msgs_t + dup_msgs if m.startswith("[WARN]"))
    print(f"\n=== 結果: ERROR {total_errors}件 / WARN {total_warns}件 ===")
    sys.exit(1 if total_errors else 0)


if __name__ == "__main__":
    main()
