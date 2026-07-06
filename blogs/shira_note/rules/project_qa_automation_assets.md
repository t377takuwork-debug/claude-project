---
name: project-qa-automation-assets
description: 2026-07-03作成の業務自動化資産3点（draft検品スクリプト・post-reviewコマンド・番組差分監視）の場所と使い方
metadata: 
  node_type: memory
  type: project
  originSessionId: acd957ad-2091-40e6-ad75-1d1b4b73d2b9
---

2026-07-03の業務改善セッションで作成した自動化資産。

## 1. draft検品スクリプト（shira_note）
- `blogs/shira_note/tools/qa_draft.py` — スマートクォート/禁止ワード/WPブロック開閉/ショートコード混在/JSON-LDパース/メタ⇔JSON-LD同期/AFリンク仕様/ul style/カテゴリURL/リード文日付/締め文主観形容詞（語幹マッチ・「な」なしも検出）を機械チェック。`--fix`でスマートクォート自動修正
- **WARNベースライン方式（2026-07-05改修）**：`tools/output/qa_baseline.json` の既知WARN（指紋＋件数）を超えた分を[新規]と分類。**ERROR または 新規WARN 有りで終了コード1**（完了条件＝ERROR 0件・新規WARN 0件）。`--update-baseline` はユーザー承認時のみ実行可。初期ベースラインは既存13件（cdtv3・ongakunohi1・star2・teretou6・utadeaetara1）を登録済み
- 起動: `/shira-qa {ファイル名}`（`.claude/commands/shira-qa.md`）
- **全リライトコマンドの最終ステップとしてERROR 0件確認が運用ルール**（[[feedback-rewrite-smart-quotes]] [[feedback-shira-rewrite-banned-words]] [[feedback-rakuten-af-link-rules]] 等を機械化したもの）

## 2. /post-review コマンド（SNS投稿壁打ち）
- repo内 `.claude/commands/post-review.md` — [[feedback_s4lv_x_post_workflow]] が参照していたが実体が存在しなかったスキルを新規作成
- s4lv X/Threads・MBTICODEリプライの事実→構造→文体→投稿群全体の4段チェック＋100点採点
- 投稿生成→/post-review→修正→提案の順番を守る

## 3. 番組情報 差分監視（shira_note）
- `blogs/shira_note/tools/watch_programs.py` — bangumi.orgを今日〜N日先(既定7日)スキャンし、スナップショット(`tools/output/snapshots/`)と比較して新規特番・時間変更・消失を`tools/output/watch_report.md`に出力
- 依頼: 「番組監視して」。1日1回朝実行の運用
