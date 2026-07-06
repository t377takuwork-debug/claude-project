---
name: shira-rewrite-common-rules-pointer
description: shira_noteリライト共通ルール（禁止ワード・段落・タイトル/メタ・WPブロック・AFリンク・ナビURL等）はrepoのrewrite_common_rules.mdが唯一の正
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 78ff6626-dcaf-4206-a702-b89d1d33c5fb
---

shira_noteの全リライト共通ルールは、リポジトリ内の **`blogs/shira_note/rewrite_common_rules.md`** に統合済み（2026-07-05）。リライト・新規記事作成時は必ずこのファイルを読む。

**Why:** 2026年6〜7月に個別メモリ14本（禁止ワード・スマートクォート・メタ設計・evergreen・段落分割・継続性表現・WPブロック囲み・ショートコード独立ブロック・ul→div・楽天AFリンク仕様・速報型商材選定・ナビURL一覧・段落文体・musicday段落スタイル）として蓄積したルールを、モデル・環境が変わっても失われないようリポジトリへ昇格した。メモリ側は本ポインタのみ残す。

**How to apply:** ルールの追加・変更が発生したら、新しいメモリを作らず `rewrite_common_rules.md` を直接更新する（番組固有ルールのみメモリまたは各`*-rewrite`コマンドへ）。機械チェック可能なルールは `tools/qa_draft.py` への追加も検討する。
