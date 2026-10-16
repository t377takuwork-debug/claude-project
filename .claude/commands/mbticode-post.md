# MBTICODE X・Threads 投稿バッチ生成

MBTICODE（@MBTICODE）のX・Threads投稿を生成する。

**手順・本数・時間帯・チェック項目の唯一の正は `brands/mbticode/sns_post_cheatsheet.md`**（本ファイルには手順や数値を重複記載しない）。文体の決まりの唯一の正は `brands/mbticode/rules/style_0930.md`。

**完了の条件**：検品（`publish_batch.py`）でERROR 0件／確認役（`mbticode-post-reviewer`）の指摘を直した／外部の投稿を参考にした項目は類似チェック（`check_similarity.py`）を通した／投稿の全文を、根拠の表と注意点つきでオーナーに見せた／オーナーOKのあとにシートへ投入し、読み戻しが一致した。

---

## 実行前に読むもの（この順）

1. `brands/mbticode/sns_post_cheatsheet.md` — 生成ワークフロー（Step 1〜6）
2. `brands/mbticode/rules/style_0930.md` — 文体の決まり（オーナーの指摘を含む）
3. `brands/mbticode/persona_core.md` — ペルソナ。`brands/mbticode/personal_data.md` は、**体験を匂わせるときだけ**読む（実体験と誤認させる書き方はしない）
4. `brands/mbticode/analysis/neta/neta_ledger.md` の「**ネタ在庫**」（状態が「未使用」のもの）— 投稿のネタはここから選ぶ。悩み・タイプ・資料の根拠は同じ番号の `neta_stock_candidates_*.md` にある
5. **タイプの行動を書くときは、書く前に `brands/mbticode/reference/MBTI各タイプ傾向まとめ.txt`（詳細版）の該当タイプの節を読む。** 簡易版（`mbti_quick_ref.md`）だけで行動を書かない。ラブタイプは `lovetype_sns_ref.txt`、流行語は `trend_words_bank.md`
6. `brands/mbticode/analysis/patterns.md`（反響のパターン候補）と `analysis/log.md` の直近1件 — 案ごとに「どのパターンに沿うか／新しく試すか」を1行添える
7. `brands/mbticode/posts/cta_templates.md` — URL誘導を付ける投稿だけ。誘導文は平たい文（`style_0930.md` の7）

**読まないもの**：`analysis/neta/neta_sources.md`（外部投稿の記録。文言を見ながら書かない）。外部の型は `analysis/neta/formats_external.md`（形の発想の参考だけ・使うときは類似チェック）。

条件付き：`brands/mbticode/reference/threads_engagement_rubric.md`（オーナーが「評価して」「点数をつけて」と明示したときだけ）／`brands/mbticode_strategy.md`（戦略背景が要る判断のときだけ）。

---

## 実行

読み込んだあと、`sns_post_cheatsheet.md` の「生成ワークフロー」に従って実行する。検品（`publish_batch.py`・`qa_post.py`）・確認役・類似チェック・シートへの投入・報告まで、すべてワークフロー側に定義済み。
