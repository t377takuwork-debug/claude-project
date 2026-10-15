"""バズ投稿の分析材料を、溜めたXの投稿データから取り出して画面に出す（buzz-why の第1段階。Claudeのトークンは使わない）。

使い方：  py -3 .claude/skills/buzz-why/select_posts.py [--top 10] [--accounts 3] [--post-days 7] [--min-text 30]
                [--min-followers 100] [--max-followers 100000] [--days 7] [--min-likes 100] [--url URL ...]
出力：    画面に出すだけ（保存しない）。他人の投稿の全文を、リポジトリに保存しないため。
読む元：  research/data/x_posts.jsonl（gitに入らない。毎日の自動収集が溜める）
選び方：  ①観察対象アカウントの投稿を、最大 --accounts 件（そのアカウントのしきい値で拾ったもの。勢いの順）
          ②残りを、「勢い」上位と「フォロワーの割に伸びた比率」上位で半分ずつ
          同じ投稿者は1件まで。重複は1つに。
外すもの：分野の語がない（観察対象は除く）・勧誘・ノイズ・他人への返信・投稿日が --post-days 日より前・
          本文がURLを除いて --min-text 字未満（題名とリンクだけで、文章からは分析できない）・
          すでに分析した、または在庫に登録した投稿（3_広報部/バズ分析/ と 0_社長室/ネタ在庫.md にURLがあるもの）
          --url を付けると、その投稿だけを出す（選び方・外すものは使わない）。
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
S4LV = Path(__file__).resolve().parents[3]  # S4LVnote/
ROOT = S4LV.parent  # claude project/
sys.path.insert(0, str(ROOT / "research"))
import make_shortlist as m  # noqa: E402  分野の語・ノイズ・勧誘の印を、毎日の収集と同じにする

TREE_MARKS = ["🧵", "↓", "👇", "続き", "スレッド", "ツリー", "(1/", "1/", "手順を", "シェアします", "まとめました"]
DONE_FILES = [S4LV / "0_社長室" / "ネタ在庫.md"] + sorted((S4LV / "3_広報部" / "バズ分析").glob("*.md"))


def num(s):
    try:
        return float(str(s).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def length(text):
    return len(re.sub(r"https?://\S+", "", text).replace("\n", "").strip())


def parse_dt(s):
    try:
        return datetime.fromisoformat(s)
    except (TypeError, ValueError):
        return None


def post_id(url):
    return url.rstrip("/").split("/")[-1]


def build(d):
    li, rp, rt, bm, v, f = (num(d.get(k)) or 0 for k in ("likes", "replies", "reposts", "bookmarks", "views", "followers"))
    pts = li + rt * 3 + rp * 2 + bm * 5
    t0, t1 = parse_dt(d.get("posted_at")), parse_dt(d.get("last_seen"))
    days = max((t1 - t0).total_seconds() / 86400, 0) if t0 and t1 else 1
    text = d["text"]
    return {
        "url": d["url"], "author": d["author"], "followers": f, "likes": li, "replies": rp, "reposts": rt,
        "bookmarks": bm, "views": v, "pts": pts, "momentum": pts / (days + 1),
        "ratio": pts / f if f >= 1 else 0, "reach": v / f if f >= 1 and v else 0,
        "bm_rate": 100 * bm / v if v else 0, "rp_rate": 100 * rp / v if v else 0,
        "rt_rate": 100 * rt / v if v else 0, "like_rate": 100 * li / v if v else 0,
        "len": length(text), "lines": len([x for x in text.split("\n") if x.strip()]),
        "first_len": length(text.split("\n")[0]), "has_url": "http" in text,
        "tree": [k for k in TREE_MARKS if k in text], "posted": (d.get("posted_at") or "")[:10], "text": text,
        "account": d.get("source") == "account", "min_faves": d.get("min_faves"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--accounts", type=int, default=3, help="観察対象アカウントの投稿の枠（最大件数）")
    ap.add_argument("--post-days", type=int, default=7, help="投稿日が、この日数より前のものは外す")
    ap.add_argument("--min-text", type=int, default=30, help="本文がURLを除いてこの字数未満のものは外す")
    ap.add_argument("--min-followers", type=int, default=100)
    ap.add_argument("--max-followers", type=int, default=100000, help="これを超えるアカウントは外す（大手・公式は、真似できない規模のため）")
    ap.add_argument("--min-likes", type=int, default=100, help="語で拾った投稿のいいね下限（観察対象は、そのアカウントのしきい値）")
    ap.add_argument("--days", type=int, default=7, help="最後に見かけてから、何日以内の投稿か")
    ap.add_argument("--url", nargs="*", help="このURL（またはID）の投稿だけを出す")
    a = ap.parse_args()

    done_text = "\n".join(p.read_text(encoding="utf-8") for p in DONE_FILES if p.exists())
    terms = m.TOPIC_TERMS["s4lv_UYA"]
    rows, now = [], datetime.now()
    ex = {"分野外・勧誘・ノイズ・返信": 0, "投稿が古い": 0, "本文が短い（題名とリンクだけ）": 0, "分析済み・登録済み": 0, "規模・反響の条件": 0}
    for line in (ROOT / "research" / "data" / "x_posts.jsonl").open(encoding="utf-8"):
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if a.url:
            if any(post_id(u) == post_id(d["url"]) for u in a.url):
                rows.append(build(d))
            continue
        ls = parse_dt(d.get("last_seen"))
        if ls and (now - ls).days > a.days:
            continue
        if not set(d.get("groups") or []) & set(m.VIEWS["s4lv_UYA"]):
            continue  # MBTICODE 向けの語・観察対象で拾った投稿は見ない
        r = build(d)
        t = d["text"].lower()
        if not r["account"] and (r["followers"] < a.min_followers or r["followers"] > a.max_followers or r["likes"] < a.min_likes):
            ex["規模・反響の条件"] += 1
            continue
        if d["text"].startswith("@") or any(n.lower() in t for n in m.NOISE) or any(s.lower() in t for s in m.SOLICIT) \
                or (not r["account"] and not any(m.term_in(x, t) for x in terms)):
            ex["分野外・勧誘・ノイズ・返信"] += 1
            continue
        pdt = parse_dt(d.get("posted_at"))
        if not pdt or (now - pdt).days >= a.post_days:
            ex["投稿が古い"] += 1
            continue
        if r["len"] < a.min_text:
            ex["本文が短い（題名とリンクだけ）"] += 1
            continue
        if post_id(d["url"]) in done_text:
            ex["分析済み・登録済み"] += 1
            continue
        rows.append(r)

    if not a.url:
        chosen, seen_url, seen_author = [], set(), set()

        def take(pool, n):
            for r in pool:
                if n <= 0:
                    break
                if r["url"] in seen_url or r["author"] in seen_author:
                    continue
                seen_url.add(r["url"])
                seen_author.add(r["author"])
                chosen.append(r)
                n -= 1

        take(sorted([r for r in rows if r["account"]], key=lambda r: -r["momentum"]), a.accounts)
        rest = a.top - len(chosen)
        others = [r for r in rows if not r["account"]]
        take(sorted(others, key=lambda r: -r["momentum"]), (rest + 1) // 2)
        take(sorted(others, key=lambda r: -r["ratio"]), a.top - len(chosen))
        rows = chosen

    if not a.url:
        print("外した件数：" + "、".join("%s %d" % (k, v) for k, v in ex.items()))
    print("対象 %d 件（読んだ元：x_posts.jsonl）\n" % len(rows))
    for i, r in enumerate(rows, 1):
        print("=" * 60)
        print("【%d】@%s%s  %s  投稿日 %s" % (i, r["author"], "（観察対象・しきい値%s）" % r["min_faves"] if r["account"] else "",
                                         r["url"], r["posted"]))
        print("数字：フォロワー%d／いいね%d／再投稿%d／返信%d／保存%d／表示%d" % (
            r["followers"], r["likes"], r["reposts"], r["replies"], r["bookmarks"], r["views"]))
        print("比率：反響点÷フォロワー %.1f／表示÷フォロワー %.0f／保存率 %.2f%%／返信率 %.3f%%／再投稿率 %.2f%%／いいね率 %.2f%%" % (
            r["ratio"], r["reach"], r["bm_rate"], r["rp_rate"], r["rt_rate"], r["like_rate"]))
        print("形：%d字（URL除く）／%d行／1行目 %d字／本文にURL %s／ツリーの印 %s" % (
            r["len"], r["lines"], r["first_len"], "あり" if r["has_url"] else "なし", "、".join(r["tree"]) or "なし"))
        print("---本文---")
        print(r["text"])
        print()


if __name__ == "__main__":
    main()
