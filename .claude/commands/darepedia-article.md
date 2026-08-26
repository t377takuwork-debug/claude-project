# darepedia 記事生成システム

darepedia（https://darepedia.com/）の新規記事を、構成→本文→内部リンク→QAまで一気通貫で生成する。会議は行わない。確定済みのdarepediaルールを直接適用し、ユーザーの承認ポイントのみで進む。

darepediaはcf_room/vtuber_logと異なり画像自動配置・WPアップロードの仕組みを持たない（SNS埋め込みURLのみ）。実在の人物・進行中の社会問題を扱うため、報道倫理（断定回避・噂と事実の書き分け・個人攻撃助長の回避）を毎回必ず適用する。

## 呼び出し方

```
/darepedia-article [人物名/トピック] [記事タイプ]
```

例：`/darepedia-article 内堀太郎 プロフィールWiki型`
例：`/darepedia-article 探偵ナイトスクープ母親問題 時事速報型`

記事タイプが未指定の場合はStep 0で確認する。

## 実行前の準備（毎回必ず読む）

- `blogs/darepedia/rules/article_pipeline.md` — 工程順の1枚地図（本スキルはこれの自動化）
- `blogs/darepedia/rules/writing_tone_and_ethics.md` — 断定回避・報道倫理・捏造禁止（**他の全ルールに優先**）
- 工程ごとに`article_pipeline.md`の参照ファイル列に従い該当ルールを開く（`category_persona_keyword.md`・`headline_writing.md`・`article_structure.md`・`design_components.md`・`wordpress_output_rules.md`）
- 内容・デザインの完成形リファレンス：ユーザー提供の記事①（時事速報・炎上考察型）、既存サイトの`uchiboritaro-wiki`記事構成（プロフィールWiki型・分析結果は`article_structure.md`に反映済み）
- **技術フォーマット（Gutenbergブロックコメント）のリファレンス：`blogs/shira_note/drafts/draft_cdtv.txt`。** ユーザー提供の記事①②は見出しを読みやすくするための簡略化版であり、実際の入稿フォーマットそのものではない（2026-08-26確定）。出力形式は`wordpress_output_rules.md`が唯一の正

---

## Step 0：記事タイプ・資料インプット確認

1. 記事タイプ（プロフィールWiki型／時事速報・炎上考察型）が未指定ならユーザーに確認する。上記2タイプ以外（予想・考察型等）を依頼された場合は、テンプレート未整備の旨を伝え設計方針をユーザーと合意してから進める
2. 「この記事に使える一次資料（公式サイト・公式SNS・プレスリリース・報道記事・過去の調査メモ・本文に埋め込みたいX/Instagram投稿のURLなど）はお持ちですか？」と確認する。資料があれば事実情報の基盤として優先使用する
3. 資料が無い場合のみWebSearch/WebFetchで補完するが、個別の詳細情報には精度限界があることをユーザーに伝え、判明した範囲で提示し不足があれば追加資料を依頼する（`category_persona_keyword.md`のキーワード調査手順に従う）
4. **SNS投稿の埋め込みURLは自動でリサーチしない。** WebFetchはX/InstagramのJS描画・ログイン制限により投稿本文をほぼ取得できず、実在しないURLを推測で作ることも捏造禁止原則で許されないため、埋め込みたい投稿はユーザーから資料としてURLを受け取る運用とする（`design_components.md` §3）
5. 事実確認できない事項は本文に含めない。断定せず「不明」「未公表」と明記する方針をこの時点で確認する

## Step 1：カテゴリ・スラッグ・関連記事確認

1. カテゴリ（celebrity/sports/expert/others）を決定する（`category_persona_keyword.md`）
2. スラッグ案を決定する（既存パターン表に沿わせる）
3. `blogs/darepedia/rules/internal_links.md`を確認し、同一人物の既存記事が無いかチェックする。あれば見出し構成・言い回しの一貫性を保ち、内部リンク候補にする

## Step 2：検索意図・ペルソナ確認（タイトル設計の前に必ず行う）

1. このキーワードで検索する人が「何を知りたくて」「どんな状況で」検索しているかを具体的に言語化する（`category_persona_keyword.md`の一般ペルソナを土台に、今回のキーワード固有の検索意図に絞り込む）
2. 検索意図の分類（例：関係の経緯を確認したい／プロフィールを確認したい／見逃し配信を探している）を1つに絞る
3. この記事で「最後に知りたいこと」＝記事冒頭に置く結論を決める
4. 1〜3を簡潔に提示し、ユーザーの確認を取る（1ラウンドで済ませる。shira_note `shira-keyword-article.md` Step2と同じ考え方）

**このステップを飛ばしてStep3のタイトル設計に進まない。**

## Step 3：タイトル決定

1. Step2で確定したペルソナ・検索意図に沿って、タイトル案を`headline_writing.md`の型で複数案作成する。**この時点では見出し構成は提案しない**
2. 案の中でペルソナ・検索意図に最も合うものを1つ推奨案として示し、理由を添える

**承認ポイント①**：タイトル案を提示し、ユーザーにタイトルを確定してもらう。見出し構成はまだ出さない。

## Step 4：見出し構成設計

1. Step3で確定したタイトルに沿って、記事タイプ別テンプレート（`article_structure.md` §1または§2）を土台にH2/H3構成を設計する
2. 未確定情報がある場合はここで明示する

**承認ポイント②**：見出し構成を提示し、ユーザーの確認を取る。

## Step 5：本文執筆

1. `writing_tone_and_ethics.md`（文体・語尾のバリエーション・断定回避・報道倫理・捏造禁止）に従って本文を執筆する。1文書き終えるごとに文末が3文以上連続していないか意識する
2. `design_components.md`のHTML装飾部品を組み込む（同じ型を3回以上使わない）。SNS埋め込みの扱い・配置は同ファイル§3が唯一の正（ユーザーから埋め込みコードが提供された場合はそちらを使う）
3. 内部リンクを設置する（`internal_links.md`にある実在URLのみ。無理に埋めず、関連性のある記事があれば1〜3本程度）
4. **`wordpress_output_rules.md`のGutenbergブロックコメント形式（`<!-- wp:paragraph -->`/`<!-- wp:heading -->`・h3は`{"level":3}`属性・装飾HTMLは`<!-- wp:html -->`・1文＝1段落）で `drafts/draft_{スラッグ}.txt` に保存する。** ファイル冒頭にタイトル行・メタディスクリプション行・スラッグ・アイキャッチ画像（提供時のみ）、`[nopc][title][/nopc]`、リード文の後に`[nopc][mokujimae][/nopc]`、本文中盤に`[nopc][originalsc][/nopc]`を1箇所配置する（同ファイル §2・§3・§7）

**承認ポイント③**：本文全体を提示し、事実関係・トーンに問題がないかユーザーの確認を取る（特に実在人物への配慮が必要な記事は、公開前に必ずこの確認を挟む）。

## Step 6：QAと記録

1. `powershell -ExecutionPolicy Bypass -File "blogs/darepedia/tools/qa_draft.ps1" "blogs/darepedia/drafts/draft_{スラッグ}.txt"`を実行し**ERROR 0件**を確認する。ERROR/WARNが出た場合はその場で修正し再実行する
2. `blogs/darepedia/rules/internal_links.md`の「確認済みタイトル」表に新規記事のURL・タイトルを追記する
3. `blogs/darepedia/publish_log.md`に1行追記する（公開日は実際にWordPressへ反映した日、無ければドラフト完成日を仮置きしユーザーに反映後の更新を依頼する）
4. **構造化データ（JSON-LD）はユーザーから依頼があった場合のみ追加する（毎回必須ではない）。** `wordpress_output_rules.md` §11のサイト定数・テンプレートに従う。datePublished等の未確定項目は都度聞き直さず、指示がなければドラフト作成日を使ってよい
5. 完了報告：QA結果（ERROR/WARN件数）・保存先パス・タイトル・カテゴリ・残タスク（WordPress貼り付け＝コードエディタ経由必須、公開前チェックリスト＝`wordpress_output_rules.md` §10）

---

## 完了条件

「`drafts/draft_{スラッグ}.txt`保存済み・`qa_draft.ps1` ERROR 0件・`internal_links.md`追記済み・`publish_log.md`追記済み」の4点。

## 注意事項

- 確定済みルールは再議論しない。ルールにない判断が必要になったら都度確認する
- 事実情報は確認できたもののみ使用（捏造絶対禁止）。手元にない情報はWebSearchで公式情報を確認し、確認できなければ「不明」「未公表」と書く
- 実在の人物・進行中の社会問題を扱うため、断定的な加害者視・犯人視表現、私人への詮索を助長する記述は書かない（`writing_tone_and_ethics.md`）
- リライト（既存記事の改稿）は本スキルではなく`article_pipeline.md`を手動で通す
