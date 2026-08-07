---
name: system-shira-release-article
description: CD/DVD等リリース記事（アフィリエイト購入導線特化）の制作システム。NEWS「変身」Blu-ray/DVD記事の設計セッションで確定
metadata:
  node_type: memory
  type: project
---

2026-08-07、「NEWS LIVE TOUR 2025 変身」Blu-ray/DVD記事を題材に設計した、CD/DVD等リリース記事専用の制作システム。番組タイムテーブル速報（`draft_XXXX.txt`）・キーワード起点記事（`/shira-keyword-article`）とは別枠。**目的は検索上位表示そのものより「商品リンク経由の購入」を最大化すること**。まだ専用スラッシュコマンド化はしていない（次回以降に`/shira-release-article`として command 化する想定）。

## 1. キーワード選定方針

必須3要素：①商品名・アーティスト名 ②形態（アルバム/DVD/Blu-ray等） ③どこで買う・どれを選ぶ（購入導線 or 比較決定）。

- 「予約」「特典」等の単体高ボリューム語**だけ**を狙いキーワードにはしない（公式サイト・ECが上位を占有し到達性が低いため）。ただし「どこで買う」「違い」等と**組み合わせてタイトル・見出しに含めるのは可**（2026-08-08確定・当初「周辺キーワード止まり」としていたが、ユーザー指示によりタイトル本文への直接組み込みに変更）。例：「予約はどこで？特典の違いも解説」
- 「どこで買う」「どれがいい/どっちがいい」は、公式サイトが自社目線の訴求文言（「ご予約はこちら」等）でしか最適化しておらず、口語の疑問形での検索需要を拾える余地がある。**主軸キーワードとして積極採用する**
- 「どっちがいい」を見出しに使う際、比較対象が曖昧にならないよう明示する（例：「Blu-ray/DVD、どっちがいい？」は形態比較と誤読されるため、実際に比較したいのが初回盤/通常盤ならその語を直接入れる）

## 2. タイトル設計（5パターン、10パターンから絞り込み）

`/shira-keyword-article`の10パターンから、このジャンル向けに5パターンへ再設計。

| # | パターン | 特徴 |
|---|---|---|
| 1 | 比較優先型 | 「違い」が主役、購入は軽く添える |
| 2 | 購入導線優先型 | 「どこで買うべきか」が主役、比較は軽く添える（**目的が購入最大化なら基本この型を採用**） |
| 3 | 疑問統合型 | 比較＋購入を1つの疑問文で統合 |
| 4 | 断定解説型 | 疑問形を使わず「〜を解説」で言い切る |
| 5 | ライト層向け型 | 初めて購入する層向けの平易な表現 |

- **速報統合型（発売日を焼き込む型）は不採用**。発売日は過ぎると陳腐化し、アフィリエイト目的の長期流入と相性が悪い（`rewrite_common_rules.md`のTV番組向け「数値を焼き込まない」原則を、日付にも拡張適用）
- 商品名（アーティスト名+作品名+形態）は**必ず冒頭**に置く。`SEO_guide.txt`の「メリットを冒頭に」という一般原則とは形式上ズレるが、「商品名自体が検索クエリ」であるリリース記事特有の事情として、意図的な派生ルールとする
- 文字数は**32〜36字を目標、40字を上限**とする。これはSEO評価目的ではなく**SERP表示切れ防止**が目的（`SEO_guide.txt`は文字数最適化そのものを「やらなくていいこと」と明記しているため、目的を混同しない）
- **候補が複数ある場合、必ずPowerShell等で`.Length`を実測してから提示する**（目算は`rewrite_common_rules.md`既知の事故要因。本セッションでも目算34→実測41字等のズレが複数回発生した）

## 3. 見出し構成（H2/H3）設計

- タイトルの優先順位（購入導線が主／比較が副）と、見出し構成の優先順位を一致させる。タイトルが「どこで買うべき」を主役にしたのに、購入導線H2が終盤（5番目等）にあると、`SEO_guide.txt`の「ユーザーが最後に知りたいことを起点にする」原則に反する
- H2見出しの長さは記事内で揃える（本セッションで1つだけ41字と突出し、他は13〜31字だった不整合を修正した実例あり）。見出しに要素を詰め込みすぎない
- **内部リンク導線を構成に必ず含める**（`SEO_guide.txt`のトピカル・オーソリティ原則）。同ジャンル記事がまだ無い場合でも、まとめセクションに将来の相互リンク先・カテゴリページへの導線を設計しておく
- 収録内容（セットリスト等の長い一覧）は、特典差などの決定要因となる情報より**後**に配置する（読者の意思決定に直結する情報を先に）

### リンク離脱対策（多重導線）

購入リンクをどこか1箇所にしか置かないと、そこに到達する前の離脱（ブラウザバック）で機会損失になる。以下の5段階でリンクに触れる機会を作る。

1. リード文直後の冒頭クイック情報ボックス（発売日・価格・予約リンク）
2. 比較結論部（「どっちがいい」H2の結論に該当リンクを添える）
3. 特典差など個別セクション（仕様ごとの個別リンク）
4. 購入導線の詳細H2（全リンクを集約）
5. まとめ（最終CTA。ただし省略してよい。2026-08-08 NEWS「変身」記事でユーザー指示によりまとめ末尾のリンクを削除した実例あり）

**各タッチポイントは複数ショップを選べる形にする**（2026-08-08確定）。1つのタッチポイントに1ショップのリンクだけを置き続けると「その都度好きなショップを選べない」という指摘を受けた。冒頭box・比較結論部・特典差セクションそれぞれに、確認済みの直接商品URLを持つ2〜3ショップを並べる（全5ショップを毎回並べる必要はない。個別仕様URLが無いショップは購入導線の集約H2にのみ置く）。

**リンク先が実際にどのSKU（単体仕様 or セット商品）を指しているか、ラベルと一致させる**（2026-08-08確定）。ASPの商品ページURLは「初回盤単体」ではなく「初回盤+通常盤セット」等のバンドル商品である場合がある。ラベル（「初回盤はこちら」等）を安易に付けず、実際のリンク先ページの商品名を確認してから文言を決める。単体仕様の直リンクが無い場合は「セット商品ページです」等、正確な注記を添える。

## 4. アフィリエイトリンク仕様

**本セクションのID・仕組みはShiraNote（shira-treat.com）専用のアフィリエイトアカウントに紐づく（2026-08-08確定）**。楽天もしもの`a_id=4824566`等、セブンネットのバリューコマース`sid=3773727`等、Amazonの`tag=shira1-22`は、いずれもShiraNote運用者本人のASPアカウントIDであり、他のブログ・アカウント（`blogs/cf_room`・`blogs/vtuber_log`・`brands/s4lv`・`brands/mbticode`・`Junk314/junk_juice`等）にそのまま流用できない。他アカウントで同様のリリース記事システムを作る場合は、そのアカウント自身のASP登録・ID取得から着手する必要がある。

`blogs/shira_note/tools/generate_af_link.py`で生成する。使い方は同スクリプトのdocstring参照。

**本文への反映ルール**：1記事内で同じ商品を複数箇所（多重導線、本章2節参照）でリンクする場合も、`href`/`rel`/`referrerpolicy`/`attributionsrc`/インプレッションピクセルの構造は毎回完全に同一のものを使い回す。変えてよいのはリンクテキスト（アンカー内の文言）のみ。ボタン風の装飾で囲む場合も、装飾用のdiv/span側だけを変更し、内側の`<a>`タグ自体（生成スクリプトの出力）には手を加えない。

| ASP/プラットフォーム | 自動変換 | rel属性 | target="_blank" | 備考 |
|---|---|---|---|---|
| 楽天ブックス（もしもアフィリエイト） | ○（商品URLのみで可） | `nofollow`のみ | 付与しない | `a_id=4824566&p_id=54&pc_id=54&pl_id=616`は使い回し可の固定ID |
| セブンネット（バリューコマース） | ○（商品URLのみで可） | `nofollow`のみ | 付与しない | `sid=3773727&pid=892674443`は使い回し可の固定ID |
| Amazon | ×（amzn.to短縮URLは商品ごとに個別発行が必要。ユーザーから受け取る） | `nofollow sponsored noopener noreferrer` | 付与しない | rel属性の付与はスクリプトが自動で行う |

- **`target="_blank"`は本システムでは一切手動付与しない**。理由：①もしも・バリューコマースが実際に生成するコードにtarget属性が無い、②WordPress側で外部リンクに自動付与される（本セッションで実機確認済み）。TV番組タイムテーブル記事（`rewrite_common_rules.md`7章）は手動付与する旧仕様のままなので混同しない
- URLエンコードは必ず`urllib.parse.quote`（Pythonスクリプト）または`[System.Uri]::EscapeDataString`（PowerShell確認時）等のツールで行う。手動の文字列結合は`&`等を含むURLで壊れるリスクがある
- 「配送が必要な物理商材はNG」という`rewrite_common_rules.md`の商材選定ルールは**速報型記事（放送当日CVを狙う記事）専用の制約であり、本システムには適用しない**。本システムは発売前の予約導線がそのまま目的のため、物理商材こそが正解
- **商品ページURLは公式アナウンス直後だと検索エンジンに未反映のことがある**（1年前の類似商品や別商品〈スタジオアルバム vs ライブ映像作品〉と混同するリスクが高い）。WebSearchで確度高く特定できない場合は、ユーザーに直接URL提供を求める。誤った商品へのリンクを推測で提示しない
- **Amazon・楽天ブックスはWebFetchでの自動検証が信頼できない**（2026-08-08確定）。ボット対策により正常なページでも404/503相当の誤判定が返ることがある（本セッションで実際に発生し、ユーザーへの誤った指摘になった）。この2サイトのURL確認は最初からWebFetchを試みず、ユーザーに目視確認を依頼する方が早い。公式サイト・タワーレコード・セブンネットは概ねWebFetchで確認できる

## 4-1. サイト広告ショートコードは不使用

`[nopc][title][/nopc]`・`[nopc][mokujimae][/nopc]`・`[nopc][originalsc][/nopc]`は、番組タイムテーブル速報記事群で使われているサイト広告ネットワークのショートコードだが、本システム（CD/DVDリリース記事）では使用しない（2026-08-08 NEWS「変身」記事で確定）。

## 4-1-2. 比較表は差分のみ載せる

初回盤・通常盤等の比較表は、**値が仕様間で同じ項目（先着共通特典等）を表の行に含めない**。表は「差がある項目」だけに絞り、共通項目は表の下に注記1行でまとめる（2026-08-08確定。本セッションで一度「先着共通特典」を両列に同じ値で重複掲載し、後から統合する手戻りが発生した）。

## 4-1-3. 複数箇所に同じ注記・リンクテキストを置く場合は最初から言い換える

多重導線（本章2節）で同じ商品への注記（「※セット商品ページです」等）を複数セクションに置く場合、**最初から3パターン程度に言い換えて書く**。同一文をコピーして貼ると`qa_draft.py`の「同一文3回リピート」WARNで手戻りになる（2026-08-08確定、本セッションで実際に発生）。

## 4-1-4. タイトル変更時はメタディスクリプションのキーワードも点検する

タイトルの主要キーワードを変更した場合（例：「予約」を追加）、メタディスクリプションの文言も一字一句同期するだけでなく、**含めるキーワード自体が新しいタイトルと整合しているか**を都度確認する（2026-08-08確定。本セッションでタイトルに「予約」を追加した際、メタ側の更新が漏れて後から指摘を受けた）。

## 4-2. 購入導線セクションには判断材料を添える

「どこで予約・購入する？」等の集約セクションは、ただリンクを並べるだけでなく、**販売先ごとの実際の差（価格・ポイント還元・実勢価格・SNS上の人気傾向等）を短く添える**（2026-08-08確定）。差が資料から確認できない販売先は「普段利用しているアカウントでそのまま購入できます」等、無理に差別化しない。数値・キャンペーン情報は資料またはユーザー提供情報にあるものだけを使い、憶測で補わない。

## 4-3. 文体・トーン

「ですます」一辺倒で語尾が単調にならないよう、以下でリズムを作る（2026-08-08確定）。

- 語尾のバリエーション：〜です/ます、〜でしょう、〜てみてください、〜といいですよ、〜ですね　等を混在させる
- 同じ動詞・形容表現の連発を避ける（例：「異なります」の代わりに「違ってきます」「違いがあります」等に言い換える）
- 短文を2文に割る、語順を入れ替える等でリズムを変える
- 事実関係・数値・リンク構造は文体調整の対象外（変更しない）

## 4-4. 検品後の手動チェック

`qa_draft.py`は句点（。）の抜けを検知しない。ERROR/WARN 0件を確認した後も、**最終稿は人の目で通し読みし、文末の句点抜け等の細部を確認する**（2026-08-08 NEWS「変身」記事で実際に句点抜けが1箇所発生し、機械チェック通過後に目視で発見した実例あり）。

## 4-5. 再利用可能なHTMLテンプレート

本セッションで何度も設計→ユーザー指摘→修正を繰り返した末にたどり着いた最終形。**次回はここから書き始め、イチから設計しない**（2026-08-08確定）。色（`{color}`等）は商品・ASPに応じて変更してよいが、構造（display/gap/padding/border-radius等）は変更不要な完成形として扱う。

### ピル型リンクボタン（単体・白背景）

```html
<a href="{href}" rel="{rel}" style="display: inline-flex; align-items: center; justify-content: center; gap: 5px; background: #ffffff; border: 1.5px solid {accent}; color: {accent}; text-decoration: none; font-size: 11.5px; font-weight: 800; padding: 8px 10px; border-radius: 999px; box-shadow: 0 2px 6px {accent}1f; box-sizing: border-box;">
  {リンクテキスト} <span style="font-size:13px;">›</span>
</a>
```

### 2ショップ横並びグリッド（ピル型・SKU注記付き）

```html
<div style="margin: 16px 0; display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
  {ピル型リンク × 2}
</div>
<p style="font-size: 11px; color: #888; margin: 6px 2px 0;">{SKU注記（複数箇所で使う場合は言い換える。4-1-3参照）}</p>
```

### ベタ塗りCTAボタン（冒頭box等・中央寄せ・コンパクト）

```html
<div style="text-align: center;">
  <a href="{href}" rel="{rel}" style="display: inline-flex; align-items: center; gap: 5px; background: {accent}; color: #fff; padding: 6px 20px; border-radius: 999px; text-decoration: none; font-size: 11.5px; font-weight: 800; box-shadow: 0 2px 6px {accent}40;">
    {リンクテキスト} <span style="font-size:13px;">›</span>
  </a>
</div>
```

### スマホ対応比較表（差分のみ・data-labelで仕様名を明示）

```html
<div style="margin: 20px 0; box-sizing: border-box;">
  <style>
    .edition-table { width: 100%; border-collapse: collapse; font-size: 13px; line-height: 1.6; }
    .edition-table th, .edition-table td { border: 1px solid #ddd; padding: 10px; text-align: left; }
    .edition-table thead { background: #2c2c2c; color: #fff; }
    @media (max-width: 600px) {
      .edition-table thead { display: none; }
      .edition-table, .edition-table tbody { display: block; width: 100%; box-sizing: border-box; }
      .edition-table tr { display: grid; grid-template-columns: 1fr 1fr; width: 100%; box-sizing: border-box; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }
      .edition-table td { border: none; box-sizing: border-box; padding: 7px 9px; }
      .edition-table td:first-child { grid-column: 1 / -1; background: #f2f2f2; font-weight: 900; color: #2c2c2c; border-bottom: 1px solid #eee; padding: 6px 9px; }
      .edition-table td:nth-child(2) { border-right: 1px solid #eee; }
      .edition-table td[data-label]::before { content: attr(data-label) "："; display: block; font-size: 9px; font-weight: 900; color: {accent}; margin-bottom: 2px; }
    }
  </style>
  <table class="edition-table" role="region" aria-label="{仕様比較}">
    <thead><tr><th>項目</th><th>{仕様A}</th><th>{仕様B}</th></tr></thead>
    <tbody>
      {差分のある行のみ。<td data-label="{仕様A}">...</td> の形式}
    </tbody>
  </table>
  <p style="font-size: 11.5px; color: #666; margin: 8px 2px 0;">{共通項目の注記（4-1-2参照）}</p>
</div>
```

### 情報カード（ラベル+値グリッド）

```html
<div role="region" aria-label="{カード名}" style="margin: 16px 0; border: 1px solid #e0e0e0; border-radius: 10px; background: #ffffff; box-shadow: 0 4px 12px rgba(0,0,0,0.05); overflow: hidden; box-sizing: border-box; width: 100%;">
  <div style="background: #2c2c2c; padding: 10px 16px;"><span style="font-size: 12px; font-weight: 900; color: #fff;">{見出し}</span></div>
  <div style="padding: 16px; display: grid; gap: 12px; box-sizing: border-box;">
    <div style="display: flex; gap: 10px; align-items: flex-start;">
      <div style="flex-shrink: 0; font-size: 11px; font-weight: 900; color: {accent}; min-width: 72px;">{ラベル}</div>
      <div style="font-size: 13px; color: #333; line-height: 1.6;">{値}</div>
    </div>
    {ラベル+値を必要な数だけ繰り返す}
  </div>
</div>
```

### 販売先ごとの判断材料カード（4-2用）

```html
<div style="margin: 12px 0; display: grid; gap: 8px; box-sizing: border-box;">
  <div style="border: 1px solid {light-border}; border-radius: 8px; padding: 10px 12px; background: {light-bg}; box-sizing: border-box;">
    <div style="font-size: 11px; font-weight: 900; color: {accent}; margin-bottom: 3px;">{販売先名}</div>
    <div style="font-size: 12.5px; color: #333; line-height: 1.5;">{差別化ポイント（価格・ポイント還元・人気傾向等、資料の裏付けがあるものだけ）}</div>
  </div>
  {販売先の数だけ繰り返す}
</div>
```

## 5. SNS発の行動データ（購入先の裏付け等）の扱い

ユーザーからX(旧Twitter)等の個人投稿（購入報告等、出典明記あり）を資料として受け取ることがある。`shira-keyword-article.md`の「匿名掲示板・出典不明のSNS情報は使用しない」は出典明記があるため技術的には抵触しないが、個人の購入行動を特定可能な形で記事に晒すのは避ける。

- **本文では匿名化した傾向情報としてのみ言及する**（例：「SNS上では楽天ブックスでの予約報告が多く見られます（公式集計ではありません）」）
- **個別のハンドルネーム・投稿の直接引用/リンクは行わない**
- どの購入先を優先的に紹介するか（本記事では楽天ブックスを主要導線にした）の判断材料としては使ってよい

関連: [[system_shira_keyword_article]]（タイトル/見出し設計手法の元になった既存フロー）
