# darepedia - Claude Code ガイド

## プロジェクト概要

話題人物特化型Wikiまとめブログ「darepedia」（https://darepedia.com/）の記事制作サポート用ワークスペース。
ドラマ・動画・ニュースなどで話題になった人物が「誰なのか」「どんな人なのか」を検索した読者に即答することを目的とする。カテゴリはcelebrity（芸能人）/sports（スポーツ選手）/expert（専門家等）/others（その他）の4種。詳細は`rules/category_persona_keyword.md`。

## 記事タイプ

darepediaは「1人物×1属性＝1記事」を基本単位とする。現時点でシステム化しているのは以下2タイプ。

| タイプ | 内容 | 構成テンプレート |
|---|---|---|
| プロフィールWiki型 | 「〇〇は何者？」に答えるストック型記事（プロフィール・彼氏/旦那・学歴・引退等） | `rules/article_structure.md` §1 |
| 時事速報・炎上考察型 | 放送・報道直後の出来事を整理する速報型記事 | `rules/article_structure.md` §2 |

「予想・考察型」（未確定情報のSNS予想を整理する記事）は現時点でスコープ外。依頼された場合はユーザーに設計方針を確認してから進める。

## コマンド一覧

| コマンド | 対象 | 手順ファイル |
|---|---|---|
| `/darepedia-article` | 新規記事の生成（構成→本文→内部リンク→QAまで一気通貫） | `.claude/commands/darepedia-article.md`（プロジェクトルート） |

## 記事制作の工程

工程順の1枚地図は `rules/article_pipeline.md`。新規記事は`/darepedia-article`で工程を自動実行できる。

## 事前情報確認・捏造禁止

- 事実情報（経歴・関係性・発言内容等）は一次資料（公式サイト・公式SNS・プレスリリース・報道）を最優先し、確認できない場合は本文執筆前にユーザーに資料提供を求める
- 実在の人物・進行中の社会問題を扱うため、断定回避表現・噂と事実の書き分け・個人攻撃助長の回避を必須とする（`rules/writing_tone_and_ethics.md`が唯一の正）
- 不明な事項は「不明」「未公表」と明記する。憶測で埋めない

## ドラフト命名規則

記事ごとに新規ファイル（上書き運用はしない）。

- ファイル名：`draft_{スラッグ}.txt`
- 保存先：`drafts/`フォルダ（`C:\Users\PC_User\claude project\blogs\darepedia\drafts\`）

## 検品ツール（ドラフト編集後は必ず実行）

```powershell
powershell -ExecutionPolicy Bypass -File "tools\qa_draft.ps1" "drafts\draft_{スラッグ}.txt"
```

チェック内容：`wp:paragraph`/`wp:heading`/`wp:html`ブロックの開閉バランス／コメント総数の一致（入れ子混入検知）／タイトル行・メタディスクリプション行の存在／h2見出し数・記事末尾が「まとめ」h2で終わっているか／h3が`{"level":3}`属性を持っているか／FAQ見出しの有無／スマートクォート混入／`wp:html`内への`wp:xxx`入れ子／ショートコード（`[nopc][title]`等）が独立ブロックに配置されているか／仮リンク`href="#"`／空alt属性／内部リンクの実在（`rules/internal_links.md`照合）／JSON-LD構文（使用時のみ）。

**完了条件：「ERROR 0件」を確認してから完了報告する。** WARNは公開前チェックリスト（`rules/wordpress_output_rules.md` §10）として扱う。

## 参照ファイル一覧

| ファイル | 内容 |
|---|---|
| `rules/article_pipeline.md` | 記事制作の工程順1枚地図（**記事作業はまずここから**） |
| `rules/category_persona_keyword.md` | カテゴリ定義・想定ペルソナ・スラッグ命名パターン・キーワード調査の進め方 |
| `rules/headline_writing.md` | タイトル・メタディスクリプション設計ルール |
| `rules/article_structure.md` | 記事タイプ別H2/H3構成テンプレート |
| `rules/design_components.md` | HTML装飾部品カタログ（summary-card・要点カード・SNS埋め込み等） |
| `rules/writing_tone_and_ethics.md` | 文体・断定回避表現・報道倫理・捏造禁止（**他の全ルールに優先**） |
| `rules/wordpress_output_rules.md` | WordPress貼り付け用の技術出力ルール（`<h2>`/`<h3>`実タグ直接出力） |
| `rules/internal_links.md` | 内部リンク用の全記事URL一覧（実在URLのみ使用・リンク捏造防止） |
| `C:\Users\PC_User\claude project\blogs\seo\SEO_guide.txt` | SEO基礎・構成設計・タイトル設計（全ブログ共通マスター） |

darepedia固有の判断は`rules/`を優先し、そこに記載のない全ブログ共通の一般論のみ`SEO_guide.txt`で補完する。

## 公開記録

記事公開後は`publish_log.md`（darepedia直下）に更新日・記事名・変更概要を1行追記する。
