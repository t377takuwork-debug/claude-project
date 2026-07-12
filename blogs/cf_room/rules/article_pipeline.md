# cf_room 記事制作パイプライン（新規・リライト共通の工程順）

どの工程で・どのファイルを参照するかの1枚地図。各ファイルの中身はここに重複記載しない（詳細は必ず参照先を開く）。

## 工程

| # | 工程 | 参照するファイル | この工程の完了条件 |
|---|---|---|---|
| 1 | テーマ・キーワード決定 | `seo_writing_reference.md`（§1評価されるコンテンツ・§5トピカルオーソリティ） | 対策キーワード1つと差別化の切り口が決まっている |
| 2 | タイトル・メタ設計 | `headline_writing.md`（4原則・型カタログ・cf_room固有ルール） | キーワード完全一致が先頭・具体的数字入り・メタとの差別化レベルが揃っている |
| 3 | 構成設計 | `seo_writing_reference.md`（§5結論ファースト）＋`copywriting_phrases.md`（PASONA） | H2一覧と各H2の役割（結論→根拠→補足の粒度）が決まっている |
| 4 | 本文執筆 | `copywriting_phrases.md`（構成）→`copywriting_phrase_bank.md`（言い回しの具体例） | 実体験・実測データのみ使用（捏造ゼロ）・Affinityは事実ベース |
| 5 | デザイン組み込み | `design_components.md`（型1〜9＋使い分けの原則） | 同じ型を3回以上繰り返していない・見出し実体が必要な箇所は`<h3>` |
| 6 | 画像選定・配置・アップロード | `image_placement.md`（選定基準・alt・manifest・`tools\wp_upload.ps1`） | manifest作成済み・メディアへアップロード済み・`src`は`uploaded_urls.json`の実URL |
| 7 | 内部リンク設置 | `internal_links.md`（実在URLのみ＋設置ルール） | 本文に関連記事リンク2〜6本・同一URL重複なし・一覧にないURLを使っていない（久々の作業なら先に `tools\update_internal_links.ps1` で鮮度確認） |
| 8 | JSON-LD生成 | `structured_data_prompt.md` | `<!-- MANUAL_JSONLD -->`付きで`wp:html`内に組み込み済み |
| 9 | WordPress形式で出力 | `wordpress_output_rules.md`（ブロック規則・禁止事項） | `drafts/`に`.txt`で保存済み・注釈コメントを含んでいない |
| 10 | 機械QA | `tools\qa_draft.ps1` | **ERROR 0件**（これを確認してから完了報告） |
| 11 | 公開前チェック | `wordpress_output_rules.md` §8 | WARN全解消（仮リンク・日付・画像実寸・メタ転記・貼り付け後の目視） |
| 12 | 更新記録 | `rewrite_log.md`（cf_room直下） | 更新日・変更概要・効果検証予定日（3〜4週間後）を1行追記済み |

## 補足

- **新規記事は `/cf-article` スキルで工程1〜12を一気通貫実行できる**（承認ポイント：画像理解・タイトル構成・アップロード実行の3箇所）。
- リライトの場合も工程1（キーワードと差別化の再確認）から順に通す。飛ばしてよいのは変更のない工程だけで、10〜12は毎回必須。
- 完成形リファレンスは `drafts/deco-be22-review_revised_v2.txt`（デザイン・出力形式・言い回しの見本）。
- cf_room固有ルールにない全ブログ共通の一般論のみ `blogs/seo/SEO_guide.txt` で補完する。
