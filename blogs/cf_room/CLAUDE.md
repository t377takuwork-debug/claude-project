## SEOリライト参考ファイル

記事のリライト時は以下のファイルを参照すること。

| ファイル | 内容 |
|---|---|
| `C:\Users\PC_User\claude project\blogs\seo\SEO_guide.txt` | SEO基礎・構成設計・タイトル設計・リライトチェックリスト（全ブログ共通マスター） |

## cf_room専用ルール（2026-07-12統合）

`rules/`配下がcf_room固有ルールの唯一の正（元資料はDesktop上にあったが統合済みのため以後不要）。
**参照優先順位**：cf_room固有の判断は `rules/` を優先し、そこに記載のない全ブログ共通の一般論のみ `SEO_guide.txt` で補完する。

| ファイル | 内容 |
|---|---|
| `rules/article_pipeline.md` | 記事制作の工程順1枚地図（新規・リライト共通。**記事作業はまずここから**） |
| `rules/seo_writing_reference.md` | SEO判断基準（Google公式見解ベース＋結論ファースト等の構成思考） |
| `rules/headline_writing.md` | タイトル・見出し作成ルール（ケープルズ式4原則＋cf_room適用ルール） |
| `rules/copywriting_phrases.md` | 文章パートの構成ルール（PASONA＋フレーズカテゴリ一覧） |
| `rules/copywriting_phrase_bank.md` | フレーズ辞典（約420パターンの表現Few-Shot集。カテゴリ一覧から引く具体例の本体） |
| `rules/design_components.md` | WordPress用コードコンポーネント集（ベネフィットカード・スペックグリッド等の再利用パーツ） |
| `rules/wordpress_output_rules.md` | WordPress貼り付け用の技術ルール（ブロックコメント規則・既知の不具合と対策） |
| `rules/structured_data_prompt.md` | 構造化データ（JSON-LD）生成プロンプトと実装例 |
| `rules/internal_links.md` | 内部リンク用の全記事URL一覧（実在するURLのみ使用・リンク捏造防止） |
| `rules/image_placement.md` | 画像選定・alt・配置・WPアップロードのルール（`assets/`運用と`wp_upload.ps1`） |

**参考記事**：`drafts/deco-be22-review_revised_v2.txt`（TP-Link Deco BE22レビュー）を、デザイン・WordPress出力形式・文章の言い回しの完成形リファレンスとする。

**新規記事の作成**：`assets/<スラッグ>/`に画像を入れて `/cf-article` スキルを起動（構成→本文→画像自動配置→WPアップロード→QAまで一気通貫）。

## 完了条件（ドラフト作成・リライト共通）

ドラフトの編集後は必ず以下を実行し、**「ERROR 0件」を確認してから完了報告する**（WARNは公開前チェックリスト＝`rules/wordpress_output_rules.md` 8章として扱う）。

```powershell
powershell -ExecutionPolicy Bypass -File "tools\qa_draft.ps1" "drafts\対象ファイル.txt"
```

リライト・新規公開の完了には `rewrite_log.md`（cf_room直下）への1行追記（更新日・変更概要・効果検証予定日）まで含む。
