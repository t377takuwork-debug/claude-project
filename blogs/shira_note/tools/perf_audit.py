#!/usr/bin/env python3
"""
PageSpeed Insights 診断ツール
Usage:
  python perf_audit.py <url1> [url2] [url3] ...
  python perf_audit.py <url> --strategy desktop
  python perf_audit.py <url> --strategy both

APIキー:
  1. 環境変数 GOOGLE_PSI_API_KEY
  2. tools/psi_auth.local.json の "apiKey"（psi_auth.local.example.json をコピーして作成。gitignore対象）

出力:
  tools/output/psi/YYYYMMDD/{strategy}_{url-slug}.json （生レスポンス。次段の解析スクリプトが読む）
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

JST = timezone(timedelta(hours=9))
TOOLS_DIR = Path(__file__).resolve().parent
AUTH_FILE = TOOLS_DIR / "psi_auth.local.json"
OUTPUT_ROOT = TOOLS_DIR / "output" / "psi"
API_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


def load_api_key() -> str:
    env_key = os.environ.get("GOOGLE_PSI_API_KEY")
    if env_key:
        return env_key
    if AUTH_FILE.exists():
        data = json.loads(AUTH_FILE.read_text(encoding="utf-8"))
        key = data.get("apiKey")
        if key:
            return key
    raise SystemExit(
        f"APIキーが見つかりません。環境変数 GOOGLE_PSI_API_KEY を設定するか、"
        f"{AUTH_FILE} を作成してください（psi_auth.local.example.json 参照）"
    )


def slugify(url: str) -> str:
    parsed = urlparse(url)
    raw = f"{parsed.netloc}{parsed.path}"
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", raw).strip("-")
    return slug or "root"


def fetch_report(url: str, strategy: str, api_key: str) -> dict:
    params = {
        "url": url,
        "key": api_key,
        "strategy": strategy,
        "category": "PERFORMANCE",
    }
    resp = requests.get(API_ENDPOINT, params=params, timeout=60)
    resp.raise_for_status()
    return resp.json()


def save_report(report: dict, url: str, strategy: str) -> Path:
    now = datetime.now(JST)
    day_dir = OUTPUT_ROOT / now.strftime("%Y%m%d")
    day_dir.mkdir(parents=True, exist_ok=True)
    base = f"{strategy}_{slugify(url)}_{now.strftime('%H%M%S')}"
    out_path = day_dir / f"{base}.json"
    suffix = 2
    while out_path.exists():
        out_path = day_dir / f"{base}-{suffix}.json"
        suffix += 1
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def summarize(report: dict) -> str:
    try:
        score = report["lighthouseResult"]["categories"]["performance"]["score"]
        return f"performance score: {round(score * 100)}"
    except KeyError:
        return "performance score: 取得失敗（レスポンス形式を確認してください）"


def main():
    parser = argparse.ArgumentParser(description="PageSpeed Insights 診断ツール")
    parser.add_argument("urls", nargs="+", help="診断対象URL（1〜複数）")
    parser.add_argument(
        "--strategy",
        choices=["mobile", "desktop", "both"],
        default="mobile",
        help="デフォルト: mobile",
    )
    args = parser.parse_args()

    api_key = load_api_key()
    strategies = ["mobile", "desktop"] if args.strategy == "both" else [args.strategy]

    for url in args.urls:
        for strategy in strategies:
            print(f"[{strategy}] {url} を取得中...")
            try:
                report = fetch_report(url, strategy, api_key)
            except requests.HTTPError as e:
                print(f"  失敗: {e}", file=sys.stderr)
                continue
            except requests.RequestException as e:
                print(f"  通信エラー: {e}", file=sys.stderr)
                continue
            out_path = save_report(report, url, strategy)
            print(f"  {summarize(report)}")
            print(f"  保存先: {out_path}")


if __name__ == "__main__":
    main()
