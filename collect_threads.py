"""スレッズの検索（「最近」タブ）から、新しくて反響のある投稿を集めて溜める（Claudeのトークンは使わない）。

説明書：  docs/sop/sop_research_auto_collect.md
事前に：  py -3 threads_login.py  （調査用アカウントで、人の手でログイン。切れたらやり直す）
使い方：  py -3 collect_threads.py --daily            毎日の自動実行用（毎日の枠＋日替わり枠。同じ日の2回目はスキップ）
          py -3 collect_threads.py --max-keywords 1   テスト（各グループの先頭1語だけ）
保存先：  research_data/threads_posts.jsonl（1行1投稿。同じ投稿は数字だけ更新。30日より古いものは消す）
終了コード： 0=成功 3=ログイン切れ 5=途中で止まった 6=1件も取れなかった（画面の作りが変わった可能性）
"""
import argparse
import random
import re
import sys
import time
from datetime import datetime, timedelta
from urllib.parse import quote

from playwright.sync_api import sync_playwright

import research_common as rc

LOGIN_STATE = rc.ROOT / "threads_state.local.json"
OUT = rc.DATA_DIR / "threads_posts.jsonl"
STATE = rc.DATA_DIR / "daily_state.json"

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

REL_RE = re.compile(r"^(\d+)\s*(分|時間|日|週|年)$")
DATE_RE = re.compile(r"^(20\d{2})/(\d{1,2})/(\d{1,2})$")
REL_HOURS = {"分": 1 / 60.0, "時間": 1.0, "日": 24.0, "週": 24.0 * 7, "年": 24.0 * 365}
REPLY_RE = re.compile(r"^@?[\w.]+に返信$")


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


def find_time_label(lines):
    """投稿者名の下の行（先頭から数行）にある、投稿時刻の表示（「10分」「3時間」「2日」「2026/10/04」）を探す。
    投稿者名とテーマのタグ（例：AI副業）の次に出るため、位置は一定でない。"""
    for i, l in enumerate(lines[1:5], start=1):
        if REL_RE.match(l) or DATE_RE.match(l):
            return i, l
    return None, ""


def posted_at_from_label(label, now):
    m = REL_RE.match(label)
    if m:
        return now - timedelta(hours=int(m.group(1)) * REL_HOURS[m.group(2)])
    m = DATE_RE.match(label)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    return None


def normalize(raw, now=None):
    now = now or datetime.now()
    href = re.sub(r"/media$", "", raw["href"])  # 画像つき投稿の末尾「/media」を除き、同じ投稿を1つにまとめる
    author = href.split("/")[1].lstrip("@") if href.startswith("/@") else ""
    lines = raw["lines"]
    idx, label = find_time_label(lines)
    rest = [l for i, l in enumerate(lines[1:], start=1) if i != idx]
    if idx != 1 and rest:
        rest = rest[1:]  # 時刻表示より前の行（テーマのタグ）は本文に入れない。時刻表示がないときは2行目をタグとみなす
    body = [l for l in rest if not re.fullmatch(r"[0-9.,万KkM]+", l) and l != "もっと見る"]
    is_reply = any(REPLY_RE.match(l) for l in lines[1:6])  # 「@◯◯に返信」＝他人への返信。ネタの材料にしない
    m = raw["metrics"]
    p = posted_at_from_label(label, now) if label else None
    return {
        "url": "https://www.threads.com" + href,
        "platform": "threads",
        "author": author,
        "time_label": label,
        "posted_at": p.isoformat(timespec="seconds") if p else "",  # 時刻表示が読めなかったら空（候補にはしない）
        "text": "\n".join(body),
        "likes": pick(m, "いいね"),
        "replies": pick(m, "返信", "コメント"),
        "reposts": pick(m, "再投稿"),
        "is_reply": is_reply,
    }


def run(args):
    sys.stdout.reconfigure(encoding="utf-8")
    if not LOGIN_STATE.exists():
        print("ログイン状態がありません。先に py -3 threads_login.py を実行してください。")
        return rc.LOGIN_EXPIRED
    cfg = rc.platform_keywords(rc.KEYWORDS, "threads")
    group_of = rc.group_of_keywords(cfg)

    state = {}
    if args.daily:
        state = rc.load_state(STATE)
        today = datetime.now().strftime("%Y-%m-%d")
        if state.get("last_run_date") == today:
            print("今日はすでに実行済みです（%s）。スキップします。" % today)
            return rc.OK
        keywords, no, total, n_fixed = rc.daily_plan(cfg, state)
        print("日替わり枠：%d/%d組目 ／ 毎日の枠%d語＋日替わり%d語" % (no, total, n_fixed, len(keywords) - n_fixed))
    else:
        keywords = []
        for g, v in cfg["groups"].items():
            keywords += v["keywords"][: args.max_keywords] if args.max_keywords else v["keywords"]
    jobs = [(group_of[k], k) for k in keywords]
    gap_min, gap_max = (20, 40) if args.daily else (10, 20)

    data = rc.load_jsonl(OUT)
    now = rc.now_iso()
    new_count = upd_count = fetched = errors = done = tab_fail = 0
    login_expired = False

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(storage_state=str(LOGIN_STATE), locale="ja-JP", viewport={"width": 1280, "height": 2400})
            page = ctx.new_page()
            for idx, (group, kw) in enumerate(jobs):
                try:
                    page.goto("https://www.threads.com/search?q=" + quote(kw) + "&serp_type=default",
                              wait_until="domcontentloaded", timeout=45000)
                    page.wait_for_timeout(6000)
                    if "login" in page.url:
                        login_expired = True
                        print("ログインが切れています。py -3 threads_login.py をやり直してください。")
                        break
                    # 「最近」タブに切り替える（2026-10-14の実測：「上位」タブは古い人気投稿が中心で、48時間以内・いいね100以上が0件）
                    try:
                        page.get_by_text("最近", exact=True).first.click(timeout=5000)
                        page.wait_for_timeout(4500)
                    except Exception:
                        tab_fail += 1
                        print("  （「最近」タブに切り替えられませんでした。この語は飛ばします）")
                        continue
                    got = {}
                    for _ in range(args.scrolls):
                        for raw in page.evaluate(EXTRACT_JS):
                            got[raw["href"]] = raw
                        page.mouse.wheel(0, 2400)
                        page.wait_for_timeout(random.randint(2200, 3500))
                except Exception as e:  # 通信の失敗・時間切れなど。この語だけ飛ばして続ける
                    errors += 1
                    print("[%d/%d] %s / %s : エラー（%s）" % (idx + 1, len(jobs), group, kw, type(e).__name__))
                    if errors >= 3:
                        print("エラーが3回続いたため、ここで止めます。")
                        break
                    continue
                fetched += len(got)
                kept = 0
                for raw in got.values():
                    row = normalize(raw)
                    if row.pop("is_reply") or row["likes"] < args.min_likes:
                        continue  # 返信と、反響の小さい投稿は保存しない
                    kept += 1
                    if rc.merge_row(data, row, now, group, kw) == "new":
                        new_count += 1
                    else:
                        upd_count += 1
                done += 1
                print("[%d/%d] %s / %s : 取得%d件 → 保存対象%d件" % (idx + 1, len(jobs), group, kw, len(got), kept))
                if idx < len(jobs) - 1:
                    time.sleep(random.randint(gap_min, gap_max))
            browser.close()
    finally:  # 途中で止まっても、そこまでの分は必ず保存する
        kept_rows, pruned = rc.save_jsonl(OUT, data)
        print("新規 %d 件 / 既存の数字更新 %d 件 / 合計 %d 件（古い%d件を整理） → %s" % (
            new_count, upd_count, kept_rows, pruned, OUT.relative_to(rc.ROOT)))

    if login_expired:
        code = rc.LOGIN_EXPIRED
    elif jobs and fetched == 0:
        code = rc.NOTHING_FOUND  # 1件も読めない＝画面の作りが変わった・タブが見つからない可能性
        print("1件も取れませんでした。画面の作りが変わった可能性があります。")
    elif done < len(jobs):
        code = rc.INCOMPLETE
    else:
        code = rc.OK
    rc.write_status("threads", {"exit_code": code, "keywords": len(jobs), "done": done, "fetched": fetched,
                                "new": new_count, "updated": upd_count, "errors": errors, "tab_fail": tab_fail})
    if args.daily and code == rc.OK:
        state["last_run_date"] = datetime.now().strftime("%Y-%m-%d")
        state["last_run_at"] = now
        state["rotation_next"] = state.get("rotation_next", 0) + 1
        rc.save_state(STATE, state)
    return code


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--daily", action="store_true", help="毎日の自動実行用：毎日の枠＋日替わり枠（前回の続き）。同じ日の2回目はスキップ")
    ap.add_argument("--max-keywords", type=int, default=0, help="テスト用：各グループの先頭N語だけ")
    ap.add_argument("--scrolls", type=int, default=5, help="1キーワードあたりのスクロール回数")
    ap.add_argument("--min-likes", type=int, default=10, help="これ未満のいいねは保存しない（候補にするのは、make_shortlist.py の下限以上）")
    sys.exit(run(ap.parse_args()))


if __name__ == "__main__":
    main()
