# UYA. 作業ルール

## アカウント概要

- **Note**：https://note.com/uyadot
- **X**：https://x.com/uyadott
- **スレッズ**：https://www.threads.com/@uyadott
- **表示名**：UYA.
- **ジャンル**：働き方・生き方のエッセイ＋AI/ブログ/SNSを試した記録。パチスロは自己紹介記事＋プロフィール一言のみ
- **コンテンツ方針**：実体験ベース（`shared/personal_data.md` にない体験・数字は使わない。捏造禁止）
- **既存アカウント（s4lv・MBTICODE・vivant・junk_juice）とは完全に独立**。ルール・文体・実績データを流用しない

## 作業開始時に必ず読むファイル

1. `profile.md` ← アカウント基本情報・看板・読者像・トーンの要約
2. `rules/project_uya_positioning.md` ← 立ち位置・パチスロの扱い・収益の見せ方・s4lv差別化・トーンの決定の正（`/notekaigi` 2026-09-27）
3. `shared/personal_data.md` ← 実体験データ・数字・開示ルール（記事執筆時に必ず参照。未完成・随時更新）
4. `rules/project_uya_accounts.md` ← 3媒体のURL・現状のプロフィール文（書き直し待ち）

## ディレクトリ構成

```
uya/
├── CLAUDE.md              ← 本ファイル
├── profile.md             ← アカウント基本情報・看板・読者像・トーン
├── examples_essay.md      ← 文体・語尾・句読点・改行の余白・引用/太字の見本（`/uya-article` Step 2で必読）
├── sns_post_cheatsheet.md ← X・スレッズ投稿の運用ルール（型・頻度・s4lvとの重複回避・note誘導。`/notekaigi` 2026-09-28決定）
├── shared/
│   └── personal_data.md   ← 実体験データ・実績数字・開示ルール
├── rules/
│   ├── project_uya_positioning.md ← 立ち位置・差別化・トーンの決定（notekaigi 2026-09-27）
│   ├── project_uya_accounts.md    ← アカウントURL・現状プロフィール文（書き直し待ち）
│   ├── neta_candidates.md         ← `/uya-research`が発掘した投稿ネタ候補の一覧
│   └── uya_learnings.md           ← 投稿の学びの台帳（sns_post_cheatsheet.md未収録の断片的な好みのみ。`/uya-post`が毎回読む・2026-09-29新設）
├── tools/
│   └── qa_post_uya.py     ← 投稿の機械チェック（軽量版・2026-09-29新設）
├── posts/                 ← `/uya-post`が保存するX・スレッズ投稿本文（posts_x.txt・posts_threads.txt。2026-09-29初回生成済み）
└── articles/
    ├── drafts/            ← 執筆中・下書き
    ├── published/         ← 公開済み記事アーカイブ
    └── article_index.md   ← 記事の価格・URL・公開状況を管理
```

## 現状（2026-09-29時点）

- 立ち位置・差別化・トーンは決定済み（`rules/project_uya_positioning.md`）
- 経歴・実績の材料ファイル（`shared/personal_data.md`）は主要項目が確定済み
- 3媒体のプロフィール文は確定済み（`rules/project_uya_accounts.md`）
- 記事生成スキル`/uya-theme`・`/uya-article`を新設済み（2026-09-27）
- X・スレッズ投稿の運用ルール（型・頻度・X/スレッズの役割分担・ネタ切れ対策）を`/notekaigi`で決定済み（2026-09-28〜29。`sns_post_cheatsheet.md`）。ネタ元は`/journal`（本命）・`/uya-research`（補助）の2本立て。投稿本文の生成は`/uya-post`（軽量版。機械チェックは`tools/qa_post_uya.py`、判断が要る学びは`rules/uya_learnings.md`に蓄積。専用審査エージェントは投稿量が増えるまで後回し）
- 2026-09-29に初回投稿（朝・夜×X・スレッズ計4本）を`posts/`へ保存・投稿予約済み

## 記事生成スキル

| スキル | 用途 |
|---|---|
| `/uya-theme` | テーマ評価・有料無料判断・タイトル決定（記事作成の最初に使う） |
| `/uya-article` | 構成設計・本文生成・品質チェック・保存（`/uya-theme`の出力を引き継ぐ） |

**記事は必ず`/uya-theme`→`/uya-article`の順で作る**（他アカウントと同じ、構成案の提示と合意を飛ばさないため）。「記事を作って」とだけ言われた場合もこの順で進める。

## SNS投稿の運用

| やること | 最初に開くファイル |
|---|---|
| X・スレッズ投稿の型・頻度・役割分担等のルール確認 | `sns_post_cheatsheet.md` |
| 投稿ネタの記録（本命。日々の気づきを話して残す） | `/journal` スキルを起動（`journals/content_seeds.md`のuyaタグに蓄積） |
| 投稿ネタのリサーチ（補助。ネタ切れ対策・ユーザー指示時のみ） | `/uya-research` スキルを起動（`rules/neta_candidates.md`に蓄積） |
| X・スレッズ投稿本文の生成 | `/uya-post` スキルを起動 |

`/uya-post`は軽量版（専用審査エージェントなし）。生成後に`tools/qa_post_uya.py`で機械チェック、オーナーとのすり合わせ後に修正の意図を`rules/uya_learnings.md`へ書き戻す。投稿は`posts/posts_x.txt`・`posts/posts_threads.txt`へ追記保存。

## 記事保存ルール

- 下書きは必ず `articles/drafts/` に保存
- 公開後は `articles/published/` へ移動し `article_index.md` に登録する
- `articles/drafts/` 配下のファイルを削除する前に、必ず `articles/published/` と `article_index.md` を確認する（未追跡ファイルの削除は復元不能）

## このシステムについて

このディレクトリは他の業務（brands/・Junk314/・vivant/等）から独立した構成。撤去する場合は `uya/` ディレクトリと、将来追加する `.claude/commands/uya-*.md` を削除すれば他システムに影響しない。
