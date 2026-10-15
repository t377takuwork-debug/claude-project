"""溜めた投稿から、アカウント別の「今週の候補」ファイルを作る（Claudeのトークンは使わない）。

説明書：  docs/sop/sop_research_auto_collect.md
使い方：  py -3 research/make_shortlist.py
出力：    research/data/shortlist/shortlist_<アカウント>_<日付>.md（14日より古いものは自動で消す）
          - MBTICODE ……… mbti_love グループ（/mbticode-neta が読む入力）
          - s4lv_UYA ……… blog_note_sns・ai グループ（/neta-research が読む入力。s4lvとUYA.共通）

新しさ：  **集めた時点（初めて見かけた時点）で、投稿からX=24時間以内・スレッズ=48時間以内**のものだけ
          （アカウント起点は5日以内。約4日で一周するため）。集めてから7日分を蓄積して並べる。
選び方：  反響点 = いいね＋再投稿×3＋返信×2＋保存×5（保存はXだけ）
          勢い = 反響点 ÷（投稿から最後に見かけるまでの日数＋1）。短い時間で伸びたものを上に並べる
除外：    ①すでに台帳にある投稿（投稿IDで判定） ②勧誘・配布・募集・販売など ③自分のアカウント
          ④反響が小さいもの ⑤分野の語がない・無関係な話題 ⑥同じ投稿者・同じ語の偏り
          ⑦本文がほぼない（画像・リンクだけ）・他人への返信・日本語でない投稿
注意：    本文の抜粋は、ローカルだけに置く（research/data は git に入れない）。台帳には全文を写さない。
          意味の関連（その話題が運用に使えるか）は、機械では判定しきれない。週1回の仕分けで人とClaudeが見る。
"""
import argparse
import re
import sys
from datetime import datetime, timedelta

import research_common as rc

OUT_DIR = rc.DATA_DIR / "shortlist"
SOURCES = [rc.DATA_DIR / "threads_posts.jsonl", rc.DATA_DIR / "x_posts.jsonl"]

VIEWS = {
    "MBTICODE": ["mbti_love"],
    "s4lv_UYA": ["blog_note_sns", "ai", "save_pattern"],
}
# Xの語の検索のうち、保存数・保存率で選ぶグループ（2026-10-15。keywords.json に window_hours がある行だけ）
SAVE_GROUPS = {"blog_note_sns", "ai", "save_pattern"}
SAVE_MIN, SAVE_STRONG, SAVE_RATE = 50, 100, 0.5  # 保存50以上、かつ（保存100以上、または保存率0.5%以上）
# すでに使った・集めた投稿の記録（ここに投稿IDがあれば「既出」として除く）
LEDGERS = [
    rc.REPO / "brands/mbticode/analysis/neta/neta_ledger.md",
    rc.REPO / "brands/mbticode/analysis/neta/neta_sources.md",
    rc.REPO / "journals/external_seeds.md",
]
OWN_AUTHORS = {"mbti_code", "mbticode", "cfrms4lv", "s4lv", "uyadott"}
# 分野と無関係だと分かっている話題の印（2026-10-13の試運転で混入を確認したもの）
NOISE = ["第五", "パスワード", "フィッシング", "集計結果", "アンケート", "ご協力", "血液型", "精神疾患", "ADHD", "発達障害",
         "ガチャ", "二次創作", "ネップリ"]
# 勧誘・配布・募集・販売の印。「プレゼント」「募集」などの単語だけだと、恋愛の話（彼氏へのプレゼント）まで外すので、言い回しで見る
SOLICIT = [
    "公式LINE", "LINE登録", "LINEに登録", "LINEで受け取", "無料プレゼント", "プレゼント企画", "プレゼント中", "プレゼントします",
    "無料配布", "配布中", "配布します", "受け取り方", "DMで", "DMください", "DMして", "コメントで「", "コメントに「",
    "モニター募集", "募集中", "募集します", "紹介パートナー", "wtb", "api key", "販売中", "販売開始", "販売します",
    "購入はこちら", "お申し込み", "申し込みはこちら", "無料相談", "プロフのリンク", "プロフから",
]
# アカウント別の「この分野の語」（小文字で比べる）。本文にこの語がない投稿は外す
TOPIC_TERMS = {
    "s4lv_UYA": [
        "ai", "claude", "chatgpt", "チャッピー", "gemini", "codex", "opus", "sonnet", "gpt", "llm", "copilot", "cursor",
        "生成", "プロンプト", "自動化", "エージェント", "mcp", "aio", "llmo", "ai検索",
        "note", "ブログ", "seo", "アフィリ", "アドセンス", "サチコ", "検索流入", "記事", "ライティング",
        "sns", "threads", "スレッズ", "インプレ", "アルゴリズム", "フォロワー", "投稿", "運用", "発信", "副業",
    ],
    "MBTICODE": [
        "mbti", "16タイプ", "infj", "infp", "intj", "intp", "enfj", "enfp", "entj", "entp",
        "istj", "isfj", "estj", "esfj", "istp", "isfp", "estp", "esfp",
        "恋愛", "彼氏", "彼女", "好きな人", "片思い", "脈あり", "未練", "浮気", "復縁", "既読", "line", "返信",
        "付き合", "結婚", "元彼", "元カノ", "デート", "告白", "相性", "愛着", "恋人", "パートナー",
    ],
}
# その語で拾えたこと自体が、分野に合っている証拠になる語（小文字）。これ以外の語（「フォロワー」「指示」「SNS運用」など）は
# ふつうの言葉で、無関係な投稿も拾う。その場合は「検索した語とは別の、分野の語」が本文にあることを求める
# （2026-10-13の試運転：検索した語が本文にあるだけの、クエン酸・政治・訃報の投稿が上位を占めたため）
SPECIFIC_KEYWORDS = {
    "s4lv_UYA": lambda k: k in {
        "生成ai", "claude", "claude code", "claude 使い方", "チャッピー", "gemini",
        "claude code 仕事", "ai エージェント 作り方", "claude code 自動化", "claude code 設定", "chatgpt 仕事",
        "mcp 連携", "claude.md", "claude note", "ai検索 seo", "(aio or llmo)",
    },
    # MBTI・タイプ名・「恋愛」を含む語は分野そのもの。「未練」のような語は、ゲームや誕生日の話も拾うので、別の語を求める
    "MBTICODE": lambda k: re.search(r"mbti|[ie][ns][tf][jp]|恋愛", k) is not None,
}


def term_in(term, text):
    """英字の語は単語の境界で比べる（URLや他の語の一部に当たらないように）。"""
    if re.fullmatch(r"[a-z0-9]+", term):
        return re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", text) is not None
    return term in text


def on_topic(r, account):
    """分野の語があるか。ふつうの言葉で拾った投稿は、検索した語とは別の分野の語を求める。"""
    low = re.sub(r"https?://\S+", " ", r["text"].lower())
    terms = TOPIC_TERMS[account]
    specific = SPECIFIC_KEYWORDS[account]
    kws = [k.lower() for k in r["keywords"] if not k.startswith("@")]
    if any(specific(k) for k in kws):
        return any(term_in(t, low) for t in terms)
    own = " ".join(kws)
    return any(term_in(t, low) for t in terms if t not in own)


def readable(r):
    """ネタの材料として読める投稿か。画像やリンクだけで本文がほぼない投稿、他人への返信、日本語でない投稿は外す。"""
    t = re.sub(r"https?://\S+", " ", r["text"]).strip()
    if len(re.sub(r"\s+", "", t)) < 8:
        return False
    if re.match(r"@?[\w.]+に返信", t):
        return False
    return re.search(r"[ぁ-んァ-ヶ]", t) is not None


def hours_between(r, key):
    """投稿から、first_seen（初めて見かけた）／last_seen（最後に見かけた）までの時間。投稿日時が分からなければ None。"""
    try:
        p = datetime.fromisoformat(r["posted_at"])
        t = datetime.fromisoformat(r[key])
    except (KeyError, ValueError):
        return None
    return max(0.0, (t - p).total_seconds() / 3600.0)


def score(r):
    # 既存スキルの優先順位「ブックマーク＞返信＞いいね」に合わせる（ブックマークはXだけ取れる）
    return r["likes"] + 3 * r["reposts"] + 2 * r["replies"] + 5 * r.get("bookmarks", 0)


def is_save_row(r):
    """保存数・保存率で選ぶ行か（Xの語の検索で、keywords.json の window_hours つきで集めたもの）。"""
    return (r.get("platform") == "x" and r.get("source") != "account" and "window_hours" in r
            and "bookmarks" in r and bool(set(r.get("groups", [])) & SAVE_GROUPS))


def save_ok(r):
    """保存50以上、かつ（保存100以上、または保存率0.5%以上）。表示数が分からなければ、保存100以上だけで見る。"""
    b = r.get("bookmarks", 0)
    if b < SAVE_MIN:
        return False
    if b >= SAVE_STRONG:
        return True
    return bool(r.get("views")) and 100.0 * b / r["views"] >= SAVE_RATE


def momentum(r):
    h = hours_between(r, "last_seen")
    days_plus = (h / 24.0 if h is not None else 2.0) + 1.0
    if is_save_row(r):
        return r["bookmarks"] / days_plus  # 保存の勢い（保存数÷(日数+1)）
    return score(r) / days_plus


def age_limit_hours(r, args):
    if r.get("source") == "account":
        return args.max_age_account_hours
    if is_save_row(r):
        return r["window_hours"] + 1  # その語の検索の窓（keywords.json）。1時間は余裕
    return args.max_age_hours if r.get("platform") == "x" else args.max_age_threads_hours


def min_likes_for(r, args):
    if r.get("source") == "account":
        return r.get("min_faves", args.min_likes_x)  # そのアカウントのしきい値（watch_accounts.json）
    if is_save_row(r):
        return r.get("min_faves", 30)  # その語の検索の下限（keywords.json）。選ぶのは、下の保存の条件
    return args.min_likes_x if r.get("platform") == "x" else args.min_likes_threads


def pick_with_quota(keep, top, quota):
    """媒体ごとに最低 quota 件（あれば）を確保してから、残りを勢いの順に埋める。"""
    chosen = []
    for is_x in (True, False):
        chosen += [r for r in keep if (r.get("platform") == "x") == is_x][:quota]
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


def status_lines():
    """直近の収集がうまくいっているかを、候補ファイルの頭に書く（古い候補を、新しいと思って使わないように）。"""
    st = rc.load_state(rc.STATUS)
    names = {"x": "X", "threads": "スレッズ"}
    reasons = {rc.LOGIN_EXPIRED: "ログイン切れ", rc.COOKIE_INVALID: "ログイン情報が使えない", rc.INCOMPLETE: "途中で止まった",
               rc.NOTHING_FOUND: "1件も取れなかった"}
    out = []
    for key, name in names.items():
        s = st.get(key)
        if not s:
            out.append("- 収集の状態（%s）：記録なし" % name)
            continue
        ok_at = s.get("last_ok_at", "")
        line = "- 収集の状態（%s）：最後に成功した収集 %s" % (name, ok_at.replace("T", " ")[:16] or "なし")
        if s.get("exit_code") != rc.OK:
            line += " ／ **直近の実行は失敗（%s）**" % reasons.get(s.get("exit_code"), "コード%s" % s.get("exit_code"))
        elif ok_at and (datetime.now() - datetime.fromisoformat(ok_at)) > timedelta(hours=60):
            line += " ／ **2日以上、収集が動いていません**（PCを起動していない・通知を確認）"
        out.append(line)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=30, help="1ファイルの最大件数")
    ap.add_argument("--min-likes-x", type=int, default=100, help="X：これ未満のいいねは候補にしない")
    ap.add_argument("--min-likes-threads", type=int, default=100, help="スレッズ：これ未満のいいねは候補にしない")
    ap.add_argument("--max-age-hours", type=int, default=24, help="X：集めた時点で、投稿からこの時間以内のものだけ候補にする")
    ap.add_argument("--max-age-threads-hours", type=int, default=48, help="スレッズ：同上（時刻表示が「日」単位に丸まるため48時間）")
    ap.add_argument("--max-age-account-hours", type=int, default=120, help="アカウント起点の投稿：同上（約4日で一周するため5日）")
    ap.add_argument("--window-days", type=int, default=7, help="この日数以内に集めたものを蓄積して並べる（週1回のリサーチ用）")
    ap.add_argument("--max-per-author", type=int, default=2)
    ap.add_argument("--max-per-keyword", type=int, default=6, help="1つのキーワードから取る最大件数（偏りを防ぐ）")
    ap.add_argument("--min-per-platform", type=int, default=10, help="媒体ごとの最低枠（その媒体の候補がある場合）")
    ap.add_argument("--keep-files-days", type=int, default=14, help="これより古い候補ファイルは消す")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    posts = []
    for src in SOURCES:
        posts += list(rc.load_jsonl(src).values())
    if not posts:
        sys.exit("溜めたデータがありません。先に collect_threads.py / collect_x.py を実行してください。")
    ledger_text = "\n".join(p.read_text(encoding="utf-8") for p in LEDGERS if p.exists())
    window_start = (datetime.now() - timedelta(days=args.window_days)).isoformat(timespec="seconds")
    today = datetime.now().strftime("%Y-%m-%d")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    health = status_lines()

    for account, groups in VIEWS.items():
        pool = [r for r in posts if set(r["groups"]) & set(groups)]
        ex = {"集めたのが古い": 0, "投稿が古い・日時不明": 0, "反響小": 0, "保存が少ない": 0, "自分のアカウント": 0, "本文なし・返信・日本語でない": 0,
              "勧誘など": 0, "無関係な話題": 0, "分野の語なし": 0, "既出": 0, "同じ投稿者": 0, "語の上限": 0}
        keep, per_author, kw_count = [], {}, {}
        for r in sorted(pool, key=momentum, reverse=True):
            low = r["text"].lower()
            h_first = hours_between(r, "first_seen")
            if r["first_seen"] < window_start:
                ex["集めたのが古い"] += 1
            elif h_first is None or h_first > age_limit_hours(r, args):
                ex["投稿が古い・日時不明"] += 1  # 集めた時点で基準より経っていたもの。日時が分からないものも、新しいと言えないので除く
            elif r["likes"] < min_likes_for(r, args):
                ex["反響小"] += 1
            elif is_save_row(r) and not save_ok(r):
                ex["保存が少ない"] += 1
            elif r["author"].lower() in OWN_AUTHORS:
                ex["自分のアカウント"] += 1
            elif not readable(r):
                ex["本文なし・返信・日本語でない"] += 1
            elif any(w.lower() in low for w in SOLICIT):
                ex["勧誘など"] += 1
            elif any(w.lower() in low for w in NOISE):
                ex["無関係な話題"] += 1
            elif r.get("source") != "account" and not on_topic(r, account):
                ex["分野の語なし"] += 1  # 観察対象アカウントの投稿は、人が選んだアカウントなので、この判定をしない
            elif rc.post_code(r["url"]) in ledger_text:
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
        n_x = sum(1 for r in keep if r.get("platform") == "x")

        lines = [
            "# 今週の候補：%s（%s）" % (account, today),
            "",
            "- 対象グループ：%s ／ 溜めたデータ：%d件 → 候補 **%d件**（X %d件・スレッズ %d件）" % (
                "・".join(groups), len(pool), len(keep), n_x, len(keep) - n_x),
        ] + health + [
            "- 新しさ：**集めた時点で、投稿からX=%d時間以内・スレッズ=%d時間以内**（アカウント起点は%d時間以内）のものだけ。集めてから%d日分を蓄積して並べている" % (
                args.max_age_hours, args.max_age_threads_hours, args.max_age_account_hours, args.window_days),
            "- 並び順：**勢い**＝反響点÷(投稿から最後に見かけるまでの日数＋1)。反響点＝いいね＋再投稿×3＋返信×2＋保存×5（保存はXだけ）",
            "- 絞り込み：同じ投稿者は最大%d件、1つの語から最大%d件、媒体ごとに最低%d件（あれば）。いいね：Xは%d以上・スレッズは%d以上（アカウント起点は各アカウントのしきい値）" % (
                args.max_per_author, args.max_per_keyword, args.min_per_platform, args.min_likes_x, args.min_likes_threads),
            "- **Xの語の検索のうち、ai・blog_note_sns・save_pattern の語**：保存%d以上、かつ（保存%d以上、または保存率%.1f%%以上）の投稿だけ。新しさは、その語の窓（keywords.json の window_hours）以内。並びは **保存の勢い**＝保存数÷(日数＋1)" % (
                SAVE_MIN, SAVE_STRONG, SAVE_RATE),
            "- 除外の内訳：" + "、".join("%s %d" % (k, v) for k, v in ex.items()),
            "- **意味の関連は、機械では判定しきれない**（検索した語が本文にあるだけの、無関係な投稿が混ざることがある）。使えるかどうかは、読んで判断する",
            "- この表は、本文の冒頭だけを載せたローカル用のメモ。台帳には、URL・型・数字だけを書く（全文は写さない）",
            "",
            "| # | 媒体 | 勢い | 反響点 | いいね | 返信 | 再投稿 | 保存数 | 保存率 | 表示数 | 投稿日 | 集めた時の経過 | 投稿者 | フォロワー | 拾ったキーワード | 本文の冒頭 | URL |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        for i, r in enumerate(keep, 1):
            has_bm = "bookmarks" in r
            rate = ("%.2f%%" % (100.0 * r["bookmarks"] / r["views"])) if has_bm and r.get("views") else "−"
            lines.append("| %d | %s | %d | %d | %d | %d | %d | %s | %s | %s | %s | %s | @%s | %s | %s | %s | %s |" % (
                i, "X" if r.get("platform") == "x" else "スレッズ", momentum(r), score(r), r["likes"], r["replies"], r["reposts"],
                (str(r["bookmarks"]) if has_bm else "−"), rate,
                ("{:,}".format(r["views"]) if r.get("views") else "−"),
                r["posted_at"][:10], label_hours(hours_between(r, "first_seen")),
                r["author"], ("{:,}".format(r["followers"]) if r.get("followers") else "−"),
                "／".join(r["keywords"][:3]),
                one_line(r["text"]).replace("|", "｜"), r["url"]))
        path = OUT_DIR / ("shortlist_%s_%s.md" % (account, today))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("%s：%d件（X %d・スレッズ %d） → %s（除外：%s）" % (account, len(keep), n_x, len(keep) - n_x, path.relative_to(rc.REPO),
              "、".join("%s%d" % (k, v) for k, v in ex.items() if v)))

    # 古い候補ファイルを消す（毎日1つずつ増えるため。読むのは最新のものだけ）
    limit = datetime.now() - timedelta(days=args.keep_files_days)
    for f in OUT_DIR.glob("shortlist_*.md"):
        m = re.search(r"_(\d{4}-\d{2}-\d{2})\.md$", f.name)
        if m and datetime.strptime(m.group(1), "%Y-%m-%d") < limit:
            f.unlink()


if __name__ == "__main__":
    main()
