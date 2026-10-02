# s4lv（@cfrms4lv）の入口

s4lv のX・Threads投稿の決まりは、話題ごとに「正のファイル」を1つだけ決めている。このファイルには、その一覧と、決まりを変える手順だけを書く。決まりの中身は、ここには書かない。

## 正のファイル

| 話題 | 正のファイル |
|---|---|
| 声と書き方（語尾・主語・1行目・読点・改行・記号・箇条書き・使わない言い方・わかりやすさ・ばらつき・提案前の自己チェック） | `rules/s4lv_voice.md` |
| 材料と事実（ネタの出どころ・既出の確認・作り話の禁止・開示・AIの話・数字・外の話題の確かめ方・使ったあとの記録） | `rules/sns_common_rules.md` |
| Xだけの決まり（反響の狙い・1行目と長さ・Note記事への誘導） | `rules/x_post_generation_rules.md` |
| Threadsだけの決まり（反響の狙い・役割・問い・自己リプライ・トピック） | `rules/threads_post_generation_rules.md` |
| 本数・時刻・投稿後の動き | `rules/project_s4lv_operation_system.md`「投稿量」 |
| アカウント・プロフィール・2本柱 | `rules/project_s4lv_accounts.md` |
| 実績の数字・開示の全文 | `shared/personal_data.md` |
| ネタ（事実） | `x_neta_daicho.md` |
| ネタの候補（UYA.と共通の置き場） | `journals/external_seeds.md`（外の話題）／`journals/content_seeds.md`（体験） |
| 投稿づくりの手順 | `.claude/commands/s4lv-post.md` |
| 審査の見方 | `docs/rubrics/sns_ai_tone_rubric.md` |
| 広め方の仕組みの資料 | `brands/reference/x_algorithm_2026.md`／`brands/reference/threads_algorithm_2026.md` |
| Note記事の決まり | `rules/project_s4lv_note_article_process.md`／`rules/note_article_checklist.md` |
| Note運用の学びと数字の記録 | `rules/s4lv_learnings.md` |

食い違いを見つけたら、正のファイルが正。見つけた食い違いは、下の手順でその場で直す。

## 決まりを変える手順

オーナーの指摘や新しい決定を反映するときは、必ずこの順で行う。

1. 上の一覧で、その話題の正のファイルを決める
2. 変える案を作る。正のファイルの該当する所を**置き換える**（書き足すだけにしない）。食い違う旧い記述を検索して、**消す**案に入れる。「旧版」「いまは使わない」の注意書きや、経緯の一言で残さない（履歴は git にある）
3. ほかのファイルには決まりを写さない。要るときは「正は〇〇」と場所だけ書く
4. 変える全文をオーナーに見せて、確認をもらってから保存する。一度伝えた注意は繰り返さない
5. もう使わない言葉・ファイル名ができたら、`tools/check_rules.py` のリストに足す
6. `python brands/s4lv/tools/check_rules.py` を実行して、0件を確かめる
