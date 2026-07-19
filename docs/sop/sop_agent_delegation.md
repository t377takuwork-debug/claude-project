# SOP: エージェント委譲体制（Fable 5司令塔 × Sonnet 5実行部隊）

作成: 2026-07-19（パイロット2回合格を受けて確立）。体制の設計判断の経緯はメモリ `project-agent-rollout-0718`、実装は `.claude/agents/shira-rewriter.md`・`blogs/shira_note/rewrite_engine.md` を参照。

## 役割分離の原則（1行定義）

**機械QAが受入判定できるタスクはSonnetのエージェントに委譲し、判定できないタスク（戦略・設計・環境変更・新規立ち上げ・例外処理）はFable 5が直接実行する。**

| 役割 | 担当 | 具体例 |
|---|---|---|
| 司令塔（Fable 5） | 資料の整形・承認取得・委譲・受入判定・コミット・失敗パターンの昇格 | 資料②の尺チェック、git diff検分、rules/メモリ更新 |
| 実行部隊（Sonnet 5） | 手順書どおりの生成・編集・機械QA合格まで | 番組リライト（shira-rewriter）、今後: SNS投稿（post-writer） |

## 日常運用フロー（shira_noteリライト・確立済み）

1. **ユーザー → 司令塔**：番組名＋資料①②③＋アイキャッチを渡す（従来と同じ投げ方）
2. **司令塔・委譲前チェック**：①資料②をテンプレ形式へ整形 ②時間データと放送尺の整合（超過・欠落はAskUserQuestionで承認を取る）③通常回か特番か ④前回が特別回なら「通常回戻し」を委譲文に明記
3. **委譲**：shira-rewriterへ。資料一式＋番組名＋受入条件を渡す
4. **実行部隊**：共通ルール→エンジン→番組別ファイルの順に読み、Edit差分更新→`qa_draft.py` ERROR 0件・新規WARN 0件・exit=0まで完遂。判断が必要な例外は保留として報告に返す
5. **司令塔・受入判定**：git diff（変更が指示範囲に閉じているか・純増減の妥当性）＋QA再実行＋エージェントの事実主張の独立裏取り（例: YouTube最新動画IDはRSSを自分で再取得）→合格ならコミット
6. **失敗パターンの還流**：報告の「初回不合格ログ」「保留・提案」が空でなければ、rules/またはメモリへの昇格を必ず判定する

## 注意点（2回のパイロットで確定した運用知識）

- **エージェントタイプが未認識の場合**（作成セッション内等）：general-purpose＋`model: sonnet`に `.claude/agents/shira-rewriter.md` の定義全文を貼り込んで代替する。Write禁止は指示で代替し、受入時のgit diffで全置換がないことを検分する
- **「draftが既に最新」は正常系**：エージェントは化粧直しをせず検証＋実差分のみ返す（7/19に2回発生・いずれも正しい挙動）
- `--update-baseline` はユーザー承認事項。エージェントには実行禁止を明示済み
- `tools/output/` 配下の自動収集ファイルは毎朝更新される。受入コミットに混ぜない
- 本環境のBashツールは出力不達。エージェントへの委譲文に「PowerShellを使え」を毎回含める
- コミットは司令塔のみが行う（実行部隊はgit操作禁止）

## Phase 4設計案: post-writer（SNS投稿バッチの委譲）

**目的**：日次のMBTICODE/s4lv投稿バッチ生成（業務D1・I4）をSonnetへ委譲する。

| 設計項目 | 内容 |
|---|---|
| 定義ファイル | `.claude/agents/post-writer.md`（model: sonnet / effort: medium） |
| 読み順 | `brands/CLAUDE.md` → `/mbticode-post` または `/s4lv-post` コマンドファイル（参照順序・本数体制を内包済み）→ 見本バンク（`examples_sns.md` 等） |
| ツール | Read・Grep・Glob・**Write**・PowerShell（投稿ファイルは「毎回上書き」運用のためshira-rewriterと異なりWriteを付与。上書き対象は `brands/*/posts/posts_*.txt` のみと定義に明記） |
| 受入条件 | `python brands/tools/qa_post.py <postsファイル>` ERROR 0件。**exit code仕様は実装前に要確認（未検証）**——exit非対応なら出力全文貼付を受入条件にする |
| 司令塔の受入 | qa_post再実行＋`/post-review`（LLM冷徹チェック）は司令塔側で実施——機械QA=実行部隊・LLMレビュー=司令塔の2段構えを役割分離にそのまま写像 |
| 禁止事項 | shira-rewriterと同型（捏造禁止=personal_data.md/reference/外の実体験を書かない・git禁止・rules編集禁止・2回失敗で停止・初回不合格ログ報告） |
| パイロット | 次のMBTICODE投稿バッチ依頼1回。受入合格でs4lv-postにも適用 |

**実装済み（2026-07-19）**：`.claude/agents/post-writer.md`。実装時の実測で確定した仕様——①qa_post.pyはexit 0/1/2対応（ERROR 0件=0）②両コマンドの「ユーザーOK」工程は2段階運用（設計テーブル提示で停止→司令塔経由の承認→本文生成）に写像 ③CTAライブラリ追記のみEdit許可（`cta_templates.md`）。パイロット（次の投稿バッチ依頼1回）が未実施。

## 委譲プロンプト定型

**shira-rewriter（番組リライト）**

> shira-rewriterに委譲：{番組名} {M/DD}回のリライト（/{番組}-rewrite）。
> 資料①：{放送日・出演者・披露曲・見どころ・通常回/特番}
> 資料②：`## 資料② INPUT: {番組名} / {前回日付}` ＋テンプレ形式のセットリスト表（**司令塔が整形・尺チェック・承認取得済みであること**）
> 資料③：{あれば}／アイキャッチ：{URL または「既存URL維持」}
> {前回が特別回なら}前回は「{特別回名}」のため残存文言のGrep除去まで含む。
> 受入判定は司令塔が git diff＋qa_draft.py（ERROR 0・新規WARN 0・exit=0）で行う。報告はagent定義の形式で。

**post-writer（SNS投稿バッチ）**

> post-writerに委譲：{mbticode|s4lv} {対象日}分のX・Threads投稿バッチ（{本数}）を生成して。
> Phase Aの設計テーブルが上がったら私に見せること。承認後にPhase B（本文生成→qa_post.py→posts_*.txt保存）まで。
> 受入は司令塔が qa_post.py再実行＋git diff＋/quality-guardrail・/post-review で行う。

**エージェントタイプ未認識時の共通フォールバック**：general-purpose＋`model: sonnet` に `.claude/agents/{名前}.md` の定義全文を貼り込み、「コマンド実行はPowerShellを使え」を添える。

## ロードマップ・優先順位

| 期限 | タスク | 完了条件 |
|---|---|---|
| 今日中 | `/consolidate-memory` 第2回（前回7/7・目安超過中） | 削除/統合/保留の報告＋MEMORY.md整合 |
| 今日中 | 新セッション冒頭でネイティブshira-rewriter認識を確認 | エージェント一覧に表示される（表示されなければフォールバック継続） |
| 今週中 | ~~Phase 4実装~~（7/19完了）→ 次の投稿バッチ依頼でpost-writerパイロット | qa_post ERROR 0件で受入合格1回 |
| 今週中 | 次のリライト依頼番組をエンジン移行（パラメータ化） | 固有トークン照合で知識欠落0件＋1コミット |
| 今月中 | 残り10番組のエンジン移行完了 | 全番組ENGINE準拠宣言・共通変更のメンテ対象1ファイル化 |
| 今月中 | article-writer展開（qa_article.py受入・Note記事本文生成） | パイロット1本受入合格 |
| 今月中 | CLAUDE.mdの「effort手動切替表」を司令塔/実行部隊の役割表へ置換 | 本SOPへの参照1行に集約 |
| 今月中 | 会議系スキル4本（notekaigi・asp系3本）のFable 5最適化 | 全ラウンド出力強制→対立点と結論のみ出力へ |
