"""溜めた投稿から、アカウント別の「今週の候補」ファイルを作る（Claudeのトークンは使わない）。

使い方：  py -3 make_shortlist.py                  研究データ全部から、アカウント別に作る
          py -3 make_shortlist.py --top 20 --max-age-hours 24
出力：    research_data/shortlist/shortlist_<アカウント>_<日付>.md
          - MBTICODE ……… mbti_love グループ（/mbticode-neta が読む入力）
          - s4lv_UYA ……… blog_note_sns・ai グループ（/neta-research が読む入力。s4lvとUYA.共通）

新しさ：  **集めた時点（初めて見かけた時点）で、投稿から24時間以内**のものだけを候補にする
          （アカウント起点は5日以内。約4日で一周するため）。集めてから7日分を蓄積して並べる
          （週1回のリサーチで、1週間分を見られるように）。
選び方：  反響点 = いいね＋再投稿×3＋返信×2＋保存×5（保存はXだけ）
          勢い = 反響点 ÷（投稿から最後に見かけるまでの日数＋1）。短い時間で伸びたものを上に並べる
除外：    ①すでに台帳にある投稿（投稿IDで判定） ②勧誘・配布・募集・販売など ③自分のアカウント
          ④反響が小さいもの ⑤この分野の語がない・無関係な話題 ⑥同じ投稿者・同じ語の偏り
注意：    本文の抜粋は、ローカルだけに置く（research_data は git に入れない）。台帳には全文を写さない。
"""
import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
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
                for k in ("posted_at", "followers", "source", "min_faves"):
                    if k in r and k not in old:
                        old[k] = r[k]
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
    """本文の先頭に「2026/07/10」のような日付があれば、その日を返す（古いスレッズのデータ用）。"""
    for t in (r.get("time_label", ""), r.get("text", "")):
        m = re.match(r"\s*(20\d{2})/(\d{1,2})/(\d{1,2})", t)
        if m:
            try:
                return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                return None
    return None


def posted_at(r):
    """投稿された日時（この PC の時刻）。分からなければ None。"""
    if r.get("posted_at"):
        try:
            return datetime.fromisoformat(r["posted_at"])
        except ValueError:
            pass
    tl = r.get("time_label", "")
    m = re.match(r"(\d{4})/(\d{1,2})/(\d{1,2}) (\d{1,2}):(\d{2})$", tl)
    if m and r.get("platform") == "x":  # 古いXのデータ：時刻はUTCで保存していた
        utc = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), tzinfo=timezone.utc)
        return utc.astimezone().replace(tzinfo=None)
    return post_date(r)


def hours_at(r, key):
    """投稿から、first_seen（初めて見かけた）／last_seen（最後に見かけた）までの時間。分からなければ None。"""
    p = posted_at(r)
    if p is None:
        return None
    try:
        t = datetime.fromisoformat(r[key])
    except (KeyError, ValueError):
        return None
    return max(0.0, (t - p).total_seconds() / 3600.0)


def score(r):
    # 既存スキルの優先順位「ブックマーク＞返信＞いいね」に合わせる（ブックマークはXだけ取れる）
    return r["likes"] + 3 * r["reposts"] + 2 * r["replies"] + 5 * r.get("bookmarks", 0)


def momentum(r):
    """勢い＝反響点÷(投稿から最後に見かけるまでの日数＋1)。短い時間で伸びたものが上に来る。日時が分からない古いデータは2日扱い。"""
    h = hours_at(r, "last_seen")
    days = (h / 24.0) if h is not None else 2.0
    return score(r) / (days + 1.0)


def age_limit_hours(r, args):
    return args.max_age_account_hours if r.get("source") == "account" else args.max_age_hours


def min_likes_for(r, args):
    if r.get("source") == "account":
        return r.get("min_faves", args.min_likes_x)  # そのアカウントのしきい値（watch_accounts.json）
    return args.min_likes_x if r.get("platform") == "x" else args.min_likes_threads


def pick_with_quota(keep, top, quota):
    """媒体ごとに最低 quota 件（あれば）を確保してから、残りを勢いの順に埋める。"""
    chosen = []
    for plat in ("x", "threads"):
        same = [r for r in keep if (r.get("platform") == "x") == (plat == "x")]
        chosen += same[:quota]
    ids = {id(r) for r in chosen}
    chosen += [r for r in keep if id(r) not in ids][: max(0, top - len(chosen))]
    return sorted(chosen, key=momentum, reverse=True)[:top]


def one_line(text, n=80):
    t = re.sub(r"\s+", " ", text).strip()
    return t[:n] + ("…" if len(t) > n else "")


def label_hours(h):
    if h is None:
        return "不明"
    return "%d分" % round(h * 60) if h < 1 else "%.0f時間" % h if h < 48 else "%.0f日" % (h / 24)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=30, help="1ファイルの最大件数")
    ap.add_argument("--min-likes-x", type=int, default=100, help="X：これ未満のいいねは候補にしない")
    ap.add_argument("--min-likes-threads", type=int, default=100, help="スレッズ：これ未満のいいねは候補にしない")
    ap.add_argument("--max-age-hours", type=int, default=24, help="集めた時点で、投稿からこの時間以内のものだけ候補にする")
    ap.add_argument("--max-age-account-hours", type=int, default=120, help="アカウント起点の投稿：同上（約4日で一周するため5日）")
    ap.add_argument("--window-days", type=int, default=7, help="この日数以内に集めたものを蓄積して並べる（週1回のリサーチ用）")
    ap.add_argument("--max-per-author", type=int, default=2)
    ap.add_argument("--max-per-keyword", type=int, default=6, help="1つのキーワードから取る最大件数（偏りを防ぐ）")
    ap.add_argument("--min-per-platform", type=int, default=10, help="媒体ごとの最低枠（その媒体の候補がある場合）")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    files = sorted(DATA_DIR.glob("threads_*.jsonl")) + sorted(DATA_DIR.glob("x_posts*.jsonl"))
    if not files:
        sys.exit("研究データがありません。先に collect_threads.py を実行してください。")
    posts = load_posts(files)
    ledger_text = "\n".join(p.read_text(encoding="utf-8") for p in LEDGERS if p.exists())
    window_start = (datetime.now() - timedelta(days=args.window_days)).isoformat(timespec="seconds")
    today = datetime.now().strftime("%Y-%m-%d")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for account, groups in VIEWS.items():
        pool = [r for r in posts if set(r["groups"]) & set(groups)]
        ex = {"集めたのが古い": 0, "投稿が古い": 0, "反響小": 0, "自分のアカウント": 0, "勧誘など": 0, "無関係な話題": 0,
              "関連語なし": 0, "既出": 0, "同じ投稿者": 0, "語の上限": 0}
        keep, per_author, kw_count = [], {}, {}
        for r in sorted(pool, key=momentum, reverse=True):
            low = r["text"].lower()
            h_first = hours_at(r, "first_seen")
            if r["first_seen"] < window_start:
                ex["集めたのが古い"] += 1
            elif (h_first if h_first is not None else 48.0) > age_limit_hours(r, args):
                ex["投稿が古い"] += 1  # 集めた時点で、投稿から24時間より経っていたもの（日時が分からない古いデータも含む）
            elif r["likes"] < min_likes_for(r, args):
                ex["反響小"] += 1  # アカウント起点の投稿は、そのアカウントのしきい値（watch_accounts.json）で判定
            elif r["author"].lower() in OWN_AUTHORS:
                ex["自分のアカウント"] += 1
            elif any(w.lower() in low for w in SOLICIT):
                ex["勧誘など"] += 1
            elif any(w.lower() in low for w in NOISE):
                ex["無関係な話題"] += 1
            elif r.get("source") != "account" and low.strip() and not has_topic(low, TOPIC_TERMS[account]):
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
        keep = pick_with_quota(keep, args.top, args.min_per_platform)

        lines = [
            "# 今週の候補：%s（%s）" % (account, today),
            "",
            "- 対象グループ：%s ／ 元のデータ：%d件 → 候補 **%d件**" % ("・".join(groups), len(pool), len(keep)),
            "- 新しさ：**集めた時点で、投稿から%d時間以内**（アカウント起点は%d時間以内）のものだけ。集めてから%d日分を蓄積して並べている" % (
                args.max_age_hours, args.max_age_account_hours, args.window_days),
            "- 並び順：**勢い**＝反響点÷(投稿から最後に見かけるまでの日数＋1)。反響点＝いいね＋再投稿×3＋返信×2＋保存×5（保存はXだけ）",
            "- 絞り込み：同じ投稿者は最大%d件、1つの語から最大%d件、媒体ごとに最低%d件（あれば）。いいね：Xは%d以上・スレッズは%d以上（アカウント起点は各アカウントのしきい値）" % (
                args.max_per_author, args.max_per_keyword, args.min_per_platform, args.min_likes_x, args.min_likes_threads),
            "- 除外の内訳：" + "、".join("%s %d" % (k, v) for k, v in ex.items()),
            "- この表は、本文の冒頭だけを載せたローカル用のメモです。台帳には、URL・型・数字だけを書く（全文は写さない）",
            "",
            "| # | 媒体 | 勢い | 反響点 | いいね | 返信 | 再投稿 | 保存数 | 保存率 | 表示数 | 投稿日 | 集めた時の経過 | 投稿者 | フォロワー | 拾ったキーワード | 本文の冒頭 | URL |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        for i, r in enumerate(keep, 1):
            p = posted_at(r)
            has_bm = "bookmarks" in r
            rate = ("%.2f%%" % (100.0 * r["bookmarks"] / r["views"])) if has_bm and r.get("views") else "−"
            lines.append("| %d | %s | %d | %d | %d | %d | %d | %s | %s | %s | %s | %s | @%s | %s | %s | %s | %s |" % (
                i, "X" if r.get("platform") == "x" else "スレッズ", momentum(r), score(r), r["likes"], r["replies"], r["reposts"],
                (str(r["bookmarks"]) if has_bm else "−"), rate,
                ("{:,}".format(r["views"]) if r.get("views") else "−"),
                p.strftime("%Y-%m-%d") if p else "−", label_hours(hours_at(r, "first_seen")),
                r["author"], ("{:,}".format(r["followers"]) if r.get("followers") else "−"),
                "／".join(r["keywords"][:3]),
                one_line(r["text"]).replace("|", "｜") or "（本文なし・画像）", r["url"]))
        path = OUT_DIR / ("shortlist_%s_%s.md" % (account, today))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("%s：%d件 → %s（除外：%s）" % (account, len(keep), path.relative_to(ROOT),
              "、".join("%s%d" % (k, v) for k, v in ex.items() if v)))


if __name__ == "__main__":
    main()
