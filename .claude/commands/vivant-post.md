# vivant Threads 投稿バッチ生成

vivant（VIVANTの伏線・考察メモ）のThreads投稿を生成する。

型定義・頻度・ローテーション・生成手順の**唯一の正は `vivant/sns_post_cheatsheet.md`**（本ファイルには数値・手順を重複記載しない）。

---

## 必須：実行前に読み込むファイル（この順序で必ず全て読む）

1. `vivant/profile.md` — アカウント基本情報・ペルソナ
2. `vivant/sns_post_cheatsheet.md` — 型定義（連鎖考察／感情実況／読者への問い）・頻度・曜日別重みづけ・かぶり回避・Note誘導ローテーション・生成ワークフロー一式（唯一の正）
3. `vivant/examples_essay.md` — 文体・トーンの型（言い回しは流用しない。断定回避・AIっぽい定型描写NG等の共通ルール）
4. `vivant/rules/project_vivant_content_policy.md` — 情報ベース記事のコンテンツルール（出典不明の断定的数字禁止・事実描写の精度ルール・根拠の時系列確認ルール）
5. 対象エピソードの `vivant/vivant_database_ep[N].md`・`vivant/reference/` — 考察素材・放送事実・SNS反応

条件付き参照（該当する場合のみ）：
- Note誘導を組み込む回 → `vivant/articles/published/`・`vivant/articles/article_index.md`（誘導先記事の選定・直近誘導していない記事の確認）
- 直近の投稿ログとのかぶり確認 → `vivant/posts/posts_threads.txt`（未作成の場合はこのバッチが初回）

---

## 実行

上記ファイルを読み込んだ後、`sns_post_cheatsheet.md` の「生成ワークフロー」（Step 1〜6）に従って実行する。型・頻度・かぶり回避・Note誘導ローテーション・保存・キュー転送・報告まで全てチートシート側に定義済み。

**注意（2026-08-02時点）**：`brands/tools/qa_post.py`のvivant拡張（`check_vivant_post()`）は未実装。Step 3の機械検品は現時点でスキップし、LLM判断チェック（絶対禁止事項・`examples_essay.md`の文体ルール・`sns_post_cheatsheet.md`の型定義との照合）のみで運用する。拡張実装後はMBTICODE同様「ERROR 0件」を保存条件に切り替える。

## 保存先

`vivant/posts/posts_threads.txt`（MBTICODE同形式）。ディレクトリ・ファイルが存在しない場合は新規作成する。

## キュー投入

`python vivant/tools/push_threads_queue.py <csv>`（CSV列：投稿日時,本文,リプライ本文,型,FW。手順詳細は同スクリプトのdocstring参照）。
