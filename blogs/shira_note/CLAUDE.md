# Shira Notes - Claude Code ガイド

## プロジェクト概要

音楽番組タイムテーブル特化の速報系ブログ「Shira Notes」（https://shira-treat.com/）の
記事制作サポート用ワークスペース。

## ネタ収集ツール

### 実行方法

```
python tools/collect_news.py              # 今日の番組・リリース情報を収集
python tools/collect_news.py --date YYYYMMDD  # 指定日の番組を収集（例: --date 20260627）
```

チャットでは「ネタ収集して」「今日のネタを集めて」と依頼するだけでよい。
日付を指定したい場合は「6月27日のネタを収集して」のように伝えればよい。

### 出力ファイル

| ファイル | 内容 |
|---|---|
| `tools/output/programs.md` | 番組ネタ候補（音楽番組 / 長時間特番） |
| `tools/output/releases.md` | リリース情報ネタ候補（過去2時間以内のみ。深夜〜早朝は0件になりやすい） |

### 収集先

| 対象 | URL | 備考 |
|---|---|---|
| 番組情報 | `https://bangumi.org/epg/td?broad_cast_date=YYYYMMDD&ggm_group_id=42` | 省略時は実行日、`--date` で指定可。東京エリア（42固定） |
| リリース情報 | mdpr.jp / realsound.jp / oricon.co.jp | `--date` 指定時はスキップ。natalie.mu は 403 のためスキップ |

### 効率的な依頼パターン

| やりたいこと | 依頼例 |
|---|---|
| 番組・リリース両方収集 | 「ネタ収集して」「今日のネタを集めて」 |
| 日付を指定して収集 | 「6月27日のネタを収集して」 |
| 番組情報だけ見たい | 「番組情報だけ収集して」 |
| リリース情報だけ見たい | 「リリース情報だけ収集して」 |
| 結果を見たい（再実行不要） | 「前回のネタ結果を見せて」 |

### キーワード設定（tools/collect_news.py）

- **MUSIC_KEYWORDS**: 音楽番組として拾うキーワード一覧
- **MUSIC_KEYWORDS_EXACT**: 単語境界が必要なキーワード（STAR、SONGSなど部分一致を避けたいもの）
- **LONG_SPECIAL_KEYWORDS**: 長時間特番として拾うキーワード（タイトル先頭40文字のみ対象）

キーワードの追加・変更が必要な場合は「〇〇をキーワードに追加して」と依頼。

## ドラフト検品ツール（リライト後は必ず実行）

```
python tools/qa_draft.py draft_XXXX.txt        # 1ファイル検品
python tools/qa_draft.py --all                 # 全draft検品
python tools/qa_draft.py draft_XXXX.txt --fix  # スマートクォート自動修正＋検品
```

チャットでは `/shira-qa {ファイル名}` で起動する（結果の解釈・修正ルールは `.claude/commands/shira-qa.md`）。
チェック内容: スマートクォート / 禁止ワード / WPブロック開閉 / ショートコード混在 / JSON-LDパース / メタ⇔JSON-LD同期 / AFリンク仕様 / ul style / カテゴリURL残存 / リード文日付 / 締め文の主観形容詞。
**全リライトコマンドの最終ステップとしてERROR 0件を確認してから完了報告すること。**

## 番組情報 差分監視ツール

```
python tools/watch_programs.py            # 今日〜7日先をスキャンし前回との差分を検出
python tools/watch_programs.py --days 14  # 14日先まで
```

チャットでは「番組監視して」「新しい特番出てないか見て」と依頼するだけでよい。
1日1回実行すると、新規に番組表へ載った音楽番組・特番、時間変更、消失（放送中止の可能性）を `tools/output/watch_report.md` に出力する。初回はベースライン保存のみ。

## 新規番組記事の立ち上げ

コマンド一覧に無い番組（新番組・単発特番）の記事を一から作る場合は `/shira-new-article` を起動する。
既存draftのH2順を踏襲した構成にし、専用リライトコマンドの新規作成・CLAUDE.mdへの登録まで1セッションで完結させる。詳細手順は `.claude/commands/shira-new-article.md`。

## 音楽番組タイムテーブル記事のリライト

各番組のリライトはスラッシュコマンドで開始する。詳細な手順は各コマンドファイルに記載。

### スラッシュコマンド一覧

| コマンド | 対象番組・記事 | 手順ファイル |
|---|---|---|
| `/mste-rewrite` | ミュージックステーション | `.claude/commands/mste-rewrite.md` |
| `/cdtv-rewrite` | CDTVライブ！ライブ！（タイムテーブル速報） | `.claude/commands/cdtv-rewrite.md` |
| `/cdtv-archive-rewrite` | CDTVライブ！ライブ！（月次アーカイブ記事） | `.claude/commands/cdtv-archive-rewrite.md` |
| `/star-rewrite` | STAR（フジテレビ） | `.claude/commands/star-rewrite.md` |
| `/musicday-rewrite` | THE MUSIC DAY（日本テレビ・年1回特番） | `.claude/commands/musicday-rewrite.md` |
| `/teretou-rewrite` | テレ東音楽祭（テレビ東京・年1回特番） | `.claude/commands/teretou-rewrite.md` |
| `/fns-rewrite` | FNS歌謡祭（フジテレビ・年2回特番） | `.claude/commands/fns-rewrite.md` |
| `/ongakunohi-rewrite` | 音楽の日（TBS・年1回特番） | `.claude/commands/ongakunohi-rewrite.md` |
| `/utadeaetara-rewrite` | NHK夏の音楽祭 うたであえたら（NHK・年1回特番） | `.claude/commands/utadeaetara-rewrite.md` |
| `/shira-qa` | 全番組共通・ドラフト検品（リライト後必須） | `.claude/commands/shira-qa.md` |

### リライト時に必要な事前情報（共通）

| 資料 | 内容 |
|---|---|
| 資料① | 放送日・出演者・楽曲・見どころ（必須） |
| 資料② | 直前回のX投稿分析データ（過去一覧・アーカイブパネルに使用） |
| アイキャッチ画像URL | 構造化データ（JSON-LD）に反映 |

### ドラフトファイルの命名規則

番組ごとに固定ファイル名1本を上書き運用する。各コマンドの手順①に従い、必要なセクションのみ Read してから更新する（全体Readは不要）。

| 番組 | ファイル名 |
|---|---|
| Mステ | `draft_mste.txt` |
| CDTV | `draft_cdtv.txt` |
| STAR | `draft_star.txt` |
| CDTVアーカイブ | `draft_cdtv_archive.txt` |
| THE MUSIC DAY | `draft_musicday.txt` |
| テレ東音楽祭 | `draft_teretou.txt` |
| FNS歌謡祭 | `draft_fns.txt` |
| 音楽の日 | `draft_ongakunohi.txt` |
| NHK夏の音楽祭 うたであえたら | `draft_utadeaetara.txt` |

保存先：このフォルダ直下（`C:\Users\PC_User\claude project\blogs\shira_note\`）

---

## SEOリライト参考ファイル

記事のリライト時は以下のファイルを参照すること。

| ファイル | 内容 | 対象 |
|---|---|---|
| `C:\Users\PC_User\claude project\blogs\seo\SEO_guide.txt` | SEO基礎・構成設計・タイトル設計・リライトチェックリスト | 全番組共通 |
| `persona_timetable.txt` | タイムテーブル・出演順番記事用ペルソナ（佐藤 真由） | 全番組共通 |
| `template_timetable.txt` | タイムテーブル記事リライト用ベーステンプレート（冒頭〜aside〜締め） | Mステ |
| `template_jsonld_mste.txt` | 構造化データ（JSON-LD）テンプレート・プレースホルダー一覧 | Mステ |
| `template_mste_static.txt` | 変更不要の静的ブロック（見逃し配信・ナビゲーション/アフィリエイト） | Mステ |
| `template_cdtv_static.txt` | 変更不要の静的ブロック（見逃し配信・ナビゲーション/アフィリエイト） | CDTV |
| `template_jsonld_cdtv.txt` | 構造化データ（JSON-LD）テンプレート・プレースホルダー一覧 | CDTV |

---

## JSON-LD 出演者データ生成ツール

### 実行方法

```
python tools/generate_jsonld.py artists.txt   # ファイル入力
python tools/generate_jsonld.py               # 標準入力（空行2連続で終了）
```

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

---

## 資料② 入力テンプレート（直前回の確定データ）

リライト開始時に資料②を渡す場合は、**必ず以下のテンプレートで入力すること**。
テンプレート形式でない場合、AIは推測処理を開始せず「テンプレートに従って入力してください」と返す。

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

### ガードレールルール（AIへの指示）

資料②が渡された場合、以下を確認すること：
1. `## 資料② INPUT:` ヘッダーが存在するか
2. `### セットリスト` セクションにデータが1行以上あるか

上記のいずれかが欠けている場合は、リライトを開始せず以下を返すこと：
> 「資料②がテンプレート形式ではありません。`shira_note/CLAUDE.md` の『資料② 入力テンプレート』をコピーし、セットリストを埋めてから再度渡してください。」

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

