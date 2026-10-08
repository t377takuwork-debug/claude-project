"""リライトでくり返し使う部品HTMLの組み立て（2026-10-09新設）

CDTV・Venue101・STARのリライトで、出演者カード・出演順の行・過去一覧のカードなどを毎回手で書いていた。
ここに「今の記事と1文字も違わない形」で部品化した（tools/test_draft_parts.py が現在のdraftと一致することを確認する）。
デザイン・文言は変えない。入れ替わるのは名前・曲・時刻・説明文だけ。

使い方（スクリプトの例）:
    import sys; sys.path.insert(0, r'tools')
    from draft_parts import cdtv_artist_card, venue_past_card, ...
注意: 組み立てに「%」書式は使わない（CSSの 50% と衝突する）。文字列の足し算だけを使っている。
"""

# ---------------------------------------------------------------- CDTV
def cdtv_artist_card(name, badge, text):
    """出演者・歌唱曲一覧のカード1枚（badge空なら付けない）"""
    b = (' <span style="font-size:9px;font-weight:900;color:#ff008d;background:rgba(255,0,141,0.12);padding:2px 6px;border-radius:2px;">' + badge + '</span>') if badge else ''
    return ('  <div style="flex:1 1 calc(50% - 4px);min-width:140px;position:relative;background:#111;border:1px solid #ff008d;border-radius:4px;overflow:hidden;box-sizing:border-box;">\n'
            '    <div style="position:absolute;top:0;left:0;width:100%;height:2px;background:linear-gradient(90deg,#ff008d,#ffdc00)"></div>\n'
            '    <div style="padding:12px;">\n'
            '      <p style="margin:0;font-size:clamp(12px, calc(12px + (100vw - 480px) / 360), 14px);font-weight:900;color:#fff;">' + name + b + '</p>\n'
            '      <p style="margin:6px 0 0;font-size:clamp(10.5px, calc(10.5px + (100vw - 480px) / 240), 13.5px);color:#ccc;line-height:1.6;font-weight:700;">' + text + '</p>\n'
            '    </div>\n'
            '  </div>')


def cdtv_order_row(time, who, song):
    """「実際の出演順」表の1行。who/songの & は &amp; で渡す"""
    return ('                    <tr><td bgcolor="#111111" border="1">\n'
            '                        <font color="#ffffff" size="2"><b>' + time + '頃：' + who + '</b></font><br>\n'
            '                        <font color="#ff008d" size="2">' + song + '</font>\n'
            '                    </td></tr>')


def cdtv_order_block(label, rows):
    """前半／後半のブロック。rows は (time, who, song) のリスト"""
    return ('                <font color="#ff008d" size="2"><b>' + label + '</b></font>\n\n'
            '                <table border="0" width="100%" cellpadding="5" cellspacing="4" style="margin-top: 8px;">\n'
            '                    <tbody>\n' + '\n'.join(cdtv_order_row(*r) for r in rows) + '\n                    </tbody>\n'
            '                </table>')


def cdtv_past_full_card(date_jp, date_aria_label, front_label, front_text, back_label, back_text, bulb, back_extra_yellow=None, front_time='19:00〜', back_time='20:00〜', sp_note=''):
    """過去一覧のフルカード（H3つき）。date_jp 例: 2026年9月14日、back_extra_yellow=最も投稿が伸びた枠の黄色文"""
    br = '<br>' + chr(10) if back_text else ''
    yellow = (br + '<span style="color:#f9ff00;font-size:clamp(12px, calc(12px + (100vw - 480px) / 360), 14px);">' + back_extra_yellow + '</span>') if back_extra_yellow else ''
    return ('<!-- wp:heading {"level":3} -->\n<h3>CDTV ' + date_jp + 'のタイムテーブル</h3>\n<!-- /wp:heading -->\n\n<!-- wp:html -->\n'
            '<div role="region" aria-label="CDTV ' + date_aria_label + 'タイムテーブル" style="font-family:\'Inter\',\'Helvetica Neue\',Arial,sans-serif;margin:20px 0;background:#0b0b0c;border:1px solid #222;border-radius:6px;overflow:hidden;box-shadow:0 10px 30px rgba(0,0,0,0.5);">\n'
            '<div style="height:3px;background:linear-gradient(90deg,#ff008d,#ff00ea);"></div>\n'
            '<div style="padding:12px 14px;background:#111;border-bottom:1px solid #222;">\n'
            '<div style="font-size:clamp(10px, calc(10px + (100vw - 480px) / 360), 12px);font-weight:900;color:#f9ff00;letter-spacing:.08em;">TIME TABLE</div>\n'
            '<div style="font-size:13px;font-weight:900;color:#fff;">出演順・盛り上がり実績（' + date_jp + '放送' + sp_note + '）</div>\n'
            '</div>\n<div>\n'
            '<div style="display:flex;border-bottom:1px solid #222;">\n'
            '<div style="width:95px;background:#0f0f10;padding:14px 10px;text-align:center;border-right:1px solid #222;">\n'
            '<div style="font-size:13px;font-weight:900;color:#ff00ea;">' + front_time + '</div>\n'
            '<div style="font-size:9px;font-weight:700;color:#aaa;margin-top:2px;">' + front_label + '</div>\n'
            '</div>\n'
            '<div style="flex:1;padding:14px 14px;font-size:clamp(11px, calc(11px + (100vw - 480px) / 240), 14px);font-weight:700;color:#ddd;line-height:1.7;">\n' + front_text + '\n</div>\n</div>\n'
            '<div style="display:flex;">\n'
            '<div style="width:95px;background:#0f0f10;padding:14px 10px;text-align:center;border-right:1px solid #222;">\n'
            '<div style="font-size:13px;font-weight:900;color:#ff00ea;">' + back_time + '</div>\n'
            '<div style="font-size:9px;font-weight:700;color:#aaa;margin-top:2px;">' + back_label + '</div>\n'
            '</div>\n'
            '<div style="flex:1;padding:14px 14px;font-size:clamp(11px, calc(11px + (100vw - 480px) / 240), 14px);font-weight:700;color:#ddd;line-height:1.7;">\n' + back_text + yellow + '\n</div>\n</div>\n</div>\n'
            '<div style="padding:10px 14px;background:#0f0f10;border-top:1px solid #222;font-size:clamp(10px, calc(10px + (100vw - 480px) / 180), 14px);font-weight:700;color:#bbb;line-height:1.6;">\n'
            '💡 ' + bulb + '\n</div>\n</div>\n<!-- /wp:html -->')


def cdtv_past_compact(title, front, back, first=False):
    """折りたたみ内のコンパクト1エントリ。title 例: 2026年8月31日のタイムテーブル"""
    return ('<h3 style="margin:' + ('10px 0 6px' if first else '18px 0 6px') + ';font-size:14px;font-weight:900;color:#fff;">' + title + '</h3>\n'
            '<div style="border:1px solid #222;border-radius:6px;overflow:hidden;margin:14px 0;background:#0b0b0c;">\n'
            '<div style="height:3px;background:linear-gradient(90deg,#ff008d,#ff00ea);"></div>\n'
            '<div style="padding:14px 16px;font-size:clamp(12px, calc(12px + (100vw - 480px) / 360), 14px);font-weight:700;color:#ddd;line-height:1.8;">\n'
            '19:00台〜<br>\n' + front + '<br><br>\n20:00台〜<br>\n' + back + '\n</div>\n</div>')


# ---------------------------------------------------------------- Venue101
def venue_artist_card(n, s):
    return ('<div style="background:#1a1a1a;border-top:3px solid #d4ff00;padding:10px 10px 12px;"><div style="font-size:clamp(12px, calc(12px + (100vw - 480px) / 240), 15px);font-weight:900;color:#ffffff;line-height:1.4;">' + n +
            '</div><div style="font-size:clamp(11px, calc(11px + (100vw - 480px) / 240), 14px);font-weight:700;color:#d4ff00;margin-top:4px;line-height:1.5;">' + s + '</div></div>')


def venue_artist_grid(cards):
    """cards: [(名前, 曲), ...]"""
    return ('  <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-bottom:12px;">' +
            ''.join(venue_artist_card(n, s) for n, s in cards) + '</div>')


def venue_plan_row(a, b):
    return ('<div style="display:flex;gap:8px;padding:6px 0;border-top:1px solid #333333;font-size:clamp(11px, calc(11px + (100vw - 480px) / 240), 14px);line-height:1.6;"><div style="flex:0 0 42%;font-weight:900;color:#ffffff;">' + a +
            '</div><div style="flex:1;font-weight:700;color:#cccccc;">' + b + '</div></div>')


def venue_timeline_item(time, title, desc, hl=False):
    """アーカイブパネルのタイムライン1項目"""
    if hl:
        dot = '<div style="position:absolute;left:-21px;top:4px;width:12px;height:12px;border-radius:50%;background:#d4ff00;border:2px solid #1a1a1a;"></div>'
        col = '#d4ff00'
    else:
        dot = '<div style="position:absolute;left:-19px;top:4px;width:8px;height:8px;border-radius:50%;background:#999999;border:2px solid #1a1a1a;"></div>'
        col = '#999999'
    return ('    <div style="position:relative;padding-bottom:14px;">' + dot +
            '<div style="font-size:clamp(10px, calc(10px + (100vw - 480px) / 180), 14px);color:' + col + ';font-weight:800;">' + time +
            '</div><div style="font-size:clamp(12px, calc(12px + (100vw - 480px) / 240), 15px);color:#ffffff;margin-top:3px;"><strong>' + title +
            '</strong><br><span style="font-size:clamp(11px, calc(11px + (100vw - 480px) / 240), 14px);color:#cccccc;display:block;margin-top:2px;">' + desc + '</span></div></div>')


def venue_past_row(time, label, title, desc, hl=False):
    bg = 'rgba(212,255,0,0.12)' if hl else '#0d0d0d'
    tc = '#d4ff00' if hl else '#ffffff'
    return ('    <div style="display:flex;border-bottom:1px solid #333333;"><div style="flex:0 0 92px;background:' + bg +
            ';padding:12px 8px;text-align:center;border-right:1px solid #333333;display:flex;flex-direction:column;justify-content:center;"><div style="font-size:clamp(11px, calc(11px + (100vw - 480px) / 240), 14px);font-weight:900;color:' + tc +
            ';white-space:nowrap;">' + time + '</div><div style="font-size:clamp(9px, calc(9px + (100vw - 480px) / 240), 12px);font-weight:800;color:#999999;margin-top:2px;">' + label +
            '</div></div><div style="flex:1;padding:12px 14px;"><div style="font-size:clamp(12px, calc(12px + (100vw - 480px) / 240), 15px);font-weight:900;color:#ffffff;">' + title +
            '</div><div style="font-size:clamp(10px, calc(10px + (100vw - 480px) / 180), 14px);color:#cccccc;margin-top:4px;line-height:1.5;">' + desc + '</div></div></div>')


def venue_past_card(date_h3, aria, ttl, tag, rows, bulb, note):
    return ('<!-- wp:heading {"level":3} -->\n<h3>' + date_h3 + '</h3>\n<!-- /wp:heading -->\n\n<!-- wp:html -->\n'
            '<div role="region" aria-label="' + aria + '" style="font-family:\'Helvetica Neue\', Arial, \'Hiragino Sans\', Meiryo, sans-serif;margin:20px 0;background:#1a1a1a;border:1px solid #333333;border-radius:8px;overflow:hidden;">\n'
            '  <div style="height:4px;background:#d4ff00;"></div>\n'
            '  <div style="padding:14px 16px;border-bottom:1px solid #333333;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;">\n'
            '    <div><div style="font-size:clamp(10px, calc(10px + (100vw - 480px) / 180), 14px);font-weight:900;color:#d4ff00;letter-spacing:0.1em;">PAST DATA ARCHIVE</div><div style="font-size:clamp(13px, calc(13px + (100vw - 480px) / 240), 16px);font-weight:900;color:#ffffff;">' + ttl + '</div></div>\n'
            '    <div style="font-size:clamp(10px, calc(10px + (100vw - 480px) / 180), 14px);font-weight:800;color:#999999;">' + tag + '</div>\n'
            '  </div>\n  <div>\n' + '\n'.join(rows) + '\n  </div>\n'
            '  <div style="padding:12px 14px;background:#0d0d0d;border-top:1px solid #333333;font-size:clamp(11px, calc(11px + (100vw - 480px) / 240), 14px);font-weight:700;color:#cccccc;line-height:1.5;">\n'
            '    💡 <strong>調査結果：</strong> ' + bulb + '\n'
            '    <div style="font-size:clamp(9px, calc(9px + (100vw - 480px) / 240), 12px);color:#999999;margin-top:6px;">' + note + '</div>\n'
            '  </div>\n</div>\n<!-- /wp:html -->')


# ---------------------------------------------------------------- STAR
def star_timeline_item(time, body, desc=None, kind='mid'):
    """アーカイブパネルのタイムライン1項目。kind: open / mid / last"""
    if kind == 'mid':
        dot = '<div style="position: absolute; left: -19px; top: 4px; width: 8px; height: 8px; border-radius: 50%; background: #00B7B5; border: 2px solid #fff;"></div>'
    else:
        dot = '<div style="position: absolute; left: -21px; top: 4px; width: 12px; height: 12px; border-radius: 50%; background: #F26522; border: 2px solid #fff;"></div>'
    tw = '800' if kind != 'mid' else '700'
    d = ('<br>\n          <span style="font-size: clamp(11px, calc(11px + (100vw - 480px) / 240), 14px); color: #666;">' + desc + '</span>') if desc else ''
    return ('      <div style="position: relative; padding-bottom: 14px;">\n        ' + dot + '\n'
            '        <div style="font-size: 11px; color: #F26522; font-weight: ' + tw + ';">' + time + '</div>\n'
            '        <div style="font-size: 13px; color: #1a1a1a;">\n          ' + body + d + '\n        </div>\n      </div>')


def star_lineup_row(name, song, note, tint=False, last=False):
    bd = '' if last else ' border-bottom: 1px solid #f0f0f0;'
    bg = ' background: #fdf2ed;' if tint else ''
    return ('<div style="display: flex; flex-direction: column; padding: 10px 14px;' + bd + bg + '">\n'
            '  <div style="font-size: 13px; font-weight: 800; color: #1a1a1a;">' + name + '</div>\n'
            '  <div style="font-size: 12px; color: #00B7B5; margin-top: 2px; font-weight: 700;">' + song + '</div>\n'
            '  <div style="font-size: clamp(11px, calc(11px + (100vw - 480px) / 240), 14px); color: #666; margin-top: 2px;">' + note + '</div>\n'
            '</div>')


def star_schedule_block(time, text):
    """aside②（タイムテーブル速報）の2つ目以降の行"""
    return ('      <div style="display: flex; gap: 6px; align-items: flex-start; border-top: 1px dashed #eee; padding-top: 4px;">\n'
            '        <span style="color: #00B7B5; font-size: 12px;">✦</span>\n'
            '        <p style="margin: 0; font-size: 11.5px; color: #333;">\n'
            '          <strong>' + time + '</strong> ' + text + '\n'
            '        </p>\n'
            '      </div>')


def star_past_card(date_jp, date_dot, lines, bulb, new=False):
    """過去一覧（details内）のカード。lines は HTML行（<strong>時刻 名前</strong>：内容）のリスト"""
    tag = ' (NEW)' if new else ''
    return ('<!-- ======================= -->\n<!-- ' + date_dot + tag + ' -->\n<!-- ======================= -->\n'
            '<h3 style="margin:16px 0 10px;font-size:14px;font-weight:900;color:#1a1a1a;">\n' + date_jp + '放送回\n</h3>\n\n'
            '<div style="\nborder-radius:12px;\noverflow:hidden;\nborder:1px solid #eee;\nbackground:#fff;\nbox-shadow:0 6px 18px rgba(0,0,0,0.06);\n">\n\n'
            '<div style="height:4px;background:linear-gradient(90deg,#F26522,#00B7B5);"></div>\n\n'
            '<div style="padding:12px 14px;background:#fdfdfd;border-bottom:1px solid #eee;">\n'
            '  <div style="font-size:11px;font-weight:900;color:#F26522;">PAST LOG / STAR ARCHIVE</div>\n'
            '  <div style="font-size:14px;font-weight:900;color:#1a1a1a;">' + date_dot + '</div>\n</div>\n\n'
            '<div style="padding:14px;font-size:clamp(12px, calc(12px + (100vw - 480px) / 240), 15px);line-height:1.8;color:#333;">\n\n' + '<br>\n'.join(lines) + '\n\n</div>\n\n'
            '<div style="padding:10px 14px;background:#f7fafc;font-size:clamp(11px, calc(11px + (100vw - 480px) / 240), 14px);color:#666;">\n' + bulb + '\n</div>\n\n</div>\n')
