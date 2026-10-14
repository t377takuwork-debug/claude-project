"""X algorithm weights watcher (no Claude, no tokens).

Fetches the official params file from github.com/xai-org/x-algorithm,
compares ALL params (numeric weights + switches/limits) with the last saved
values, and writes a diff when something changed or a new param appeared.
It never edits the reference document by itself: the owner confirms first.
Guide: docs/sop/sop_research_auto_collect.md ("X algorithm weights" section)

Usage:
  py -3 x_algo_weights.py             # runs only if >= 2 days since last check
  py -3 x_algo_weights.py --force     # run now
  py -3 x_algo_weights.py --render    # print the full table (markdown) from the saved values
Exit codes: 0 ok (no change / first baseline / only items that do not matter for posts changed) / 10 an item that matters for posts changed / 2 fetch failed / 3 parse failed
Files (all under research/data/x_algo/, not in git):
  latest.json  state.json  changes.md
"""
import argparse
import datetime as dt
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "x_algo"
LATEST = OUT / "latest.json"
STATE = OUT / "state.json"
CHANGES = OUT / "changes.md"

REPO = "xai-org/x-algorithm"
FILE_PATH = "vm-ranker/params.rs"
RAW_URL = f"https://raw.githubusercontent.com/{REPO}/main/{FILE_PATH}"
COMMIT_URL = f"https://api.github.com/repos/{REPO}/commits?path={FILE_PATH}&per_page=1"

# param!(Name, type, "config_key", value);   (value may be -1.5 / true / 10_000 / "")
PARAM_RE = re.compile(
    r'param!\(\s*(\w+)\s*,\s*(\w+)\s*,\s*"([^"]+)"\s*,\s*(.+?)\s*,?\s*\)\s*;',
    re.S,
)
MIN_PARAMS = 20  # fewer than this means the file layout changed

# name -> (group, plain Japanese label). Unknown names are shown as "new item".
G_POS, G_LIGHT, G_ZERO, G_NEG, G_ADJ, G_SW, G_NEW = (
    "強いプラス", "軽いプラス", "いまは評価に入っていない（値0）", "マイナス",
    "表示の調整", "切り替え・上限の設定", "新しい項目（未訳）",
)
LABELS = {
    "ShareViaCopyLinkWeight": (G_POS, "リンクをコピーして共有"),
    "BidirectionalFollowReplyWeightBoost": (G_POS, "相互フォロー相手の返信（返信5.0に足される加算分）"),
    "ReplyWeight": (G_POS, "返信"),
    "QuoteWeight": (G_POS, "引用"),
    "ShareViaDmWeight": (G_POS, "DMで共有"),
    "FollowAuthorWeight": (G_POS, "投稿者をフォロー"),
    "ShareWeight": (G_POS, "シェア"),
    "RetweetWeight": (G_POS, "リポスト"),
    "FavoriteWeight": (G_LIGHT, "いいね"),
    "ContClickDwellTimeWeight": (G_LIGHT, "開いて10秒以上滞在"),
    "ClickWeight": (G_LIGHT, "投稿を開く"),
    "OpenLinkWeight": (G_LIGHT, "リンクを開く"),
    "VideoOpenWeight": (G_LIGHT, "動画を開く"),
    "DwellWeight": (G_LIGHT, "投稿の上で止まる"),
    "QuotedClickWeight": (G_LIGHT, "引用元の投稿を開く"),
    "PhotoExpandWeight": (G_LIGHT, "写真を拡大"),
    "PostUnexploredWeight": (G_LIGHT, "フォロー中の人の未読の投稿"),
    "ContDwellTimeWeight": (G_LIGHT, "滞在時間（1秒あたり）"),
    "ReportWeight": (G_NEG, "報告"),
    "MuteAuthorWeight": (G_NEG, "投稿者をミュート"),
    "NotInterestedWeight": (G_NEG, "興味なし"),
    "BlockAuthorWeight": (G_NEG, "投稿者をブロック"),
    "NotDwelledWeight": (G_NEG, "止まらずスクロールして通過"),
    "BidirectionalFollowDwellWeightBoost": (G_ZERO, "相互フォロー相手の滞在への加算"),
    "ProfileClickWeight": (G_ZERO, "プロフィールを開く"),
    "VqvWeight": (G_ZERO, "動画の十分な視聴"),
    "QuotedVqvWeight": (G_ZERO, "引用元動画の十分な視聴"),
    "VideoContinuationWeight": (G_ZERO, "動画の続けて視聴"),
    "UserVideoContinuationWeight": (G_ZERO, "ユーザー単位の動画の続けて視聴"),
    "ProfileVisitSecsWeight": (G_ZERO, "プロフィールの滞在秒数"),
    "ReactWithVideoWeight": (G_ZERO, "動画つきで反応"),
    "WeightPerturbationSigma": (G_ZERO, "重みをランダムに揺らす幅"),
    "OonWeightFactor": (G_ADJ, "フォロー外の投稿に掛ける係数"),
    "TopicOonWeightFactor": (G_ADJ, "話題経由のフォロー外の投稿に掛ける係数"),
    "NewUserOonWeightFactor": (G_ADJ, "新規ユーザー向けのフォロー外の係数"),
    "AuthorDiversityDecay": (G_ADJ, "同じ作者の2本目以降の減衰率"),
    "AuthorDiversityFloor": (G_ADJ, "同じ作者の減衰の下限"),
    "AuthorExplorationBonus": (G_ADJ, "作者の探索ボーナス"),
    "DppTheta": (G_ADJ, "似た投稿を並べない調整の強さ（DPP）"),
}


SWITCH_LABELS = {
    "EnableAuthorDiversity": "同じ作者の連続表示を減衰させる",
    "DppEnabled": "似た投稿を並べない調整（DPP）を使う",
    "TopicDppEnabled": "話題ごとのDPPを使う",
    "DppMaxSelectedRank": "DPPの対象にする順位の上限",
    "EnableOonRescoreForInNetworkRepliesRetweets": "フォロー中の人の返信・リポストをフォロー外の係数で再採点する",
    "PostUnexploredIncludeOutOfNetwork": "未読の投稿の加点をフォロー外にも使う",
    "MinVideoDurationMs": "動画の視聴とみなす最短の長さ（ミリ秒）",
    "EnableQuotedVqvDurationCheck": "引用元動画の長さを確かめる",
    "WeightPerturbationSalt": "重みを揺らすときの乱数の種",
    "MultiplierPreOffset": "係数を加算の前に掛ける",
    "NewUserAgeThresholdSecs": "新規ユーザーとみなす経過秒数",
    "ComputeValueModel": "価値モデルを計算する",
}


# name -> (どんな行動・調整か, 投稿づくりでの意味, 確度)
# 確度: "確認済み"＝公式コード（xai-value-model/scoring.rs・weights.rs・inputs.rs）で動きを確かめた
#       "推測"＝項目名からの推測（コードで確かめていない）
DESC = {
    "ShareViaCopyLinkWeight": ("投稿のリンクをコピーして共有する", "人に送りたくなる・保存したくなる、完結した中身か", "確認済み"),
    "BidirectionalFollowReplyWeightBoost": ("相互フォロー相手の「原投稿」への返信（返信自体・リポストは対象外）の予測に、返信の重みへ足される", "相互フォローとの本物のやり取りが生まれる投稿か", "確認済み"),
    "ReplyWeight": ("投稿に返信する", "返したくなる問い・余白・具体的な体験があるか", "確認済み"),
    "QuoteWeight": ("投稿を引用して投稿する", "引用したくなる意見・視点があるか", "確認済み"),
    "ShareViaDmWeight": ("投稿をDMで送る", "誰かに直接送りたくなる内容か", "確認済み"),
    "FollowAuthorWeight": ("投稿を見て、その投稿者をフォローする", "アカウントとしての一貫性・価値が伝わるか", "確認済み"),
    "ShareWeight": ("通常のシェアをする", "共有したくなる情報か", "確認済み"),
    "RetweetWeight": ("リポストする", "リポストしたくなる情報か", "確認済み"),
    "FavoriteWeight": ("いいねする", "基準の行動。これだけを狙わない", "確認済み"),
    "ContClickDwellTimeWeight": ("投稿を開いたあと、どれだけ読み続けるか（予測した滞在時間に掛かる。確率ではない）", "開いたあとも読み進めたくなる構成・長さか", "確認済み（連続値。単位は秒と推測）"),
    "ClickWeight": ("投稿をタップして開く", "開きたくなる1行目か", "確認済み"),
    "OpenLinkWeight": ("投稿内のリンクを開く", "外部リンクは軽いプラス止まり。本文リンクは控えめに", "確認済み"),
    "VideoOpenWeight": ("動画を開く", "動画は補助的", "確認済み"),
    "PhotoExpandWeight": ("写真を拡大する", "画像で目を止められるか", "確認済み"),
    "DwellWeight": ("投稿の上でしばらく止まる", "流し見されず、立ち止まらせられるか", "確認済み（確率）"),
    "QuotedClickWeight": ("引用された元の投稿を開く", "引用の連鎖が起きるか", "確認済み"),
    "PostUnexploredWeight": ("まだ見ていない投稿（フォロー中の人のものだけ。設定で、フォロー外にも使える）", "名前からの意味づけ。投稿づくりでは意識しにくい", "確認済み（対象の条件）／意味は推測"),
    "ContDwellTimeWeight": ("投稿を見ている時間（予測した滞在時間に掛かる。確率ではない）", "滞在時間そのものの加点。係数が小さい", "確認済み（連続値）"),
    "ReportWeight": ("投稿を報告する", "報告されうる表現は避ける（最優先）", "確認済み"),
    "MuteAuthorWeight": ("投稿者をミュートする", "不快・攻撃的・スパム感を避ける", "確認済み"),
    "NotInterestedWeight": ("「興味なし」を選ぶ", "興味のない人に押し付けない（ジャンルのぶれに注意）", "確認済み"),
    "BlockAuthorWeight": ("投稿者をブロックする", "攻撃的な表現を避ける", "確認済み"),
    "NotDwelledWeight": ("止まらずに通り過ぎる", "1行目で引っかけられないと、軽いマイナスになる", "確認済み"),
    "BidirectionalFollowDwellWeightBoost": ("相互フォロー相手の原投稿の「滞在」に足される加算", "いまは0なので影響なし", "確認済み"),
    "ProfileClickWeight": ("投稿者のプロフィールを開く", "いまは評価に入っていない", "確認済み"),
    "VqvWeight": ("動画を十分な長さ見る（短すぎる動画は対象外）", "いまは評価に入っていない", "確認済み"),
    "QuotedVqvWeight": ("引用元の動画を十分な長さ見る", "いまは評価に入っていない", "確認済み"),
    "VideoContinuationWeight": ("動画を開いたあと、続けて見る時間", "いまは評価に入っていない", "確認済み"),
    "UserVideoContinuationWeight": ("閲覧者ごとの、動画を続けて見る時間", "いまは評価に入っていない", "確認済み"),
    "ProfileVisitSecsWeight": ("プロフィールを開いたあとの滞在時間", "いまは評価に入っていない", "確認済み"),
    "ReactWithVideoWeight": ("動画つきで反応する", "いまは評価に入っていない", "確認済み"),
    "WeightPerturbationSigma": ("閲覧者ごとに、すべての重みをランダムに少し上下させる幅", "0なので揺らしていない。0より大きくなると、重みは閲覧者ごとに変わる", "確認済み"),
    "OonWeightFactor": ("フォロー外の投稿の最終スコアに掛ける。フォロー中の人の返信・リポストにも掛かる（設定が有効なため）", "フォロー外へ届くには、この割引（×0.75）を超える反応が要る", "確認済み"),
    "TopicOonWeightFactor": ("話題経由で届くフォロー外の投稿に掛ける係数", "話題経由は、より強く割り引かれる", "推測"),
    "NewUserOonWeightFactor": ("新規ユーザーに対するフォロー外の係数", "ほぼ0。新規ユーザーにはフォロー外が出にくい", "推測"),
    "AuthorDiversityDecay": ("同じ閲覧者に出る同じ作者の投稿を、スコアの高い順に並べ、2本目以降に掛ける割引の速さ", "1本目×1.0、2本目×0.625、3本目×0.44、4本目×0.34、下限×0.25", "確認済み"),
    "AuthorDiversityFloor": ("同じ作者の割引の下限", "どれだけ続けても×0.25より下がらない", "確認済み"),
    "AuthorExplorationBonus": ("新しい作者への加点（スコアに足される）", "コード上は加点の仕組みがあるが、いまは常に0", "確認済み"),
    "DppTheta": ("似た内容の投稿が並ばないよう、上位の並びを再調整する強さ", "同じ話題・同じ形の投稿は、並びで不利になりうる", "確認済み（仕組み）／強さの意味は推測"),
}

LABEL_FIX = {
    "ContClickDwellTimeWeight": "開いたあとの滞在時間",
    "ContDwellTimeWeight": "投稿を見ている時間",
    "ClickWeight": "投稿を開く（タップ）",
}


def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "x-algo-weights-watcher"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


def parse_params(text):
    """Return (weights {name: float}, others {name: 'type=value'})."""
    weights, others = {}, {}
    for name, typ, _key, val in PARAM_RE.findall(text):
        val = val.strip()
        if typ == "f64":
            try:
                weights[name] = float(val.replace("_", ""))
                continue
            except ValueError:
                pass
        others[name] = "%s=%s" % (typ, val)
    return weights, others


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def save_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")


def fmt(v):
    return v if isinstance(v, str) else ("%g" % v)


# 投稿づくりに落とし込めるものだけ。ここに無い項目（値0・設定・小さな係数）は、
# 変わっても通知しない・資料の表に載せない（全項目は latest.json に残る）。
RELEVANT = {
    "ShareViaCopyLinkWeight", "BidirectionalFollowReplyWeightBoost", "ReplyWeight", "QuoteWeight",
    "ShareViaDmWeight", "FollowAuthorWeight", "ShareWeight", "RetweetWeight", "FavoriteWeight",
    "ContClickDwellTimeWeight", "ClickWeight", "OpenLinkWeight", "VideoOpenWeight", "PhotoExpandWeight",
    "NotDwelledWeight", "ReportWeight", "MuteAuthorWeight", "NotInterestedWeight", "BlockAuthorWeight",
    "OonWeightFactor", "AuthorDiversityDecay", "AuthorDiversityFloor",
}

SWITCH_CONFIRMED = {
    "EnableAuthorDiversity", "EnableOonRescoreForInNetworkRepliesRetweets", "MultiplierPreOffset",
    "PostUnexploredIncludeOutOfNetwork", "MinVideoDurationMs", "WeightPerturbationSalt", "DppMaxSelectedRank",
}


def render_table(data, curated=True):
    weights = data.get("weights", {})
    others = data.get("others", {})
    fav = weights.get("FavoriteWeight") or 0.5
    order = [G_POS, G_LIGHT, G_NEG, G_ADJ, G_ZERO, G_SW, G_NEW]
    rows = {g: [] for g in order}
    for k, v in weights.items():
        if curated and k not in RELEVANT:
            continue
        g, label = LABELS.get(k, (G_NEW, k))
        rows[g].append((k, LABEL_FIX.get(k, label), v))
    for k, v in ({} if curated else others).items():
        rows[G_SW].append((k, SWITCH_LABELS.get(k, "（新しい設定・未訳）"), v.split("=", 1)[1]))
    out = [
        "公式の値の取得：%s／コミット %s" % (data.get("fetched_at", "?"), data.get("commit", "?")),
        "",
    ]
    for g in order:
        items = rows[g]
        if not items:
            continue
        if g in (G_POS, G_LIGHT, G_NEG, G_ZERO, G_NEW):
            items.sort(key=lambda r: -abs(r[2]))
        out.append("### " + g)
        out.append("")
        if g == G_SW:
            out.append("| 項目 | 値 | 役割 | 確度 |")
            out.append("|---|---|---|---|")
            for k, label, v in items:
                conf = "確認済み" if k in SWITCH_CONFIRMED else "推測"
                out.append("| `%s` | %s | %s | %s |" % (k, v, label, conf))
        elif g == G_ADJ:
            out.append("| 項目 | 値 | どんな調整か | 投稿づくりでの意味 | 確度 |")
            out.append("|---|---|---|---|---|")
            for k, label, v in items:
                d = DESC.get(k, ("（未確認の新しい項目）", "", "未確認"))
                out.append("| %s `%s` | %s | %s | %s | %s |" % (label, k, fmt(v), d[0], d[1], d[2]))
        else:
            out.append("| 項目 | 値 | いいね基準 | どんな行動か | 投稿づくりでの意味 | 確度 |")
            out.append("|---|---|---|---|---|---|")
            for k, label, v in items:
                rel = "" if v == 0 else "約%.3g倍" % (v / fav)
                d = DESC.get(k, ("（未確認の新しい項目）", "", "未確認"))
                out.append("| %s `%s` | %s | %s | %s | %s | %s |" % (label, k, fmt(v), rel, d[0], d[1], d[2]))
        out.append("")
    return chr(10).join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--render", action="store_true", help="print the curated table (post-making items only)")
    ap.add_argument("--render-all", action="store_true", help="print every param (for checking)")
    ap.add_argument("--mark-reflected", action="store_true", help="record that the reference doc now matches the saved values")
    ap.add_argument("--interval-days", type=float, default=2.0)
    args = ap.parse_args()

    if args.render or args.render_all:
        data = load_json(LATEST, None)
        if not data:
            print("no saved values yet (run with --force first)")
            return 2
        print(render_table(data, curated=not args.render_all))
        return 0

    if args.mark_reflected:
        OUT.mkdir(parents=True, exist_ok=True)
        st = load_json(STATE, {})
        cur = load_json(LATEST, {})
        st["needs_update"] = False
        st["reflected_commit"] = cur.get("commit", "")
        save_json(STATE, st)
        print("marked as reflected (%s)" % st["reflected_commit"])
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now()
    state = load_json(STATE, {})

    if not args.force and state.get("last_checked"):
        last = dt.datetime.fromisoformat(state["last_checked"])
        # allow a little slack so a daily logon trigger does not skip a due run
        if (now - last) < dt.timedelta(days=args.interval_days) - dt.timedelta(hours=2):
            print("skip: last check %s (< %g days)" % (state["last_checked"], args.interval_days))
            return 0

    try:
        text = http_get(RAW_URL)
    except Exception as e:
        print("fetch failed: %r" % (e,))
        return 2

    weights, others = parse_params(text)
    if len(weights) + len(others) < MIN_PARAMS:
        print("parse failed: only %d params found (file layout may have changed)" % (len(weights) + len(others)))
        return 3

    commit = ""
    try:
        data = json.loads(http_get(COMMIT_URL, timeout=20))
        commit = data[0]["sha"][:10] + " " + data[0]["commit"]["committer"]["date"][:10]
    except Exception:
        commit = "unknown"

    old = load_json(LATEST, None)
    stamp = now.strftime("%Y-%m-%d %H:%M")
    state["last_checked"] = now.isoformat(timespec="seconds")
    new_data = {"fetched_at": stamp, "commit": commit, "source": RAW_URL, "weights": weights, "others": others}

    if old is None:
        save_json(LATEST, new_data)
        save_json(STATE, state)
        print("baseline saved: %d weights + %d settings (%s)" % (len(weights), len(others), commit))
        return 0

    ow, oo = old.get("weights", {}), old.get("others", {})
    diffs = []
    for k in sorted(set(ow) | set(weights)):
        a, b = ow.get(k), weights.get(k)
        if a != b:
            diffs.append((k, a, b))
    for k in sorted(set(oo) | set(others)):
        a, b = oo.get(k), others.get(k)
        if a != b:
            diffs.append((k, a, b))

    if not diffs:
        old["last_confirmed"] = stamp
        save_json(LATEST, old)
        save_json(STATE, state)
        print("no change (%s)" % commit)
        return 0

    def matters(k, a, b):
        if k in RELEVANT:
            return True
        # a brand-new numeric weight that is not zero: unknown, so let the owner see it once
        known = k in LABELS or k in SWITCH_LABELS
        return a is None and not known and isinstance(b, float) and b != 0

    important = [d for d in diffs if matters(*d)]
    lines = ["## %s  (commit %s)" % (stamp, commit), ""]
    for k, a, b in diffs:
        tag = "" if matters(k, a, b) else "  (投稿づくりには影響しない項目)"
        if a is None:
            lines.append("- NEW %s: %s%s" % (k, fmt(b), tag))
        elif b is None:
            lines.append("- REMOVED %s: was %s%s" % (k, fmt(a), tag))
        else:
            lines.append("- %s: %s -> %s%s" % (k, fmt(a), fmt(b), tag))
    lines.append("")
    prev = CHANGES.read_text(encoding="utf-8") if CHANGES.exists() else "# X algorithm weight changes (newest first)" + chr(10) + chr(10)
    head, _, rest = prev.partition(chr(10) + chr(10))
    CHANGES.write_text(head + chr(10) + chr(10) + chr(10).join(lines) + chr(10) + rest, encoding="utf-8")

    save_json(LATEST, new_data)
    if important:
        state["needs_update"] = True
    save_json(STATE, state)
    print("CHANGED: %d item(s), %d matter for posts" % (len(diffs), len(important)))
    for k, a, b in diffs:
        print("  %s: %s -> %s" % (k, "(none)" if a is None else fmt(a), "(removed)" if b is None else fmt(b)))
    return 10 if important else 0


if __name__ == "__main__":
    sys.exit(main())
