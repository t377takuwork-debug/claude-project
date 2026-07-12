# cf_room デザインコンポーネント集（唯一の正）

`deco-be22-review_revised_v2.txt` で確立した、記事内で使い回せるコードパーツ集。新規記事・リライトで「結論を先に見せたい」「表を作りたい」等のニーズがあれば、まずここから流用し、内容に応じて文言だけ差し替える。色・余白等の基礎トーンは統一し、単調にならないよう用途ごとに型を描き分ける（使い分けの一覧は本ファイル末尾「使い分けの原則」）。

すべて `<!-- wp:html -->` ブロックとして使用する。

---

## 1. ベネフィットカード（結論＋要点、記事冒頭用）

結論ファースト（`seo_writing_reference.md`参照）を体現する、記事冒頭に置く「読むべき記事か」を即判断させるカード。

```html
<div style="background: #ffffff; border: 1px solid #e0e0e0; padding: 20px; margin: 30px 0;">
    <div style="font-weight: 800; font-size: clamp(16px, 4vw, 19px); margin-bottom: 20px; line-height: 1.4; color: #111;">
        （ベネフィットを一言で表す見出し文）
    </div>
    <ul style="list-style: none; padding: 0; margin: 0; font-size: 13px !important; line-height: 1.2 !important; color: #333;">
        <li style="display: flex; margin-bottom: 6px !important; line-height: 1.2 !important;">
            <span style="flex-shrink: 0; background: #eef2f5; color: #4a6278; font-weight: 800; padding: 2px 8px; margin: 0 12px 0 0; height: 1.4em; display: flex; align-items: center; font-size: 12px !important; line-height: 1.2 !important;">ラベル</span>
            <span style="display: flex; align-items: center; line-height: 1.2 !important; font-size: 13px !important;">内容テキスト</span>
        </li>
        <!-- 以下、行を追加。最後の行はmargin-bottomを付けない -->
    </ul>
</div>
```

配色パターン（用途に応じて使い分け）：ポジティブ項目=`#eef2f5`/`#4a6278`、価格系=`#f0f4ef`/`#587058`、推奨対象=`#f5f2f0`/`#856a5d`、注意点=`#333`/`#fff`（黒地に白文字）。

## 2. 公式情報ボックス（アイキャッチ画像直後用）

```html
<div style="margin: 25px 0; border: 1px solid #dcdcdc; padding: 18px; background: #fff; text-align: center;">
    <div style="margin-bottom: 18px; display: flex; justify-content: center; gap: 20px; font-size: 11px; font-weight: 600;">
        <a href="（公式サイトURL）" style="color: #333; text-decoration: none;">🌐 公式サイト</a>
        <a href="（公式X URL）" style="color: #333; text-decoration: none;">
            <span style="font-weight: 900; margin-right: 3px; font-family: sans-serif;">X</span>公式アカウント
        </a>
        <a href="（購入リンク）" rel="nofollow" style="color: #333; text-decoration: none;">📦 Amazon</a>
    </div>
    <div style="border-top: 1px solid #eee; padding-top: 15px; display: flex; justify-content: center; align-items: center; gap: 20px;">
        <div style="text-align: center; flex: 1;">
            <div style="font-size: 10px; color: #888; letter-spacing: 0.1em; margin-bottom: 2px;">（プラン名）</div>
            <div style="font-size: 17px; font-weight: 400; color: #111;">（価格）<span style="font-size: 11px; margin-left: 2px; color: #888;">円</span></div>
        </div>
        <!-- 価格帯が複数ある場合は区切り線+同じ構造を追加 -->
    </div>
</div>
```

## 3. スペックグリッド（ラベル＋値・縦積み、製品仕様表用）

表（`wp:table`）の代わりに使う。項目数に制限なく追加可能。

```html
<div style="margin: 30px 0; border-top: 2px solid #111; padding-top: 5px;">
    <ul style="list-style: none; padding: 0; margin: 0;">
        <li style="display: flex; flex-direction: column; padding: 12px 0; border-bottom: 1px solid #f0f0f0; line-height: 1.3;">
            <span style="font-size: 12px !important; font-weight: 800; color: #999; letter-spacing: 0.15em; text-transform: uppercase; margin-bottom: 2px;">項目名</span>
            <span style="font-size: 13px !important; color: #222; font-weight: 500;">値・説明</span>
        </li>
        <!-- 最後の項目だけ border-bottom を外す -->
    </ul>
</div>
```

## 4. 2項目比較グリッド（横2列、モード比較等）

```html
<div style="margin: 30px 0; border-top: 2px solid #111; padding-top: 15px;">
    <div style="display: grid; grid-template-columns: 30% 70%; align-items: start; padding: 12px 0; border-bottom: 1px solid #f0f0f0;">
        <span style="font-size: 12px !important; font-weight: 800; color: #999; letter-spacing: 0.15em; text-transform: uppercase;">項目A</span>
        <span style="font-size: 13px !important; color: #222; font-weight: 500;">説明</span>
    </div>
    <div style="display: grid; grid-template-columns: 30% 70%; align-items: start; padding: 12px 0;">
        <span style="font-size: 12px !important; font-weight: 800; color: #999; letter-spacing: 0.15em; text-transform: uppercase;">項目B</span>
        <span style="font-size: 13px !important; color: #222; font-weight: 500;">説明</span>
    </div>
</div>
```

## 5. 3列比較グリッド（実測値の比較表等）

行見出し＋2条件（例：2.4GHz/5GHz）を比較するのに使う。列幅は `grid-template-columns` の割合を変えて調整。

```html
<div style="margin: 40px 0; border-top: 2px solid #111; padding-top: 15px;">
    <div style="display: grid; grid-template-columns: 25% 37.5% 37.5%; align-items: start; padding-bottom: 15px; border-bottom: 1px solid #e0e0e0; margin-bottom: 20px; font-size: 12px; font-weight: 800; color: #333; letter-spacing: 0.05em;">
        <div style="padding-left: 5px;">（軸ラベル）</div>
        <div style="text-align: center;">条件A<br><span style="font-weight: 400; color: #888; font-size: 11px;">（補足）</span></div>
        <div style="text-align: center;">条件B<br><span style="font-weight: 400; color: #888; font-size: 11px;">（補足）</span></div>
    </div>
    <div style="display: grid; grid-template-columns: 25% 37.5% 37.5%; align-items: start; margin-bottom: 25px;">
        <div style="display: flex; align-items: start; padding-left: 5px;">
            <span style="background: #eef6ff; color: #1a73e8; font-size: 12px; font-weight: 800; padding: 3px 8px; border-radius: 2px;">行ラベル</span>
        </div>
        <div style="font-size: 13px !important; line-height: 1.6; color: #444; padding: 0 5px;">値<br><span style="font-size: 12px; color: #777;">補足コメント</span></div>
        <div style="font-size: 13px !important; line-height: 1.6; color: #444; padding: 0 5px;">値<br><span style="font-size: 12px; color: #777;">補足コメント</span></div>
    </div>
    <!-- 行を追加する場合はバッジ色を変える（例：#fdf5e6/#b8860b） -->
</div>
```

## 6. ドット付き横並びリスト（機能一覧等）

```html
<div style="margin: 16px 0;">
    <div style="display: flex; align-items: center; padding: 8px 0; border-bottom: 1px solid #f0f0f0;">
        <span style="width: 6px; height: 6px; border-radius: 50%; background: #4a6278; margin-right: 10px; flex-shrink: 0;"></span>
        <span style="font-size: 13px !important; color: #333;">項目テキスト</span>
    </div>
    <!-- 最後の項目だけ border-bottom を外す -->
</div>
```

## 7. 丸数字バッジリスト（手順・理由の列挙、「おすすめな人」等）

```html
<div style="margin: 16px 0;">
    <div style="display: flex; align-items: flex-start; margin-bottom: 10px;">
        <span style="flex-shrink: 0; width: 22px; height: 22px; background: #111; color: #fff; font-size: 11px; font-weight: 800; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 10px;">1</span>
        <span style="font-size: 13px !important; color: #333; line-height: 1.5;">理由・特徴の説明</span>
    </div>
    <!-- 番号を2,3...と増やす。最後の項目だけ margin-bottom を外す -->
</div>
```

## 8. デメリットカード（見出し＋本文、実体は`<h3>`）

目次に拾われるよう、実体は必ず`<h3>`にする（外見はバッジ付き）。

```html
<div style="margin: 30px 0; border-top: 2px solid #111; padding-top: 15px;">
    <div style="margin-bottom: 16px;">
        <h3 style="font-size: 15px; font-weight: 800; color: #111; margin: 0 0 6px 0; display: flex; align-items: center;">
            <span style="flex-shrink: 0; background: #333; color: #fff; font-weight: 800; padding: 2px 8px; margin-right: 10px; height: 1.4em; display: flex; align-items: center; font-size: 12px !important; border-radius: 2px;">注意点1</span>
            見出しテキスト
        </h3>
        <p style="font-size: 13px !important; color: #333; line-height: 1.5; margin: 0;">本文テキスト</p>
    </div>
    <!-- 番号を増やして繰り返す -->
</div>
```

## 9. Q&Aカード（実体は`<h3>`、画像埋め込み対応）

```html
<div style="margin-bottom: 30px;">
    <h3 style="font-size: 18px; font-weight: 800; color: #111; margin-bottom: 12px; display: flex;">
        <span style="color: #888; margin-right: 10px;">Q1</span>
        質問文
    </h3>
    <div style="font-size: 13px !important; line-height: 1.7; color: #555; padding-left: 28px;">
        回答テキスト
    </div>
</div>
```
画像を挟む場合は `padding-left: 28px;` の div内、回答テキストの前に `<img src="..." alt="..." style="width: 100%; border-radius: 2px; margin-bottom: 15px;">` を追加し、回答は `<p>` タグで包む。

小さいタグ（MLO対応・4K-QAM等の補足ラベル）を回答内に入れる場合：
```html
<div style="display: flex; gap: 8px; margin: 12px 0;">
    <span style="background: #f4f4f4; color: #333; font-size: 12px !important; font-weight: 700; padding: 4px 8px; border-radius: 2px;">ラベル</span>
</div>
```

---

## 使い分けの原則

同じ記事内で同じ型を3回以上繰り返すと単調になる。内容の性質で描き分ける：
- 製品スペックの列挙 → 3（スペックグリッド）
- 2択の比較 → 4
- 3列以上の比較（実測値等） → 5
- 短い機能名の羅列（4項目程度） → 6（ドットリスト）
- 理由・ステップの列挙（3項目程度） → 7（丸数字バッジ）
- デメリット・注意点 → 8（黒バッジ）
- Q&A → 9
