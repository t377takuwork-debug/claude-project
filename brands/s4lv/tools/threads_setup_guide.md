# s4lv Threads自動投稿 導入準備ドキュメント（2026-08-18棚卸し）

MBTICODE→vivantで2回稼働実績のあるThreads自動投稿基盤をs4lvへ横展開するための準備資料。
「1. システム棚卸し」で仕組みを、「2. 導入方針」でこれまでの運用判断を、「3. 導入手順」で実作業を定義する。

- 参考実装：`brands/mbticode/tools/`（初代・2026-07-25稼働）、`vivant/tools/`（横展開版・2026-08-02稼働）
- **コピー元はvivant版を使う**（MBTICODE版の障害対応・自動ソート・GitHub同期を全て含む最新形。`withdraw_posted_row.py`等の後発ツールもvivant側にしかない）

---

## 1. システム棚卸し（MBTICODE/vivant基盤の全体像）

### アーキテクチャ

```
[Claude Code ローカル]                     [Google クラウド]                [Meta]
 投稿バッチ生成スキル                        Googleスプレッドシート
  → qa_post.py 検品                          ├ 投稿キュー（予定管理）
  → posts_threads.txt 保存                   ├ 設定（トークン投入用・実行後自動消去）
  → push_threads_queue.py ──Sheets API──►    ├ インサイト（数値蓄積）
                                             └ 日次観測ログ
  fetch_insights.py ◄──Sheets API──          Apps Script (threads_scheduler.gs)
  （週次分析用の読み取り）                    ├ postScheduled  定時投稿 ──Graph API──► Threads
                                             ├ collectInsights 23:30 ◄─インサイト取得
                                             ├ dailyObservationLog 23:35
                                             ├ syncDataToGitHub 23:40 ──► GitHubリポジトリ
                                             ├ checkHealth 23:45（異常時のみメール通知）
                                             └ refreshToken 毎週月曜07:00（トークン自動更新）
```

- **PC非依存**：投稿・数値回収・監視・トークン更新はすべてApps Script側で常駐実行。ローカルPCの起動状態に関係なく動く（ブラウザ自動化はThreads/Xともタイムアウトで不可能と確定済み・提案禁止）
- **投稿API**：Threads公式Graph API 2段階方式（コンテナ作成→公開）。自己リプライも対応
- **`postScheduled()`は「予定時刻を過ぎた未投稿行」を全処理する**設計。トリガー時刻を変えなくても、キューへの投入本数・日時で頻度を自由に制御できる

### スプレッドシート構成（列順は絶対に変えない）

| タブ | 列 |
|---|---|
| Threads投稿キュー | 投稿日時 \| 本文 \| リプライ1本文 \| リプライ2本文 \| リプライ3本文 \| リプライ4本文 \| 型 \| FW \| ステータス \| 投稿ID \| リプライ1投稿ID \| リプライ2投稿ID \| リプライ3投稿ID \| リプライ4投稿ID（2026-08-23、単発リプライ1本→連続スレッド最大4本連鎖へ拡張。リプライ1は本文へ、リプライ2はリプライ1へ、…と順に連鎖投稿する） |
| 設定 | B1=access_token・B2=threads_user_id・B3=github_token（`setup()`実行後に自動消去） |
| インサイト | 投稿ID \| 投稿日時 \| 型 \| FW \| Views \| Likes \| Replies \| Reposts \| Quotes \| 取得日時 |
| 日次観測ログ | 日付キーでupsertされる集計 |

列追加は必ず「挿入」を使い、`threads_scheduler.gs`冒頭コメントと一致させる（ズレるとスクリプト誤動作）。

### ローカルツール一式（vivant/tools/ 基準）

| ファイル | 役割 |
|---|---|
| `threads_scheduler.gs` | Apps Script本体（クラウド側の全機能）。スプレッドシートに貼り付けて使う |
| `push_threads_queue.py <csv>` | CSV→投稿キュー投入。過去時刻スキップ・重複日時スキップ・投入後の日時昇順自動ソート付き |
| `fetch_insights.py` | インサイトタブの読み取り（週次分析用・コピペ不要） |
| `fetch_past_posts.py` | 投稿済みデータの取得 |
| `check_analysis_due.py` | 前回分析から7日超過で`[REMINDER]`を出す安全網 |
| `check_queue_coverage.py` | キュー残量が3日未満で`[REMINDER]`（受け渡し忘れ・生成失敗の検知） |
| `update_threads_queue_body.py` | 保存済み投稿の本文・リプライ・型をシートへ同期 |
| `withdraw_posted_row.py "YYYY-MM-DD HH:MM"` | Threads本体で手動削除した投稿の後始末（投稿ID列のみ空にする。**ステータス列は直接編集禁止**＝再投稿事故防止） |
| `verify_queue_matches_file.py` | posts_threads.txtとキューの一致検証 |
| `threads_connect_test.ps1` | 疎通確認・単発テスト投稿 |
| `sheets_config.json` | spreadsheet_id等（非秘密・git管理） |
| `threads_auth.local.json` | Threadsトークン（**gitignore必須・チャット貼付絶対禁止**） |
| `sheets_service_account.local.json` | Sheets APIサービスアカウント鍵（gitignore必須・既存を複製） |
| `threads_analysis_log.json` | 週次分析の実施日記録 |

### 運用ループ（日次・週次）

1. **バッチ生成**：投稿生成スキル（`/mbticode-post`・`/vivant-post`相当）で事前設計→承認→本文生成→`qa_post.py` ERROR 0件→`posts_threads.txt`へ**追記**保存
2. **キュー投入**：CSV（投稿日時,本文,リプライ1,リプライ2,リプライ3,リプライ4,型,FW。リプライ2〜4は省略可）を作り`push_threads_queue.py`で反映（2026-08-23、連続スレッド最大4本連鎖に対応）
3. **自動投稿**：以降は無人（Apps Scriptトリガー）
4. **週次分析**：`check_analysis_due.py`のリマインドを起点に`fetch_insights.py`→分析→`threads_insights_notes`系ファイルへ「観測／反映」を追記＋`threads_analysis_log.json`更新。**この2点セットを忘れるとループが閉じない**
5. **監視**：`checkHealth`が異常時のみメール通知。何も来なければ正常

### postScheduledトリガーの早発火事故（2026-08-23発見・修正済み）

初回実バッチ（8/23 07:30枠）が投稿されない不具合が発生。「実行数」ログを確認したところ、`postScheduled`が07:30の**4分前（7:26:37）**に発火しており、その時点では`scheduledAt(07:30) > now(7:26)`のため対象なしとして終了していた。07:30/12:00/21:30トリガーは`atHour().nearMinute()`による**1日1回だけの発火**のため、早発火した場合その日の投稿は誰にも拾われずスキップされる（次に同じトリガーが発火するのは翌日）。08/22の実行ログでも同じ7:26:37という早発火が確認できたため、単発の偶然ではなく構造的な問題と判断した。

**修正**：`installTriggers()`を、07:30/12:00/21:30の単発トリガー3本から**15分おきの`postScheduled`ポーリングトリガー1本**へ変更（`threads_scheduler.gs`参照）。実際の投稿時刻はキューの投稿日時列で制御されるため、頻度・時刻設計（1日3本・07:30/12:00/21:30）自体への影響はない。

**対応完了（2026-08-23、ユーザー確認済み）**：①スクリプト再貼り付け ②`installTriggers()`再実行 ③`postScheduled`手動実行、の3点を実施。8/23 07:30分はステータス「投稿済み」・投稿ID`18123010648756382`で反映を確認済み。以降は15分おきポーリングで無人運用に戻る。

### 過去の障害・落とし穴（横展開時に必ず引き継ぐ知見）

- **トークンのドリフト事故（2026-07-26）**：ローカルとApps Scriptが別々に週次リフレッシュして系統がズレ、投稿失敗。**トークン更新はApps Script側の月曜07:00のみが唯一の経路**。ローカルのタスクスケジューラでのリフレッシュは作らない
- **トークン漏洩事故の再発防止**：スクリプトは例外時に生のレスポンスを出力しない実装済み。設定タブ経由でのみ投入し、チャットには絶対に貼らせない
- **Insights APIは`metric`パラメータが単数形必須**（`metrics`だと400）
- **20:30枠の教訓（vivant）**：投稿日時は必ずトリガー時刻のいずれかに揃える。中途半端な時刻に投入すると次トリガーまで遅延する
- **スプレッドシートへの手動コピペ禁止**：セル内改行が行割れする。必ず`push_threads_queue.py`経由
- **Windows注意**：pythonは絶対パス`C:\Users\PC_User\AppData\Local\Python\bin\python.exe`。スクリプト内`sys.stdout.reconfigure(encoding="utf-8")`がないと文字化け

### 発展系（MBTICODEのみ稼働中・s4lv初期導入では見送り）

週次クラウドルーティン（claude.ai上のopus-5が次週21本を自動生成→`_pending_batch.json`→人間がダウンロード→`apply_pending_batch.py`で反映）。クラウド側は構造的に読み取り専用のため「受け渡し」だけ人力が残る。**vivant同様、Phase1-4（生成は会話・投稿は自動）が安定してから検討**。

---

## 2. 導入方針（過去のやり取りから確定しているユーザー意図）

1. **技術基盤は丸ごと流用、投稿設計は流用しない**：vivant横展開時、接続基盤はそのまま使い、投稿の型・頻度はジャンル実データで再検証してから確定した（notekaigi 2回）。s4lvもThreads文体OS（`rules/feedback_s4lv_threads_writing_style.md`）は既にあるが、キュー運用前提の型・頻度・曜日配分は未定義→**投入開始前に軽い戦略会議で確定する**
2. **X自動化は対象外**（ユーザー指示済み）。自動化はThreadsのみ。Xは従来通り`/s4lv-post`手動運用
3. **段階導入**：Phase1-4先行、週次クラウド自動生成は安定後。ルールが実運用で安定してから機械チェックを固める順序（s4lvは`qa_post.py --account s4lv --platform threads`が既に対応済みで、vivantより有利）
4. **qa合格は最低ライン**：保存前に1本ずつ人間目線で読み直す目視確認を省略しない（2026-08-14フィードバック）
5. **実測データが出るまで方針を確定しない**：頻度増・型の入れ替えは4週間程度の観測後に判断
6. **GCP資産は再利用**：サービスアカウント`mbticode-sheets-writer@avian-computer-503518-f6.iam.gserviceaccount.com`を新規発行せず使い回す（MBTICODE→vivantで実績あり）

---

## 3. 導入手順

### Phase A：ユーザー作業（Meta Developer＋スプレッドシート）

`vivant/tools/threads_setup_guide.md`のSTEP 1〜15と完全に同一手順（読み替えのみ）：

- 対象アカウント：**Threads @cfrms4lv**（2026-08-18ユーザー確認：新設・設定中。旧@s4lv24ではない。プロフィール文は`rules/project_s4lv_accounts.md`の確定Threadsプロフィール文を流用し、リンク先はNote https://note.com/salvami77 に設定する）
- STEP 1〜8：Meta Developerアプリ作成（例："s4lv threads bot"）→Threads APIプロダクト追加→@cfrms4lvをテスター登録・スマホで招待承認→短期トークン発行→長期トークンへ交換→threads_user_id確認→`brands/s4lv/tools/threads_auth.local.json`へ保存→`threads_connect_test.ps1`で疎通確認
  - ※s4lv用Facebookアカウントが既存アプリ（MBTICODE/vivant）と同一なら、新規アプリを作らず既存アプリに@cfrms4lvをテスター追加する選択肢もある（トークンはアカウント別に発行される）
- STEP 9〜15：スプレッドシート新規作成（例：「s4lv Threads運用」）→上記サービスアカウントを編集者共有→**スプレッドシートIDをClaudeに伝える**→タブ自動作成後、Apps Scriptに`threads_scheduler.gs`貼り付け→`setup()`→`installTriggers()`
- STEP 16〜24（GitHub同期・任意）：週次分析をクラウドで行う予定ができてからでよい。初期導入では省略可

### Phase B：Claude側作業（スプレッドシートID受領後に実施するチェックリスト）

1. `vivant/tools/`から複製：`threads_scheduler.gs`（vivant固有のトリガー時刻・GITHUB_SYNC_PATH等を書き換え）・`push_threads_queue.py`・`fetch_insights.py`・`fetch_past_posts.py`・`check_analysis_due.py`・`check_queue_coverage.py`・`update_threads_queue_body.py`・`withdraw_posted_row.py`・`verify_queue_matches_file.py`・`threads_connect_test.ps1`（汎用設計のためほぼ無変更で動く実績あり）
2. `sheets_config.json`をs4lvのスプレッドシートIDで新規作成、Sheets API経由で4タブ＋ヘッダー行を自動作成
3. `sheets_service_account.local.json`を複製配置
4. ルート`.gitignore`へ2行追加：`brands/s4lv/tools/threads_auth.local.json`・`brands/s4lv/tools/sheets_service_account.local.json`（**認証ファイル作成より先に行う**）
5. `threads_analysis_log.json`を初期化
6. `brands/s4lv/posts/`を新設し、`posts_threads.txt`を**追記式（投稿日時付き・MBTICODE同形式）**へ変更。`.claude/commands/s4lv-post.md`のStep 6（現行は上書き式）とThreads分の工程（CSV作成→`push_threads_queue.py`投入）を改修
7. トリガー時刻の決定を反映（下記④）
8. E2E確認：疎通テスト→テスト投稿1本→キュー投入→定時投稿→インサイト取得まで

### 開始前の決定事項（2026-08-21確定）

| # | 決定事項 | 確定内容 |
|---|---|---|
| ① | 投稿頻度 | **1日3本**（MBTICODE/vivantと同水準。1本から様子見はせず開始） |
| ② | 投稿設計（型・曜日配分・Note誘導ローテーション） | `/notekaigi`は開かず軽量版で開始。既存X/Threads文体OSの「型・思想6割／AI実働記録4割」比率をそのままThreads3本/日にも適用（**2026-08-23時点で内容面は全面更新済み**：`rules/project_s4lv_persona.md`（ペルソナ）・`rules/feedback_s4lv_threads_writing_style.md`（文体OS全面改訂）・`articles/note_article_index.md`（Note記事基盤の小出し設計）が現在の唯一の正。比率6:4の骨格自体は変更なし） |
| ③ | 自己リプライ（Note誘導URL枠）の使い方 | 既存ルール通り、URLは本文でなく自己リプライ欄。直近4週間未誘導の記事を優先するローテーション（MBTICODE前例踏襲） |
| ④ | トリガー時刻 | **07:30／12:00／21:30**（通勤前チェック→昼休み→夜のブログ作業時間帯というブロガー層の生活導線を想定） |
| ⑤ | 週次クラウド自動生成（Phase5） | 初期導入に含めない（vivant同様。Phase1-4が安定してから検討） |

4週間の実測データが貯まった時点で`/notekaigi`により型・頻度・トリガー時刻を見直す（s4lv全体の運用再検証サイクルと同期。`project_s4lv_notekaigi_reactivation_0819.md`参照）。

### 投稿者本人の返信対応について（2026-08-23追加）

`brands/reference/threads_algorithm_2026.md`の分析により、投稿直後30分〜1時間以内に投稿者本人がリプライへ返信すると拡散が大きく伸びるとされる。現状の自動投稿基盤（投稿しっぱなし）には、この対応が構造的に欠けている。

ユーザーの実働時間は不定期なため、固定の返信専用枠（例：21:30の投稿だけ必ず対応）は設計しない。**手が空いたタイミングで、その日の未返信投稿にまとめて返信するベストエフォート運用**とする。`kpi_weekly_template.md`の「投稿者本人が返信したか」列で記録し、4週間後の`/notekaigi`で反響との相関を確認する。

---

## 4. 完了定義・進捗（2026-08-21時点）

- **Phase A完了**＝`threads_connect_test.ps1`で`[OK] authenticated as: cfrms4lv`＋`setup()`/`installTriggers()`実行済み → **✅完了（2026-08-21）**
  - **重要な変更**：s4lv用に新規Meta Developerアプリを作らず、**既存のVIVANTアプリに`@cfrms4lv`をテスターとして追加**する方式に切り替えた。新規アプリ作成直後は`error_code:1349245`（招待未承認エラー）が解消せず、原因はブラウザのThreadsセッションが`kousatsumemo`（vivant用アカウント）のままだったこと。VIVANTアプリに切り替えてから`cfrms4lv`としてOAuth同意し直して解決。今後の`app_secret`は「VIVANTアプリのThreadsアプリID/Threadsのapp secret」を使用する
- **Phase B完了**＝ツール一式複製・トリガー時刻反映（07:30/12:00/21:30）・スプレッドシート4タブ自動作成・Apps Script `setup()`/`installTriggers()`実行・.gitignore追記 → **✅完了（2026-08-21）**
- **E2Eテスト**＝`threads_connect_test.ps1 -Step post -Confirm2Publish`で実投稿→本人が内容確認→手動削除 → **✅完了（2026-08-21）**
- **Phase B項目6完了（2026-08-22）**：`brands/s4lv/posts/`フォルダ新設（`posts_threads.txt`＝追記式・MBTICODE/vivant同形式のヘッダー付き、`posts_x.txt`＝X自動化対象外のため上書き式のまま、`archive/`＝ローテーション先）。`.claude/commands/s4lv-post.md`のStep 6を「保存（X上書き／Threads追記）」「Step 7：CSV作成→`push_threads_queue.py`投入」「Step 8：完了報告」の3段に分割済み
- **導入完了の最終基準（未達）**＝初回実バッチが`qa_post.py` ERROR 0件で投入され、1週間の無人投稿＋`checkHealth`無通知で稼働

### 連続スレッド（自己リプライ最大4本連鎖）対応・2026-08-23

参考にした高反響投稿分析から、自己リプライを連鎖させて本文を分割する型を追加導入した。スプレッドシート・`push_threads_queue.py`・`update_threads_queue_body.py`・`verify_queue_matches_file.py`・ローカルの`threads_scheduler.gs`は更新済み・動作確認済み（テスト投入→確認→削除で検証済み）。

**✅ Apps Script再貼り付け完了（2026-08-23、ユーザー確認済み）**。スプレッドシート（14列）・Apps Script・ローカルツール（push_threads_queue.py／update_threads_queue_body.py／verify_queue_matches_file.py）の全てが新スキーマで整合済み・動作確認済み。

### 次回セッションで再開する場合
1. まず本ガイドの「4. 完了定義・進捗」を読んで現在地を確認
2. `/s4lv-post`でバッチ生成→Step 6保存→Step 7でCSV化→`push_threads_queue.py`でキュー投入（`rules/project_s4lv_persona.md`・`articles/note_article_index.md`を踏まえること。詳細は`.claude/commands/s4lv-post.md`参照）
3. 1週間、`checkHealth`のメール通知が来ないことを確認して「導入完了」
4. スプレッドシート列構成やApps Scriptを変更した場合は、必ずApps Scriptエディタへの手動再貼り付けが必要（Sheets API経由では反映されない）
