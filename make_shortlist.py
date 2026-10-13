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
# 恋愛・人間関係・ブログ・SNS・AIの話ではないと分かっている話題の印（2026-10-13の試運転で混入を確認したもの）
NOISE = ["第五", "パスワード", "フィッシング", "集計結果", "アンケート", "ご協力", "血液型", "精神疾患", "ADHD", "発達障害"]
# アカウント別の「この分野の語」。本文にこの語が1つもない投稿は外す（本文が空の画像投稿は判断できないので残す）。
# 2026-10-13の試運転で、クエン酸・政治・訃報などの非関連の超バズが上位を占めたため追加。語は小文字で比べる。
TOPIC_TERMS = {
    "s4lv_UYA": [
        "ai", "claude", "chatgpt", "チャッピー", "gemini", "codex", "opus", "sonnet", "gpt", "llm", "copilot", "cursor",
        "生成", "プロンプト", "指示", "自動化", "スキル", "エージェント",
        "note", "ブログ", "seo", "アフィリ", "アドセンス", "サチコ", "検索流入", "記事",
        "sns", "threads", "スレッズ", "x運用", "インプレ", "アルゴリズム", "投稿", "運用", "副業",
    ],
    "MBTICODE": [
        "mbti", "16タイプ", "infj", "infp", "intj", "intp", "enfj", "enfp", "entj", "entp",
        "istj", "isfj", "estj", "esfj", "istp", "isfp", "estp", "esfp",
        "恋愛", "彼氏", "彼女", "好きな人", "片思い", "脈あり", "未練", "浮気", "復縁", "既読", "line", "返信",
        "付き合", "結婚", "元彼", "元カノ", "デート", "告白", "相性", "愛着", "恋人", "パートナー",
    ],
}
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


def has_topic(low, terms):
    """本文（小文字）に分野の語があるか。URLは除き、英字の語は単語の境界で比べる（URLや他の語の一部に当たらないように）。"""
    t = re.sub(r"https?://\S+", " ", low)
    for w in terms:
        if re.fullmatch(r"[a-z0-9]+", w):
            if re.search(r"(?<![a-z0-9])" + re.escape(w) + r"(?![a-z0-9])", t):
                return True
        elif w in t:
            return True
    return False


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
    ap.add_argument("--max-per-keyword", type=int, default=6, help="1つのキーワードから取る最大件数（偏りを防ぐ）")
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
        ex = {"投稿が古い": 0, "古い": 0, "反響小": 0, "自分のアカウント": 0, "勧誘など": 0, "無関係な話題": 0, "関連語なし": 0,
              "既出": 0, "同じ投稿者": 0, "語の上限": 0}
        keep, per_author, kw_count = [], {}, {}
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
            elif any(w.lower() in low for w in NOISE):
                ex["無関係な話題"] += 1
            elif low.strip() and not has_topic(low, TOPIC_TERMS[account]):
                ex["関連語なし"] += 1
            elif post_code(r["url"]) in ledger_text:
                ex["既出"] += 1
            elif per_author.get(r["author"], 0) >= args.max_per_author:
                ex["同じ投稿者"] += 1
            else:
                # 1つの語に候補が偏らないよう、拾ったキーワードのうち、いま一番少ない語に数える
                kw = min(r["keywords"] or [""], key=lambda x: kw_count.get(x, 0))
                if kw_count.get(kw, 0) >= args.max_per_keyword:
                    ex["語の上限"] += 1
                else:
                    kw_count[kw] = kw_count.get(kw, 0) + 1
                    per_author[r["author"]] = per_author.get(r["author"], 0) + 1
                    keep.append(r)
        keep = keep[: args.top]

        lines = [
            "# 今週の候補：%s（%s）" % (account, today),
            "",
            "- 対象グループ：%s ／ 元のデータ：%d件 → 候補 **%d件**" % ("・".join(groups), len(pool), len(keep)),
            "- 選び方：反響点＝いいね＋再投稿×3＋返信×2＋保存×5（保存はXだけ）。同じ投稿者は最大%d件、1つの語から最大%d件。いいね%d以上。最後に見かけた日が%d日以内" % (args.max_per_author, args.max_per_keyword, args.min_likes, args.days),
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
