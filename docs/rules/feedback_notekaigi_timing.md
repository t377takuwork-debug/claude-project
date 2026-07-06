---
name: feedback-notekaigi-timing
description: /notekaigiを起動すべきタイミング——ファイル整理・軽量化などの構造的判断も対象（2026-06-20確定）
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8312248e-8f4a-42a7-b646-9c18d6931a05
---

スキルファイルの指示内容削減・memoryとスキルの役割分担・draftの削除判断など、**運用品質に直結する構造的な判断**は /notekaigi を通してから実行する。

**Why:** 2026-06-20、junk_juiceファイル整理の際に /notekaigi を通さず直接提案・実行しようとしてユーザーに指摘された。「ファイルの技術的な整理」と判断したが、「スキルの指示内容をどこまで削るか」「memoryとスキルの役割分担」は提案品質に直結する戦略判断だった。

**How to apply:** 以下のタスクは /notekaigi を起動してから実行する：
- スキルファイル（.claude/commands/）の指示内容の削除・統合
- memoryとスキルファイルの役割分担の変更
- drafts/published/の整理・削除判断
- 複数ファイルにまたがる構造的な変更
