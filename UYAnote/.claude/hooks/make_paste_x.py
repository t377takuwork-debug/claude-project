#!/usr/bin/env python3
"""X投稿の提案ファイルから、Xの予約投稿に貼り付けるためのファイルを作る(UYAnote用)。

使い方:
    python .claude/hooks/make_paste_x.py <提案ファイル(.md)> <最初の投稿日 YYYY-MM-DD> [出力ファイル] [--only 1,3,4]

投稿は、最初の投稿日から2日おき、20:45 に出す前提で日時を付ける(`X投稿の型.md`)。
提案ファイルの読み方は qa_post_x.py と同じ(見出し「## 〜本目」の下の ``` ブロック。
直前の行が「自己返信」で始まるものは自己返信)。
各投稿の「注意:」で始まる行も、いっしょに写す(出す前に見てもらうため)。
出力は、本文を ``` で囲んだ貼り付け用ファイル。X予約AIが、これを読んでXに予約する(確定の前に、オーナーの許可を取る)。
"""
import datetime
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

POST_TIME = "20:45"
STEP_DAYS = 2
WEEKDAY = "月火水木金土日"


def weight(text):
    return sum(1 if ord(c) < 128 else 2 for c in text)


def parse(md):
    """見出しごとに、本文・自己返信・注意をまとめる。"""
    posts, cur, lines, i, prev = [], None, md.split("\n"), 0, ""
    while i < len(lines):
        line = lines[i]
        m = re.match(r"## (\d+)本目(.*)", line)
        if m:
            cur = {"n": int(m.group(1)), "title": line[3:].strip(), "body": None, "reply": None, "notes": []}
            posts.append(cur)
        elif line.startswith("## "):
            cur = None
        if line.startswith("```") and cur is not None:
            j, body = i + 1, []
            while j < len(lines) and not lines[j].startswith("```"):
                body.append(lines[j])
                j += 1
            text = "\n".join(body).strip("\n")
            if prev.startswith("自己返信"):
                cur["reply"] = text
            elif cur["body"] is None:
                cur["body"] = text
            i = j
            prev = ""
        elif line.strip():
            prev = line.strip()
            if cur is not None and line.startswith("注意:"):
                cur["notes"].append(line.strip())
        i += 1
    return [p for p in posts if p["body"]]


def main():
    if len(sys.argv) < 3:
        print("使い方: python .claude/hooks/make_paste_x.py <提案ファイル> <最初の投稿日 YYYY-MM-DD> [出力ファイル]")
        sys.exit(1)
    args = sys.argv[1:]
    only = None
    if "--only" in args:
        i = args.index("--only")
        only = [int(x) for x in args[i + 1].split(",")]
        del args[i:i + 2]
    src, start = args[0], datetime.date.fromisoformat(args[1])
    out = args[2] if len(args) > 2 else None
    with open(src, encoding="utf-8") as f:
        posts = parse(f.read())
    if only:
        posts = [p for p in posts if p["n"] in only]
    if not posts:
        print("[ERROR] 投稿が見つからない")
        sys.exit(1)

    o = [f"# X貼り付け用({src.replace(chr(92), '/').split('/')[-1]} から)", "",
         "Xの予約投稿に入れるための元データ。X予約AIが読んで、内蔵ブラウザから予約する(予約の確定の前に、オーナーの許可を取る)。ブラウザが使えないときは、下の本文をそのまま貼って手で予約する。",
         "自己返信がある投稿は、本文と同じ日時のスレッド(2つ並んだポスト)にして予約する(Xの予約は返信単体に使えないため)。",
         "「手直し済み」と書いた投稿は、実際に手直ししてから出す。", ""]
    for k, p in enumerate(posts):
        d = start + datetime.timedelta(days=STEP_DAYS * k)
        o.append(f"## {p['title']}")
        o.append(f"予約日時: {d.year}-{d.month:02d}-{d.day:02d}({WEEKDAY[d.weekday()]}) {POST_TIME}")
        o.append(f"字数: 重み{weight(p['body'])}/280")
        o.append("")
        o.append("本文:")
        o.append("```")
        o.append(p["body"])
        o.append("```")
        if p["reply"]:
            o.append("")
            o.append("自己返信(本文と同じ日時のスレッドの2つ目として予約する):")
            o.append("```")
            o.append(p["reply"])
            o.append("```")
        for n in p["notes"]:
            o.append("")
            o.append(n)
        o.append("")
    text = "\n".join(o).rstrip("\n") + "\n"
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[OK] {out} に保存({len(posts)}本)")
    else:
        print(text)


if __name__ == "__main__":
    main()
