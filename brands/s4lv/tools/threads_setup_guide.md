# s4lv Threads自動投稿の仕組み

s4lv（Threads @cfrms4lv）の投稿を、スプレッドシートに入れておくと自動で投稿する仕組みの説明。投稿の決まりは `rules/threads_post_generation_rules.md`、作る手順は `.claude/commands/s4lv-post.md`。Xは自動化の対象外（手で投稿する）。

---

## 1. 全体の形

```
[Claude Code ローカル]                     [Google クラウド]                [Meta]
 /s4lv-post で投稿を作る                     Googleスプレッドシート
  → qa_post.py 検品                          ├ 投稿キュー（予定管理）
  → posts_threads.txt 保存                   ├ 設定（トークン投入用・実行後自動消去）
  → queue_from_posts.py ──Sheets API──►      ├ インサイト（数値蓄積）
                                             └ 日次観測ログ
  fetch_insights.py ◄──Sheets API──          Apps Script (threads_scheduler.gs)
  （分析用の読み取り）                        ├ postScheduled  15分おき ──Graph API──► Threads
                                             ├ collectInsights 23:30 ◄─インサイト取得
                                             ├ dailyObservationLog 23:35
                                             ├ syncDataToGitHub 23:40 ──► GitHubリポジトリ
                                             ├ checkHealth 23:45（異常時のみメール通知）
                                             └ refreshToken 毎週月曜07:00（トークン自動更新）
```

- **PCに頼らない**：投稿・数字の回収・監視・トークン更新は、すべてApps Script側で動く。PCを閉じていても動く
- **投稿API**：Threads公式のGraph API（コンテナ作成→公開の2段階）。自己リプライは、最大4本までつなげて投稿できる
- **`postScheduled()` は15分おきに動き、「予定時刻を過ぎた、まだ投稿していない行」を全部処理する**。実際の投稿時刻は、キューの「投稿日時」の列で決まる。枠は 07:30／12:00／21:30
- ブラウザの自動操作は、ThreadsもXもタイムアウトでできない（提案しない）
- アプリは、既存のVIVANTアプリに `@cfrms4lv` をテスターとして追加した形で動いている（s4lv専用のアプリは作っていない）。`app_secret` は「VIVANTアプリのThreadsのapp secret」を使う
- Sheets APIのサービスアカウントは、MBTICODE・vivantと同じもの（`mbticode-sheets-writer@avian-computer-503518-f6.iam.gserviceaccount.com`）を使い回している

## 2. スプレッドシートの構成（列の順番は絶対に変えない）

| タブ | 列 |
|---|---|
| Threads投稿キュー | 投稿日時 \| 本文 \| リプライ1本文 \| リプライ2本文 \| リプライ3本文 \| リプライ4本文 \| 型 \| FW \| ステータス \| 投稿ID \| リプライ1投稿ID \| リプライ2投稿ID \| リプライ3投稿ID \| リプライ4投稿ID \| **トピック**（15列目。Threadsのトピック。メインの投稿にだけ付く。空でもよい） |
| 設定 | B1=access_token・B2=threads_user_id・B3=github_token（`setup()` を実行すると自動で消える） |
| インサイト | 投稿ID \| 投稿日時 \| 型 \| FW \| Views \| Likes \| Replies \| Reposts \| Quotes \| 取得日時 |
| 日次観測ログ | 日付をキーにして上書きされる集計 |

- 列を足すときは必ず「挿入」を使い、`threads_scheduler.gs` の冒頭のコメントと合わせる（ずれるとスクリプトが誤動作する）
- **列の構成やApps Scriptを変えたら、Apps Scriptのエディタへ手で貼り直す**（Sheets API経由では反映されない）
- FWの列（人が見るための短いラベル）は空で入る。要るときは、シートの側で手で入れる

## 3. 道具の一覧（`brands/s4lv/tools/`）

| ファイル | 役割 |
|---|---|
| `threads_scheduler.gs` | Apps Scriptの本体（クラウド側の全機能）。スプレッドシートに貼り付けて使う |
| `queue_from_posts.py <posts_threads.txt> <日付…>` | 投稿ファイルからキューへ入れる。機械チェック → CSV作成 → 投入 → 照合までを一度に行う。`--dry-run` で、投入の前まで確かめられる |
| `push_threads_queue.py <csv>` | CSVをキューへ入れる。過去の時刻は飛ばす・同じ日時は飛ばす・入れたあとに日時の順へ並べ直す |
| `verify_queue_matches_file.py` | `posts_threads.txt` とキューが同じ内容かを確かめる |
| `update_threads_queue_body.py` | すでに入れた投稿の本文・リプライ・型を、シートへ反映し直す |
| `withdraw_posted_row.py "YYYY-MM-DD HH:MM"` | Threadsの側で手で消した投稿の後始末（投稿IDの列だけ空にする） |
| `fetch_insights.py` | インサイトのタブを読む（分析用） |
| `fetch_past_posts.py` | 投稿済みのデータを取る |
| `check_analysis_due.py` | 前回の分析から7日を超えたら `[REMINDER]` を出す |
| `check_queue_coverage.py` | キューの残りが3日分を切ったら `[REMINDER]` を出す |
| `threads_connect_test.ps1` | つながるかの確認と、1本だけの試し投稿 |
| `sheets_config.json` | スプレッドシートのIDなど（秘密ではない。gitで管理） |
| `threads_auth.local.json` | Threadsのトークン（**gitに入れない。チャットに貼らない**） |
| `sheets_service_account.local.json` | Sheets APIの鍵（gitに入れない） |
| `threads_analysis_log.json` | 分析をした日の記録 |

## 4. ふだんの流れ

1. `/s4lv-post` で投稿を作り、`posts/posts_threads.txt` の末尾に足す
2. `queue_from_posts.py` でキューへ入れる
3. あとは自動で投稿される
4. 数字は毎晩自動で回収される。分析するときは `fetch_insights.py` で読み、結果を `tools/s4lv_threads_insights_notes_*.md` に書いて、`threads_analysis_log.json` を更新する
5. 異常があるときだけ、`checkHealth` がメールで知らせる。何も来なければ正常

## 5. 過去の障害と落とし穴

- **トリガーが早く動く**（2026-08-23に直した）：07:30などの1日1回のトリガーは、数分早く動くことがあり、その日の投稿が拾われなかった。15分おきに動くトリガー1本に変えてある
- **当日の枠に入れるときは、本文を確定させてから入れる**：15分おきに、時刻を過ぎた分が投稿される。2026-09-10に、確定する前の本文が先に投稿された
- **投稿日時は、枠の時刻（07:30／12:00／21:30）にそろえる**
- **トークンの更新は、Apps Script側の月曜07:00だけ**：ローカルでも更新すると、2つの系統がずれて投稿に失敗する（2026-07-26にMBTICODEで起きた）。ローカルで更新する仕組みは作らない
- **トークンをチャットに貼らない**：設定のタブからだけ入れる。スクリプトは、エラーのときに生の応答を出さない作りにしてある
- Insights APIの `metric` パラメータは単数形（`metrics` だと400エラー）
- **スプレッドシートへ手でコピペしない**：セルの中の改行で行が割れる。必ず道具で入れる
- **ステータスの列を直接書き換えない**：もう一度投稿される事故になる。手で消した投稿の後始末は `withdraw_posted_row.py` を使う
- 古い投稿にはURL付きのものがある。`qa_post.py` を `--since` なしで回すと `th-url` のERRORが出るので、新しい分の検品には `--since` を付ける
- Windowsでは、pythonは絶対パス `C:\Users\PC_User\AppData\Local\Python\bin\python.exe` を使う
