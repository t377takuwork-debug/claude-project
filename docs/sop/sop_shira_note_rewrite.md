# SOP: shira_note 番組タイムテーブルリライト

対象AI: すべてのモデル（賢さに依存しない）。このSOPの手順以外のことを推測で行わないこと。

## 完了条件（これを満たすまで完了報告禁止）

`python tools/qa_draft.py draft_XXXX.txt`（**作業ディレクトリ: `blogs/shira_note/` で実行**）が **ERROR 0件・新規WARN 0件（終了コード0）**。完了報告には必ずこのQA実行結果を貼ること。

## 事前に揃える入力（欠けていたら作業開始せず、ユーザーに要求する）

1. 資料①: 放送日・出演者・楽曲・見どころ（必須）
2. 資料②: 直前回のセットリスト確定データ（`blogs/shira_note/CLAUDE.md` の「資料② 入力テンプレート」形式のみ受理。形式外なら推測せず差し戻す）
3. アイキャッチ画像URL（JSON-LD用）

## 手順

1. `blogs/shira_note/rewrite_common_rules.md` を読む（禁止ワード・段落文体・WPブロック・AFリンクの**唯一の正**。読まずに書き始めることを禁止）
2. 番組に対応するスラッシュコマンドを起動する（対応表: `blogs/shira_note/CLAUDE.md` のコマンド一覧）。コマンドファイル内の手順・参照ファイル指定に従う
3. 番組別の落とし穴チェック: `blogs/shira_note/rules/` 内の該当番組ファイルを読む
   - CDTV → `feedback_cdtv_rewrite_checklist.md`（H2直下リード文の日付更新漏れに注意）
   - テレ東音楽祭 → `feedback_teretou_rewrite_structure.md`（前半/後半2枚カード構造）
   - FNS → `feedback_fns_rewrite_style.md`（締め文は1文のみ）
4. draftファイル（固定名・上書き運用）を編集する。必要なセクションのみReadする
5. `/shira-qa`（= `python tools/qa_draft.py draft_XXXX.txt`）を実行し、完了条件を確認する

## 必ず守るルール

- 禁止ワード・文体は `rewrite_common_rules.md` に従う。自分の判断で「良い表現」に言い換えない
- `--update-baseline` はユーザー承認時のみ実行する
- JSON-LDとメタ・本文FAQの同期はqa_draft.pyが検査する。手動で「たぶん合っている」と判断しない
- 出演者情報・放送日を推測で補完しない。資料①にないものは書かない（捏造禁止）

## 出力見本

- 完成形のdraft: `blogs/shira_note/draft_cdtv.txt`（最新の合格済みドラフト。構造・文体・WPブロックの実例として参照する）
- JSON-LD: `blogs/shira_note/template_jsonld_cdtv.txt` 等の番組別テンプレート

## 新規番組の場合

コマンド一覧に無い番組は `/shira-new-article` を起動する（構成確認→aria-label→専用コマンド新設→CLAUDE.md登録まで1セッションで完結）。
