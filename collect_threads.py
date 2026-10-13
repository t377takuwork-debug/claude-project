"""スレッズの検索結果から、反響のある投稿を集めて溜める（Claudeのトークンは使わない）。

事前に：  py -3 threads_login.py  （調査用アカウントで、人の手でログイン。1回だけ）
使い方：  py -3 collect_threads.py                       全キーワードを集める
          py -3 collect_threads.py --group mbti_love     グループを絞る
          py -3 collect_threads.py --max-keywords 2      テスト（先頭2語だけ）
保存先：  research_data/threads_posts.jsonl （1行1投稿。同じ投稿は上書きせず、数字だけ更新）
注意：    取得間隔は空けてある。1日数回までにする（制限を避けるため）。
"""
import argparse
import json
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "threads_state.local.json"
KEYWORDS = ROOT / "keywords.json"
OUT = ROOT / "research_data" / "threads_posts.jsonl"

# 画面上の投稿を、ボタン名つきの数字ごと取り出す（ログインなしは「コメントする」、ログイン時は「返信」）
EXTRACT_JS = r"""
() => {
  const links = [...document.querySelectorAll('a[href*="/post/"]')];
  const seen = new Set(), res = [];
  for (const a of links) {
    const href = a.getAttribute('href').split('?')[0];
    if (seen.has(href)) continue;
    let el = a, ok = null;
    for (let i = 0; i < 10 && el.parentElement; i++) {
      el = el.parentElement;
      const posts = new Set([...el.querySelectorAll('a[href*="/post/"]')].map(x => x.getAttribute('href').split('?')[0]));
      if (posts.size > 1) break;
      if (el.querySelectorAll('svg title').length >= 3) ok = el;
    }
    if (!ok) continue;
    seen.add(href);
    const m = {};
    ok.querySelectorAll('[role=button]').forEach(b => {
      const t = b.querySelector('svg title'); if (!t) return;
      const n = (b.innerText || '').trim();
      m[t.textContent.trim()] = n;
    });
    const lines = (ok.innerText || '').split('\n').map(s => s.trim()).filter(Boolean);
    res.push({href, metrics: m, lines: lines.slice(0, 60)});
  }
  return res;
}
"""


def to_int(v):
    """「1,234」「1.2万」「3.5K」を数にする。空は0。"""
    t = str(v or "").replace(",", "").strip()
    m = re.match(r"^([0-9.]+)\s*(万|K|k|M)?$", t)
    if not m:
        return 0
    n = float(m.group(1))
    unit = m.group(2)
    return int(n * (10000 if unit == "万" else 1000 if unit in ("K", "k") else 1000000 if unit == "M" else 1))


def pick(metrics, *names):
    for n in names:
        for key, val in metrics.items():
            if n in key:
                return to_int(val)
    return 0


def normalize(raw):
    href = raw["href"]
    author = href.split("/")[1].lstrip("@") if href.startswith("/@") else ""
    lines = raw["lines"]
    time_label = lines[1] if len(lines) > 1 else ""
    body = [l for l in lines[2:] if not re.fullmatch(r"[0-9.,万KkM]+", l) and l not in ("もっと見る",)]
    m = raw["metrics"]
    return {
        "url": "https://www.threads.com" + href,
        "author": author,
        "time_label": time_label,
        "text": "\n".join(body),
        "likes": pick(m, "いいね"),
        "replies": pick(m, "返信", "コメント"),
        "reposts": pick(m, "再投稿"),
    }


def load_existing(path):
    data = {}
    if path.exists():
        # splitlines()は本文中の特殊な行区切り（U+2028等）でも切れるので使わない
        for line in path.read_text(encoding="utf-8").split(chr(10)):
            if line.strip():
                row = json.loads(line)
                data[row["url"]] = row
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", help="keywords.json のグループ名（省略で全部）")
    ap.add_argument("--max-keywords", type=int, default=0, help="テスト用：各グループの先頭N語だけ")
    ap.add_argument("--scrolls", type=int, default=6, help="1キーワードあたりのスクロール回数")
    ap.add_argument("--min-likes", type=int, default=10, help="これ未満のいいねは保存しない")
    ap.add_argument("--file", default="keywords.json", help="キーワード表のファイル名（候補を回すときは keyword_candidates.json）")
    ap.add_argument("--out", default="threads_posts.jsonl", help="research_data 内の保存ファイル名")
    ap.add_argument("--shuffle", action="store_true", help="キーワードの順番をランダムにする（順番の偏り・連続アクセスの癖を避ける）")
    ap.add_argument("--daily", action="store_true",
                    help="毎日の自動実行用：毎日の枠＋日替わり枠（前回の続き）だけ回す。同じ日の2回目はスキップ")
    ap.add_argument("--gap-min", type=int, default=0, help="語と語の間隔（秒）の下限。0なら 通常10／--daily は20")
    ap.add_argument("--gap-max", type=int, default=0, help="語と語の間隔（秒）の上限。0なら 通常20／--daily は40")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    gap_min = args.gap_min or (20 if args.daily else 10)
    gap_max = args.gap_max or (40 if args.daily else 20)

    if not STATE.exists():
        sys.exit("ログイン状態がありません。先に py -3 threads_login.py を実行してください。")
    cfg = json.loads((ROOT / args.file).read_text(encoding="utf-8"))
    jobs = []
    for gname, g in cfg["groups"].items():
        if args.group and gname != args.group:
            continue
        kws = g["keywords"][: args.max_keywords] if args.max_keywords else g["keywords"]
        jobs += [(gname, k) for k in kws]

    daily_state = None
    if args.daily:
        state_path = ROOT / "research_data" / "daily_state.json"
        daily_state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
        today = datetime.now().strftime("%Y-%m-%d")
        if daily_state.get("last_run_date") == today:
            print("今日はすでに実行済みです（%s）。スキップします。" % today)
            return
        group_of = {k: g for g, v in cfg["groups"].items() for k in v["keywords"]}
        fixed = [k for k in cfg.get("daily_fixed", []) if k in group_of]
        rest = [k for k in group_of if k not in fixed]
        size = cfg.get("rotation_size", 5)
        batches = [rest[i:i + size] for i in range(0, len(rest), size)] or [[]]
        nxt = daily_state.get("rotation_next", 0) % len(batches)
        jobs = [(group_of[k], k) for k in fixed + batches[nxt]]
        print("日替わり枠：%d/%d組目 ／ 毎日の枠%d語＋日替わり%d語" % (nxt + 1, len(batches), len(fixed), len(batches[nxt])))
    if args.shuffle:
        random.shuffle(jobs)
    out_path = ROOT / "research_data" / args.out
    data = load_existing(out_path)
    now = datetime.now().isoformat(timespec="seconds")
    new_count = upd_count = 0
    login_expired = False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(storage_state=str(STATE), locale="ja-JP", viewport={"width": 1280, "height": 2400})
        page = ctx.new_page()
        for idx, (group, kw) in enumerate(jobs):
            url = "https://www.threads.com/search?q=" + quote(kw) + "&serp_type=default"
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(6000)
            if "login" in page.url:
                login_expired = True
                print("ログインが切れています。py -3 threads_login.py をやり直してください。")
                break
            got = {}
            for _ in range(args.scrolls):
                for raw in page.evaluate(EXTRACT_JS):
                    got[raw["href"]] = raw
                page.mouse.wheel(0, 2400)
                page.wait_for_timeout(random.randint(2200, 3500))
            kept = 0
            for raw in got.values():
                row = normalize(raw)
                if row["likes"] < args.min_likes:
                    continue
                kept += 1
                old = data.get(row["url"])
                if old is None:
                    row.update({"first_seen": now, "last_seen": now, "groups": [group], "keywords": [kw]})
                    data[row["url"]] = row
                    new_count += 1
                else:
                    for k in ("likes", "replies", "reposts"):
                        old[k] = max(old.get(k, 0), row[k])
                    old["last_seen"] = now
                    if group not in old["groups"]:
                        old["groups"].append(group)
                    if kw not in old["keywords"]:
                        old["keywords"].append(kw)
                    upd_count += 1
            print("[%d/%d] %s / %s : 取得%d件 → 保存対象%d件" % (idx + 1, len(jobs), group, kw, len(got), kept))
            if idx < len(jobs) - 1:
                time.sleep(random.randint(gap_min, gap_max))
        browser.close()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for row in data.values():
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("新規 %d 件 / 既存の数字更新 %d 件 / 合計 %d 件 → %s" % (new_count, upd_count, len(data), out_path.relative_to(ROOT)))
    if login_expired:
        sys.exit(3)
    if daily_state is not None:
        daily_state["last_run_date"] = datetime.now().strftime("%Y-%m-%d")
        daily_state["rotation_next"] = daily_state.get("rotation_next", 0) + 1
        state_path.write_text(json.dumps(daily_state, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
