# MBTICODE X・Threads 投稿バッチ生成

MBTICODE（@MBTICODE）のX・Threads投稿を生成する。

**2026-07-05 notekaigi更新**：X・Threadsとも本文投稿は1日3本（各週21本）。頻度・FW比率の最新値は`sns_post_cheatsheet.md`の基本設定を参照（本ファイルには数値を重複記載しない）。

---

## 必須：実行前に読み込むファイル（この順序で必ず全て読む）

1. `brands/mbticode/personal_data.md` — 実体験データ・開示ルール・コンテンツ変換ルール
2. `brands/mbticode/persona_core.md` — ペルソナ定義（行動トリガー／課金感情状態／期待値）
3. `brands/mbticode_strategy.md` — 戦略・FW使い分け・フェーズ・フラッグシップ記事情報
4. `brands/mbticode/sns_post_cheatsheet.md` — アルゴリズム対応ルール・生成ワークフロー・チェックリスト・X/Threads専用ルール一式
5. `brands/mbticode/posts/cta_templates.md` — 記事別CTAライブラリ（URL事後型・新規記事公開日の自己リプライを割り当てる投稿がある場合のみ参照）

---

## 実行

上記ファイルを読み込んだ後、`sns_post_cheatsheet.md` の「生成ワークフロー」に従って実行する。

### ワークフロー概要

1. **Step 1**：タイプ参照ファイルを確認する（タイプ言及がある投稿がある場合のみ）
2. **Step 2**：その日（またはそのバッチ対象期間）分のX投稿・Threads事前設計テーブルをチャットに出力してユーザーの確認を取る
3. **Step 3**：ユーザーOK後 → 対象分の本文を内部生成する
4. **Step 4（必須）**：保存前に `/quality-guardrail` を全投稿に通す。「AIっぽい薄い表現」（〜ですね／〜と思います／〜しましょう／〜が重要です等）を検出・添削し、検出0件を確認してから次に進む。**1日3本以上を同時生成する場合はStep2.5（同日投稿間の角度重複チェック）も必ず実行する**。発信前チェックリスト（cheatsheet側）とquality-guardrailは両方通過が必須で、どちらか一方の省略は不可
5. **Step 5**：発信前チェックリストとquality-guardrailを両方通過した投稿を `posts_threads.txt` / `posts_x.txt` に保存する（Threads本文はチャット出力しない）。完了を1行で報告する

タイプファイルの参照先・発信前チェックリスト・X/Threads専用ルールはチートシート内に記載済み。

### CTA割り当て（URL事後型・自己リプライ）

投稿がURL事後型（高インプ翌日ルール発動）または新規記事公開日にあたる場合：

1. `cta_templates.md` で該当記事のセクションを確認する
2. 3パターンが揃っていれば、本文の温度（共感寄り／実益寄り／勢いがある）に合うものを1つ選ぶ。同じ記事のCTAを前回と同じパターンで連続させない
3. 該当記事のセクションが未作成（`(未作成)`）の場合は、その場で3パターンを新規作成し `cta_templates.md` に追記してから使う。CTAをチャット上だけで作って保存し忘れない
4. 選んだCTAをそのまま自己リプライとして `posts_x.txt` / `posts_threads.txt` に本文とセットで保存する
