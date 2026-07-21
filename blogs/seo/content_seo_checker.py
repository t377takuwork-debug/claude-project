#!/usr/bin/env python3
"""
記事URL × ターゲットキーワードのSEO最適化度診断ツール

Usage:
  python content_seo_checker.py <URL> <キーワード1>[,キーワード2,...]

  例: python content_seo_checker.py https://example.com/article/ SEO対策,検索順位

処理:
  1. SEO_guide.txt（このファイルと同じディレクトリ）の「リライト判断チェックリスト」を読み込む
  2. 指定URLのHTMLを取得し、title / meta description / H1〜H3 / 本文文字数 / 表・リスト数を抽出
  3. キーワード（カンマ区切り。1つ目=メイン、以降=サブ）の含有状況をタイトル・メタ・見出し・本文で機械チェック
  4. チェックリストの各項目のうち自動判定できるものは判定し、判定できないもの
     （独自視点・一次情報・記事起点の設計など）は「要確認(人的判断)」として明示する
  5. Markdownレポートを output/ に保存する

設計メモ:
  SEO_guide.txt が明確に否定する「メタキーワード最適化」「文字数の魔法数字」
  「EEATスコア単体最適化」は行わない。合計点・スコアは算出せず、
  チェックリスト形式（✅/⚠️/ℹ️/要確認）で判定する。

出力: output/latest_report.md（実行のたびに上書き。履歴は残さない）
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

JST = timezone(timedelta(hours=9))
SCRIPT_DIR = Path(__file__).resolve().parent
GUIDE_PATH = SCRIPT_DIR / "SEO_guide.txt"
OUTPUT_PATH = SCRIPT_DIR / "output" / "latest_report.md"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
TIMEOUT = 15
PREFIX_WINDOW = 20  # タイトル冒頭とみなす文字数（検出用ヒューリスティック。最適化目標値ではない）

CONTENT_CLASS_HINTS = [
    "entry-content", "post-content", "article-body",
    "main-content", "article__body", "post_content",
]

session = requests.Session()
session.headers.update({"User-Agent": UA})


# ---------- SEO_guide.txt 読み込み ----------

def load_guide_checklist(guide_path: Path) -> list:
    """SEO_guide.txt の「## リライト判断チェックリスト」テーブルをパースする。"""
    if not guide_path.exists():
        return []
    text = guide_path.read_text(encoding="utf-8")
    m = re.search(r"## リライト判断チェックリスト\n(.*?)(?:\n---|\Z)", text, re.S)
    if not m:
        return []
    rows = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        if cells[0] == "フェーズ" or set(cells[0]) <= {"-"}:
            continue
        rows.append({"phase": cells[0], "point": cells[1]})
    return rows


# ---------- HTML取得・抽出 ----------

def fetch_html(url: str):
    try:
        r = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        r.raise_for_status()
    except requests.RequestException as e:
        raise SystemExit(f"URL取得に失敗しました: {e}")
    return r.text, r.url, r.status_code


def find_main_content(soup: BeautifulSoup):
    """本文とみなす要素を推定する。汎用サイト向けのヒューリスティック。"""
    article = soup.find("article")
    if article and article.get_text(strip=True):
        return article, "articleタグ"

    for hint in CONTENT_CLASS_HINTS:
        node = soup.find(class_=re.compile(hint, re.I))
        if node and node.get_text(strip=True):
            return node, f"class指定要素（{hint}相当）"

    main = soup.find("main")
    if main and main.get_text(strip=True):
        return main, "mainタグ"

    body = soup.find("body") or soup
    for tag_name in ("nav", "header", "footer", "aside", "form"):
        for t in body.find_all(tag_name):
            t.decompose()
    return body, "body全体からnav/header/footer等を除外（フォールバック・精度低めの可能性あり）"


def _find_key_in_json(data, key):
    if isinstance(data, dict):
        if data.get(key):
            return data[key]
        for v in data.values():
            found = _find_key_in_json(v, key)
            if found:
                return found
    elif isinstance(data, list):
        for item in data:
            found = _find_key_in_json(item, key)
            if found:
                return found
    return None


def find_modified_date(soup: BeautifulSoup):
    for prop in ("article:modified_time", "og:updated_time"):
        tag = soup.find("meta", attrs={"property": prop})
        if tag and tag.get("content"):
            return tag["content"].strip()

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        found = _find_key_in_json(data, "dateModified")
        if found:
            return found
    return None


def extract_seo_elements(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.get_text(strip=True) if soup.title else None

    meta_description = None
    tag = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    if tag and tag.get("content"):
        meta_description = tag["content"].strip()

    h1_list = [h.get_text(strip=True) for h in soup.find_all("h1") if h.get_text(strip=True)]
    h2_list = [h.get_text(strip=True) for h in soup.find_all("h2") if h.get_text(strip=True)]
    h3_list = [h.get_text(strip=True) for h in soup.find_all("h3") if h.get_text(strip=True)]

    modified_date = find_modified_date(soup)

    main_node, method = find_main_content(soup)
    for tag_name in ("script", "style"):
        for t in main_node.find_all(tag_name):
            t.decompose()

    body_text = main_node.get_text(separator="\n", strip=True)
    char_count = len(re.sub(r"\s+", "", body_text))
    table_count = len(main_node.find_all("table"))
    list_count = len(main_node.find_all(["ul", "ol"]))

    return {
        "title": title,
        "meta_description": meta_description,
        "h1_list": h1_list,
        "h2_list": h2_list,
        "h3_list": h3_list,
        "body_text": body_text,
        "char_count": char_count,
        "table_count": table_count,
        "list_count": list_count,
        "main_content_method": method,
        "modified_date": modified_date,
    }


# ---------- キーワードチェック ----------

def count_occurrences(text, keyword) -> int:
    if not text or not keyword:
        return 0
    return text.lower().count(keyword.lower())


def build_keyword_rows(keywords: list, ctx: dict) -> list:
    h2h3 = ctx["h2_list"] + ctx["h3_list"]
    rows = []
    for kw in keywords:
        h2h3_hit = sum(1 for h in h2h3 if kw.lower() in h.lower())
        rows.append({
            "keyword": kw,
            "title": count_occurrences(ctx["title"], kw),
            "meta": count_occurrences(ctx["meta_description"], kw),
            "h1": count_occurrences(" ".join(ctx["h1_list"]), kw),
            "h2h3_hit": h2h3_hit,
            "h2h3_total": len(h2h3),
            "body": count_occurrences(ctx["body_text"], kw),
        })
    return rows


def badge_count(n: int) -> str:
    return f"✅ 含有({n}回)" if n > 0 else "⚠️ 未含有"


def badge_h2h3(hit: int, total: int) -> str:
    if total == 0:
        return "ℹ️ 見出し(H2/H3)自体が0件"
    return f"{'✅' if hit > 0 else '⚠️'} {hit}/{total}件に含有"


# ---------- SEO_guide.txt チェックリスト対照 ----------

def _check_composition(ctx):
    if ctx["table_count"] > 0 or ctx["list_count"] > 0:
        return "✅", f"表{ctx['table_count']}件・リスト{ctx['list_count']}件を検出"
    return "⚠️", "本文中に表・リストが検出されませんでした"


def _check_title(ctx):
    kw = ctx["primary_keyword"]
    title = ctx["title"] or ""
    if not title:
        return "⚠️", "titleタグが取得できません"
    idx = title.lower().find(kw.lower())
    if idx == -1:
        return "⚠️", f"タイトルにメインキーワード「{kw}」が見つかりません"
    if idx <= PREFIX_WINDOW:
        return "✅", f"メインキーワードがタイトル先頭{PREFIX_WINDOW}文字以内（位置{idx}）"
    return "⚠️", f"メインキーワードはタイトル内にありますが冒頭から離れています（位置{idx}）"


def _check_operation(ctx):
    if ctx["modified_date"]:
        return "ℹ️", f"更新日情報を検出: {ctx['modified_date']}"
    return "ℹ️", "更新日メタ情報(dateModified/article:modified_time等)が見つかりません"


CHECKLIST_HANDLERS = {
    "構成": _check_composition,
    "タイトル": _check_title,
    "運用": _check_operation,
}


def evaluate_checklist(rows: list, ctx: dict) -> list:
    results = []
    for row in rows:
        handler = CHECKLIST_HANDLERS.get(row["phase"])
        if handler:
            verdict, detail = handler(ctx)
        else:
            verdict, detail = "要確認(人的判断)", "自動判定不可。ガイド原文の確認ポイントを目視で判断してください"
        results.append({"phase": row["phase"], "point": row["point"], "verdict": verdict, "detail": detail})
    return results


# ---------- 改善アドバイス ----------

def build_advice(ctx: dict, keyword_rows: list, checklist_results: list) -> list:
    advice = []
    primary = keyword_rows[0]

    if primary["title"] == 0:
        advice.append(f"タイトルにメインキーワード「{ctx['primary_keyword']}」が含まれていません。追加を検討してください")

    if primary["meta"] == 0:
        if ctx["meta_description"]:
            advice.append("メタディスクリプションにメインキーワードを含めると検索結果でのマッチ度が上がります")
        else:
            advice.append("メタディスクリプションが未設定です。記事の要点とキーワードを1〜2文で要約すると検索結果でのマッチ度が上がります")

    if primary["h2h3_total"] > 0 and primary["h2h3_hit"] == 0:
        advice.append("見出し(H2/H3)にメインキーワードが1件も含まれていません。関連見出しへの反映を検討してください")
    elif primary["h2h3_total"] > 0 and primary["h2h3_hit"] < primary["h2h3_total"]:
        advice.append(
            f"見出し(H2/H3)の{primary['h2h3_total']}個中{primary['h2h3_hit']}個にメインキーワードが含まれています。"
            f"他の見出しへの反映も検討してください"
        )

    if ctx["table_count"] == 0 and ctx["list_count"] == 0:
        advice.append("本文中に表・リストが検出されませんでした。3つ以上の事象を並べる箇所があれば表かリストへの変換を検討してください（SEO_guide.txt方針）")

    h1_n = len(ctx["h1_list"])
    if h1_n == 0:
        advice.append("H1タグが検出されません。記事に1つのH1を設定することを検討してください")
    elif h1_n > 1:
        advice.append(f"H1タグが{h1_n}個検出されました。1記事1H1が基本です")

    title_check = next((r for r in checklist_results if r["phase"] == "タイトル"), None)
    if title_check and title_check["verdict"].startswith("⚠️") and primary["title"] > 0:
        advice.append("タイトル内にキーワードは含まれていますが冒頭から離れています。可能なら前方への移動を検討してください")

    return advice


# ---------- レポート生成・保存 ----------

def render_report(access_url, final_url, keywords, ctx, keyword_rows, checklist_results, advice) -> str:
    now = datetime.now(JST)
    h1_n = len(ctx["h1_list"])
    lines = ["# SEO診断レポート", ""]

    lines.append(f"- URL: {access_url}" + (f"（最終到達: {final_url}）" if final_url != access_url else ""))
    kw_line = f"メイン=「{keywords[0]}」"
    if len(keywords) > 1:
        kw_line += " / サブ=" + "、".join(f"「{k}」" for k in keywords[1:])
    lines.append(f"- キーワード: {kw_line}")
    lines.append(f"- 取得日時: {now.strftime('%Y-%m-%d %H:%M:%S')} JST（本文抽出: {ctx['main_content_method']}）")
    lines.append(f"- Title: {ctx['title'] or '(取得できませんでした)'}")
    lines.append(f"- Meta Description: {ctx['meta_description'] or '(未設定)'}")
    lines.append(f"- H1({h1_n}件): {' / '.join(ctx['h1_list']) or '-'}")
    lines.append(
        f"- H2({len(ctx['h2_list'])}件)/H3({len(ctx['h3_list'])}件) ・ "
        f"本文{ctx['char_count']}字 ・ 表{ctx['table_count']} ・ リスト{ctx['list_count']}"
    )
    lines.append("")

    lines.append("## キーワード含有チェック")
    lines.append("")
    lines.append("| キーワード | タイトル | メタディスクリプション | H1 | H2/H3 | 本文 |")
    lines.append("|---|---|---|---|---|---|")
    for i, row in enumerate(keyword_rows):
        label = ("メイン:" if i == 0 else "サブ:") + row["keyword"]
        lines.append(
            f"| {label} | {badge_count(row['title'])} | {badge_count(row['meta'])} | "
            f"{badge_count(row['h1'])} | {badge_h2h3(row['h2h3_hit'], row['h2h3_total'])} | "
            f"{badge_count(row['body'])} |"
        )
    lines.append("")

    lines.append("## SEO_guide.txt 判断チェックリスト対照")
    lines.append("")
    if checklist_results:
        lines.append("| フェーズ | 確認ポイント | 判定 | 詳細 |")
        lines.append("|---|---|---|---|")
        for r in checklist_results:
            lines.append(f"| {r['phase']} | {r['point']} | {r['verdict']} | {r['detail']} |")
    else:
        lines.append(f"（{GUIDE_PATH} からチェックリストを取得できませんでした）")
    lines.append("")

    lines.append("## 改善アドバイス")
    lines.append("")
    if advice:
        for a in advice:
            lines.append(f"- {a}")
    else:
        lines.append("- 機械チェック上の明確な指摘事項はありません。「要確認」項目は目視で判断してください。")
    lines.append("")

    return "\n".join(lines)


def save_report(report_md: str) -> Path:
    """固定ファイルへ上書き保存する（履歴は残さない。直近の診断結果のみ確認できればよいため）。"""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report_md, encoding="utf-8")
    return OUTPUT_PATH


def main():
    parser = argparse.ArgumentParser(description="記事URL×ターゲットキーワードのSEO診断ツール")
    parser.add_argument("url", help="診断対象の記事URL")
    parser.add_argument("keywords", help="カンマ区切りキーワード。1つ目がメインキーワード")
    args = parser.parse_args()

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    if not keywords:
        raise SystemExit("キーワードを1つ以上指定してください")

    guide_rows = load_guide_checklist(GUIDE_PATH)
    if not guide_rows:
        print(f"[WARN] {GUIDE_PATH} からチェックリストを抽出できませんでした。判定は「要確認」のみになります。", file=sys.stderr)

    print(f"[1/3] {args.url} を取得中...")
    html, final_url, status = fetch_html(args.url)
    print(f"  status={status} final_url={final_url}")

    print("[2/3] 要素を抽出中...")
    ctx = extract_seo_elements(html)
    ctx["primary_keyword"] = keywords[0]

    print("[3/3] 判定・レポート生成中...")
    checklist_results = evaluate_checklist(guide_rows, ctx)
    keyword_rows = build_keyword_rows(keywords, ctx)
    advice = build_advice(ctx, keyword_rows, checklist_results)
    report_md = render_report(args.url, final_url, keywords, ctx, keyword_rows, checklist_results, advice)

    out_path = save_report(report_md)
    print(f"\n完了。レポート: {out_path}")


if __name__ == "__main__":
    main()
