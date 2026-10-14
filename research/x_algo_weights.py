"""X algorithm weights watcher (no Claude, no tokens).

Fetches the official params file from github.com/xai-org/x-algorithm,
compares ALL params (numeric weights + switches/limits) with the last saved
values, and writes a diff when something changed or a new param appeared.
It never edits the reference document by itself: the owner confirms first.
Guide: docs/sop/sop_research_auto_collect.md ("X algorithm weights" section)

Usage:
  py -3 x_algo_weights.py             # runs only if >= 3 days since last check
  py -3 x_algo_weights.py --force     # run now
  py -3 x_algo_weights.py --render    # print the full table (markdown) from the saved values
Exit codes: 0 ok (no change / first baseline) / 10 changed / 2 fetch failed / 3 parse failed
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


def render_table(data):
    weights = data.get("weights", {})
    others = data.get("others", {})
    fav = weights.get("FavoriteWeight") or 0.5
    order = [G_POS, G_LIGHT, G_NEG, G_ADJ, G_ZERO, G_SW, G_NEW]
    rows = {g: [] for g in order}
    for k, v in weights.items():
        g, label = LABELS.get(k, (G_NEW, k))
        rows[g].append((k, label, v))
    for k, v in others.items():
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
        if g in (G_ADJ, G_SW):
            out.append("| 項目 | 公式名 | 値 |")
            out.append("|---|---|---|")
            for k, label, v in items:
                out.append("| %s | `%s` | %s |" % (label, k, fmt(v)))
        else:
            out.append("| 項目 | 公式名 | 値 | いいね基準 |")
            out.append("|---|---|---|---|")
            for k, label, v in items:
                rel = "" if v == 0 else "約%.3g倍" % (v / fav)
                out.append("| %s | `%s` | %s | %s |" % (label, k, fmt(v), rel))
        out.append("")
    return chr(10).join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--interval-days", type=float, default=3.0)
    args = ap.parse_args()

    if args.render:
        data = load_json(LATEST, None)
        if not data:
            print("no saved values yet (run with --force first)")
            return 2
        print(render_table(data))
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

    lines = ["## %s  (commit %s)" % (stamp, commit), ""]
    for k, a, b in diffs:
        if a is None:
            lines.append("- NEW %s: %s" % (k, fmt(b)))
        elif b is None:
            lines.append("- REMOVED %s: was %s" % (k, fmt(a)))
        else:
            lines.append("- %s: %s -> %s" % (k, fmt(a), fmt(b)))
    lines.append("")
    prev = CHANGES.read_text(encoding="utf-8") if CHANGES.exists() else "# X algorithm weight changes (newest first)" + chr(10) + chr(10)
    head, _, rest = prev.partition(chr(10) + chr(10))
    CHANGES.write_text(head + chr(10) + chr(10) + chr(10).join(lines) + chr(10) + rest, encoding="utf-8")

    save_json(LATEST, new_data)
    save_json(STATE, state)
    print("CHANGED: %d item(s)" % len(diffs))
    for k, a, b in diffs:
        print("  %s: %s -> %s" % (k, "(none)" if a is None else fmt(a), "(removed)" if b is None else fmt(b)))
    return 10


if __name__ == "__main__":
    sys.exit(main())
