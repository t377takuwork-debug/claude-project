# MBTICODE X・Threads 投稿バッチ生成

MBTICODE（@MBTICODE）のX・Threads投稿を生成する。

頻度・FW比率・生成手順・チェックリストの**唯一の正は `brands/mbticode/sns_post_cheatsheet.md`**（本ファイルには数値・手順を重複記載しない）。

---

## 必須：実行前に読み込むファイル（この順序で必ず全て読む）

1. `brands/mbticode/personal_data.md` — 実体験データ・開示ルール・コンテンツ変換ルール
2. `brands/mbticode/persona_core.md` — ペルソナ定義（行動トリガー／課金感情状態／期待値）
3. `brands/mbticode/rules/style_0930.md` — 文体ルール（暫定版・問いかけ／読点／現実にありえる場面／1行目）。**生成の前に必ず読む**
3-2. `brands/mbticode/sns_post_cheatsheet.md` — 生成ワークフロー・内容の正確性チェック・X/Threads専用ルール一式（唯一の正）
   - Threadsは**スプレッドシートが正**（`posts_threads.txt` には追記しない。一時ファイルで検品してからシートへ投入する）
   - タイプの話をする投稿は、ワークフロー Step 1 に従い、書く前に `reference/` の該当資料を必ず読む

4. `brands/mbticode/analysis/patterns.md` — 反響が出やすい投稿のパターン候補（基礎分析）。**案を出すときの参考として読む**（確定ルールではなく、試す価値のある仮説。確度が低いものは1つずつ試す）。あわせて `analysis/log.md` に週次分析の記録があれば、直近の1件を読む

5. `brands/mbticode/analysis/neta/neta_ledger.md` の「**1. 自分のネタ**」（切り口に変換済み）のうち、状態が「未使用」のものを、案の参考にする。**`neta_sources.md`（外部投稿の記録）は読まない・案の材料にしない**（文言を見ながら書かない）。使ったネタは状態を「使用（日付・投稿の日時）」に更新し、あとで自分の投稿の結果（数字）を書き足す。**「自分のネタ」から作った投稿は、保存・投入の前に、類似チェック（型・テーマ・タイプのうち元ネタと一致するのは最大1つ＋着想の近さ＋`brands/tools/check_similarity.py`）を必ず行う。型を再現せず、反響を生んでいそうな「要素」を取り入れる**（手順は `/mbticode-neta` の「類似チェック」。元ネタの本文は、投稿IDからChromeで取得して一時ファイルに書く。リポジトリには保存しない）

6. `brands/mbticode/analysis/neta/formats_external.md` — 外部の型・パターン（収集した元ネタの形）。**案出しで、形の発想の参考にする**（他人のアカウントのデータで、自分では未検証の仮説。借りるのは構造まで。使うときは類似チェックを通す）

**再構築が終わるまで読まないもの（2026-09-29）**：`examples_sns.md`（旧文体の見本）は生成に使わない。テーマ・型の決め方も保留中のため、Step 2 でユーザーに案を出して決めてもらう。

条件付き参照（該当する場合のみ）：
- `brands/mbticode/posts/cta_templates.md` — URL事後型・新規記事公開日のCTA割り当てがある場合。使い方・未作成時の新規作成ルールはファイル内冒頭を参照
- `brands/mbticode_strategy.md` — 戦略背景・フェーズ・フラッグシップ情報が必要な判断時のみ（通常バッチ生成では読まない）
- `brands/mbticode/reference/threads_engagement_rubric.md` — ユーザーから「評価して」「85点以上にして」等の反響力チェックを明示的に求められた時のみ、この基準で自己採点する（通常バッチ生成では読まない）

---

## 実行

上記ファイルを読み込んだ後、`sns_post_cheatsheet.md` の「生成ワークフロー」（Step 1〜6）に従って実行する。手順・検品（qa_post.py／quality-guardrail／post-review）・保存・キュー転送・報告まで全てワークフロー側に定義済み。
