---
name: system-asp-theme
description: /asp-kaigiの出力を受けて記事テーマを提案するSEO戦略システム。WebSearchで実測データを取得して黄金のロングテールを特定する。
metadata: 
  node_type: memory
  type: project
  originSessionId: 349bb718-5cc3-420d-b18a-0a86c4ab2581
---

記事テーマ提案専用システム。スキルファイルは repo内 `.claude/commands/asp-theme.md`。`/asp-theme` で呼び出す。

**Why:** /asp-kaigiで「やる」と決めた後、具体的にどの記事を書くかを実測データに基づいて決定するため。

**How to apply:** /asp-kaigiの出力後にユーザーがテーマ提案を求めた場合は `/asp-theme` を案内する。

## 使用順序
```
/asp-kaigi → 案件分析・参入判定・越境思考の確立
      ↓
/asp-theme → /asp-kaigiの出力を貼り付けて呼び出す
             WebSearchで実際のサジェスト・allintitleを調査
             黄金のロングテールを特定して3〜5本のテーマを提案
```

## 出力（各テーマごとに5項目）
1. 提案テーマ（記事タイトル案）
2. ターゲットペルソナ
3. SEO勝算分析（allintitle実測・難易度S/A/B/C・攻略判断）
4. 執筆のフック（競合に勝てる理由）
5. 記事骨子

## 重要ルール
- 推測・想像によるキーワード提案禁止。WebSearchの実測データのみ使用
- 【完全撤退】判定テーマは提案せず代替テーマを提示
- /asp-kaigiの出力がない場合は貼り付けを求める
