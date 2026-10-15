# -*- coding: utf-8 -*-
"""お笑いの日2026 draft builder（str.replace・文字列の足し算のみ。%書式は使わない）

【初回作成専用の実例】新規記事の立ち上げで、部品（template_parts・ナビ・JSON-LD）を
人名データ1か所から組み立てる形の見本。**公開後は再実行しない**（オーナーの手直しや放送後の更新を
上書きするため。既存の下書きがあれば止まる）。更新は `/owarainohi-rewrite` のEditで行う。
別番組へ流用するときは、人名・本文・FAQ・配色（PALETTE_MAP）・URLを書き換えて使う。
"""
import json, re, os, sys

BASE = r"C:\Users\PC_User\claude project\blogs\shira_note"
OUT = os.path.join(BASE, "drafts", "draft_owarainohi.txt")
URL = "https://shira-treat.com/owarainohi-2026/"
EYECATCH = "https://shira-treat.com/wp-content/uploads/2026/10/image.webp"
INNER_IMG = "https://shira-treat.com/wp-content/uploads/2026/10/image-2-1.webp"
TODAY = "2026.10.16"

TITLE = "お笑いの日2026のタイムテーブル｜順番・スケジュールを時間別まとめ"
META = ("お笑いの日2026（2026年10月17日・TBS系）のタイムテーブルとスケジュール。"
        "午後2時スタートの生放送で、敗者復活戦・芸人総選挙・キングオブコント決勝の順番と出演者を時間別にまとめています。")

CS = "clamp(11px, calc(11px + (100vw - 480px) / 360), 13px)"
CM = "clamp(13px, calc(13px + (100vw - 480px) / 360), 15px)"
GOLD, RED, DGOLD, PINK = "#f2c230", "#e3262a", "#d4a017", "#ff6b6e"
BORDERS = [(GOLD, GOLD), (RED, PINK), (DGOLD, GOLD)]

# ---- 人名データ（HTML・JSON-LDの両方をここから作る）----
# (表示名, 種別) 種別: P=Person / G=PerformingGroup
MC_LOSER = [("濱家隆一（かまいたち）", "P"), ("チョコレートプラネット", "G")]
ANNA_LOSER = [("宇賀神メグ", "P")]
LOSERS = [("江戸川ジャンクジャンク", "G"), ("オフローズ", "G"), ("cacao", "G"), ("喫茶ムーン", "G"),
          ("しずる", "G"), ("生姜猫", "G"), ("スパイシーガーリック", "G"), ("そいつどいつ", "G"),
          ("ネルソンズ", "G"), ("破壊ありがとう", "G")]
JUDGES = ["青色1号", "あんよの日", "いぬ", "うるとらブギーズ", "オテンキ", "鬼ヶ島", "おむかいの葉っぱ洋食店",
          "かが屋", "カゲヤマ", "ザ・ギース", "3時のヒロイン", "GAG", "ジグザグジギー", "スクールゾーン",
          "スクラップス", "スタミナパン", "たらちね", "忠犬立ハチ高", "ドゥリオ", "ドンココ",
          "にゃんこスター・スーパー3助", "春とヒコーキ", "ぶったま", "ベルナルド", "ママタルト", "虫と兵隊", "ゆくえ"]
GUESTS_LOSER = [("鎮西寿々歌（FRUITS ZIPPER）", "P"), ("ホラン千秋", "P"), ("森本慎太郎（SixTONES）", "P")]
MC_SOUSENKYO = [("ダイアン津田", "P"), ("永野", "P")]
ANNA_SOUSENKYO = [("田村真子", "P")]
GUESTS_SOUSENKYO = [("ウエストランド井口", "P"), ("ロングコートダディ兎", "P"), ("エバース", "G"), ("カカロニ", "G"),
                    ("きしたかの", "G"), ("キンタロー。", "P"), ("タイムマシーン3号", "G"), ("たくろう", "G"),
                    ("トム・ブラウン", "G"), ("ドンデコルテ", "G"), ("コロコロチキチキペッパーズ・ナダル", "P"),
                    ("ぱーてぃーちゃん", "G"), ("ヒコロヒー", "P"), ("みなみかわ", "P"), ("モグライダー", "G"),
                    ("平成ノブシコブシ吉村", "P"), ("レインボー", "G")]
MC_FINAL = [("浜田雅功", "P")]
ANNA_FINAL = [("日比麻音子", "P")]
FINALISTS = [("ヤッホイ", "G"), ("相性はいいよね", "G"), ("ジェラードン", "G"), ("ダウ90000", "G"), ("や団", "G"),
             ("ザ・マミィ", "G"), ("ななまがり", "G"), ("元祖いちごちゃん", "G"), ("蛙亭", "G"), ("ニッポンの社長", "G")]
RADIO = [("ナイツ", "G"), ("御手洗菜々", "P"), ("川島明（麒麟）", "P")]


def nm(items):
    return " / ".join([x[0] if isinstance(x, tuple) else x for x in items])


def jl_name(n):
    # 括弧つきの補足は構造化データの name から外す
    return re.sub(r"（.*?）", "", n).strip() if n != "ダイアン津田" else n


# ---- 配色（番組ロゴ：黒地にシアン・マゼンタ・赤。2026-10-16 オーナー提供画像から） ----
# 部品は紺×金×赤で書いてあるため、書き出し前に番組の色へ一括置換する（ナビブロック・速報ガイド部品も同時に変わる）
PALETTE_MAP = [
    ("#0a0b22", "#0a0a0f"),            # 背景（濃紺→黒）
    ("#1c1a55", "#1b1b26"),            # 背景グラデーション
    ("#050510", "#000000"),            # ヘッダー背景
    ("#f2c230", "#1fc8ee"),            # 主役の色（金→シアン）
    ("rgba(242, 194, 48", "rgba(31, 200, 238"),
    ("#d4a017", "#d92a86"),            # 3色目（濃い金→マゼンタ）
]

def card(label, big=None, text=None, idx=0, strong=False):
    b, c = BORDERS[idx % 3]
    s = '      <div style="background: rgba(255,255,255,0.05); padding: 10px 12px; border-radius: 4px; border-left: 4px solid ' + b + ';">\n'
    s += '        <span style="font-size: ' + CS + '; color: ' + c + '; font-weight: 800;">' + label + '</span>'
    if big:
        s += ' <span style="font-size: ' + CM + '; font-weight: 800;">' + big + '</span>'
    if big and text:
        s += '<br>'
    elif not big and text:
        pass
    s += '\n'
    if text:
        s += '        <p style="font-size: ' + CS + '; color: #ccc; margin: 4px 0 0; line-height: 1.6;">' + text + '</p>\n'
    s += '      </div>\n'
    return s


def big_card(label, big, text, idx=0):
    """出演者カード：名前を大きく、説明は小さく（allstar出演者一覧の型）"""
    b, c = BORDERS[idx % 3]
    s = '      <div style="background: rgba(255,255,255,0.05); padding: 10px 12px; border-radius: 4px; border-left: 4px solid ' + b + ';">\n'
    s += '        <span style="font-size: ' + CS + '; color: ' + c + '; font-weight: 800;">' + label + '</span><br>\n'
    s += '        <span style="font-size: ' + CM + '; font-weight: 800;">' + big + '</span>\n'
    s += '        <p style="font-size: ' + CS + '; color: #ccc; margin: 4px 0 0; line-height: 1.6;">' + text + '</p>\n'
    s += '      </div>\n'
    return s


def aside_small(aria, header_html, cards, footer_html=""):
    s = '<!-- wp:html -->\n'
    s += '<aside role="region" aria-label="' + aria + '" style="display: block; font-family: \'Hiragino Kaku Gothic ProN\', sans-serif; background: #0a0b22; border: 1px solid #f2c230; border-radius: 6px; overflow: hidden; box-shadow: 0 4px 15px rgba(242, 194, 48, 0.2); color: #fff; max-width: 800px;">\n'
    s += '  <div style="padding: 12px; background-image: radial-gradient(circle at top, #1c1a55 0%, #0a0b22 100%);">\n\n'
    s += header_html
    s += '    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 10px;">\n\n'
    s += "\n".join(cards)
    s += '\n    </div>\n  </div>\n'
    s += footer_html
    s += '</aside>\n<!-- /wp:html -->\n'
    return s


def head_date(text):
    return ('    <div style="margin-bottom: 12px; border-bottom: 1px solid rgba(242, 194, 48, 0.3); padding-bottom: 4px;">\n'
            '      <span style="font-size: 12px; color: #f2c230; font-weight: 800;">' + text + '</span>\n    </div>\n\n')


def head_slot(time_text, badge="公式発表"):
    return ('    <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-bottom: 12px; border-bottom: 1px solid rgba(242, 194, 48, 0.3); padding-bottom: 6px;">\n'
            '      <span style="font-size: 12px; color: #f2c230; font-weight: 800;">▼ ' + time_text + '</span>\n'
            '      <span style="font-size: 10px; font-weight: 900; color: #f2c230; border: 1px solid #f2c230; border-radius: 2px; padding: 0 5px;">' + badge + '</span>\n'
            '    </div>\n\n')


def aside_big(aria, title, cards_html, min_w=240, note=""):
    s = '<!-- wp:html -->\n'
    s += '<aside role="region" aria-label="' + aria + '" style="display: block; font-family: \'Hiragino Kaku Gothic ProN\', sans-serif; background: #0a0b22; border: 1px solid #f2c230; border-radius: 8px; overflow: hidden; margin: 20px 0; box-shadow: 0 4px 20px rgba(242, 194, 48, 0.3); color: #fff;">\n\n'
    s += '  <div style="background: #050510; padding: 12px 15px; border-bottom: 2px solid #f2c230; text-align: center;">\n'
    s += '    <div style="font-size: 15px; font-weight: 900; letter-spacing: 0.1em; background: linear-gradient(135deg, #f2c230 0%, #ffffff 50%, #f2c230 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">\n'
    s += '      ' + title + '\n    </div>\n  </div>\n\n'
    s += '  <div style="padding: 15px; background-image: radial-gradient(circle at top, #1c1a55 0%, #0a0b22 80%);">\n\n'
    s += '    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(' + str(min_w) + 'px, 1fr)); gap: 10px;">\n\n'
    s += cards_html
    s += '\n    </div>\n'
    if note:
        s += '\n    <div style="margin-top: 12px; text-align: center; font-size: 10px; color: #a8a8c8; line-height: 1.6;">' + note + '</div>\n'
    s += '  </div>\n\n</aside>\n<!-- /wp:html -->\n'
    return s


def para(t):
    return '<!-- wp:paragraph -->\n<p>' + t + '</p>\n<!-- /wp:paragraph -->\n'


def h2(t):
    return '<!-- wp:heading -->\n<h2>' + t + '</h2>\n<!-- /wp:heading -->\n'


def h3(t):
    return '<!-- wp:heading {"level":3} -->\n<h3>' + t + '</h3>\n<!-- /wp:heading -->\n'


def past_card(aria, rows, items, note):
    s = '<!-- wp:html -->\n'
    s += '<aside role="region" aria-label="' + aria + '" style="display: block; font-family: \'Hiragino Kaku Gothic ProN\', sans-serif; background: #0a0b22; border: 1px solid #f2c230; border-radius: 8px; overflow: hidden; margin: 20px 0; box-shadow: 0 4px 20px rgba(242, 194, 48, 0.3); color: #fff;">\n\n'
    s += '  <div style="padding: 15px; background-image: radial-gradient(circle at top, #1c1a55 0%, #0a0b22 80%);">\n\n'
    s += '    <div style="display: grid; gap: 6px; margin-bottom: 14px; font-size: ' + CS + '; color: #ddd; line-height: 1.6;">\n'
    for k, v in rows:
        s += '      <div><span style="color: #f2c230; font-weight: 800;">' + k + '</span>　' + v + '</div>\n'
    s += '    </div>\n\n'
    s += '    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 8px;">\n\n'
    for i, (tm, tx) in enumerate(items):
        b, c = (GOLD, GOLD) if i % 2 == 0 else (RED, PINK)
        s += '      <div style="background: rgba(255,255,255,0.05); padding: 8px 12px; border-radius: 4px; border-left: 3px solid ' + b + ';">\n'
        s += '        <span style="font-size: ' + CS + '; color: ' + c + '; font-weight: 800;">' + tm + '</span><br>\n'
        s += '        <span style="font-size: ' + CS + '; color: #ddd; line-height: 1.6;">' + tx + '</span>\n'
        s += '      </div>\n\n'
    s += '    </div>\n\n'
    s += '    <div style="margin-top: 10px; font-size: 10px; color: #a8a8c8; line-height: 1.6;">' + note + '</div>\n\n'
    s += '  </div>\n\n</aside>\n<!-- /wp:html -->\n'
    return s


# ---- FAQ ----
FAQ = [
    ("お笑いの日2026は何時から何時までですか？",
     "2026年10月17日（土）午後2時から、TBS系で生放送されます。キングオブコント2026の決勝は午後9時56分までで、全体で約8時間の放送です。"),
    ("タイムテーブルや出番の順番は発表されていますか？",
     "企画の時間帯は発表されています。午後2時から4時30分が敗者復活戦、4時30分から6時が芸人総選挙、6時から9時56分がキングオブコント2026決勝です。各企画の中の出番の順番はまだ発表されておらず、放送後に実際の流れへ更新します。"),
    ("敗者復活戦に出るのはどの芸人ですか？",
     "江戸川ジャンクジャンク、オフローズ、cacao、喫茶ムーン、しずる、生姜猫、スパイシーガーリック、そいつどいつ、ネルソンズ、破壊ありがとうの10組です。芸人審査員の採点で3組に絞り、視聴者の国民投票で決勝に進む1組が決まります。"),
    ("キングオブコント2026の決勝進出者は誰ですか？",
     "ヤッホイ、相性はいいよね、ジェラードン、ダウ90000、や団、ザ・マミィ、ななまがり、元祖いちごちゃん、蛙亭、ニッポンの社長の10組です。敗者復活戦を勝ち上がった1組が加わり、合計11組で争います。MCは浜田雅功さん、審査員は例年より2名多い7名で、新しい審査員は放送中に発表される予定です。"),
    ("お笑いの日2026は見逃し配信はありますか？",
     "リアルタイム配信と見逃し配信は、TVerで案内されています。配信期間は公式の発表を確認してください。過去の『お笑いの日』『キングオブコント』はU-NEXTで視聴できると案内されていました。"),
]


def faq_aside():
    cards = ""
    for i, (q, a) in enumerate(FAQ):
        col = PINK if i % 2 == 0 else GOLD
        cards += '      <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(242, 194, 48, 0.2); border-radius: 6px; padding: 12px;">\n'
        cards += '        <div style="color: ' + col + '; font-weight: 900; font-size: 13px; margin-bottom: 5px;">Q' + str(i + 1) + '｜' + q + '</div>\n'
        cards += '        <div style="font-size: 11px; color: #eee; line-height: 1.6; border-top: 1px solid rgba(255,255,255,0.1); margin-top: 5px; padding-top: 5px;">\n'
        cards += '          ' + a + '\n        </div>\n      </div>\n\n'
    return aside_big("お笑いの日2026 よくある質問", "💬 よくある質問（FAQ）", cards, min_w=300)


# ---- 本文 ----
def build():
    p = []
    p.append('<!-- wp:paragraph -->\nタイトル：' + TITLE + '\n\nメタディスクリプション（' + str(len(META)) + '字）：\n' + META + '\n<!-- /wp:paragraph -->\n')
    p.append(para('[nopc][title][/nopc]'))
    p.append(para('2026年10月17日（土）放送の『お笑いの日2026』について、タイムテーブルとスケジュール・企画の順番・出演者をまとめています。'))

    # 速報ガイド（template_parts）
    g = open(os.path.join(BASE, "template_parts", "sokuho_guide.html"), encoding="utf-8").read()
    rep = {
        "{{記事名}}": "お笑いの日2026",
        "{{企画名と回}}": "お笑いの日2026",
        "{{月/日}}": "10/17",
        "{{YYYY.MM.DD (曜) HH:MM - HH:MM}}": "2026.10.17 (土) 14:00 - 21:56",
        "{{放送局}}": "TBS系",
        "{{番組の正式名称}}": "お笑いの日2026",
        "{{発表状況を1行で}}": "3つの企画の時間帯は発表済み",
        "{{補足1行}}": "各企画の中の出番の順番は、まだ発表されていません",
        "{{過去の目安を1行で}}": "決勝の開始は昨年より30分早い18:00",
        "{{根拠の補足}}": "2025年は14:00〜18:30が第一部で、決勝は18:30から始まりました",
        "{{目立たせたい情報1行}}": "キングオブコント初の敗者復活戦を生放送",
        "{{YYYY.MM.DD}}": TODAY,
    }
    # {{補足1行}} は2回出る（発表状況と目立たせたい情報）。順に置き換える
    second_hosoku = "決勝に進む1組は、視聴者の国民投票で決まります"
    for k, v in rep.items():
        if k == "{{補足1行}}":
            g = g.replace(k, v, 1)
            g = g.replace(k, second_hosoku, 1)
        else:
            g = g.replace(k, v)
    assert "{{" not in g, "guide placeholder left"
    p.append(g)
    p.append(para('[nopc][mokujimae][/nopc]'))
    p.append(para('キングオブコント初の敗者復活戦から芸人総選挙、決勝へと続く約8時間のお笑い特番！'))
    p.append(para('決勝の開始は昨年より30分早い午後6時！新しい追加情報などあり次第更新していきます！'))

    # --- タイムテーブル ---
    p.append(h2('お笑いの日2026 最新タイムテーブル【10/17】'))
    p.append(para('企画の時間帯は発表済みで、各企画の中の出番の順番はまだ発表されていません。'))
    top = [
        card("放送枠", "14:00〜21:56", "TBS系で生放送されます。", 0),
        card("企画の時間帯", "発表済み", "敗者復活戦・芸人総選挙・決勝の3つに分かれています。", 1),
        card("出番の順番", "未発表", "今のところ公式からのアナウンスはありません。", 2),
    ]
    p.append(aside_small("お笑いの日2026 タイムテーブル（10月17日）", head_date("▼ 2026年10月17日（土）"), top))
    p.append(para('公式が発表しているのは、3つの企画の時間帯です。'))
    p.append(para('出番の順番は、分かった範囲でこの欄に書き足します。'))

    p.append(h3('14：00～ キングオブコント2026 敗者復活戦'))
    c = [
        card("内容", None, "2008年に始まったキングオブコントで初めての敗者復活戦です。決勝進出を逃した10組が挑みます。", 0),
        card("決め方", None, "スタジオにいる芸人審査員の採点で3組に絞り、視聴者の国民投票で決勝に進む1組を決めます。", 1),
        card("MC・進行", None, "MCは濱家隆一さん（かまいたち）とチョコレートプラネット、進行はTBSの宇賀神メグアナウンサーです。", 2),
        card("挑戦する10組", None, nm(LOSERS) + "。10組は五十音順に案内されていて、出番の順番は発表されていません。", 0),
        card("ゲスト・審査員", None, "ゲストは" + nm(GUESTS_LOSER) + "です。芸人審査員は27組で、一覧は下の出演者の欄に載せています。", 2),
    ]
    p.append(aside_small("お笑いの日2026 タイムテーブル（14時台）", head_slot("14:00〜16:30"), c))

    p.append(para('[nopc][originalsc][/nopc]'))

    p.append(h3('16：30～ 芸人総選挙 お笑いの日ver.'))
    c = [
        card("内容", None, "芸人へのアンケートをもとに、2026年上半期に活躍した芸人をランキング形式で紹介します。", 0),
        card("MC・進行", None, "MCはダイアン津田さんと永野さん、進行はTBSの田村真子アナウンサーです。", 1),
        card("MCの2人", None, "津田さんは「芸人総選挙2025」の2025年一番面白かった芸人で1位、永野さんは2位でした。", 2),
        card("ゲスト（17組）", None, nm(GUESTS_SOUSENKYO) + "。生放送のため一部変更になる可能性があります。", 0),
    ]
    p.append(aside_small("お笑いの日2026 タイムテーブル（16時台）", head_slot("16:30〜18:00"), c))

    p.append(h3('18：00～ キングオブコント2026 決勝'))
    c = [
        card("内容", None, "第19回大会の決勝です。3445組がエントリーし、優勝賞金は1000万円です。", 0),
        card("決勝の組数", None, "決勝進出の10組に、敗者復活戦を勝ち上がった1組が加わり、11組で争います。", 1),
        card("MC・進行", None, "MCは浜田雅功さん、進行はTBSの日比麻音子アナウンサーで、7年連続になります。", 2),
        card("決勝進出の10組", None, nm(FINALISTS) + "。敗者復活戦の勝者1組が加わります。", 0),
        card("審査員", None, "例年より2名多い7名です。新しい審査員は放送中に発表される予定です。", 2),
    ]
    p.append(aside_small("お笑いの日2026 タイムテーブル（18時台）", head_slot("18:00〜21:56"), c))

    # --- 出演者 ---
    p.append(h2('お笑いの日2026の出演者一覧【10/17】'))
    p.append('<!-- wp:image {"align":"center","className":"size-full"} -->\n<figure class="wp-block-image aligncenter size-full"><img src="' + INNER_IMG + '" alt="お笑いの日2026のタイムテーブル 順番・スケジュール・出演者"/><figcaption class="wp-element-caption"><a href="https://www.tbs.co.jp/onair/geininsousenkyo/">公式サイト</a>｜<a href="https://x.com/owaraiday">公式X(@owaraiday)</a></figcaption></figure>\n<!-- /wp:image -->\n')
    p.append(para('出演者は企画ごとに分かれていて、MCも企画ごとに変わります。'))
    cards = ""
    cards += big_card("敗者復活戦 MC・進行", nm(MC_LOSER) + " / " + nm(ANNA_LOSER) + "（TBSアナウンサー）", "14:00からの敗者復活戦を進めます。", 0)
    cards += "\n" + big_card("敗者復活戦に挑む10組", nm(LOSERS), "公式に案内されている並びは五十音順です。", 1)
    cards += "\n" + big_card("敗者復活戦のゲスト", nm(GUESTS_LOSER), "スタジオで見守るゲストです。", 2)
    cards += "\n" + big_card("敗者復活戦の芸人審査員（27組）", nm(JUDGES), "採点で決勝に近い3組を選びます。", 0)
    cards += "\n" + big_card("芸人総選挙 MC・進行", nm(MC_SOUSENKYO) + " / " + nm(ANNA_SOUSENKYO) + "（TBSアナウンサー）", "16:30からの芸人総選挙を進めます。", 1)
    cards += "\n" + big_card("芸人総選挙のゲスト（17組）", nm(GUESTS_SOUSENKYO), "生放送のため一部変更の可能性があります。", 2)
    cards += "\n" + big_card("キングオブコント2026 MC・進行", nm(MC_FINAL) + " / " + nm(ANNA_FINAL) + "（TBSアナウンサー）", "18:00からの決勝を進めます。", 0)
    cards += "\n" + big_card("キングオブコント2026 決勝進出（10組）", nm(FINALISTS), "敗者復活戦の勝者1組が加わり、合計11組になります。", 1)
    p.append(aside_big("お笑いの日2026 出演者一覧", "★ 出演者（企画別）", cards))
    p.append(para('芸人審査員の27組は、敗者復活戦で採点を担当します。'))
    p.append(para('決勝の審査員7名の名前は、放送中に発表される予定です。'))
    p.append(para('[nopc][originalsc][/nopc]'))

    # --- 放送時間 ---
    p.append(h2('お笑いの日2026は何時から？放送時間とスケジュール'))
    p.append(para('本放送は10月17日（土）午後2時からTBS系で始まり午後9時56分に終わります。'))
    p.append(para('同じ日の午前には、TBSラジオで『ラジオお笑いの日2026』も放送されます。'))
    cards = ""
    cards += card("午前｜TBSラジオ", "9:00〜（約5時間）", "『ラジオお笑いの日2026』です。パーソナリティはナイツ、アシスタントは御手洗菜々アナウンサー、ゲストは川島明さん（麒麟）と永野さんです。", 1)
    cards += "\n" + card("午後｜第1部", "14:00〜18:00", "キングオブコント2026 敗者復活戦（14:00〜16:30）と、芸人総選挙 お笑いの日ver.（16:30〜18:00）です。", 0)
    cards += "\n" + card("夜｜第2部", "18:00〜21:56", "キングオブコント2026 決勝です。", 2)
    p.append(aside_small("お笑いの日2026 放送スケジュール", head_date("▼ 2026年10月17日（土）"), [cards]))

    # --- 順番の見方 ---
    p.append(h2('お笑いの日の企画の順番と見どころ'))
    p.append(para('時間帯が発表されている3つの企画について、押さえておきたい点をまとめています。'))
    cards = ""
    cards += card("🎯 敗者復活戦の決まり方", None, "芸人審査員の採点で3組に絞り、視聴者の国民投票で1組が決勝に進みます。決勝へ向かう道筋が、放送の前半で決まります。", 1)
    cards += "\n" + card("⏰ 決勝は30分早く始まる", None, "2025年は18:30から決勝が始まりましたが、今回は18:00からです。終了は両年とも21:56でした。", 0)
    cards += "\n" + card("⚖️ 審査員が2名増える", None, "2025年の審査員は5名でした。今回は7名で、新しい審査員は放送中に発表される予定です。", 2)
    cards += "\n" + card("🏅 芸人総選挙", None, "芸人へのアンケートをもとに、2026年上半期に活躍した芸人をランキング形式で紹介します。", 1)
    p.append(aside_small("お笑いの日2026 企画の順番の見方", "", [cards]))
    p.append(para('分単位の台本は公開されていないため、時間帯は公式が案内した枠だけを載せています。'))

    # --- 配信 ---
    p.append(h2('お笑いの日2026の見逃し配信・再放送はある？'))
    p.append(para('リアルタイム配信と見逃し配信は、TVerで案内されています。'))
    p.append(para('配信期間は公式の発表を確認してください。'))
    p.append(para('過去の『お笑いの日』『キングオブコント』は、U-NEXTで視聴できると案内されていました。'))
    cards = ""
    cards += '      <div style="background: rgba(255,255,255,0.05); border: 1px solid rgba(242, 194, 48, 0.25); border-radius: 6px; padding: 12px;">\n'
    cards += '        <div style="text-align: center; color: #f2c230; font-weight: 900; font-size: ' + CS + '; margin-bottom: 10px;">リアルタイム・見逃し配信</div>\n'
    cards += '        <a href="https://tver.jp/live/simul/leaj9s2vqx" target="_blank" rel="noopener" style="display: flex; align-items: center; justify-content: center; min-height: 40px; background: #ffffff; border-radius: 5px; text-decoration: none; box-sizing: border-box; padding: 6px 10px; margin-bottom: 8px;">\n'
    cards += '          <span style="font-size: ' + CS + '; font-weight: 900; color: #0a0b22; line-height: 1.4;">TVerで見る ▶</span>\n'
    cards += '        </a>\n'
    cards += '      </div>\n\n'
    cards += '      <div style="background: rgba(255,255,255,0.05); border: 1px solid rgba(242, 194, 48, 0.25); border-radius: 6px; padding: 12px;">\n'
    cards += '        <div style="text-align: center; color: #f2c230; font-weight: 900; font-size: ' + CS + '; margin-bottom: 10px;">これまでの配信はこちら</div>\n'
    cards += '        <a href="https://px.a8.net/svt/ejp?a8mat=2ZWAMB+51LYIQ+3250+BW8O2&amp;a8ejpredirect=https%3A%2F%2Fvideo.unext.jp%2Ffreeword%3Fquery%3D%25E3%2581%258A%25E7%25AC%2591%25E3%2581%2584%25E3%2581%25AE%25E6%2597%25A5" target="_blank" rel="nofollow" style="display: flex; align-items: center; justify-content: center; min-height: 40px; background: #ffffff; border-radius: 5px; text-decoration: none; box-sizing: border-box; padding: 6px 10px; margin-bottom: 8px;">\n'
    cards += '          <span style="font-size: ' + CS + '; font-weight: 900; color: #0a0b22; line-height: 1.4;">U-NEXT</span>\n'
    cards += '          <span style="font-size: 9px; font-weight: 900; color: #999; border: 1px solid #ccc; border-radius: 2px; padding: 0 3px; margin-left: 8px;">PR</span>\n'
    cards += '        </a>\n'
    cards += '        <img border="0" width="1" height="1" src="https://www18.a8.net/0.gif?a8mat=2ZWAMB+51LYIQ+3250+BW8O2" alt="">\n'
    cards += '      </div>\n'
    p.append(aside_big("お笑いの日2026 配信ガイド", "📺 配信ガイド", cards, min_w=220,
                       note="※都合により視聴できない場合があります。U-NEXTのリンクは広告（PR）です。"))

    # --- 過去 ---
    p.append(h2('お笑いの日 過去のタイムテーブル一覧'))
    p.append(para('放送後は、2026年の実際の流れもここに加えます。'))
    p.append(h3('2025年10月11日（土）お笑いの日2025'))
    p.append(past_card("お笑いの日 過去のタイムテーブル（2025年）",
        [("放送", "14:00〜21:56（第1部 14:00〜18:30「お笑い夢のコラボ祭」、キングオブコント2025決勝 18:30〜21:56）"),
         ("MC", "かまいたち・チョコレートプラネット。スペシャルサポーターはジェシーさんと田中樹さん、進行は田村真子アナウンサー"),
         ("決勝", "MCは浜田雅功さん、審査員は5名。ファイナリストは10組でした")],
        [("第1部の企画", "「キングオブ東西ネタバトル」（東西の芸人がくじで即席コンビを組んで3分ネタ）"),
         ("第1部の企画", "「キングオブエチュードバトル」（芸人と俳優が即席タッグで即興芝居）"),
         ("第1部の企画", "「キングオブミュージックバトル」（芸人とアーティストのコラボ対決）"),
         ("18:30〜21:56", "キングオブコント2025 決勝")],
        "内容は放送前の発表をもとにしています。企画ごとの細かい時刻は確認できていません。"))
    p.append(h3('2024年10月12日（土）お笑いの日2024'))
    p.append(past_card("お笑いの日 過去のタイムテーブル（2024年）",
        [("放送", "14:00から約8時間の生放送。テーマは「笑いの灯」"),
         ("MC", "かまいたち（山内健司さん・濱家隆一さん）が番組初のMC。担当は14:00〜18:30でした")],
        [("14:00〜18:30", "『ラヴィット！』『最強スポーツ男子頂上決戦2024秋』『ザ・ベストワン』との特別コラボ企画"),
         ("18:30〜", "キングオブコント2024（エントリー3139組）。王者はラブレターズ")],
        "コラボ企画の時刻は確認できていません。"))
    p.append(h3('2023年10月21日（土）お笑いの日2023'))
    p.append(past_card("お笑いの日 過去のタイムテーブル（2023年）",
        [("放送", "14:00〜21:54の生放送。総合MCはダウンタウン"),
         ("決勝", "キングオブコント2023（エントリー3036組）は19:00から。王者はサルゴリラ")],
        [("午後", "『ラヴィット！』『ザ・ベストワン』との企画"),
         ("19:00〜21:54", "キングオブコント2023 決勝")],
        "企画ごとの細かい時刻は確認できていません。"))

    # --- FAQ ---
    p.append(h2('よくある質問（FAQ）'))
    p.append(para('お笑いの日2026について、よく検索される疑問に答えています。'))
    p.append(faq_aside())

    # --- まとめ ---
    p.append(h2('【まとめ】'))
    p.append(para('『お笑いの日2026』は2026年10月17日（土）午後2時から午後9時56分まで、TBS系で生放送されます。'))
    p.append(para('午後2時からはキングオブコント初の敗者復活戦が始まります。'))
    p.append(para('午後4時30分からは芸人総選挙、午後6時からは決勝が続きます。'))
    p.append(para('出演者は、敗者復活戦の10組と決勝進出の10組などが発表されています。'))
    p.append(para('各企画の中の出番の順番は、まだ発表されていません。'))
    p.append(para('決勝の新しい審査員は、放送中に発表される予定です。'))
    return "\n".join(p)


def nav_block():
    src = open(os.path.join(BASE, "drafts", "draft_allstar.txt"), encoding="utf-8").read()
    i = src.index('<div style="margin: 18px 0 14px; background: #ffffff; border: 1px solid #e5e7eb;')
    start = src.rfind('<!-- wp:html -->', 0, i)
    end = src.index('<!-- /wp:html -->', i) + len('<!-- /wp:html -->')
    return src[start:end]


def jsonld():
    people = {}
    order = []

    def add(n, t):
        nn = jl_name(n)
        if nn not in people:
            people[nn] = t
            order.append(nn)
    for grp in [MC_LOSER, ANNA_LOSER, [(x, "G") for x in LOSERS_N()], [(j, "G") for j in JUDGES], GUESTS_LOSER,
                MC_SOUSENKYO, ANNA_SOUSENKYO, GUESTS_SOUSENKYO, MC_FINAL, ANNA_FINAL, FINALISTS, RADIO]:
        for n, t in grp:
            add(n, t)

    def ent(n):
        return {"@type": "Person" if people[n] == "P" else "PerformingGroup", "name": n}
    ents = [ent(n) for n in order]
    g = [
        {
            "@type": "BlogPosting", "@id": URL + "#post", "url": URL,
            "mainEntityOfPage": {"@type": "WebPage", "@id": URL},
            "headline": TITLE, "description": META,
            "keywords": ["お笑いの日2026 タイムテーブル", "お笑いの日2026 順番", "お笑いの日2026 スケジュール",
                         "お笑いの日 何時から", "キングオブコント2026 敗者復活戦", "芸人総選挙 お笑いの日ver.", "TBS"],
            "datePublished": "2026-10-16T12:00:00+09:00", "dateCreated": "2026-10-16T12:00:00+09:00",
            "dateModified": "2026-10-16T12:00:00+09:00", "inLanguage": "ja",
            "image": {"@type": "ImageObject", "@id": URL + "#primaryimage", "url": EYECATCH, "width": 1196, "height": 661},
            "thumbnailUrl": EYECATCH,
            "author": {"@type": "Person", "name": "Shira Notes", "url": "https://shira-treat.com/operator-information/"},
            "publisher": {"@type": "Organization", "name": "Shira Notes", "url": "https://shira-treat.com/",
                          "sameAs": ["https://x.com/ShiraNotes_"],
                          "logo": {"@type": "ImageObject", "url": "https://shira-treat.com/wp-content/uploads/2025/08/Shira-Notes-1.webp", "width": 512, "height": 512}},
            "articleSection": "お笑いの日",
            "about": [{"@type": "Thing", "name": "お笑いの日（TBS系お笑い特番）"},
                      {"@type": "Thing", "name": "お笑いの日2026 タイムテーブル"}],
            "mentions": ents,
            "hasPart": [{"@id": URL + "#broadcast"}, {"@id": URL + "#lineup"}, {"@id": URL + "#faq"}, {"@id": URL + "#breadcrumb"}],
        },
        {
            "@type": "BroadcastEvent", "@id": URL + "#broadcast",
            "name": "お笑いの日2026（2026年10月17日放送）",
            "startDate": "2026-10-17T14:00:00+09:00", "endDate": "2026-10-17T21:56:00+09:00",
            "eventStatus": "https://schema.org/EventScheduled", "isLiveBroadcast": True,
            "eventAttendanceMode": "https://schema.org/OnlineEventAttendanceMode",
            "description": "TBS系で2026年10月17日に生放送されるお笑い特番。キングオブコント2026の敗者復活戦と決勝、芸人総選挙を放送する。",
            "image": EYECATCH, "performer": ents,
            "broadcaster": {"@type": "Organization", "name": "TBSテレビ", "sameAs": "https://www.tbs.co.jp/"},
        },
        {
            "@type": "ItemList", "@id": URL + "#lineup",
            "name": "お笑いの日2026（10/17）出演者一覧", "numberOfItems": len(order),
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n} for i, n in enumerate(order)],
        },
        {
            "@type": "FAQPage", "@id": URL + "#faq",
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ],
        },
        {
            "@type": "BreadcrumbList", "@id": URL + "#breadcrumb",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "ホーム", "item": "https://shira-treat.com/"},
                {"@type": "ListItem", "position": 2, "name": "タイムテーブル", "item": "https://shira-treat.com/category/timetable/"},
                {"@type": "ListItem", "position": 3, "name": "お笑いの日2026 タイムテーブル", "item": URL},
            ],
        },
    ]
    body = json.dumps({"@context": "https://schema.org", "@graph": g}, ensure_ascii=False, indent=2)
    return "<!-- wp:shortcode -->\n<!-- MANUAL_JSONLD -->\n[jsonld]\n" + body + "\n[/jsonld]\n<!-- /wp:shortcode -->\n", order


def LOSERS_N():
    return [x[0] for x in LOSERS]


if __name__ == "__main__":
    if os.path.exists(OUT) and "--force" not in sys.argv:
        sys.exit("既存の下書きがあるため中止（初回作成専用）: " + OUT + "  上書きするなら --force")
    body = build()
    nav = nav_block()
    ld, names = jsonld()
    txt = body + "\n" + nav + "\n\n" + ld
    for a, b in PALETTE_MAP:
        txt = txt.replace(a, b)
    # 書き出し前の確認
    assert "%s" not in txt and "{{" not in txt
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(txt)
    print("meta len", len(META), "title len", len(TITLE), "names", len(names))
    open(os.path.join(BASE, "tools", "output", "owarainohi_names.txt"), "w", encoding="utf-8").write("\n".join(names))
