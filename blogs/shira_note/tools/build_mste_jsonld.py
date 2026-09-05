#!/usr/bin/env python3
"""
build_mste_jsonld.py  ―  Mステ タイムテーブル記事の JSON-LD ブロックを丸ごと生成する

`/mste-rewrite` 手順14 の手作業（約140行の @graph をEditで組み直し、FAQ本文と
一字一句合わせる）を置き換える。放送日・出演者・FAQ5問を入力すると、
`<!-- wp:shortcode -->` 〜 `<!-- /wp:shortcode -->` を含む完成ブロックを stdout に出す。
出力をそのまま draft_mste.txt 末尾の JSON-LD ブロックへ Edit で貼り替える。

────────────────────────────────────────────────────────────────────────
【使い方】
  python tools/build_mste_jsonld.py --sample > tools/output/mste_jsonld_input.json
      入力テンプレートを書き出す（値を埋めて使う）

  python tools/build_mste_jsonld.py tools/output/mste_jsonld_input.json
      入力JSONから完成ブロックを生成して stdout へ

  python tools/build_mste_jsonld.py input.json --no-wrapper
      [jsonld] ラッパー・wp:shortcode コメントなしで JSON 本体だけ出す

【入力JSON（--sample で雛形を出せる）】
  title              WordPressタイトル（= headline）
  meta_description   メタディスクリプション（= BlogPosting.description。120字以内）
  image_url          アイキャッチ画像URL
  image_width/height 省略時 1200 / 675
  date_modified      ISO（例 "2026-09-06T12:00:00+09:00"）。"2026-09-06" だけでも可（12:00:00補完）
  broadcast_date     "YYYY-MM-DD"
  start_time         "HH:MM"
  end_time           "HH:MM"
  special_edition    特別編成名（通常回は null）
  broadcast_description  BroadcastEvent.description の手動指定（省略時は出演者名から自動生成）
  artists            [{ "name": "...", "type": "MusicGroup"|"Person" }] を発表順（=五十音順）で。
                     type 省略時は generate_jsonld.py と同じ規則で自動判定（要確認は stderr 警告）
  lineup_order       itemListElement の並び（出演順予想）。name の配列。省略時は artists 順
  faq               [{ "q": "...", "a": "..." }] を5問。本文Q&Aと同じ文字列にすること

【検証（stderr。ERRORは終了コード1）】
  - meta_description 120字超 / faq が5件でない / lineup_order が artists の並べ替えでない
  - artist type 自動判定 → 要確認リスト
  - end_time <= start_time
────────────────────────────────────────────────────────────────────────
"""

import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── 固定値（手順14「固定箇所（変更不要）」） ────────────────────────────────
BASE = "https://shira-treat.com/music-station-timetable/"
SITE = "https://shira-treat.com/"
DATE_PUBLISHED = "2025-11-17T18:00:00+09:00"

AUTHOR = {"@type": "Person", "name": "Shira Notes", "url": "https://shira-treat.com/operator-information/"}
PUBLISHER = {
    "@type": "Organization",
    "name": "Shira Notes",
    "url": SITE,
    "sameAs": ["https://x.com/ShiraNotes_"],
    "logo": {"@type": "ImageObject", "url": "https://shira-treat.com/wp-content/uploads/2025/08/Shira-Notes-1.webp", "width": 512, "height": 512},
}
ABOUT = [
    {"@type": "Thing", "name": "ミュージックステーション", "sameAs": "https://www.tv-asahi.co.jp/music/"},
    {"@type": "Thing", "name": "Mステ タイムテーブル"},
]
TVA_PLACE = {"@type": "Place", "name": "テレビ朝日", "sameAs": "https://www.tv-asahi.co.jp/"}
TVA_ORG = {"@type": "Organization", "name": "テレビ朝日", "sameAs": "https://www.tv-asahi.co.jp/"}
BREADCRUMB = {
    "@type": "BreadcrumbList",
    "@id": BASE + "#breadcrumb",
    "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "ホーム", "item": SITE},
        {"@type": "ListItem", "position": 2, "name": "ミュージックステーション", "item": "https://shira-treat.com/category/musictv/music-station-2/"},
        {"@type": "ListItem", "position": 3, "name": "Mステ タイムテーブル", "item": BASE},
    ],
}

# ── アーティスト型の自動判定（generate_jsonld.py と同一ルール） ──────────────
GROUP_KEYWORDS = ["&", "×", "グループ", "group", "バンド", "ボーイズ", "ガールズ", "BOYS", "GIRLS"]
SOLO_PATTERN = re.compile(r"^[぀-ゟ゠-ヿ一-鿿]{2,6}$")


def classify(name):
    for kw in GROUP_KEYWORDS:
        if kw.lower() in name.lower():
            return "MusicGroup", False
    if SOLO_PATTERN.match(name):
        return "Person", False
    return "MusicGroup", True  # 判定不能 → MusicGroup 扱い・要確認


def err(msg):
    print(f"[ERROR] {msg}", file=sys.stderr)


def warn(msg):
    print(f"[WARN]  {msg}", file=sys.stderr)


def jp_date(y, m, d):
    return f"{y}年{m}月{d}日"


def normalize_dt(s, label):
    s = s.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return s + "T12:00:00+09:00"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+09:00", s):
        return s
    err(f"{label} は 'YYYY-MM-DD' か 'YYYY-MM-DDTHH:MM:SS+09:00' で指定してください: {s!r}")
    raise SystemExit(1)


def build_artists(raw_list):
    out, uncertain = [], []
    for a in raw_list:
        name = a["name"].strip()
        t = (a.get("type") or "").strip()
        if t not in ("MusicGroup", "Person"):
            t, is_unc = classify(name)
            if is_unc:
                uncertain.append(name)
        out.append({"name": name, "type": t})
    return out, uncertain


def main():
    args = [a for a in sys.argv[1:]]
    if "--sample" in args:
        print(json.dumps(SAMPLE, ensure_ascii=False, indent=2))
        return

    no_wrapper = "--no-wrapper" in args
    paths = [a for a in args if not a.startswith("--")]
    if not paths:
        err("入力JSONのパスを指定してください（雛形は --sample）")
        raise SystemExit(1)

    src = sys.stdin.read() if paths[0] == "-" else open(paths[0], encoding="utf-8").read()
    cfg = json.loads(src)

    # ── 取り出し・検証 ──────────────────────────────────────────────────
    title = cfg["title"].strip()
    meta = cfg["meta_description"].strip()
    if len(meta) > 120:
        warn(f"meta_description が {len(meta)}字（120字以内推奨）")

    bdate = cfg["broadcast_date"].strip()
    mo = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", bdate)
    if not mo:
        err(f"broadcast_date は YYYY-MM-DD: {bdate!r}")
        raise SystemExit(1)
    y, m, d = int(mo[1]), int(mo[2]), int(mo[3])
    jd = jp_date(y, m, d)

    st, et = cfg["start_time"].strip(), cfg["end_time"].strip()
    for v in (st, et):
        if not re.fullmatch(r"\d{2}:\d{2}", v):
            err(f"start_time / end_time は HH:MM: {v!r}")
            raise SystemExit(1)
    if et <= st:
        warn(f"end_time({et}) が start_time({st}) 以下です")

    date_modified = normalize_dt(cfg["date_modified"], "date_modified")
    date_published = cfg.get("date_published", DATE_PUBLISHED)
    img = cfg["image_url"].strip()
    iw = int(cfg.get("image_width", 1200))
    ih = int(cfg.get("image_height", 675))
    special = (cfg.get("special_edition") or "").strip()

    artists, uncertain = build_artists(cfg["artists"])
    names = [a["name"] for a in artists]
    if uncertain:
        warn("型を自動判定（MusicGroup）― 要確認: " + " / ".join(uncertain))

    lineup_names = cfg.get("lineup_order") or names
    if sorted(lineup_names) != sorted(names):
        err("lineup_order が artists の並べ替えになっていません\n"
            f"  artists : {names}\n  lineup  : {lineup_names}")
        raise SystemExit(1)
    by_name = {a["name"]: a for a in artists}
    lineup = [by_name[n] for n in lineup_names]

    faq = cfg["faq"]
    if len(faq) != 5:
        warn(f"faq が {len(faq)}件（本文と同じく5件が標準）")

    # ── @graph 組み立て ────────────────────────────────────────────────
    ev_name = f"ミュージックステーション（{jd}放送{('「' + special + '」') if special else ''}）"
    ev_desc = cfg.get("broadcast_description") or (
        f"{jd}放送のミュージックステーション。{'、'.join(names)}が出演する回。"
    )

    blogposting = {
        "@type": "BlogPosting",
        "@id": BASE + "#post",
        "mainEntityOfPage": {"@type": "WebPage", "@id": BASE},
        "headline": title,
        "description": meta,
        "image": {"@type": "ImageObject", "@id": BASE + "#primaryimage", "url": img, "width": iw, "height": ih},
        "thumbnailUrl": img,
        "datePublished": date_published,
        "dateModified": date_modified,
        "author": AUTHOR,
        "publisher": PUBLISHER,
        "articleSection": "音楽番組",
        "keywords": [
            "Mステ タイムテーブル", "ミュージックステーション タイムテーブル",
            "Mステ 出演順", "Mステ 曲順", f"Mステ {y}", f"Mステ {m}月{d}日",
        ],
        "inLanguage": "ja",
        "about": ABOUT,
        "mentions": [{"@type": a["type"], "name": a["name"]} for a in artists],
    }
    broadcast = {
        "@type": "BroadcastEvent",
        "@id": BASE + "#event",
        "name": ev_name,
        "startDate": f"{bdate}T{st}:00+09:00",
        "endDate": f"{bdate}T{et}:00+09:00",
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/MixedEventAttendanceMode",
        "isLiveBroadcast": True,
        "description": ev_desc,
        "image": img,
        "location": TVA_PLACE,
        "organizer": TVA_ORG,
        "performer": [{"@type": a["type"], "name": a["name"]} for a in artists],
    }
    itemlist = {
        "@type": "ItemList",
        "@id": BASE + "#lineup",
        "name": f"{jd} Mステ出演者一覧",
        "numberOfItems": len(artists),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "item": {"@type": a["type"], "name": a["name"]}}
            for i, a in enumerate(lineup)
        ],
    }
    faqpage = {
        "@type": "FAQPage",
        "@id": BASE + "#faq",
        "mainEntity": [
            {"@type": "Question", "name": q["q"].strip(),
             "acceptedAnswer": {"@type": "Answer", "text": q["a"].strip()}}
            for q in faq
        ],
    }

    graph = {"@context": "https://schema.org", "@graph": [blogposting, broadcast, itemlist, faqpage, BREADCRUMB]}
    body = json.dumps(graph, ensure_ascii=False, indent=2)

    if no_wrapper:
        print(body)
    else:
        print("<!-- wp:shortcode -->")
        print("<!-- MANUAL_JSONLD -->")
        print("[jsonld]")
        print(body)
        print("[/jsonld]")
        print("<!-- /wp:shortcode -->")

    print("", file=sys.stderr)
    print(f"[OK] 出演者 {len(artists)}組 / FAQ {len(faq)}問 / 放送 {jd} {st}〜{et}"
          + (f" / 特別編成「{special}」" if special else ""), file=sys.stderr)


SAMPLE = {
    "title": "Mステ タイムテーブル【M月DD日】出演順・出演時間をリアルタイム更新",
    "meta_description": "Mステ（M月DD日）タイムテーブルを速報更新！{注目1}・{注目2}。出演順・登場時間の目安を随時追記。",
    "image_url": "https://shira-treat.com/wp-content/uploads/2026/08/image-9.webp",
    "image_width": 1200,
    "image_height": 675,
    "date_modified": "2026-09-06",
    "broadcast_date": "2026-09-18",
    "start_time": "21:00",
    "end_time": "21:54",
    "special_edition": None,
    "broadcast_description": None,
    "artists": [
        {"name": "あいみょん", "type": "Person"},
        {"name": "上白石萌音", "type": "Person"},
        {"name": "THE SPELLBOUND×BOOM BOOM SATELLITES", "type": "MusicGroup"},
        {"name": "中島健人", "type": "Person"},
        {"name": "M!LK", "type": "MusicGroup"},
        {"name": "渡辺美里", "type": "Person"},
    ],
    "lineup_order": [
        "THE SPELLBOUND×BOOM BOOM SATELLITES", "M!LK", "中島健人",
        "上白石萌音", "渡辺美里", "あいみょん",
    ],
    "faq": [
        {"q": "9/18の詳細なタイムテーブルは事前にわかりますか？", "a": "..."},
        {"q": "あいみょんさんの出番は何時頃ですか？", "a": "..."},
        {"q": "M!LKの出番は何時頃ですか？", "a": "..."},
        {"q": "録画を忘れました。見逃し配信はありますか？", "a": "..."},
        {"q": "Mステとは何の略ですか？", "a": "Mステは『ミュージックステーション』の略称です。テレビ朝日系列で毎週金曜よる8時から生放送されている音楽番組で、1986年の放送開始から続く長寿番組として知られています。"},
    ],
}


if __name__ == "__main__":
    main()
