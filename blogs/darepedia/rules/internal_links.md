# darepedia 内部リンク用 全記事URL一覧（実在URLのみ使用・リンク捏造防止）

`qa_draft.ps1`の内部リンク実在チェックが照合する唯一の正。新記事を公開したら、その都度この一覧に追記する（`article_pipeline.md`工程8）。

**注意**：以下は2026-08-26時点で`post-sitemap.xml`から取得したURL一覧。タイトルは確認できた8件のみ記載し、それ以外は未確認のため空欄にしてある（憶測でタイトルを埋めない）。本文で内部リンクを張る際、タイトル不明な記事へリンクする場合は、リンク先の実際のページ内容をWebFetch等で確認してからにする。カテゴリ（celebrity/sports/expert/others）の個別記事への割当も未確認のため記載していない。

## 確認済みタイトル

| URL | タイトル |
|---|---|
| https://darepedia.com/youngcarer-nightscoop/ | ヤングケアラー炎上回｜何があった？探偵ナイトスクープ母親問題 |
| https://darepedia.com/abe-haruka-profile/ | ヤングケアラー騒動で注目｜福山市の母親(あべはるか)について |
| https://darepedia.com/uchiboritaro-wiki/ | 内堀太郎は何者？どんなドラマに出てたか、出演作や経歴まとめ |
| https://darepedia.com/nagaoka-yuna-kawaii/ | 長岡柚奈がかわいいと話題｜彼氏は森口澄士選手という噂について |
| https://darepedia.com/yunasumi-pair/ | ミラノ五輪出場のフィギュア「ゆなすみペア」は付き合ってる？ |
| https://darepedia.com/karuma-punchdrunk/ | ドラマ「パンチドランク・ウーマン」河北竜馬役は誰？気になる俳優カルマについて |
| https://darepedia.com/sawada-kyomi-fukase/ | 沢田京海とは誰？Fukase熱愛で注目の20歳インフルエンサー |
| https://darepedia.com/gochi-new-member/ | ゴチ新メンバー誰？｜1/15最新予想と有力説2人をネタバレ(2026 1/15) |
| https://darepedia.com/lovejyoutou2-kazukun-ruru/ | 「ラブ上等2」のかずくんとるるは付き合ってる？急接近のきっかけを解説 |

## タイトル未確認（URLのみ・スラッグから内容を推測せず本文執筆時に要確認）

| URL |
|---|
| https://darepedia.com/sato-buzon-matsuko/ |
| https://darepedia.com/araki-sahori-buzz/ |
| https://darepedia.com/matsumoto-wakana/ |
| https://darepedia.com/nuts-princess/ |
| https://darepedia.com/kurochan-karen/ |
| https://darepedia.com/mirichamu-danna/ |
| https://darepedia.com/kizuki-minami-profile/ |
| https://darepedia.com/tommy-bastow-profile/ |
| https://darepedia.com/tommy-bastow-info/ |
| https://darepedia.com/takaishi-akari-gakureki/ |
| https://darepedia.com/takaishi-akari-eyes/ |
| https://darepedia.com/satomegumi-retirement/ |
| https://darepedia.com/kaishi-akari-kareshi/ |
| https://darepedia.com/sato-syouri-uraaka/ |
| https://darepedia.com/ainina-eshi/ |
| https://darepedia.com/ainina-ayase/ |
| https://darepedia.com/hashimoto-emi-poikatsu/ |
| https://darepedia.com/sugitakaoru-the-current/ |
| https://darepedia.com/shirayama-noa-wiki/ |
| https://darepedia.com/kawakita-mayuko-husband/ |
| https://darepedia.com/takaichi-children-adoption/ |
| https://darepedia.com/takaichisanae-danna/ |
| https://darepedia.com/nakamura-yuri-marriage/ |
| https://darepedia.com/tanihara-nanato-family/ |
| https://darepedia.com/nakasaka-miyu-manager/ |

## サイト固定URL

| URL | 内容 |
|---|---|
| https://darepedia.com/ | ホーム |
| https://darepedia.com/category/celebrity/ | カテゴリ：芸能人 |
| https://darepedia.com/category/sports/ | カテゴリ：スポーツ選手 |
| https://darepedia.com/category/expert/ | カテゴリ：専門家等 |
| https://darepedia.com/category/others/ | カテゴリ：その他 |

## 新規記事追記時のフォーマット

```
| https://darepedia.com/{スラッグ}/ | {タイトル} |
```

「確認済みタイトル」表に追記する。
