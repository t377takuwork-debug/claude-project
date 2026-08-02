# vivant Threads自動投稿 セットアップガイド（ユーザー作業）

MBTICODEの`brands/mbticode/tools/`と同じ構成をvivantに横展開するための初期セットアップ手順。
STEP 1〜8はMeta Developer側（ブラウザ操作・ユーザーのみ実行可能）、STEP 9〜はGoogleスプレッドシート側。

※Meta Developerサイトの画面文言・導線は時期によって変わることがあります。文言が多少違っても
「Threads API」「テスター」「アクセストークン」に相当する項目を探せば同じ手順です。

## 前提
- vivant用のThreadsアカウント・Facebookアカウントは取得済み
- 参考実装：MBTICODEで同じ手順を実施済み（`brands/mbticode/tools/threads_connect_test.ps1`・`threads_scheduler.gs`冒頭コメント）

## STEP 1: Meta Developerアプリの作成
1. https://developers.facebook.com/ にアクセスし、vivant用に使うFacebookアカウントでログイン
2. 「マイアプリ」→「アプリを作成」
3. アプリの種類は「その他」を選択（特定のユースケースを聞かれたら「アクセス許可のリクエストとデータの管理」等、Threads APIに近いものを選択）
4. アプリ名は分かりやすいもの（例："vivant threads bot"）を入力して作成

## STEP 2: Threads APIプロダクトを追加
1. 作成したアプリのダッシュボードで「プロダクトを追加」
2. 一覧から「Threads」を探して「設定」を押す
3. 左メニューに「Threads API の設定」が出ればOK

## STEP 3: Threadsアカウントをテスターとして登録
1. 「Threads API の設定」内の「テスター管理」（または「ユースケースを設定」）で、vivantのThreadsアカウント（@ハンドル）を追加
2. スマホのThreadsアプリで該当アカウントにログインし、届いた招待を承認する（設定→アカウント→招待、または通知）
   - これを飛ばすと、アプリが未公開（開発中）モードのままそのアカウントを操作できません

## STEP 4: アクセストークンを発行
1. 「Threads API の設定」画面の「アクセストークンを生成」相当のボタンで短期トークンを発行（開発中アプリのテスト用途はこれで足ります）
2. 「設定」→「ベーシック」からApp ID・App Secretも控えておく（STEP 5で使用）

## STEP 5: 長期トークンへ交換
ブラウザのアドレスバーに以下を貼り付けて開く（`APP_SECRET`と`SHORT_LIVED_TOKEN`は実際の値に置換）:
```
https://graph.threads.net/access_token?grant_type=th_exchange_token&client_secret=APP_SECRET&access_token=SHORT_LIVED_TOKEN
```
返ってきたJSONの`access_token`が長期トークン（有効期間は約60日、以後Apps Script側で週次自動更新する運用にします）。

## STEP 6: threads_user_idを確認
```
https://graph.threads.net/v1.0/me?fields=id,username&access_token=長期トークン
```
返ってきた`id`がthreads_user_id。

## STEP 7: 認証情報をローカルファイルへ保存
`vivant/tools/threads_auth.local.json` を新規作成（gitignore対象。**中身は絶対にチャットへ貼らないでください**）:
```json
{
  "access_token": "取得した長期トークン",
  "threads_user_id": "取得したid",
  "app_secret": "APP_SECRET"
}
```

## STEP 8: 疎通確認
```
powershell -ExecutionPolicy Bypass -File vivant\tools\threads_connect_test.ps1
```
`[OK] authenticated as: ...` と出ればSTEP1〜7は完了です。

---

## STEP 9〜: スプレッドシート側のセットアップ

9. Googleスプレッドシートを新規作成（名前は任意。例：「vivant Threads運用」）
10. 共有設定で以下のサービスアカウントを「編集者」として追加（MBTICODEと同じGCPサービスアカウントを再利用。新規発行は不要）:
    ```
    mbticode-sheets-writer@avian-computer-503518-f6.iam.gserviceaccount.com
    ```
11. URL（`https://docs.google.com/spreadsheets/d/【この部分】/edit`）からスプレッドシートIDを控える
12. 「スプレッドシートID: xxxxx」と私に伝えてください → `vivant/tools/sheets_config.json`へ反映し、必要タブ（投稿キュー／設定／インサイト／日次観測ログ）をAPI経由で自動作成します
13. スプレッドシートの「拡張機能」→「Apps Script」を開き、`vivant/tools/threads_scheduler.gs`の中身をエディタへ貼り付けて保存
14. 実行対象関数を`setup`にして一度実行（初回は権限承認ダイアログが出るので許可）→「設定」タブB1にaccess_token・B2にthreads_user_idを貼り付けてから、もう一度`setup`を実行（実行後トークンはシート上から自動で消去されます）
15. 実行対象関数を`installTriggers`にして実行 → 定時投稿・インサイト収集などのトリガーが設定されます

STEP 9〜15はSTEP 1〜8と並行して進めてもらって構いません（スプレッドシート作成自体はThreadsトークン取得を待つ必要がありません）。

---

## STEP 16〜: 週次分析の自動化（GitHub連携）

週次のクラウドルーティンが分析データを読めるようにするため、Apps ScriptからGitHubへ日次でデータを同期する仕組みを追加する。そのためのトークンを発行する。

16. https://github.com/settings/personal-access-tokens/new （Fine-grained personal access tokens）を開く
17. トークン名：任意（例："vivant-threads-sync"）
18. 有効期限：任意（GitHub PATには自動更新がないため、期限が切れたら手動で再発行が必要。長すぎる期限は漏洩時のリスクが上がるため、90日〜1年程度を推奨）
19. Repository access：「Only select repositories」→ このリポジトリ（`t377takuwork-debug/claude-project`）のみを選択
20. Permissions → Repository permissions → **Contents: Read and write** を選択（他の権限は付与しない）
21. 「Generate token」でトークンを発行・コピー
22. vivant用スプレッドシートの「設定」タブに以下を追加：
    ```
    A3: github_token       B3: <発行したトークンを貼り付け>
    ```
23. Apps Scriptエディタで`setupGithubToken()`を実行対象に選び実行 → B3が自動で消去されればOK
24. `installTriggers()`を再実行 → 日次のGitHub同期トリガーが追加される

