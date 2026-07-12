# vtuber_log 内部リンク用URL一覧（2026-07-12時点・ユーザー提供＋sitemap照合済み）

記事作成・リライトで内部リンクを設置する際は、**必ずこの一覧に実在するURLだけを使う**。一覧にない記事へのリンクを推測で作らない（存在しない記事へのリンク捏造防止）。新記事の公開・削除があれば本ファイルを更新する。

**鮮度チェック**：`tools\update_internal_links.ps1` を実行するとサイトの実sitemapと本一覧の差分（追加すべきURL・sitemap不在のURL）がレポートされる。記事公開・削除後や、しばらく更新していないときに実行し、差分を本ファイルへ手で反映する（説明文・分類は手書きのため自動書き換えはしない）。

## 設置ルール（入れ忘れ・過剰の両方を防ぐ）

内部リンクはトピカルオーソリティの結合線（`seo_writing_reference.md` §5）。ただし数を稼ぐものではない。

- **本数の目安：本文中に2〜6本**。`qa_draft.ps1` が0本と7本以上をWARNで検出する
- **本文と直接関連する記事だけ貼る**。いま説明している話題の深掘り・次の検討ステップになる記事が対象。関連が薄いリンクでの水増し禁止
- **同じURLへのリンクは記事内1回まで**（重複はWARN検出）
- **設置位置**：その話題を扱っているセクション内の自然な文脈に置く。記事末尾の「関連記事」羅列だけに頼らない
- **アンカーテキスト**：「こちら」「この記事」ではなくリンク先の内容がわかる言葉にする（`seo_writing_reference.md` §2）
- カテゴリページへの本文リンクは、一覧へ誘導する明確な理由があるときのみ
- **同一人物の別切り口記事（プロフィール⇔中の人⇔前世）は最優先の内部リンク候補**。同一人物の記事が複数ある場合は相互リンクを検討する

## カテゴリページ

| カテゴリ | URL |
|---|---|
| ホロライブ | https://vtuber-verse.com/category/hololive/ |
| にじさんじ | https://vtuber-verse.com/category/nijisanji/ |
| ぶいすぽっ！ | https://vtuber-verse.com/category/vspo/ |
| すぺしゃりて | https://vtuber-verse.com/category/specialite/ |
| Crazy Raccoon | https://vtuber-verse.com/category/crazy-raccoon/ |
| Neo-Porte | https://vtuber-verse.com/category/neoporte/ |
| REJECT | https://vtuber-verse.com/category/reject/ |
| StelLive | https://vtuber-verse.com/category/stellive/ |
| VShojo NOVA | https://vtuber-verse.com/category/vshojo-nova/ |
| ゆにれいど! | https://vtuber-verse.com/category/uniraid/ |
| ミリプロ | https://vtuber-verse.com/category/millionproduction/ |
| 無原唱レコード | https://vtuber-verse.com/category/mugensho-record/ |
| VTuber特集 | https://vtuber-verse.com/category/topic/ |
| 個人/その他 | https://vtuber-verse.com/category/individual-others/ |

※カテゴリ名は各カテゴリページの実タイトルから採録（2026-07-12確認）。

## 固定ページ

| ページ | URL |
|---|---|
| 運営者情報 | https://vtuber-verse.com/operator-information/ |
| お問い合わせ | https://vtuber-verse.com/contact/ |
| プライバシーポリシー | https://vtuber-verse.com/privacy-policy/ |
| 最新記事一覧 | https://vtuber-verse.com/new/ |
| HTMLサイトマップ | https://vtuber-verse.com/sitemap.html |

## ホロライブ・にじさんじ関連

- https://vtuber-verse.com/nekomataokayu-past/ — 猫又おかゆ（前世・喉の音）
- https://vtuber-verse.com/nekomataokayu-piyopiyo/ — 猫又おかゆ（喉の音）
- https://vtuber-verse.com/yukishiro-mahiro-nakanohito/ — 雪城眞尋（中の人）
- https://vtuber-verse.com/yukishiro-mahiro-fc/ — 雪城眞尋（引退・ファンクラブ）
- https://vtuber-verse.com/mahiro-retirement-rumor/ — 雪城眞尋（引退噂）
- https://vtuber-verse.com/shishido-akari-profile/ — 獅子堂あかり（プロフィール）
- https://vtuber-verse.com/shishido-akari-nakanohito/ — 獅子堂あかり（中の人）
- https://vtuber-verse.com/harusaku-nodoka-nakanohito/ — 春先のどか（中の人）
- https://vtuber-verse.com/kaguramea-nakanohito/ — 神楽めあ（中の人）
- https://vtuber-verse.com/kaguramea-yabai/ — 神楽めあ（やばい）
- https://vtuber-verse.com/ayatsuno-yuni-profile/ — 綾都ゆに（プロフィール）
- https://vtuber-verse.com/holoan-announcement/ — ホロライブ・ニュース（告知）

## ぶいすぽっ！・すぺしゃりて・その他新人関連

- https://vtuber-verse.com/ieiri-popo-profile/ — 家入ポポ（プロフィール）
- https://vtuber-verse.com/chise-tatsumaki-profile/ — 龍巻ちせ（プロフィール）
- https://vtuber-verse.com/ginjo-saine-profile/ — 銀城サイネ（プロフィール）
- https://vtuber-verse.com/azusa-honami-profile/ — 本阿弥あずさ（プロフィール）
- https://vtuber-verse.com/amayui-moka-nakanohito/ — 甘結もか（中の人）
- https://vtuber-verse.com/amayui-moka-streetfighter/ — 甘結もか（スト6）
- https://vtuber-verse.com/ameno-momoka-profile/ — 雨乃こさめ（プロフィール）
- https://vtuber-verse.com/ameno-momoka-nakanohito/ — 雨乃こさめ（中の人）
- https://vtuber-verse.com/amane-amu-profile/ — 天音あむ（プロフィール）
- https://vtuber-verse.com/amane-amu-nakanohito/ — 天音あむ（中の人）
- https://vtuber-verse.com/mochizuki-hoguno-profile/ — 望月ほぐの（プロフィール）

## ストリーマー・その他VTuber・企画関連

- https://vtuber-verse.com/akami-karubi-yabai/ — 赤見かるび（やばい）
- https://vtuber-verse.com/yutori-peke-profile/ — 独り言（ゆとりぺけ・プロフィール）
- https://vtuber-verse.com/yutori-peke-nakano-hito/ — 独り言（ゆとりぺけ・中の人）
- https://vtuber-verse.com/hestia-happiness-naka/ — ヘスティア・ハピネス（中の人）
- https://vtuber-verse.com/hestia-nationality/ — ヘスティア・ハピネス（国籍）
- https://vtuber-verse.com/tororo-ojousama-episodes/ — 猫麦とろろ（お嬢様エピソード）
- https://vtuber-verse.com/tororo-pastlife/ — 猫麦とろろ（前世）
- https://vtuber-verse.com/nekotoro-face-reveal/ — 猫麦とろろ（顔バレ・中の人）※sitemapから採録
- https://vtuber-verse.com/nemuta-nemune-nakanohito/ — 眠田ねむね（中の人）
- https://vtuber-verse.com/nemuta-profile/ — 眠田ねむね（プロフィール）
- https://vtuber-verse.com/nyamakumo-nakanohito/ — 若魔雲ふわり（中の人・素顔）※sitemapから採録
- https://vtuber-verse.com/wakamakumo-sanrio-k4sen/ — 若魔雲ふわり（サンリオとの関係・k4sen共演）※sitemapから採録
- https://vtuber-verse.com/wakamakumo-ribbon-theory/ — 若魔雲ふわり（前世・姫熊りぼん転生説）※sitemapから採録
- https://vtuber-verse.com/hinatamaru-vtuber-profile/ — 雛丸（プロフィール）
- https://vtuber-verse.com/hinatamaru-voice/ — 雛丸（声）
- https://vtuber-verse.com/hagukimoegoe-vtuber/ — 羽柴もえこ
- https://vtuber-verse.com/choya-hanabi-nakanohito/ — 長夜ハナビ（中の人）
- https://vtuber-verse.com/kawakurar-profile/ — 雛隈（プロフィール）
- https://vtuber-verse.com/onatsunonibitashi-profile/ — おなつの煮浸し（プロフィール）
- https://vtuber-verse.com/onatsunonibitashi-nakanohito/ — おなつの煮浸し（中の人）
- https://vtuber-verse.com/orisaki-moshu-profile/ — 織崎もす（プロフィール）
- https://vtuber-verse.com/yubarirei-nakanohito/ — 湯原れい（中の人）
- https://vtuber-verse.com/amagairuka-nakanohito/ — 天海るか（中の人）
- https://vtuber-verse.com/saba-sameko-identity/ — 鯖さめこ（正体）
- https://vtuber-verse.com/kurageuroa-nakanohito/ — 倉ヶ野うろあ（中の人）
- https://vtuber-verse.com/kaguyapito-face-reveal/ — 輝夜ピト（顔バレ）
- https://vtuber-verse.com/otodamatamako-nakanohito/ — 音霊たまこ（中の人）
- https://vtuber-verse.com/hanayori-yoruha-profile/ — 花依ヨルハ（プロフィール）
- https://vtuber-verse.com/komawarikoma-pmarusama/ — 駒割コマ（P丸様。関連）
- https://vtuber-verse.com/komawari-koma-zense/ — 駒割コマ（前世）
- https://vtuber-verse.com/compsaurus-profile/ — コンプサウルス（プロフィール）
- https://vtuber-verse.com/amakamikonomi-profile/ — 天上コノミ（プロフィール）
- https://vtuber-verse.com/mementovanitas-nakanohito/ — メメント・ヴァニタス（中の人）
- https://vtuber-verse.com/mitsuba-eni-nakanohito/ — 三つ葉えに（中の人）
- https://vtuber-verse.com/madtown-gta-vtuber/ — MadTown GTA（VTuber関連企画）
