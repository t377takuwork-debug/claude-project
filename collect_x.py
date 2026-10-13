"""Xの検索から、反響のある投稿を集めて溜める（Claudeのトークンは使わない）。

2種類を集める：
  ①キーワード検索   keywords.json の「x」の表（毎日の枠＋日替わり枠）
  ②アカウント起点   watch_accounts.json の観察対象（from:アカウント名。1日 per_day 件ずつ巡回）
収集用のアカウントのログイン情報は x_cookies.local.json（gitに入れない・チャットに貼らない）。
  中身： {"auth_token": "...", "ct0": "..."}   ※ブラウザで調査用アカウントにログイン→Cookieから写す

使い方：  py -3 collect_x.py --daily               毎日の自動実行用（同じ日の2回目はスキップ）
          py -3 collect_x.py --max-keywords 1      テスト（各グループの先頭1語だけ。アカウントは回さない）
          py -3 collect_x.py --only-accounts --max-accounts 2   アカウント起点だけ、先頭2つで試す
保存先：  research_data/x_posts.jsonl（スレッズ側と同じ形式。make_shortlist.py が両方を読む）
終了コード： 0=成功 4=ログイン情報が使えない（Cookieの取り直しが必要）
"""
import argparse
import asyncio
import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

from twikit import Client

ROOT = Path(__file__).resolve().parent
COOKIES = ROOT / "x_cookies.local.json"
KEYWORDS = ROOT / "keywords.json"
ACCOUNTS = ROOT / "watch_accounts.json"
OUT = ROOT / "research_data" / "x_posts.jsonl"
STATE = ROOT / "research_data" / "daily_state_x.json"


def load_existing():
    data = {}
    if OUT.exists():
        # splitlines()は本文中の特殊な行区切り（U+2028等）でも切れるので使わない
        for line in OUT.read_text(encoding="utf-8").split(chr(10)):
            if line.strip():
                row = json.loads(line)
                data[row["url"]] = row
    return data


def since_date(days):
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


def tweet_to_row(t):
    screen = getattr(getattr(t, "user", None), "screen_name", "") or ""
    tid = getattr(t, "id", "")
    if not tid:
        return None
    created = getattr(t, "created_at_datetime", None)
    return {
        "url": "https://x.com/%s/status/%s" % (screen or "i", tid),
        "platform": "x",
        "author": screen,
        "followers": int(getattr(getattr(t, "user", None), "followers_count", 0) or 0),
        "time_label": created.strftime("%Y/%m/%d %H:%M") if created else "",
        "posted_at": created.astimezone().replace(tzinfo=None).isoformat(timespec="seconds") if created else "",
        "text": getattr(t, "full_text", None) or getattr(t, "text", "") or "",
        "likes": int(getattr(t, "favorite_count", 0) or 0),
        "replies": int(getattr(t, "reply_count", 0) or 0),
        "reposts": int(getattr(t, "retweet_count", 0) or 0) + int(getattr(t, "quote_count", 0) or 0),
        "views": int(getattr(t, "view_count", 0) or 0) if str(getattr(t, "view_count", "")).isdigit() else 0,
        # ブックマーク数は、twikitの公開項目にはないが、元のデータ（_legacy）に入っている
        "bookmarks": int((getattr(t, "_legacy", None) or {}).get("bookmark_count", 0) or 0),
    }


async def run(args):
    sys.stdout.reconfigure(encoding="utf-8")
    if not COOKIES.exists():
        print("x_cookies.local.json がありません。")
        return 4
    cfg = json.loads(KEYWORDS.read_text(encoding="utf-8"))
    if "platforms" in cfg:  # 媒体別の表（keywords.json v3以降）
        cfg = cfg["platforms"]["x"]
    group_of = {k: g for g, v in cfg["groups"].items() for k in v["keywords"]}
    acc_cfg = json.loads(ACCOUNTS.read_text(encoding="utf-8")) if ACCOUNTS.exists() else {"accounts": []}
    acc_list = [a for a in acc_cfg["accounts"] if a.get("enabled", True)]

    state = {}
    kw_jobs, acc_jobs = [], []
    if args.daily:
        state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
        today = datetime.now().strftime("%Y-%m-%d")
        if state.get("last_run_date") == today:
            print("今日はすでに実行済みです（%s）。スキップします。" % today)
            return 0
        fixed = [k for k in cfg.get("daily_fixed", []) if k in group_of]
        rest = [k for k in group_of if k not in fixed]
        size = cfg.get("rotation_size", 5)
        batches = [rest[i:i + size] for i in range(0, len(rest), size)] or [[]]
        nxt = state.get("rotation_next", 0) % len(batches)
        kw_jobs = fixed + batches[nxt]
        print("日替わり枠：%d/%d組目 ／ 毎日の枠%d語＋日替わり%d語" % (nxt + 1, len(batches), len(fixed), len(batches[nxt])))
        if acc_list and not args.no_accounts:
            per = acc_cfg.get("per_day", 4)
            start = state.get("account_rotation_next", 0) % len(acc_list)
            acc_jobs = [acc_list[(start + i) % len(acc_list)] for i in range(min(per, len(acc_list)))]
            print("アカウント起点：%d/%d人目から%d人" % (start + 1, len(acc_list), len(acc_jobs)))
    elif args.only_accounts:
        acc_jobs = acc_list[: args.max_accounts] if args.max_accounts else acc_list
    else:
        for g, v in cfg["groups"].items():
            ks = v["keywords"][: args.max_keywords] if args.max_keywords else v["keywords"]
            kw_jobs += ks

    # キーワード検索の期間：毎日の実行なら「前回の収集日から」（＝前日以降。PCを使わない日があれば、その日数ぶん広げる。最大7日）
    # since_time（秒）なら、24時間ちょうどで絞れる（since: は日単位）
    hours = args.hours
    if args.daily and state.get("last_run_at"):
        gap_h = (datetime.now() - datetime.fromisoformat(state["last_run_at"])).total_seconds() / 3600.0
        hours = min(max(args.hours, gap_h + 1), 24 * 7)  # 前回の収集時刻から（最短24時間・最大7日）。1時間は余裕
        print("検索期間：直近%.0f時間（前回の収集は %.0f時間前）" % (hours, gap_h))
    kw_since = int(datetime.now().timestamp() - hours * 3600)
    run_started_at = datetime.now().isoformat(timespec="seconds")

    # 検索の一覧（種類・グループ・表示名・検索式・並び・ページ数・追加の項目）
    jobs = []
    for k in kw_jobs:
        q = "%s min_faves:%d lang:ja -filter:replies since_time:%d" % (k, args.min_faves, kw_since)
        jobs.append({"kind": "keyword", "group": group_of[k], "label": k, "query": q, "product": "Top",
                     "pages": args.pages, "extra": {}, "min_faves": args.min_faves})
    for a in acc_jobs:
        q = "from:%s min_faves:%d -filter:replies -filter:retweets since:%s" % (
            a["name"], a["min_faves"], since_date(acc_cfg.get("since_days", 10)))
        jobs.append({"kind": "account", "group": a["group"], "label": "@" + a["name"], "query": q, "product": "Latest",
                     "pages": 1, "extra": {"source": "account", "min_faves": a["min_faves"]}, "min_faves": a["min_faves"]})

    client = Client(language="ja")
    client.set_cookies(json.loads(COOKIES.read_text(encoding="utf-8")))
    data = load_existing()
    now = datetime.now().isoformat(timespec="seconds")
    new_count = upd_count = 0
    auth_failed = False
    errors = 0

    for idx, job in enumerate(jobs):
        group, kw = job["group"], job["label"]
        try:
            result = await client.search_tweet(job["query"], job["product"], count=20)
            tweets = list(result)
            for _ in range(job["pages"] - 1):
                if not tweets:
                    break
                if int(getattr(tweets[-1], "favorite_count", 0) or 0) < job["min_faves"]:
                    break  # 条件に合う投稿が尽きている
                await asyncio.sleep(random.uniform(3, 6))
                result = await result.next()
                if not result:
                    break
                tweets += list(result)
        except Exception as e:  # twikit の例外は種類が多いので、名前で見分ける
            name = type(e).__name__
            if name in ("Unauthorized", "Forbidden", "AccountSuspended", "AccountLocked") or "401" in str(e) or "403" in str(e):
                auth_failed = True
                print("ログイン情報が使えません（%s）。Cookieの取り直しが必要です。" % name)
                break
            errors += 1
            print("[%d/%d] %s / %s : エラー（%s）" % (idx + 1, len(jobs), group, kw, name))
            if name in ("TooManyRequests",) or errors >= 3:
                print("回数制限か連続エラーのため、ここで止めます。")
                break
            await asyncio.sleep(random.uniform(args.gap_min, args.gap_max))
            continue

        kept = 0
        for t in tweets:
            row = tweet_to_row(t)
            if row is None or row["likes"] < job["min_faves"]:
                continue
            row.update(job["extra"])
            kept += 1
            old = data.get(row["url"])
            if old is None:
                row.update({"first_seen": now, "last_seen": now, "groups": [group], "keywords": [kw]})
                data[row["url"]] = row
                new_count += 1
            else:
                for k in ("likes", "replies", "reposts", "views", "bookmarks", "followers"):
                    old[k] = max(old.get(k, 0), row.get(k, 0))
                old["last_seen"] = now
                if job["extra"]:  # アカウント起点で見つけた投稿は、そのしきい値で判定できるように印をつける
                    old.update(job["extra"])
                if group not in old["groups"]:
                    old["groups"].append(group)
                if kw not in old["keywords"]:
                    old["keywords"].append(kw)
                upd_count += 1
        print("[%d/%d] %s / %s : 取得%d件" % (idx + 1, len(jobs), group, kw, kept))
        if idx < len(jobs) - 1:
            await asyncio.sleep(random.uniform(args.gap_min, args.gap_max))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for row in data.values():
            f.write(json.dumps(row, ensure_ascii=False) + chr(10))
    print("新規 %d 件 / 既存の数字更新 %d 件 / 合計 %d 件 → %s" % (new_count, upd_count, len(data), OUT.relative_to(ROOT)))
    if auth_failed:
        return 4
    if args.daily and errors < 3:
        state["last_run_date"] = datetime.now().strftime("%Y-%m-%d")
        state["last_run_at"] = run_started_at
        state["rotation_next"] = state.get("rotation_next", 0) + 1
        if acc_jobs:
            state["account_rotation_next"] = state.get("account_rotation_next", 0) + len(acc_jobs)
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--daily", action="store_true")
    ap.add_argument("--max-keywords", type=int, default=0)
    ap.add_argument("--only-accounts", action="store_true", help="アカウント起点だけ集める（テスト用）")
    ap.add_argument("--max-accounts", type=int, default=0)
    ap.add_argument("--no-accounts", action="store_true", help="--daily でもアカウント起点を回さない")
    ap.add_argument("--min-faves", type=int, default=100, help="キーワード検索：この数以上のいいねの投稿だけ（24時間以内で100。件数が足りない語は50に下げる）")
    ap.add_argument("--hours", type=int, default=24, help="キーワード検索：直近何時間の投稿を探すか。--daily は、前回の収集時刻から（最短この時間・最大7日）")
    ap.add_argument("--pages", type=int, default=2, help="キーワード検索：1語あたりの取得ページ数（1ページ約20件）")
    ap.add_argument("--gap-min", type=int, default=20)
    ap.add_argument("--gap-max", type=int, default=40)
    args = ap.parse_args()
    sys.exit(asyncio.run(run(args)))


if __name__ == "__main__":
    main()
