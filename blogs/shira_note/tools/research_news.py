#!/usr/bin/env python3
"""
Shira Notes ネタリサーチツール（オンデマンド・過去12時間）
Usage: python tools/research_news.py

収集先:
  番組・タイアップ系: natalie.mu/music
  発売・予約系:       mdpr.jp / realsound.jp / oricon.co.jp

2026-08-07: news.ceek.jp（WebFetch経由）はタイムアウト多発・
ゲーム/アニメ記事の混入によるノイズ過多のため廃止。
本スクリプトは requests + BeautifulSoup でHTMLを直接パースし、
一覧ページに埋め込まれた分単位のタイムスタンプをそのまま使うため、
WebFetchのAI要約に頼らず正確な時間フィルタが可能。

出力はジャンル未判定の候補リスト（時間フィルタ済み・重複排除済み）。
番組・タイムテーブル記事/発売・予約記事として使えるかどうかの最終判定・
優先順位付けは /shira-research コマンド側（チャット）で行う。
"""

import os
import re
from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

JST = timezone(timedelta(hours=9))
WINDOW_HOURS = 12

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

NATALIE_URL = "https://natalie.mu/music"

RELEASE_SOURCES = [
    ("https://mdpr.jp/",                r"/news/\d+",          "https://mdpr.jp",          "モデルプレス"),
    ("https://realsound.jp/music",      r"/\d{4}/\d{2}/post-", "https://realsound.jp",     "リアルサウンド"),
    ("https://www.oricon.co.jp/music/", r"/news/\d+",          "https://www.oricon.co.jp", "ORICON NEWS"),
]


def fetch(url: str) -> BeautifulSoup | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"  [ERROR] {url} -> {e}")
        return None


# ---------------------------------------------------------------------------
# natalie.mu/music
# ---------------------------------------------------------------------------

def fetch_natalie_precise_time(url: str) -> datetime | None:
    """個別記事ページの NA_article_date から分単位の正確な日時を取得する
    （一覧側は当日以外 M月D日 のみで時刻を持たないため、深夜またぎ判定にのみ使う）
    """
    soup = fetch(url)
    if not soup:
        return None
    tag = soup.find(class_=re.compile("NA_article_date"))
    if not tag:
        return None
    m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日\s*(\d{1,2}):(\d{2})", tag.get_text(strip=True))
    if not m:
        return None
    try:
        return datetime(
            int(m.group(1)), int(m.group(2)), int(m.group(3)),
            int(m.group(4)), int(m.group(5)), tzinfo=JST,
        )
    except ValueError:
        return None


def scrape_natalie(now: datetime, threshold: datetime) -> list[dict]:
    soup = fetch(NATALIE_URL)
    if not soup:
        return []

    crosses_midnight = threshold.date() < now.date()
    yesterday = (now - timedelta(days=1)).date()

    articles: list[dict] = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=re.compile(r"/music/news/\d+")):
        href = a["href"]
        if not href.startswith("http"):
            href = "https://natalie.mu" + href
        href_key = href.split("?")[0]
        if href_key in seen:
            continue

        title_tag = a.find(class_=re.compile("NA_card_title"))
        title = title_tag.get_text(strip=True) if title_tag else ""
        if not title:
            img = a.find("img")
            title = img.get("alt", "").strip() if img else ""
        if not title or len(title) < 5:
            continue

        date_tag = a.find(class_=re.compile("NA_card_date"))
        date_text = date_tag.get_text(strip=True) if date_tag else None
        if not date_text:
            continue

        m_time = re.fullmatch(r"(\d{1,2}):(\d{2})", date_text)
        m_date = re.fullmatch(r"(\d{1,2})月(\d{1,2})日", date_text)

        pub_dt = None
        if m_time:
            # 当日記事: 一覧の時刻をそのまま使う
            pub_dt = now.replace(hour=int(m_time.group(1)), minute=int(m_time.group(2)), second=0, microsecond=0)
            if pub_dt > now:
                continue
        elif m_date:
            month, day = int(m_date.group(1)), int(m_date.group(2))
            try:
                d = datetime(now.year, month, day, tzinfo=JST).date()
            except ValueError:
                continue
            if d > now.date():
                d = datetime(now.year - 1, month, day, tzinfo=JST).date()

            if not crosses_midnight or d != yesterday:
                # 深夜またぎでない、または境界日(前日)より古い日付 → 時刻不明では
                # 基準時刻との前後判定ができないため対象外
                continue

            # 境界日(前日)ぴったりの記事のみ、個別記事ページを開いて正確な時刻を確認する
            pub_dt = fetch_natalie_precise_time(href_key)
            if pub_dt is None:
                continue
        else:
            continue

        if pub_dt < threshold or pub_dt > now:
            continue

        seen.add(href_key)
        label = pub_dt.strftime("%H:%M") if pub_dt.date() == now.date() else pub_dt.strftime("%m/%d %H:%M")
        articles.append({
            "published": label,
            "sort_key": pub_dt,
            "title": title,
            "url": href_key,
            "source": "ナタリー",
        })

    articles.sort(key=lambda a: a["sort_key"], reverse=True)
    return articles


# ---------------------------------------------------------------------------
# リリース系サイト（mdpr.jp / realsound.jp / oricon.co.jp）
# ---------------------------------------------------------------------------

def parse_release_datetime(text: str) -> datetime | None:
    m = re.search(r"(\d{4})[.\-/](\d{2})[.\-/](\d{2})\s+(\d{2}):(\d{2})", text)
    if not m:
        return None
    try:
        return datetime(
            int(m.group(1)), int(m.group(2)), int(m.group(3)),
            int(m.group(4)), int(m.group(5)), tzinfo=JST,
        )
    except ValueError:
        return None


def fetch_article_heading(url: str) -> str | None:
    """一覧のalt版タイトルしか取れなかった記事について、本体ページのh1/titleを補完取得する"""
    soup = fetch(url)
    if not soup:
        return None
    h1 = soup.find("h1")
    if h1:
        text = h1.get_text(strip=True)
        if text:
            return text
    if soup.title:
        text = soup.title.get_text(strip=True)
        text = re.sub(r"\s*[-|｜]\s*[^-|｜]+$", "", text).strip()
        if text:
            return text
    return None


def scrape_releases(now: datetime, threshold: datetime) -> list[dict]:
    articles: list[dict] = []

    for url, pattern, base, source in RELEASE_SOURCES:
        soup = fetch(url)
        if not soup:
            continue

        # 同じ記事へのリンクがページ内に複数回出現する(本文リストの見出し版・
        # サイドバーのサムネイルalt版など)ため、href単位で最良の候補を選ぶ
        candidates: dict[str, dict] = {}

        for a in soup.find_all("a", href=re.compile(pattern)):
            # タイトル: class名に title を含む要素を優先。全文取得(a.get_text)は
            # 見出し+要約+日付が連結されて壊れるため使わない
            title_tag = a.find(class_=re.compile("title", re.IGNORECASE))
            title = title_tag.get_text(strip=True) if title_tag else ""
            from_alt = False
            if not title:
                img = a.find("img")
                title = img.get("alt", "").strip() if img else ""
                from_alt = True
            if not title or len(title) < 5:
                continue

            href = a["href"]
            if href.startswith("/"):
                href = base + href
            href_key = href.split("?")[0]

            # 日時: <time datetime="..."> 属性を最優先、なければ周辺テキストを正規表現で探す
            pub_dt = None
            time_tag = a.find("time", attrs={"datetime": True})
            if time_tag:
                pub_dt = parse_release_datetime(time_tag["datetime"])
            if pub_dt is None:
                date_text = ""
                for elem in [a.parent, a.parent.parent if a.parent else None, a]:
                    if elem is None:
                        continue
                    t = elem.get_text(separator=" ", strip=True)
                    if re.search(r"\d{4}[.\-/]\d{2}[.\-/]\d{2}\s+\d{2}:\d{2}", t):
                        date_text = t
                        break
                pub_dt = parse_release_datetime(date_text)

            existing = candidates.get(href_key)
            # タイトルが長い(=省略alt版でなく本来の見出し)方、日時は判明している方を残す
            if existing is None or (not from_alt and existing["from_alt"]) or \
                    (from_alt == existing["from_alt"] and len(title) > len(existing["title"])):
                candidates[href_key] = {"title": title, "pub_dt": pub_dt, "from_alt": from_alt}
            elif existing["pub_dt"] is None and pub_dt is not None:
                existing["pub_dt"] = pub_dt

        for href_key, c in candidates.items():
            pub_dt = c["pub_dt"]
            if pub_dt is None or pub_dt < threshold or pub_dt > now:
                continue

            title = c["title"]
            if c["from_alt"]:
                # 一覧ページにalt版しかない場合、記事本体のh1/titleから正式な見出しを補う
                full_title = fetch_article_heading(href_key)
                if full_title:
                    title = full_title

            label = pub_dt.strftime("%H:%M") if pub_dt.date() == now.date() else pub_dt.strftime("%m/%d %H:%M")
            articles.append({
                "published": label,
                "sort_key": pub_dt,
                "title": title,
                "url": href_key,
                "source": source,
            })

    articles.sort(key=lambda a: a["sort_key"], reverse=True)
    return articles


# ---------------------------------------------------------------------------
# 出力
# ---------------------------------------------------------------------------

def write_output(natalie_articles, release_articles, now, threshold, output_dir) -> str:
    path = os.path.join(output_dir, "research_candidates.md")

    lines = [
        f"# Shira Notes ネタリサーチ候補（過去{WINDOW_HOURS}時間・未ジャンル判定）",
        "",
        f"調査時刻: {now.strftime('%Y-%m-%d %H:%M')} JST",
        f"対象: {threshold.strftime('%Y-%m-%d %H:%M')} 以降",
        "",
        "※ 時間フィルタ・重複排除済みの候補リスト。番組・タイムテーブル記事/",
        "  発売・予約記事として実際に使えるかどうかの絞り込みは /shira-research",
        "  コマンド側（Step 4以降）で行う。",
        "",
        f"## natalie.mu/music（{len(natalie_articles)}件）",
        "",
    ]
    if natalie_articles:
        for a in natalie_articles:
            lines.append(f"- {a['published']} ｜ {a['title']}")
            lines.append(f"  {a['url']}")
    else:
        lines.append("該当なし")

    lines += ["", f"## リリース系サイト（{len(release_articles)}件）", ""]
    if release_articles:
        for a in release_articles:
            lines.append(f"- {a['published']} ｜ {a['source']} ｜ {a['title']}")
            lines.append(f"  {a['url']}")
    else:
        lines.append("該当なし")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return path


def main() -> None:
    now = datetime.now(JST)
    threshold = now - timedelta(hours=WINDOW_HOURS)

    print(f"=== Shira Notes ネタリサーチ（過去{WINDOW_HOURS}時間） ===")
    print(f"調査時刻: {now.strftime('%Y-%m-%d %H:%M')} JST / 対象: {threshold.strftime('%Y-%m-%d %H:%M')} 以降\n")

    print("[natalie.mu/music] 取得中...")
    natalie_articles = scrape_natalie(now, threshold)
    print(f"  {len(natalie_articles)}件")

    print("[リリース系サイト] 取得中...")
    release_articles = scrape_releases(now, threshold)
    print(f"  {len(release_articles)}件")

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    path = write_output(natalie_articles, release_articles, now, threshold, output_dir)

    print(f"\n=== 完了 ===")
    print(f"-> {path}")
    print(f"natalie: {len(natalie_articles)}件 / release: {len(release_articles)}件")


if __name__ == "__main__":
    main()
