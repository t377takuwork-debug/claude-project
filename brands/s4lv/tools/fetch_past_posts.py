#!/usr/bin/env python3
"""Fetch this account's past Threads posts directly from the Threads API,
including posts made outside the automation queue (e.g. manual posts),
along with their insights.

Usage:
  python fetch_past_posts.py [--limit N] [--full]

--limit caps how many posts are fetched (default 50, across pagination).
--full prints full post text (newlines flattened) instead of the default
30-character preview; useful when analyzing what made specific posts work.
Read-only: lists posts via GET /{threads_user_id}/threads, then fetches
insights per post via GET /{media_id}/insights. Prints a markdown table;
does not write anything to the spreadsheet (unlike fetch_insights.py,
which reads back what collectInsights already wrote).

Auth: tools/threads_auth.local.json (access_token, threads_user_id).
Note: this file is a manually-refreshed diagnostic copy, not the token
actually used for scheduled posting (that lives in Apps Script Script
Properties). Run threads_connect_test.ps1 -Step refresh first if this
script reports an auth error.
"""
import json
import sys
from pathlib import Path

import requests

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

TOOLS_DIR = Path(__file__).resolve().parent
AUTH_FILE = TOOLS_DIR / "threads_auth.local.json"
BASE = "https://graph.threads.net/v1.0"
DEFAULT_LIMIT = 50


def load_auth():
    if not AUTH_FILE.exists():
        print(f"ERROR: auth file not found: {AUTH_FILE}")
        sys.exit(1)
    auth = json.loads(AUTH_FILE.read_text(encoding="utf-8-sig"))
    if not auth.get("access_token") or not auth.get("threads_user_id"):
        print("ERROR: threads_auth.local.json is missing access_token or threads_user_id.")
        sys.exit(1)
    return auth["access_token"], auth["threads_user_id"]


def list_posts(token, user_id, limit):
    posts = []
    url = f"{BASE}/{user_id}/threads"
    params = {"fields": "id,text,timestamp,permalink", "access_token": token, "limit": min(limit, 25)}
    while url and len(posts) < limit:
        resp = requests.get(url, params=params if "?" not in url else None)
        body = resp.json()
        if resp.status_code >= 300:
            msg = body.get("error", {}).get("message", resp.text)
            print(f"ERROR: 投稿一覧の取得に失敗しました: {msg}")
            sys.exit(1)
        posts.extend(body.get("data", []))
        url = body.get("paging", {}).get("next")
        params = None  # cursor URL already includes all query params
    return posts[:limit]


def fetch_insights(token, media_id):
    url = f"{BASE}/{media_id}/insights"
    params = {"metric": "views,likes,replies,reposts,quotes", "access_token": token}
    resp = requests.get(url, params=params)
    body = resp.json()
    if resp.status_code >= 300:
        msg = body.get("error", {}).get("message", resp.text)
        return None, msg
    metrics = {}
    for m in body.get("data", []):
        if "total_value" in m:
            metrics[m["name"]] = m["total_value"]["value"]
        elif m.get("values"):
            metrics[m["name"]] = m["values"][-1]["value"]
    return metrics, None


def main():
    limit = DEFAULT_LIMIT
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            limit = int(sys.argv[idx + 1])
    full_text = "--full" in sys.argv

    token, user_id = load_auth()
    posts = list_posts(token, user_id, limit)

    if not posts:
        print("投稿が見つかりませんでした。")
        return

    text_label = "本文（全文）" if full_text else "本文（先頭30字）"
    header = ["投稿ID", "投稿日時", text_label, "Views", "Likes", "Replies", "Reposts", "Quotes"]
    print("| " + " | ".join(header) + " |")
    print("|" + "---|" * len(header))

    fetch_errors = []
    for post in posts:
        metrics, err = fetch_insights(token, post["id"])
        raw_text = (post.get("text") or "").replace("\n", " ")
        text = raw_text if full_text else raw_text[:30]
        timestamp = post.get("timestamp", "")
        if err:
            fetch_errors.append((post["id"], err))
            row = [post["id"], timestamp, text, "?", "?", "?", "?", "?"]
        else:
            row = [
                post["id"], timestamp, text,
                str(metrics.get("views", 0)), str(metrics.get("likes", 0)),
                str(metrics.get("replies", 0)), str(metrics.get("reposts", 0)),
                str(metrics.get("quotes", 0)),
            ]
        print("| " + " | ".join(row) + " |")

    print(f"\n{len(posts)}件取得しました。")
    if fetch_errors:
        print(f"\n[WARN] インサイト取得に失敗した投稿が{len(fetch_errors)}件あります:")
        for post_id, err in fetch_errors:
            print(f"  - {post_id}: {err}")


if __name__ == "__main__":
    main()
