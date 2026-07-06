---
name: feedback-note-article-draft-save
description: note-article記事生成完了後はdraftsフォルダへの保存が必須（2026-06-12確認）
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0ff331f1-8156-40a8-9f28-4b7c1eb25070
---

記事本文生成（Step 4）完了後、ユーザーへの出力と同時に必ず `mbticode/articles/drafts/` へファイルを書き出す。

**Why:** スキル内にStep 5（保存）の明示がなかったが、ユーザーから指摘を受けた。生成しっぱなしにせずdraftsへの書き出しまでが1セットの作業。

**How to apply:**
- ファイル名：記事テーマを簡潔に表した日本語（例：`合わせすぎて自分がわからなくなる理由.md`）
- 保存先：`brands/mbticode/articles/drafts/`
- ファイル先頭に管理情報（作成日・種別・有料誘導先・Noteタグ）を記載する
- s4lvの記事生成時も同様にdraftsフォルダへ保存する
