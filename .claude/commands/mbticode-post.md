# MBTICODE X・Threads 投稿バッチ生成

MBTICODE（@MBTICODE）のX・Threads投稿を生成する。

頻度・FW比率・生成手順・チェックリストの**唯一の正は `brands/mbticode/sns_post_cheatsheet.md`**（本ファイルには数値・手順を重複記載しない）。

---

## 必須：実行前に読み込むファイル（この順序で必ず全て読む）

1. `brands/mbticode/personal_data.md` — 実体験データ・開示ルール・コンテンツ変換ルール
2. `brands/mbticode/persona_core.md` — ペルソナ定義（行動トリガー／課金感情状態／期待値）
3. `brands/mbticode/sns_post_cheatsheet.md` — 生成ワークフロー・チェックリスト・X/Threads専用ルール一式（唯一の正）
4. `brands/mbticode/examples_sns.md` — Good/Bad見本バンク（生成前に必ず読む）
5. `brands/mbticode/threads_insights_notes.md` — 直近の週次分析結論（一番上のエントリのみ。「まだ分析記録なし」なら無視してよい）

条件付き参照（該当する場合のみ）：
- `brands/mbticode/posts/cta_templates.md` — URL事後型・新規記事公開日のCTA割り当てがある場合。使い方・未作成時の新規作成ルールはファイル内冒頭を参照
- `brands/mbticode_strategy.md` — 戦略背景・フェーズ・フラッグシップ情報が必要な判断時のみ（通常バッチ生成では読まない）

---

## 実行

上記ファイルを読み込んだ後、`sns_post_cheatsheet.md` の「生成ワークフロー」（Step 1〜6）に従って実行する。手順・検品（qa_post.py／quality-guardrail／post-review）・保存・キュー転送・報告まで全てワークフロー側に定義済み。
