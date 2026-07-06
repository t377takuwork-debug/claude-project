# SOP: Note記事生成（MBTICODE／s4lv）

対象AI: すべてのモデル。実体験・実績数値は各アカウントの `personal_data.md` にあるものだけを使う（捏造禁止）。

## 完了条件

本文が該当アカウントの `articles/drafts/` へ保存済みであること。**チャット出力だけで終わらせること（生成しっぱなし）を禁止**（`brands/mbticode/rules/feedback_note_article_draft_save.md`）。

## 手順（MBTICODE）

1. `/note-article mbticode [テーマ]` を起動する（ペルソナ→SEO確認→タイトル→構成→本文→drafts保存まで一貫）
2. タイトルには感情系検索語句を組み込み、`docs/rubrics/title_scoring.md` の配点表で採点してから提示する（`brands/mbticode/rules/project_mbticode_note_title_seo.md`。Step 2.5のキーワード確認は必須）
2b. 保存後に機械検品: `python brands/tools/qa_article.py "<draftパス>"`（有料記事は `--paid`）→ **ERROR 0件必須**
3. テーマの優先順位は `brands/mbticode/rules/project_mbticode_article_themes.md` に従う
4. 保存先: `brands/mbticode/articles/drafts/`
5. `/quality-guardrail` でAIっぽさを添削する

## 手順（s4lv）

1. プロセス定義: `brands/s4lv/rules/project_s4lv_note_article_process.md`（無料記事7ステップ・有料記事3フェーズ・タイトル95点基準・公開日プロモ導線）
2. プロフィール・実績: `brands/s4lv/shared/personal_data.md`＋アカウント別 `profile.md`
3. ライティング原則: `brands/writing/writing_core.md` を起点に4ファイル

## 必ず守るルール

- ペルソナ定義は性別・年齢を作らない。心理×購買感情の3軸のみ（`brands/mbticode/rules/project_mbticode_persona_core.md`）
- Note規約: 性的描写・断定的統計・特定個人を傷つける表現は禁止（`brands/CLAUDE.md`）
- 有料記事の販売判断・CTA設計の現行方針: `brands/mbticode/rules/project_mbticode_no_new_sales_process_0705.md`

## 出力見本

- 無料記事: `brands/mbticode/articles/published/01_【無料】既読スルーの理由、MBTIだけ調べてた人に言いたいことがある.md`
- 有料記事（実際に売れた記事）: `brands/mbticode/articles/published/02_【有料】MBTI×ラブタイプで導く、既読スルーを覆す返信の方程式.md`（行動テンプレート型が購買要因という分析: `rules/project_mbticode_paid_article_sales_factor.md`）
