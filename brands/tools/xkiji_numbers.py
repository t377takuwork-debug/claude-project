#!/usr/bin/env python3
"""X記事の数字の確認(s4lv・UYA.共通)。

投稿やQ&Aに出てくる「数字＋単位」(21年・5,000円・10%・30記事 など)のうち、
X記事の原文(journals/X記事/原文/)にあって、そのアカウントの記録にないものを知らせる。
X記事の書き手の経歴・実績・例の数字を、自分のこととして出さないための確認。

使い方:
    python brands/tools/xkiji_numbers.py <ファイル> --account uya|s4lv|both
各アカウントの機械チェック(UYAnote の qa_post_x.py・S4LVnote の qa_post.py)からも呼ばれる。

判定: お金(円)・割合(%)・「万」がつくもの・10以上の数は ERROR。それ以外(1日・3本 など、よく使う小さな数)は WARN。
ERROR が1件でもあれば exit code 1。
"""
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTICLES_DIR = ROOT / "journals" / "X記事" / "原文"

# アカウントの記録(ここにある数字は、自分のこととして使ってよい)
RECORDS = {
    "uya": [
        "UYAnote/0_社長室/UYA設定/personal_data.md",
        "UYAnote/0_社長室/X投稿の本音メモ.md",
        "UYAnote/2_商品開発部/公開済み/*.md",
        "journals/daily/*.md",
    ],
    "s4lv": [
        "S4LVnote/0_社長室/S4LV設定/personal_data.md",
        "S4LVnote/0_社長室/x_neta_daicho.md",
        "S4LVnote/0_社長室/s4lv_learnings.md",
        "journals/daily/*.md",
    ],
}

NUM_RE = re.compile(
    r"(?<!\d)(\d+(?:,\d{3})*)\s*(万|千)?\s*"
    r"(円|%|年|か月|ヶ月|カ月|週間|週|日|時間|分|記事|本|件|人|回|倍|位|PV|部)"
)
UNIT_SAME = {"ヶ月": "か月", "カ月": "か月", "週間": "週"}

_cache = {}


def tokens(text):
    """文章から「数字＋単位」を取り出し、表記をそろえた集合で返す。"""
    t = unicodedata.normalize("NFKC", text or "")
    out = set()
    for m in NUM_RE.finditer(t):
        value = m.group(1).replace(",", "")
        unit = UNIT_SAME.get(m.group(3), m.group(3))
        out.add((value, m.group(2) or "", unit))
    return out


def _read(path):
    try:
        return path.read_text(encoding="utf-8-sig")
    except Exception:
        return ""


def article_tokens():
    if "articles" not in _cache:
        s = set()
        for p in sorted(ARTICLES_DIR.glob("*.md")):
            text = _read(p)
            # 先頭の管理メモ(「---」の行まで)は除く
            parts = re.split(r"^---[ \t]*$", text, maxsplit=1, flags=re.M)
            s |= tokens(parts[1] if len(parts) == 2 else text)
        _cache["articles"] = s
    return _cache["articles"]


def record_tokens(account):
    key = "rec:" + account
    if key not in _cache:
        accounts = ["uya", "s4lv"] if account == "both" else [account]
        s = set()
        for a in accounts:
            for pattern in RECORDS[a]:
                for p in ROOT.glob(pattern):
                    s |= tokens(_read(p))
        _cache[key] = s
    return _cache[key]


def _level(value, man, unit):
    try:
        big = float(value) >= 10
    except ValueError:
        big = False
    return "ERROR" if unit in ("円", "%") or man or big else "WARN"


def check(text, account):
    """(level, message) のリストを返す。X記事の原文が無ければ、何も返さない。"""
    arts = article_tokens()
    if not arts:
        return []
    recs = record_tokens(account)
    msgs = []
    for value, man, unit in sorted(tokens(text) & arts):
        if (value, man, unit) in recs:
            continue
        word = f"{value}{man}{unit}"
        msgs.append((_level(value, man, unit), f"「{word}」はX記事の原文にあり、自分の記録にない数字(書き手の数字を自分のこととして出していないか)"))
    return msgs


def main():
    args = sys.argv[1:]
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if len(args) != 3 or args[1] != "--account" or args[2] not in ("uya", "s4lv", "both"):
        print("使い方: python brands/tools/xkiji_numbers.py <ファイル> --account uya|s4lv|both")
        sys.exit(2)
    msgs = check(_read(Path(args[0])), args[2])
    for level, m in msgs:
        print(f"[{level}] {m}")
    n_err = sum(1 for lv, _ in msgs if lv == "ERROR")
    if msgs:
        print("直し方: 自分の記録にある数字に置き換えるか、数字を外す(考えだけを使う)")
    print(f"=== X記事の数字の確認: ERROR {n_err}件 / WARN {len(msgs) - n_err}件 ===")
    sys.exit(1 if n_err else 0)


if __name__ == "__main__":
    main()
