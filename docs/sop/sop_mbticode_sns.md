# SOP: MBTICODE X・Threads投稿／ネタ／分析／リプライ

対象AI: すべてのモデル。**投稿生成の手順の唯一の正は `brands/mbticode/sns_post_cheatsheet.md`（生成ワークフロー Step 1〜6）、文体の唯一の正は `brands/mbticode/rules/style_0930.md`。ここに手順を重複記載しない。**

## 全体の流れ（2026-10-17整理）

| 工程 | 何をする | いつ・誰が | 手順の正 |
|---|---|---|---|
| 1. 収集 | X・スレッズの反響の大きい恋愛・MBTI投稿を自動で溜める（トークン0） | 毎日・自動 | `docs/sop/sop_research_auto_collect.md` |
| 2. ネタの補充 | 候補ファイルから、ネタ候補を作る。OKされた分だけ台帳の「ネタ在庫」へ（目標：未使用30件） | 2週間に1回・予約実行 `mbticode-neta-refill`（毎月1日・15日）／「リサーチして」と言ったとき | `.claude/commands/mbticode-neta.md` |
| 3. 投稿の生成 | 在庫のネタから、1日3本（08・16・22）を作る → 検品 → 確認役 → 類似チェック → オーナーに全文を見せる → OKのあとシートへ投入 | 次のバッチが要るとき（キューの残り日数で判断） | `/mbticode-post` → チートシート |
| 4. 分析 | 自分の投稿の数字を診断し、次の変更を決める。OKされた分だけ `log.md` に記録 | オーナーが「分析して」と言ったときだけ | `.claude/commands/mbticode-analysis.md` |
| 5. リプライ・引用RT | 他者投稿へのリプライ、引用ポスト | 必要なとき | `/reply` |

## 完了条件

- 投稿バッチ：`publish_batch.py` でERROR 0件／確認役の指摘を直した／外部の投稿を参考にした項目は類似チェックを通した／全文をオーナーに見せてOKを取った／シートへ投入し、読み戻しが一致した（Threads）。Xは運用停止中（2026-08-18以降）
- ネタの補充：候補をオーナーに提示し、OKされた分を台帳に記録した
- リプライ：投稿分析→反映メモ→本文の3ブロック出力済み

## 手順

- 投稿バッチ：`/mbticode-post` を起動する（読む順番はコマンド側が保証する）。タイプの行動は、資料の**詳細版**を読んでから書く
- リプライ・引用RT：`/reply` を起動する。文体は `brands/mbticode/rules/feedback_mbticode_reply_style.md`
- 委譲：実行部隊 `post-writer` は、ネタIDを渡して下書きと検品までを任せる（確認役・類似チェック・オーナー確認・投入は司令塔）

## 必ず守るルール

- MBTI・DSKB・ラブタイプの内容は `brands/mbticode/reference/` のデータのみ使用（架空のタイプ論・自作の相性データは捏造にあたる）。資料にない行動は断定しない
- 投稿本数と時間帯の現行値は `brands/mbticode/sns_post_cheatsheet.md` の基本設定が唯一の正
- 出力の見本：Threadsは `py -3 brands/mbticode/tools/show_queue_recent.py --full`（直近のキュー）
- 誘導文（note）は平たい文。毎回は付けない（週1〜3本）
