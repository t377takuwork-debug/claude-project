"""X・スレッズの自動リサーチで、収集（collect_x.py / collect_threads.py）と候補づくり（make_shortlist.py）が共通で使う部品。

説明書： docs/sop/sop_research_auto_collect.md
"""
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "research_data"          # gitに入れないローカルの置き場
KEYWORDS = ROOT / "keywords.json"
STATUS = DATA_DIR / "status.json"          # 直近の実行結果（成否・件数）。候補ファイルの頭に表示する
KEEP_DAYS = 30                             # これより前に最後に見かけた投稿は、溜めたデータから消す（候補に使うのは7日分）

# 終了コード（run_threads_research.cmd が、0以外なら小さな通知を出す）
OK, LOGIN_EXPIRED, COOKIE_INVALID, INCOMPLETE, NOTHING_FOUND = 0, 3, 4, 5, 6

NUM_KEYS = ("likes", "replies", "reposts", "views", "bookmarks", "followers")


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def load_jsonl(path):
    """1行1投稿のファイルを、URLをキーにして読む。"""
    data = {}
    if path.exists():
        # splitlines()は、本文中の特殊な行区切り（U+2028等）でも切れるので使わない
        for line in path.read_text(encoding="utf-8").split(chr(10)):
            if line.strip():
                row = json.loads(line)
                data[row["url"]] = row
    return data


def save_jsonl(path, data, keep_days=KEEP_DAYS):
    """保存する。最後に見かけてから keep_days 日より古い投稿は、ここで消す（ファイルが増え続けないように）。"""
    limit = (datetime.now() - timedelta(days=keep_days)).isoformat(timespec="seconds")
    rows = [r for r in data.values() if r.get("last_seen", "") >= limit]
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + chr(10))
    tmp.replace(path)  # 書いている途中で止まっても、元のファイルが壊れないように入れ替える
    return len(rows), len(data) - len(rows)


def merge_row(data, row, now, group, keyword):
    """同じ投稿（URL）があれば数字だけ更新し、なければ足す。返り値は 'new' か 'upd'。"""
    old = data.get(row["url"])
    if old is None:
        row.update({"first_seen": now, "last_seen": now, "groups": [group], "keywords": [keyword]})
        data[row["url"]] = row
        return "new"
    for k in NUM_KEYS:
        if k in row or k in old:
            old[k] = max(old.get(k, 0), row.get(k, 0))
    for k in ("source", "min_faves"):  # アカウント起点で見つけた印
        if k in row:
            old[k] = row[k]
    if not old.get("posted_at") and row.get("posted_at"):
        old["posted_at"] = row["posted_at"]
    old["last_seen"] = now
    if group not in old["groups"]:
        old["groups"].append(group)
    if keyword not in old["keywords"]:
        old["keywords"].append(keyword)
    return "upd"


def platform_keywords(path, platform):
    """keywords.json から、その媒体（'x' か 'threads'）の表を読む。"""
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    return cfg["platforms"][platform] if "platforms" in cfg else cfg


def daily_plan(cfg, state):
    """毎日の枠＋日替わり枠（前回の続き）。返り値：(今日の語の一覧, 何組目か, 全部で何組か, 毎日の枠の語数)"""
    group_of = {k: g for g, v in cfg["groups"].items() for k in v["keywords"]}
    fixed = [k for k in cfg.get("daily_fixed", []) if k in group_of]
    rest = [k for k in group_of if k not in fixed]
    size = cfg.get("rotation_size", 5)
    batches = [rest[i:i + size] for i in range(0, len(rest), size)] or [[]]
    nxt = state.get("rotation_next", 0) % len(batches)
    return fixed + batches[nxt], nxt + 1, len(batches), len(fixed)


def group_of_keywords(cfg):
    return {k: g for g, v in cfg["groups"].items() for k in v["keywords"]}


def load_state(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def write_status(name, info):
    """直近の実行結果を status.json に書く（name は 'x' か 'threads'）。成功した日時は別に持つ。"""
    st = load_state(STATUS)
    prev = st.get(name, {})
    info = dict(info)
    info["last_run_at"] = now_iso()
    info["last_ok_at"] = info["last_run_at"] if info.get("exit_code") == OK else prev.get("last_ok_at", "")
    st[name] = info
    save_state(STATUS, st)


def post_code(url):
    """投稿のID（台帳との照合・類似チェックで使う）。スレッズの画像つき投稿の末尾「/media」は除く。"""
    u = re.sub(r"/media$", "", url.strip().rstrip("/"))
    return u.split("/")[-1].split("?")[0]
