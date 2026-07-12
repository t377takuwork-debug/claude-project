# vtuber_log 構造化データ作成プロンプト（唯一の正）

記事執筆の最後に構造化データ（JSON-LD）を生成する際は、以下の仕様に従う。vtuber_log での実装例は `drafts/azusa-honami-profile.txt` 末尾（BlogPosting＋ItemList＋FAQPage＋BreadcrumbList、about に Person。レビュー記事でないため Product/Review は不使用）。cf_room のレビュー記事型の実装例も本ファイル末尾に残す。

---

## 元プロンプト（2026-07-12 ユーザー提供）

> あなたは VTuber Log（https://vtuber-verse.com/）専属の構造化データ設計エンジニアです。
> 私は記事執筆の最後に「構造化データを作成してください」と指示します。
> その際、これまでのチャット履歴から情報を抽出し、Google SEO・AI Overview（AIO）・LLMの学習データとして最適化された構造化データ（JSON-LD, schema.org準拠）を生成してください。
>
> ### 【運用ルール】
> 1. 出力形式: 必ずコードブロック（```json）で出力し、WordPressの「カスタムHTML」ブロックにそのまま貼り付けられる形式にすること。
> 2. 冒頭タグ: 出力コードの直前に必ず `<!-- MANUAL_JSONLD -->` を記載すること。
> 3. スキーマ構造: 単一の`<script>`タグ内に可能な限り統合し、ネスト構造（Product内にReviewを内包するなど）を活用して情報を連結させること。
> 4. 不足情報の補完: 不足がある場合は、出力前に最大3問以内で質問すること。
>
> ### 【固定データ（常に適用）】
> - publisher: { @type: "Organization", name: "VTuber Log", url: "https://vtuber-verse.com/" }　※logo：確認済みのロゴ画像URLが未取得のため未設定（判明したら追記する。捏造したURLを入れない）
> - author: { @type: "Person", name: "minase", url: "https://vtuber-verse.com/author/vlogyt/" }　※サイト既存JSON-LDの実装と同一（2026-07-12確認）
> - inLanguage: "ja"
>
> ### 【生成仕様（AI最適化）】
> 1. BlogPosting: 記事本体のメタ情報。
> 2. Product: レビュー対象がある場合は必ず使用。`category`プロパティを明記し、可能であれば`gtin`や`model`も含めること。
> 3. Review: 単体で出力せず、該当するProductの`review`プロパティ内にネストすること。
> 4. ItemList（重要）: 記事内の「見出し構成」や「比較表」「同梱物」を列挙し、記事のトピックオーソリティを明示する。
> 5. HowTo: 設定ガイドがある場合にのみ使用。手順はHowToStepを使用。
> 6. FAQ: Q&Aがある場合はFAQPageを使用。
> 7. 日付処理: 本文内に明示された最終更新日がある場合は、それをdateModifiedに適用すること。
>
> ### 【必須項目リスト（不足時は質問）】
> 1. 記事タイトル（headline）
> 2. メタディスクリプション（description）
> 3. 記事URL（url）
> 4. カテゴリー（articleSection）
> 5. 公開日 / 更新日（ISO8601）
> 6. 代表画像URL（1200x675）
> 7. [該当する場合] 製品詳細（製品名/価格/メーカー/販売サイト/購入リンク）

---

## 適用ノート（実運用での補足）

- **gtin**：実在するバーコード情報を確認できない場合は捏造せず省略する
- **著者情報**：固定データにより個別記事ごとの著者名調査は不要（常に publisher: VTuber Log／author: minase）
- **画像の実寸**：1200x675ぴったりの画像がない場合、既存のアイキャッチ画像を流用しつつ、公開前に実際のピクセルサイズを確認する旨を利用者に伝える
- **articleSection**：サイトの実際のカテゴリ階層（パンくず等）と一致させる。不明な場合は質問に含める
- **HowTo**：Q&A形式の中に「手順1・手順2」のような明示的なステップがない限り使用しない（単なる説明文はHowToStep化しない）
- 出力先がドラフトファイル（.txt）の場合は、`wordpress_output_rules.md`の規則に従い `<!-- wp:html -->` ブロックの中に `<!-- MANUAL_JSONLD -->` ＋ `<script type="application/ld+json">` の形で直接組み込む（チャット上でコードブロック提示のみで終わらせない）

## 実装例（cf_room: deco-be22-review_revised_v2.txt）

`@graph` に以下5ノードを含む構成を採用：
1. `BlogPosting`（headline/description/articleSection/image/author/publisher/mainEntityOfPage）
2. `Product`（name/model/category/brand/description/offers(AggregateOffer)/review(ネスト)）
3. `ItemList`（H2見出し7項目を列挙）
4. `FAQPage`（Q&Aセクションの4問）
5. `BreadcrumbList`

詳細な実装コードは cf_room の `blogs/cf_room/drafts/deco-be22-review_revised_v2.txt` 末尾の `<!-- wp:html -->` ブロックを参照。
