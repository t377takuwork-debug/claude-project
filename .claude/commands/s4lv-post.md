# s4lv X・Threads 投稿バッチ生成

s4lv統一アカウント（X @cfrms4lv／Threads @s4lv24）の投稿を生成する。

**2026-07-08 1アカウント統一後の体制**：X 1日2本・Threads 1日1本。コンテンツ2本柱（型・思想6割／AI実働4割）の最新定義は `brands/s4lv/rules/project_s4lv_accounts.md` を参照（本ファイルには重複記載しない）。

---

## 必須：実行前に読み込むファイル（この順序で必ず全て読む）

### 共通（X・Threadsとも）

1. `brands/s4lv/rules/project_s4lv_accounts.md` — 統一アイデンティティ原則・2本柱・確定プロフィール
2. `brands/s4lv/shared/personal_data.md` — 実績データ・開示ルール（**使用可能な数値の唯一の源。捏造禁止**）

### X投稿を含む場合

3. `brands/s4lv/rules/feedback_s4lv_x_writing_style.md` — X投稿文体OS（フック・本文・締め・禁止事項）
4. `brands/s4lv/rules/feedback_s4lv_x_post.md` — 精度ルール・反響別の確定構造（96〜99点基準）・素材の使用可否
5. `brands/s4lv/examples_x_posts.md` — Good/Bad見本バンク（生成前に必ず読む）
6. `brands/reference/x_algorithm_2026.md` — Xアルゴリズム資料

### Threads投稿を含む場合

7. `brands/s4lv/rules/feedback_s4lv_threads_writing_style.md` — Threads文体OS（X OSの持ち込み禁止・余韻・絵文字は😅✋のみ）

---

## 実行ワークフロー

1. **Step 1：事前設計テーブルの提示**
   投稿ごとに「柱（型・思想／AI実働）・狙う反響（ブックマーク／いいねRP／リプライ）・使用素材」をテーブルでチャットに出力し、ユーザーの確認を取る。**狙う反響を決めずに書き始めることは絶対禁止**。

2. **Step 2：群全体チェック**（同日・同バッチ内）
   - 170万PVの言及は1回以内か
   - Note誘導は1本以内か（URLは本文に入れずリプライ欄）
   - 複数投稿が同じトーン・フックになっていないか
   - 週単位で2本柱の比率（6:4）から大きく外れていないか
   - AI（Claude Code等）の話は**進行形表現のみ**（「再現する過程」「テスト運用中」）。完了形の実績断定は禁止

3. **Step 3：本文生成**
   ユーザーOK後に生成。X・Threadsで文体OSを切り替える（Threadsに X の硬さを持ち込まない）。

4. **Step 4：機械検品（必須）**
   `C:\Users\PC_User\AppData\Local\Python\bin\python.exe brands/tools/qa_post.py <postsファイル> --account s4lv --platform <x|threads>`
   **ERROR 0件が次工程への条件**。結果はユーザーに提示する。

5. **Step 5：/post-review 壁打ち（必須・スキップ禁止）**
   `rules/feedback_s4lv_x_post_workflow.md` の確定工程。生成 → `/post-review` → 修正 → 提案の順番を守り、スキルを通さず直接出力しない。

6. **Step 6：保存と報告**
   通過した投稿を `brands/s4lv/posts/posts_x.txt` / `brands/s4lv/posts/posts_threads.txt` に保存する（毎回上書き・コピペ即使用）。完了を1行で報告する（検証の証拠＝QA結果を添える）。
