# shira_note アーティスト別 発売情報トラッカー記事 制作コマンド

アーティスト単位で、CD・DVD・Blu-ray・雑誌掲載等の発売・予約情報を横断的にまとめ、継続的に更新していく記事のフロー。
番組タイムテーブル速報（`draft_XXXX.txt`）・キーワード起点記事（`/shira-keyword-article`）・単発リリース深堀り記事（`/shira-release-article`）とは別枠。

「{アーティスト名}の発売情報まとめ記事を作りたい／更新したい」と言われたら、このコマンドの手順に従う。

**目的は「見落とし防止・網羅性」。検索上位表示だけでなく、読者が発表に気づかず終わらないことに価値を置く。** 判断に迷ったらこの目的を優先する。

---

## 位置づけ・差別化の経緯（2026-09-18確定・要参照）

- 当初「テレビ出演情報まとめ」を検討したが、Google実検索で確認したところ「見逃し」は見逃し配信（VOD）の意味で解釈され、ファンブログ（sixtones6info.com等）が既に強い。テレビ出演は頻度が高すぎて「発表に気づかなかった」という悩みが顕在化しにくく、**この切り口では優位性が薄いため対象外**（再検証せず流用しない）
- 「発売物（CD/DVD/Blu-ray/雑誌等）」に絞り「予約し忘れていないか確認したい」という切り口に変更したところ、Google実検索で「予約忘れた」という実際の焦り投稿（Threads/X/Yahoo!知恵袋）は多数見つかったが、それに答える記事は1本も無かった＝**本物の空白地帯**と確認済み
- 競合（sixtones6info.com等のアーティスト専門ファンブログ）は「スケジュール全部乗せ」型で強いが、「予約・発売の見落とし防止」に特化した記事は作っていない

## Step 0. 対象アーティスト・スコープ確認

- アーティスト名を確認する（**複数アーティストへの横展開が前提**。ファイル名・スラッグはアーティスト名を変数として扱い、アーティストごとに1ファイル・1記事とする。同時並存が前提のため上書き禁止）
- 初回作成か、既存記事の更新（リライト）かを確認する

## Step 1. リサーチ（優先順位固定・2026-09-18確立）

無駄な調査を避けるため、以下の優先順位を厳守する。①だけで足りることが多い。

1. **STARTO公式スケジュール（第一情報源・必須）**
   `https://starto.jp/s/p/media/list?tag={artistId}&list[]={artistId}&artist={artistId}&dy={YYYYMM}`
   - **URLの`dy`パラメータは初回ロード時のみ有効**。月を跨いで見る場合はSPAのため直接URL遷移では反映されない。画面上部カレンダーの「→」ボタン（初期表示で概ね座標(203,280)付近）をクリックして遷移する
   - 対象カテゴリは主に`RELEASE`・`MAGAZINE`。ALL表示のまま目視でよい
   - **直近1〜2ヶ月先までは充実するが、それ以降はほぼ空**（発売の1〜3週間前に順次追加される運用と判明済み）。遠い月を無理に調べても情報が無いことが多いので、その旨を記事の「見落とし注意」文脈で正直に書く
2. **WebSearch（通常のGoogle検索）で裏取り**
   STARTO公式にまだ反映されていない大型リリースがないか、「{アーティスト名} {商品名やキーワード} 発売」で検索して確認する。公式サイト・タワーレコード・HMV等の一次情報を優先する
3. **Grok（X検索）は最終手段・ピンポイント利用に限定**
   STARTO・WebSearchで拾いきれない最新告知（ファンクラブ限定商品・SNS限定情報等）の補完のみに使う。**毎回のルーティン更新では使わない**（初稿作成時・公開直前の最終チェック時の2回が目安）。

   **プロンプトの型**（既知の判明分リストを渡し、そこに無い情報だけを探させる）：
   ```
   X（旧Twitter）を検索して調べてください。{アーティスト名}の、これから発売されるCD・DVD・Blu-ray・雑誌・写真集・書籍などの「発売情報」について、公式サイト(starto.jp)やCDショップにまだ広く知られていない最新の告知がないか調べています。

   現時点で確認できている情報（このリストに無いものを探してください）：
   ・{判明済み項目を箇条書き}

   知りたいこと：
   1. 上記リストに無い、新しく発表された発売・予約情報
   2. 情報の出典（ポストのURLまたは投稿者名、いつの投稿か）
   3. 未確定・噂レベルの情報は「未確定」と明記

   現時点（{今日の日付}）でわかる範囲で構いません。
   ```

   **Claude in Chromeでgrok.comを操作する際の既知の罠と対処は、メモリ`env-grok-chrome-automation`に一次情報がある。Grokを実際に使う段階になってから該当メモリをReadすること**（screenshotのタイムアウト・ProseMirror入力欄への貼り付け方法・応答のブロック対策等）。ここでは重複記載しない（毎回のルーティン更新ではGrok自体を使わないため、この詳細を都度読み込む必要はない）。
4. **情報源の信頼度順**：STARTO公式 ＞ 公式サイト/公式X/大手ニュース ＞ 通販サイトの先行掲載 ＞ ファンまとめアカウント（本文に直接転記しない。参考程度に留め、事実は他ソースで裏取りする）

## Step 2. 商品ページ調査・アフィリエイトリンク生成

- **楽天ブックス**：`https://books.rakuten.co.jp/search?sitem={商品名}&g={ジャンルコード}`（DVD=003, CD=002, 雑誌=007）で検索し、商品ページURL（`/rb/{ID}/`）を取得する
  - **定価（参考小売価格）より高い出品は除外する**
  - 「ご注文できない商品」等で購入不可の場合、直リンクは付けず、楽天市場・Amazonの検索/商品リンクのみにする
- **楽天市場**：上記が使えない場合、`https://search.rakuten.co.jp/search/mall/{商品名}/`を検索リンクとして使う（定価超えの出品しかない場合も、検索リンク自体は残してよい。価格比較は読者に委ねる）
- **Amazon**：`https://www.amazon.co.jp/s?k={商品名}`で検索し、対象商品のASIN（10桁、URL中の`/dp/{ASIN}/`）を取得する

**リンク生成は`tools/generate_af_link.py`を使う**（2026-09-18確定仕様）：
```
python tools/generate_af_link.py rakuten  "{楽天商品ページURL or 楽天市場検索URL}" "{リンクテキスト}"
python tools/generate_af_link.py amazon   "{ASINまたはAmazon商品URL}" "{リンクテキスト}"
```
- Amazonは`https://www.amazon.co.jp/dp/{ASIN}/ref=nosim?tag=shira1-22`形式で**完全自動生成できる**（ASINだけで足りる。amzn.to短縮URLの個別発行は不要）
- `tag=shira1-22`は**ShiraNote専用**。他ブログ・他アカウントでは流用不可
- 商品ごとのリンク構成は「①{ASP名}で予約する（個別直リンク、最優先）②楽天市場で探す（検索、もしもAF）③Amazonで予約する／見る（ASIN直リンク）」の3本を基本形にする。直リンクが作れない場合は②③のみでよい

## Step 3. タイトル・見出し設計（確定テンプレート）

- **タイトル型**：「{アーティスト名}最新情報｜発売予定・予約情報をまとめてチェック」（32〜35字前後目安）
- **年月をタイトルに入れない**（継続更新記事のため。鮮度は「最新」の語と冒頭asideの更新日で表現する）
- **スラッグ**：`{artist-slug}-release-schedule`
- **ファイル名**：`draft_release_{artist-slug}.txt`（アーティストごとに1ファイル、以後は上書き運用）

**見出し構成（固定型）**
- H2 {アーティスト名}の発売情報｜最新のCD・DVD/Blu-ray・雑誌まとめ
  - H3 CD・DVDの発売情報
  - H3 雑誌掲載・写真集などの発売情報
- H2 今月の注目リリースをピックアップ
- H2 よくある質問（固定4問。episode非依存の定型文のため、文言はアーティストが変わっても使い回してよい）
  - 発売情報はいつ更新されますか？
  - 予約の締切はいつまでですか？
  - 特典は店舗によって違いますか？
  - 発表に気づかず見逃さないためにはどうすればいいですか？
- H2 まとめ

**⚠️ SEO原則の遵守（2026-09-18リライトで崩れた実例あり）**：SEO_guide.txtの「H2のうち最低1つは疑問形にする」原則を満たすこと。上記H2-1を疑問形にするか（例：「{アーティスト名}の発売情報、見落としてない？」）、他のH2いずれかを疑問形にする。ユーザーが見出しを整形する際に疑問形が失われやすいので、リライト完了前のセルフチェックで必ず確認する。

## Step 4. デザインテンプレート（確定・コピペで使う）

冒頭の「見落とし防止まとめボックス」「商品カード」は、2026-09-18に複数回のフィードバックを経て確定した以下のテンプレートをそのまま使う。イチから設計しない。色は商品カテゴリごとに固定（Blu-ray/DVD＝インディゴ系`#4f46e5`〜`#7c3aed`、雑誌＝ローズ系`#db2777`〜`#f472b6`）。アーティストが変わっても配色はこのまま流用してよい（アーティスト固有色の指定が無い限り）。

### 4-1. 冒頭「発売・予約情報」まとめボックス

```html
<!-- wp:html -->
<aside role="region" aria-label="{アーティスト名}発売情報まとめ" style="display:block;background:#ffffff;border:1px solid #eef0f4;border-radius:18px;padding:20px;margin:1.6em 0;box-shadow:0 10px 30px rgba(15,23,42,0.07);box-sizing:border-box;max-width:100%;">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:8px;">
    <div style="display:flex;align-items:center;gap:10px;">
      <span style="display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:9px;background:linear-gradient(160deg,#4f46e5,#db2777);color:#fff;font-size:13px;flex-shrink:0;">📌</span>
      <span style="font-size:clamp(13px,calc(13px + (100vw - 480px)/200),15px);font-weight:900;color:#0f172a;letter-spacing:0.01em;">{アーティスト名} 発売・予約情報</span>
    </div>
    <span style="font-size:10px;font-weight:800;color:#4f46e5;background:#eef2ff;padding:4px 10px;border-radius:999px;letter-spacing:0.03em;">随時更新</span>
  </div>
  <div style="display:flex;flex-direction:column;gap:12px;">
    <div style="display:flex;align-items:flex-start;gap:12px;">
      <span style="flex-shrink:0;font-size:10.5px;font-weight:800;color:#94a3b8;width:78px;padding-top:2px;letter-spacing:0.02em;">更新日</span>
      <span style="font-size:clamp(12.5px,calc(12.5px + (100vw - 480px)/220),14px);font-weight:700;color:#1e293b;">{更新日}</span>
    </div>
    <div style="display:flex;align-items:flex-start;gap:12px;">
      <span style="flex-shrink:0;font-size:10.5px;font-weight:800;color:#94a3b8;width:78px;padding-top:2px;letter-spacing:0.02em;">直近の発売</span>
      <span style="font-size:clamp(12.5px,calc(12.5px + (100vw - 480px)/220),14px);font-weight:700;color:#1e293b;line-height:1.6;"><span style="color:#4f46e5;font-weight:800;">{直近の発売日}</span>　{直近の商品名}</span>
    </div>
    <div style="display:flex;align-items:flex-start;gap:10px;padding-top:12px;border-top:1px dashed #e2e8f0;">
      <span style="flex-shrink:0;font-size:15px;line-height:1.4;">⚠️</span>
      <span style="font-size:clamp(12.5px,calc(12.5px + (100vw - 480px)/220),14px);font-weight:700;color:#b45309;line-height:1.6;">{見落とし注意の一言。無ければこの行ごと省略}</span>
    </div>
  </div>
</aside>
<!-- /wp:html -->
```

### 4-2. 商品カード（Blu-ray／DVD・CD用）

```html
  <div style="background:#ffffff;border:1px solid #eef0f4;border-radius:16px;padding:16px;box-shadow:0 8px 24px rgba(15,23,42,0.06);box-sizing:border-box;">
    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:10px;">
      <span style="flex-shrink:0;padding:5px 10px;border-radius:8px;background:linear-gradient(160deg,#4f46e5,#7c3aed);color:#fff;box-shadow:0 4px 10px rgba(79,70,229,0.3);white-space:nowrap;"><span style="font-size:13px;font-weight:900;">{M/D}</span><span style="font-size:10px;font-weight:700;opacity:0.9;margin-left:2px;">({曜})</span></span>
      <span style="font-size:10px;font-weight:800;color:#4f46e5;letter-spacing:0.06em;">Blu-ray／DVD</span>
      <span style="display:inline-flex;align-items:center;gap:4px;font-size:10px;font-weight:700;color:#059669;border:1px solid #a7f3d0;background:#f0fdf4;padding:2px 9px;border-radius:999px;margin-left:auto;">
        <span style="width:5px;height:5px;border-radius:50%;background:#059669;"></span>予約受付中
      </span>
    </div>
    <div style="font-size:clamp(14.5px,calc(14.5px + (100vw - 480px)/150),16.5px);font-weight:900;color:#0f172a;line-height:1.45;margin-bottom:4px;">{商品名}</div>
    <div style="font-size:clamp(11.5px,calc(11.5px + (100vw - 480px)/220),13px);color:#64748b;font-weight:600;margin-bottom:10px;">{アーティスト名／出演者名}</div>
    <div style="font-size:clamp(12px,calc(12px + (100vw - 480px)/200),13.5px);color:#475569;line-height:1.7;margin-bottom:12px;">{補足説明。無ければこの行を省略}</div>
    <div style="display:flex;flex-wrap:wrap;gap:8px;">
      {リンクボタン群（Step2参照）}
    </div>
    {楽天リンクを使った場合のみ、もしもインプレッションピクセルimgタグ}
  </div>
```

**在庫状況によるステータスバッジの出し分け**：
| 状況 | バッジ文言 | 色 |
|---|---|---|
| 予約受付中 | 予約受付中 | 緑（`#059669` / 枠`#a7f3d0` / 背景`#f0fdf4`） |
| 購入不可・要確認 | 要確認 | アンバー（`#b45309` / 枠`#fde68a` / 背景`#fffbeb`） |

雑誌カードは同じ構造で、日付チップとカテゴリラベルの色をローズ系（`background:linear-gradient(160deg,#db2777,#f472b6)` / ラベル色`#db2777`）に差し替え、カテゴリラベルは「雑誌」にする。

### 4-3. リンクボタン（共通テンプレート）

```html
<a href="{もしもAFリンク}" rel="nofollow" referrerpolicy="no-referrer-when-downgrade" attributionsrc style="display:inline-flex;align-items:center;padding:6px 12px;border:1px solid #bf0000;border-radius:999px;text-decoration:none;font-size:clamp(11px,calc(11px + (100vw - 480px)/200),13px);font-weight:700;color:#bf0000;background:#fff;">楽天ブックスで予約する ›</a>
<a href="{楽天市場もしもAFリンク}" rel="nofollow" referrerpolicy="no-referrer-when-downgrade" attributionsrc style="display:inline-flex;align-items:center;padding:6px 12px;border:1px solid #9ca3af;border-radius:999px;text-decoration:none;font-size:clamp(11px,calc(11px + (100vw - 480px)/200),13px);font-weight:700;color:#4b5563;background:#fff;">楽天市場で探す ›</a>
<a href="{Amazonリンク}" rel="nofollow sponsored noopener noreferrer" style="display:inline-flex;align-items:center;padding:6px 12px;border:1px solid #232f3e;border-radius:999px;text-decoration:none;font-size:clamp(11px,calc(11px + (100vw - 480px)/200),13px);font-weight:700;color:#232f3e;background:#fff;">Amazonで予約する ›</a>
```

### 4-4. 見落としやすい情報コールアウト（該当情報がある場合のみ）

```html
<!-- wp:html -->
<div role="region" aria-label="見落としやすい発売情報" style="background:#fffaf0;border:1px solid #fde8c8;border-radius:14px;padding:14px 16px;margin:1.5em 0;box-shadow:0 6px 18px rgba(180,83,9,0.06);box-sizing:border-box;width:100%;">
  <div style="display:flex;align-items:flex-start;gap:10px;">
    <span style="flex-shrink:0;display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:8px;background:#f59e0b;color:#fff;font-size:13px;">⚠</span>
    <div>
      <p style="margin:0 0 5px;font-weight:900;font-size:clamp(12.5px,calc(12.5px + (100vw - 480px)/220),14px);color:#92400e;">見落としやすい情報</p>
      <p style="margin:0;font-size:clamp(12.5px,calc(12.5px + (100vw - 480px)/220),14px);color:#78350f;line-height:1.7;">{ファンクラブ限定・SNS限定等、通常ルートに出てこない情報の説明}</p>
    </div>
  </div>
</div>
<!-- /wp:html -->
```

### 4-5. 本文中の強調表現

- 商品名・重要な事実は`<strong>`で太字にする
- 文中で目立たせたい語句は、リンクと誤認しないよう**黒字＋薄い青の下線**にする（`color:#111827;text-decoration:underline;text-decoration-color:#93c5fd;text-decoration-thickness:2px;text-underline-offset:3px;`）。青系のプレーンなリンク色は絶対に使わない

## Step 5. 本文執筆・段落ルール

- `rewrite_common_rules.md`の禁止ワード・**1段落=1テーマ**（複合文は生成時点から別々のwp:paragraphブロックに分ける）を厳守する
- `[nopc][title]`・`[nopc][originalsc]`等の**nopc系ショートコードはこの記事タイプでは使用しない**（2026-09-18確定。速報型タイムテーブル記事とは別の設計方針）
- タイトル・メタディスクリプション行は`<!-- wp:paragraph -->`ブロックで囲む（全記事共通仕様）

## Step 6. 更新（リライト）時の運用

初回作成後、同じファイルに継続的に上書きしていく際の手順。**通常の更新はStep1-1（STARTO公式チェック）だけで完結する**。WebSearch・Grokは「STARTO公式に載っていない大型リリースの噂を聞いた」等、具体的な理由がある時だけ追加で使う（毎回セットで実行しない）。

1. STARTO公式（Step1-1）を確認し、新規追加された項目があるかだけ見る
2. 新規項目が無ければ、冒頭asideの「更新日」だけ最新化して終了（それ以外は触らない）
3. 新規項目があれば、その商品分だけStep2（商品ページ・アフィリエイトリンク調査）を行う。**既存カードのリンクは再検証しない**
4. 新しいカードを追加し、冒頭asideの「更新日」「直近の発売」を最新化する
5. 「要確認」だった商品のうち、発売日を迎えた／購入可能になったものだけステータスバッジを更新する（要確認以外のカードは触らない）
6. 発売済みで役目を終えた「今月の注目リリース」の記述は次回更新時に入れ替える（過去の発売情報カード自体は読者の振り返り需要もあるため即削除しない。記事が長大化した場合のみアーカイブ化を検討し、事前にユーザーへ提案する）

## Step 7. 構造化データ（JSON-LD）

`/shira-keyword-article`と同じ固定データ（publisher/author/inLanguage等）を使う。

- `BlogPosting`：headline/description（メタと一字一句一致）/keywords/image（アイキャッチ必須）/about（`Thing`型、アーティスト名）/hasPart
- `ItemList`：発売情報カードと対応させる（position順、商品ページURLを付与）
- `FAQPage`：本文FAQと一字一句一致（本文に`<strong>`等の装飾を入れても、JSON-LD側はプレーンテキストで一致させる）
- `BreadcrumbList`：カテゴリURL未確定なら「ホーム→記事→本記事」の3階層

## Step 8. 検品

```
python tools/qa_draft.py draft_release_{artist-slug}.txt
```
ERROR 0件・新規WARN 0件を確認してから完了報告する。

---

## 参考実例

`drafts/draft_release_sixtones.txt`（SixTONES、2026-09-18作成・公開済み）。本コマンドの全ステップとデザインテンプレートは、この記事の制作過程で複数回のフィードバックを経て確立した。
