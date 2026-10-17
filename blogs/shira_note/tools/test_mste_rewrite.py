"""mste_rewrite.py（データから記事を一括で書き換える道具）が、公開した記事を再現できることを確認する

実行: python tools/test_mste_rewrite.py
やること: 10/16回の公開版（263e7ab6）に、10/23回のデータ（tools/mste_data_example_1023.json）を当てて書き換え、
          10/23回の公開版（WANT_REV）と1文字も違わないことを確かめる。
道具・部品・データの形を直したら必ず実行する（デザインを意図して変えたときは、WANT_REVも新しい公開版に付け替える）。
"""
import io
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mste_rewrite  # noqa

REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
BASE_REV = '263e7ab6'
WANT_REV = 'b07d6f68'


def show(rev):
    r = subprocess.run(['git', 'show', rev + ':blogs/shira_note/drafts/draft_mste.txt'], cwd=REPO, capture_output=True)
    assert r.returncode == 0, ('git show に失敗', rev)
    return r.stdout.decode('utf-8').replace('\r\n', '\n')


def main():
    want_path = sys.argv[1] if len(sys.argv) > 1 else None   # 比べる相手を作業中のファイルにしたいときだけ指定
    want = io.open(want_path, encoding='utf-8', newline='').read() if want_path else show(WANT_REV)
    d = tempfile.mkdtemp()
    tmp = os.path.join(d, 'draft.txt')
    io.open(tmp, 'w', encoding='utf-8', newline='\n').write(show(BASE_REV))
    data = json.load(io.open(os.path.join(HERE, 'mste_data_example_1023.json'), encoding='utf-8'))
    mste_rewrite.run(data, tmp, os.path.join(d, 'jsonld.json'))
    got = io.open(tmp, encoding='utf-8', newline='').read()
    if got == want:
        print('OK: データから再現した記事が、公開版と1文字も違わない')
        return 0
    import difflib
    print('NG: 公開版と違う箇所')
    for l in list(difflib.unified_diff(want.split('\n'), got.split('\n'), 'want', 'got', lineterm='', n=0))[:40]:
        print(l[:200])
    return 1


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
