# s4lv X・Threads 投稿づくり

> **2026-10-08 から、s4lv の X・スレッズの投稿は `S4LVnote/` フォルダで作る（入口は `S4LVnote/CLAUDE.md`）。このスキルは使わない。** このスキルで呼ばれたら、作業を始めずに「S4LVnote フォルダを選んで、『Xの投稿を作って』『スレッズの投稿を作って』と頼んでください」と1行返して止まる（投稿の記録が2か所に分かれないようにするため）。古い場所 `brands/s4lv/` は、S4LVnote が完成するまで保険として残している。

s4lv（X @cfrms4lv／Threads @cfrms4lv）の投稿を作る手順。XもThreadsも、同じ手順で作る。決まりの中身はここには書かない。どの話題はどのファイルが正かは `brands/s4lv/CLAUDE.md`。

## 読むもの

毎回読む。

1. `brands/s4lv/rules/s4lv_voice.md`（声と書き方）
2. `brands/s4lv/rules/sns_common_rules.md`（材料と事実）
3. 媒体の決まりを1本：X＝`brands/s4lv/rules/x_post_generation_rules.md`／Threads＝`brands/s4lv/rules/threads_post_generation_rules.md`
4. `brands/s4lv/x_neta_daicho.md` の冒頭「オーナー確認状況」と、使う項目だけ（全部は読まない）

必要なときだけ読む。

- 本数・時刻・投稿後の動き：`brands/s4lv/rules/project_s4lv_operation_system.md`「投稿量」
- 2本柱の比率：`brands/s4lv/rules/project_s4lv_accounts.md`
- 実績の数字・開示の全文：`brands/s4lv/shared/personal_data.md`
- Xの誘導の回：`brands/s4lv/articles/note_article_index.md`
- 外の話題・音声ジャーナルを使うとき：`journals/external_seeds.md`・`journals/content_seeds.md`
- プロジェクトの中に情報がない・古いかもしれない話は、WebSearchで確かめる

## 手順

1. **直近を見る**：`python brands/s4lv/tools/recent_forms.py` を実行して、直近の投稿の形・入り方・終わり・問い・締めの語尾と、最近使ったネタを見る
2. **設計する**：1本ごとに次を決めて、表にする
   - 柱（型・思想／AI実働）と元ネタ（台帳 K◯・A◯・柱3-◯／ジャーナル M/D／note記事の章）
   - 形・入り方・終わり
   - Xは、反響の狙い（A／B）と推奨の投稿時刻。Threadsは、役割とトピック
3. **書く**
4. **自分で確かめる**：声の決まりの「作ったあとに見る」と「提案前の自己チェック」を、1本ずつ通す
5. **機械チェック**：`C:\Users\PC_User\AppData\Local\Python\bin\python.exe brands/tools/qa_post.py <ファイル> --account s4lv --platform <x|threads>`
   - ERROR 0件が、次へ進む条件。WARNは1件ずつ自分で判断する。同じ形のくり返しを知らせるWARNが出たら、形を変える
   - Threadsは、新しい分だけを見るために `--since M/D` を付ける
   - 保存しただけでは、自動チェックは走らない。必ず自分で実行する
6. **審査**：`sns-ai-reviewer` に渡す
   - 渡す文：「sns-ai-reviewer に委譲：s4lv {X|Threads} 投稿 {対象日}。下書き＝{パス}。媒体＝{x|threads}。1巡目。」
   - 審査は原則1巡。2巡目に回すのは、BLOCKがあるか、FIXが3件以上のときだけ。それより少ないFIXは、直して先へ進む
   - 同じ指摘への直しは2巡まで。残ったら、いまの状態と理由を添えて、オーナーに判断を仰ぐ
   - オーナーが自分で書き直した本文は、審査に回さない。機械チェックだけ通す
   - 審査役を呼び出せないときは、`general-purpose`（`model: sonnet`）に `.claude/agents/sns-ai-reviewer.md` の全文を渡して代わりにする
7. **提案する**：設計の表・本文・機械チェックと審査の結果を、1回で出す
   - 「◯日分の3本を提案して」のようにはっきりした依頼のときは、設計の表で止まらず、ここまで一気に進める。ネタの方向があいまいなときだけ、設計の段階で1回確認する
   - オーナーの指摘で本文を直したら、**変えたあとの全文と変えた点を先に見せて、確認をもらってから保存する**
   - 一度伝えた注意は、2回目からは書かない
8. **保存する**
   - X＝`brands/s4lv/posts/posts_x.txt`、Threads＝`brands/s4lv/posts/posts_threads.txt`。どちらも末尾に追記する。7日より古い分は `brands/s4lv/posts/archive/` へ移す
   - 見出しには、日時・柱・元ネタと、`／形：○○／入り方：○○／終わり：○○` を書く。Xは反響の狙い（A／B）、Threadsは役割とトピックも書く
   - Xの誘導の回は、自己リプライを本文のすぐ下に、そのままコピペできる形で書く。URLを書くのはそこだけ
   - 直すときは、該当する行だけを直す。ファイル全体を書き直さない
   - メモは、オーナーが確定した・差し替えた、という事実だけを1〜2行で書く。機械チェックが止める言い回しを、例としても書かない
9. **Threadsを自動投稿の列に入れる**：`python brands/s4lv/tools/queue_from_posts.py brands/s4lv/posts/posts_threads.txt <日付…> [--dry-run]`
   - 機械チェック → 投入 → 照合までを一度に行う。`--dry-run` で、投入の前まで確かめられる
   - 当日の枠に入れるときは、本文を確定させてから入れる（15分おきに、時刻を過ぎた分が自動で投稿されるため）
   - すでに入れた投稿を差し替えるときは `update_threads_queue_body.py`。仕組みの説明は `brands/s4lv/tools/threads_setup_guide.md`
10. **使った記録を付ける**：材料と事実の決まりの「使ったあとの記録」のとおり
11. **報告する**：保存先・機械チェックの結果・列に入れた結果を、1〜3行で書く。実行していないものを「できたはず」と書かない
12. **指摘を決まりに反映する**：オーナーが本文を直した・却下した所があれば、その意図（文言ではなく「何を嫌ったか／何を求めたか」）を、`brands/s4lv/CLAUDE.md`「決まりを変える手順」で正のファイルに反映する。1回きりの直しを決まりにするときは、オーナーに確認する
13. **コミット**：往復のたびにはしない。オーナーが確定した時点で1回
