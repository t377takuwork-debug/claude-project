# SOP: MBTICODE X・Threads投稿／リプライ生成

対象AI: すべてのモデル。文体・タイプ論の知識は自分の学習知識を使わず、必ず下記の参照ファイルの記述だけを使うこと。

## 完了条件

- 投稿バッチ: `qa_post.py` ERROR 0件で `brands/mbticode/posts/posts_x.txt`・`posts_threads.txt` へ**追記**保存済み（7日より古い分は`posts/archive/`へローテーション）＋Threadsは投稿キューへCSV投入済み
- リプライ: 投稿分析→反映メモ→本文の3ブロック出力済み

## 手順（投稿バッチ）

1. `/mbticode-post` を起動する（`.claude/commands/mbticode-post.md`。参照ファイルの読み込み順序はコマンド側が保証する）
2. 以降の全工程（検品・保存・キュー転送・報告）は `brands/mbticode/sns_post_cheatsheet.md` の「生成ワークフロー」Step 1〜6 が唯一の正。ここに手順を重複記載しない
3. 必要に応じて `brands/mbticode/mbticode_tasks.md` で現在のタスク状況を確認する

## 手順（リプライ・引用RT）

1. `/reply` を起動する（`.claude/commands/reply.md`）
2. 文体は `brands/mbticode/rules/feedback_mbticode_reply_style.md` に従う（句読点・語尾パターン・「わかります」の使用条件・「設計」の扱い）

## 必ず守るルール

- MBTI・DSKB・ラブタイプの内容は `brands/mbticode/reference/` のデータのみ使用（架空のタイプ論・自作の相性データは捏造にあたる）
- Threads投稿はX投稿の転用ではない。文体・構成は `brands/mbticode/sns_post_cheatsheet.md`（Threads専用ルール・別角度カタログ）と `brands/mbticode/rules/project_mbticode_threads_strategy_0614.md`（X投稿と角度を変える・週1リスト型・自己リプライ即コンテンツ化）に従う
- 投稿本数の現行値: X・Threadsとも本文1日3本（各週21本・2026-07-28再判断で維持確定）。**最新値は `brands/mbticode/sns_post_cheatsheet.md` の基本設定が唯一の正**（決定経緯: `rules/project_mbticode_x_strategy_0609.md`）

## 出力見本

- X投稿: `brands/mbticode/posts/posts_x.txt`（直近の確定済みバッチ）
- Threads投稿: `brands/mbticode/posts/posts_threads.txt`（自己リプライ構造含む）
