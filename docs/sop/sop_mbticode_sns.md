# SOP: MBTICODE X・Threads投稿／リプライ生成

対象AI: すべてのモデル。文体・タイプ論の知識は自分の学習知識を使わず、必ず下記の参照ファイルの記述だけを使うこと。

## 完了条件

- 投稿バッチ: `brands/mbticode/posts/posts_x.txt`・`posts_threads.txt` へ上書き保存済み＋`/post-review` チェック済み
- リプライ: 投稿分析→反映メモ→本文の3ブロック出力済み

## 手順（投稿バッチ）

1. 見本バンク `brands/mbticode/examples_sns.md`（Good/Bad対比）を読む
2. `/mbticode-post` を起動する（`.claude/commands/mbticode-post.md`。参照ファイルの読み込み順序はコマンド側が保証する）
3. `brands/mbticode/mbticode_tasks.md` で現在のタスク状況を確認する
4. 機械検品: `python brands/tools/qa_post.py brands/mbticode/posts/posts_x.txt`（threads側も同様）→ **ERROR 0件必須**
5. `/post-review` で壁打ちしてから確定する（生成→即確定は禁止）
6. `/quality-guardrail` の同日重複チェックを通す

## 手順（リプライ・引用RT）

1. `/reply` を起動する（`.claude/commands/reply.md`）
2. 文体は `brands/mbticode/rules/feedback_mbticode_reply_style.md` に従う（句読点・語尾パターン・「わかります」の使用条件・「設計」の扱い）

## 必ず守るルール

- MBTI・DSKB・ラブタイプの内容は `brands/mbticode/reference/` のデータのみ使用（架空のタイプ論・自作の相性データは捏造にあたる）
- Threads投稿はX投稿の転用ではない。文体・構成は `/mbticode-post` コマンド内の指示と `brands/mbticode/rules/project_mbticode_threads_strategy_0614.md`（X投稿と角度を変える・週1リスト型・自己リプライ即コンテンツ化）に従う
- 投稿本数の現行値: X・Threadsとも本文1日3本（各週21本）。**最新値は `brands/mbticode/sns_post_cheatsheet.md` の基本設定が唯一の正**（決定経緯: `rules/project_mbticode_x_strategy_0609.md`、再判断日2026-07-19。ユーザー確認済み 2026-07-06）

## 出力見本

- X投稿: `brands/mbticode/posts/posts_x.txt`（直近の確定済みバッチ）
- Threads投稿: `brands/mbticode/posts/posts_threads.txt`（自己リプライ構造含む）
