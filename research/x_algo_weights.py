"""X algorithm weights watcher (no Claude, no tokens).

Fetches the official weights file from github.com/xai-org/x-algorithm,
compares with the last saved values, and writes a diff when something changed.
It never edits the reference document by itself: the owner confirms first.
Guide: docs/sop/sop_research_auto_collect.md ("X algorithm weights" section)

Usage:
  py -3 x_algo_weights.py             # runs only if >= 3 days since last check
  py -3 x_algo_weights.py --force     # run now
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

PARAM_RE = re.compile(
    r'param!\(\s*(\w+)\s*,\s*f64\s*,\s*"([^"]+)"\s*,\s*(-?[0-9]*\.?[0-9]+)\s*,?\s*\)',
    re.S,
)
MIN_PARAMS = 20  # fewer than this means the file layout changed


def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "x-algo-weights-watcher"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


def parse_weights(text):
    return {name: float(val) for name, _key, val in PARAM_RE.findall(text)}


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def save_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")


def fmt(v):
    return ("%g" % v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--interval-days", type=float, default=3.0)
    args = ap.parse_args()

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

    weights = parse_weights(text)
    if len(weights) < MIN_PARAMS:
        print("parse failed: only %d params found (file layout may have changed)" % len(weights))
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

    if old is None:
        save_json(LATEST, {"fetched_at": stamp, "commit": commit, "source": RAW_URL, "weights": weights})
        save_json(STATE, state)
        print("baseline saved: %d params (%s)" % (len(weights), commit))
        return 0

    ow = old.get("weights", {})
    diffs = []
    for k in sorted(set(ow) | set(weights)):
        a, b = ow.get(k), weights.get(k)
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
        a_s = "(none)" if a is None else fmt(a)
        b_s = "(removed)" if b is None else fmt(b)
        lines.append("- %s: %s -> %s" % (k, a_s, b_s))
    lines.append("")
    prev = CHANGES.read_text(encoding="utf-8") if CHANGES.exists() else "# X algorithm weight changes (newest first)" + chr(10) + chr(10)
    head, _, rest = prev.partition(chr(10) + chr(10))
    CHANGES.write_text(head + chr(10) + chr(10) + chr(10).join(lines) + chr(10) + rest, encoding="utf-8")

    save_json(LATEST, {"fetched_at": stamp, "commit": commit, "source": RAW_URL, "weights": weights})
    save_json(STATE, state)
    print("CHANGED: %d value(s)" % len(diffs))
    for k, a, b in diffs:
        print("  %s: %s -> %s" % (k, a, b))
    return 10


if __name__ == "__main__":
    sys.exit(main())
