# s4lv 知見・意図ファイル棚卸し（2026-09-10）

`/note-advisor`（s4lv）設計の前提資料。s4lv の「誰が・誰に・何を・いくらで・どう書くか」に関わる知見と、オーナーの意図・修正が**今どこに記録されているか**を洗い出し、アドバイザーの参照元・学びの台帳への統合計画・先に潰すべき矛盾を確定する。

対象：`brands/s4lv/` 全ファイル／共通ファイル（`brands/writing/`・`docs/reference/`・`docs/rubrics/`）／s4lv 関連メモリ16本／公開draft 6本。他アカウントは対象外（雛形化は s4lv 版が回ってから）。

---

## 0. 最重要の発見（先に読む）

1. **アドバイザーの人格は既に定義されている**。`rules/project_s4lv_operation_system.md` 週次ルーチン表（2026-08-21確定）：戦略壁打ち時の Claude は「**シビアで現実的なビジネスアドバイザー**（ROI・リスク管理最優先、綺麗事や再現性のないノウハウを排除）」。公開コンテンツの著者ボイス（謙虚な職人・カジュアル）とは別レイヤー。→ `/note-advisor` はこれを継承する。新しく作らない
2. **実測データの蓄積基盤が実質ゼロ**。`kpi_weekly_template.md` は存在するが `kpi_log.md` は未作成（2026-08-19新設決定→8/25「未実施」→以後記録なし）。反応データは `note_article_index.md`「反応の記録」の**1行**（アフィリ記事スキ20）と `tools/s4lv_threads_insights_notes_0907.md`（Threads初回分析）だけ。→ 「作業するたび賢くなる」仕組みは、**まず数字を1箇所に貯める習慣**がないと成立しない
3. **旧文体OSの残骸が現行方針と矛盾したまま生きている**（§2 の #2〜#4）。特に `examples_x_posts.md` は cheatsheet から「生成前に読め」と参照されているのに、中身は 2026-09-07 に「使わない」と決めた旧文体（砂漠の看板・遺言・記憶のゆらぎ）の見本。アドバイザーがこれを読むと凡庸ではなく**逆方向に**ズレる
4. **「学びの台帳」の原型はすでに散在している**。`persona.md`「未検証の前提」節／`note_article_index.md`「反応の記録」／`threads_insights_notes`「所見と仮説（確信度つき）」／`paid_price_kaigi`「KPI観察トリガー」／`note_affiliate_kaigi`「需要発火条件」。新規ファイルを増やすのではなく、これらを1箇所へ寄せる

---

## 1. ファイル一覧（役割・鮮度・重複）

### 1-1. アイデンティティ・ペルソナ（誰が・誰に）

| ファイル | 役割 | 鮮度 | 備考 |
|---|---|---|---|
| `rules/project_s4lv_accounts.md` | **唯一の正**：1アカウント体制・3媒体プロフィール文・アイデンティティ原則7・2本柱（型6:AI4） | 現行（09-08） | アドバイザー Tier 1 |
| `rules/project_s4lv_persona.md` | **唯一の正**：読者3軸ペルソナ＋根拠（公開7記事スキ数）＋市場検証＋**「未検証の前提」節** | 現行（08-23） | Tier 1。「未検証の前提」は台帳へ |
| `shared/personal_data.md` | **唯一の正**：実績数値・開示ルール・経歴・参入/撤退アルゴリズム PHASE1〜4・捨てたSEO理論 | 現行 | Tier 1 |
| `rules/project_s4lv_identity.md` | 人格・思想の源（5人の成功エッセンス・三極構造・黄金ルール）。末尾は旧プロフィール/ターゲット | 半歴史資料 | ヘッダーで「源として残す」と自己宣言済み。Tier 2 |
| `profile.md` | 2026-07-08版プロフィール（セットA） | **陳腐化** | 数字入りアカウント名・プロフィール文が残存。accounts.md（08-19改訂）と矛盾 → §2 #1 |

### 1-2. マネタイズ戦略・運用（何を・いくらで・どう回す）

| ファイル | 役割 | 鮮度 | 備考 |
|---|---|---|---|
| `rules/project_s4lv_operation_system.md` | 投稿量・工程担当・週次ルーチン・**マネタイズ導線・価格戦略・月50万目標・撤退基準**・アドバイザー人格 | 現行だが一部陳腐 | 「未整備の資産」節が古い（§2 #6）。Tier 2 |
| `rules/project_s4lv_note_article_process.md` | Note記事7ステップ・95点基準・有料3フェーズ・価格帯別字数・**マネタイズ設計原則（切り売り禁止）**・執筆ルールの累積 | 現行だが**累積型で肥大**（164行・日付層が5層） | 既存記事棚卸し表は index と重複（§2 #5）。Tier 2 |
| `articles/note_article_index.md` | 公開9記事の一覧・適合判定・章別チャプター・**反応の記録**・誘導ローテ | 現行 | **唯一の反応データ記録先**。Tier 1 |
| `kpi_weekly_template.md` | 週次KPIテンプレ | 現行・**未使用** | `kpi_log.md` 不在（§0 #2） |
| `rules/project_s4lv_assets_lost.md` | 消失資産4本の記録 | 保留 | 「実測貯まってから」で凍結中 |

### 1-3. 文体OS — SNS（どう書くか）

| ファイル | 役割 | 鮮度 | 備考 |
|---|---|---|---|
| `rules/threads_post_generation_rules.md` | Threads生成の唯一の正（09-07） | 現行 | 生成スキルの領分。アドバイザーは読まない |
| `rules/feedback_s4lv_threads_writing_style.md` | Threads詳細文体リファレンス | 現行（格下げ済み） | 同上 |
| `rules/feedback_s4lv_x_writing_style.md` | X文体の唯一の正 | 現行だが**内部矛盾** | 「エグい比喩解放」「ライブ感①②③」節と「平易さ優先（上より優先）」節が同居（§2 #3） |
| `rules/feedback_s4lv_x_post.md` | X反響設計A/B・「確定構造3種」・ユーザー文体調整パターン | 現行だが**旧OS混在** | 「確定構造3種」＝旧文体OS（§2 #4）。「ユーザーの文体調整パターン」節は意図資料として有用 |
| `sns_post_cheatsheet.md` | SNS運用ナビ凝縮版・唯一の正マップ | 現行 | Tier 2（SNS相談時） |
| `x_neta_daicho.md` | ネタ台帳K1〜16／A1〜16 | 現行 | 生成スキルの領分。「事実欄＝本人確認済みのみ」ルールは意図資料として重要 |
| `examples_x_posts.md` | X Good/Bad見本 | **陳腐化（実害あり）** | 07-06作成・旧文体OSの見本。cheatsheet が参照中（§2 #2） |
| `rules/feedback_s4lv_x_post_workflow.md` | 審査工程（sns-ai-reviewer） | 現行 | — |
| `tools/s4lv_threads_insights_notes_0907.md` | Threads初回週次分析（確信度つき所見） | 現行・**最新の実測** | Tier 2。所見は台帳へ |

### 1-4. 文体OS — Note（共通・全アカウント）

| ファイル | 役割 | 備考 |
|---|---|---|
| `brands/writing/writing_tone.md` | Note文体共通核＋s4lv上書き（オーナーの意図6点を冒頭に明記） | Tier 2（Note記事相談時） |
| `brands/writing/writing_core.md`／`_note_structure`／`_headlines`／`_expressions` | 共通原則 | 生成スキルの領分 |
| `brands/writing/note_review_rubric.md` | note-ai-reviewer 採点基準 | 同上 |
| `docs/rubrics/title_scoring.md`／`sns_ai_tone_rubric.md` | 採点表 | 同上 |
| `docs/reference/note_asset_check_prompt.md` | 迫×コトラー資産化チェック（任意） | ほぼ未使用。アドバイザーの「導線・資産性」視点と重なる → 吸収候補 |
| `docs/reference/note_monetization_reference.md` | notekaigi 3レンズ思考モデル＋note公式データ（09-10新設） | Tier 1 |

### 1-5. 意図の一次資料（オーナーが1文ずつ合意した公開記事）

| draft | 公開 | 往復 | 意図として読めるもの |
|---|---|---|---|
| `note_free_20260908_note_access_kaiseki.md` | 09-09 | **約17回** | 最新のオーナー好み（煽らない・教えない・気取らない・寄り添い1〜2箇所・型を毎回変える）。memory `feedback_s4lv_note_topical_article_intent_0909` に言語化済み |
| `note_free_20260831_note_affiliate_hajimekata.md` | 09-04 | 多数 | 実用リファレンス型・法律は一次ソース・語りかけ口調＋太字。**スキ20/3日＝現状唯一の需要シグナル** |
| `note_free_20260710_title_tsukekata.md` | 09-03差替 | — | ペルソナ再設定の実例・writing_tone 成立の元記事 |
| `note_free_20260709_trendblog_kasegeru.md` | 07-09 | — | 参入判定フローの無料開示範囲 |
| `note_paid_20260430_sekkei_no_kata.md` | 08-25再公開 | — | 核記事¥4,980。切り売り禁止は遡及適用せず |
| `note_paid_20260831_kensaku_jyoi_hiyou_iranai.md` | 未公開 | — | 防衛側の型・マスク版証拠・¥9,800想定。「まだ修正する」 |

### 1-6. メモリ16本（オーナー修正・決定の経緯）

| 種別 | ファイル | 台帳へ移す中身 |
|---|---|---|
| 決定 | `notekaigi_reactivation_0819` | 価格据え置き・次は980〜1,980円・KPIログ新設（未実施） |
| 決定 | `profile_redesign_0819` | 数字非表示・経歴ドラマ排除・カジュアル |
| 決定 | `business_doc_review_0821` | **答えの切り売り禁止**・月50万目標・アドバイザー人格の分離 |
| 決定 | `new_paid_article_theme_kaigi_0823` | ¥1,480「見切りと転換」（未着手） |
| 決定 | `paid_article_price_kaigi_0825` | ¥4,980（限定¥3,980）・**KPI観察トリガー**（4週 or 500〜1,000ビューで購入0なら値下げ検討） |
| 決定 | `note_affiliate_article_kaigi_0830` | 実用リファレンス方向・**需要発火条件**・¥300〜500切り売り不採用・案X/Y/Z |
| 決定 | `shira_jisseki_disclosure_kaigi_0831` | 実名不採用・マスク版・4ジャンル横断で訴求 |
| 決定 | `x_post_redesign_algo_research_0904` | 2軸再編・X数字条件付き解禁・旧文体OS不使用 |
| 決定 | `threads_intent_redefinition_0904`／`threads_playbook_0907` | Threads誘導全廃・現場で開く |
| 意図 | `note_topical_article_intent_0909` | Note記事のオーナー好み8点 |
| 意図 | `x_post_ai_tone_structural_check_0906` | 構造レベルAI臭さ・入口・語尾4点 |
| 意図 | `sns_batch_efficiency_0907` | 審査1巡・参照はcheatsheet起点 |
| 運用 | `kpi_log_workflow_0825` | KPIはスクショで渡す |
| 進行 | `kensaku_jyoi_kiji_shitagaki_0831`／`title_article_rewrite_0829` | 下書き状況 |
| インフラ | `threads_automation_*` ×3 | 対象外 |

原則（`project_asset_migration_0706`）：**ルールは repo が正、メモリは経緯**。アドバイザーの参照元にメモリを含めない。決定事項で repo 未反映のものは台帳シードで拾う。

---

## 2. 矛盾・重複・陳腐化（先に潰す）

| # | 箇所 | 問題 | 実害 | 処置案 |
|---|---|---|---|---|
| 1 | `profile.md` | 07-08版。アカウント名「s4lv｜10年続く…」・170万PV入りプロフィール文が残存。accounts.md（08-19：タグラインなし・数字非表示）が正 | 新セッションが読むと矛盾情報を取り込む | **削除**（内容は accounts.md「旧セットA」注記と git 履歴で足りる） |
| 2 | `examples_x_posts.md` | 旧文体OS（砂漠の看板・遺言・記憶のゆらぎ）の Good 見本。09-07「旧文体OSは使わない」確定後も cheatsheet「Good/Bad見本」で参照中 | **生成前に読むと旧文体へ引き戻される**（memory 0907 が /post-review で同じ問題を指摘済み） | 現行方針（平易・番号手順・固有名詞・線を引いて終わる）の見本へ**差し替え**。差し替えまでは cheatsheet の参照を外す |
| 3 | `feedback_s4lv_x_writing_style.md` | 「エグい比喩を解放」「情景ワードをねじ込む」「ライブ感①記憶のゆらぎ」と「平易さ優先（上より優先）」が同居。生成後自己チェックは「ライブ感要素を1つ」を要求 | どちらが正か毎回判断が要る。審査ルーブリックは旧構造を対象外にしたが、生成側ファイルは残したまま | 旧OS節を「**歴史・現行では使わない**」ブロックへ隔離 or 削除。自己チェックの「ライブ感」要件を「喋り言葉の接続詞・非対称リズム」に限定 |
| 4 | `feedback_s4lv_x_post.md` | 「確定構造3種（96〜99点）…次回以降の投稿提案はこの構造を基準にする」＝旧OS | #3 と同じ | 「確定構造3種」を歴史注記に。「ユーザーの文体調整パターン」節は残す |
| 5 | `note_article_process.md`「既存記事の棚卸し」表 | `note_article_index.md` と同じ記事一覧。index にのみ URL・反応記録・誘導日がある | 二重管理。片方だけ更新されるズレ（09-03 のタイトル差替で両方直した実績＝手間） | process 側を index へのポインタに圧縮 |
| 6 | `operation_system.md`「未整備の資産」 | 「`article_index.md` 未作成」「`published/` 未作成」と記載。index は存在、published/ は 09-03 に「s4lv は対象外」と判断済み | 陳腐 | 節を現状に更新（残るのは neta_bank／examples_note／suggest_keywords の3点のみ） |
| 7 | KPI ログ | `kpi_log.md` 不在。全ルールが「KPIログに蓄積」を前提に書かれている | **学びの基盤がない**。paid_price の観察トリガー（4週＝09-22頃）を判定する数字が無い | 台帳に「実測ログ」節を持たせ、`kpi_log.md` は**作らない**（ファイルを増やさない）。テンプレは残す |
| 8 | `note_asset_check_prompt.md` | 迫×コトラー資産化チェック。「任意」で実質未使用 | 放置 | アドバイザーの「導線・資産性」視点に吸収し、ファイルはポインタ化（今回は提案のみ） |

#1〜#4 は**アドバイザー構築の前提**（読ませる前に潰す）。#5〜#8 は構築と同時でよい。

---

## 3. アドバイザーの参照元（確定案）

### Tier 1：毎回読む（合計 約600行・小さい）

| ファイル | 何のために |
|---|---|
| `rules/project_s4lv_accounts.md` | アイデンティティ原則・2本柱・数字の扱い |
| `rules/project_s4lv_persona.md` | 誰に売るか・3軸 |
| `shared/personal_data.md` | 実績・開示ルール・参入/撤退アルゴリズム |
| `articles/note_article_index.md` | 何を出していて反応はどうか |
| **学びの台帳（新設）** | 検証済み／仮説／棄却／オーナー意図／実測ログ |
| `docs/reference/note_monetization_reference.md` | note公式データ・3レンズ思考モデル |

### Tier 2：相談テーマに応じて開く

| テーマ | ファイル |
|---|---|
| 価格・目標・撤退 | `rules/project_s4lv_operation_system.md`（価格戦略・月50万・撤退基準） |
| 有料記事の中身・切り売り判定 | `rules/project_s4lv_note_article_process.md`（マネタイズ設計原則・価格帯別字数・95点基準） |
| Note記事のトーン | `brands/writing/writing_tone.md` 0章＋s4lv上書き |
| 特定記事の相談 | `drafts/` の該当記事（**オーナーが合意した到達点として読む**） |
| SNS導線 | `sns_post_cheatsheet.md`・`tools/s4lv_threads_insights_notes_*.md` |
| 人格・思想の深掘り | `rules/project_s4lv_identity.md` |

### 読まない

- 文体OSの詳細（threads_post_generation_rules／x_writing_style／examples）— 生成スキルの領分。アドバイザーは「何を出すか」を助言し「どう書くか」は生成スキルに渡す
- `x_neta_daicho.md` 全文 — 必要なら該当K/Aだけ
- メモリ — 経緯であって正ではない

---

## 4. 学びの台帳：統合計画とシード

### 置き場所・形式

- **`brands/s4lv/rules/s4lv_learnings.md`**（1ファイル・上限150行）。既存の rules/ 配下に置き、cheatsheet「唯一の正マップ」に1行追加
- 1エントリ＝`日付｜区分｜内容｜根拠｜確信度`。区分＝**検証済み／仮説／棄却／オーナー意図／観測トリガー／実測ログ**
- 入れる条件：根拠が「KPI数値・オーナー修正・notekaigi決定」のいずれか。「〜すると良いかも」は入れない
- 棚卸し：4週ごと。仮説に確認データ2件以上→検証済みへ圧縮、否定→棄却へ1行残して本文削除、実測ログは直近8週のみ保持（古い分は `s4lv_learnings_archive.md` へ）

### シード（既存ファイルから移す・元ファイル側の処置つき）

| 区分 | 内容 | 出典 → 元ファイルの処置 |
|---|---|---|
| 観測 | 公開7記事のスキ数（トレンド16／アドセンス7／タイトル5／売れない理由4／X 3／設計の型1／楽天1）。最多は「続けるか迷っている」系 | `persona.md` 根拠データ → **残す**（ペルソナの根拠として必要）。台帳は要約1行 |
| 観測 | アフィリ記事：公開3日でスキ20（無料記事ベースライン＝数ヶ月で1〜16）。実用リファレンス系の需要シグナル | `note_article_index.md` 反応の記録 → index はポインタ化、**正は台帳** |
| 観測 | Threads：フォロワー1・31件平均13view・エンゲージ0。ボトルネックは型でなくリーチ | `threads_insights_notes_0907` 所見 → 分析ファイルは残す、台帳は結論1行 |
| 仮説 | 「型の深掘りは売れる」（¥4,980記事・購入1件）は法則でなく仮説 | `notekaigi_reactivation_0819`・`new_paid_theme_0823` |
| 仮説 | 実用リファレンス系は無料でスキが速い。有料化は需要発火（遷移率／質問3件／スキ中央値超え）待ち | `note_affiliate_kaigi_0830` |
| 仮説 | 無料で分類提示→有料で行動テンプレ、が購買を決める（MBTICODE n=1）。s4lv転用可否＝購買心理は近いが実証なし | `mbticode/rules/project_mbticode_paid_article_sales_factor.md` |
| 仮説 | s4lvのペルソナは「迷い・答え合わせ」。AI Overview時代の一次情報勝ち筋と一致するが自アカウントでは未実測 | `persona.md`「未検証の前提」→ 節ごと台帳へ移し、persona.md はポインタ |
| 観測トリガー | ¥4,980記事：4週（09-22頃）or 500〜1,000ビューで購入0なら値下げ¥2,980〜3,980を再検討 | `paid_price_kaigi_0825` |
| 観測トリガー | アフィリ記事の有料化：2〜4週で遷移率／質問コメント3件／スキ中央値超え、案Zは「もしも詳しく」2件 | `note_affiliate_kaigi_0830` |
| 観測トリガー | Threads：09-21再分析でフォロワー二桁に乗らなければ継続可否を会議 | `threads_insights_notes_0907` |
| 棄却 | 実名フル開示／高価格でリスク相殺／¥300〜500切り売り／相互フォロー返信ブースト優先／RP依頼 | 各 kaigi メモリ |
| 決定（Note固有） | 答えの切り売り禁止（売るのは生存構造・思考プロセス・仕組み）／次の有料は980〜1,980円／月50万目標・期限なし／実名はマスク版が恒久 | `business_doc_review_0821`・`shira_disclosure_0831` |
| オーナー意図（Note） | 煽らない参考記事／教えない／気取った語を素直な動詞に／寄り添い1〜2箇所／ベネフィット文・締めCTAの型を毎回変える／4,000〜5,000字台／実データ画像は2例対比 | `feedback_s4lv_note_topical_article_intent_0909` → 既に `note_article_process.md` にも反映済み。台帳は要約 |
| オーナー意図（媒体横断） | 数字非表示（プロフ）・数字は答え合わせ材料（本文）／経歴ドラマ不要／カジュアル／進行形のみ／「〜んだ。」「正直〜」「格言オチ」「汎用疑問符」はAI臭／型が見えたら崩す／台帳事実欄は本人確認済みのみ | `x_post_ai_tone_structural_0906`・`x_post.md`「文体調整パターン」・`x_neta_daicho` 3b |
| 実測ログ | （空。次のKPIスクショから開始） | `kpi_weekly_template.md` の項目を流用 |

---

## 5. 書き戻しの引き金（設計要件として確定）

| 引き金 | 誰が | 台帳のどこへ |
|---|---|---|
| KPIスクショを渡す | アドバイザーが読み取り→「実測ログ」に数値＋「何を確認/否定したか」を1行 | 実測ログ／仮説の更新 |
| `/notekaigi` の [更新] | 決定と観測トリガーを1行 | 決定／観測トリガー |
| Note記事・SNSバッチ完了時 | 「今回オーナーが直した箇所の意図」を1〜3行（`/note-article`・`/s4lv-post` の完了ステップに追記） | オーナー意図 |
| オーナーが「これは効いた/外した」と言う | 即1行 | 検証済み／棄却 |

---

## 6. 他アカウントへの雛形化に向けたメモ

- 構造（Tier 1/2・台帳6区分・引き金4つ）はアカウント非依存
- MBTICODE は `rules/project_mbticode_paid_article_sales_factor.md` が台帳の「仮説」節そのもの。雛形化時はこれを吸収
- vivant は情報ベース（実体験なし）のため「オーナー意図」の中身が違うだけで構造は同じ
- 共通化するのは**アドバイザーの骨格**（人格・接地要件・引き金）のみ。台帳の中身はアカウントごと
