#!/usr/bin/env python3
"""千鳥の鬼レンチャン 出演者の人物記事（サビだけカラオケ）を、入力ファイル2つから作る。

使い方:
  python tools/build_onirenchan.py tools/onirenchan/broadcast_20260927.json tools/onirenchan/sasaki.json
  → drafts/draft_onirenchan_{人物のfile}.txt を作り、そのまま検品（qa_draft.py）まで実行する

入力:
  ① 放送回ファイル（放送日・挑戦者・配信URLなど。同じ放送の人物で使い回す）
  ② 人物ファイル（名前・プロフィール・文章など。人物ごとに1つ）
出力:
  WordPress用の下書き（コード部品・構造化データ込み）。タイトル・メタ・FAQは
  本文と構造化データで必ず同じ文になる。
項目の意味は .claude/commands/onirenchan-article.md の「入力ファイル」を参照。
"""
import argparse
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SITE = "https://shira-treat.com/"
FONT_A = "'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', sans-serif"
FONT_B = "'Hiragino Kaku Gothic ProN', sans-serif"
FS_CARD = "clamp(11px, calc(11px + (100vw - 480px) / 360), 13px)"
FS_NAME = "clamp(13px, calc(13px + (100vw - 480px) / 360), 15px)"
FS_TTL = "clamp(12px, calc(12px + (100vw - 480px) / 360), 14px)"

# サビだけカラオケのFAQ（番組が同じなら共通。放送回ファイルの faq_common で上書き可）
FAQ_COMMON = {
    "q": "サビだけカラオケとはどんな企画？",
    "a": "名曲のサビだけを一音も外さずに10曲連続で歌う企画です。スタジオでは千鳥とかまいたちが"
         "何レンチャンできるかを予想して、選んだ挑戦者でチームを作り合計のレンチャン数で勝敗を競います。",
}

REQUIRED_B = ["date", "weekday", "start", "end", "channel", "program", "official_url", "x_url",
              "x_handle", "count_text", "challengers", "challengers_note", "update_promise", "vod",
              "about_name"]
REQUIRED_P = ["name", "file", "slug", "title_tail", "meta", "lead", "published", "eyecatch",
              "image_src", "image_alt", "guide", "intro", "profile", "after_profile", "when",
              "after_challengers", "result", "faq", "matome", "event_note", "mentions"]


def T(tpl, **kw):
    for k, v in kw.items():
        tpl = tpl.replace("@@" + k + "@@", str(v))
    return tpl


def j(s):
    """JSON用に文字列を包む（日本語はそのまま）"""
    return json.dumps(s, ensure_ascii=False)


def p(text):
    return "<!-- wp:paragraph -->\n<p>" + text + "</p>\n<!-- /wp:paragraph -->"


def h2(text):
    return "<!-- wp:heading -->\n<h2>" + text + "</h2>\n<!-- /wp:heading -->"


def h3(text):
    return '<!-- wp:heading {"level":3} -->\n<h3>' + text + "</h3>\n<!-- /wp:heading -->"


def html(inner):
    return "<!-- wp:html -->\n" + inner + "\n<!-- /wp:html -->"


def check(d, keys, label):
    miss = [k for k in keys if k not in d]
    if miss:
        sys.exit(f"[入力エラー] {label}に必要な項目がありません: {', '.join(miss)}")


# ---------------------------------------------------------------- コード部品

def quick_guide(b, pr, name, md, date_dot, upd):
    g = pr["guide"]
    return html(T("""<aside role="region" aria-label="鬼レンチャン @@name@@ 速報ガイド" style="display: block; font-family: @@FONT@@; background: #ffffff; color: #333333; border: 1px solid #ead3ce; border-radius: 4px; overflow: hidden; position: relative; max-width: 100%; margin: 10px 0; box-shadow: 0 10px 30px rgba(0,0,0,0.08);">

  <div style="position: relative; background: #2b4288; padding: 10px 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #d94c63;">
    <div style="font-size: 11px; font-weight: 700; letter-spacing: 0.1em; color: #ffe3e8;">@@program@@ サビだけカラオケ</div>
    <div style="display: flex; align-items: center; gap: 6px; font-size: 9px; font-weight: 600; color: #fff; border-left: 1px solid rgba(255, 255, 255, 0.5); padding-left: 10px; white-space: nowrap;">
      @@md@@ 放送分
    </div>
  </div>

  <div style="position: relative; padding: 20px 12px; display: grid; gap: 15px;">

    <div style="display: flex; align-items: flex-start; gap: 8px;">
      <div style="flex-shrink: 0; font-size: 8px; font-weight: 700; border: 1px solid #2b4288; color: #2b4288; padding: 2px 4px; letter-spacing: 0.02em; width: 48px; text-align: center; margin-top: 2px;">放送日</div>
      <div style="flex: 1;">
        <span style="font-size: clamp(15.5px, calc(15.5px + (100vw - 480px) / 240), 20px); font-weight: 700; color: #2b4288; display: block; margin-bottom: 4px; white-space: nowrap; letter-spacing: -0.02em;">@@dateline@@</span>
        <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 6px;">
          <span style="color: #d94c63; font-size: 10.5px; font-weight: 800;">@@channel@@</span>
          <span style="color: #666; font-size: 10px;">@@program@@</span>
        </div>
      </div>
    </div>

    <div style="display: flex; align-items: flex-start; gap: 8px;">
      <div style="flex-shrink: 0; font-size: 8px; font-weight: 700; border: 1px solid #2b4288; color: #2b4288; padding: 2px 4px; letter-spacing: 0.02em; width: 48px; text-align: center; margin-top: 1px;">挑戦者</div>
      <div style="flex: 1; font-size: 12.5px; font-weight: 700; color: #333; line-height: 1.5;">
        @@count@@
        <div style="font-size: 10px; font-weight: 500; color: #666; margin-top: 3px;">@@csub@@</div>
      </div>
    </div>

    <div style="display: flex; align-items: flex-start; gap: 8px;">
      <div style="flex-shrink: 0; font-size: 8px; font-weight: 700; background: #2f51b7; color: #fff; padding: 2px 4px; letter-spacing: 0.02em; width: 48px; text-align: center; margin-top: 1px;">人物</div>
      <div style="flex: 1; font-size: 12.5px; font-weight: 700; color: #333; line-height: 1.5;">
        @@pmain@@
        <div style="font-size: 10px; font-weight: 500; color: #666; margin-top: 3px;">@@psub@@</div>
      </div>
    </div>

    <div style="background: rgba(217, 76, 99, 0.06); border-left: 3px solid #d94c63; padding: 8px 10px;">
      <div style="font-size: 10.5px; color: #d94c63; font-weight: 800; margin-bottom: 2px;">
        @@rmain@@
      </div>
      <div style="font-size: 9px; font-weight: 500; color: #888;">
        @@rsub@@
      </div>
    </div>

  </div>

  <div style="background: #fcfcfc; padding: 10px 12px; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #eee;">
    <div style="color: #999; font-size: 9px;">Update: @@upd@@</div>
    <a href="#st-toc-h-1" style="display: inline-flex; align-items: center; background: #d94c63; color: #fff; text-decoration: none; font-size: 10.5px; font-weight: 800; padding: 5px 12px; border-radius: 20px; box-shadow: 0 4px 10px rgba(217, 76, 99, 0.2);">
      詳細を確認 <span style="margin-left: 4px; font-size: 11px;">↓</span>
    </a>
  </div>

</aside>""", FONT=FONT_A, name=name, program=b["program"], md=md, dateline=date_dot,
        channel=b["channel"], count=b["count_text"], csub=g["challenger_sub"],
        pmain=g["person_main"], psub=g["person_sub"], rmain=g["result_main"],
        rsub=g["result_sub"], upd=upd))


def profile_card(pr, name):
    pf = pr["profile"]
    right = ""
    if pf.get("group_label"):
        right = ('\n    <div style="font-size: 9px; font-weight: 600; color: #fff; border-left: 1px solid '
                 'rgba(255, 255, 255, 0.5); padding-left: 10px; white-space: nowrap;">'
                 + pf["group_label"] + "</div>")
    rows = []
    for label, value in pf["rows"]:
        rows.append(T("""    <div style="display: flex; align-items: flex-start; gap: 8px;">
      <div style="flex-shrink: 0; font-size: 9px; font-weight: 700; border: 1px solid #2b4288; color: #2b4288; padding: 2px 4px; width: 56px; text-align: center; box-sizing: border-box;">@@l@@</div>
      <div style="flex: 1; font-size: 12.5px; font-weight: 700; color: #333; line-height: 1.5;">@@v@@</div>
    </div>""", l=label, v=value))
    return html(T("""<aside role="region" aria-label="@@name@@ プロフィール" style="display: block; font-family: @@FONT@@; background: #ffffff; color: #333333; border: 1px solid #ead3ce; border-radius: 4px; overflow: hidden; max-width: 100%; margin: 10px 0; box-shadow: 0 10px 30px rgba(0,0,0,0.08);">

  <div style="background: #2b4288; padding: 10px 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #d94c63;">
    <div style="font-size: 11px; font-weight: 700; letter-spacing: 0.1em; color: #ffe3e8;">@@name@@ プロフィール</div>@@right@@
  </div>

  <div style="padding: 16px 12px; display: grid; gap: 10px;">

@@rows@@

  </div>

  <div style="background: #fcfcfc; padding: 8px 12px; border-top: 1px solid #eee; color: #999; font-size: 9px; line-height: 1.6;">@@note@@</div>

</aside>""", FONT=FONT_A, name=name, right=right, rows="\n\n".join(rows), note=pf["note"]))


def challenger_cards(b, name, md):
    cards = []
    for c in b["challengers"]:
        me = c["key"] == name
        cards.append(T("""      <div style="background: #ffffff; padding: 10px 12px; border-radius: 4px; border-left: 4px solid @@bd@@;">
        <span style="font-size: @@fsn@@; font-weight: 800; color: #2b4288;">@@label@@</span>
        <p style="font-size: @@fsc@@; color: #555555; margin: 4px 0 0; line-height: 1.6;">@@note@@</p>
      </div>""", bd="#d94c63" if me else "#2f51b7", fsn=FS_NAME, fsc=FS_CARD,
                       label=c["label"], note=c["note"]))
    return html(T("""<aside role="region" aria-label="@@md@@放送 サビだけカラオケの挑戦者" style="display: block; font-family: @@FONT@@; background: #f9ede9; border: 1px solid #d94c63; border-radius: 6px; overflow: hidden; box-shadow: 0 4px 15px rgba(217, 76, 99, 0.15); color: #333333; max-width: 800px;">
  <div style="padding: 12px;">

    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 10px;">

@@cards@@

    </div>

    <div style="margin-top: 10px; font-size: 10px; color: #8a6f6a; line-height: 1.6;">@@note@@</div>

  </div>
</aside>""", md=md, FONT=FONT_B, cards="\n\n".join(cards), note=b["challengers_note"]))


def vod_guide(b):
    v = b["vod"]
    btn = ('display: flex; align-items: center; justify-content: center; min-height: 40px; '
           'background: #2b4288; border-radius: 5px; text-decoration: none; box-sizing: border-box; '
           'padding: 6px 10px; margin-bottom: 8px;')
    card = "background: #ffffff; border: 1px solid #e6c9c9; border-radius: 6px; padding: 12px;"
    ttl = ("text-align: center; color: #2b4288; font-weight: 900; font-size: " + FS_TTL
           + "; margin-bottom: 10px;")
    sp = "font-size: " + FS_CARD + "; font-weight: 900; color: #ffffff; line-height: 1.4;"
    return html(T("""<aside role="region" aria-label="@@program@@ 配信ガイド" style="display: block; font-family: @@FONT@@; background: #f9ede9; border: 1px solid #d94c63; border-radius: 8px; overflow: hidden; margin: 20px 0; box-shadow: 0 4px 20px rgba(217, 76, 99, 0.15); color: #333333;">

  <div style="background: #2b4288; padding: 12px 15px; border-bottom: 2px solid #d94c63; text-align: center;">
    <div style="font-size: 15px; font-weight: 900; letter-spacing: 0.1em; color: #ffffff;">
      📺 配信ガイド
    </div>
  </div>

  <div style="padding: 15px;">

    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px;">

      <div style="@@card@@">
        <div style="@@ttl@@">リアルタイムで配信</div>
        <a href="@@rt@@" target="_blank" rel="noopener" style="@@btn@@">
          <span style="@@sp@@ text-align: center;">TVerのリアルタイム配信 ▶</span>
        </a>
      </div>

      <div style="@@card@@">
        <div style="@@ttl@@">見逃し配信はこちら</div>
        <a href="@@series@@" target="_blank" rel="noopener" style="@@btn@@">
          <span style="@@sp@@">TVer</span>
        </a>
        <a href="@@fod@@" target="_blank" rel="noopener" style="@@btn@@">
          <span style="@@sp@@">FOD</span>
        </a>
      </div>


    </div>

    <div style="margin-top: 12px; text-align: center; font-size: 10px; color: #8a6f6a; line-height: 1.6;">※都合により視聴できない場合があります。</div>

  </div>

</aside>""", program=b["program"], FONT=FONT_B, card=card, ttl=ttl, btn=btn, sp=sp,
        rt=v["realtime_url"], series=v["series_url"], fod=v["fod_url"]))


def embed_block(pr):
    if pr.get("embed_html"):
        return html(pr["embed_html"])
    if pr.get("embed_url"):
        return html('<center><blockquote class="twitter-tweet" data-media-max-width="560"><a href="'
                    + pr["embed_url"] + '"></a></blockquote> <script async src="https://platform.x.com/'
                    'widgets.js" charset="utf-8"></script></center>')
    return None


# ---------------------------------------------------------------- 構造化データ

def jsonld(b, pr, ctx):
    name, slug = pr["name"], pr["slug"]
    url = SITE + slug + "/"
    pub = pr["published"]
    mod = pr.get("modified", pub)
    kws = pr.get("keywords") or [name, name + " 鬼レンチャン", "鬼レンチャン " + name,
                                 "鬼レンチャン サビだけカラオケ", "千鳥の鬼レンチャン 挑戦者"]
    kw_txt = ",\n".join("        " + j(k) for k in kws)
    mentions = ",\n".join(T("""        {
          "@type": "@@t@@",
          "name": @@n@@
        }""", t=m["type"], n=j(m["name"])) for m in pr["mentions"])
    performers = ",\n".join('        { "@type": "Person", "name": ' + j(c["key"]) + " }"
                            for c in b["challengers"])
    items = ",\n".join('        { "@type": "ListItem", "position": %d, "name": %s }' % (i, j(c["label"]))
                       for i, c in enumerate(b["challengers"], 1))
    faq = []
    for q, a in ctx["faq"]:
        faq.append(T("""        {
          "@type": "Question",
          "name": @@q@@,
          "acceptedAnswer": {
            "@type": "Answer",
            "text": @@a@@
          }
        }""", q=j(q), a=j(a)))
    d = b["date"]
    body = T("""<!-- wp:shortcode -->
<!-- MANUAL_JSONLD -->
[jsonld]
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "BlogPosting",
      "@id": "@@url@@#post",
      "url": "@@url@@",
      "mainEntityOfPage": {
        "@type": "WebPage",
        "@id": "@@url@@"
      },
      "headline": @@title@@,
      "description": @@meta@@,
      "keywords": [
@@kws@@
      ],
      "datePublished": "@@pub@@",
      "dateCreated": "@@pub@@",
      "dateModified": "@@mod@@",
      "inLanguage": "ja",
      "image": {
        "@type": "ImageObject",
        "@id": "@@url@@#primaryimage",
        "url": "@@eye@@",
        "width": 1200,
        "height": 675
      },
      "thumbnailUrl": "@@eye@@",
      "author": {
        "@type": "Person",
        "name": "Shira Notes",
        "url": "https://shira-treat.com/operator-information/"
      },
      "publisher": {
        "@type": "Organization",
        "name": "Shira Notes",
        "url": "https://shira-treat.com/",
        "sameAs": ["https://x.com/ShiraNotes_"],
        "logo": {
          "@type": "ImageObject",
          "url": "https://shira-treat.com/wp-content/uploads/2025/08/Shira-Notes-1.webp",
          "width": 512,
          "height": 512
        }
      },
      "articleSection": @@program@@,
      "about": [
        {
          "@type": "Thing",
          "name": @@about@@,
          "sameAs": "@@official@@"
        }
      ],
      "mentions": [
@@mentions@@
      ],
      "hasPart": [
        { "@id": "@@url@@#broadcast" },
        { "@id": "@@url@@#challengers" },
        { "@id": "@@url@@#faq" },
        { "@id": "@@url@@#breadcrumb" }
      ]
    },
    {
      "@type": "BroadcastEvent",
      "@id": "@@url@@#broadcast",
      "name": @@bname@@,
      "startDate": "@@start@@",
      "endDate": "@@end@@",
      "eventStatus": "https://schema.org/EventScheduled",
      "isLiveBroadcast": false,
      "eventAttendanceMode": "https://schema.org/OnlineEventAttendanceMode",
      "location": {
        "@type": "VirtualLocation",
        "url": "@@official@@"
      },
      "description": @@bdesc@@,
      "image": "@@eye@@",
      "broadcaster": {
        "@type": "Organization",
        "name": @@channel@@,
        "sameAs": "@@chsame@@"
      },
      "performer": [
@@performers@@
      ],
      "potentialAction": {
        "@type": "WatchAction",
        "target": "@@rt@@"
      }
    },
    {
      "@type": "ItemList",
      "@id": "@@url@@#challengers",
      "name": @@iname@@,
      "numberOfItems": @@n@@,
      "itemListElement": [
@@items@@
      ]
    },
    {
      "@type": "FAQPage",
      "@id": "@@url@@#faq",
      "mainEntity": [
@@faq@@
      ]
    },
    {
      "@type": "BreadcrumbList",
      "@id": "@@url@@#breadcrumb",
      "itemListElement": [
        {
          "@type": "ListItem",
          "position": 1,
          "name": "ホーム",
          "item": "https://shira-treat.com/"
        },
        {
          "@type": "ListItem",
          "position": 2,
          "name": "記事",
          "item": "https://shira-treat.com/"
        },
        {
          "@type": "ListItem",
          "position": 3,
          "name": @@bcname@@,
          "item": "@@url@@"
        }
      ]
    }
  ]
}
[/jsonld]
<!-- /wp:shortcode -->""", url=url, title=j(ctx["title"]), meta=j(pr["meta"]), kws=kw_txt, pub=pub,
        mod=mod, eye=pr["eyecatch"], program=j(b.get("section", "千鳥の鬼レンチャン")),
        about=j(b["about_name"]), official=b["official_url"], mentions=mentions,
        bname=j(f'{b["program"]}（{ctx["ymd_jp"]}放送）'),
        start=f'{d}T{b["start"]}:00+09:00', end=f'{d}T{b["end"]}:00+09:00',
        bdesc=j(f'{b["channel"]}で{ctx["ymd_jp"]}に放送される「サビだけカラオケ」の回。{pr["event_note"]}'),
        channel=j(b["channel"]), chsame=b.get("channel_url", "https://www.fujitv.co.jp/"),
        performers=performers, rt=b["vod"]["realtime_url"],
        iname=j(f'{ctx["md"]}放送 サビだけカラオケの挑戦者'), n=len(b["challengers"]),
        items=items, faq=",\n".join(faq), bcname=j("鬼レンチャン " + name))
    return body


# ---------------------------------------------------------------- 組み立て

def build(b, pr):
    check(b, REQUIRED_B, "放送回ファイル")
    check(pr, REQUIRED_P, "人物ファイル")
    name = pr["name"]
    y, m, dd = b["date"].split("-")
    md = f"{int(m)}/{int(dd)}"
    ymd_jp = f"{int(y)}年{int(m)}月{int(dd)}日"
    wd = b["weekday"]
    date_dot = f'{y}.{m}.{dd} ({wd}) {b["start"]} - {b["end"]}'
    title = f"鬼レンチャン {name}は誰？{md}の挑戦者｜{pr['title_tail']}"
    meta = pr["meta"]
    mod = pr.get("modified", pr["published"])
    upd = mod[:10].replace("-", ".")
    faq_common = b.get("faq_common", FAQ_COMMON)
    ctx = {"title": title, "md": md, "ymd_jp": ymd_jp,
           "faq": [(f"{name}は誰？", pr["faq"]["who"]),
                   (pr["faq"]["q2"], pr["faq"]["a2"]),
                   (faq_common["q"], faq_common["a"])]}
    suffix = pr["result"].get("suffix", "")
    v = b["vod"]

    blocks = []
    blocks.append("<!-- wp:paragraph -->\nタイトル：" + title + "\n\nメタディスクリプション（"
                  + str(len(meta)) + "字）：\n" + meta + "\n<!-- /wp:paragraph -->")
    blocks.append(p("[nopc][title][/nopc]"))
    blocks.append(p(pr["lead"]))
    blocks.append(quick_guide(b, pr, name, md, date_dot, upd))
    blocks.append(p("[nopc][mokujimae][/nopc]"))
    blocks.append(p(b["update_promise"]))

    blocks.append(h2(f"鬼レンチャン {name}は誰？"))
    emb = embed_block(pr)
    if emb:
        blocks.append(emb)
    blocks += [p(t) for t in pr["intro"]]
    blocks.append(profile_card(pr, name))
    blocks += [p(t) for t in pr["after_profile"]]

    blocks.append(h2(f"サビだけカラオケは何時から？挑戦者と見どころ【{md}】"))
    blocks.append("<!-- wp:image {\"align\":\"center\",\"className\":\"size-full\"} -->\n"
                  '<figure class="wp-block-image aligncenter size-full"><img src="' + pr["image_src"]
                  + '" alt="' + pr["image_alt"] + '"/><figcaption class="wp-element-caption">参考：<a href="'
                  + b["official_url"] + '">公式サイト</a>｜<a href="' + b["x_url"] + '">公式X('
                  + b["x_handle"] + ")</a></figcaption></figure>\n<!-- /wp:image -->")
    blocks.append(p(f'放送は{int(m)}月{int(dd)}日（{wd}）の{b["start"]}〜{b["end"]}で{b["channel"]}です。'))
    blocks += [p(t) for t in pr["when"]]
    blocks.append(challenger_cards(b, name, md))
    blocks += [p(t) for t in pr["after_challengers"]]
    blocks.append(p('詳しい案内は<a href="' + b["official_url"] + '">公式サイト</a>や<a href="'
                    + b["x_url"] + '">公式X</a>で見られます。'))
    blocks.append(p("[nopc][originalsc][/nopc]"))

    blocks.append(h2(f"{name}は何レンチャン？歌った曲と結果{suffix}"))
    blocks += [p(t) for t in pr["result"]["paragraphs"]]

    blocks.append(h2("鬼レンチャンの見逃し配信はある？"))
    blocks.append(p(v["lead"]))
    blocks.append(vod_guide(b))
    blocks.append(p(v["after"]))

    blocks.append(h2("よくある質問（FAQ）"))
    blocks.append(p(f"{name}さんについてよく検索されそうな疑問に答えます。"))
    for q, a in ctx["faq"]:
        blocks.append(h3(q))
        blocks.append(p(a))

    blocks.append(h2("【まとめ】"))
    blocks += [p(t) for t in pr["matome"]]
    blocks.append(jsonld(b, pr, ctx))
    return "\n\n".join(blocks) + "\n", title


def main():
    ap = argparse.ArgumentParser(description="鬼レンチャン人物記事の下書きを作る")
    ap.add_argument("broadcast", help="放送回ファイル（json）")
    ap.add_argument("person", help="人物ファイル（json）")
    ap.add_argument("-o", "--output", help="出力先（省略時 drafts/draft_onirenchan_{file}.txt）")
    ap.add_argument("--no-qa", action="store_true", help="作成後の検品を省く")
    a = ap.parse_args()
    with open(a.broadcast, encoding="utf-8") as f:
        b = json.load(f)
    with open(a.person, encoding="utf-8") as f:
        pr = json.load(f)
    text, title = build(b, pr)
    out = os.path.abspath(a.output) if a.output else os.path.join(
        BASE, "drafts", f"draft_onirenchan_{pr['file']}.txt")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"作成: {out}")
    print(f"タイトル: {title}（{len(title)}字）")
    if a.no_qa:
        return
    drafts = os.path.join(BASE, "drafts")
    if os.path.dirname(out) != drafts:
        print("[注意] drafts/ の外に作ったため、検品は実行しません（qa_draft.py は drafts/ 内だけを検品します）")
        return
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(BASE, "tools", "qa_draft.py"),
                        os.path.basename(out)], cwd=BASE)
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
