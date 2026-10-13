"""溜めた投稿から、アカウント別の「今週の候補」ファイルを作る（Claudeのトークンは使わない）。

使い方：  py -3 make_shortlist.py                  研究データ全部から、アカウント別に作る
          py -3 make_shortlist.py --top 20 --min-likes 200
出力：    research_data/shortlist/shortlist_<アカウント>_<日付>.md
          - MBTICODE ……… mbti_love グループ（/mbticode-neta が読む入力）
          - s4lv_UYA ……… blog_note_sns・ai グループ（/neta-research が読む入力。s4lvとUYA.共通）

選び方：  反響点 = いいね＋再投稿×3＋返信×2。同じ投稿者は最大2件。
除外：    ①すでに台帳にある投稿（投稿IDで判定） ②勧誘・配布・募集・販売など
          ③自分のアカウント ④反響が小さいもの（既定は100いいね未満）
注意：    本文の抜粋は、ローカルだけに置く（research_data は git に入れない）。台帳には全文を写さない。
"""
import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "research_data"
OUT_DIR = DATA_DIR / "shortlist"

VIEWS = {
    "MBTICODE": ["mbti_love"],
    "s4lv_UYA": ["blog_note_sns", "ai"],
}
# すでに使った・集めた投稿の記録（ここに投稿IDがあれば「既出」として除く）
LEDGERS = [
    ROOT / "brands/mbticode/analysis/neta/neta_ledger.md",
    ROOT / "brands/mbticode/analysis/neta/neta_sources.md",
    ROOT / "journals/external_seeds.md",
]
OWN_AUTHORS = {"mbti_code", "mbticode", "cfrms4lv", "s4lv", "uyadott"}
# 勧誘・配布・募集・販売などの印（見つかったら除外）。多すぎて困るときは見直す
SOLICIT = [
    "公式LINE", "LINE登録", "LINEに登録", "LINEで受け取", "プレゼント", "無料配布", "配布中", "受け取り方",
    "DMで", "DMください", "DMして", "コメントで「", "コメントに「", "「」と送", "モニター", "募集", "紹介パートナー",
    "wtb", "api key", "販売", "購入はこちら", "申し込み", "無料相談", "プロフのリンク", "プロフから",
]


def post_code(url):
    return url.rstrip("/").split("/")[-1]


def load_posts(files):
    merged = {}
    for f in files:
        # splitlines()は本文中の特殊な行区切り（U+2028等）でも切れるので使わない
        for line in f.read_text(encoding="utf-8").split(chr(10)):
            if not line.strip():
                continue
            r = json.loads(line)
            old = merged.get(r["url"])
            if old is None:
                merged[r["url"]] = r
            else:  # 数字は大きいほうを残し、キーワード・グループは足す
                for k in ("likes", "replies", "reposts"):
                    old[k] = max(old.get(k, 0), r.get(k, 0))
                old["views"] = max(old.get("views", 0), r.get("views", 0))
                if "bookmarks" in r or "bookmarks" in old:
                    old["bookmarks"] = max(old.get("bookmarks", 0), r.get("bookmarks", 0))
                old["groups"] = sorted(set(old["groups"]) | set(r["groups"]))
                old["keywords"] = sorted(set(old["keywords"]) | set(r["keywords"]))
                old["last_seen"] = max(old["last_seen"], r["last_seen"])
                old["first_seen"] = min(old["first_seen"], r["first_seen"])
    return list(merged.values())


def post_date(r):
    """本文の先頭に「2026/07/10」のような日付があれば、その日を返す（相対表示の新しい投稿は None）。"""
    for t in (r.get("time_label", ""), r.get("text", "")):
        m = re.match(r"\s*(20\d{2})/(\d{1,2})/(\d{1,2})", t)
        if m:
            try:
                return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                return None
    return None


def score(r):
    # 既存スキルの優先順位「ブックマーク＞返信＞いいね」に合わせる（ブックマークはXだけ取れる）
    return r["likes"] + 3 * r["reposts"] + 2 * r["replies"] + 5 * r.get("bookmarks", 0)


def one_line(text, n=80):
    t = re.sub(r"\s+", " ", text).strip()
    return t[:n] + ("…" if len(t) > n else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=30, help="1ファイルの最大件数")
    ap.add_argument("--min-likes", type=int, default=100, help="これ未満のいいねは候補にしない")
    ap.add_argument("--days", type=int, default=14, help="この日数より古く見かけた投稿は除く（最後に見かけた日で判定）")
    ap.add_argument("--max-per-author", type=int, default=2)
    ap.add_argument("--max-age-days", type=int, default=60, help="投稿日が分かる投稿は、この日数より古ければ除く（0で無効）")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    files = sorted(DATA_DIR.glob("threads_*.jsonl")) + sorted(DATA_DIR.glob("x_posts*.jsonl"))
    if not files:
        sys.exit("研究データがありません。先に collect_threads.py を実行してください。")
    posts = load_posts(files)
    ledger_text = "\n".join(p.read_text(encoding="utf-8") for p in LEDGERS if p.exists())
    cutoff = (datetime.now() - timedelta(days=args.days)).isoformat(timespec="seconds")
    today = datetime.now().strftime("%Y-%m-%d")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for account, groups in VIEWS.items():
        pool = [r for r in posts if set(r["groups"]) & set(groups)]
        ex = {"投稿が古い": 0, "古い": 0, "反響小": 0, "自分のアカウント": 0, "勧誘など": 0, "既出": 0, "同じ投稿者": 0}
        keep, per_author = [], {}
        for r in sorted(pool, key=score, reverse=True):
            low = r["text"].lower()
            pd = post_date(r)
            if args.max_age_days and pd and (datetime.now() - pd).days > args.max_age_days:
                ex["投稿が古い"] += 1
            elif r["last_seen"] < cutoff:
                ex["古い"] += 1
            elif r["likes"] < args.min_likes:
                ex["反響小"] += 1
            elif r["author"].lower() in OWN_AUTHORS:
                ex["自分のアカウント"] += 1
            elif any(w.lower() in low for w in SOLICIT):
                ex["勧誘など"] += 1
            elif post_code(r["url"]) in ledger_text:
                ex["既出"] += 1
            elif per_author.get(r["author"], 0) >= args.max_per_author:
                ex["同じ投稿者"] += 1
            else:
                per_author[r["author"]] = per_author.get(r["author"], 0) + 1
                keep.append(r)
        keep = keep[: args.top]

        lines = [
            "# 今週の候補：%s（%s）" % (account, today),
            "",
            "- 対象グループ：%s ／ 元のデータ：%d件 → 候補 **%d件**" % ("・".join(groups), len(pool), len(keep)),
            "- 選び方：反響点＝いいね＋再投稿×3＋返信×2＋保存×5（保存はXだけ）。同じ投稿者は最大%d件。いいね%d以上。最後に見かけた日が%d日以内" % (args.max_per_author, args.min_likes, args.days),
            "- 除外の内訳：" + "、".join("%s %d" % (k, v) for k, v in ex.items()),
            "- この表は、本文の冒頭だけを載せたローカル用のメモです。台帳には、URL・型・数字だけを書く（全文は写さない）",
            "",
            "| # | 媒体 | 反響点 | いいね | 返信 | 再投稿 | 保存数 | 保存率 | 表示数 | 投稿日 | 投稿者 | 拾ったキーワード | 本文の冒頭 | URL |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        for i, r in enumerate(keep, 1):
            pd = post_date(r)
            has_bm = "bookmarks" in r
            rate = ("%.2f%%" % (100.0 * r["bookmarks"] / r["views"])) if has_bm and r.get("views") else "−"
            lines.append("| %d | %s | %d | %d | %d | %d | %s | %s | %s | %s | @%s | %s | %s | %s |" % (
                i, "X" if r.get("platform") == "x" else "スレッズ", score(r), r["likes"], r["replies"], r["reposts"],
                (str(r["bookmarks"]) if has_bm else "−"), rate,
                ("{:,}".format(r["views"]) if r.get("views") else "−"),
                pd.strftime("%Y-%m-%d") if pd else "直近",
                r["author"], "／".join(r["keywords"][:3]),
                one_line(r["text"]).replace("|", "｜") or "（本文なし・画像）", r["url"]))
        path = OUT_DIR / ("shortlist_%s_%s.md" % (account, today))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("%s：%d件 → %s（除外：%s）" % (account, len(keep), path.relative_to(ROOT),
              "、".join("%s%d" % (k, v) for k, v in ex.items() if v)))


if __name__ == "__main__":
    main()
