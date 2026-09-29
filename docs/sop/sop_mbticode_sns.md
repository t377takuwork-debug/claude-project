# SOP: MBTICODE X・Threads投稿／リプライ生成

対象AI: すべてのモデル。**手順の唯一の正は `brands/mbticode/sns_post_cheatsheet.md`（生成ワークフロー Step 1〜6）。ここに手順を重複記載しない。**

## 完了条件

- 投稿バッチ: `qa_post.py` ERROR 0件で、Threadsは一時ファイルで検品後にスプレッドシートのキューへ投入・読み戻しで一致確認済み（`publish_batch.py`）。Xは `brands/mbticode/posts/posts_x.txt` へ追記保存済み（2026-08-18以降は運用していない）
- リプライ: 投稿分析→反映メモ→本文の3ブロック出力済み

## 手順

- 投稿バッチ: `/mbticode-post` を起動する（読み込み順序はコマンド側が保証する）
- リプライ・引用RT: `/reply` を起動する。文体は `brands/mbticode/rules/feedback_mbticode_reply_style.md`（語尾・読点・問い・「わかります」の使用条件・「設計」の扱い）
- 文体（投稿本文）: `brands/mbticode/rules/style_0930.md`（暫定版）

## 必ず守るルール

- MBTI・DSKB・ラブタイプの内容は `brands/mbticode/reference/` のデータのみ使用（架空のタイプ論・自作の相性データは捏造にあたる）
- 投稿本数と時間帯の現行値は `brands/mbticode/sns_post_cheatsheet.md` の基本設定が唯一の正
- 出力の見本: Threadsは `python brands/mbticode/tools/show_queue_recent.py --full`（直近のキュー）
