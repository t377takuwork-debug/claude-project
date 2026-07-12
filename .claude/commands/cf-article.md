# cf_room 記事生成システム（画像自動配置つき）

cf_roomのレビュー記事を、構成→本文→画像選定・配置→WordPressアップロード→QAまで一気通貫で生成する。会議は行わない。確定済みのcf_roomルールを直接適用し、ユーザーの承認ポイントのみで進む。

## 呼び出し方

```
/cf-article [記事スラッグ] [テーマ/対策キーワード]
```

例：`/cf-article tapo-c500-review Tapo C500 屋外カメラ レビュー`

**前提**：`blogs/cf_room/assets/<記事スラッグ>/` に記事で使う画像を投入済みであること。未投入なら「assetsフォルダに画像を入れてください」と案内して待つ。

## 実行前の準備（毎回必ず読む）

- `blogs/cf_room/rules/article_pipeline.md` — 工程順の1枚地図（本スキルはこれの自動化）
- `blogs/cf_room/rules/image_placement.md` — 画像選定・alt・配置・アップロードの全ルール
- 工程ごとに `article_pipeline.md` の参照ファイル列に従い該当ルールを開く（headline_writing・design_components等）
- 完成形リファレンス：`drafts/deco-be22-review_revised_v2.txt`

---

## Step 1：入力確認と画像インベントリ

1. スラッグ・テーマ・`assets/<スラッグ>/` の画像有無を確認する
2. ファイル名がASCII・スラッグ入りかチェックし、違反があればリネーム案を提示して承認後にリネームする
3. 各画像を`Read`で解析し、`assets/<スラッグ>/manifest.md` を生成する（`image_placement.md` §5の表形式：file / alt / title / description / 配置先）。既存manifestがあれば追加画像のみ解析する

**承認ポイント①**：manifest（各画像の内容理解とalt案）を提示し「この理解で合っていますか？」と確認する。

## Step 2：タイトル・構成設計（パイプライン工程1〜3）

1. キーワードと差別化の切り口を決め、タイトル・メタを設計する（`headline_writing.md` の4原則・型カタログ・完全一致先頭）
2. H2構成を設計する。各セクションに「使う画像（manifestの配置先と対応）」も割り当てる（`image_placement.md` §3：関連テキストの近く・H2ごと0〜2枚・全体5〜12枚）

**承認ポイント②**：タイトル案＋構成＋画像配置対応表を提示し確認する。未使用になる画像があればここで報告する。

## Step 3：画像アップロード（B案・REST API）

1. `powershell -ExecutionPolicy Bypass -File "blogs/cf_room/tools/wp_upload.ps1" -Slug <スラッグ> -DryRun` で対象一覧を提示
2. ユーザーの実行OKを得てから本実行（`-DryRun`なし）。alt/タイトルはmanifestから自動設定される
3. `uploaded_urls.json` が生成されたことを確認する。失敗が2回続いたら中断して状況を報告する（認証ファイル未作成の場合はスクリプトの案内に従いユーザーに作成を依頼する）

## Step 4：本文生成（パイプライン工程4〜8）

1. 本文を生成する（`copywriting_phrases.md`のPASONA構成・`copywriting_phrase_bank.md`の言い回し・実体験の捏造禁止）
2. デザインコンポーネントを組み込む（`design_components.md`・同じ型3回以上禁止）
3. 画像を配置する。**`src`は必ず`uploaded_urls.json`の実URLを使う**（手組み禁止）。形式は`image_placement.md` §2の`wp:image`ブロック
4. 内部リンクを設置する（`internal_links.md`：実在URLのみ・本文2〜6本・重複なし）
5. JSON-LDを生成し（`structured_data_prompt.md`）、`wordpress_output_rules.md`の形式で `drafts/<スラッグ>.txt` に保存する

## Step 5：QAと記録（パイプライン工程10〜12）

1. `powershell -ExecutionPolicy Bypass -File "blogs/cf_room/tools/qa_draft.ps1" "drafts/<スラッグ>.txt"` を実行し**ERROR 0件**を確認する（画像はチェック8・12でURL照合される）
2. `rewrite_log.md` に1行追記する（新規公開・効果検証予定日つき）
3. 完了報告：QA結果・保存先パス・アップロード済み画像数・未使用画像・残タスク（WP貼り付け＝コードエディタ経由、公開前チェックリスト＝`wordpress_output_rules.md` §8）
4. 完了報告に必ず添える：「WP貼り付け・画像表示確認後、`assets/<スラッグ>/` は削除可（未使用画像 ◯件は未アップロードのため、元データがなければ退避してから）。削除依頼をもらえば実行する」

---

## 完了条件

「`drafts/<スラッグ>.txt`保存済み・qa_draft ERROR 0件・`uploaded_urls.json`存在・rewrite_log追記済み」の4点。

## 注意事項

- 確定済みルールは再議論しない。ルールにない判断が必要になったら都度確認する
- 実測データ・体験談は提供された情報のみ使用（捏造絶対禁止）。手元にないスペック値はWebSearchで公式情報を確認する
- リライト（既存記事の改稿）は本スキルではなく `article_pipeline.md` を手動で通す
