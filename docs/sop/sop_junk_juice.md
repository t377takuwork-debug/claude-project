# SOP: junk_juice 記事制作（クライアント案件）

対象AI: すべてのモデル。クライアント管理アカウント（60代推し活エッセイ）のため、品質基準は特に厳守。

## 完了条件

- テーマ・タイトル: `/junk-theme` の出力フォーマット完了
- 本文: `Junk314/junk_juice/articles/drafts/` へ保存済み＋下記チェックリスト通過

## 手順

0. 見本バンク `Junk314/junk_juice/examples_essay.md`（バズ記事②の解剖）を読む
1. アカウント理解: `Junk314/junk_juice/CLAUDE.md` と `profile.md` を読む
2. テーマ・タイトル設計: `/junk-theme` を起動する
3. 構成・本文・保存: `/junk-article` を起動する
4. H2見出しには不安キーワードを組み込む。Step 3確認結果は次工程へ必ず引き継ぐ（`Junk314/junk_juice/rules/feedback_junk_article_seo_heading.md`）
5. Noteスマホ縦読みチェック4項目を通す（同上ファイル）
6. 機械検品: `python brands/tools/qa_article.py "<draftパス>"`（有料は `--paid`）→ **ERROR 0件必須**

## 有料記事（200円）の追加基準

`Junk314/junk_juice/rules/feedback_junk_paid_article.md` に従う:
- 無料パート: 情景フック1文の設計
- 有料パート: 「知らなかった情報」の密度基準
- 公開前チェックリスト**最低15項目**
- 文体維持ルール（エッセイ調を崩さない）

## 必ず守るルール

- 60代の実体験エッセイという建付けを壊す表現（若者言葉・AI的な整いすぎた文）を使わない
- 実績参照: バズ記事②（いいね155）の構造が成功パターン（`rules/project_junk314_junk_juice.md`）

## 出力見本

- 公開済み記事: `Junk314/junk_juice/articles/published/article_02_20260614.md`（バズ記事・いいね155）
