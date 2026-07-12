# 業務棚卸し表（STEP 1成果物）

作成日: 2026-07-06 ／ 目的: 全業務と資産の対応を1枚で俯瞰する。新しいAI・新しいセッションはまずこの表で「どの業務か」を特定し、エントリポイント列のファイルだけを開く。

---

## 頻度別・業務一覧

### 日次（毎日 or ほぼ毎日）

| # | 業務 | エントリポイント | 完了条件 | QA・検品 |
|---|---|---|---|---|
| D1 | MBTICODE X・Threads投稿バッチ生成 | `/mbticode-post`（`.claude/commands/mbticode-post.md`） | `brands/mbticode/posts/posts_x.txt`・`posts_threads.txt` に上書き保存済み＋`qa_post.py` ERROR 0件 | `brands/tools/qa_post.py`（機械）→`/post-review`（LLM） |
| D2 | MBTICODE リプライ・引用RT生成 | `/reply`（`.claude/commands/reply.md`） | 投稿分析→反映メモ→本文の3ブロック出力 | 文体ルール: `brands/mbticode/rules/feedback_mbticode_reply_style.md` |
| D3 | shira_note ネタ収集 | 「ネタ収集して」→ `python tools/collect_news.py` | `tools/output/programs.md`・`releases.md` 更新 | －（収集のみ） |
| D4 | shira_note 番組差分監視 | 「番組監視して」→ `python tools/watch_programs.py` | `tools/output/watch_report.md` 更新 | －（監視のみ） |

### 放送日ドリブン（番組放送の前後）

| # | 業務 | エントリポイント | 完了条件 | QA・検品 |
|---|---|---|---|---|
| B1 | shira_note 番組タイムテーブルリライト | 番組別コマンド（`blogs/shira_note/CLAUDE.md` の一覧表） | **`/shira-qa` ERROR 0件・新規WARN 0件（終了コード0）** | `python tools/qa_draft.py`（機械検品） |

### 週次

| # | 業務 | エントリポイント | 完了条件 | QA・検品 |
|---|---|---|---|---|
| W1 | MBTICODE KPI記録 | `/kpi-weekly`（数値はユーザーがテンプレ形式等で渡す） | `brands/mbticode/kpi_log.md` へ追記＋前週比3点コメント | 数値の捏造・補間禁止 |

### 不定期（依頼・判断ドリブン）

| # | 業務 | エントリポイント | 完了条件 | QA・検品 |
|---|---|---|---|---|
| I1 | MBTICODE Note記事生成 | `/note-article mbticode [テーマ]` | `brands/mbticode/articles/drafts/` へ保存済み＋`qa_article.py` ERROR 0件 | `brands/tools/qa_article.py`（機械）→`/quality-guardrail`（LLM） |
| I2 | junk_juice テーマ・タイトル設計 | `/junk-theme` | テーマ・タイトル確定 | － |
| I3 | junk_juice 記事生成（クライアント） | `/junk-article` | `Junk314/junk_juice/articles/drafts/` へ保存済み | 有料記事は `Junk314/junk_juice/rules/feedback_junk_paid_article.md` のチェックリスト最低15項目 |
| I4 | s4lv Note記事・X/Threads投稿 | `brands/s4lv/rules/`（文体・プロセス一式） | X投稿は `/post-review` チェック済み | 反響設計図（`rules/feedback_s4lv_x_post.md`） |
| I5 | shira_note キーワード起点記事 | `/shira-keyword-article` | `/shira-qa` ERROR 0件 | qa_draft.py |
| I6 | shira_note 新規番組記事立ち上げ | `/shira-new-article` | 専用コマンド新設＋CLAUDE.md登録まで1セッション完結 | qa_draft.py |
| I7 | 戦略・方針判断 | `/notekaigi`（構造的判断は必ずここを経由） | 4ステップ出力フォーマット完了 | － |
| I8 | ASP記事設計 | `/asp-kaigi` → `/asp-theme` → `/asp-outline` の順に連結 | 各スキルの出力フォーマット完了 | － |
| I9 | ブログ戦略・記事CV改善 | `/blog-kaigi`（戦略）／`/monetize-kaigi`（CV改善） | 5名合議の出力完了 | － |
| I10 | バズ投稿分析 | `/buzz-analysis`（収集はユーザー手動・自動取得はX/Threadsで機能せず見送り済み） | 4部構成の分析出力（投稿別分析表〜資産反映提案） | 固定フレームワーク6観点 |
| I11 | cf_room 記事新規作成・リライト | 新規は `/cf-article`／リライトは `blogs/cf_room/CLAUDE.md`（工程地図: `rules/article_pipeline.md`） | drafts/保存＋`qa_draft.ps1` ERROR 0件＋rewrite_log追記 | `blogs/cf_room/tools/qa_draft.ps1`（機械） |
| I12 | vtuber_log 記事新規作成・リライト | 新規は `/vtuber-article`／リライトは `blogs/vtuber_log/CLAUDE.md`（工程地図: `rules/article_pipeline.md`） | drafts/保存＋`qa_draft.ps1` ERROR 0件＋rewrite_log追記 | `blogs/vtuber_log/tools/qa_draft.ps1`（機械） |

### 休眠・準備中

| # | 対象 | 状態 |
|---|---|---|
| S1 | `blogs/darepedia` | CLAUDE.mdは空ファイル（.claudeignoreで除外中）・skills空。稼働時は cf_room 構造（rules/＋tools/＋専用スキル＋機械QA）を横展開する |

※cf_room は2026-07-12に稼働開始（→I11）、vtuber_log は2026-07-12にcf_room構造を横展開して稼働開始（→I12）。

---

## 「察してやっていたこと」の所在（可視化結果）

2026-07-06の棚卸しで、以下の暗黙知はすべてファイル化済み・repo内に移設済みであることを確認した。

| 暗黙知 | 明文化ファイル（repo内） |
|---|---|
| s4lv X投稿の文体（フック3種・締め・口調・禁止事項） | `brands/s4lv/rules/feedback_s4lv_x_writing_style.md` |
| s4lv Threads投稿の文体（X投稿とは別OS） | `brands/s4lv/rules/feedback_s4lv_threads_writing_style.md` |
| s4lv Note記事生成プロセス（無料7ステップ・有料3フェーズ） | `brands/s4lv/rules/project_s4lv_note_article_process.md` |
| MBTICODEリプライの句読点・語尾・「わかります」使用条件 | `brands/mbticode/rules/feedback_mbticode_reply_style.md` |
| 番組別リライトの落とし穴（CDTV日付更新漏れ・テレ東2枚カード構造・FNS締め文） | `blogs/shira_note/rules/feedback_cdtv_rewrite_checklist.md` ほか同フォルダ |
| junk_juice 有料記事の品質基準（情景フック・情報密度・15項目チェック） | `Junk314/junk_juice/rules/feedback_junk_paid_article.md` |
| 「タスクを確認」＝mbticode_tasks.mdをReadする等の作業習慣 | `docs/rules/feedback_task_check.md`・`feedback_notekaigi_timing.md` |

## 要確認事項（推定が混ざっている箇所）

- ~~MBTICODE X投稿の本数の不一致~~ → **解消済み（2026-07-06ユーザー確認）**: 現行は1日3本・各週21本。最新値は `brands/mbticode/sns_post_cheatsheet.md` が唯一の正（再判断日: 2026-07-19）。
- ~~頻度分類は推定~~ → **確定済み（2026-07-06ユーザー確認）**: 日次・週次の分類はこの表の通りで正しい。
