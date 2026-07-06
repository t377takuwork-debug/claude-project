---
name: s4lv-assets-lost
description: s4lv系の参考資産4ファイル（テーマストック・他者タイトル集・サジェストKW・ネタバンク）が現存しない件の記録と旧運用ルール
metadata: 
  node_type: memory
  type: project
  originSessionId: 78ff6626-dcaf-4206-a702-b89d1d33c5fb
---

2026-07-05のメモリ棚卸しで、以下のs4lv参考資産ファイルがプロジェクト内・ユーザープロファイル配下に存在しないことを確認した（s4lv_official→brands/s4lv再編時に未移行または削除とみられる）。バックアップの有無は**ユーザーに要確認**。

| 資産 | 旧パス | 旧運用ルール |
|---|---|---|
| 有料記事テーマストック | `brands\s4lv_official\theme_stock.md` | `[ ]`ストック中／`[x]`記事化済みで管理。テーマ確認時に一覧提示・記事化完了で移動 |
| 他者有料記事タイトル集 | `brands\s4lv_official\reference_titles.md` | 実際に購入された他者タイトルを蓄積。タイトル提案・テーマ選定時に構造分析の参考にする |
| サジェストキーワード | `brands\s4lv_pro\suggest_keywords.md` | ラッコキーワード収集のGoogleサジェストを軸KWごとにセクション管理。テーマ・タイトル提案時に参照 |
| コンテンツネタバンク | `brands/s4lv_shared/content_neta_bank.md` | Note・X・Threads共通素材。5カテゴリ×5ネタ（2026-04-26）→最終的に10カテゴリまで拡張の記録あり |

※ 類似名ファイルを1件発見：`C:\Users\PC_User\OneDrive\デスクトップ\MBTI\修正用\キーワード\suggest_keywords.md`（MBTI用の可能性が高い・s4lv_pro版かは要確認）

**Why:** 参照先が消えた場所ポインタのメモリ4本を1本に統合した。旧運用ルール自体は再開時に流用できるため保持。

**How to apply:** s4lvのテーマ選定・タイトル設計・投稿ネタ出しを再開する場合、まずこれらの資産の所在（バックアップ・旧リポジトリ）をユーザーに確認する。見つからなければ上記の運用ルールで新規作成する。関連: [[s4lv-note-article-process]]
