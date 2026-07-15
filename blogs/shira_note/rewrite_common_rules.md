# shira_note 全リライト共通ルール集

全番組のリライト・新規記事作成で必ず適用するルール。各`*-rewrite`コマンド実行時はこのファイルを最初に読むこと。
（旧: メモリ13ファイルに分散していたルールを2026-07-05に統合。以後このファイルが唯一の正）

多くの項目は `python tools/qa_draft.py`（`/shira-qa`）が機械チェックするが、**生成時点から守ることで手戻りをなくす**のが目的。

---

## 1. 禁止表現・ワード（本文・カード説明文・まとめ文・冒頭締め文すべて）

| 禁止表現 | 代替の方向性 |
|---|---|
| 幕を開けます | 「続く」「登場する」「スタートする」等、動作で言い換える |
| 筆頭に、 | 並列で事実を並べる（「〜のコラボ、〇〇・△△など〜が」） |
| 見せ場です | 「集中する」「登場する予定」等、事実ベースの記述に |
| フィナーレを飾ります／締めくくります | 「ラストに登場します」「最後に登場します」等（「担います」はかしこまりすぎなので使わない） |
| 彩る／彩ります／飾る | 「担当する」「出演する」「登場する」「集結」等、具体的な動詞に |

テンプレ感・AI文体が出やすい表現のため全番組で禁止（2026-07-01確定）。

## 2. 段落・文体ルール

- **1段落 = 1テーマ**。複合文（「〜が発表されました＋状況説明」等）は生成時点から別々の`<!-- wp:paragraph -->`ブロックに分ける
- アーティスト列挙文と「今後も追加発表予定」等の告知文も原則別ブロック
- 冒頭リード文（`[nopc][title]`直前）は**1文のみ**（テーマと規模感だけ。「随時更新」等の更新告知は入れない）
- 冒頭2段落目は放送形式の変更点のみ（MC情報・見どころは混ぜない）
- タイムテーブルH2直後リード文は1文のみ（「総勢〇組」「随時更新」不要）
- 締め文（`[nopc][mokujimae][/nopc]`直後）に**主観形容詞NG**（「感動的な」「豪華な」「圧倒的な」等）。「企画名＋など見どころ満載！」の形で完結
- 締め文に具体企画名の詳述は不要。「更新・ブックマーク」の促進のみ
- H2見出しの「｜補足サブテキスト」は、本文に同内容があれば省略を検討（見出しは短いほど良い）
- 資料①に含まれる周辺トリビア（異体字・旧字体の由来、結成◯周年、一部公演への不参加情報等）は、フッター注記やカード説明文などスペースが限られた箇所に機械的に全部詰め込まない。情報量過多で視認性が落ちるため、追加するか・どこに置くか迷ったら最小限（触れない）に倒すか一言確認する（2026-07-08 うたであえたら回でユーザーが差し戻し）
- 冒頭aside「番組情報まとめ」のステータス表示は、数値のみ（「31組発表」等）より代表アーティスト名2〜4組を例示した形式（「あいみょん、くるり、福山雅治、LUNA SEA他、全32組」等）が好まれる。ラベルも「出演者：」→「主な出演：」、「進行：」→「タイムテーブル：」のように内容が一目でわかる語を優先する（同上セッションでの手直し）

## 3. タイトル・メタディスクリプション

- **数値を焼き込まない**：「31組」「司会3名」等その時点の具体数値はタイトル・メタに入れない（追加発表のたびに陳腐化するため）。年号は「番組名2026」のように名称へ直接付け、末尾の【2026】ブラケットは使わない
- **誇張語NG**：「どこよりも早く」「最速で」等の速報訴求はトーンに合わない。「タイムテーブル」「出演者」「順番」等の検索KWと更新中の事実記述に留める
- **番組テーマ名を入れない**（例:「こえる。きこえる。」）。メタ末尾は「タイムテーブルや出演者の順番を最速でお届けします」等KW直結の締めにする
- **メタディスクリプションに「出演順」「順番」「曲順」「登場時間」のいずれかを必ず含める**（タイトルには標準で入っているがメタに漏れやすい。2026-07-11 STARリライトでメタのみ抜けていたユーザー指摘により明文化。既存の全番組ドラフトは満たしている）
- 字数オーバー時（目安120字以内）は修飾語を削ってよい（例:「SUPER BEAVERのスペシャルステージ中継」→「SUPER BEAVERの中継」）
- **メタを修正したらJSON-LDのdescriptionも一字一句同じ文に更新する**（headlineも同様。ユーザー手直し後は聞かれる前に再同期を確認）

## 4. WPブロック構造

- **ドラフト冒頭のタイトル・メタ行も`<!-- wp:paragraph -->`〜`<!-- /wp:paragraph -->`で囲む**（参照メモ扱いで除去しない。ユーザー指定仕様）

```
<!-- wp:paragraph -->
タイトル：{タイトル文字列}
メタディスクリプション（n字）：
{メタディスクリプション文字列}
<!-- /wp:paragraph -->
```

- **ショートコード（`[nopc][title]`・`[nopc][mokujimae]`・`[nopc][originalsc]`）は必ず単独のwp:paragraphブロックに配置**。前後テキストとの同一ブロック混在は絶対NG
  - NG例: `<p>テキスト[nopc][title][/nopc]</p>` / `<p>[nopc][mokujimae][/nopc]締め文</p>`

## 5. HTML実装ルール

- **インラインスタイル付き`<ul>`は使わず`<div>`で書く**（WPテーマCSSがfont-size等を上書きするため）
  - `<ul style="...">` → `<div style="...">`（list-style等リスト固有CSSは削除）、`<li>` → `<div>`、シンプルな箇条書きは先頭に`・`
- **スマートクォート禁止**：EditでHTMLブロックを差し替える際、U+201C/U+201D/U+2018/U+2019が混入するとHTML属性が壊れる。リライト完了後に必ず`python tools/qa_draft.py {ファイル名} --fix`で検証・修正

## 6. 継続性表現の誤読防止

- 「〇年連続」「引き続き」「再び」等を使う場合、直前直後に対象番組名を明記し、今回の番組とは別物だと一文で分かるようにする（年1回特番は「今年が初回」が根幹事実のため）
- 本文修正時は、同内容を要約したバッジ・見出し・カード内テキスト・JSON-LDにも同表現が残っていないか**Grepで横断チェック**（「昨年」「引き続き」「連続」等）

## 7. アフィリエイト

### 楽天もしもAFリンク仕様（全ドラフト共通・2026-06-27確定）

```html
<a href="//af.moshimo.com/af/c/click?a_id=4824566&p_id=54&pc_id=54&pl_id=616&url=https%3A%2F%2Fbooks.rakuten.co.jp%2Franking%2Fdaily%2F002%2F"
  target="_blank"
  rel="nofollow"
  referrerpolicy="no-referrer-when-downgrade"
  attributionsrc>
  楽天ブックスでCDを探す
</a>
<img src="//i.moshimo.com/af/i/impression?a_id=4824566&p_id=54&pc_id=54&pl_id=616" width="1" height="1" style="border:none;" alt="" loading="lazy">
```

- `rel="nofollow"`のみ（sponsored/noopener/noreferrerは付けない）
- ランキング期間は`daily/002/`（hourlyはノイズ・weeklyは遅い）
- `attributionsrc`は値なしのboolean属性
- インプレッションピクセル`<img>`をaタグ直後にセット配置

### 商材選定（速報型記事）

- **配送が必要な物理商材はNG**（外付けHDD・レコーダー・録画機器等）。放送当日に行動できずCVゼロ
- 有効: Amazon Music Unlimited（即日利用可・楽曲予習導線）／楽天ブックスCDランキング（放送後の記念購入）

## 8. ナビブロック「他の音楽番組もチェック」確定URL一覧（2026-06-25確定）

新規ドラフト作成時・年次更新時はこの一覧と照合。カテゴリURL（`/category/musictv/xxx/`）が残っていれば固定URLに更新する。

| 番組 | URL |
|---|---|
| CDTV | `https://shira-treat.com/cdtv-timetable/` |
| STAR | `https://shira-treat.com/star-timetable/` |
| Mステ | `https://shira-treat.com/music-station-timetable/` |
| FNS歌謡祭 | `https://shira-treat.com/fnskayousai-timetable/` |
| THE MUSIC DAY | `https://shira-treat.com/the-musicday-timetable/` |
| 音楽の日 | `https://shira-treat.com/ongakunohi-timetable/` |
| テレ東音楽祭 | `https://shira-treat.com/teretoongakusai-timetable/` |
| うたであえたら | `https://shira-treat.com/utadeaetara-timetable/` |
| レコード大賞 | `https://shira-treat.com/record-award-timetable/` |
| 紅白歌合戦 | `https://shira-treat.com/nhk-kouhaku-timetable/` |
| うたコン | `https://shira-treat.com/utacon-timetable/` |

- **BreadcrumbList（JSON-LD）内のカテゴリURLは変更不要**（WP分類構造用でナビブロックとは別物）
- その記事自身へのリンクは入れない
- **新番組追加時はこの表に加えて`tools/qa_draft.py`の`NAV_FIXED_URLS`・`NAV_SELF_URL_BY_FILENAME`も必ず更新する**（2026-07-15 うたコン追加時、この表のみ更新してqa_draft.py側を漏らす実際の見落としが発生。両方セットで初めて他番組ドラフトの網羅性チェックが機能する）

### ナビブロックHTML雛形（コピペ用・2026-07-15追加）

新規記事作成時、既存draftを読まずにこのHTMLをコピーしてリンク行を組み替えるだけで済む。**自分の番組の行だけ削除する**（例：うたコン記事なら「うたコン」の`<a>`行を除く）。

```html
<!-- wp:html -->
<div style="margin: 18px 0 14px; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px 10px; font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">

  <div style="display: flex; align-items: center; background: #f8fafc; padding: 5px 10px; border-radius: 5px; margin-bottom: 8px;">
    <span style="width: 3px; height: 11px; background: #c94277; margin-right: 8px; border-radius: 1px;"></span>
    <p style="margin: 0; font-size: 10px; font-weight: 800; color: #334155; letter-spacing: 0.02em;">他の音楽番組もチェック</p>
  </div>

  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 10px;">
    <!-- 以下、上表の番組名×URLで<a>を1行ずつ生成。自番組の行は除く -->
    <a href="{URL}" style="display: flex; align-items: center; justify-content: center; height: 34px; background: #ffffff; border: 1px solid #dbe3ec; border-radius: 5px; text-decoration: none; box-sizing: border-box;">
      <span style="font-size: 10px; font-weight: 900; color: #1f2937; letter-spacing: 0.03em; display: flex; align-items: center;">
        {番組名} <span style="font-size: 14px; margin-left: 6px; color: #c94277;">›</span>
      </span>
    </a>
    <!-- ↑を全番組分繰り返す -->
  </div>

  <div style="display: flex; align-items: center; background: #f8fafc; padding: 5px 10px; border-radius: 5px; margin-bottom: 8px;">
    <span style="width: 3px; height: 11px; background: #64748b; margin-right: 8px; border-radius: 1px;"></span>
    <p style="margin: 0; font-size: 10px; font-weight: 800; color: #334155; letter-spacing: 0.02em;">今夜の放送で気になったアーティストの楽曲・CDを探す</p>
  </div>

  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px;">
    <a href="https://amzn.to/3PbpcG5" target="_blank" rel="nofollow sponsored noopener noreferrer" style="display: flex; align-items: center; justify-content: center; height: 34px; background: #232f3e; border-radius: 5px; text-decoration: none; box-sizing: border-box; border-bottom: 2px solid #161d26;">
      <span style="font-size: 10px; font-weight: 900; color: #ffffff; letter-spacing: 0.05em; display: flex; align-items: center;">
        CDをAmazonで探す <span style="font-size: 14px; margin-left: 6px; color: #ff9900;">›</span>
      </span>
    </a>

    <a href="//af.moshimo.com/af/c/click?a_id=4824566&amp;p_id=54&amp;pc_id=54&amp;pl_id=616&amp;url=https%3A%2F%2Fbooks.rakuten.co.jp%2Franking%2Fdaily%2F002%2F" target="_blank" rel="nofollow" referrerpolicy="no-referrer-when-downgrade" attributionsrc style="display: flex; align-items: center; justify-content: center; height: 34px; background: #bf0000; border-radius: 5px; text-decoration: none; box-sizing: border-box; border-bottom: 2px solid #8a0000;">
      <span style="font-size: 10px; font-weight: 900; color: #ffffff; letter-spacing: 0.05em; display: flex; align-items: center;">
        楽天ブックスでCDを探す <span style="font-size: 14px; margin-left: 6px; color: #ffffff; opacity: 0.8;">›</span>
      </span>
    </a>
  </div>

  <img src="//i.moshimo.com/af/i/impression?a_id=4824566&amp;p_id=54&amp;pc_id=54&amp;pl_id=616" width="1" height="1" style="border:none;" alt="" loading="lazy">

  <a href="https://amzn.to/4xMd00d" target="_blank" rel="nofollow sponsored noopener noreferrer" style="display: flex; align-items: center; justify-content: flex-start; height: 40px; background: linear-gradient(90deg, {番組カラー1}, {番組カラー2}); border-radius: 5px; text-decoration: none; box-sizing: border-box; border: 1px solid {アクセントカラー}; box-shadow: 0 2px 4px rgba(0,0,0,0.08); padding: 0 15px;">
    <span style="font-size: 9px; font-weight: 900; color: {アクセントカラー}; border: 1px solid {アクセントカラー}; padding: 1px 4px; border-radius: 2px; margin-right: 12px; margin-left: 3px;">Music</span>
    <span style="font-size: 11px; font-weight: 800; color: #ffffff; letter-spacing: 0.05em;">Amazon Musicで楽曲を聴く（30日間無料）</span>
    <span style="font-size: 18px; color: {アクセントカラー}; margin-left: auto;">›</span>
  </a>

</div>
<!-- /wp:html -->
```

`{番組カラー1}`/`{番組カラー2}`/`{アクセントカラー}`は記事の配色イメージに合わせる（無指定なら`#0a4d68`/`#0d6a8f`/`#e8a33d`を使用）。

## 9. 効率化ルール（Read/Edit・往復削減）

- **ユーザー手動編集の確認はgit diffを優先する**：ドラフト修正後にユーザーが直接編集した内容を確認する際、system-reminderに具体的な差分が含まれていない場合は、まず `git diff {ファイル名}`（PowerShell）で変更行のみ取得する。全文Read（複数チャンクにまたがる場合）での目視比較は、トークン消費が大きく見落としリスクも高いため避ける。gitで追跡されていない・差分取得に失敗した場合のみ全文Readにフォールバックする。
- **文字数を伴う複数候補は提示前に一括実測する**：タイトル・見出し・メタディスクリプション等、文字数の優劣で判断が必要な提案をユーザーに出す前に、必ずPowerShellで全候補の`.Length`を実測してから提示する。目算・概算での字数記載は誤りの原因になり、訂正の往復が発生する（2026-07-17 Mステ1500回記念H2で目算「35字前後」が実測42字と判明し手戻りが発生）。

---

## 最終チェック

リライト完了後は必ず `/shira-qa {ファイル名}` を実行し **「ERROR 0件・新規WARN 0件」（終了コード0）** を確認してから完了報告する。
既知WARN（`tools/output/qa_baseline.json` 登録済みの残置分）は、該当箇所を触るリライトのついでに解消し、解消後にユーザー承認の上 `--update-baseline` でベースラインを更新する。
