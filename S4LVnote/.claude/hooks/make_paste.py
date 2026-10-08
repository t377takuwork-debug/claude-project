#!/usr/bin/env python3
# 使い方: python3 .claude/hooks/make_paste.py "3_広報部/note本文_YYYY-MM-DD.txt"
#        (Windowsで python3 が無ければ python か py -3 で同じ)
# 本文txt(マークダウン見出し付き)から、noteエディタに合成pasteで一括投入する完成JavaScriptを1行で出力する
# Mac / Windows 共通: 入出力はUTF-8固定(コンソールの文字コードに依存しない)
import sys, json, re, html

if len(sys.argv) < 2:
    sys.stderr.buffer.write("使い方: python3 .claude/hooks/make_paste.py 本文ファイル.txt\n".encode("utf-8"))
    sys.exit(1)

with open(sys.argv[1], encoding="utf-8-sig") as f:
    src = f.read().replace("\r\n", "\n")

# 全角スペースだけの行(見出し前の広い余白)を消さないよう、空行の判定は半角の空白だけにする
WS = " \t\r\n"
blocks = [b for b in re.split(r"\n[ \t]*\n+", src) if b.strip(WS)]

def inline(t):
    # **〜** を太字(<strong>)にする。エスケープしてから変換する
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(t))

out = []
for b in blocks:
    s = b.strip(WS)
    if s.strip("　") == "":
        out.append("<p>　</p>")
    elif re.fullmatch(r"https?://\S+", s):
        # URLだけの段落は、リンクにして独立した段落にする(自分の過去記事へのリンクなど)
        u = html.escape(s, quote=True)
        out.append('<p><a href="' + u + '">' + u + "</a></p>")
    elif s.startswith(">"):
        lines = [re.sub(r"^>\s?", "", l) for l in s.split("\n")]
        out.append("<blockquote><p>" + "<br>".join(inline(l) for l in lines) + "</p></blockquote>")
    elif s.startswith("### "):
        out.append("<h3>" + html.escape(s[4:]) + "</h3>")
    elif s.startswith("## "):
        out.append("<h2>" + html.escape(s[3:]) + "</h2>")
    elif s.startswith("# "):
        out.append("<h2>" + html.escape(s[2:]) + "</h2>")
    else:
        out.append("<p>" + inline(s).replace("\n", "<br>") + "</p>")

# --raw：日本語をUnicodeエスケープに変換せず、そのまま出す(出力が約4分の1になり、AIが扱うトークンが減る)。
# 付けない場合は従来どおりASCIIのみ(コンソールの文字コードに依存しない)
RAW = "--raw" in sys.argv[2:]
data = json.dumps({"html": "".join(out), "text": src}, ensure_ascii=not RAW)
js = (
    "(function(){const DATA=" + data + ";"
    "const eds=[...document.querySelectorAll('[contenteditable=\"true\"]')]"
    ".filter(x=>!(x.getAttribute('data-placeholder')||'').includes('\\u30bf\\u30a4\\u30c8\\u30eb'));"  # 'タイトル' をASCIIで表記(コンソールの文字コードに依存しない)
    "const e=eds.sort((a,b)=>b.offsetHeight-a.offsetHeight)[0];e.focus();"
    "const d=new DataTransfer();d.setData('text/html',DATA.html);d.setData('text/plain',DATA.text);"
    "e.dispatchEvent(new ClipboardEvent('paste',{clipboardData:d,bubbles:true,cancelable:true}));"
    "return e.innerText.length;})()"
)
sys.stdout.buffer.write((js + "\n").encode("utf-8"))
