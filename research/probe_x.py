"""Xで、新しいキーワードの候補を1回ずつ検索して、当たり外れを測る（語を見直すときだけ使う。毎日の収集とは別）。

説明書：  docs/sop/sop_research_auto_collect.md 「語を見直すとき」
使い方：  py -3 research/probe_x.py [--min-faves N] [--hours H] [--dump ファイル] 語1 "語 2" "(A OR B) 恋愛"
          条件の既定は、毎日の収集と同じ（直近24時間・いいね100以上・日本語・返信を除く）。
          --min-faves と --hours で、いいねの下限と新しさ（時間）を変えられる。
          --dump を付けると、拾った投稿を jsonl で保存する（目で確かめるとき用）。
出力：    画面に採点表を出す（保存は --dump のときだけ）。1回に試すのは20語まで（回数制限に当たるため）。
          保存（ブックマーク）の数・保存率（保存÷表示）・分野に合う率（機械の判定。目安）も出す
"""
import asyncio
import json
import random
import re
import statistics as st
import sys
from collections import Counter
from datetime import datetime

from twikit import Client

import research_common as rc

MIN_FAVES, HOURS, MAX_WORDS = 100, 24, 20

# 分野に合う投稿かの機械判定（目安。最後は目で確かめる）。MBTI・創作・ファン活動の話は外す
TOPIC = re.compile(
    r"Claude|クロード|ChatGPT|チャッピー|Codex|Gemini|Cursor|プロンプト|ブログ|SEO|アフィリ|副業|note|Threads|スレッズ|"
    r"X運用|SNS運用|インプレ|自動化|MCP|エージェント|スキル|NotebookLM|Obsidian|Notion|検索流入|AIO|LLMO|アルゴリズム")
NOISE = re.compile(r"MBTI|INFJ|INTJ|ENFP|恋愛|未練|イラスト|ガチャ|二次創作|推し|おは[よぽ]")


def n(t, name):
    return int(getattr(t, name, 0) or 0)


def bookmarks(t):
    return int((getattr(t, "_legacy", None) or {}).get("bookmark_count", 0) or 0)


def views(t):
    v = getattr(t, "view_count", 0)
    return int(v) if str(v).isdigit() else 0


def on_topic(t):
    text = getattr(t, "full_text", None) or getattr(t, "text", "") or ""
    return bool(TOPIC.search(text)) and not NOISE.search(text)


async def main(words, min_faves, hours, dump):
    sys.stdout.reconfigure(encoding="utf-8")
    client = Client(language="ja")
    client.set_cookies(json.loads((rc.ROOT / "x_cookies.local.json").read_text(encoding="utf-8")))
    since_ts = int(datetime.now().timestamp() - hours * 3600)
    per = {}
    for i, w in enumerate(words):
        q = "%s min_faves:%d lang:ja -filter:replies since_time:%d" % (w, min_faves, since_ts)
        try:
            res = await client.search_tweet(q, "Top", count=20)
            tw = [t for t in res if n(t, "favorite_count") >= min_faves]
            if len(tw) >= 20:  # 1ページ目がすべて条件を満たすときだけ、次のページを取る
                await asyncio.sleep(random.uniform(3, 6))
                nxt = await res.next()
                tw += [t for t in (nxt or []) if n(t, "favorite_count") >= min_faves]
            per[w] = tw
        except Exception as e:
            print("[%d/%d] %s : エラー %s" % (i + 1, len(words), w, type(e).__name__))
            if type(e).__name__ in ("Unauthorized", "Forbidden", "TooManyRequests"):
                break
            per[w] = []
        if i < len(words) - 1:
            await asyncio.sleep(random.uniform(12, 20))

    seen = Counter(t.id for tw in per.values() for t in tw)
    print("条件：いいね%d以上・直近%d時間・日本語・返信を除く" % (min_faves, hours))
    print("| 語 | 件数 | 保存100以上 | 保存率の中央値 | 分野に合う率 | 保存100以上かつ分野に合う | 投稿者数 | 他の語と重複 |")
    print("|---|---|---|---|---|---|---|---|")
    rows = []
    for w, tw in per.items():
        if not tw:
            rows.append((0, 0, "| %s | 0 | − | − | − | − | − | − |" % w))
            continue
        bm100 = [t for t in tw if bookmarks(t) >= 100]
        rates = [100.0 * bookmarks(t) / views(t) for t in tw if views(t)]
        ontopic = [t for t in tw if on_topic(t)]
        good = [t for t in bm100 if on_topic(t)]
        rows.append((len(good), len(tw), "| %s | %d | %d | %s | %d%% | %d | %d | %d |" % (
            w, len(tw), len(bm100), ("%.2f%%" % st.median(rates)) if rates else "−",
            round(100.0 * len(ontopic) / len(tw)), len(good),
            len({t.user.screen_name for t in tw}), sum(1 for t in tw if seen[t.id] > 1))))
    for _, _, line in sorted(rows, key=lambda x: (-x[0], -x[1])):
        print(line)

    if dump:
        with open(dump, "w", encoding="utf-8") as f:
            for w, tw in per.items():
                for t in tw:
                    f.write(json.dumps({
                        "word": w, "url": "https://x.com/%s/status/%s" % (t.user.screen_name, t.id),
                        "author": t.user.screen_name, "followers": n(t.user, "followers_count"),
                        "likes": n(t, "favorite_count"), "bookmarks": bookmarks(t), "views": views(t),
                        "posted_at": str(getattr(t, "created_at_datetime", "") or ""),
                        "on_topic": on_topic(t),
                        "text": getattr(t, "full_text", None) or getattr(t, "text", "") or "",
                    }, ensure_ascii=False) + "\n")
        print("拾った投稿を保存しました：%s" % dump)


if __name__ == "__main__":
    argv = sys.argv[1:]
    mf, hr, dp, words = MIN_FAVES, HOURS, None, []
    i = 0
    while i < len(argv):
        if argv[i] == "--min-faves" and i + 1 < len(argv):
            mf = int(argv[i + 1]); i += 2
        elif argv[i] == "--hours" and i + 1 < len(argv):
            hr = int(argv[i + 1]); i += 2
        elif argv[i] == "--dump" and i + 1 < len(argv):
            dp = argv[i + 1]; i += 2
        else:
            words.append(argv[i]); i += 1
    if not words:
        sys.exit(__doc__)
    if len(words) > MAX_WORDS:
        sys.exit("1回に試すのは%d語までにしてください（Xの回数制限に当たります）。" % MAX_WORDS)
    asyncio.run(main(words, mf, hr, dp))
