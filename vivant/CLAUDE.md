# vivant 作業ルール

## アカウント概要

- **Note**: https://note.com/s4lv24（表示名「VIVANTの伏線・考察メモ」。旧s4lvアカウントを再利用。現行のs4lvはnote.com/salvami77で別物）
- **ジャンル**: ドラマ考察（TBS系日曜劇場『VIVANT（ヴィヴァント）』続編・第2シーズン）
- **記事タイプ**: 無料記事＋有料記事（マネタイズ）
- **コンテンツ方針**: 実体験ベースではなく、情報・知識をもとに記事を作成する（`rules/project_vivant_content_policy.md` 参照・2026-07-31確定）

## 作業開始時に必ず読むファイル

1. `profile.md` ← アカウント基本情報・ペルソナ・ジャンル
2. `rules/project_vivant_content_policy.md` ← 情報ベース記事のコンテンツルール（捏造禁止ルールの代替）
3. `rules/project_vivant_copyright_and_monetization.md` ← 著作権配慮ルール＋マネタイズ順序（無料記事優先・有料は反応が出てから着手）
4. `reference/` ← VIVANT各話の放送内容・視聴率・SNS反応・SEOキーワード・登場人物等の事実情報（記事執筆時に必ず参照。ここにない断定的な数字・エピソードは書かない）。ユーザーから提供される情報は都度確認せず自動でここに保存する運用（2026-07-31確定）
5. `examples_essay.md` ← 文体・構成の型（言い回し自体は流用しない。詳細は同ファイル冒頭の注意書き参照）

## ディレクトリ構成

```
vivant/
├── CLAUDE.md          ← 本ファイル
├── profile.md         ← アカウント情報・ペルソナ
├── examples_essay.md  ← 良い例・悪い例（公開記事が蓄積次第記入）
├── reference/         ← VIVANT各話の放送内容・視聴率・SNS反応・SEOキーワード・登場人物等の事実情報（新規情報は自動保存）
│   ├── vivant_s2_broadcast_facts.md      ← 話数ごとの放送事実情報（話数見出しで追記）
│   ├── vivant_characters.md              ← 登場人物一覧（スキル実行時にWebSearchで鮮度チェック・自動更新）
│   ├── vivant_ep11_kurosu_x_discourse.md ← 話数×キャラクター単位のX世論まとめ（今後同形式で増える）
│   ├── vivant_seo_keywords_kurosu.md     ← キャラクター・トピック単位のSEOキーワードクラスタ（今後同形式で増える）
│   └── vivant_ep11_theories_crossover.md ← 話数単位・複数キャラ横断の考察まとめ（今後同形式で増える）
├── rules/
│   ├── project_vivant_content_policy.md
│   └── project_vivant_copyright_and_monetization.md
└── articles/
    ├── drafts/         ← 執筆中・下書き
    ├── published/      ← 公開済み記事アーカイブ
    └── article_index.md ← 有料記事の価格・URL・公開状況を管理
```

## 記事生成スキル

| スキル | 用途 |
|---|---|
| `/vivant-theme` | テーマ評価・ペルソナ設定・タイトル決定（記事作成の最初に使う） |
| `/vivant-article` | 構成設計・本文生成・品質チェック・保存（`/vivant-theme` の出力を引き継ぐ） |

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

このディレクトリと関連スキル（`/vivant-theme`・`/vivant-article`）は他の業務（brands/・Junk314/等）から独立した構成。撤去する場合はこのディレクトリと `.claude/commands/vivant-theme.md`・`.claude/commands/vivant-article.md` を削除すれば他システムに影響しない。
