## SEOリライト参考ファイル

記事のリライト時は以下のファイルを参照すること。

| ファイル | 内容 |
|---|---|
| `C:\Users\PC_User\claude project\blogs\seo\SEO_guide.txt` | SEO基礎・構成設計・タイトル設計・リライトチェックリスト（全ブログ共通マスター） |

## vtuber_log専用ルール（2026-07-12 cf_roomから横展開）

サイト：**VTuber Log**（https://vtuber-verse.com/ ・VTuberの前世・中の人・プロフィール・最新ニュースを扱う情報ブログ・テーマはAFFINGER）

`rules/`配下がvtuber_log固有ルールの唯一の正。cf_roomの完成形テンプレート（`blogs/cf_room/`）を複製し、ドメイン・サイト情報を差し替えたもの。
**参照優先順位**：vtuber_log固有の判断は `rules/` を優先し、そこに記載のない全ブログ共通の一般論のみ `SEO_guide.txt` で補完する。

| ファイル | 内容 |
|---|---|
| `rules/article_pipeline.md` | 記事制作の工程順1枚地図（新規・リライト共通。**記事作業はまずここから**） |
| `rules/seo_writing_reference.md` | SEO判断基準（Google公式見解ベース＋結論ファースト等の構成思考） |
| `rules/headline_writing.md` | タイトル・見出し作成ルール（ケープルズ式4原則＋適用ルール） |
| `rules/copywriting_phrases.md` | 文章パートの構成ルール（PASONA＋フレーズカテゴリ一覧） |
| `rules/copywriting_phrase_bank.md` | フレーズ辞典（約420パターンの表現Few-Shot集。カテゴリ一覧から引く具体例の本体） |
| `rules/design_components.md` | WordPress用コードコンポーネント集（再利用パーツ） |
| `rules/wordpress_output_rules.md` | WordPress貼り付け用の技術ルール（ブロックコメント規則・既知の不具合と対策） |
| `rules/structured_data_prompt.md` | 構造化データ（JSON-LD）生成プロンプト（publisher: VTuber Log／author: minase） |
| `rules/internal_links.md` | 内部リンク用の全記事URL一覧（実在するURLのみ使用・リンク捏造防止） |
| `rules/image_placement.md` | 画像選定・alt・配置・WPアップロードのルール（`assets/`運用と`wp_upload.ps1`） |

**ジャンル調整メモ**：headline_writing・copywriting_phrase_bank・design_components はcf_room（ガジェットレビュー）由来の例・型を含む。1本目の記事制作時にVTuber記事（人物プロフィール・前世・中の人系）向けへ調整する（2026-07-12ユーザー決定）。

**参考記事**：`drafts/azusa-honami-profile.txt`（本阿弥あずさ・2026-07-13登録・qa_draft ERROR 0/WARN 0）を、デザイン・WordPress出力形式・VTuber記事の文体（断定回避・プロフィール表・前世比較表・FAQ構成）の完成形リファレンスとする。※公開中の実記事とは差分あり（内部リンク2本・alt・JSON-LDはドラフト側にのみ存在。実記事へ反映するかは別途判断）。

**新規記事の作成**：`blogs/vtuber_log/assets/<スラッグ>/`に画像を入れて `/vtuber-article` スキルを起動（構成→本文→画像自動配置→WPアップロード→QAまで一気通貫）。

**WP接続**：`tools/wp_auth.local.json`（gitignore済・**中身は読まない**）。未作成の場合は各スクリプトが作成手順を案内する。疎通確認は `tools/wp_connect_test.ps1`。

## 完了条件（ドラフト作成・リライト共通）

ドラフトの編集後は必ず以下を実行し、**「ERROR 0件」を確認してから完了報告する**（WARNは公開前チェックリスト＝`rules/wordpress_output_rules.md` 8章として扱う）。

```powershell
powershell -ExecutionPolicy Bypass -File "tools\qa_draft.ps1" "drafts\対象ファイル.txt"
```

リライト・新規公開の完了には `rewrite_log.md`（vtuber_log直下）への1行追記（更新日・変更概要・効果検証予定日）まで含む。
