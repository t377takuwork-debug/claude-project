"""Xで、キーワード候補を1回ずつ検索して、当たり外れを測る（単発の調査用。毎日の収集とは別）。

使い方：  py -3 probe_x.py probe_words.txt           1行1語（演算子つきの検索もそのまま書ける）
保存先：  research_data/x_probe_<日付>.jsonl（収集のデータとは別。make_shortlist.py は読まない）
          research_data/x_probe_report_<日付>.md（語ごとの採点表）
1語あたり最大2ページ（約40件）。条件は collect_x.py と同じ（日本語・返信を除く・100いいね以上・14日以内）。
"""
import asyncio
import json
import random
import statistics as st
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from twikit import Client

ROOT = Path(__file__).resolve().parent
COOKIES = ROOT / "x_cookies.local.json"


async def main(words, min_faves=100, days=14, pages=2):
    sys.stdout.reconfigure(encoding="utf-8")
    client = Client(language="ja")
    client.set_cookies(json.loads(COOKIES.read_text(encoding="utf-8")))
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    per = {}
    for i, w in enumerate(words):
        q = "%s min_faves:%d lang:ja -filter:replies since:%s" % (w, min_faves, since)
        rows = []
        try:
            res = await client.search_tweet(q, "Top", count=20)
            tw = list(res)
            for _ in range(pages - 1):
                if not tw:
                    break
                await asyncio.sleep(random.uniform(3, 6))
                res = await res.next()
                if not res:
                    break
                tw += list(res)
            for t in tw:
                u = getattr(getattr(t, "user", None), "screen_name", "") or ""
                rows.append({
                    "url": "https://x.com/%s/status/%s" % (u or "i", t.id), "author": u,
                    "text": getattr(t, "full_text", None) or getattr(t, "text", "") or "",
                    "likes": int(getattr(t, "favorite_count", 0) or 0),
                    "replies": int(getattr(t, "reply_count", 0) or 0),
                    "reposts": int(getattr(t, "retweet_count", 0) or 0) + int(getattr(t, "quote_count", 0) or 0),
                    "created": getattr(t, "created_at_datetime", None).strftime("%Y/%m/%d") if getattr(t, "created_at_datetime", None) else "",
                    "probe": w,
                })
            print("[%d/%d] %s : %d件" % (i + 1, len(words), w, len(rows)), flush=True)
        except Exception as e:
            print("[%d/%d] %s : エラー %s" % (i + 1, len(words), w, type(e).__name__), flush=True)
            if type(e).__name__ in ("Unauthorized", "Forbidden", "TooManyRequests"):
                break
        per[w] = rows
        if i < len(words) - 1:
            await asyncio.sleep(random.uniform(12, 20))

    stamp = datetime.now().strftime("%Y-%m-%d")
    out = ROOT / "research_data" / ("x_probe_%s.jsonl" % stamp)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for rows in per.values():
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + chr(10))
    # 他の語との重複（同じ投稿がいくつの語に出たか）
    seen = Counter(r["url"] for rows in per.values() for r in rows)
    lines = ["# Xのキーワード候補の採点（%s・100いいね以上・14日以内・最大%d件）" % (stamp, pages * 20), "",
             "| 語 | 件数 | 中央値 | 500以上 | 1000以上 | 最大 | 投稿者数 | 他の語と重複 |", "|---|---|---|---|---|---|---|---|"]
    table = []
    for w, rows in per.items():
        if not rows:
            table.append((0, 0, w, "| %s | 0 | − | − | − | − | − | − |" % w))
            continue
        L = sorted((r["likes"] for r in rows), reverse=True)
        dup = sum(1 for r in rows if seen[r["url"]] > 1)
        table.append((sum(v >= 500 for v in L), len(L), w, "| %s | %d | %d | %d | %d | %d | %d | %d |" % (
            w, len(L), int(st.median(L)), sum(v >= 500 for v in L), sum(v >= 1000 for v in L), L[0],
            len({r["author"] for r in rows}), dup)))
    for _, _, _, line in sorted(table, key=lambda x: (-x[0], -x[1])):
        lines.append(line)
    rep = ROOT / "research_data" / ("x_probe_report_%s.md" % stamp)
    rep.write_text(chr(10).join(lines) + chr(10), encoding="utf-8")
    print("保存：%s／%s" % (out.relative_to(ROOT), rep.relative_to(ROOT)))


if __name__ == "__main__":
    words = [l.strip() for l in Path(sys.argv[1]).read_text(encoding="utf-8").split(chr(10)) if l.strip() and not l.startswith("#")]
    asyncio.run(main(words))
