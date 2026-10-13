"""類似チェック用の「元ネタの本文ファイル」を、ローカルに溜めたデータから作る（Claudeのトークンは使わない）。

何のために：  brands/tools/check_similarity.py の --sources に渡すファイルを作る。
              これまでは、元ネタの本文を Chrome で取り直していたが、Threads は Chrome で読めない（過去に何度も失敗）。
              本文は research_data/ にすでにあるので、そこから作る。
使い方：  py -3 export_sources.py <投稿のURLまたはID> [<URLまたはID> ...]
出力：    research_data/tmp/sources_<日時>.txt（「=== 投稿ID」区切り。gitには入らない。使い終わったら消してよい）
          続けて： python brands/tools/check_similarity.py <投稿案ファイル> --sources <出力ファイル>
注意：    スレッズの本文は、検索画面に出ていた分で、長い投稿は途中までの場合がある（その場合は警告を出す）。
          その場合は「機械チェックは目安。着想の近さ（人の判定）を必ず行う」。
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "research_data"


def code_of(s):
    s = s.strip().rstrip("/")
    s = re.sub(r"/media$", "", s)
    return s.split("/")[-1].split("?")[0]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    wanted = [code_of(a) for a in sys.argv[1:]]
    found = {}
    for f in sorted(DATA_DIR.glob("threads_*.jsonl")) + sorted(DATA_DIR.glob("x_posts*.jsonl")):
        # splitlines()は本文中の特殊な行区切りでも切れるので使わない
        for line in f.read_text(encoding="utf-8").split(chr(10)):
            if not line.strip():
                continue
            r = json.loads(line)
            c = code_of(r["url"])
            if c in wanted:
                # 同じ投稿が複数のファイルにあるときは、本文が長いほうを使う
                if c not in found or len(r.get("text", "")) > len(found[c].get("text", "")):
                    found[c] = r
    out_dir = DATA_DIR / "tmp"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / ("sources_%s.txt" % datetime.now().strftime("%Y%m%d_%H%M%S"))
    chunks, warns, missing = [], [], []
    for c in wanted:
        r = found.get(c)
        if r is None:
            missing.append(c)
            continue
        text = r.get("text", "").strip()
        if not text:
            warns.append("%s：本文が空（画像のみ）。機械チェックはできません" % c)
        elif r.get("platform") != "x" and (text.endswith("…") or len(text) < 30):
            warns.append("%s：スレッズの本文は途中までの可能性があります（機械チェックは目安）" % c)
        chunks.append("=== %s\n%s\n" % (c, text))
    path.write_text("\n".join(chunks), encoding="utf-8")
    print("作成：%s（%d件）" % (path.relative_to(ROOT), len(chunks)))
    for w in warns:
        print("警告：" + w)
    for m in missing:
        print("見つからない：%s（データにない投稿。Chromeで本文を取り直す）" % m)


if __name__ == "__main__":
    main()
