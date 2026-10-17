"""Mステ記事の部品HTMLの組み立てと、書き換え位置の一覧（2026-10-23新設）

Mステのリライトで毎回同じ形を手で書いていた部品（時間帯の行・出演者カード・出演順の記録・FAQ・過去一覧のカード等）を、
「公開中の記事と1文字も違わない形」で部品化した。tools/test_mste_parts.py が公開済みの2版（10/16回・10/23回）と
照合して確かめる。デザイン・文言の型は変えない。入れ替わるのは名前・曲・時刻・説明文だけ。

使い方:
    python tools/mste_parts.py --outline          # draft_mste.txt の書き換え位置（行番号）を一覧にする（全文を読まずに済む）
    （スクリプトの例）
    import sys; sys.path.insert(0, r'tools')
    from mste_parts import *
    from draft_patch import Patch

部品はどれも wp:html コメントの「内側」だけを返す（<!-- wp:html --> の行は含まない）。
注意: 組み立てに「%」書式は使わない（CSSの 50% と衝突する）。文字列の足し算だけを使っている。
"""
import io
import os
import re
import sys

BAR = '  <div style="height: 4px; background: linear-gradient(90deg, #ff0084, #ffdc00, #00d4ff, #0099ff);"></div>'
CLAMP14 = 'font-size: clamp(11px, calc(11px + (100vw - 480px) / 240), 14px);'


# ------------------------------------------------------------ 最新タイムテーブル
def mste_h3(text):
    """H3見出し（レベルを明示するWPブロック）"""
    return '<!-- wp:heading {"level":3} -->\n<h3>' + text + '</h3>\n<!-- /wp:heading -->'


def mste_tt_opening(start='20:00'):
    """タイムテーブルの先頭行（オープニング・出演者紹介）"""
    return ('    <!-- ' + start + ' -->\n'
            '    <div style="display: flex; border-bottom: 1px solid #f1f5f9;">\n'
            '      <div style="width: 75px; background: #f8fafc; padding: 18px 10px; text-align: center; border-right: 1px solid #f1f5f9; flex-shrink: 0;">\n'
            '        <div style="font-size: 14px; font-weight: 900; color: #003366;">' + start + '</div>\n'
            '        <div style="font-size: 8px; font-weight: 800; color: #a0aec0; margin-top: 2px;">START</div>\n'
            '      </div>\n'
            '      <div style="flex: 1; padding: 15px 16px;">\n'
            '        <div style="font-size: 14px; font-weight: 800; color: #2d3748; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">\n'
            '          <span style="color: #ff0084;">●</span>オープニング・出演者紹介\n'
            '        </div>\n'
            '      </div>\n'
            '    </div>')


def mste_tt_row(time, name, songs, last=False, badge=None, border=True):
    """出演順予想の1行。songs は曲名のリスト。last=True は大トリ予想の行（ピンク）。
    badge は名前の横の小さなバッジ（例: '番組初出演'）。バッジがある行は曲もピンク。
    border=False は枠の最後の行（下線なし）。last=True は常に下線なし。"""
    pink = last or bool(badge)
    bd = ' border-bottom: 1px solid #f1f5f9;' if (border and not last) else ''
    tcol = '#ff0084' if last else '#003366'
    lab = '大トリ予想' if last else '予想'
    lcol = '#ff0084' if last else '#a0aec0'
    bg = ('background: #fff0f6; color: #ff0084; font-size: 11px; padding: 4px 10px; border-radius: 2px; font-weight: 700; border: 1px solid #ffd6ea;'
          if pink else
          'background: #f1f5f9; color: #4a5568; font-size: 11px; padding: 4px 10px; border-radius: 2px; font-weight: 700; border: 1px solid #e2e8f0;')
    b = (' <span style="font-size: 10px; font-weight: 900; color: #ff0084; background: #fff0f6; padding: 2px 6px; border-radius: 2px;">' + badge + '</span>') if badge else ''
    sp = ''.join('          <span style="' + bg + '">' + s + '</span>\n' for s in songs)
    return ('    <!-- ' + time + ' ' + name + ' -->\n'
            '    <div style="display: flex;' + bd + '">\n'
            '      <div style="width: 75px; background: #f8fafc; padding: 18px 10px; text-align: center; border-right: 1px solid #f1f5f9; flex-shrink: 0;">\n'
            '        <div style="font-size: 14px; font-weight: 900; color: ' + tcol + ';">' + time + '</div>\n'
            '        <div style="font-size: 8px; font-weight: 800; color: ' + lcol + '; margin-top: 2px;">' + lab + '</div>\n'
            '      </div>\n'
            '      <div style="flex: 1; padding: 15px 16px; background: #fff;">\n'
            '        <div style="font-size: 13px; font-weight: 700; color: #2d3748; margin-bottom: 8px;">' + name + b + '</div>\n'
            '        <div style="display: flex; flex-wrap: wrap; gap: 6px;">\n'
            + sp +
            '        </div>\n'
            '      </div>\n'
            '    </div>')


def mste_tt_header(date_dot):
    """カード上部の「独自予想」バッジ付きヘッダー（date_dot は '2026.10.23'）"""
    return ('  <div style="padding: 16px; background: #fcfdfe; border-bottom: 1px solid #edf2f7;">\n'
            '    <div style="display: flex; align-items: center; gap: 8px;">\n'
            '      <span style="background: #ff0084; color: #fff; font-size: 10px; font-weight: 900; padding: 2px 6px; border-radius: 2px;">独自予想</span>\n'
            '      <span style="font-size: 14px; font-weight: 900; color: #1a202c; letter-spacing: -0.01em;">' + date_dot + ' タイムテーブル（出演順予想）</span>\n'
            '    </div>\n'
            '  </div>')


def mste_tt_footer(text='上記は過去の傾向に基づく独自予想です。放送が始まったら、実際の歌唱順に書き換えていきます。'):
    """カード下部の注意書きの帯"""
    return ('  <div style="padding: 12px 16px; background: #1a202c; color: #fff;">\n'
            '    <div style="font-size: 11px; font-weight: 700; line-height: 1.6; display: flex; align-items: flex-start; gap: 8px;">\n'
            '      <span style="color: #ffdc00; font-size: 14px;">⚠️</span>\n'
            '      <span>' + text + '</span>\n'
            '    </div>\n'
            '  </div>')


def mste_tt_card(aria, rows, header=None, footer=None):
    """タイムテーブルのカード1枚。rows は部品の文字列のリスト。header/footer は無ければ None。
    1時間の通常回は header・footer 付きの1枚。2時間の特番は時間帯ごとのH3に分け、
    先頭のカードに header、最後のカードに footer を付ける。"""
    opn = ('<div role="region" aria-label="' + aria + '" style="font-family: \'Inter\', \'Hiragino Sans\', \'Yu Gothic\', sans-serif; margin: 20px 0; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 4px; overflow: hidden; box-shadow: 0 10px 25px -5px rgba(0, 40, 80, 0.1);">')
    parts = [opn, '', BAR, '']
    if header:
        parts += [header, '']
    parts += ['  <div style="padding: 0;">', '', '\n\n'.join(rows), '', '  </div>']
    if footer:
        parts += ['', footer]
    parts += ['</div>']
    return '\n'.join(parts)


# ------------------------------------------------------------ 出演者・歌唱曲一覧
def mste_lineup_card(name, text, badge=None):
    """出演者カード1枚。badge があればピンクの強調カード（例: '番組初出演'・'テレビ初披露'）"""
    if badge:
        bg = 'linear-gradient(180deg, #fff8f8 0%, #fff0f6 100%); border: 1px solid #ffcce0'
        bar = 'linear-gradient(90deg, #ff0084, #ffdc00)'
        b = ' <span style="font-size: 10px; font-weight: 900; color: #ff0084; background: #fff0f6; padding: 2px 6px; border-radius: 2px;">' + badge + '</span>'
    else:
        bg = 'linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%); border: 1px solid #dce4ed'
        bar = 'linear-gradient(90deg, #ff007a, #00d4ff)'
        b = ''
    return ('  <!-- ' + name + ' -->\n'
            '  <div style="flex: 1 1 calc(50% - 3px); min-width: 140px; position: relative; background: ' + bg + '; border-radius: 4px; box-sizing: border-box; overflow: hidden;">\n'
            '    <div style="position: absolute; top: 0; left: 0; width: 100%; height: 2px; background: ' + bar + ';"></div>\n'
            '    <div style="padding: 14px 12px;">\n'
            '      <p style="margin: 0 !important; font-size: 13px !important; font-weight: 900 !important; color: #1a202c !important; line-height: 1.4 !important;">' + name + b + '</p>\n'
            '      <p style="margin: 6px 0 0 !important; font-size: clamp(11px, calc(11px + (100vw - 480px) / 240), 14px) !important; font-weight: 600; color: #4a5568; line-height: 1.6;">' + text + '</p>\n'
            '    </div>\n'
            '  </div>')


# ------------------------------------------------------------ 出演時間の目安・順番の傾向
def mste_guide_block(date_label, blocks, footer):
    """「出演時間は何時頃？」の予測ガイド。blocks は (時刻ラベル, 枠の名前, 説明文) の3つ。"""
    out = []
    for i, (tm, ttl, txt) in enumerate(blocks):
        last = (i == len(blocks) - 1)
        extra = '' if last else ' margin-bottom: 12px; border-bottom: 1px dashed #edf2f7; padding-bottom: 10px;'
        out.append('    <div style="display: grid; grid-template-columns: 80px 1fr; gap: 10px;' + extra + '">\n'
                   '      <div style="font-size: 11px; font-weight: 800; color: #ff0084; background: #fff0f6; padding: 2px 6px; border-radius: 4px; text-align: center; align-self: start;">' + tm + '</div>\n'
                   '      <div style="font-size: 12px; color: #2d3748; line-height: 1.5;">\n'
                   '        <strong>' + ttl + '</strong><br>\n'
                   '        <span style="' + CLAMP14 + ' color: #718096;">' + txt + '</span>\n'
                   '      </div>\n'
                   '    </div>')
    return ('<div style="font-family: \'Hiragino Sans\', \'Meiryo\', sans-serif; margin: 20px 0; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">\n'
            '  <div style="background: #003366; color: #ffffff; padding: 12px 15px; font-size: 14px; font-weight: 900; display: flex; align-items: center; gap: 8px;">\n'
            '    <span style="color: #00d4ff;">●</span> ' + date_label + ' 出演時間帯の予測ガイド\n'
            '  </div>\n\n'
            '  <div style="padding: 15px; background: #ffffff;">\n'
            + '\n\n'.join(out) + '\n'
            '  </div>\n\n'
            '  <div style="background: #f8fafc; padding: 10px 15px; font-size: clamp(10px, calc(10px + (100vw - 480px) / 180), 14px); color: #a0aec0; border-top: 1px solid #edf2f7;">\n'
            '    ' + footer + '\n'
            '  </div>\n'
            '</div>')


def mste_tendency_cards(aria, cards, update_badge):
    """「順番の傾向」の4枚カード。cards は (見出し, 本文) の4つ。最後のカードに update_badge の小さな帯が付く。"""
    out = []
    for i, (ttl, txt) in enumerate(cards):
        badge = ''
        if i == len(cards) - 1:
            badge = '\n    <div style="margin-top: 8px; align-self: flex-start; font-size: 9px; font-weight: 900; color: #00b8e6; background: rgba(0, 184, 230, 0.07); padding: 2px 8px; border-radius: 2px;">' + update_badge + '</div>'
        out.append('  <div role="listitem" style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 2px; box-shadow: 0 3px 10px rgba(0, 34, 68, 0.05); overflow: hidden; position: relative; padding: 12px 14px; min-height: 80px; display: flex; flex-direction: column;">\n'
                   '    <div style="position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, #ff0084, #ffdc00, #00d4ff, #0099ff);"></div>\n'
                   '    <div style="display: flex; align-items: center; gap: 8px; font-weight: 900; color: #003366; margin-bottom: 6px; font-size: 12px; letter-spacing: -0.01em;">' + ttl + '</div>\n'
                   '    <p style="margin: 0; ' + CLAMP14.replace('font-size: ', 'font-size: ') + ' font-weight: 700; color: #4a5568; line-height: 1.6;">' + txt + '</p>' + badge + '\n'
                   '  </div>')
    return ('<div role="list" aria-label="' + aria + '" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 10px; margin: 14px 0; font-family: \'Inter\', \'Hiragino Sans\', \'Yu Gothic\', sans-serif;">\n\n'
            + '\n\n'.join(out) + '\n\n</div>')


# ------------------------------------------------------------ 実際の出演順（アーカイブ）・過去一覧
def mste_archive_entry(label, title, desc, kind='n', last=False):
    """出演順の記録の1件。kind: 'open'（水色の点）／'n'（青の点）／'peak'（ピンクの大きな点・★投稿のピーク）"""
    pb = '' if last else ' padding-bottom: 16px;'
    style = 'font-size: clamp(11px, calc(11px + (100vw - 480px) / 240), 14px); color: #718096;'
    if kind == 'peak':
        return ('      <div style="position: relative;' + pb + '">\n'
                '        <div style="position: absolute; left: -21px; top: 4px; width: 12px; height: 12px; border-radius: 50%; background: #ff0084; border: 2px solid #fff;"></div>\n'
                '        <div style="font-size: 11px; color: #ff0084; font-weight: 900;">' + label + '</div>\n'
                '        <div style="font-size: 13px; color: #1a202c; line-height: 1.5;">\n'
                '          <span style="font-weight: 900; color: #001a4d;">' + title + '</span><br>\n'
                '          <span style="' + style + ' font-weight: 600;">' + desc + '</span>\n'
                '        </div>\n'
                '      </div>')
    dot = '#00d4ff' if kind == 'open' else '#0099ff'
    return ('      <div style="position: relative;' + pb + '">\n'
            '        <div style="position: absolute; left: -19px; top: 4px; width: 8px; height: 8px; border-radius: 50%; background: ' + dot + '; border: 2px solid #fff;"></div>\n'
            '        <div style="font-size: 10px; color: #a0aec0; font-weight: 800;">' + label + '</div>\n'
            '        <div style="font-size: 12px; color: #2d3748; margin-top: 4px;">\n'
            '          <strong style="color: #001a4d;">' + title + '</strong><br>\n'
            '          <span style="' + style + ' display: block; margin: 2px 0 6px 0;">' + desc + '</span>\n'
            '        </div>\n'
            '      </div>')


def mste_past_card(date_h3, head, body, tip):
    """過去のタイムテーブル一覧（details内）のコンパクトなカード。body の改行は <br> と実際の改行で渡す。"""
    return ('<h3>' + date_h3 + '</h3>\n\n'
            '<div style="background:#fff;border:1px solid #e2e8f0;border-radius:4px;overflow:hidden;margin:16px 0;box-shadow:0 6px 15px rgba(0,40,80,0.05);">\n'
            '<div style="height:4px;background:linear-gradient(90deg,#ff0084,#ffdc00,#00d4ff,#0099ff);"></div>\n'
            '<div style="padding:12px 16px;background:#fcfdfe;border-bottom:1px solid #edf2f7;">\n'
            '<div style="font-size:11px;font-weight:900;color:#003366;">PAST DATA ARCHIVE</div>\n'
            '<div style="font-size:14px;font-weight:900;color:#1a202c;">' + head + '</div>\n'
            '</div>\n'
            '<div style="padding:14px 16px;font-size:clamp(12px, calc(12px + (100vw - 480px) / 240), 15px);font-weight:700;line-height:1.8;">\n'
            + body + '\n'
            '</div>\n'
            '<div style="padding:10px 14px;background:#f7fafc;border-top:1px solid #edf2f7;font-size:clamp(11px, calc(11px + (100vw - 480px) / 240), 14px);font-weight:700;">\n'
            + tip + '\n'
            '</div>\n'
            '</div>\n')


# ------------------------------------------------------------ FAQ
def mste_faq_cards(qas):
    """FAQの5枚カード全体。qas は (質問, 回答) の5つ（5つ目は固定質問）。"""
    cards = []
    for i, (q, a) in enumerate(qas, 1):
        cm = 'Q' + str(i) + ('（固定・編集不要）' if i == 5 else '')
        cards.append('    <!-- ' + cm + ' -->\n'
                     '    <div style="background: #ffffff; border: 1px solid #e2e8ef; border-radius: 4px; padding: 15px; position: relative; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 30, 60, 0.05);">\n'
                     '      <div style="position: absolute; top: 0; left: 0; width: 100%; height: 3px; background: linear-gradient(90deg, #00d4ff, #0099ff, #ff0084);"></div>\n'
                     '      <div style="display: flex; gap: 12px; align-items: flex-start; margin-bottom: 12px;">\n'
                     '        <span style="flex: 0 0 auto; background: #003366; color: #ffffff; font-size: 11px; font-weight: 900; width: 28px; height: 18px; display: flex; align-items: center; justify-content: center; transform: skewX(-15deg); line-height: 1;">\n'
                     '          <span style="display: inline-block; transform: skewX(0deg);">Q' + str(i) + '</span>\n'
                     '        </span>\n'
                     '        <p style="margin: 0; font-size: 12px; font-weight: 900; color: #003366; line-height: 1.5;">' + q + '</p>\n'
                     '      </div>\n'
                     '      <div style="display: flex; gap: 12px; align-items: flex-start; padding-top: 12px; border-top: 1px solid #f0f4f8;">\n'
                     '        <span style="flex: 0 0 auto; color: #ff0084; font-size: 14px; font-weight: 900; line-height: 1;">A</span>\n'
                     '        <p style="margin: 0; font-size: clamp(11.5px, calc(11.5px + (100vw - 480px) / 206), 15px); color: #4a5568; line-height: 1.7; font-weight: 600;">\n'
                     '          ' + a + '\n'
                     '        </p>\n'
                     '      </div>\n'
                     '    </div>')
    return ('<div style="font-family: \'Inter\', \'Hiragino Sans\', \'Yu Gothic\', sans-serif; margin: 20px 0;">\n'
            '  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">\n\n'
            + '\n\n'.join(cards) + '\n\n'
            '  </div>\n'
            '</div>')


# ------------------------------------------------------------ 書き換え位置の一覧
OUTLINE_PAT = re.compile(r'<h[23]>|aria-label=|ARTIST LINEUP|class="mst-archive-panel"|<details|</details>|MANUAL_JSONLD|^<p>\[nopc\]|^タイトル：|\[jsonld\]|\[/jsonld\]|<!-- Q\d|<!-- \d\d:\d\d')


def outline(path=None):
    """draft_mste.txt の主な目印の行番号を出す。全文を読まずに、書き換える範囲を決めるために使う。"""
    path = path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'drafts', 'draft_mste.txt')
    for n, line in enumerate(io.open(path, encoding='utf-8').read().split('\n'), 1):
        if OUTLINE_PAT.search(line) and not re.search(r'<!-- \d\d:\d\d', line):
            print(str(n) + ': ' + line.strip()[:90])
    print('-- 時間帯の行（タイムテーブル）--')
    first = last = None
    for n, line in enumerate(io.open(path, encoding='utf-8').read().split('\n'), 1):
        if re.search(r'^    <!-- \d\d:\d\d', line):
            first = first or n
            last = n
    print('時間帯の行: ' + str(first) + ' 〜 ' + str(last) + '（最後の行の終わりは、その下の「</div>」から数える）')


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if '--outline' in sys.argv:
        outline()
    else:
        print(__doc__)
