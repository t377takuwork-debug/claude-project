# 業務OS 全体索引（README）

このリポジトリは、Note/X/Threads運用・ブログ制作・SEO施策の**全業務資産**を格納する。
どのAI（Claude/他社モデル問わず）・どのセッションでも、**このファイル → 該当SOP → 個別ファイル**の順に読めば同じ品質で業務を再現できる。

最終更新: 2026-07-06（暗黙知55ファイルのrepo統合を完了）

---

## 最初に読む3ファイル

1. `README.md`（本ファイル）— 全体地図
2. `CLAUDE.md` — 行動規範・タスク別エントリポイント（Claude Code用だが原則は全AI共通）
3. `docs/business_inventory.md` — 業務棚卸し表（日次/週次/不定期の全業務と完了条件）

## タスク → 開くファイル 対応表

| やりたいこと | SOP（手順書） | 実行手段 |
|---|---|---|
| shira_note 番組リライト | `docs/sop/sop_shira_note_rewrite.md` | `blogs/shira_note/.claude/commands/` の番組別コマンド |
| MBTICODE X・Threads投稿／リプライ | `docs/sop/sop_mbticode_sns.md` | `/mbticode-post`・`/reply`・`/post-review` |
| Note記事生成（MBTICODE／s4lv） | `docs/sop/sop_note_article.md` | `/note-article`・`/quality-guardrail`・`brands/tools/qa_article.py` |
| junk_juice 記事（クライアント） | `docs/sop/sop_junk_juice.md` | `/junk-theme`・`/junk-article`・`brands/tools/qa_article.py` |
| バズ投稿の分析 | －（スキル内完結） | `/buzz-analysis`（収集は手動・分析は固定フレームワーク） |
| 週次KPI記録 | －（スキル内完結） | `/kpi-weekly`（記録＋前週比3点コメント） |
| 新ブログの立ち上げ | －（スキル内完結） | `/blog-launch`（shira_note構造の横展開手順） |
| 戦略・方針判断 | －（会議システム） | `/notekaigi`（定義: `docs/systems/system_ai_management_meeting.md`） |
| ASP記事設計 | －（会議システム） | `/asp-kaigi`→`/asp-theme`→`/asp-outline`（定義: `docs/systems/`） |
| ブログ戦略・CV改善 | －（会議システム） | `/blog-kaigi`・`/monetize-kaigi`（定義: `docs/systems/system_blog_monetize_kaigi.md`） |

## ディレクトリ地図

```
claude project/
├── README.md              ← 本ファイル（全体索引）
├── CLAUDE.md              ← 行動規範・ナビゲーター
├── .claude/commands/      ← 汎用スキル18本（投稿生成・記事生成・会議・バズ分析・KPI・ブログ立ち上げ）★唯一の正
├── docs/
│   ├── business_inventory.md  ← 業務棚卸し表
│   ├── sop/               ← 業務別SOP 4本
│   ├── rubrics/           ← タイトル採点ルーブリック（点数の捏造防止）
│   ├── systems/           ← 会議システム定義 5本
│   ├── rules/             ← 横断的な作業ルール（タスク確認方法・notekaigi起動タイミング）
│   └── reference/         ← SNS.txt（blog-kaigi/monetize-kaigiの思考モデル参照元）
├── blogs/
│   ├── shira_note/        ← 音楽番組速報ブログ（メイン稼働・機械QA完備）
│   │   ├── CLAUDE.md          ← 番組別コマンド一覧・ツール使用法
│   │   ├── rewrite_common_rules.md ← リライト共通ルール（唯一の正）
│   │   ├── rules/             ← 番組別の落とし穴チェックリスト 9本
│   │   ├── .claude/commands/  ← リライト・QA・リサーチ系コマンド 13本
│   │   └── tools/             ← qa_draft.py（機械検品）・collect_news.py・watch_programs.py
│   ├── seo/SEO_guide.txt  ← 全ブログ共通SEOマスターガイド
│   └── cf_room / darepedia / vtuber_log ← 準備中（CLAUDE.mdは空ファイル。稼働時はshira_note構造＝共通ルール1本＋コマンド＋機械QAを横展開）
├── brands/
│   ├── CLAUDE.md          ← s4lv・MBTICODE共通ナビ
│   ├── tools/             ← qa_post.py（SNS投稿の機械検品）・qa_article.py（Note記事の機械検品）
│   ├── writing/           ← ライティング原則4ファイル（起点: writing_core.md）
│   ├── s4lv/
│   │   ├── rules/         ← 文体定義・Note記事プロセス・アカウント方針 9本
│   │   ├── examples_x_posts.md ← X投稿見本バンク（Good/Bad対比・生成前に読む）
│   │   ├── shared/ ai/ pro/ ← プロフィール・実績データ
│   │   └── （brands/s4lv_pro/ は空フォルダ。実体は s4lv/pro/）
│   └── mbticode/
│       ├── rules/         ← 文体・戦略・KPI・販売分析 12本
│       ├── examples_sns.md ← SNS投稿見本バンク（Good/Bad対比・生成前に読む）
│       ├── reference/     ← MBTI/DSKB/ラブタイプ診断データ（捏造防止の一次情報）
│       ├── articles/ posts/ ← 成果物（published/ が出力見本）
│       └── mbticode_tasks.md ← タスク管理（「タスクを確認」はこれをReadする）
└── Junk314/junk_juice/    ← クライアント案件（60代推し活エッセイ）
    ├── CLAUDE.md / profile.md
    ├── rules/             ← SEO見出し・有料記事品質基準 3本
    ├── examples_essay.md  ← バズ記事②解剖の見本バンク（生成前に読む）
    └── articles/          ← published/article_02_20260614.md がバズ見本（いいね155）
```

## 運用原則（全AI共通）

1. **唯一の正**: 同じ情報が複数箇所にある場合、`rules/`・`rewrite_common_rules.md`・各コマンドファイルの記載を正とする。2026-07-06以降、ルールの編集は**repo内のファイルのみ**に行う（旧マスターの `~\.claude\commands\` は `~\.claude\commands_backup_20260706\` へ退避済み。Claude Codeメモリも旧マスターであり編集禁止。**万一スラッシュコマンドが動かない場合はバックアップから復元**: `Copy-Item "$env:USERPROFILE\.claude\commands_backup_20260706\*.md" "$env:USERPROFILE\.claude\commands\"`）
2. **捏造禁止**: 実体験・実績・診断データは `personal_data.md`／`reference/` にあるものだけを使う
3. **完了条件ファースト**: 着手前に各SOP冒頭の完了条件を確認し、満たすまで完了報告しない
4. **QAを飛ばさない**: 機械検品（ERROR 0件必須）→LLMチェックの2段構え。shira_noteは `tools/qa_draft.py`、SNS投稿は `brands/tools/qa_post.py`＋`/post-review`、Note記事は `brands/tools/qa_article.py`＋`/quality-guardrail` を通してから確定する
4b. **見本バンクを先に読む**: 投稿・記事の生成前に各アカウントの `examples_*.md`（Good/Bad対比）を読む。タイトルは `docs/rubrics/title_scoring.md` の配点表で採点してから提示する
5. **生成しっぱなし禁止**: 成果物は必ず規定の保存先（各SOPに記載）へ保存する

## Claude Code以外のAIで使う場合

- スラッシュコマンド（`/xxx`）が使えない環境では、`.claude/commands/xxx.md` を開いて内容をそのまま指示文として貼り付ける（コマンドファイル＝指示テンプレート）
- Claude Codeのメモリ機能に相当する知識はすべて各 `rules/` フォルダに置いてあるため、メモリなしでも本README経由で到達できる
