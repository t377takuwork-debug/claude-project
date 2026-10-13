"""Xで、新しいキーワードの候補を1回ずつ検索して、当たり外れを測る（語を見直すときだけ使う。毎日の収集とは別）。

説明書：  docs/sop/sop_research_auto_collect.md 「語を見直すとき」
使い方：  py -3 research/probe_x.py 語1 "語 2" "(A OR B) 恋愛"     条件は、毎日の収集と同じ（直近24時間・いいね100以上・日本語・返信を除く）
出力：    画面に採点表を出すだけ（保存しない）。1回に試すのは20語まで（回数制限に当たるため）
"""
import asyncio
import json
import random
import statistics as st
import sys
from collections import Counter
from datetime import datetime

from twikit import Client

import research_common as rc

MIN_FAVES, HOURS, MAX_WORDS = 100, 24, 20


async def main(words):
    sys.stdout.reconfigure(encoding="utf-8")
    client = Client(language="ja")
    client.set_cookies(json.loads((rc.ROOT / "x_cookies.local.json").read_text(encoding="utf-8")))
    since_ts = int(datetime.now().timestamp() - HOURS * 3600)
    per = {}
    for i, w in enumerate(words):
        q = "%s min_faves:%d lang:ja -filter:replies since_time:%d" % (w, MIN_FAVES, since_ts)
        try:
            res = await client.search_tweet(q, "Top", count=20)
            tw = [t for t in res if int(getattr(t, "favorite_count", 0) or 0) >= MIN_FAVES]
            if len(tw) >= 20:  # 1ページ目がすべて条件を満たすときだけ、次のページを取る
                await asyncio.sleep(random.uniform(3, 6))
                nxt = await res.next()
                tw += [t for t in (nxt or []) if int(getattr(t, "favorite_count", 0) or 0) >= MIN_FAVES]
            per[w] = tw
        except Exception as e:
            print("[%d/%d] %s : エラー %s" % (i + 1, len(words), w, type(e).__name__))
            if type(e).__name__ in ("Unauthorized", "Forbidden", "TooManyRequests"):
                break
            per[w] = []
        if i < len(words) - 1:
            await asyncio.sleep(random.uniform(12, 20))

    seen = Counter(t.id for tw in per.values() for t in tw)
    print("| 語 | 件数（最大40） | いいねの中央値 | 500以上 | 最大 | 投稿者数 | 他の語と重複 |")
    print("|---|---|---|---|---|---|---|")
    rows = []
    for w, tw in per.items():
        likes = sorted((int(t.favorite_count or 0) for t in tw), reverse=True)
        if not likes:
            rows.append((0, 0, "| %s | 0 | − | − | − | − | − |" % w))
            continue
        rows.append((sum(v >= 500 for v in likes), len(likes), "| %s | %d | %d | %d | %d | %d | %d |" % (
            w, len(likes), int(st.median(likes)), sum(v >= 500 for v in likes), likes[0],
            len({t.user.screen_name for t in tw}), sum(1 for t in tw if seen[t.id] > 1))))
    for _, _, line in sorted(rows, key=lambda x: (-x[0], -x[1])):
        print(line)


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    if len(args) > MAX_WORDS:
        sys.exit("1回に試すのは%d語までにしてください（Xの回数制限に当たります）。" % MAX_WORDS)
    asyncio.run(main(args))
