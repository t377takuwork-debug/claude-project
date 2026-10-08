#!/usr/bin/env python3
# 使い方: python note_diff.py 前の版.md 新しい版.md
# 2つの記事(先頭の管理情報は自動で除く)を、段落ごとに比べて、直された箇所と「修正率」を短く出す。
# noteの画面から読み取った本文(note_read.js の md)と、完成稿を比べるときに使う。出力はUTF-8。
import sys, re, difflib, io

def load(path):
    t = open(path, encoding="utf-8-sig").read().replace("\r\n", "\n")
    m = re.match(r"^.*?\n---[ \t]*\n", t, flags=re.S)
    mm = re.search(r"^# [^\n]*\n", t, flags=re.M)
    if t.startswith("作成日") and mm and (not m or mm.start() < m.end()):
        # s4lvの原稿：管理情報（区切り線なし）のあと、「# タイトル」の行までを除く（S4LVnote版）
        t = t[mm.end():]
    elif m and "作成日" in t[:m.end()]:
        t = t[m.end():]
    blocks = [b.strip(" \t\n") for b in re.split(r"\n[ \t]*\n+", t)]
    out = []
    for b in blocks:
        if not b:
            continue
        # 過去記事のURLだけの段落は、noteの画面側の「カード」と同じ表記にそろえる
        mm = re.fullmatch(r"https?://note\.com/[^/\s]+/n/(n[0-9a-z]+)", b)
        out.append("[カード:%s]" % mm.group(1) if mm else b)
    return out

def main():
    if len(sys.argv) < 3:
        print("使い方: python note_diff.py 前の版.md 新しい版.md"); sys.exit(1)
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    a, b = load(sys.argv[1]), load(sys.argv[2])
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    changed = 0
    lines = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        changed += max(i2 - i1, j2 - j1)
        if tag == "replace":
            # 近い段落どうしを組にして「前→後」を出す
            for k in range(max(i2 - i1, j2 - j1)):
                x = a[i1 + k] if i1 + k < i2 else None
                y = b[j1 + k] if j1 + k < j2 else None
                if x is not None and y is not None:
                    lines.append("直した:\n  前: %s\n  後: %s" % (x, y))
                elif y is not None:
                    lines.append("足した: %s" % y)
                else:
                    lines.append("削った: %s" % x)
        elif tag == "delete":
            lines += ["削った: %s" % x for x in a[i1:i2]]
        else:
            lines += ["足した: %s" % y for y in b[j1:j2]]
    total = max(len(a), len(b))
    cnt = lambda bl, pat: sum(1 for x in bl if re.match(pat, x))
    print("段落数 %d → %d / 直した段落 %d (修正率 %.0f%%)" % (len(a), len(b), changed, 100.0 * changed / total if total else 0))
    print("引用 %d → %d / 見出し %d → %d / 太字 %d → %d / カード %d → %d" % (
        cnt(a, r"> "), cnt(b, r"> "), cnt(a, r"## "), cnt(b, r"## "),
        sum(len(re.findall(r"\*\*[^*\n]+\*\*", x)) for x in a), sum(len(re.findall(r"\*\*[^*\n]+\*\*", x)) for x in b),
        cnt(a, r"\[カード"), cnt(b, r"\[カード")))
    print("\n".join(lines) if lines else "差はありません")

main()
