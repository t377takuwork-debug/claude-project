# Threads API の接続手順(任意)

分析AIが毎日Threadsの反応(閲覧数・いいね・返信・再投稿)を自動で取るための設定です。
**分からなければ飛ばして構いません。** その場合、分析AIはnoteの数字だけで分析し、Threadsの数字は手で送ってもらう形になります。

## 手順(15分)
1. Meta for Developers(developers.facebook.com)にログインし、「アプリを作成」→ ユースケースで「Threads API」を選ぶ
2. アプリの設定で「Threads API」を追加し、権限に `threads_basic` と `threads_manage_insights` を付ける
3. 「ユーザートークン生成」で、自分のThreadsアカウントを追加してアクセストークンを発行する
4. 発行されたトークンは短期(1時間)なので、長期トークン(60日)に交換する:
   `https://graph.threads.net/access_token?grant_type=th_exchange_token&client_secret=アプリシークレット&access_token=短期トークン` をブラウザで開く
5. 返ってきた `access_token` を `0_社長室/連携設定.md` の THREADS_ACCESS_TOKEN= に貼る
6. 自分のユーザーIDを取る: `https://graph.threads.net/v1.0/me?fields=id&access_token=トークン` をブラウザで開き、返ってきた `id` を THREADS_USER_ID= に貼る

## 確認
ClaudeCodeに「反応の分析を開始してください」と送って、レポートにThreadsの数字が入っていれば接続できています。

## 注意
- 長期トークンは60日で切れます。切れると分析AIが「未取得」と記録するので、手順4からやり直してください
- Meta側の画面や名称は変わることがあります。分からなければ設定しなくても記事作りには影響しません
