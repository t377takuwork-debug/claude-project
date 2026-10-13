"""調査用のスレッズアカウントに、人の手でログインして、ログイン状態を保存する（切れたときにやり直す）。

説明書：  docs/sop/sop_research_auto_collect.md 「うまく動かないとき」
使い方：  py -3 research/threads_login.py
  1. ブラウザが開く。調査用アカウントで、自分でログインする（パスワードはこのスクリプトを通らない）
  2. ログインできてホーム画面が見えたら、黒い画面に戻ってEnterを押す（「保存しました」が出るまで、ブラウザは閉じない）
  3. research/threads_state.local.json に保存される（gitには入らない・チャットに貼らない）
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

STATE = Path(__file__).resolve().parent / "threads_state.local.json"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    ctx = browser.new_context(locale="ja-JP", viewport={"width": 1100, "height": 900})
    page = ctx.new_page()
    page.goto("https://www.threads.com/login")
    input("ログインが終わってホーム画面が見えたら、ここでEnterを押してください > ")
    ctx.storage_state(path=str(STATE))
    browser.close()
print("保存しました:", STATE)
