---
name: s4lv X投稿提案ワークフロー
description: X（およびThreads）投稿を提案する際は、生成後に sns-ai-reviewer の審査を通してPASSしてから出力する（2026-09-07に /post-review から差し替え）
type: feedback
originSessionId: 988f214a-40f2-4104-af52-f16a37db79b5
---
s4lv の X・Threads 投稿の提案をする際は、投稿案を生成した後にそのまま出力せず、必ず `sns-ai-reviewer`（審査部隊）の審査を通し、**PASS が出てから** ユーザーへ提案・保存すること。

**Why:** 壁打ち・ファクトチェックなしで出力した投稿に問題が発生した。当初は `/post-review`（100点採点の壁打ち）を工程にしていたが、その旧ルーブリックが旧文体（比喩・記憶のゆらぎ）へ引き戻す問題があり、2026-09-07の `/notekaigi` で専用審査エージェント `sns-ai-reviewer` へ差し替えた。詳細・設計は memory `project_s4lv_x_post_redesign_algo_research_0904`。

**How to apply:** X・Threads投稿の提案依頼を受けたとき、生成（`/s4lv-post` Step 3）→ 自己レビュー（Step 3.5）→ `qa_post.py`（Step 4）→ **`sns-ai-reviewer` 審査（Step 5・PASSまで）** → 保存（Step 6）、の順を守る。
- 審査基準は `docs/rubrics/sns_ai_tone_rubric.md`（「審査しないこと」＝文体の良し悪し・旧確定構造への適合・100点採点）。台帳 `brands/s4lv/x_neta_daicho.md` との根拠照合・開示・初心者可読性・名前つきAI臭さ・投稿群整合を見る
- FAIL → 指摘に沿って修正 → 2巡目。同じ指摘への修正は2巡まで。2巡後に残る FIX は現状・理由を添えてユーザー判断へ
- `/post-review` は削除せず、手動の深掘り・投稿群の戦略チェック用に残置（定型工程には含めない）
