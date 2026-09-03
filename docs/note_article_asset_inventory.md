# Note記事制作 資産棚卸し（2026-09-04）

> 目的：Note記事の制作に関わるスキル・ルール・機械検品・レビュー資産を1枚に並べ、**トーン／AIっぽさ／改行のルールが今どこにあり、どこまで強制されているか**を可視化する。トーン基準の正式化（Step 1）と審査エージェント構築（Step 2）の土台。
> 対象アカウント：s4lv／MBTICODE／vivant（junk_juiceは棚卸し対象だがトーン基準の適用外）。
> 更新ルール：Note記事制作に関わる資産を追加・廃止したら本表を更新する。

---

## 1. 制作フローと、各段階で効く資産

```
テーマ → ペルソナ → タイトル → 構成（合意） → 本文 → 機械QA → LLMチェック → drafts保存 → 公開 → published移設
```

| 段階 | s4lv | MBTICODE | vivant | 共通 |
|---|---|---|---|---|
| テーマ | `/notekaigi`・`rules/project_s4lv_persona.md`根拠データ | `rules/project_mbticode_article_themes.md`（優先順位） | `/vivant-theme` Step 0〜2・`reference/` | `/content-scan`（既存記事から次テーマ抽出） |
| ペルソナ | `rules/project_s4lv_persona.md`（3軸・2026-08-23） | `persona_core.md`（3軸・属性なし） | `/vivant-theme` Step 1（自動確定） | `/note-article` Step 1 |
| タイトル | `rules/project_s4lv_note_article_process.md` 95点基準 | `rules/project_mbticode_note_title_seo.md`（感情KW） | `/vivant-theme` Step 3〜4 | `docs/rubrics/title_scoring.md`（配点表）・`writing_headlines.md`・`/note-article` Step 2/2.5 |
| 構成 | 同process（構成合意＝ユーザー最重要関門） | `mbticode_tone.md` 記事構成定型 | `/vivant-article` Step 1 | `writing_note_structure.md`（3視点・導入3要素・H2/結論）・`/note-article` Step 3 |
| 本文 | 同process（4,000字以上・テーブル禁止・語尾3種・Note貼付記法・2026-07-10執筆ルール） | `mbticode_tone.md`（語尾表・禁止記号・記号フォーマット・自己開示型・N定型・CTA） | `/vivant-article` Step 2（一文一段落・柔らか語尾・NG定型・リンク形式）・`examples_essay.md`・`rules/project_vivant_content_policy.md` | `writing_core.md`（5大ルール・PASONA・句読点・AI臭さ除去）・`writing_expressions.md`・`personal_data.md`（捏造禁止） |
| 機械QA | `brands/tools/qa_article.py` | 同左（`--paid`） | 同左（vivant冒頭blockquote検知あり） | 層1〜6（下記3章） |
| LLMチェック | process「AI臭さ除去3軸」（3行） | `/note-article` Step 4完了後チェックリスト・`mbticode_tone.md` 照合チェックリスト・`/quality-guardrail` | `/vivant-article` Step 3 品質チェック（最も詳細） | `docs/reference/note_asset_check_prompt.md`（任意・資産性）・`/notekaigi`（任意） |
| 保存 | `drafts/` 直下 | `articles/drafts/`＋管理ヘッダー | `articles/drafts/` | `rules/feedback_note_article_draft_save.md`（保存必須・生成しっぱなし禁止） |
| 公開後 | `articles/note_article_index.md` | `/note-article` Step 6（published移設＋index） | `/vivant-article` Step 5 | `brands/CLAUDE.md` ルール5（drafts削除前にpublished確認） |

---

## 2. 資産一覧（種別・カバー範囲・強制力）

強制力の凡例：**機械**＝qa_article.pyが検知／**手順**＝スキルのStepとして必ず通る／**LLM**＝チェックリスト項目として人間・AIが判断／**任意**＝呼び出した時だけ／**メモリ**＝メモリにしかなく記事生成時に自動では効かない

### 2-1. スキル（`.claude/commands/`）

| スキル | 役割 | 対象 | 強制力 |
|---|---|---|---|
| `/note-article` | ペルソナ→SEO→タイトル→構成→本文→保存→公開後の一貫フロー | MBTICODE中心・s4lvはprocess参照 | 手順 |
| `/vivant-theme` → `/vivant-article` | vivant専用の2段フロー。Step 3品質チェックが最も網羅的 | vivant | 手順 |
| `/junk-theme` → `/junk-article` | junk_juice専用（文体2層：エピソード口語／鉄則ですます） | junk_juice | 手順（トーン基準適用外） |
| `/quality-guardrail` | AIっぽさ添削（ヘッジ・説教・相槌の書き直し） | **SNS投稿設計**（cheatsheet上に重ねる前提） | SOP上はNoteにも使えと記載（後述の矛盾3） |
| `/notekaigi` | 5人格の戦略会議。テーマ・価格・方針転換 | 全 | 任意（戦略判断・スキル改変時は必須：`docs/rules/feedback_notekaigi_timing.md`） |
| `/content-scan` | 記事から読者の疑問・無意識の前提を抽出→次テーマ | 全 | 任意 |
| `/monetize-kaigi` | アフィリ収益最適化会議 | ブログ向け | 任意（Note記事にはほぼ未使用） |
| `/seo-check` | URL×KWのSEO診断 | ブログ向け（Note URLにも適用可） | 任意 |
| `/mbticode-content-pipeline` | published記事→SNSネタ | MBTICODE | 下流（制作ではない） |

### 2-2. ライティング原則（`brands/writing/`・全アカウント共通）

| ファイル | 内容 | 強制力 |
|---|---|---|
| `writing_core.md` | 5大ルール・PASONA・親近感8手法・**句読点ルール**・**AI臭さ除去（層4〜6の正・2026-09-03）** | 手順で参照＋一部機械 |
| `writing_headlines.md` | ケープルズ見出し5原則・チェックリスト | LLM |
| `writing_note_structure.md` | 3視点構造・導入3要素（痛み/ベネフィット/フック）・H2設計・結論（1アクション＋隙） | LLM |
| `writing_expressions.md` | 表現パターン辞典（問題/欲求/問い/好奇心/ギャップ/対比/注意） | 参照のみ |

### 2-3. アカウント別ルール

**s4lv（`brands/s4lv/`）**

| ファイル | 内容 |
|---|---|
| `rules/project_s4lv_note_article_process.md` | 無料7ステップ・有料3フェーズ・タイトル95点・**AI臭さ除去3軸**（語尾3種／──禁止・リスト後に肌感覚／謙虚と自信の共存）・Note貼付記法・平易化・2026-07-10執筆ルール（検索クエリ直書き禁止／実績過去形単独禁止／H3は2本以上／引用は文字数比／配布プロンプトは実テスト） |
| `rules/project_s4lv_identity.md` | 謙虚な実力者・包容力のある断言・命令口調禁止・なまいきくん流（謙虚な毒） |
| `rules/project_s4lv_accounts.md` | 1アカウント統一・**トーンはカジュアル・親しみやすさ優先（2026-08-19）**・経歴ドラマ排除・数字非表示（プロフィール） |
| `rules/project_s4lv_persona.md` | 3軸ペルソナ・「隣で一緒に確認してくれる距離感」 |
| `rules/project_s4lv_operation_system.md` | 役割分担（構成合意＝ユーザー／本文＝Claude：執筆→AI臭さ除去→qa→保存）・依頼プロンプト定型 |
| `shared/personal_data.md`・`profile.md`・`articles/note_article_index.md` | 実績・開示ルール・公開一覧 |

**MBTICODE（`brands/`・`brands/mbticode/`）**

| ファイル | 内容 |
|---|---|
| `mbticode_tone.md` | **Note専用文体**：語尾表（んです／でした／じゃない／けど／てしまう／だは3回以内）・禁止記号（""・──・ではない・でも）・記号フォーマット（①②③・「・」・blockquote・太字は核心のみ・1文短く・段落間空行）・自己開示6段・有料構成定型・N定型・感謝文・CTA・わかりやすさ・照合チェックリスト |
| `mbticode_strategy.md`・`persona_core.md`・`personal_data.md` | ゴール・ターゲット・3軸ペルソナ・実体験DB |
| `rules/project_mbticode_note_title_seo.md` | 感情系検索語句をタイトルに |
| `rules/project_mbticode_article_themes.md` | 無料・有料テーマ優先順位 |
| `rules/feedback_note_article_draft_save.md` | 保存必須 |
| `rules/project_mbticode_paid_article_sales_factor.md` | 行動テンプレート型が購買要因（仮説） |
| `rules/project_mbticode_no_new_sales_process_0705.md` | 新工程・エージェント新設は不要と判断（2026-07-05・規模変化で再検討） |

**vivant（`vivant/`）**

| ファイル | 内容 |
|---|---|
| `profile.md` | ですます・観察者視点・温かみ・断定回避・「〜ですね／〜でしょうか」で読者と共有 |
| `examples_essay.md` | 型のみ流用・言い回し禁止・**NG：読者反応の決めつけ／身体反応の誇張／裏取りプロセスの露出** |
| `rules/project_vivant_content_policy.md` | 情報ベース（捏造禁止の代替）・事実描写の精度・根拠の時系列確認 |
| `rules/project_vivant_free_article_length_0801.md` | 下限2,500字・上限なし |
| `.claude/commands/vivant-article.md` Step 2/3 | 一文一段落厳格・柔らか語尾3〜5箇所・「〜の域を出ません」禁止・数字＋説禁止・AIっぽい定型描写（時間経過演出／取ってつけた接続語／自問自答締め）・深刻度ミスマッチ・リンクは裸URL |

### 2-4. 機械検品（`brands/tools/qa_article.py`）

| 層 | 内容 | 判定 |
|---|---|---|
| 1 | いかがでしたか／以上のように・まとめると／──・——／個人差があります・一概には | ERROR |
| 2 | ことが大切です・重要です／お勧めします／このように、／いかがでしょうか／数字＋説／疑問文の「か。」 | WARN |
| 3 | Note貼付で崩れる記法（`- `・空`>`・note.comのMDリンク・太字と括弧の隣接・`%**`） | WARN |
| 構造 | 同一語尾4連続／読点3つ以上／2,000字超で見出しなし／H2直下のH3単独／冒頭に問いなし／CTA数／保存先／vivant冒頭blockquote | WARN（vivantはERROR） |
| 4 | 制作側用語（感情トリガー／再現性シグナル／ベネフィット／フック／ペルソナ／PASONA／CTA／権威性／網羅性／即時性／エンゲージメント／FW） | WARN |
| 5 | 過去記事と20字以上一致（`CROSS_DUP_IGNORE`で定型除外） | WARN |
| 6 | 記事内で同一文2回以上／言い直し（4gram重なり0.70以上） | WARN |

### 2-5. レビュー用プロンプト・会議

| 資産 | 視点 | 忖度 | 強制力 |
|---|---|---|---|
| `docs/reference/note_asset_check_prompt.md` | 迫×コトラー（資産性・導線・LTV） | 禁止・減点方式 | 任意 |
| `/notekaigi` | CEO・コトラー・リサーチャー・Noteマネタイザー・AIエージェント | 同意だけ禁止 | 任意 |
| `/quality-guardrail` | 構文レベルの薄さ | — | SNS設計 |
| `/content-scan` | 読者の疑問・前提 | — | 任意 |

### 2-6. SOP・索引

| ファイル | 内容 |
|---|---|
| `docs/sop/sop_note_article.md` | MBTICODE／s4lv手順・完了条件（drafts保存＋qa ERROR 0）・出力見本 |
| `docs/business_inventory.md` I1／I3／I4 | 完了条件・QA手段 |
| `docs/sop/運用マスターシート.md`・`超わかりやすい運用ガイド.md` | 入口。マスターシートは「`/quality-guardrail`＝Note記事・投稿のAIっぽさ検出」と記載 |
| `docs/sop/sop_agent_delegation.md` | **article-writer（Note本文生成の実行部隊）展開が「今月中」の未着手項目** |

### 2-7. エージェント（`.claude/agents/`）

`post-writer`・`shira-rewriter` のみ。**Note記事用のエージェントは書き手・審査ともに未作成。**

### 2-8. メモリ（記事生成時に自動では効かないもの）

| メモリ | 内容 | repo反映 |
|---|---|---|
| `feedback_note_article_ai_tone_checks_0903` | 層4〜6 | 済（writing_core・qa_article） |
| `feedback_kutouten_kihon_rule_0903` | 句読点 | 済 |
| `feedback_avoid_section_word_ai_tone_0901` | 「セクション」不使用 | **shira_noteのみ機械化。Note側は未反映** |
| `feedback_note_article_kousei_teiji_hikkasu_0831` | 構成合意を飛ばさない | `/note-article` Step 3承認として存在 |
| `feedback_examples_file_pattern_not_phrasebank` | 見本の言い回し流用禁止 | vivant・mbticode_tone照合に反映。s4lvは未明文化 |
| `feedback_mbticode_note_no_phrase_reuse_0729` | 既存記事の核心フレーズ流用禁止 | mbticode_tone照合に反映 |
| `feedback_vivant_article_opening_pattern_variety_0815` | 導入部の型が毎回同じ | vivant-articleに一部。機械検知なし |
| `feedback_surface_level_fix_vs_root_logic`・`feedback_apply_rules_exhaustively` | 字面でなくロジック／通し適用 | 行動規範（CLAUDE.md） |
| **s4lvトーン基準10項目（2026-09-04サンプル調整で確定）** | 口語化・語尾の段落末分散・2〜4文塊＋全角スペースの一拍・寄り添い一言・「正直に言うと」1回・冒頭ベネフィット言い切り・断言のメリハリ・読点・引用枠内は（1）表記・前提の順序 | **反映済（`brands/writing/writing_tone.md`・2026-09-04 Step 1）** |

---

## 3. トーン／AIっぽさ／改行ルールの所在マップ

| 観点 | 今どこにあるか | 強制力 | 備考 |
|---|---|---|---|
| AI定型表現（いかが／まとめると／──／個人差／大切／お勧め） | writing_core AI臭さ章＋qa層1〜2 | 機械 | 全アカウント |
| 制作側用語の本文流入 | writing_core＋qa層4 | 機械WARN | 全 |
| 過去記事／記事内の重複 | writing_core＋qa層5〜6 | 機械WARN | 型の重複（導入の構造が同じ等）は取れない |
| 語尾4連続 | s4lv process 3軸＋qa | 機械WARN | 「4連続でなければ単調でない」ではない（vivant-articleが明記） |
| 句読点（か？／読点2つ） | writing_core＋qa | 機械WARN | 全 |
| 「〜と思います」「〜ですね」「〜でしょう」「〜しましょう」 | quality-guardrail Step 1 → **qa_post.py**のみ | Note側は機械化なし | 実際に「多いと思います」がs4lv記事に混入していた |
| 「セクション」不使用 | メモリ＋shira qa_draft | Note側なし | |
| 語尾のバリエーション | s4lv「3種混在」／vivant「柔らか語尾3〜5箇所」／mbticode「語尾表・だ3回以内」 | LLM | **定義が3系統** |
| じゃない／けど／んです | mbticode_tone | LLM | mbticodeのみ明文化。s4lvは今回のサンプルで採用済みだが未記載 |
| 段落・改行 | s4lv「1〜2文ごと」／vivant「一文一段落厳格」／mbticode「1文短く・段落間空行」／**今回s4lv「2〜4文の塊＋節目に一拍」** | LLM | **正面衝突**（下記4章） |
| 全角スペース行での一拍 | なし | なし | 今回確定・未反映。引用枠内の`>　`だけ既存 |
| 口語化（だからこそ→だから／文頭「これ、」禁止／「ものさし」禁止／「渡します」回避） | なし | なし | 今回確定・未反映 |
| 寄り添い一言／「正直に言うと」は1回 | なし | なし | 今回確定・未反映 |
| 冒頭フック／ベネフィット言い切り | writing_note_structure 導入3要素／s4lv process／vivant-article／mbticode_tone照合 | LLM | 4箇所に分散 |
| 読者反応・記憶の決めつけNG／身体反応の誇張NG | vivant examples_essay | LLM | vivantのみ。全アカウントに当てはまる |
| 「〜の域を出ません」／AIっぽい定型描写（時間経過演出・取ってつけた接続語・自問自答締め） | vivant-article Step 3 | LLM | vivantのみ。全アカウントに当てはまる |
| 見本フレーズ流用禁止 | examples_essay冒頭／mbticode_tone照合／メモリ | LLM | s4lvは未明文化 |
| 検索クエリの直書き禁止 | s4lv process | LLM | s4lvのみ |
| 謙虚な職人／包容力のある断言 | s4lv identity・accounts | LLM | s4lvのみ |
| 一発逆転ストーリー必須 | writing_core親近感8手法／mbticode_tone自己開示6段 | LLM | s4lvは今回サンプルで失敗談を削ったが、識別上は残す想定 |

---

## 4. 重複・矛盾

| # | 内容 | 影響 |
|---|---|---|
| 1 | **改行ルールが4種類**：s4lv 1〜2文／vivant 一文一段落厳格／mbticode 1文短く／今回s4lv 2〜4文の塊＋一拍 | vivantの厳格ルールと今回の塊ルールは正反対。共通基準を決めないと審査員が判定できない |
| 2 | **語尾ルールが3系統**（3種混在／柔らか語尾3〜5箇所／語尾表＋だ3回） | 「単調にしない」は共通だが基準値が別。ルーブリックで共通核＋アカウント上書きに整理が要る |
| 3 | **`/quality-guardrail`はSNS設計**なのに、`sop_note_article.md`・`運用マスターシート.md`はNote記事にも使えと記載。Step 1の機械化先は`qa_post.py`で`qa_article.py`ではなく、Step 2は`persona_core.md`（MBTICODE）前提 | Note用のAIっぽさLLM審査が**実質存在しない**（s4lv processの「3軸」3行が代替） |
| 4 | **AI臭さルールの所在が4箇所**（writing_core AI臭さ章／quality-guardrail／s4lv process 3軸／vivant-article Step 3） | 同じ趣旨を別の言葉で書いている。正を1つにする |
| 5 | **「〜でしょう」の扱いが正反対**：guardrail（SNS）は禁止／vivant profileは推奨／s4lv今回は「逃げでなければ可」 | アカウント別上書きとして明示しないと審査員が誤判定する |
| 6 | **タイトル基準の呼び名と本文禁止語が同じ**：`title_scoring.md`の「感情トリガー／再現性シグナル／ベネフィット」が、本文では層4のWARN語 | 「内部ルーブリックの用語としては可、読者向け本文では不可」と書き分けが要る |
| 7 | **article-writer（書き手）が計画のみ未着手**（`sop_agent_delegation.md`「今月中」） | 今回作る審査エージェントとは役割が別（書く／審査する）。両方作るか、審査だけ先行かを決める |
| 8 | **本文完成後のチェック工程がアカウントごとに別実装**：`/note-article` Step 4完了後はMBTICODE専用、s4lvはprocess、vivantはvivant-article Step 3 | 審査ゲートを1箇所に置くには、各スキルの該当Stepから共通の審査を呼ぶ形にする必要がある |
| 9 | `project_mbticode_no_new_sales_process_0705.md`が「新エージェント不要」と判断（販売促進目的） | 今回の審査エージェントは品質目的で別論点だが、同メモリとの関係を1行書いておくと後で混乱しない |

---

## 5. 空白（ルールがない／強制されていない）

| # | 空白 | 現状 |
|---|---|---|
| 1 | s4lvトーン基準10項目 | repo未反映（本棚卸しの2-8参照） |
| 2 | Note記事向けのAIっぽさLLM審査工程 | guardrailはSNS、資産化チェックは任意、notekaigiは戦略 → **文章品質を忖度なしで審査する工程が無い** |
| 3 | 「〜と思います」「〜ですね」「〜しましょう」等のNote側機械検知 | qa_post.pyのみ |
| 4 | 「セクション」不使用のNote側機械検知 | メモリのみ |
| 5 | 導入部の「型の重複」（構造が毎回同じ）の検知 | 層5は20字一致のみ |
| 6 | 段落・改行の共通基準 | アカウントごとに別・矛盾 |
| 7 | 親近感の具体的な書き方（読者の内心を代弁→寄り添い一言、等） | writing_core親近感8手法は抽象。今回の実例が唯一 |
| 8 | 読者反応の決めつけNG・AIっぽい定型描写NGの全アカウント化 | vivantのみに存在 |
| 9 | 見本フレーズ流用禁止のs4lv明文化 | vivant・mbticodeのみ |

---

## 6. Step 1（正式化）・Step 2（審査）への含意

### Step 1：トーン基準の正式化
- 新規 `brands/writing/writing_tone.md` を作り、**共通核（全アカウント）＋アカウント別上書き（s4lv／MBTICODE／vivant）の2層**にする。junk_juiceは対象外と明記
- 共通核：口語化の禁止語・語尾を段落末で散らす・段落の塊と一拍（全角スペース行）・寄り添い一言・「正直に言うと」1回・冒頭ベネフィット言い切り・断言のメリハリ・読者反応の決めつけNG・AIっぽい定型描写NG・見本流用禁止
- 上書きで解消する矛盾：改行（vivantの一文一段落を残すか塊に寄せるか）／語尾の基準値／「〜でしょう」の可否／じゃない・けどの採否
- `/quality-guardrail`のNote相当は writing_tone に吸収し、SOP・マスターシートの「guardrail＝Note記事にも」記載を修正
- `qa_article.py` に追加：「〜と思います」「〜ですね」「〜しましょう」（WARN）・「セクション」（WARN）
- `title_scoring.md` に「基準名は内部用語。本文では層4の言い換えを使う」の1行

### Step 2：審査エージェント＋ルーブリック
- ルーブリック＝ writing_tone（共通核＋上書き）＋ writing_core AI臭さ章 ＋ qa_article.py結果 の3点セット
- `note-ai-reviewer` は「本文完成→drafts保存前」の必須ゲート。`/note-article` Step 4完了後・`/vivant-article` Step 3 から共通で呼ぶ
- article-writer（書き手）とは分離。審査だけ先行し、書き手エージェント化は別判断
- 忖度なし・減点方式・`file:line`付き指摘は `note_asset_check_prompt.md` の設計を踏襲

---

## 7. Step 1 実施記録（2026-09-04）

オーナー裁定4点（段落は全アカウント「2〜4文の塊＋一拍」／「〜でしょう」はアカウント別上書き／`/quality-guardrail`のNote相当は新ファイルへ吸収／審査エージェントは書き手と分離）を受けて実施。

| 変更 | ファイル |
|---|---|
| 新設：共通核11項目＋アカウント別上書き（s4lv／MBTICODE／vivant）＋機械検知対応表 | `brands/writing/writing_tone.md` |
| 機械検知 層7追加：`tone-omoimasu`（と思います／感じています）・`tone-shimashou`・`tone-section`・`tone-desune`（vivant除外） | `brands/tools/qa_article.py` |
| 矛盾1解消：「一文一段落厳格」廃止→塊＋一拍 | `.claude/commands/vivant-article.md` |
| 矛盾1解消：「1文短く・段落間空行」→塊＋一拍。共通核への参照追加 | `brands/mbticode_tone.md` |
| 矛盾1・4解消：「1〜2文ごと改行」→塊＋一拍。3軸は writing_tone に統合と明記 | `brands/s4lv/rules/project_s4lv_note_article_process.md` |
| 参照追加：実行前準備・Step 4適用ルールに writing_tone | `.claude/commands/note-article.md` |
| 矛盾3解消：`/quality-guardrail`→writing_tone照合に差し替え | `docs/sop/sop_note_article.md`・`docs/sop/運用マスターシート.md`・`docs/business_inventory.md` |
| 矛盾6解消：基準名は内部用語、本文では言い換え | `docs/rubrics/title_scoring.md` |

解消した空白：1（s4lv10項目）・3（と思います等の機械検知）・4（セクション）・6（段落共通基準）・7（寄り添いの書き方）・8（決めつけNG・定型描写NGの全アカウント化）・9（見本流用禁止のs4lv明文化）。
残る空白：2（Note用LLM審査工程→Step 2）・5（導入部の型の重複検知→審査員のLLM判断で対応）。
残る矛盾：2（語尾の基準値はアカウント上書きとして併存させた＝解消でなく整理）・7（article-writerは別判断）・8（各スキルの本文完成後チェックから共通審査を呼ぶ形はStep 2で実装）。

検証：`py_compile` OK。s4lv・MBTICODE記事は新チェックに触れず、vivant公開記事09で「と思います」1件を検知、vivantの「ですね」は除外どおり非検知。

### Step 2 実施記録（2026-09-04）

| 変更 | ファイル |
|---|---|
| 新設：審査ルーブリック（重大度 BLOCK／FIX／NOTE・採点項目 A〜J・出力フォーマット固定・忖度禁止） | `brands/writing/note_review_rubric.md` |
| 新設：審査部隊エージェント（Read/Grep/Glob/PowerShellのみ・Edit/Write なし・sonnet/high） | `.claude/agents/note-ai-reviewer.md` |
| 新設：手動起動スキル `/note-shinsa <パス> [--paid] [--round N]` | `.claude/commands/note-shinsa.md` |
| 必須ゲート組み込み：Step 4.5（保存→審査→PASSまで本文非表示→FAILは修正・再審査2巡まで） | `.claude/commands/note-article.md` |
| 必須ゲート組み込み：Step 3.5（同上・vivant上書き付き） | `.claude/commands/vivant-article.md` |
| 手順5を審査委譲に置換 | `brands/s4lv/rules/project_s4lv_note_article_process.md`・`docs/sop/sop_note_article.md`・`docs/business_inventory.md` |

**検証（初回2本は general-purpose に定義ファイルを読ませて実行。その後、型 `note-ai-reviewer` が同セッション内で登録されたため、本来の型で確認実行を追加）**

| 対象 | 想定 | 結果 | 所見 |
|---|---|---|---|
| vivant 公開記事09（旧ルールで執筆） | FAIL | **FAIL（FIX 6／NOTE 2）** | 「と思います」・直近記事10との導入/結び/人物紹介の同型・裏取り露出（vivant上書き）・旧一文一段落を新ルールで指摘。行番号＋引用＋直し方＋根拠が全件揃う |
| s4lv タイトル診断（本日トーン調整済み） | PASS | **FAIL（FIX 5／NOTE 7）** | トーン（D/E/G）はほぼ通過。落ちたのは **H：同じ主張の言い直し3回×2組**（qa層6が取れない語彙違いの反復）と **F：ベネフィットが冒頭300字内にない**（570字地点）。さらに段落末「です」3連続（ユーザー自身の最終編集で混入）を検知 |
| s4lv タイトル診断（同上・**本来の型 `note-ai-reviewer` で再実行**） | — | **FAIL（FIX 3／NOTE 4）** | ツール制限下（Edit/Writeなし・PowerShell）で qa→採点→固定形式まで完走。F（300字）・H（反復）・「です」3連続・締めの同型は general-purpose 実行と一致＝核の指摘は安定。差分：s4lv上書き「検索クエリの直書き禁止」（L47）を追加検知、「です」3連続と締め同型は NOTE に降格 |

再現性の所見：同一記事を2回審査して**核の指摘（F・H）は一致**、境界的な項目（段落末3連続・締めの同型）で FIX／NOTE の判定が揺れる。判定を固定したい項目は rubric 側で「〜連続はFIX」と閾値を明記すれば揺れは消える（未実施・オーナー判断）。L47の検索クエリ指摘は「読者の行動描写としての引用」か「クエリの直書き」かの解釈が分かれる箇所。

**ゲートループの実走（同日・オーナー「今直す」裁定後）**：rubric D に閾値「段落末同一語尾3段落連続＝FIX／2連続＝NOTE」を追加（オーナー委任で決定。締めの型の重複は s4lv の意図的CTA設計と衝突するため閾値化せず）。1巡目 FAIL（FIX 3：冒頭300字にベネフィット／主張の反復／検索クエリ直書き）→修正→2巡目 FAIL（新規 FIX 2：「です。」4ブロック連続の再発／口語化漏れ5箇所）→修正→**3巡目 PASS（NOTE 6）**。各指摘は2巡以内で解消し、ループは3巡で収束。審査員は「前回#nの対応：解消／未解消」を項目ごとに追跡し、プロンプト枠内の「ではなく」を対象外と正しく判定した。残る NOTE（導入の問いかけ型が直近3記事で連続／結びが affiliate 記事と同型・同一URL／L15-17「ます」2連続／L51-53 近接言い直し）は非ブロックで据え置き。

想定が外れた理由：本日の調整は「トーン」だけを人手で合わせたもので、ルーブリックは独自性・反復・導入300字も見る。**審査員が、時間をかけて調整した記事でも忖度せず落とした**＝設計どおり。s4lv記事の5件を直すかはオーナー判断（記録のみ）。

残る空白2（Note用LLM審査工程）・矛盾8（各スキルからの共通審査呼び出し）は解消。矛盾7（article-writer）は引き続き別判断。

## 付録：本棚卸しで読んだ範囲

`.claude/commands/`（note-article・vivant-theme・vivant-article・junk-theme・junk-article・quality-guardrail・notekaigi・monetize-kaigi・seo-check・content-scan・mbticode-content-pipeline）／`brands/writing/` 4本／`brands/mbticode_tone.md`・`mbticode_strategy.md`／`brands/mbticode/`（persona_core・rules 6本）／`brands/s4lv/rules/`（process・identity・accounts・persona・operation_system）／`vivant/`（CLAUDE・profile・examples_essay・rules 3本）／`brands/tools/qa_article.py`／`docs/`（sop_note_article・business_inventory・運用マスターシート・超わかりやすい運用ガイド・sop_agent_delegation・note_asset_check_prompt・title_scoring・feedback_notekaigi_timing）／`.claude/agents/`／メモリ索引。
