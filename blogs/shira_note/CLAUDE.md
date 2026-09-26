# Shira Notes - Claude Code ガイド

## プロジェクト概要

音楽番組タイムテーブル特化の速報系ブログ「Shira Notes」（https://shira-treat.com/）の
記事制作サポート用ワークスペース。

## 音楽番組タイムテーブル記事のリライト

各番組のリライトはスラッシュコマンドで開始する。詳細な手順・参照ファイルは各コマンドファイルに記載。

**全リライト・新規記事共通ルール**：作業開始時に必ず `rewrite_common_rules.md`（このフォルダ直下）を読むこと。禁止ワード・段落分割・タイトル/メタ設計・WPブロック構造・AFリンク仕様・ナビURL一覧はこのファイルが唯一の正。
**ENGINE準拠番組**（コマンドファイル冒頭に宣言あり。現在: うたコン・Venue101）は続けて `rewrite_engine.md`（速報型の共通手順骨格）→ 番組別コマンド（パラメータ）の順で読む。未移行番組は従来どおり番組別コマンドのフル手順が正。

### スラッシュコマンド一覧

| コマンド | 対象番組・記事 | 手順ファイル |
|---|---|---|
| `/mste-rewrite` | ミュージックステーション | `.claude/commands/mste-rewrite.md` |
| `/mste-research` | Mステ リライト用の資料①②リサーチ（資料が渡されなかった回のみ／`/mste-rewrite` から呼ばれる） | `.claude/commands/mste-research.md` |
| `/mste-archive-rewrite` | ミュージックステーション（月次アーカイブ記事） | `.claude/commands/mste-archive-rewrite.md` |
| `/cdtv-rewrite` | CDTVライブ！ライブ！（タイムテーブル速報） | `.claude/commands/cdtv-rewrite.md` |
| `/cdtv-research` | CDTV リライト用の資料①②リサーチ（資料が渡されなかった回のみ／`/cdtv-rewrite` の手順0から呼ばれる） | `.claude/commands/cdtv-research.md` |
| `/cdtv-archive-rewrite` | CDTVライブ！ライブ！（月次アーカイブ記事） | `.claude/commands/cdtv-archive-rewrite.md` |
| `/star-rewrite` | STAR（フジテレビ） | `.claude/commands/star-rewrite.md` |
| `/star-research` | STAR リライト用の資料①②リサーチ（資料が渡されなかった回のみ／`/star-rewrite` の手順0から呼ばれる） | `.claude/commands/star-research.md` |
| `/musicday-rewrite` | THE MUSIC DAY（日本テレビ・年1回特番） | `.claude/commands/musicday-rewrite.md` |
| `/teretou-rewrite` | テレ東音楽祭（テレビ東京・年1回特番） | `.claude/commands/teretou-rewrite.md` |
| `/fns-rewrite` | FNS歌謡祭（フジテレビ・年2回特番） | `.claude/commands/fns-rewrite.md` |
| `/ongakunohi-rewrite` | 音楽の日（TBS・年1回特番） | `.claude/commands/ongakunohi-rewrite.md` |
| `/utadeaetara-rewrite` | NHK夏の音楽祭 うたであえたら（NHK・年1回特番） | `.claude/commands/utadeaetara-rewrite.md` |
| `/utacon-rewrite` | うたコン（NHK総合・定期番組） | `.claude/commands/utacon-rewrite.md` |
| `/24tv-rewrite` | 24時間テレビ（日本テレビ・年1回特番） | `.claude/commands/24tv-rewrite.md` |
| `/tvmrs-rewrite` | テレビ×ミセス（TBS・月曜・コラボバラエティ／ハイブリッド型） | `.claude/commands/tvmrs-rewrite.md` |
| `/kanshasai-rewrite` | 1億2000万人のありがとう 歌の感謝祭（日本テレビ・不定期特番） | `.claude/commands/kanshasai-rewrite.md` |
| `/venue101-rewrite` | Venue101（NHK総合・定期番組。EXTRA・拡大版SP等の特別編成あり） | `.claude/commands/venue101-rewrite.md` |
| `/venue101-research` | Venue101 リライト用の資料①②リサーチ（資料が渡されなかった回のみ／Yahoo検索＋Grok。TVerなし） | `.claude/commands/venue101-research.md` |
| `/allstar-rewrite` | オールスター感謝祭（TBS系クイズ特番・年2回。出演順ではなく企画の流れを軸にする） | `.claude/commands/allstar-rewrite.md` |
| `/shira-qa` | 全番組共通・ドラフト検品（リライト後必須） | `.claude/commands/shira-qa.md` |
| `/shira-keyword-article` | キーワード起点の新規テーマ記事（番組タイムテーブル速報とは別枠） | `.claude/commands/shira-keyword-article.md` |
| `/shira-release-article` | CD/DVD等リリース記事（予約・購入導線特化、1リリース＝1記事） | `.claude/commands/shira-release-article.md` |
| `/shira-release-tracker` | アーティスト別・発売情報トラッカー記事（見落とし防止軸、複数商品を1記事に横断まとめ・継続更新） | `.claude/commands/shira-release-tracker.md` |
| `/shira-research` | 記事ネタ収集（news.ceek.jp 3URL・直近5時間の番組/発売情報） | `.claude/commands/shira-research.md` |
| `/shira-tv-scout` | 番組表ベースの新規ネタ発掘（手動実行・音楽番組に限らず全ジャンルの概要文から候補抽出） | `.claude/commands/shira-tv-scout.md` |
| `/onirenchan-article` | 千鳥の鬼レンチャン サビだけカラオケの出演者の人物記事（放送前に公開・人物ごとに新規記事。下書き1本を人物ごとに差し替える） | `.claude/commands/onirenchan-article.md` |

### リライト時に必要な事前情報（共通）

| 資料 | 内容 |
|---|---|
| 資料① | 放送日・出演者・楽曲・見どころ（必須） |
| 資料② | 直前回のX投稿分析データ（過去一覧・アーカイブパネルに使用。テンプレートは次節参照） |
| 資料③ | 視聴メモ（放送前後に気づいたこと・注目点の断片メモ。**任意**。提供された回のみ「視聴メモ」ブロックとして記事に反映する。仕様は `rewrite_common_rules.md` 10章） |
| アイキャッチ画像URL | 構造化データ（JSON-LD）に反映 |

### ドラフトファイルの命名規則

番組ごとに固定ファイル名1本を上書き運用する。読み込み方は各コマンドの手順①に従う（全面リライトは全文Read 1回、部分更新のみの回は必要セクションだけGrep→部分Read。詳細は `rewrite_common_rules.md` 9章）。

| 番組 | ファイル名 |
|---|---|
| Mステ | `draft_mste.txt` |
| Mステアーカイブ | `draft_mste_archive.txt` |
| CDTV | `draft_cdtv.txt` |
| STAR | `draft_star.txt` |
| CDTVアーカイブ | `draft_cdtv_archive.txt` |
| THE MUSIC DAY | `draft_musicday.txt` |
| テレ東音楽祭 | `draft_teretou.txt` |
| FNS歌謡祭 | `draft_fns.txt` |
| 音楽の日 | `draft_ongakunohi.txt` |
| NHK夏の音楽祭 うたであえたら | `draft_utadeaetara.txt` |
| 音楽の日 ダンスバトル（DREAMダンス） | `draft_dancebattle.txt` |
| うたコン | `draft_utacon.txt` |
| 24時間テレビ | `draft_24tv.txt` |
| テレビ×ミセス | `draft_tvmrs.txt` |
| 歌の感謝祭 | `draft_kanshasai.txt` |
| Venue101 | `draft_venue101.txt` |
| オールスター感謝祭 | `draft_allstar.txt` |
| オールスター感謝祭 マラソン（キーワード起点記事。年号なしで毎年上書き） | `draft_allstar_marathon.txt` |
| 千鳥の鬼レンチャン サビだけカラオケの出演者（人物記事。人物ごとに中身を差し替えて1本を使い回す。1人ずつ結果の書き足しまで終えてから次へ） | `draft_onirenchan.txt` |

保存先：`drafts/` フォルダ（`C:\Users\PC_User\claude project\blogs\shira_note\drafts\`）

**アーティスト別・発売情報トラッカー記事**（`/shira-release-tracker`）は番組ではなくアーティスト単位でファイルを分ける：`draft_release_{artist-slug}.txt`（例：SixTONES → `draft_release_sixtones.txt`）。複数アーティストへの同時展開が前提のため上書き禁止・アーティストごとに1ファイル。

---

## 資料② 入力テンプレート（直前回の確定データ）

リライト開始時に資料②を渡す場合、テンプレート形式（下記）での入力が理想だが、自由形式（調査メモ・分析レポート等）で渡してもよい。

### ガードレールルール（AIへの指示）

資料②相当のデータ（直前回の出演順・歌唱曲・時間帯など）が渡された場合、以下の手順で処理する。

1. `## 資料② INPUT:` ヘッダーと `### セットリスト` の表がすでに揃っている場合 → そのまま使用する
2. テンプレート形式でない場合（自由形式の調査メモ等） → **推測で埋めず**、渡された内容から読み取れる範囲でテンプレート形式に自動整形し、変換結果をユーザーに提示して確認を求める。ユーザーが承認（または修正）してから本編のリライトに着手する
3. 時間帯・アーティスト・曲名など必須項目が読み取れないほど情報が不足している場合のみ、リライトを開始せず不足箇所を質問する

自由形式からの変換時は、原文にない情報（時間帯の推測・曲順の断定等）を creativeに補わない。原文に明記された時刻・曲順表記をそのまま転記し、不明な項目は空欄または「不明」とする。

### テンプレート（コピーして数値・内容を埋める）

```
## 資料② INPUT: {番組名} / {放送日}

### セットリスト【必須】
| 時間帯 | アーティスト | 歌唱曲 | 備考 |
|---|---|---|---|
| 19:XX頃 | アーティスト名 | 曲名 | 初披露/コラボ等あれば |
| 20:XX頃 | アーティスト名 | 曲名 | |

### SNS反響【任意】
- Top_Tweet: {最もエンゲージメントの高かった投稿文面（引用不要・要約で可）}
- Key_Insight: {なぜ伸びたかの考察（1行）}
- Impression: {インプレッション数（わかれば）}
```

### フィールド定義

| フィールド | 必須 | 使われる箇所 |
|---|---|---|
| 番組名 / 放送日 | ✅ | アーカイブパネル・過去一覧カードの日付 |
| セットリスト（時間帯・アーティスト・曲） | ✅ | アーカイブパネルの出演順・歌唱曲確定表示 |
| 備考（初披露・コラボ等） | 推奨 | H3フルカードの特記バッジ・REPORT欄 |
| Top_Tweet / Key_Insight | 任意 | アーカイブパネルの「REPORT」コメント欄 |
| Impression | 任意 | 使用しない（参考記録のみ） |

### 入力例

```
## 資料② INPUT: Mステ / 2026年6月6日

### セットリスト【必須】
| 時間帯 | アーティスト | 歌唱曲 | 備考 |
|---|---|---|---|
| 20:05頃 | SixTONES | Vibes | |
| 20:20頃 | Snow Man | HELLO HELLO | |
| 20:40頃 | 米津玄師 | 地球儀 | ラスト出演 |
| 20:55頃 | King & Prince | Magic Touch | 大トリ |

### SNS反響【任意】
- Top_Tweet: 米津玄師のラスト出演が神がかっていた
- Key_Insight: ラスト出演発表でXのトレンド入り。アーカイブ閲覧が前回比2倍
```

---

## ドラフト検品ツール（リライト後は必ず実行）

```
python tools/qa_draft.py draft_XXXX.txt        # 1ファイル検品
python tools/qa_draft.py --all                 # 全draft検品
python tools/qa_draft.py draft_XXXX.txt --fix  # スマートクォート自動修正＋検品
```

チャットでは `/shira-qa {ファイル名}` で起動する（結果の解釈・修正ルールは `.claude/commands/shira-qa.md`）。
チェック内容: スマートクォート / 禁止ワード / WPブロック開閉 / ショートコード混在 / ショートコード連続配置（originalsc同士の間に本文が必要） / JSON-LDパース / メタ⇔JSON-LD同期 / 本文FAQ⇔JSON-LD FAQPage同期（Q1/A形式のspanマークアップと「Q1｜質問文」のdiv形式に対応。どちらでも取れない形式のみ判定スキップ。2026-09-26にdiv形式へ対応） / AFリンク仕様 / ul style / wp:imageのalign⇔figureのclass不一致（手動修正時のズレ検知） / カテゴリURL残存 / ナビブロックの番組網羅漏れ・自己参照リンク（`rewrite_common_rules.md` 8章のURL一覧と照合。新番組追加時はこの一覧を先に更新） / リード文日付 / 締め文の主観形容詞（`shicho-memo`ブロック内は対象外） / 同一文の記事内3回以上リピート（数字違いは同一視・表現ローテーション用） / 他番組告知パラグラフの放送日が自記事より過去（放送済み番組への導線残存を検知）。 文体（読点2つ以上の段落・ニュース調・句点なし・H3が1つだけのH2。`STYLE_STRICT_FILES`に登録した新規記事は**警告**、それ以外は参考表示。2026-09-26新設）。FAQの照合は、キーワード記事の「H3＋回答」の形にも対応。
WARNは `tools/output/qa_baseline.json` と照合して[新規]/[既知]に分類される。
**全リライトコマンドの最終ステップとして「ERROR 0件・新規WARN 0件」（終了コード0）を確認してから完了報告すること。** `--update-baseline` はユーザー承認時のみ。

## 新規番組記事の立ち上げ

コマンド一覧に無い番組（新番組・単発特番）の記事を一から作る場合は `/shira-new-article` を起動する。
既存draftのH2順を踏襲した構成にし、専用リライトコマンドの新規作成・CLAUDE.mdへの登録まで1セッションで完結させる。詳細手順は `.claude/commands/shira-new-article.md`。

---

## SEOリライト参考ファイル

全番組共通の参照ファイルのみここに記載する。**番組別テンプレート（タイムテーブル本体・JSON-LD・静的ブロック等）は、各リライトコマンド（`.claude/commands/*-rewrite.md`）内の「参照ファイル」セクションを唯一の正とする**（番組追加のたびにここを更新する必要をなくすため）。

| ファイル | 内容 | 対象 |
|---|---|---|
| `rewrite_common_rules.md` | 禁止ワード・段落文体・タイトル/メタ・WPブロック・AFリンク・ナビURLの共通ルール集（**リライト時必読**） | 全番組共通 |
| `rewrite_engine.md` | 速報型リライトの共通手順骨格（手順1〜14・Read/Edit規律・JSON-LD共通差し替え表） | ENGINE準拠番組（現在: うたコン・Venue101）で必読 |
| `C:\Users\PC_User\claude project\blogs\seo\SEO_guide.txt` | SEO基礎・構成設計・タイトル設計・リライトチェックリスト | 全番組共通 |
| `persona_timetable.txt` | タイムテーブル・出演順番記事用ペルソナ（佐藤 真由） | 全番組共通 |
| `template_parts/` | すぐ貼れるHTML部品（冒頭のコード・時間帯の予想カード・配信ガイド）。`README.md`に使い方 | 新規記事・リライト |

---

## 番組表リサーチ（ネタ発掘）

「番組表から調査して」と依頼するだけでよい。手順・出力形式は `/shira-tv-scout`（`.claude/commands/shira-tv-scout.md`）を参照。
音楽番組に絞らず東京エリアの全番組を概要文つきで取得し、記事になりそうな人物・話題をAIが読んで拾う仕組み。**手動実行専用**（自動実行の仕組みは持たない）。既定では翌日から3日分・夜のプライム帯（18:00〜23:00）だけに絞って取得する（`--days`/`--start`/`--end`/`--full`で変更可）。

## JSON-LD 生成ツール

### Mステ記事：JSON-LDブロック丸ごと生成（`/mste-rewrite` 手順14）

```
python tools/build_mste_jsonld.py --sample > tools/output/mste_jsonld_input.json  # 入力雛形
python tools/build_mste_jsonld.py tools/output/mste_jsonld_input.json              # 完成ブロック生成
```

放送日・出演者・FAQ5問を入力JSONに書くと、`<!-- wp:shortcode -->` 〜 `<!-- /wp:shortcode -->` を含む
JSON-LDブロック（BlogPosting/BroadcastEvent/ItemList/FAQPage/BreadcrumbList）を stdout に出す。
出力をドラフト末尾のJSON-LDブロックへEditで丸ごと貼り替える。headline/description⇔メタ、FAQPage⇔本文FAQ の
一字一句一致が構造的に保証される。詳細は `.claude/commands/mste-rewrite.md` 手順14。

### 出演者フラグメント生成（Mステ以外の番組・汎用）

```
python tools/generate_jsonld.py artists.txt   # ファイル入力
python tools/generate_jsonld.py               # 標準入力（空行2連続で終了）
```

mentions / performer 配列・itemListElement 配列・keywords 文字列などの断片のみ生成する。
チャットでは「JSON-LD生成して」「出演者リストからJSON-LD作って」と依頼するだけでよい。

### 出演者リストの書き方ルール（AIへの渡し方）

```
# 1行1アーティスト。グループ/ソロを明示するとより正確になる
SixTONES [G]
Snow Man [G]
坂本冬美 [P]
King & Prince        # & を含むため自動でグループ判定
NewJeans [G]
山下智久 [P]
```

| タグ | 意味 | 使う場面 |
|---|---|---|
| `[G]` | 強制グループ（MusicGroup） | 英語名・カタカナ名のグループ |
| `[P]` | 強制ソロ（Person） | 漢字・ひらがな以外のソロ名義 |
| なし | 自動判定 | `&` `×` `group` 含む → MusicGroup / 漢字2〜6文字 → Person |

**タグなし自動判定の例**
- `King & Prince` → `&` 含む → MusicGroup ✅
- `Aぇ! group` → `group` 含む → MusicGroup ✅
- `坂本冬美` → 漢字4文字 → Person ✅
- `SixTONES` → ルール未適合 → MusicGroup（要確認フラグ付き）

### 出力セクション

| セクション | 使用箇所 |
|---|---|
| [1] mentions / performer 配列 | JSON-LD の `mentions`・BroadcastEvent の `performer` |
| [2] itemListElement 配列 | JSON-LD の `ItemList.itemListElement` |
| [3] keywords 文字列 | CDTV 記事の `keywords` フィールド |
| [4] numberOfItems | JSON-LD の `ItemList.numberOfItems` |

### 注意事項

- `[!] 要確認` フラグが付いたアーティストは MusicGroup/Person を手動で確認する
- ソロ名義でも活動名がグループ名風の場合（例：`米津玄師`）は `[P]` を明示する
