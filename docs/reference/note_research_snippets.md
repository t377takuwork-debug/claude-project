# note・Googleの調べ方（Claude in Chrome・動作確認済みの短い手順）

`/uya-theme` のキーワード確認と、`/uya-article` のハッシュタグ確認で使う。試行錯誤で呼び出しを増やさないための、2026-10-03〜05に動いた方法だけを書く。使うのは `javascript_tool`（ページの中でfetchする）。

**共通の注意**
- 1回のJSは**約40秒で止まる**。リクエストは1回に8本以内、間に0.6秒ほど空ける。多いときは結果を `window.__res` に入れ、次の呼び出しで読む
- 出力が長いと切れる。`slice(0,70)` で題だけ出す
- `get_page_text` や `screenshot` は、note.comの重いページ（`/contests` など）で固まる。ページの確認は、下の `innerText` の方法を使う

## 1. Googleのサジェスト（実在する検索語か）
`https://www.google.com/?hl=ja` を開いた状態で：
```
await (await fetch('/complete/search?client=firefox&hl=ja&q='+encodeURIComponent('ブログ リライト '))).json().then(j=>j[1])
```
語の末尾に半角スペースを付けると、続きの候補が出る。空配列は「サジェストなし」（需要が小さいか、組み合わせが珍しい）。`suggestqueries.google.com` を直接開く方法は固まる。

## 2. note内検索（人気順・新着順は別々に取る）
`https://note.com/` のどのページでもよい：
```
const r=await fetch('/api/v3/searches?context=note&q='+encodeURIComponent(q)+'&size=12&start=0&sort=popular'); // sort=new も
(await r.json()).data.notes.contents.map(n=>n.name.slice(0,70)+' ['+n.like_count+' ¥'+n.price+' '+n.publish_at.slice(0,10)+']')
```
スキ数は勝ち負けの証拠に使わない。見るのはタイトルの形だけ。出どころ（人気順／新着順）を表に残す。

## 3. ハッシュタグの実在・件数・お題かどうか
```
const d=(await (await fetch('/api/v2/hashtags/'+encodeURIComponent('ブログ運営'))).json()).data;
({count:d.count, related:d.relatedHashtags.slice(0,4).map(x=>x.name)})
```
- 関連タグを見ると、そのタグの読者層が分かる（例：「リライト」は怪談の創作が中心）
- お題・コンテストか確認するには、`https://note.com/hashtag/<タグ>` を開き、`location.pathname` が `/contest/…` になるか見る。中身は `document.body.innerText.slice(0,600)`
- 件数は需要の指標ではない（実在確認のため）
- `[BLOCKED: Cookie/query string data]` と出たら、`relatedContests` など長い出力をやめ、上のpathnameの方法に切り替える
