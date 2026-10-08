"""draftの複数箇所を一度に書き換える道具（2026-10-09新設）

CDTV・Venue101・STAR・オールスターのリライトで毎回同じ形のスクリプトを書いていたので共通化した。
安全装置:
  - 置換前の文字列が「その行に1回だけ」あることを確認する（違えば何も書かずに止まる）
  - 範囲置換は、先頭行に目印の文字列があることを確認する
  - 範囲が重なっていれば止まる
  - 書き込みは最後に1回だけ（途中で止まれば、ファイルは1文字も変わらない）
  - 部品HTMLの組み立てに「%」書式を使わない（CSSの 50% と衝突して失敗した実例あり）。文字列の足し算か .replace を使う

使い方（スクリプトの例）:
    import sys; sys.path.insert(0, r'tools')
    from draft_patch import Patch
    p = Patch('draft_star.txt')           # drafts/ 内のファイル名
    p.S(67, ('10.1 <span', '10.15 <span'))        # その行の中の置換（複数なら [(old,new),...]）
    p.R(2, 2, 'タイトル：…', chk='タイトル：')      # 行の範囲を丸ごと差し替え（chk=先頭行にある目印）
    p.I(712, '挿入したいテキスト')                  # 712行目の手前に挿入
    p.D(833, 869, chk='2026.08.06')                # 範囲を削除
    p.apply()                                      # 検証して一括書き込み

行番号はすべて「書き換え前の行番号」（Readした番号）で指定する。下から順に自動で適用するので、番号のずれは気にしなくてよい。
"""
import io
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Patch:
    def __init__(self, filename):
        self.path = filename if os.path.isabs(filename) else os.path.join(BASE, 'drafts', os.path.basename(filename))
        src = io.open(self.path, encoding='utf-8', newline='').read()
        assert '\r' not in src, '改行がCRLFです。先にLFへそろえてください'
        self.L = src.split('\n')
        self.ops = []  # (start, end, text)  end < start は「挿入」

    def _line(self, n):
        assert 1 <= n <= len(self.L), ('行番号が範囲外', n)
        return self.L[n - 1]

    def S(self, n, pairs):
        if isinstance(pairs, tuple):
            pairs = [pairs]
        line = self._line(n)
        for old, new in pairs:
            assert line.count(old) == 1, ('置換前の文字列が1回だけではありません', n, old[:40], line.count(old))
            line = line.replace(old, new)
        self.ops.append((n, n, line))

    def R(self, a, b, new, chk=None):
        if chk is not None:
            assert chk in self._line(a), ('先頭行に目印がありません', a, chk, self._line(a)[:60])
        assert a <= b <= len(self.L), ('範囲が不正', a, b)
        self.ops.append((a, b, new))

    def I(self, n, text):
        self._line(n)
        self.ops.append((n, n - 1, text))

    def D(self, a, b, chk=None):
        self.R(a, b, '', chk)

    def apply(self):
        ops = sorted(self.ops, key=lambda o: (o[0], o[1]), reverse=True)
        prev = None
        for a, b, _ in ops:
            if prev is not None and b >= prev:
                raise AssertionError(('範囲が重なっています', a, b, prev))
            prev = a
        L = list(self.L)
        for a, b, new in ops:
            seg = [] if new == '' else new.split('\n')
            if b < a:
                L[a - 1:a - 1] = seg
            else:
                L[a - 1:b] = seg
        out = '\n'.join(L)
        io.open(self.path, 'w', encoding='utf-8', newline='\n').write(out)
        print('ok', len(self.ops), 'ops ->', os.path.basename(self.path))
