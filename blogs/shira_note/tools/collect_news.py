#!/usr/bin/env python3
"""
Shira Notes ネタ収集ツール
Usage: python collect_news.py

収集先:
  番組情報: bangumi.org/genres/music
  リリース情報: mdpr.jp / realsound.jp / oricon.co.jp
  ※ natalie.mu は 403 のためスキップ
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import os
import re

JST = timezone(timedelta(hours=9))

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# bangumi.org で一致したら「音楽番組」として扱うキーワード
MUSIC_KEYWORDS = [
    "Mステ", "ミュージックステーション", "CDTV", "音楽の日",
    "MUSIC AWARDS", "FNS歌謡祭", "with MUSIC",
    "うたコン", "SONGS", "THE MUSIC DAY", "ベストアーティスト",
    "レコード大賞", "レコ大", "ミュージックフェア", "MUSIC BLOOD",
    "MUSIC STATION", "歌番組", "音楽番組", "ポップジャム",
    "MUSIC FAIR", "僕らの音楽", "Musicる",
]

# 単語境界が必要なキーワード（部分一致で誤マッチするもの）
MUSIC_KEYWORDS_EXACT = [
    r"(?<![A-Za-z])STAR(?![A-Za-z0-9])",   # STAR番組（STARDOM等を除外）
    r"(?<![A-Za-z])SONGS(?![A-Za-z0-9])",  # SONGS（NHK）
]

# bangumi.org で一致したら「長時間特番」として扱うキーワード
LONG_SPECIAL_KEYWORDS = [
    "24時間テレビ", "27時間テレビ", "72時間", "時間テレビ",
    "年末年始", "紅白歌合戦", "生放送スペシャル", "オールナイト",
]


# ---------------------------------------------------------------------------
# ユーティリティ
# ---------------------------------------------------------------------------

def fetch(url: str) -> BeautifulSoup | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"  [ERROR] {url} → {e}")
        return None


def parse_datetime(text: str) -> datetime | None:
    """YYYY.MM.DD HH:MM / YYYY-MM-DD HH:MM 形式をパース（JST付き）"""
    m = re.search(r"(\d{4})[.\-/](\d{2})[.\-/](\d{2})\s+(\d{2}):(\d{2})", text)
    if not m:
        return None
    try:
        return datetime(
            int(m.group(1)), int(m.group(2)), int(m.group(3)),
            int(m.group(4)), int(m.group(5)),
            tzinfo=JST,
        )
    except ValueError:
        return None


def is_fresh(dt: datetime | None) -> bool:
    """公開日時が現在から2時間以内かどうかを返す"""
    if dt is None:
        return False
    now = datetime.now(JST)
    return (now - timedelta(hours=2)) <= dt <= now


def keyword_match(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def keyword_match_exact(text: str, patterns: list[str]) -> bool:
    """正規表現パターンで単語境界を考慮したマッチング"""
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


# ---------------------------------------------------------------------------
# 番組情報: bangumi.org
# ---------------------------------------------------------------------------

def _parse_bangumi_soup(soup: BeautifulSoup, seen_urls: set, broadcast_date: str = "") -> list[dict]:
    """bangumi.org のページから番組を抽出する共通処理"""
    programs = []

    for a in soup.find_all("a", href=re.compile(r"(^/tv_events/|bangumi\.org/tv_events/)")):
        raw_href = a["href"]
        href = raw_href if raw_href.startswith("http") else "https://bangumi.org" + raw_href
        # クエリパラメータ（?overwrite_area=...）を除いた URL で重複排除
        href_key = href.split("?")[0]
        if href_key in seen_urls:
            continue
        seen_urls.add(href_key)

        raw = a.get_text(separator=" ", strip=True)

        # 日時・放送局パターンを抽出: "N月N日 X曜 H:MM 放送局名"
        m = re.search(
            r"(\d+月\d+日)\s+(\S+曜)\s+(\d+:\d+)\s+(.+?)(?:\s{2,}|$)", raw
        )
        if m:
            time_str = m.group(3)
            channel = re.split(r"\s+This text", m.group(4))[0].strip()
            title = raw[: m.start()].strip()
            if len(title) < 4:
                title = raw
            date_str = m.group(1)
        else:
            # epg ページは日付がリンクテキストに含まれないため URL パラメータから補完
            time_str = channel = ""
            date_str = broadcast_date
            title = raw

        # "音楽 " などジャンル接頭辞を除去
        title = re.sub(r"^(音楽|バラエティ|ドラマ|映画|スポーツ|アニメ)\s+", "", title).strip()

        is_music = (
            keyword_match(raw, MUSIC_KEYWORDS)
            or keyword_match_exact(raw, MUSIC_KEYWORDS_EXACT)
        )
        # 長時間特番はタイトル相当部分（先頭40文字）のみチェック
        # 説明文に「紅白歌合戦出場」等が含まれる番組への誤マッチを防ぐ
        is_special = keyword_match(raw[:40], LONG_SPECIAL_KEYWORDS)

        if not (is_music or is_special):
            continue

        programs.append({
            "title": title,
            "date": date_str,
            "time": time_str,
            "channel": channel,
            "url": href_key,
            "type": "長時間特番" if is_special else "音楽番組",
        })

    return programs


def scrape_bangumi() -> list[dict]:
    """bangumi.org の番組表（当日分・東京エリア）から音楽番組・長時間特番を取得"""
    today = datetime.now(JST).strftime("%Y%m%d")
    today_label = datetime.now(JST).strftime("%-m月%-d日") if os.name != "nt" else datetime.now(JST).strftime("%#m月%#d日")
    url = f"https://bangumi.org/epg/td?broad_cast_date={today}&ggm_group_id=42"
    print(f"    対象日: {today_label}（東京エリア）")

    soup = fetch(url)
    if not soup:
        return []

    seen_urls: set = set()
    programs = _parse_bangumi_soup(soup, seen_urls, broadcast_date=today_label)
    print(f"    取得件数: {len(programs)}件")
    return programs


# ---------------------------------------------------------------------------
# リリース情報: 各ニュースサイト
# ---------------------------------------------------------------------------

def _extract_articles(
    soup: BeautifulSoup,
    link_pattern: str,
    base_url: str,
    source: str,
) -> list[dict]:
    """共通のアーティクル抽出ロジック"""
    articles = []
    seen = set()

    for a in soup.find_all("a", href=re.compile(link_pattern)):
        # タイトル取得（img alt → テキスト の優先順位）
        img = a.find("img")
        title = (img.get("alt", "").strip() if img else "") or a.get_text(strip=True)
        if not title or len(title) < 5:
            continue

        href = a["href"]
        if href.startswith("/"):
            href = base_url + href
        if href in seen:
            continue
        seen.add(href)

        # 公開日時を親要素含めたテキストから探す
        date_text = ""
        for elem in [a.parent, a.parent.parent if a.parent else None, a]:
            if elem is None:
                continue
            t = elem.get_text(separator=" ", strip=True)
            if re.search(r"\d{4}[.\-/]\d{2}[.\-/]\d{2}\s+\d{2}:\d{2}", t):
                date_text = t
                break

        pub_dt = parse_datetime(date_text)
        if not is_fresh(pub_dt):
            continue

        articles.append({
            "title": title,
            "url": href,
            "published": pub_dt.strftime("%Y-%m-%d %H:%M") if pub_dt else "不明",
            "source": source,
        })

    return articles


def scrape_mdpr() -> list[dict]:
    soup = fetch("https://mdpr.jp/")
    if not soup:
        return []
    return _extract_articles(soup, r"/news/\d+", "https://mdpr.jp", "モデルプレス")


def scrape_realsound() -> list[dict]:
    soup = fetch("https://realsound.jp/music")
    if not soup:
        return []
    return _extract_articles(
        soup, r"/\d{4}/\d{2}/post-", "https://realsound.jp", "リアルサウンド"
    )


def scrape_oricon() -> list[dict]:
    soup = fetch("https://www.oricon.co.jp/music/")
    if not soup:
        return []
    return _extract_articles(
        soup, r"/news/\d+", "https://www.oricon.co.jp", "ORICON NEWS"
    )


# ---------------------------------------------------------------------------
# Markdown 出力
# ---------------------------------------------------------------------------

def write_programs_md(programs: list[dict], output_dir: str) -> None:
    now = datetime.now(JST).strftime("%Y年%m月%d日 %H:%M")
    path = os.path.join(output_dir, "programs.md")

    music = [p for p in programs if p["type"] == "音楽番組"]
    specials = [p for p in programs if p["type"] == "長時間特番"]

    lines = [
        "# 番組ネタ候補",
        "",
        f"収集日時: {now} (JST)",
        f"合計: {len(programs)}件（音楽番組 {len(music)}件 / 長時間特番 {len(specials)}件）",
        "",
    ]

    for section_title, items in [("音楽番組", music), ("長時間特番", specials)]:
        lines += [f"## {section_title}（{len(items)}件）", ""]
        if items:
            for p in items:
                lines.append(f"### {p['title']}")
                if p["date"]:
                    lines.append(f"- 放送日時: {p['date']} {p['time']}")
                if p["channel"]:
                    lines.append(f"- 放送局: {p['channel']}")
                lines.append(f"- URL: {p['url']}")
                lines.append("")
        else:
            lines += ["該当なし", ""]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  → {path}（{len(programs)}件）")


def write_releases_md(articles: list[dict], output_dir: str) -> None:
    now = datetime.now(JST).strftime("%Y年%m月%d日 %H:%M")
    path = os.path.join(output_dir, "releases.md")

    lines = [
        "# リリース情報ネタ候補（過去2時間以内）",
        "",
        f"収集日時: {now} (JST)",
        f"合計: {len(articles)}件",
        "",
    ]

    if not articles:
        lines += ["過去2時間以内のリリース情報はありませんでした。", ""]
    else:
        by_source: dict[str, list[dict]] = {}
        for a in articles:
            by_source.setdefault(a["source"], []).append(a)

        for source, items in by_source.items():
            lines += [f"## {source}（{len(items)}件）", ""]
            for item in items:
                lines.append(f"### {item['title']}")
                lines.append(f"- 公開日時: {item['published']}")
                lines.append(f"- URL: {item['url']}")
                lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  → {path}（{len(articles)}件）")


# ---------------------------------------------------------------------------
# エントリーポイント
# ---------------------------------------------------------------------------

def main() -> None:
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    now_str = datetime.now(JST).strftime("%Y年%m月%d日 %H:%M")
    print(f"=== Shira Notes ネタ収集 ===")
    print(f"実行日時: {now_str} JST\n")

    print("[番組情報] bangumi.org を取得中...")
    programs = scrape_bangumi()
    write_programs_md(programs, output_dir)

    print("\n[リリース情報] 各サイトを取得中...")
    releases: list[dict] = []
    for fn in [scrape_mdpr, scrape_realsound, scrape_oricon]:
        releases += fn()
    write_releases_md(releases, output_dir)

    print(f"\n=== 完了 ===")
    print(f"番組ネタ  : {len(programs)}件")
    print(f"リリースネタ: {len(releases)}件（過去2時間以内）")


if __name__ == "__main__":
    main()
