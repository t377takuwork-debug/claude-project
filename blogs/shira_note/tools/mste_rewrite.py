"""Mステ記事のリライトを、データ（JSON）から一括で行う道具（2026-10-23新設）

ドラフトを全文読まずに、目印の文字列で書き換え位置を探して差し替える。部品は tools/mste_parts.py（公開済みの記事と一致をテスト済み）。
書き込みは最後に1回だけ。どれか1つでも目印が見つからない・複数ある場合は、1文字も書かずに止まる。

実行:
    python tools/mste_rewrite.py データ.json                  # drafts/draft_mste.txt を書き換える
    python tools/mste_rewrite.py データ.json --target 別.txt   # 別ファイルへ（テスト用。前回のデータは保存しない）
    python tools/mste_rewrite.py データ.json --jsonld-input 別.json   # JSON-LDの入力ファイルの置き場所（テスト用）
    python tools/mste_rewrite.py データ.json --no-save         # 前回のデータとして保存しない

本番のdraftを書き換えると、使ったデータを tools/output/mste_data_latest.json に残す（次回はこれを読めば、ドラフトの全文を読まずに済む）。
データの形は tools/output/mste_data_latest.json（最後に公開した回）か tools/mste_data_example_1023.json（テストで固定した実例）を見る。
キーを省くと、その部分は書き換えない。
"""
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from draft_patch import Patch  # noqa
from mste_parts import *  # noqa


def run(data, target, jsonld_input):
    p = Patch(target)
    L = p.L

    def find(pat, start=1, must=True):
        rx = re.compile(pat)
        for n in range(start, len(L) + 1):
            if rx.search(L[n - 1]):
                return n
        assert not must, ('目印が見つかりません', pat, '行', start, '以降')
        return None

    def rfind(pat, a, b):
        last = None
        for n in range(a, b + 1):
            if re.search(pat, L[n - 1]):
                last = n
        assert last, ('目印が見つかりません', pat)
        return last

    def html_inner(h2_pat):
        h = find(h2_pat)
        a = find(r'^<!-- wp:html -->$', h)
        b = find(r'^<!-- /wp:html -->$', a)
        return a + 1, b - 1

    def para(n, text):
        assert L[n - 1].startswith('<p>') and L[n - 1].endswith('</p>'), ('段落の行ではありません', n, L[n - 1][:40])
        p.R(n, n, '<p>' + text + '</p>')

    d = data
    # ---- タイトル・メタ
    if 'title' in d:
        t = find(r'^タイトル：')
        assert L[t].startswith('メタディスクリプション（')
        p.R(t, t, 'タイトル：' + d['title'])
        p.R(t + 1, t + 1, 'メタディスクリプション（' + str(len(d['meta'])) + '字）：')
        p.R(t + 2, t + 2, d['meta'])

    # ---- 冒頭2段落
    if 'lead' in d:
        n1 = find(r'\[nopc\]\[title\]')
        l1 = find(r'^<p>', n1 + 1)
        l2 = find(r'^<p>', l1 + 1)
        para(l1, d['lead'][0])
        para(l2, d['lead'][1])

    # ---- aside（番組情報まとめ）
    if 'aside' in d:
        A = d['aside']
        a0 = find(r'aria-label="Mステ最新情報"')
        n = find(r'>LIVE</span>', a0) + 1
        p.R(n, n, '      ' + A['live'])
        n = find(r'>STATUS</div>', a0) + 2
        p.R(n, n, '          <strong style="font-weight: 800; color: #ff0084;">' + A['status'] + '</strong>')
        n = find(r'>ARTISTS</div>', a0) + 2
        p.R(n, n, '          ' + A['artists'])
        n = find(r'>TIMETABLE</div>', a0) + 2
        p.R(n, n, '          ' + A['timetable'])
        n = find('💡', a0) + 1
        p.R(n, n, '      <span>' + A['comment'] + '</span>')
        n = find(r'最終更新:', a0)
        p.R(n, n, '        最終更新: ' + A['updated'] + '<br>')

    # ---- 締め文の1段落目
    if 'closing1' in d:
        m = find(r'\[nopc\]\[mokujimae\]')
        para(find(r'^<p>', m + 1), d['closing1'])

    # ---- 最新タイムテーブル
    if 'tt_groups' in d:
        h2 = find(r'<h2>.*最新タイムテーブル')
        p.R(h2, h2, '<h2>' + d['tt_h2'] + '</h2>')
        n = find(r'^<p>', h2 + 1)
        para(n, d['tt_note'])
        s = n + 3
        assert L[s - 1] in ('<!-- wp:html -->', '<!-- wp:heading {"level":3} -->'), ('タイムテーブルの開始位置が違います', L[s - 1])
        sc = find(r'^<p>\[nopc\]\[originalsc\]', n)
        e = sc - 3
        assert L[e - 1] == '<!-- /wp:html -->', ('タイムテーブルの終了位置が違います', L[e - 1])
        blocks = []
        for g in d['tt_groups']:
            rows = []
            for r in g['rows']:
                if 'opening' in r:
                    rows.append(mste_tt_opening(r['opening']))
                else:
                    rows.append(mste_tt_row(r['time'], r['name'], r['songs'], last=r.get('last', False), badge=r.get('badge'), border=r.get('border', True)))
            card = mste_tt_card(g['aria'], rows,
                                header=mste_tt_header(g['header']) if g.get('header') else None,
                                footer=mste_tt_footer() if g.get('footer') else None)
            pre = (mste_h3(g['h3']) + '\n\n') if g.get('h3') else ''
            blocks.append(pre + '<!-- wp:html -->\n' + card + '\n<!-- /wp:html -->')
        p.R(s, e, '\n\n'.join(blocks))

    # ---- 出演者・歌唱曲一覧
    if 'lineup_cards' in d:
        h2 = find(r'<h2>Mステの出演者・歌唱曲一覧')
        p.R(h2, h2, '<h2>' + d['lineup_h2'] + '</h2>')
        para(find(r'^<p>.*放送『ミュージックステーション', h2), d['lineup_intro'])
        n = find(r'ARTIST LINEUP \(')
        p.R(n, n, '<span style="color: #1a1a1a; font-size: 13px; font-weight: 900; letter-spacing: 0.05em;">ARTIST LINEUP (' + d['lineup_date_dot'] + ')</span>')
        g = find(r'flex-wrap: wrap; gap: 6px; margin-bottom: 12px;', h2)
        note = find('※放送内容および歌唱順', g)
        cs, ce = g + 2, note - 4
        assert L[ce - 1] == '  </div>' and L[ce] == '', ('出演者カードの終了位置が違います', L[ce - 1][:30])
        p.R(cs, ce, '\n\n'.join(mste_lineup_card(c['name'], c['text'], c.get('badge')) for c in d['lineup_cards']), chk='<!--')

    # ---- 出演時間の目安・順番の傾向
    if 'guide' in d:
        a, b = html_inner(r'<h2>Mステの出演時間は何時頃')
        G = d['guide']
        p.R(a, b, mste_guide_block(G['date_label'], G['blocks'], G['footer']))
    if 'tendency' in d:
        a, b = html_inner(r'<h2>ミュージックステーションの順番の傾向')
        T = d['tendency']
        p.R(a, b, mste_tendency_cards(T['aria'], T['cards'], T['badge']))

    # ---- 実際の出演順（アーカイブパネル）
    if 'archive' in d:
        R = d['archive']
        h2 = find(r'<h2>ミュージックステーション（Mステ）の実際の出演順')
        para(find(r'^<p>', h2 + 1), R['intro'])
        pn = find(r'class="mst-archive-panel"')
        n = find(r'FRI</span>', pn)
        p.R(n, n, '      <div style="font-size: 11px; font-weight: 800; color: #a0aec0;">' + R['date_dot'] + ' <span style="font-weight: 400;">FRI</span></div>')
        n = find(r'>MAIN CAST</div>', pn) + 1
        p.R(n, n, '      <div style="font-size: 13px; font-weight: 700; color: #2d3748;">' + R['main_cast'] + '</div>')
        g = find(r'display: grid; gap: 0; margin-bottom: 16px; border-left: 2px solid #edf2f7', pn)
        ge = find(r'^    </div>$', g + 2)
        es, ee = g + 2, ge - 2
        assert L[ee - 1] == '      </div>' and L[ee] == '', ('出演順の記録の終了位置が違います', L[ee - 1][:30])
        ents = R['entries']
        p.R(es, ee, '\n\n'.join(mste_archive_entry(e['label'], e['title'], e['desc'], e.get('kind', 'n'), last=(i == len(ents) - 1)) for i, e in enumerate(ents)), chk='position: relative')
        n = find(r'>REPORT</span>', pn) + 1
        p.R(n, n, '      ' + R['report'])
        n = find(r'UPDATED:', pn)
        p.R(n, n, '        <div style="font-size: 8px; color: #a0aec0;">UPDATED: ' + R['updated'] + '</div>')

    # ---- YouTube
    if 'youtube' in d:
        ns = [n for n in range(1, len(L) + 1) if 'youtube.com/watch?v=' in L[n - 1]]
        assert len(ns) == 2, ('YouTubeのURLの行が2つではありません', ns)
        for n in ns:
            p.R(n, n, re.sub(r'(watch\?v=)[\w-]+', lambda m: m.group(1) + d['youtube'], L[n - 1]))

    # ---- 過去のタイムテーブル一覧
    if d.get('past_card'):
        det = find(r'^<details')
        end = find(r'^</details>', det)
        first = find(r'^<h3>', det)
        p.I(first, d['past_card'])
        if d.get('drop_oldest', True):
            last = rfind(r'^<h3>', det, end)
            p.D(last, end - 2, chk='<h3>')

    # ---- FAQ
    if 'faq' in d:
        a, b = html_inner(r'<h2>よくある質問')
        p.R(a, b, mste_faq_cards([(q, an) for q, an in d['faq']]))

    # ---- まとめ
    if 'summary' in d:
        h2 = find(r'<h2>【まとめ】')
        na = find(r'^<!-- wp:html -->$', h2)
        ps, pe = h2 + 3, na - 2
        assert L[ps - 1] == '<!-- wp:paragraph -->' and L[pe - 1] == '<!-- /wp:paragraph -->', ('まとめの範囲が違います',)
        p.R(ps, pe, '\n\n'.join('<!-- wp:paragraph -->\n<p>' + t + '</p>\n<!-- /wp:paragraph -->' for t in d['summary']))

    # ---- JSON-LD（build_mste_jsonld.py に任せる）
    if 'jsonld' in d:
        J = dict(d['jsonld'])
        J['title'], J['meta_description'], J['faq'] = d['title'], d['meta'], [{'q': q, 'a': a} for q, a in d['faq']]
        io.open(jsonld_input, 'w', encoding='utf-8', newline='\n').write(json.dumps(J, ensure_ascii=False, indent=2))
        r = subprocess.run([sys.executable, os.path.join(HERE, 'build_mste_jsonld.py'), jsonld_input], capture_output=True, cwd=ROOT)
        sys.stderr.write(r.stderr.decode('utf-8', 'replace'))
        assert r.returncode == 0, 'build_mste_jsonld.py が失敗しました'
        out = r.stdout.decode('utf-8').replace('\r\n', '\n').strip('\n')
        j0 = rfind(r'^<!-- wp:shortcode -->$', 1, len(L))
        j1 = find(r'^<!-- /wp:shortcode -->$', j0)
        p.R(j0, j1, out)

    p.apply()


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    args = sys.argv[1:]
    if not args or args[0].startswith('-'):
        print(__doc__)
        sys.exit(0)
    target = 'draft_mste.txt'
    jin = os.path.join(HERE, 'output', 'mste_jsonld_input.json')
    if '--target' in args:
        target = args[args.index('--target') + 1]
    if '--jsonld-input' in args:
        jin = args[args.index('--jsonld-input') + 1]
    data = json.load(io.open(args[0], encoding='utf-8'))
    run(data, target, jin)
    # 本番のdraftを書き換えたときは、使ったデータを「前回のデータ」として残す（次回はこれを読めばよい。ドラフトの全文は読まない）
    if '--target' not in args and '--no-save' not in args:
        latest = os.path.join(HERE, 'output', 'mste_data_latest.json')
        if os.path.abspath(args[0]) != os.path.abspath(latest):
            io.open(latest, 'w', encoding='utf-8', newline='\n').write(json.dumps(data, ensure_ascii=False, indent=2))
            print('saved ->', os.path.relpath(latest, ROOT))
