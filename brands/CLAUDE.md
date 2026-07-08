# brands プロジェクト

s4lv（ブログ/SNS）とMBTICODE（Note/SNS）の複数アカウントを管理するコンテンツ運用プロジェクト。

---

## 管理アカウント

| アカウント | 媒体 | 目的 |
|---|---|---|
| s4lv | Note・X・Threads | 10年の「設計の型」×AI実働記録（2026-07-08に1アカウント統一。旧s4lv_ai/s4lv_proは`s4lv/rules/project_s4lv_accounts.md`参照） |
| MBTICODE | Note・X・Threads | MBTI×ラブタイプ診断×有料記事マネタイズ |

---

## 絶対遵守ルール（全アカウント共通）

1. **捏造禁止**：コンテンツ作成時は各アカウントの `personal_data.md` を参照し、実体験に基づく内容のみ使用する（s4lv系→`s4lv/shared/personal_data.md`、MBTICODE→`mbticode/personal_data.md`）
2. **開示ルール**：各 `personal_data.md` の開示ルールテーブルを必ず確認する
3. **Note規約遵守**：性的描写・断定的統計・特定個人を傷つける表現は禁止
4. **一次情報の参照**：MBTICODEのコンテンツ生成時は `mbticode/reference/` フォルダを参照する（架空データ使用禁止）

---

## 詳細情報の参照先

### タスク別 参照ファイル（作業開始時にタスクに応じて読む）

| タスク | 必須参照ファイル |
|---|---|
| MBTICODE X・Threads投稿バッチ生成 | **`/mbticode-post` スキルを起動**（参照順序・ファイル一式を保証） |
| MBTICODE SNS リプライ・引用ポスト生成 | **`/reply` スキルを起動** |
| MBTICODE Note記事生成 | **`/note-article mbticode [テーマ]` スキルを起動**（ペルソナ→SEO確認→タイトル→構成→本文→保存まで一貫保証） |
| s4lv X・Threads投稿バッチ生成 | **`/s4lv-post` スキルを起動**（参照順序・QA・/post-review工程を保証） |
| s4lv Note記事・その他作業 | `s4lv/rules/project_s4lv_accounts.md` → `s4lv/rules/project_s4lv_operation_system.md`（Note記事プロセスは `s4lv/rules/project_s4lv_note_article_process.md`） |

`mbticode/mbticode_tasks.md` は全MBTICODE作業で参照する。

### 全アカウント共通リソース

| ファイル | 内容 |
|---|---|
| `reference/x_algorithm_2026.md` | Xアルゴリズム資料（全アカウント共通・ユーザーが手動更新） |

### プロジェクトファイル（必要時のみ参照）
| ファイル | 内容 |
|---|---|
| `s4lv/shared/personal_data.md` | s4lv共通プロフィール・実績データ・開示ルール |
| `s4lv/ai/personal_data.md` | s4lv_aiアカウント固有データ・ターゲット定義 |
| `mbticode/personal_data.md` | MBTICODE発信者実体験データ・開示ルール・コンテンツ変換ルール |
| `sns_reply_guideline.md` | 他者投稿へのリプライ・引用RT設計（Brands全アカウント共通＋アカウント別） |
| `mbticode/reference/dskb_quick_ref.md` | DSKB 16タイプ クイックリファレンス（通常投稿はこちらで対応） |
| `mbticode/reference/mbti_quick_ref.md` | MBTI タイプ クイックリファレンス（通常投稿はこちらで対応） |
| `mbticode/reference/lovetype_sns_ref.txt` | ラブタイプ SNS発信リファレンス簡易版（SNS投稿用・9タイプ・対比フック付き） |
| `mbticode/reference/` | MBTI・DSKB・ラブタイプ・Nighttypeの診断データ一式（詳細が必要な場合のみ） |
| `mbticode/posts/posts_x.txt` | MBTICODE X投稿ファイル（毎回上書き・コピペ即使用） |
| `mbticode/posts/posts_threads.txt` | MBTICODE Threads投稿ファイル・自己リプライ含む（毎回上書き・コピペ即使用） |

---

## 利用可能なスキル

| スキル | 用途 | 使うタイミング |
|---|---|---|
| `/mbticode-post` | MBTICODE X・Threads投稿のバッチ生成（1日3本・各週21本体制。最新値は `mbticode/sns_post_cheatsheet.md` が唯一の正） | MBTICODEの投稿バッチを作るたびに |
| `/s4lv-post` | s4lv X・Threads投稿のバッチ生成（X 1日2本・Threads 1日1本。2本柱の最新定義は `s4lv/rules/project_s4lv_accounts.md` が唯一の正） | s4lvの投稿バッチを作るたびに |
| `/reply` | 他者投稿へのリプライ・引用ポスト生成（投稿分析→反映メモ→本文の3ブロック出力） | リプライ・引用ポストを作るたびに |
| `/note-article [アカウント] [テーマ]` | Note記事をペルソナ→SEO確認→タイトル→構成→本文→drafts保存まで一貫生成 | 記事を作るたびに |
| `/notekaigi` | 戦略的意思決定の会議 | 新規戦略・方針転換・想定外のテーマが来たとき |
| `/asp-kaigi` | ASP案件・収益化戦略会議 | ASP案件の選定・戦略を決めるとき |
| `/asp-outline` | ASP記事タイトル・構成設計 | ASP記事の設計時 |
| `/asp-theme` | ASP案件・記事テーマ戦略 | ASPのテーマ選定時 |
| `/buzz-analysis` | バズ投稿の固定フレームワーク分析（型・発話モード・ブクマ動機） | ユーザーがバズ投稿を手動収集して渡したとき |
| `/kpi-weekly` | 週次KPIの記録＋前週比3点コメント（`mbticode/kpi_log.md` へ蓄積） | 週次の数値を渡されたとき |

## 機械検品・見本バンク（生成の前後で必ず使う）

| 資産 | 用途 |
|---|---|
| `brands/tools/qa_post.py` | SNS投稿の機械検品（ERROR 0件が保存条件）。`python brands/tools/qa_post.py <postsファイル>` |
| `brands/tools/qa_article.py` | Note記事の機械検品（ERROR 0件が保存条件）。有料記事は `--paid` |
| `mbticode/examples_sns.md` | MBTICODE投稿のGood/Bad見本（生成前に読む） |
| `s4lv/examples_x_posts.md` | s4lv X投稿のGood/Bad見本（生成前に読む） |
| `docs/rubrics/title_scoring.md` | タイトル配点表（採点してから提示・点数捏造禁止） |
