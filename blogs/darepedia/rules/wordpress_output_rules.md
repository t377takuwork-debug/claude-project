# darepedia WordPress貼り付け用出力ルール（唯一の正）

**2026-08-26全面改訂**：darepedia.comはshira-treat.comと同じテーマ・プラグイン構成のWordPressサイトであることが確認できたため、`blogs/shira_note/drafts/draft_cdtv.txt`と同じGutenbergブロックコメント形式を採用する（旧版の「実タグを直接出力しブロックコメントは不要」という方針は誤りだったため撤回）。

## 1. ファイル形式

- 拡張子は`.txt`（`.html`にしない。IDE/OSがプレビュー表示しようとして紛らわしくなるため）
- 保存先は`drafts/`フォルダ、ファイル名は`draft_{スラッグ}.txt`（記事ごとに新規ファイル。上書き運用はしない）

## 2. Gutenbergブロックコメントの基本

全要素を`<!-- wp:ブロック名 -->`〜`<!-- /wp:ブロック名 -->`で明示的に囲む。

- 段落：`wp:paragraph`
- 見出し：`wp:heading`（h2はデフォルト属性なし。h3は`<!-- wp:heading {"level":3} -->`のように属性を付与する。属性を付けないとGutenberg側がh2として扱い、WordPress保存時に`<h3>`がh2へ矯正される）
- カスタムデザイン（summary-card・要点カード・プロフィール表など）：`wp:html`
- **段落は1文＝1`wp:paragraph`を基本とする。** 2文以上をひとつの`<p>`にまとめず、文単位でブロックを分ける（改行を入れてスマホでの可読性を上げる）。ただし直前の文への短い相槌・言い換えなど、分けるとかえって不自然な場合は無理に割らなくてよい

### 貼り付け手順

1. WordPress編集画面右上メニューから「コードエディター」に切り替える
2. ドラフトの内容を全文貼り付ける
3. 「ビジュアルエディター」に戻す

**ビジュアルエディターへ直接貼り付けるとブロックコメントが解釈されず、文字列としてそのまま表示される。** 必ずコードエディター経由にする。

## 3. ファイル冒頭の記法

```
<!-- wp:paragraph -->
タイトル：{確定タイトル}
メタディスクリプション（n字）：
{メタディスクリプション文字列}
スラッグ：{確定スラッグ}
アイキャッチ画像：{画像URL（ユーザーから提供された場合のみ記載。無ければ行ごと省略）}
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>[nopc][title][/nopc]</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>{リード文1文目}</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>{リード文2文目以降。1文＝1wp:paragraphで分ける}</p>
<!-- /wp:paragraph -->
```

- スラッグ・アイキャッチ画像の行は、WordPress貼り付け時にそのまま反映されるものではなく、公開作業者への申し送りメモ（ファイル名・メディア設定の参照用）。ファイル名（`draft_{スラッグ}.txt`）とも一致させる
- `[nopc][title][/nopc]`は**タイトル・メタブロック直後、本文の最初のwp:paragraphに単独で配置**（リード文より前）
- summary-card等の`wp:html`装飾ブロックを使う場合は、リード文の後・本文見出し開始前に配置する
- **`[nopc][mokujimae][/nopc]`は、リード文（＋任意のsummary-card）の直後・最初の`<h2>`が始まる直前に単独のwp:paragraphで配置する**（目次挿入位置のマーカー）

```
<!-- wp:paragraph -->
<p>[nopc][mokujimae][/nopc]</p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2>最初の見出し</h2>
<!-- /wp:heading -->
```

## 4. 見出しタグ

- `<!-- wp:heading --><h2>見出しテキスト</h2><!-- /wp:heading -->`
- `<!-- wp:heading {"level":3} --><h3>見出しテキスト</h3><!-- /wp:heading -->`
- 見出しレベルを飛ばさない（H2の直下はH3のみ）

## 5. 装飾HTML（summary-card・要点カード等）

- `design_components.md`のコンポーネントは`<!-- wp:html -->`〜`<!-- /wp:html -->`で囲んだ実HTMLとして記述する
- `<style>`ブロックは記事につき1回のみ、最初の`wp:html`ブロック（通常はsummary-card）の中でまとめて定義する
- **`wp:html`ブロックの中に別の`<!-- wp:xxx -->`を入れ子にしない**（Gutenbergのパーサーがブロックコメントをフラットに走査するため、意図通りに扱われる保証がない）
- スマートクォート（U+201C/201D/2018/2019）を混入させない
- すべての装飾`<aside>`/`<div>`/`<section>`に`role="region" aria-label="..."`を付与する
- スマホ表示を想定し、`width:100%`・`box-sizing:border-box`を基本にする

## 6. SNS埋め込み

X/InstagramのURLは、単独の`wp:paragraph`ブロック内に生URLをそのまま配置するのが基本。

```
<!-- wp:paragraph -->
<p>https://www.instagram.com/p/xxxxxxxxxxx/</p>
<!-- /wp:paragraph -->
```

`<iframe>`等を手組みしない。WordPress保存時にGutenbergが自動でリッチ埋め込みに変換する想定。

**ユーザーから公式の埋め込みコード（`<blockquote class="instagram-media">`＋`<script>`等）が提供された場合は、生URLに変換せずそのまま使う。** その場合は次の形式に従う。

```
<!-- wp:html -->
<blockquote class="instagram-media" ...>...</blockquote>
<script async src="//www.instagram.com/embed.js"></script>
<!-- /wp:html -->
```

- `<blockquote>`のインラインstyleにある`margin: 1px;`は`margin: 1px auto;`に変更し、`max-width`の範囲内でセンタリングする
- 人物の顔写真が写っている投稿は、内部リンク的な「本人確認」の役割を持つため、記事末尾に専用見出し（「〇〇のSNSでの様子」等）でまとめて置くのではなく、最初の見出しの直下やプロフィール表の直前など、本人の姿を見せる意味がある場所に分散して配置する
- 埋め込みを2本以上使う場合、連続して並べない（間に本文セクションを挟む）。1記事あたり2〜4本程度が目安（`design_components.md` §3）

## 7. 広告差し込み（`[nopc][originalsc][/nopc]`）

shira_noteと同じ広告枠ショートコード。**記事1本につき1箇所を目安に**、本文の中盤（複数のH2セクションを読んだ後）に単独のwp:paragraphで配置する。

```
<!-- wp:paragraph -->
<p>[nopc][originalsc][/nopc]</p>
<!-- /wp:paragraph -->
```

- ショートコード（`[nopc][title]`・`[nopc][mokujimae]`・`[nopc][originalsc]`）は必ず単独のwp:paragraphブロックに配置する（前後テキストとの同一ブロック混在は禁止）
- 同じショートコードを連続配置しない（間に見出し・本文パラグラフ等の実質コンテンツを挟む）

## 8. 内部リンク

`<a href="...">`で実在URLのみを使用する。`internal_links.md`にないURLをリンク先にしない（`qa_draft.ps1`でチェック対象）。

## 9. 検証手順（編集の都度必ず実施）

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\PC_User\claude project\blogs\darepedia\tools\qa_draft.ps1" "drafts\draft_{スラッグ}.txt"
```

**完了報告の前に「ERROR 0件」を確認する。** WARNは下記10の公開前チェックリストとして扱う。

## 10. 公開前チェックリスト（WARNの解消）

- [ ] 仮リンク`href="#"`を実URLに差し替え（またはリンクごと削除）
- [ ] 投稿タイトル欄・SEOプラグインのメタディスクリプション欄へ、ドラフト冒頭の参照メモから転記
- [ ] カテゴリ（celebrity/sports/expert/others）を設定
- [ ] 貼り付け後、ビジュアルエディターで「無効なコンテンツ」警告や表示崩れが出ていないか目視確認
- [ ] SNS埋め込みが実際にカード表示されるか確認（自動変換に失敗した場合はURLのみのテキストリンクになるため要注意）

## 11. 構造化データ（JSON-LD、任意）

ユーザーから依頼があった場合のみ追加する（毎回必須ではない）。フォーマットは`blogs/shira_note/drafts/draft_cdtv.txt`末尾の実装を土台とし、darepediaでは記事末尾に次の3種を`@graph`でまとめる（放送番組の実況記事ではないため`BroadcastEvent`/`ItemList`は不要）。

```
<!-- wp:html -->
<!-- MANUAL_JSONLD -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    { "@type": "BlogPosting", ... },
    { "@type": "FAQPage", ... },
    { "@type": "BreadcrumbList", ... }
  ]
}
</script>
<!-- /wp:html -->
```

**サイト定数（毎回リサーチし直さず、この値を使う。2026-08-27にサイト本体から確認済み）：**

| 項目 | 値 |
|---|---|
| サイト名 | だれペディア |
| 運営者（author） | YU-i |
| 運営者情報ページ | https://darepedia.com/operator-information/ |
| publisher.name | だれペディア |
| publisher.url | https://darepedia.com/ |
| publisher.logo.url | https://darepedia.com/wp-content/uploads/2025/08/darepedia.webp |

**記事ごとに確認・記入する項目：**

- `headline`/`description`：確定タイトル・メタディスクリプションと一致させる
- `articleSection`：設定したカテゴリ名（例：芸能人）
- `image`：アイキャッチ画像URL（ファイル冒頭の参照メモと一致させる）。width/heightは実寸が分かる場合のみ追加（不明なら省略してよい。必須ではない）
- `datePublished`/`dateModified`：**特に指示がなければドラフト作成日でよい**（実際の公開日が確定したら差し替える）
- `about`：記事の対象（番組・作品名）。公式サイト等のURLがあれば`sameAs`に入れる（無ければ`name`のみで省略可）
- `mentions`：記事内で扱う人物
- `FAQPage`：本文の「よくある質問」セクションと同内容（新しい文言を作らず転記する）
- `BreadcrumbList`：ホーム → カテゴリページ（`https://darepedia.com/category/{celebrity|sports|expert|others}/`）→ 記事

`qa_draft.ps1`はJSON構文の妥当性のみ検証する（`[OK] JSON-LD syntax valid`）。スキーマ内容の正しさは目視確認する。
