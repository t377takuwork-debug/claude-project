# /blog-launch — 新ブログ業務環境の立ち上げ（shira_note構造の横展開）

休眠ブログ（cf_room／darepedia／vtuber_log）や新規ブログを稼働させる際に、shira_noteで実証済みの業務構造（共通ルール1本＋専用コマンド＋機械QA）を複製するセットアップ手順。

## 事前にユーザーへ確認すること（回答が揃うまで作業開始しない）

1. 対象ブログ名とURL・ジャンル・想定読者
2. 記事の型（速報型／ストック型／レビュー型など）と更新頻度
3. WordPressか他プラットフォームか（WPブロック・JSON-LDの要否が変わる）
4. アフィリエイトリンクの有無と仕様

## セットアップ手順（1セッション完結）

1. **CLAUDE.md作成**: `blogs/{対象}/CLAUDE.md` を `blogs/shira_note/CLAUDE.md` の章立て（概要→コマンド一覧→事前情報→ドラフト命名規則→検品ツール→参照ファイル）を踏襲して作成。現時点で存在しない機能の記述は書かない（空約束禁止）
2. **共通ルールファイル作成**: `blogs/{対象}/rewrite_common_rules.md`。禁止ワード・段落文体・タイトル/メタ設計を定義する。初版は `blogs/shira_note/rewrite_common_rules.md` から**そのブログにも当てはまる項目だけ**を移植し、番組固有ルールは除外する
3. **ドラフト運用の決定**: 固定ファイル名の上書き運用（`draft_{記事種別}.txt`）を踏襲するか、記事ごと新規ファイルかをユーザーと決める
4. **専用コマンド作成**: `blogs/{対象}/.claude/commands/{名前}.md`。shira_noteの番組別コマンドの構成（手順①参照ファイル→手順②更新箇所→最終ステップ=機械QA）を踏襲する
5. **機械QAの接続**: WordPressなら `blogs/shira_note/tools/qa_draft.py` の流用可否を検討（禁止ワード・ベースラインはブログ別に分離が必要）。流用しない場合も「完了条件=ERROR 0件」に相当する検品手段を必ず定義する
6. **登録**: ルート `README.md` のディレクトリ地図と `docs/business_inventory.md` に新ブログの行を追加。`blogs/{対象}/CLAUDE.md` が `.claudeignore` で除外されている場合は除外を解除する

## 完了条件

上記1〜6がすべて完了し、テスト記事1本が新コマンド経由で生成→検品を通過すること。

## 参照（構造の見本）

- 完成形の実例: `blogs/shira_note/`（CLAUDE.md・rewrite_common_rules.md・.claude/commands/・tools/）
- 新規記事立ち上げの流儀: `blogs/shira_note/rules/feedback_shira_new_article_workflow.md`（先頭H2固定・FAQ位置・aria-label等）
