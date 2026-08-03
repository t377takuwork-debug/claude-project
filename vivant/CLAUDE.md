# vivant 作業ルール

## アカウント概要

- **Note**: https://note.com/s4lv24（表示名「VIVANTの伏線・考察メモ」。旧s4lvアカウントを再利用。現行のs4lvはnote.com/salvami77で別物）
- **ジャンル**: ドラマ考察（TBS系日曜劇場『VIVANT（ヴィヴァント）』続編・第2シーズン）
- **記事タイプ**: 無料記事＋有料記事（マネタイズ）
- **コンテンツ方針**: 実体験ベースではなく、情報・知識をもとに記事を作成する（`rules/project_vivant_content_policy.md` 参照・2026-07-31確定）
- **Threads**: MBTICODE方式（Apps Script+スプレッドシート+Threads API）を横展開・接続基盤稼働済み（2026-08-02）。投稿設計は`sns_post_cheatsheet.md`参照

## 作業開始時に必ず読むファイル

1. `profile.md` ← アカウント基本情報・ペルソナ・ジャンル
2. `rules/project_vivant_content_policy.md` ← 情報ベース記事のコンテンツルール（捏造禁止ルールの代替）
3. `rules/project_vivant_copyright_and_monetization.md` ← 著作権配慮ルール＋マネタイズ順序（無料記事優先・有料は反応が出てから着手）
4. `reference/` ← VIVANT各話の放送内容・視聴率・SNS反応・SEOキーワード・登場人物等の事実情報（記事執筆時に必ず参照。ここにない断定的な数字・エピソードは書かない）。ユーザーから提供される情報は都度確認せず自動でここに保存する運用（2026-07-31確定）
5. `examples_essay.md` ← 文体・構成の型（言い回し自体は流用しない。詳細は同ファイル冒頭の注意書き参照）
6. （Threads投稿作業のみ）`sns_post_cheatsheet.md` ← 型定義・頻度・ローテーション・生成ワークフローの唯一の正

## ディレクトリ構成

```
vivant/
├── CLAUDE.md          ← 本ファイル
├── profile.md         ← アカウント情報・ペルソナ
├── examples_essay.md  ← 良い例・悪い例（公開記事が蓄積次第記入）
├── sns_post_cheatsheet.md ← Threads投稿の型定義・頻度・ローテーション・生成ワークフロー（唯一の正）
├── reference/         ← VIVANT各話の放送内容・視聴率・SNS反応・SEOキーワード・登場人物等の事実情報（新規情報は自動保存）
│   ├── vivant_s2_broadcast_facts.md      ← 話数ごとの放送事実情報（話数見出しで追記）
│   ├── vivant_characters.md              ← 登場人物一覧（スキル実行時にWebSearchで鮮度チェック・自動更新）
│   ├── vivant_ep11_kurosu_x_discourse.md ← 話数×キャラクター単位のX世論まとめ（今後同形式で増える）
│   ├── vivant_seo_keywords_kurosu.md     ← キャラクター・トピック単位のSEOキーワードクラスタ（今後同形式で増える）
│   └── vivant_ep11_theories_crossover.md ← 話数単位・複数キャラ横断の考察まとめ（今後同形式で増える）
├── rules/
│   ├── project_vivant_content_policy.md
│   ├── project_vivant_copyright_and_monetization.md
│   └── project_vivant_threads_strategy_0802.md ← Threads運用方針の決定経緯（notekaigi会議録）
├── tools/
│   ├── qa_vivant_database.py ← 考察データベースの機械QA（`/vivant-episode-update` Step 3で使用）
│   ├── threads_setup_guide.md ← Threads API接続・スプレッドシート初期セットアップ手順
│   ├── threads_scheduler.gs ← Apps Script（定時投稿・インサイト収集・日次観測ログ。MBTICODE方式のPhase1-4部分のみ移植）
│   ├── threads_connect_test.ps1 / push_threads_queue.py / fetch_insights.py / fetch_past_posts.py / check_analysis_due.py / check_queue_coverage.py / update_threads_queue_body.py / withdraw_posted_row.py ← MBTICODE同形式のThreads運用ツール一式（push/update系は2026-08-04に自動並び替え・型同期・投稿済み行の安全な取り下げ機能を追加）
│   ├── sheets_config.json ← スプレッドシートID・タブ名設定
│   ├── threads_auth.local.json / sheets_service_account.local.json ← 認証情報（gitignore対象）
├── vivant_database_ep[N].md  ← 話数ごとの考察データベース（旧版は削除せず並存させる。末尾の「5. データベース運用マニュアル」が更新時の絶対ルール）
├── raw_data_ep[N].md         ← 話数ごとのWeb調査生データ（`/vivant-episode-update` Step 1で生成・削除しない）
└── articles/
    ├── drafts/         ← 執筆中・下書き
    ├── published/      ← 公開済み記事アーカイブ
    └── article_index.md ← 有料記事の価格・URL・公開状況を管理
```

## 記事生成スキル

| スキル | 用途 |
|---|---|
| `/vivant-episode-update [話数]` | 新話放送後、Webリサーチ→考察データベース差分更新→機械QAまでをワンストップで実行（記事制作の前段。**最初に実行**） |
| `/vivant-theme` | テーマ評価・ペルソナ設定・タイトル決定（記事作成の最初に使う） |
| `/vivant-article` | 構成設計・本文生成・品質チェック・保存（`/vivant-theme` の出力を引き継ぐ） |

## Threads投稿スキル

| スキル | 用途 |
|---|---|
| `/vivant-post` | Threads投稿バッチ生成。型定義・頻度・ローテーションの唯一の正は`sns_post_cheatsheet.md`（2026-08-02新設） |

## 考察データベースの運用

- 新話放送後は必ず `/vivant-episode-update [話数]` を使う（Web調査からデータベース更新までを1コマンドで完結。手動でraw_dataを作ってからデータベースを編集する運用はしない）
- 更新ルールの正は `vivant_database_ep[N].md` 末尾の「5. データベース運用マニュアル」（事実／推測の分離・ステータス管理・履歴保持・用語統一を規定）。本ファイルとマニュアルが矛盾する場合はマニュアル側を優先する
- データベースファイル（`vivant_database_ep[N].md`）・生データファイル（`raw_data_ep[N].md`）はいずれも旧版を削除せず、話数ごとに並存させる（履歴保持ルール）

## 記事生成ルール

- 必ずスキルを経由して生成する（`/vivant-theme` → `/vivant-article` の順）
- 実体験ベースではなく情報ベースで作成する（`rules/project_vivant_content_policy.md` 準拠）
- ジャンル・文体・ペルソナが未確定の間は、テーマ入力時にユーザーへ都度確認する
- **無料＝考察・整理が当面のメイン。有料＝着手時期未定**（`rules/project_vivant_copyright_and_monetization.md` 準拠）。有料記事は、公開済み無料記事への反応（「続きが知りたい」等）が出たテーマが見つかってからユーザーと相談の上で着手する

## 記事保存ルール

- 下書きは必ず `articles/drafts/` に保存
- 公開後は `articles/published/` へ移動し `article_index.md` に登録する（手順は `/vivant-article` Step 5参照）
- **`articles/drafts/` 配下のファイルを削除する前に必ず `articles/published/` と `article_index.md` を確認する**（未追跡ファイルの削除は復元不能。ルート `brands/CLAUDE.md` と同一ルール）

## このシステムについて

このディレクトリと関連スキル（`/vivant-episode-update`・`/vivant-theme`・`/vivant-article`）は他の業務（brands/・Junk314/等）から独立した構成。撤去する場合はこのディレクトリと `.claude/commands/vivant-episode-update.md`・`.claude/commands/vivant-theme.md`・`.claude/commands/vivant-article.md` を削除すれば他システムに影響しない。
