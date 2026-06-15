# brands プロジェクト

s4lv（ブログ/SNS）とMBTICODE（Note/SNS）の複数アカウントを管理するコンテンツ運用プロジェクト。

---

## 管理アカウント

| アカウント | 媒体 | 目的 |
|---|---|---|
| s4lv_ai | Note・X・Threads | AI×ブログ設計の実戦記録 |
| s4lv_pro | X | ブログ設計の思想・戦略 |
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
| s4lv_ai 作業 | `s4lv/ai/profile.md`（X投稿生成時は `reference/x_algorithm_2026.md` も参照） |
| s4lv_pro 作業 | `s4lv/pro/profile.md`（X投稿生成時は `reference/x_algorithm_2026.md` も参照） |

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
| `/mbticode-post` | MBTICODE X・Threads投稿を週9本バッチ生成（必須ファイルの参照順序を保証） | MBTICODEの投稿バッチを作るたびに |
| `/reply` | 他者投稿へのリプライ・引用ポスト生成（投稿分析→反映メモ→本文の3ブロック出力） | リプライ・引用ポストを作るたびに |
| `/note-article [アカウント] [テーマ]` | Note記事をペルソナ→SEO確認→タイトル→構成→本文→drafts保存まで一貫生成 | 記事を作るたびに |
| `/notekaigi` | 戦略的意思決定の会議 | 新規戦略・方針転換・想定外のテーマが来たとき |
| `/asp-kaigi` | ASP案件・収益化戦略会議 | ASP案件の選定・戦略を決めるとき |
| `/asp-outline` | ASP記事タイトル・構成設計 | ASP記事の設計時 |
| `/asp-theme` | ASP案件・記事テーマ戦略 | ASPのテーマ選定時 |
