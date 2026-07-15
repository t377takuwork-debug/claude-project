"""
shira-treat.com サイト全体のcanonicalタグ不整合・循環リダイレクト監査ツール。

手順:
1. sitemap.xml (sitemapindex) を辿り、post/page/category/miscの全URLを収集
2. robots.txtのDisallowを尊重して除外
3. 各URLにアクセスし、最終到達URL・ステータス・canonical値を記録
4. canonicalが自分自身と異なるURLについては、canonical先へも実際にアクセスして
   404/リダイレクト/循環を検証
5. CSVとMarkdownサマリーを tools/output/ に出力
"""

import csv
import random
import re
import time
import urllib.robotparser
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE = "https://shira-treat.com"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
HEADERS = {"User-Agent": UA}
TIMEOUT = 15
WAIT_MIN, WAIT_MAX = 0.5, 1.0

OUT_DIR = "tools/output"
CSV_PATH = f"{OUT_DIR}/seo_canonical_audit.csv"
MD_PATH = f"{OUT_DIR}/seo_canonical_audit_summary.md"

SITEMAP_INDEX_CANDIDATES = ["/sitemap.xml", "/sitemap_index.xml"]

session = requests.Session()
session.headers.update(HEADERS)


def wait():
    time.sleep(random.uniform(WAIT_MIN, WAIT_MAX))


def load_robots():
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(urljoin(BASE, "/robots.txt"))
    try:
        rp.read()
    except Exception:
        rp = None
    return rp


def can_fetch(rp, url):
    if rp is None:
        return True
    try:
        return rp.can_fetch(UA, url)
    except Exception:
        return True


def fetch_sitemap_locs(url):
    """<loc>を再帰的に集める（sitemapindexなら子sitemapも辿る）。"""
    r = session.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    locs = re.findall(r"<loc>(.*?)</loc>", r.text)
    is_index = "<sitemapindex" in r.text
    return locs, is_index


def collect_all_urls():
    root = None
    for cand in SITEMAP_INDEX_CANDIDATES:
        try:
            locs, is_index = fetch_sitemap_locs(urljoin(BASE, cand))
            root = (cand, locs, is_index)
            break
        except Exception:
            continue
    if root is None:
        raise RuntimeError("sitemap.xml / sitemap_index.xml の取得に失敗しました")

    cand, locs, is_index = root
    all_urls = []  # (種別, url)

    if is_index:
        for sub in locs:
            wait()
            name = sub.rstrip("/").split("/")[-1]
            try:
                sub_locs, sub_is_index = fetch_sitemap_locs(sub)
            except Exception as e:
                print(f"[WARN] サブsitemap取得失敗: {sub} ({e})")
                continue
            kind = name.replace(".xml", "")
            for u in sub_locs:
                all_urls.append((kind, u))
    else:
        for u in locs:
            all_urls.append(("sitemap", u))

    return all_urls


def extract_canonical(html, final_url):
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("link", rel="canonical")
    if tag is None or not tag.get("href"):
        return None
    return urljoin(final_url, tag["href"].strip())


def fetch_page(url):
    """1URLにアクセスして (status, final_url, redirected, canonical, error) を返す。"""
    try:
        r = session.get(url, timeout=TIMEOUT, allow_redirects=True)
    except requests.RequestException as e:
        return {"status": None, "final_url": None, "redirected": None,
                "canonical": None, "error": str(e)}
    redirected = len(r.history) > 0
    canonical = None
    ctype = r.headers.get("Content-Type", "")
    if "text/html" in ctype or ctype == "":
        canonical = extract_canonical(r.text, r.url)
    return {"status": r.status_code, "final_url": r.url,
            "redirected": redirected, "canonical": canonical, "error": None}


def classify(access_url, page, canonical_probe):
    """判定ロジック。page=access_urlへのfetch結果。canonical_probe=canonical先へのfetch結果 or None。"""
    if page["error"]:
        return "ERROR", f"アクセス失敗: {page['error']}"

    final_url = page["final_url"]
    canonical = page["canonical"]
    redirected = page["redirected"]

    if canonical is None:
        return "不整合(canonicalタグなし)", "canonicalタグが検出できない"

    norm_access = access_url.rstrip("/")
    norm_final = (final_url or "").rstrip("/")
    norm_canon = canonical.rstrip("/")

    self_match_access = norm_canon == norm_access
    self_match_final = norm_canon == norm_final

    # canonical先アクセス結果の評価
    probe_note = ""
    probe_bad = False
    if canonical_probe is not None:
        if canonical_probe["error"]:
            probe_bad = True
            probe_note = f"canonical先アクセス失敗: {canonical_probe['error']}"
        elif canonical_probe["status"] and canonical_probe["status"] >= 400:
            probe_bad = True
            probe_note = f"canonical先が{canonical_probe['status']}"
        elif canonical_probe["redirected"]:
            probe_bad = True
            probe_note = f"canonical先がさらにリダイレクト -> {canonical_probe['final_url']}"

    if self_match_access:
        return "OK", ""

    if not redirected:
        # リダイレクトなしなのにcanonicalが自分と違う = 明確な不整合
        if probe_bad:
            return "不整合(canonical循環/エラー)", probe_note
        return "不整合(canonicalが第三者URL)", f"canonical={canonical}"

    # ここから redirected=True のケース
    if self_match_final:
        # 301等でcanonicalが着地先を自己参照 = 一般的には正常パターン
        if probe_bad:
            return "不整合(canonical循環/エラー)", probe_note
        return "OK(301+自己参照canonical)", f"{access_url} -> {final_url}"

    if probe_bad:
        return "不整合(canonical循環/エラー)", probe_note
    return "不整合(canonicalが第三者URL)", f"アクセス={access_url} 着地={final_url} canonical={canonical}"


def main():
    print("[1/4] sitemap収集中...")
    rp = load_robots()
    all_urls = collect_all_urls()
    seen = set()
    targets = []
    for kind, u in all_urls:
        if u in seen:
            continue
        seen.add(u)
        if not can_fetch(rp, u):
            print(f"[SKIP:robots] {u}")
            continue
        targets.append((kind, u))
    print(f"対象URL数: {len(targets)}")

    print("[2/4] 各URLへアクセス中...")
    results = []
    for i, (kind, url) in enumerate(targets, 1):
        page = fetch_page(url)
        results.append({"kind": kind, "url": url, "page": page})
        if i % 25 == 0:
            print(f"  {i}/{len(targets)} 完了")
        wait()

    print("[3/4] canonical不一致URLについて追検証中...")
    canonical_cache = {}
    for r in results:
        page = r["page"]
        if page["error"] or not page["canonical"]:
            continue
        norm_access = r["url"].rstrip("/")
        norm_canon = page["canonical"].rstrip("/")
        norm_final = (page["final_url"] or "").rstrip("/")
        if norm_canon == norm_access:
            continue  # 自己参照は追検証不要
        if norm_canon == norm_final and not page["redirected"]:
            continue
        if page["canonical"] not in canonical_cache:
            if can_fetch(rp, page["canonical"]):
                canonical_cache[page["canonical"]] = fetch_page(page["canonical"])
                wait()
            else:
                canonical_cache[page["canonical"]] = None

    print("[4/4] 判定・出力中...")
    rows = []
    for r in results:
        kind, url, page = r["kind"], r["url"], r["page"]
        probe = canonical_cache.get(page["canonical"]) if page["canonical"] else None
        verdict, note = classify(url, page, probe)
        rows.append({
            "種別": kind,
            "アクセスURL": url,
            "ステータス": page["status"],
            "リダイレクト有無": "あり" if page["redirected"] else ("なし" if page["redirected"] is not None else "-"),
            "リダイレクト先": page["final_url"] if page["redirected"] else "",
            "canonical値": page["canonical"] or "",
            "判定": verdict,
            "備考": note,
        })

    import os
    os.makedirs(OUT_DIR, exist_ok=True)

    with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["種別", "アクセスURL", "ステータス", "リダイレクト有無",
                                                "リダイレクト先", "canonical値", "判定", "備考"])
        writer.writeheader()
        writer.writerows(rows)

    problems = [r for r in rows if r["判定"].startswith("不整合") or r["判定"] == "ERROR"]

    with open(MD_PATH, "w", encoding="utf-8") as f:
        f.write(f"# shira-treat.com canonical監査サマリー\n\n")
        f.write(f"- 監査対象URL数: {len(rows)}\n")
        f.write(f"- 不整合/エラー件数: {len(problems)}\n\n")
        f.write("## 不整合一覧\n\n")
        f.write("| 種別 | アクセスURL | リダイレクト有無 | リダイレクト先 | canonical値 | 判定 | 備考 |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for r in problems:
            f.write(f"| {r['種別']} | {r['アクセスURL']} | {r['リダイレクト有無']} | {r['リダイレクト先']} | "
                     f"{r['canonical値']} | {r['判定']} | {r['備考']} |\n")

    print(f"\n完了。")
    print(f"CSV: {CSV_PATH}")
    print(f"Markdownサマリー: {MD_PATH}")
    print(f"監査対象: {len(rows)}件 / 不整合・エラー: {len(problems)}件")


if __name__ == "__main__":
    main()
