#!/usr/bin/env python3
"""
generate_af_link.py  アフィリエイトリンク自動変換ツール（CD/DVDリリース記事用）

【使い方】
  python tools/generate_af_link.py rakuten   "{商品ページURL}" "{リンクテキスト}"
  python tools/generate_af_link.py sevennet  "{商品ページURL}" "{リンクテキスト}"
  python tools/generate_af_link.py amazon    "{ASIN または amazon.co.jp商品URL または amzn.to短縮URL}" "{リンクテキスト}"

【対応ASPと変換可否】
  rakuten   : もしもアフィリエイト。商品ページのプレーンURLから完全自動生成できる
              （a_id/p_id/pc_id/pl_id はアカウント固有・使い回し可、2026-06-27確定仕様）
  sevennet  : バリューコマース。商品ページのプレーンURLから完全自動生成できる
              （sid/pid はアカウント固有・使い回し可、2026-08-07確定仕様）
  amazon    : ASIN（10桁）またはamazon.co.jpの商品URLを渡すと、Amazon公式のシンプルテキスト
              リンク形式 `https://www.amazon.co.jp/dp/{ASIN}/ref=nosim?tag={アソシエイトID}` で
              完全自動生成できる（ASIN_TAG＝ShiraNote専用アソシエイトID、2026-09-18確定）。
              amzn.to短縮URLを渡した場合は従来どおりrel属性の付与のみ行う（linkId等の個別
              トラッキングパラメータを保持したい場合はamzn.toを使う。通常はASIN直渡しでよい）。
              **ASIN_TAGはShiraNoteブログ専用。他ブログ・他アカウントでは流用不可**

【出力形式についての方針】
  各ASPが実際に生成するコードスタイルをそのまま踏襲する（target="_blank"は付与しない。
  WordPress側で外部リンクに自動付与される前提のため）。TV番組タイムテーブル記事側の
  rewrite_common_rules.md 7章（target="_blank"を手動付与する旧仕様）とは別方針。
"""

import sys
import io
import re
import argparse
from urllib.parse import quote

# Windows cp932 環境でも UTF-8 で出力する
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── 楽天ブックス（もしもアフィリエイト）2026-06-27確定 ──────────────────────
RAKUTEN_A_ID = "4824566"
RAKUTEN_P_ID = "54"
RAKUTEN_PC_ID = "54"
RAKUTEN_PL_ID = "616"

# ── セブンネット（バリューコマース）2026-08-07確定 ──────────────────────
SEVENNET_SID = "3773727"
SEVENNET_PID = "892674443"

# ── Amazonアソシエイト（ShiraNote専用・2026-09-18確定） ──────────────────
# 他ブログ・他アカウントでは流用不可
AMAZON_ASSOCIATE_TAG = "shira1-22"

ASIN_RE = re.compile(r"^[A-Z0-9]{10}$")
ASIN_IN_URL_RE = re.compile(r"/dp/([A-Z0-9]{10})")


def build_rakuten(product_url: str, text: str) -> str:
    encoded = quote(product_url, safe="")
    anchor = (
        f'<a href="//af.moshimo.com/af/c/click?a_id={RAKUTEN_A_ID}&p_id={RAKUTEN_P_ID}'
        f'&pc_id={RAKUTEN_PC_ID}&pl_id={RAKUTEN_PL_ID}&url={encoded}" '
        f'rel="nofollow" referrerpolicy="no-referrer-when-downgrade" attributionsrc>{text}</a>'
    )
    pixel = (
        f'<img src="//i.moshimo.com/af/i/impression?a_id={RAKUTEN_A_ID}&p_id={RAKUTEN_P_ID}'
        f'&pc_id={RAKUTEN_PC_ID}&pl_id={RAKUTEN_PL_ID}" width="1" height="1" '
        f'style="border:none;" alt="" loading="lazy">'
    )
    return anchor + pixel


def build_sevennet(product_url: str, text: str) -> str:
    encoded = quote(product_url, safe="")
    pixel = (
        f'<img src="//ad.jp.ap.valuecommerce.com/servlet/gifbanner?sid={SEVENNET_SID}'
        f'&pid={SEVENNET_PID}" height="1" width="0" border="0">'
    )
    return (
        f'<a href="//ck.jp.ap.valuecommerce.com/servlet/referral?sid={SEVENNET_SID}'
        f'&pid={SEVENNET_PID}&vc_url={encoded}" rel="nofollow">{pixel}{text}</a>'
    )


def build_amazon(value: str, text: str) -> str:
    # amzn.to短縮URL: 個別トラッキングパラメータ（linkId等）を保持したい場合に使う。
    # rel属性の付与のみ行い、リンク自体はユーザーがSiteStripe等で発行済みのものを使う。
    if "amzn.to" in value:
        return f'<a href="{value}" rel="nofollow sponsored noopener noreferrer">{text}</a>'

    # ASINの直接指定、またはamazon.co.jp商品URLからASINを抽出
    value = value.strip()
    if ASIN_RE.match(value):
        asin = value
    else:
        m = ASIN_IN_URL_RE.search(value)
        if not m:
            print(
                "[警告] ASIN（10桁）・amazon.co.jp商品URL・amzn.to短縮URLのいずれの形式でもありません。"
                "ASINは商品詳細ページの「商品の情報」欄で確認できます。",
                file=sys.stderr,
            )
            return f'<a href="{value}" rel="nofollow sponsored noopener noreferrer">{text}</a>'
        asin = m.group(1)

    href = f"https://www.amazon.co.jp/dp/{asin}/ref=nosim?tag={AMAZON_ASSOCIATE_TAG}"
    return f'<a href="{href}" rel="nofollow sponsored noopener noreferrer">{text}</a>'


BUILDERS = {
    "rakuten": build_rakuten,
    "sevennet": build_sevennet,
    "amazon": build_amazon,
}


def main():
    parser = argparse.ArgumentParser(description="CD/DVDリリース記事用アフィリエイトリンク生成")
    parser.add_argument("platform", choices=BUILDERS.keys(), help="rakuten / sevennet / amazon")
    parser.add_argument("url", help="商品ページURL（amazonの場合はASIN／商品URL／amzn.to短縮URL）")
    parser.add_argument("text", help="リンクテキスト（例: 楽天ブックスで予約する）")
    args = parser.parse_args()

    tag = BUILDERS[args.platform](args.url, args.text)
    print(tag)


if __name__ == "__main__":
    main()
