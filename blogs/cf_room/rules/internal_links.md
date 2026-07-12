# cf_room 内部リンク用URL一覧（2026-07-12時点・ユーザー提供）

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

## カテゴリページ

| カテゴリ | URL |
|---|---|
| WordPress | https://cf-room.com/category/wordpress/ |
| AFFINGER | https://cf-room.com/category/wordpress/affinger/ |
| カスタマイズ | https://cf-room.com/category/wordpress/customize/ |
| その他 | https://cf-room.com/category/uncategorized/ |
| イヤホン・ヘッドセット | https://cf-room.com/category/earphones-headset/ |
| インターネット | https://cf-room.com/category/internet/ |
| ガジェット | https://cf-room.com/category/gadget/ |
| ゲーミングPC | https://cf-room.com/category/gamingpc/ |
| ゲーム | https://cf-room.com/category/game/ |
| スト鯖 | https://cf-room.com/category/game/streamer-server/ |
| セール | https://cf-room.com/category/sale/ |
| マウス | https://cf-room.com/category/mouse/ |
| モニター | https://cf-room.com/category/monitor/ |
| レビュー | https://cf-room.com/category/review/ |
| 家具・家電 | https://cf-room.com/category/furniture-home-appliances/ |

※AFFINGER・カスタマイズ・スト鯖はsitemap上の正規URLが階層形のため階層形へ統一（2026-07-12確認。旧フラット形も200で解決するが、1意図1URLの原則により正規形を使う）。マウス・その他はsitemap未掲載だが実在確認済み（200）。

## 固定ページ

| ページ | URL |
|---|---|
| 運営者情報 | https://cf-room.com/information/ |
| お問い合わせ | https://cf-room.com/contact/ |
| ニュース | https://cf-room.com/news/ |
| プライバシーポリシー | https://cf-room.com/privacy-policy-2/ |
| トップ | https://cf-room.com/top/ |

## TP-Link製品（ルーター・スマートホーム）

- https://cf-room.com/deco-be22-review/ — TP-Link Deco BE22 レビュー（Wi-Fi 7メッシュ）
- https://cf-room.com/archer-ge230-review/ — Archer GE230 レビュー（Wi-Fi 7ゲーミングルーター）
- https://cf-room.com/tp-link-archer-axe5400/ — TP-Link Archer AXE5400
- https://cf-room.com/tp-link-archer-ax23v/ — TP-Link Archer AX23V
- https://cf-room.com/archer-ax73v/ — Archer AX73V
- https://cf-room.com/tapo-t30-kit-review/ — Tapo T30 Kit レビュー（スマートホーム入門）
- https://cf-room.com/tp-link-tapo-h110/ — TP-Link Tapo H110
- https://cf-room.com/tapo-h100-review/ — Tapo H100 レビュー
- https://cf-room.com/tapo-t100-review/ — Tapo T100 レビュー
- https://cf-room.com/tp-link-tapo-t110/ — TP-Link Tapo T110
- https://cf-room.com/tapo-c260-review/ — Tapo C260 レビュー
- https://cf-room.com/tp-link-tapo-c200/ — TP-Link Tapo C200
- https://cf-room.com/tp-link-tapo-c220/ — TP-Link Tapo C220
- https://cf-room.com/tplink-tapo-c325wb/ — TP-Link Tapo C325WB
- https://cf-room.com/tp-linktapo-d230s1/ — TP-Link Tapo D230S1（ドアホン）
- https://cf-room.com/tp-link-tapo-p110m/ — TP-Link Tapo P110M

## ネット回線・プロバイダー

- https://cf-room.com/provider/ — プロバイダー
- https://cf-room.com/docomohikari-gmotokutokubb/ — ドコモ光 GMOとくとくBB
- https://cf-room.com/docomohikari-provider/ — ドコモ光 プロバイダー
- https://cf-room.com/docomohikari-router-replacement/ — ドコモ光 ルーター交換
- https://cf-room.com/docomohikari-rental-router/ — ドコモ光 レンタルルーター
- https://cf-room.com/ping/ — Ping
- https://cf-room.com/valorant-ping/ — Valorant Ping

## ガジェット・周辺機器レビュー

- https://cf-room.com/g-pro-x-superligh/ — Logicool G PRO X SUPERLIGHT マウスレビュー
- https://cf-room.com/gaming-mouse/ — ゲーミングマウス
- https://cf-room.com/fifine-h9-review/ — FIFINE AmpliGame H9 レビュー
- https://cf-room.com/mh-headset/ — MH ヘッドセット
- https://cf-room.com/oshinoko-earphone/ — 【推しの子】イヤホン
- https://cf-room.com/soundpeats-gofree2-review/ — SoundPEATS GoFree2 レビュー
- https://cf-room.com/capsule3-pro/ — Capsule3 Pro
- https://cf-room.com/microphone-arm/ — マイクアーム
- https://cf-room.com/keyartz-hk-750/ — KEYARTZ HK-750（毛玉取り）
- https://cf-room.com/on-lap-m152h-review/ — On-Lap M152H レビュー
- https://cf-room.com/xl2546k-review/ — XL2546K レビュー（モニター）
- https://cf-room.com/msi-optix-mag274qrf-qd-review/ — MSI Optix MAG274QRF-QD レビュー
- https://cf-room.com/wqhd-gaming-monitor-choose/ — WQHD ゲーミングモニター選び
- https://cf-room.com/wqhd-monitor-240/ — WQHD 240Hzモニター
- https://cf-room.com/grapht-customgaminggearseries/ — GRAPHT Custom Gaming Gear
- https://cf-room.com/steelseries-gg-sonar/ — SteelSeries Sonar
- https://cf-room.com/steelseries-sonar-setup/ — SteelSeries Sonar 設定
- https://cf-room.com/steelseries-sonar-microfone/ — SteelSeries Sonar マイク環境音除去
- https://cf-room.com/sonar-valorant-equalizer/ — Sonar Valorant Equalizer
- https://cf-room.com/smart-key-fingerprint/ — 家の鍵をスマートキー化（後付け指紋認証）
- https://cf-room.com/candy-house-sesame4/ — Candy House Sesame4
- https://cf-room.com/brain-sleep-clock/ — Brain Sleep Clock
- https://cf-room.com/matsuko-toaster/ — トースター（マツコ紹介）
- https://cf-room.com/beauty-face-stick/ — Beauty Face Stick
- https://cf-room.com/air-control-savings/ — Air Control Savings
- https://cf-room.com/z-gen-digital-camera/ — Z世代デジタルカメラ
- https://cf-room.com/mc-ns70f/ — MC NS70F
- https://cf-room.com/blu-ray-disc-reason/ — Blu-ray Disc 理由

## コントローラー（Freek/Blitz系）

- https://cf-room.com/freek/ — Freek
- https://cf-room.com/pro-freak-difference/ — Pro Freak 違い
- https://cf-room.com/pro-freak-recommendation/ — Pro Freak おすすめ
- https://cf-room.com/profreak-v2-xbox/ — Pro Freak V2 Xbox
- https://cf-room.com/profreak-v2-aoi/ — Pro Freak V2 Aoi
- https://cf-room.com/profreak-aka-yellow/ — Pro Freak Aka/Yellow
- https://cf-room.com/profreek-cheeky/ — Pro Freak Cheeky
- https://cf-room.com/blitz2-mode-precision/ — Blitz2 Mode Precision
- https://cf-room.com/blitz2-which-choose/ — Blitz2 どれを選ぶ
- https://cf-room.com/blitz2-stick-guide/ — Blitz2 スティックガイド
- https://cf-room.com/blitz2-apex-review/ — Blitz2 APEX レビュー

## ゲーム（攻略・情報）

- https://cf-room.com/sons-of-the-forest/ — Sons of the Forest 関連
- https://cf-room.com/sons-of-the-forest-setting/ — Sons of the Forest 設定
- https://cf-room.com/sons-of-the-forest-map/ — Sons of the Forest マップ
- https://cf-room.com/sons-of-the-forest-shovel/ — Sons of the Forest シャベル
- https://cf-room.com/sons-of-the-forest-ropegun/ — Sons of the Forest ロープガン
- https://cf-room.com/sons-of-the-forest-golden-armor/ — Sons of the Forest ゴールデンアーマー
- https://cf-room.com/sons-of-the-forest-item/ — Sons of the Forest アイテム
- https://cf-room.com/sons-of-the-forest-items/ — Sons of the Forest アイテム一覧
- https://cf-room.com/kakugama/ — かくがま
- https://cf-room.com/sv-pikachu-saikyou/ — SVピカチュウ最強
- https://cf-room.com/ff16-ps5orpc/ — FF16 PS5 or PC
- https://cf-room.com/ff16-trial-version/ — FF16 体験版
- https://cf-room.com/ff16-news/ — FF16 ニュース
- https://cf-room.com/ff16-demo-dowlord/ — FF16 デモダウンロード
- https://cf-room.com/undawn-release/ — Undawn リリース
- https://cf-room.com/undawn-campaign/ — Undawn キャンペーン
- https://cf-room.com/undawn-downlord/ — Undawn ダウンロード
- https://cf-room.com/undawn-cross-play/ — Undawn クロスプレイ
- https://cf-room.com/undawn-character-cv/ — Undawn キャラクターCV
- https://cf-room.com/apex-how-to-update/ — APEX 更新方法
- https://cf-room.com/lightsaber-style/ — ライトセーバースタイル
- https://cf-room.com/smashbros-online/ — スマブラ オンライン
- https://cf-room.com/amiibo-tears-of-the-kingdom/ — Amiibo ティアキン
- https://cf-room.com/honehonezaurus-x-release-switch/ — ホネホネザウルスX Switch
- https://cf-room.com/mh-wilds-switch-support/ — MH Wilds Switch対応
- https://cf-room.com/monster-hunter-wilds-pc-specs/ — MH Wilds PCスペック
- https://cf-room.com/monhan-recommended-gamingpc/ — モンハン向けゲーミングPC
- https://cf-room.com/monitor-choice-mhw/ — MHW モニター選び
- https://cf-room.com/monsterhunter-wilds-4k-monitor-guide/ — MH Wilds 4Kモニターガイド
- https://cf-room.com/ps5-price-increase-2024-reasons/ — PS5値上げ理由
- https://cf-room.com/ps5-pro-vs-ps5-performance/ — PS5 Pro vs PS5
- https://cf-room.com/ps5-pro-wifi7-benefits/ — PS5 Pro Wi-Fi 7メリット
- https://cf-room.com/ps5-pro-preorder-guide/ — PS5 Pro 予約ガイド
- https://cf-room.com/pre-launch-celebration/ — Pre Launch Celebration

## スト鯖・大会・VTuber

- https://cf-room.com/vcr-gta/ — VCR GTA
- https://cf-room.com/vcr-gta1/ — VCR GTA1
- https://cf-room.com/vcr-gta3-2024/ — VCR GTA3 2024
- https://cf-room.com/vcr-ark/ — VCR Ark
- https://cf-room.com/streamer-server-next/ — ストリーマーサーバー Next
- https://cf-room.com/streamer-server-rust/ — ストリーマーサーバー Rust
- https://cf-room.com/streamer-server-vcr-minecraft/ — VCR Minecraft サーバー
- https://cf-room.com/madtown-gta/ — MadTown GTA まとめ
- https://cf-room.com/madtown-gta-members/ — MadTown GTA メンバー
- https://cf-room.com/vtuber-saikyo-s6-2024/ — VTuber最強 S6 2024
- https://cf-room.com/v-saikyo-past-members/ — V最強 過去メンバー
- https://cf-room.com/vsaikyo-landmark-2024/ — V最強 Landmark 2024
- https://cf-room.com/hasematsuri-apex/ — ハセまつり APEX
- https://cf-room.com/rakuten-esports-cup-natsunoomohide/ — 楽天eスポーツ杯
- https://cf-room.com/ras-military-service/ — RAS 兵役

## eスポーツ英語学習

- https://cf-room.com/esports-english-learning/ — eスポーツ英語学習
- https://cf-room.com/esports-english-reviews/ — eスポーツ英語 レビュー
- https://cf-room.com/esports-english-comparison/ — eスポーツ英語 比較

## セール

- https://cf-room.com/prime-big-deal-days/ — Prime Big Deal Days
- https://cf-room.com/prime-big-deal-days-2023/ — Prime Big Deal Days 2023
- https://cf-room.com/prime-big-deal-days-gaming/ — Prime Big Deal Days Gaming
- https://cf-room.com/prime-sale-2024-best-items/ — Prime Sale 2024 おすすめ
- https://cf-room.com/prime-sale-2024-deals/ — Prime Sale 2024 セール
- https://cf-room.com/rakuten-super-sale/ — 楽天スーパーセール

## WordPress・ブログ運営（AFFINGER含む）

- https://cf-room.com/wordpress-start/ — WordPress 開始
- https://cf-room.com/wordpress-initial-setting/ — WordPress 初期設定
- https://cf-room.com/wordpress-rendering/ — WordPress レンダリング
- https://cf-room.com/wordpress-citation/ — WordPress 引用
- https://cf-room.com/wordpress-javascript/ — WordPress JavaScript
- https://cf-room.com/blog-start/ — ブログ開始
- https://cf-room.com/xserver-aossl/ — Xserver AOSSL
- https://cf-room.com/xserver-for-game-minecraft/ — Xserver Minecraft
- https://cf-room.com/affinger6-install/ — AFFINGER6 インストール
- https://cf-room.com/affinger6-initial-setting/ — AFFINGER6 初期設定
- https://cf-room.com/afffinger6-theme-use/ — AFFINGER6 テーマ使用
- https://cf-room.com/affinger6-theme-update/ — AFFINGER6 テーマ更新
- https://cf-room.com/affinger6-demo-site1-1/ — AFFINGER6 デモサイト
- https://cf-room.com/affinger6-design-site/ — AFFINGER6 デザイン
- https://cf-room.com/affinger6-top-sample/ — AFFINGER6 トップサンプル
- https://cf-room.com/affinger6-header-card/ — AFFINGER6 ヘッダーカード
- https://cf-room.com/adsense-yokonarabi/ — AdSense 横並び
- https://cf-room.com/adsense-examination/ — AdSense 審査
- https://cf-room.com/google-adsense-mokuji/ — Google AdSense 目次
- https://cf-room.com/google-analytics-pv/ — Google Analytics PV
- https://cf-room.com/sp-pc-bunki/ — SP/PC 分岐
- https://cf-room.com/mybox-design/ — MyBox デザイン
- https://cf-room.com/discord-icon/ — Discord アイコン
- https://cf-room.com/gaibusoushinkiritsu/ — 外部送信規律
