# s4lv X・Threads 投稿バッチ生成

s4lv統一アカウント（X @cfrms4lv／Threads @cfrms4lv）の投稿を生成する。旧Threads @s4lv24は運用終了・vivant用に転用済み（`brands/s4lv/rules/project_s4lv_accounts.md`「旧アカウント」参照）。

**体制**：X 1日2本（手動運用）・Threads 1日3本（07:30/12:00/21:30・自動投稿キュー運用。2026-08-21確定、詳細は `brands/s4lv/tools/threads_setup_guide.md`「開始前の決定事項」）。コンテンツ2本柱（型・思想6割／AI実働4割）の最新定義は `brands/s4lv/rules/project_s4lv_accounts.md` を参照（本ファイルには重複記載しない）。

---

## 必須：実行前に読み込むファイル（この順序で必ず全て読む）

### 共通（X・Threadsとも）

1. `brands/s4lv/rules/project_s4lv_accounts.md` — 統一アイデンティティ原則・2本柱・確定プロフィール
2. `brands/s4lv/shared/personal_data.md` — 実績データ・開示ルール（**使用可能な数値の唯一の源。捏造禁止**）
3. `brands/s4lv/rules/project_s4lv_persona.md` — 対象読者のペルソナ定義（2026-08-23新設。行動トリガー・課金する瞬間の感情・期待値の3軸。フック設計・CTA設計の判断基準）

### X投稿を含む場合

4. `brands/s4lv/rules/feedback_s4lv_x_writing_style.md` — X投稿文体OS（フック・本文・締め・禁止事項）
5. `brands/s4lv/rules/feedback_s4lv_x_post.md` — 精度ルール・反響別の確定構造（96〜99点基準）・素材の使用可否
6. `brands/s4lv/examples_x_posts.md` — Good/Bad見本バンク（生成前に必ず読む）
7. `brands/reference/x_algorithm_2026.md` — Xアルゴリズム資料

### Threads投稿を含む場合

4. `brands/s4lv/rules/feedback_s4lv_threads_writing_style.md` — Threads文体OS（2026-08-23全面改訂。わかりやすさ最優先・AI感排除・数字使用可・箇条書き標準装備・親しみやすさ重視。改訂経緯はファイル末尾「改訂履歴」参照）
5. `brands/s4lv/articles/note_article_index.md` — Note記事インデックス（型・思想柱の小出しネタ元・誘導ローテーションの唯一の正）
6. `brands/reference/threads_algorithm_2026.md` — Threadsアルゴリズム資料（会話速度モデル・著者返信の重要性・エンゲージメントベイトのペナルティ）

条件付き参照（該当する場合のみ）：
- 市場動向・競合の反響投稿など、repo内に情報がない/古い可能性がある論点を扱う場合 → WebSearch/WebFetchで裏取りする（2026-08-23、Xアルゴリズムの数値相違をこの方法で検証した実績あり。複数ソースで矛盾する場合は不採用にせず、両論併記でユーザーに判断を仰ぐ）

---

## 実行ワークフロー

1. **Step 1：事前設計テーブルの提示**
   投稿ごとに「柱（型・思想／AI実働）・狙う反響（ブックマーク／いいねRP／リプライ）・使用素材・Note誘導有無（誘導先記事）」をテーブルでチャットに出力し、ユーザーの確認を取る。**狙う反響を決めずに書き始めることは絶対禁止**。
   - Threadsの型・思想枠は`note_article_index.md`の「適合判定＝合う」記事を優先してネタを起こす（小出し設計。CTAなしのテーマ借用が基本）
   - Note誘導CTA（自己リプライ欄）は週3本中1本を目安に、`note_article_index.md`の「直近Threads誘導日」が空欄または最古の記事を選ぶ

2. **Step 2：群全体チェック**（同日・同バッチ内）
   - 170万PVの言及は1回以内か
   - Note誘導は1本以内か（URLは本文に入れずリプライ欄）
   - 複数投稿が同じトーン・フックになっていないか
   - 週単位で2本柱の比率（6:4）から大きく外れていないか
   - AI（Claude Code等）の話は**進行形表現のみ**（「再現する過程」「テスト運用中」）。完了形の実績断定は禁止

3. **Step 3：本文生成**
   ユーザーOK後に生成。X・Threadsで文体OSを切り替える（Threadsに X の硬さを持ち込まない）。Threadsは`feedback_s4lv_threads_writing_style.md`「反響を生む型」（フック・箇条書き・障壁除去・想定反論・CTA）を適用する。

3.5. **Step 3.5：自己レビュー（Threads・必須）**
   生成後、保存前に以下を自分で確認する（2026-08-23、実際の生成で見落としが発覚し追加）：
   - フックで提示した悩み・状況と、本文の中身・締めが同じ話を指しているか（新規参入基準↔既存記事の悩み、のような時間軸のすり替えがないか）
   - `project_s4lv_persona.md`の3軸のどれかに刺さる内容になっているか
   - 箇条書き化できる主張を文章で流し込んでいないか
   - 否定から入るフック（「違います」等）になっていないか
   問題が見つかったら、Step 4のqa_post.py実行前に直す。

4. **Step 4：機械検品（必須）**
   `C:\Users\PC_User\AppData\Local\Python\bin\python.exe brands/tools/qa_post.py <postsファイル> --account s4lv --platform <x|threads>`
   **ERROR 0件が次工程への条件**。結果はユーザーに提示する。

5. **Step 5：/post-review 壁打ち（必須・スキップ禁止）**
   `rules/feedback_s4lv_x_post_workflow.md` の確定工程。生成 → `/post-review` → 修正 → 提案の順番を守り、スキルを通さず直接出力しない。**`/post-review`がスキルとして未登録の場合**（2026-08-23に発生実績あり）、`.claude/commands/post-review.md`を直接読み込み、その採点基準（事実→構造→文体→投稿群全体・90点未満は修正案併記）に沿って自分で壁打ちを行う。省略しない。

6. **Step 6：保存**
   - X：通過した投稿を `brands/s4lv/posts/posts_x.txt` に保存する（毎回上書き・コピペ即使用。自動化対象外のため履歴管理不要）。
   - Threads：通過した投稿を `brands/s4lv/posts/posts_threads.txt` の末尾へ**追記**する（上書き禁止）。7日より古い投稿分が残っていれば `brands/s4lv/posts/archive/` へローテーション移動する。

7. **Step 7：Threads自動投稿キューへの転送**（Threads投稿を含む場合のみ）
   保存したThreads投稿からCSV（列：`投稿日時,本文,リプライ1,リプライ2,リプライ3,リプライ4,型,FW`。リプライ2〜4は連続スレッド使用時のみ・省略可。投稿日時は `YYYY-MM-DD HH:MM`。トリガー時刻＝07:30/12:00/21:30のいずれかに揃える）を作成し、
   `python brands/s4lv/tools/push_threads_queue.py <csv>` でスプレッドシートのキューへ投入する（過去時刻・重複は自動スキップ）。

8. **Step 8：完了報告**
   保存先パス・QA結果・キュー投入結果を1〜3行で報告する（検証の証拠を添える。実行していないものを「できたはず」と書かない）。
