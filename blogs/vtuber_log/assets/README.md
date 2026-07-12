# assets/ — 記事用画像の置き場

記事を作成する際、使う画像を `assets/<記事スラッグ>/` に入れてから `/vtuber-article` スキルを起動する。

```
assets/
└── <記事スラッグ>/            例：nekomataokayu-past/
    ├── nekomataokayu-past-01.webp ← 画像（ASCII名・スラッグ入り必須）
    ├── manifest.md            ← 自動生成（画像解析キャッシュ：alt・タイトル・配置先）
    └── uploaded_urls.json     ← 自動生成（WPアップロード後の実URL。gitignore済み）
```

- 命名・選定・配置のルールは `rules/image_placement.md` を参照
- アップロードは `tools/wp_upload.ps1`（認証：`tools/wp_auth.local.json`、未作成ならスクリプトが案内）
- **使い捨て運用**：候補画像は多めに入れてよい（最適なものだけ選定される）。WP貼り付け・表示確認後はフォルダごと削除可。未使用画像だけはWPに上がっていないため、元データがなければ削除前に退避（詳細：`rules/image_placement.md` §1）。このフォルダの中身はgit管理対象外（README除く）
- **人物画像の注意**：VTuber・中の人関連の画像は権利・出典に配慮し、引用要件を満たす形（出典明記等）で使う。判断に迷う画像は使わない
