#!/usr/bin/env python3
"""
recent_forms.py — 直近の投稿の「形・入り方・終わり・長さ・問い」を一覧し、
使っていない形と偏りを出す。あわせて、最近使ったネタを一覧にする（s4lv 投稿を作る前の確認用）。

目的：
  ・投稿が毎回同じ形・同じ問い・同じ語尾にならないようにする（rules/s4lv_voice.md「ばらつきの決まり」）
  ・同じネタを続けて使わないようにする（rules/sns_common_rules.md「ネタを選ぶ順番」）

使い方：
  python .claude/hooks/recent_forms.py                 # X・Threads それぞれ直近10本＋最近使ったネタ
  python .claude/hooks/recent_forms.py --n 8 --platform x
  python .claude/hooks/recent_forms.py --days 45       # 最近使ったネタを見る日数（既定30日）

見出しのタグ：【...／形：リスト／入り方：困りごと／終わり：断言】
タグが無い古い投稿は、本文から分かる項目（文字数・問い・語尾・1行目）だけ出す。
最近使ったネタは、見出しの台帳の番号（K◯・A◯）・「柱3」・「ジャーナル」・Note記事への誘導を拾う。
posts/ の今のファイルと、posts/archive/ の過去分の両方を見る。
"""
import argparse
import datetime
import re
import sys
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HOOKS = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS))
from qa_post import parse_posts  # noqa: E402

POSTS_DIR = HOOKS.parents[1] / "3_広報部" / "投稿文"
ARCHIVE_DIR = POSTS_DIR / "archive"
FILES = {"x": POSTS_DIR / "posts_x.txt", "threads": POSTS_DIR / "posts_threads.txt"}

# 最近使ったネタ：見出しから拾うもの
NETA_CODE_RE = re.compile(r"(?<![A-Za-z0-9])([KA]\d{1,2})(?![0-9])")
HDR_DATE_RE = re.compile(r"(\d{1,2})/(\d{1,2})")

# 決まりの語彙（rules/s4lv_voice.md「形の引き出し」と同じ。変えたら両方直す）
FORMS = ["散文", "リスト", "段階", "物語", "話題所感", "問い", "見出し箇条書き", "矢印", "一言", "日常一言", "節目報告", "連投"]
OPENERS = ["困りごと", "事実", "自分の現場", "共通の現状", "外部の話", "物語", "他者の言葉", "呼びかけ", "見出し", "日常", "報告", "問い", "一言"]
ENDINGS = ["断言", "問い", "決意", "励まし", "保存促し", "引き", "笑い", "所感", "体言止め", "共感"]

TAG_RE = re.compile(r"／(形|入り方|終わり)：([^／】]+)")

QUESTION_FORMS = [
    ("ってことありません？", r"ってことありません？"),
    ("ありませんか？", r"ありませんか？"),
    ("ませんか？", r"ませんか？"),
    ("じゃないですか？", r"じゃないですか？"),
    ("〜ない？", r"ない？"),
    ("の人、いませんか？", r"いませんか？"),
]

ENDING_KINDS = [
    ("〜ました。", r"ました。$"),
    ("〜してます。", r"てます。$"),
    ("〜してる。", r"てる。$"),
    ("〜んですよ。", r"んですよ。$"),
    ("〜んだよね。", r"んだよね。$"),
    ("〜よね。", r"よね。$"),
    ("〜かな。", r"かな。$"),
    ("〜ます。", r"ます。$"),
    ("〜です。", r"です。$"),
    ("〜た。", r"た。$"),
    ("〜る。", r"る。$"),
    ("〜い。", r"い。$"),
]


def tags_of(header):
    d = {}
    for k, v in TAG_RE.findall(header):
        d[k] = v.strip()
    return d


def question_form(body):
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    for ln in lines:
        # 「」の中の？は問いかけではない（AIへの指示文など）
        plain = re.sub(r"「[^」]*」", "", ln)
        if plain.endswith("？") or plain.endswith("?"):
            for name, pat in QUESTION_FORMS:
                if re.search(pat, ln):
                    return name
            return "その他の問い"
    return ""


def ending_kind(body):
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    if not lines:
        return ""
    last = lines[-1]
    for name, pat in ENDING_KINDS:
        if re.search(pat, last):
            return name
    return "その他（体言止めなど）"


def has_numbered_list(body):
    return bool(re.search(r"^\s*\d+\.\s", body, re.M)) or bool(re.search(r"^\s*[・①-⑩]", body, re.M))


def first_line(body):
    for ln in body.splitlines():
        if ln.strip():
            return ln.strip()
    return ""


def summarize(posts):
    rows = []
    for p in posts:
        # is_reply は使わない（見出しの「会話・引用型」という反響ラベルの「引用」で誤判定されるため）
        body = p["body"]
        t = tags_of(p["header"])
        rows.append({
            "label": p["header"][:34],
            "form": t.get("形", "−"),
            "opener": t.get("入り方", "−"),
            "end": t.get("終わり", "−"),
            "chars": len(re.sub(r"\s", "", body)),
            "lines": len([ln for ln in body.splitlines() if ln.strip()]),
            "q": question_form(body),
            "list": has_numbered_list(body),
            "first": first_line(body)[:20],
            "ending": ending_kind(body),
        })
    return rows


def run_streak(values, n=3):
    """直近から数えて同じ値が n 回以上続いているか"""
    vals = [v for v in values if v and v != "−"]
    if len(vals) < n:
        return None
    tail = vals[-n:]
    return tail[0] if len(set(tail)) == 1 else None


def report(name, rows, n):
    rows = rows[-n:]
    print(f"\n=== {name}：直近{len(rows)}本（古い→新しい）===")
    if not rows:
        print("（投稿なし）")
        return
    for i, r in enumerate(rows, 1):
        print(f"{i:>2}. [{r['form']}/{r['opener']}/{r['end']}] {r['chars']}字・{r['lines']}行"
              f"・問い={r['q'] or 'なし'}・リスト={'あり' if r['list'] else 'なし'}・締め={r['ending']}")
        print(f"      1行目：{r['first']}")
    tagged = [r for r in rows if r["form"] != "−"]
    print("\n【数え（タグ付きの投稿のみ）】")
    for title, key in (("形", "form"), ("入り方", "opener"), ("終わり", "end")):
        c = Counter(r[key] for r in tagged)
        print(f"  {title}：" + ("、".join(f"{k}{v}" for k, v in c.most_common()) or "（タグなし）"))
    qc = Counter(r["q"] for r in rows if r["q"])
    print(f"  問いの形（全体）：" + ("、".join(f"{k}{v}" for k, v in qc.most_common()) or "なし"))
    ec = Counter(r["ending"] for r in rows)
    print(f"  締めの語尾（全体）：" + "、".join(f"{k}{v}" for k, v in ec.most_common()))

    print("\n【最近使っていない形（次に使う候補）】")
    used_f = {r["form"] for r in tagged}
    used_o = {r["opener"] for r in tagged}
    used_e = {r["end"] for r in tagged}
    print("  形：" + ("、".join(f for f in FORMS if f not in used_f) or "なし"))
    print("  入り方：" + ("、".join(o for o in OPENERS if o not in used_o) or "なし"))
    print("  終わり：" + ("、".join(e for e in ENDINGS if e not in used_e) or "なし"))

    warns = []
    for title, key in (("形", "form"), ("入り方", "opener"), ("終わり", "end")):
        s = run_streak([r[key] for r in rows], 3)
        if s:
            warns.append(f"{title}が「{s}」で3本続いている")
    s = run_streak([r["ending"] for r in rows], 3)
    if s:
        warns.append(f"締めの語尾が「{s}」で3本続いている")
    qrows = rows[-5:]
    qf = Counter(r["q"] for r in qrows if r["q"])
    for k, v in qf.items():
        if v >= 2:
            warns.append(f"直近5本で問いの形「{k}」が{v}回")
    q_ratio = sum(1 for r in rows if r["q"]) / len(rows)
    if q_ratio > 0.5:
        warns.append(f"問いのある投稿が{round(q_ratio*100)}%（半分以下にする）")
    lists = sum(1 for r in rows if r["list"])
    if lists > 2 and len(rows) <= 5:
        warns.append(f"番号・「・」のリストが{lists}本（直近5本で2本まで）")
    print("\n【偏りの注意】")
    print("  " + ("\n  ".join(warns) if warns else "なし"))


def all_posts(platform):
    """過去分（posts/archive/posts_<媒体>_*.txt）と今のファイルを、古い順につなげて返す。"""
    files = sorted(ARCHIVE_DIR.glob(f"posts_{platform}_*.txt")) + [FILES[platform]]
    posts = []
    for f in files:
        if f.exists():
            posts.extend(parse_posts(f.read_text(encoding="utf-8")))
    return posts


def neta_of(header):
    """見出しから、使ったネタの目印を拾う。"""
    keys = list(dict.fromkeys(NETA_CODE_RE.findall(header)))
    if "柱3" in header:
        keys.append("柱3（外の話題）")
    if "ジャーナル" in header:
        keys.append("ジャーナル")
    if "note_article_index" in header or "Note誘導" in header or "誘導の回" in header:
        keys.append("Note記事への誘導")
    return keys


def header_date(header, today):
    m = HDR_DATE_RE.search(header)
    if not m:
        return None
    try:
        d = datetime.date(today.year, int(m.group(1)), int(m.group(2)))
    except ValueError:
        return None
    if (d - today).days > 60:  # 年をまたいだ過去分
        d = d.replace(year=today.year - 1)
    return d


def report_neta(days):
    today = datetime.date.today()
    used, undated = {}, {}
    for plat, name in (("x", "X"), ("threads", "Threads")):
        for p in all_posts(plat):
            d = header_date(p["header"], today)
            keys = neta_of(p["header"])
            if d is None:
                if "未定" in p["header"]:  # 日付未定のストック
                    for k in keys:
                        undated.setdefault(k, set()).add(name)
                continue
            if (today - d).days > days:
                continue
            for k in keys:
                used.setdefault(k, set()).add((d, name))
    print(f"\n=== 最近使ったネタ（直近{days}日と予約分・XとThreadsの両方）===")
    if not used and not undated:
        print("（なし）")
        return

    def order(k):
        if k[0] in "KA" and k[1:].isdigit():
            return (0 if k[0] == "K" else 1, int(k[1:]))
        return (2, 0)

    for k in sorted(set(used) | set(undated), key=order):
        items = [f"{n} {d.month}/{d.day}" for d, n in sorted(used.get(k, ()), reverse=True)]
        items += [f"{n} 日付未定のストック" for n in sorted(undated.get(k, ()))]
        print(f"  {k}：" + "、".join(items))
    print("  ※ ここにあるネタは、同じ角度では使わない。台帳のネタがどれも既出なら、外の話題か音声ジャーナルへ進む")


def main():
    ap = argparse.ArgumentParser(description="直近の投稿の形・入り方・終わりと、最近使ったネタを見える化する")
    ap.add_argument("--n", type=int, default=10, help="見る本数（既定10）")
    ap.add_argument("--platform", choices=["x", "threads", "both"], default="both")
    ap.add_argument("--days", type=int, default=30, help="最近使ったネタを見る日数（既定30）")
    args = ap.parse_args()
    targets = ["x", "threads"] if args.platform == "both" else [args.platform]
    for t in targets:
        if not FILES[t].exists():
            print(f"（{FILES[t].name} が見つかりません）")
            continue
        report(t.upper(), summarize(all_posts(t)), args.n)
    report_neta(args.days)


if __name__ == "__main__":
    main()
