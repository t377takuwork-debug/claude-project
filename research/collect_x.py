"""Xの検索から、新しくて反響のある投稿を集めて溜める（Claudeのトークンは使わない）。

説明書：  docs/sop/sop_research_auto_collect.md
2種類を集める：
  ①キーワード検索   keywords.json の「x」の表（毎日の枠＋日替わり枠）。前回の収集時刻から（最短24時間・最大7日）
  ②アカウント起点   watch_accounts.json の観察対象（from:アカウント名。1日 per_day 人ずつ巡回）
収集用のアカウントのログイン情報は x_cookies.local.json（gitに入れない・チャットに貼らない）。

使い方：  py -3 research/collect_x.py --daily               毎日の自動実行用（同じ日の2回目はスキップ）
          py -3 research/collect_x.py --max-keywords 1      テスト（各グループの先頭1語だけ。アカウントは回さない）
          py -3 research/collect_x.py --only-accounts --max-accounts 2   アカウント起点だけ、先頭2人で試す
保存先：  research/data/x_posts.jsonl（スレッズ側と同じ形式。30日より古いものは消す）
終了コード： 0=成功 4=ログイン情報が使えない 5=途中で止まった（回数制限など） 6=1件も取れなかった
"""
import argparse
import asyncio
import json
import random
import sys
from datetime import datetime, timedelta

from twikit import Client

import research_common as rc

COOKIES = rc.ROOT / "x_cookies.local.json"
ACCOUNTS = rc.ROOT / "watch_accounts.json"
OUT = rc.DATA_DIR / "x_posts.jsonl"
STATE = rc.DATA_DIR / "daily_state_x.json"
AUTH_ERRORS = ("Unauthorized", "Forbidden", "AccountSuspended", "AccountLocked")


def tweet_to_row(t):
    screen = getattr(getattr(t, "user", None), "screen_name", "") or ""
    tid = getattr(t, "id", "")
    if not tid:
        return None
    created = getattr(t, "created_at_datetime", None)
    views = getattr(t, "view_count", 0)
    return {
        "url": "https://x.com/%s/status/%s" % (screen or "i", tid),
        "platform": "x",
        "author": screen,
        "followers": int(getattr(getattr(t, "user", None), "followers_count", 0) or 0),
        # 投稿日時（このPCの時刻）。候補の「新しさ」の判定に使う
        "posted_at": created.astimezone().replace(tzinfo=None).isoformat(timespec="seconds") if created else "",
        "text": getattr(t, "full_text", None) or getattr(t, "text", "") or "",
        "likes": int(getattr(t, "favorite_count", 0) or 0),
        "replies": int(getattr(t, "reply_count", 0) or 0),
        "reposts": int(getattr(t, "retweet_count", 0) or 0) + int(getattr(t, "quote_count", 0) or 0),
        "views": int(views) if str(views).isdigit() else 0,
        # ブックマーク数は、twikitの公開項目にはないが、元のデータ（_legacy）に入っている
        "bookmarks": int((getattr(t, "_legacy", None) or {}).get("bookmark_count", 0) or 0),
    }


async def run(args):
    sys.stdout.reconfigure(encoding="utf-8")
    if not COOKIES.exists():
        print("x_cookies.local.json がありません。")
        return rc.COOKIE_INVALID
    cfg = rc.platform_keywords(rc.KEYWORDS, "x")
    group_of = rc.group_of_keywords(cfg)
    acc_cfg = json.loads(ACCOUNTS.read_text(encoding="utf-8")) if ACCOUNTS.exists() else {"accounts": []}
    acc_list = [a for a in acc_cfg["accounts"] if a.get("enabled", True)]

    state = {}
    kw_jobs, acc_jobs = [], []
    hours = args.hours
    if args.daily:
        state = rc.load_state(STATE)
        today = datetime.now().strftime("%Y-%m-%d")
        if state.get("last_run_date") == today:
            print("今日はすでに実行済みです（%s）。スキップします。" % today)
            return rc.OK
        kw_jobs, no, total, n_fixed = rc.daily_plan(cfg, state)
        print("日替わり枠：%d/%d組目 ／ 毎日の枠%d語＋日替わり%d語" % (no, total, n_fixed, len(kw_jobs) - n_fixed))
        if acc_list:
            start = state.get("account_rotation_next", 0) % len(acc_list)
            n = min(acc_cfg.get("per_day", 4), len(acc_list))
            acc_jobs = [acc_list[(start + i) % len(acc_list)] for i in range(n)]
            print("アカウント起点：%d/%d人目から%d人" % (start + 1, len(acc_list), n))
        if state.get("last_run_at"):
            # 前回の収集時刻から（最短24時間・最大7日。1時間は余裕）。PCを使わない日があっても、抜けが出ない
            gap_h = (datetime.now() - datetime.fromisoformat(state["last_run_at"])).total_seconds() / 3600.0
            hours = min(max(args.hours, gap_h + 1), 24 * 7)
            print("検索期間：直近%.0f時間（前回の収集は %.0f時間前）" % (hours, gap_h))
    elif args.only_accounts:
        acc_jobs = acc_list[: args.max_accounts] if args.max_accounts else acc_list
    else:
        for g, v in cfg["groups"].items():
            kw_jobs += v["keywords"][: args.max_keywords] if args.max_keywords else v["keywords"]

    # 検索の一覧。since_time（秒）なら、時間単位で絞れる（since: は日単位）
    since_ts = int(datetime.now().timestamp() - hours * 3600)
    acc_since = (datetime.now() - timedelta(days=acc_cfg.get("since_days", 6))).strftime("%Y-%m-%d")
    jobs = []
    for k in kw_jobs:
        jobs.append({"group": group_of[k], "label": k, "product": "Top", "pages": args.pages, "extra": {},
                     "min_faves": args.min_faves,
                     "query": "%s min_faves:%d lang:ja -filter:replies since_time:%d" % (k, args.min_faves, since_ts)})
    for a in acc_jobs:
        jobs.append({"group": a["group"], "label": "@" + a["name"], "product": "Latest", "pages": 1,
                     "extra": {"source": "account", "min_faves": a["min_faves"]}, "min_faves": a["min_faves"],
                     "query": "from:%s min_faves:%d -filter:replies -filter:retweets since:%s" % (
                         a["name"], a["min_faves"], acc_since)})

    client = Client(language="ja")
    client.set_cookies(json.loads(COOKIES.read_text(encoding="utf-8")))
    data = rc.load_jsonl(OUT)
    now = rc.now_iso()
    new_count = upd_count = fetched = errors = done = 0
    auth_failed = False

    try:
        for idx, job in enumerate(jobs):
            group, kw = job["group"], job["label"]
            try:
                result = await client.search_tweet(job["query"], job["product"], count=20)
                tweets = list(result)
                for _ in range(job["pages"] - 1):
                    # Xの「Top」は、条件に合う投稿が尽きると、条件外の投稿で次のページを埋める。尽きたら取りに行かない
                    if not tweets or int(getattr(tweets[-1], "favorite_count", 0) or 0) < job["min_faves"]:
                        break
                    await asyncio.sleep(random.uniform(3, 6))
                    result = await result.next()
                    if not result:
                        break
                    tweets += list(result)
            except Exception as e:  # twikit の例外は種類が多いので、名前で見分ける
                name = type(e).__name__
                if name in AUTH_ERRORS or "401" in str(e) or "403" in str(e):
                    auth_failed = True
                    print("ログイン情報が使えません（%s）。Cookieの取り直しが必要です。" % name)
                    break
                errors += 1
                print("[%d/%d] %s / %s : エラー（%s）" % (idx + 1, len(jobs), group, kw, name))
                if name == "TooManyRequests" or errors >= 3:
                    print("回数制限か連続エラーのため、ここで止めます。")
                    break
                await asyncio.sleep(random.uniform(args.gap_min, args.gap_max))
                continue

            kept = 0
            for t in tweets:
                row = tweet_to_row(t)
                if row is None or row["likes"] < job["min_faves"]:
                    continue  # 条件外の投稿（上のとおり、Xが混ぜてくる）は保存しない
                row.update(job["extra"])
                kept += 1
                if rc.merge_row(data, row, now, group, kw) == "new":
                    new_count += 1
                else:
                    upd_count += 1
            fetched += kept
            done += 1
            print("[%d/%d] %s / %s : 取得%d件" % (idx + 1, len(jobs), group, kw, kept))
            if idx < len(jobs) - 1:
                await asyncio.sleep(random.uniform(args.gap_min, args.gap_max))
    finally:  # 途中で止まっても、そこまでの分は必ず保存する
        kept_rows, pruned = rc.save_jsonl(OUT, data)
        print("新規 %d 件 / 既存の数字更新 %d 件 / 合計 %d 件（古い%d件を整理） → %s" % (
            new_count, upd_count, kept_rows, pruned, OUT.relative_to(rc.REPO)))

    if auth_failed:
        code = rc.COOKIE_INVALID
    elif done < len(jobs):
        code = rc.INCOMPLETE  # 回数制限・連続エラー。「実行済み」にしないので、次のログイン時にやり直す
    elif kw_jobs and fetched == 0:
        code = rc.NOTHING_FOUND
        print("1件も取れませんでした。検索の仕組みが変わった可能性があります。")
    else:
        code = rc.OK
    rc.write_status("x", {"exit_code": code, "keywords": len(kw_jobs), "accounts": len(acc_jobs), "done": done,
                          "fetched": fetched, "new": new_count, "updated": upd_count, "errors": errors,
                          "window_hours": round(hours)})
    if args.daily and code == rc.OK:
        state["last_run_date"] = datetime.now().strftime("%Y-%m-%d")
        state["last_run_at"] = now
        state["rotation_next"] = state.get("rotation_next", 0) + 1
        state["account_rotation_next"] = state.get("account_rotation_next", 0) + len(acc_jobs)
        rc.save_state(STATE, state)
    return code


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--daily", action="store_true", help="毎日の自動実行用（キーワード＋アカウント起点。同じ日の2回目はスキップ）")
    ap.add_argument("--max-keywords", type=int, default=0, help="テスト用：各グループの先頭N語だけ")
    ap.add_argument("--only-accounts", action="store_true", help="アカウント起点だけ集める（テスト用）")
    ap.add_argument("--max-accounts", type=int, default=0)
    ap.add_argument("--min-faves", type=int, default=100, help="キーワード検索：この数以上のいいねの投稿だけ")
    ap.add_argument("--hours", type=int, default=24, help="キーワード検索：直近何時間の投稿を探すか（--daily は、前回の収集時刻からに自動で広がる）")
    ap.add_argument("--pages", type=int, default=2, help="キーワード検索：1語あたりの取得ページ数（1ページ約20件）")
    ap.add_argument("--gap-min", type=int, default=20)
    ap.add_argument("--gap-max", type=int, default=40)
    args = ap.parse_args()
    sys.exit(asyncio.run(run(args)))


if __name__ == "__main__":
    main()
