"""類似チェック用の「元ネタの本文ファイル」を、ローカルに溜めたデータから作る（Claudeのトークンは使わない）。

何のために：  brands/tools/check_similarity.py の --sources に渡すファイルを作る。
              これまでは、元ネタの本文を Chrome で取り直していたが、Threads は Chrome で読めない（過去に何度も失敗）。
              本文は research_data/ にすでにあるので、そこから作る。
説明書：  docs/sop/sop_research_auto_collect.md
使い方：  py -3 export_sources.py <投稿のURLまたはID> [<URLまたはID> ...]
出力：    research_data/tmp/sources_<日時>.txt（「=== 投稿ID」区切り。gitには入らない。使い終わったら消してよい）
          続けて： python brands/tools/check_similarity.py <投稿案ファイル> --sources <出力ファイル>
注意：    スレッズの本文は、検索画面に出ていた分で、長い投稿は途中までの場合がある（その場合は警告を出す）。
          その場合は「機械チェックは目安。着想の近さ（人の判定）を必ず行う」。
"""
import sys
from datetime import datetime

import research_common as rc

ROOT, DATA_DIR, code_of = rc.ROOT, rc.DATA_DIR, rc.post_code


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    wanted = [code_of(a) for a in sys.argv[1:]]
    found = {}
    for f in (DATA_DIR / "threads_posts.jsonl", DATA_DIR / "x_posts.jsonl"):
        for r in rc.load_jsonl(f).values():
            c = code_of(r["url"])
            if c in wanted:
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
