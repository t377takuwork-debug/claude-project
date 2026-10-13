"""Xの検索から、反響のある投稿を集めて溜める（Claudeのトークンは使わない）。

収集用のアカウントのログイン情報は x_cookies.local.json（gitに入れない・チャットに貼らない）。
  中身： {"auth_token": "...", "ct0": "..."}   ※ブラウザで調査用アカウントにログイン→Cookieから写す

使い方：  py -3 collect_x.py --daily           毎日の自動実行用（毎日の枠＋日替わり枠。同じ日の2回目はスキップ）
          py -3 collect_x.py --max-keywords 1  テスト（各グループの先頭1語だけ）
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


def build_query(keyword, min_faves, days):
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    # 返信は除く／日本語／反響の下限／期間
    return "%s min_faves:%d lang:ja -filter:replies since:%s" % (keyword, min_faves, since)


async def run(args):
    sys.stdout.reconfigure(encoding="utf-8")
    if not COOKIES.exists():
        print("x_cookies.local.json がありません。")
        return 4
    cfg = json.loads(KEYWORDS.read_text(encoding="utf-8"))
    group_of = {k: g for g, v in cfg["groups"].items() for k in v["keywords"]}

    state = {}
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
        keywords = fixed + batches[nxt]
        print("日替わり枠：%d/%d組目 ／ 毎日の枠%d語＋日替わり%d語" % (nxt + 1, len(batches), len(fixed), len(batches[nxt])))
    else:
        keywords = []
        for g, v in cfg["groups"].items():
            ks = v["keywords"][: args.max_keywords] if args.max_keywords else v["keywords"]
            keywords += ks
    jobs = [(group_of[k], k) for k in keywords]

    client = Client(language="ja")
    client.set_cookies(json.loads(COOKIES.read_text(encoding="utf-8")))
    data = load_existing()
    now = datetime.now().isoformat(timespec="seconds")
    new_count = upd_count = 0
    auth_failed = False
    errors = 0

    for idx, (group, kw) in enumerate(jobs):
        query = build_query(kw, args.min_faves, args.days)
        try:
            result = await client.search_tweet(query, "Top", count=20)
            tweets = list(result)
            for _ in range(args.pages - 1):
                if not tweets:
                    break
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
            screen = getattr(getattr(t, "user", None), "screen_name", "") or ""
            tid = getattr(t, "id", "")
            if not tid:
                continue
            url = "https://x.com/%s/status/%s" % (screen or "i", tid)
            created = getattr(t, "created_at_datetime", None)
            row = {
                "url": url,
                "platform": "x",
                "author": screen,
                "time_label": created.strftime("%Y/%m/%d %H:%M") if created else "",
                "text": getattr(t, "full_text", None) or getattr(t, "text", "") or "",
                "likes": int(getattr(t, "favorite_count", 0) or 0),
                "replies": int(getattr(t, "reply_count", 0) or 0),
                "reposts": int(getattr(t, "retweet_count", 0) or 0) + int(getattr(t, "quote_count", 0) or 0),
                "views": int(getattr(t, "view_count", 0) or 0) if str(getattr(t, "view_count", "")).isdigit() else 0,
            }
            kept += 1
            old = data.get(url)
            if old is None:
                row.update({"first_seen": now, "last_seen": now, "groups": [group], "keywords": [kw]})
                data[url] = row
                new_count += 1
            else:
                for k in ("likes", "replies", "reposts", "views"):
                    old[k] = max(old.get(k, 0), row[k])
                old["last_seen"] = now
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
        state["rotation_next"] = state.get("rotation_next", 0) + 1
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--daily", action="store_true")
    ap.add_argument("--max-keywords", type=int, default=0)
    ap.add_argument("--min-faves", type=int, default=100, help="この数以上のいいねの投稿だけ（検索の演算子）")
    ap.add_argument("--days", type=int, default=14, help="何日前からの投稿を探すか")
    ap.add_argument("--pages", type=int, default=2, help="1語あたりの取得ページ数（1ページ約20件）")
    ap.add_argument("--gap-min", type=int, default=20)
    ap.add_argument("--gap-max", type=int, default=40)
    args = ap.parse_args()
    sys.exit(asyncio.run(run(args)))


if __name__ == "__main__":
    main()
