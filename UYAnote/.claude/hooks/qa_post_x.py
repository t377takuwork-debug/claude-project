#!/usr/bin/env python3
"""UYA. X投稿の機械チェック(UYAnote用)。

元の `uya/tools/qa_post_uya.py` の検知(過去形の言い切り・AI感フレーズ・『』の使いすぎ・
同じ語尾の連続・読点過多)に、X投稿の型(3_広報部/X投稿の型.md)の決まりを足したもの。
文体の良し悪し・「誰でも知っている話か」・材料の裏取りなど、判断が要るものは対象外
(X投稿AIの自己チェックと、オーナーの目で見る)。

使い方:
    python .claude/hooks/qa_post_x.py <提案ファイル(.md)> [--threads]

--threads: スレッズ用。字数の上限を全角500字(改行を含む文字数)にする。そのほかの検査はXと同じ
(3_広報部/スレッズ投稿の型.md が、Xの決まりを引き継ぐため)。

提案ファイルの読み方: 「## 〜本目」などの見出しの下にある ``` で囲んだ部分を1投稿として検査する。
その直前の行が「自己返信」で始まるものは、自己返信として検査する(自己返信は問いの割合に数えない)。
ERROR が1件でもあれば exit code 1。WARN のみなら exit code 0(自分で判断)。
"""
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

AI_PHRASES = [
    "と思います", "と感じます", "と感じています", "という感じ", "が大切です", "が重要です",
    "以上のように", "このように、まとめると", "ではないでしょうか",
]
# オーナーが「AIっぽい」として外してほしいと言った言い方(2026-10-07)
BANNED_ENDINGS = ["だけで。", "その繰り返しで。", "だけです。", "てるだけ", "してるだけ"]
# 開示してはいけない言葉(`personal_data.md` 開示ルール。s4lvとの関係にXでは触れない)
DISCLOSURE_NG = ["ヘルニア", "ロジスティクス", "s4lv", "salvami", "amiibo", "アミーボ"]

MAX_WEIGHT = 280      # 全角=2・半角=1・改行=1
THREADS_MAX_CHARS = 500   # スレッズ(--threads)は文字数
THREADS = False
# スレッズで死にやすい書き出し(threads_algorithm_2026.md)
THREADS_BAD_OPENINGS = ["方法をまとめました", "学びをシェア", "知らないと損", "保存推奨", "拡散希望"]


def weight(text):
    return sum(1 if ord(c) < 128 else 2 for c in text)


def line_width(line):
    return sum(0.5 if ord(c) < 128 else 1 for c in line)


def split_paragraphs(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def split_sentences(paragraph):
    return [s for s in re.split(r"(?<=[。？])", paragraph.replace("\n", "")) if s.strip()]


def parse_blocks(md):
    """見出しごとに ``` ブロックを集める。戻り値: [(ラベル, 種別('本文'|'自己返信'), 本文)]"""
    blocks, heading, lines, i = [], "", md.split("\n"), 0
    prev_nonempty = ""
    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            heading = line[3:].strip()
        if line.startswith("```"):
            j, body = i + 1, []
            while j < len(lines) and not lines[j].startswith("```"):
                body.append(lines[j])
                j += 1
            kind = "自己返信" if prev_nonempty.startswith("自己返信") else "本文"
            blocks.append((heading or "(見出しなし)", kind, "\n".join(body).strip("\n")))
            i = j
            prev_nonempty = ""
        elif line.strip():
            prev_nonempty = line.strip()
        i += 1
    return blocks


def check_block(label, kind, text):
    msgs = []
    paragraphs = split_paragraphs(text)
    if not paragraphs:
        return [("ERROR", "空の投稿")]

    if THREADS:
        n_chars = len(text)
        if n_chars > THREADS_MAX_CHARS:
            msgs.append(("ERROR", f"字数超過: {n_chars}字(上限{THREADS_MAX_CHARS}字)"))
        elif kind == "本文" and n_chars < 150:
            msgs.append(("WARN", f"{n_chars}字。スレッズは経過ごと出すので短すぎないか(目安250〜400字)"))
        for ph in THREADS_BAD_OPENINGS:
            if ph in text:
                msgs.append(("ERROR", f"スレッズで死にやすい言い方「{ph}」"))
        for ph in ["コメントして", "と返して", "リプして"]:
            if ph in text:
                msgs.append(("ERROR", f"反応を要求する言い方「{ph}」"))
    else:
        w = weight(text)
        if w > MAX_WEIGHT:
            msgs.append(("ERROR", f"字数超過: 重み{w}(上限{MAX_WEIGHT}。全角=2・半角=1・改行=1)"))
    urls = re.findall(r"https?://\S+", text)
    if urls and kind == "本文":
        msgs.append(("ERROR", "本文にURLが入っている(URLは、公開済みの記事がある話題の自己返信にだけ置く)"))
    elif urls and kind == "自己返信":
        for u in urls:
            if not u.startswith("https://note.com/uyadot/n/"):
                msgs.append(("ERROR", f"自己返信のURLが、UYA.のnote記事(https://note.com/uyadot/n/...)ではない: {u}"))
    for ph in AI_PHRASES:
        if ph in text:
            msgs.append(("ERROR", f"AI感フレーズ「{ph}」"))
    for p in paragraphs:
        for s in split_sentences(p):
            if re.search(r"[てで]。$", s.strip()):
                msgs.append(("ERROR", f"文末が「〜て。」「〜くて。」の尻切れ(外してほしい言い方): 「...{s.strip()[-14:]}」"))
            if re.search(r"(だった|かった)。$", s.strip()):
                msgs.append(("ERROR", f"文末が過去形の言い切り: 「...{s.strip()[-14:]}」"))
    flat = text.replace("\n", "")
    for b in BANNED_ENDINGS:
        if b in flat:
            msgs.append(("ERROR", f"外してほしいと言われた言い方「{b}」"))
    for ng in DISCLOSURE_NG:
        if ng.lower() in flat.lower():
            msgs.append(("ERROR", f"開示NGの言葉「{ng}」"))

    # 冒頭の決まり(本文のみ)
    if kind == "本文":
        first = split_sentences(paragraphs[0])
        if first:
            head = first[0].strip()
            if re.search(r"んだけど。$", head) or (len(first) == 1 and re.search(r"んだけど。$", paragraphs[0].replace("\n", ""))):
                msgs.append(("ERROR", f"冒頭が「〜んだけど。」で宙に浮いている(何の話か結論を言い切る): 「{head[:24]}...」"))
            if re.search(r"(じゃない|ではない|じゃなくて)[。、]", head) and len(head) < 40:
                msgs.append(("WARN", f"冒頭が否定の形(AIの典型の型に見えやすい): 「{head[:24]}...」"))

    if text.count("『") > 2:
        msgs.append(("WARN", f"『』が{text.count('『')}回(目安1〜2回まで)"))
    for p in paragraphs:
        for s in split_sentences(p):
            if s.count("、") > 2:
                msgs.append(("WARN", f"読点が{s.count('、')}個: 「{s.strip()[:24]}...」"))
    ends = []
    for p in paragraphs:
        m = re.search(r"([^\s。？]{2,6})[。？]?$", p.replace("\n", ""))
        ends.append(m.group(1)[-3:] if m else "")
    for a, b in zip(ends, ends[1:]):
        if a and a == b:
            msgs.append(("WARN", f"連続する段落の文末が同じ語尾「{a}」"))
    if re.search(r"\d+万円", flat):
        msgs.append(("WARN", "金額(○万円)がある。月1回まで・煽らない・今週の使用可否をオーナーに確認済みか"))
    if "パチ" in flat:
        msgs.append(("WARN", "パチンコ・パチスロへの言及。主題にしない・立ち回り/金額/店名/機種は出さない"))
    if re.search(r"(みなさん|みんな|皆さん)[^。？]*？", flat):
        msgs.append(("WARN", "「みなさんは〜？」の呼びかけ型の問い"))
    return msgs


def main():
    global THREADS
    args = [a for a in sys.argv[1:] if a != "--threads"]
    THREADS = len(args) != len(sys.argv) - 1
    if not args:
        print("使い方: python .claude/hooks/qa_post_x.py <提案ファイル(.md)> [--threads]")
        sys.exit(1)
    with open(args[0], encoding="utf-8") as f:
        md = f.read()
    blocks = parse_blocks(md)
    if not blocks:
        print("[ERROR] ``` で囲んだ投稿が見つからない")
        sys.exit(1)

    total_err = total_warn = 0
    bodies, ends_with_q, ndayone = [], 0, 0
    for label, kind, text in blocks:
        msgs = check_block(label, kind, text)
        print(f"=== {label}({kind}) ===")
        if not msgs:
            print("[OK] 検知した問題なし")
        for level, m in msgs:
            print(f"[{level}] {m}")
            total_err += level == "ERROR"
            total_warn += level == "WARN"
        print()
        if kind == "本文":
            bodies.append(text)
            if text.rstrip().endswith("？"):
                ends_with_q += 1
        ndayone += text.count("んだよね")

    print("=== 全体 ===")
    n = len(bodies)
    if n > 5:
        print(f"[WARN] 本文が{n}本(週5本まで)")
        total_warn += 1
    if n and ends_with_q > n / 3:
        print(f"[WARN] 問いで終わる投稿が{ends_with_q}/{n}本(3本に1本以下)")
        total_warn += 1
    if ndayone > 1:
        print(f"[WARN] 「〜んだよね」が{ndayone}回(4本のうち1回まで)")
        total_warn += 1
    if not (ends_with_q > n / 3 or ndayone > 1 or n > 5):
        print("[OK] 本数・問いの割合・「んだよね」の回数")
    print(f"\n=== 結果: ERROR {total_err}件 / WARN {total_warn}件 ===")
    sys.exit(1 if total_err else 0)


if __name__ == "__main__":
    main()
