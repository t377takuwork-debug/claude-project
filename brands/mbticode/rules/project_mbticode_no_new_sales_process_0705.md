---
name: project-mbticode-no-new-sales-process-0705
description: MBTICODE有料記事の販売促進のため新工程・スキル・エージェントを新設すべきか検討した結果、不要と判断（2026-07-05 notekaigi）
metadata: 
  node_type: memory
  type: project
  originSessionId: 470e9099-ab86-47b0-a20e-d68d28d5a10b
---

2026-07-05のnotekaigiで「有料記事の売上促進のために現在存在しない工程・スキル・エージェントを確立すべきか」を検討した結果、**新設不要**と判断（ユーザー了承済み）。

**判断根拠**：既存資産（`/note-article`・`/mbticode-content-pipeline`・`posts/cta_templates.md`・`/quality-guardrail`）でファネルの各段階はカバー済み。フォロワー3人・有料記事販売1件という段階で新しい分析エージェント等を組むのは、需要のない場所への先行投資になる。

**見つかった「やり残し」（新設ではなく既存タスクの延長として保留・未実装）**
- `cta_templates.md`でCTA未作成のまま残っている記事：①③⑤⑥⑦（記事②のみ3パターン整備済み）
- [[project_mbticode_paid_article_sales_factor]]の「行動テンプレート型」仮説を、`/note-article`実行時の確認項目として明示的に反映する軽微な追記（未実施）

**Why:** 行動規範の「ついで改善を禁止する」に沿い、この2点は提案止まりで実装していない。

**How to apply:** 今後「販売促進の仕組みが足りないのでは」という論点が再度上がった場合、まずこのメモリとフォロワー数・販売実績（[[project_mbticode_note_kpi_0705]]）を確認し、規模が変わっていなければ同じ結論（新設不要・既存タスク優先）を出発点にする。フォロワー数や販売件数が明確に増えた場合は再検討する。
