"""検索語ごとに「候補になった数」と「実際に元ネタに使った数」を数えて、語の見直しの材料にする（トークン0）。

説明書： docs/sop/sop_research_auto_collect.md「語を見直すとき」
使い方： py -3 research/keyword_yield.py
読むもの： research/data/shortlist/shortlist_s4lv_UYA_*.md（候補。拾った語の列と、URLの列）
          S4LVnote/3_広報部/投稿文/posts_x.txt・posts_threads.txt と archive/ の中（見出しの元ネタのURL）
出すもの： 語ごとの表（候補数・使った数）。語を入れ替えるかどうかは、あなたが決める。ファイルは書き換えない。
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
SHORTLIST_DIR = ROOT / "data" / "shortlist"
POSTS_DIR = REPO / "S4LVnote" / "3_広報部" / "投稿文"

# 投稿のURLから、同じ投稿かどうかを見分ける番号（X＝status/数字、スレッズ＝post/英数字）
ID_RE = re.compile(r"(?:status/(\d+))|(?:post/([A-Za-z0-9_-]+))")


def post_id(url):
    m = ID_RE.search(url)
    return (m.group(1) or m.group(2)) if m else None


def read_candidates():
    """候補ファイルの表から、{投稿の番号: (媒体, [拾った語])} を作る。同じ投稿は1回だけ数える。"""
    found = {}
    for path in sorted(SHORTLIST_DIR.glob("shortlist_s4lv_UYA_*.md")):
        for line in path.read_text(encoding="utf-8").split("\n"):
            if not line.startswith("|"):
                continue
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            # 列：# 媒体 勢い 反響点 いいね 返信 再投稿 保存数 保存率 表示数 投稿日 経過 投稿者 フォロワー 拾った語 本文 URL
            if len(cols) < 17 or not cols[0].isdigit():
                continue
            pid = post_id(cols[16])
            if pid and pid not in found:
                found[pid] = (cols[1], [k.strip() for k in cols[14].split("／") if k.strip()])
    return found


def read_adopted():
    """投稿文の見出し（【…】の行）にあるURLの番号を集める。"""
    ids = set()
    files = [POSTS_DIR / "posts_x.txt", POSTS_DIR / "posts_threads.txt"]
    files += sorted((POSTS_DIR / "archive").glob("*.txt")) if (POSTS_DIR / "archive").exists() else []
    for path in files:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").split("\n"):
            if line.startswith("【") and "元ネタ＝" in line:
                for m in re.finditer(r"https?://\S+", line):
                    pid = post_id(m.group(0))
                    if pid:
                        ids.add(pid)
    return ids


def main():
    if not SHORTLIST_DIR.exists():
        print("候補ファイルのフォルダがありません:", SHORTLIST_DIR)
        return 1
    cands = read_candidates()
    adopted = read_adopted()
    cand_n = defaultdict(int)
    used_n = defaultdict(int)
    for pid, (platform, kws) in cands.items():
        for kw in kws:
            cand_n[(platform, kw)] += 1
            if pid in adopted:
                used_n[(platform, kw)] += 1
    print(f"候補ファイル内の投稿 {len(cands)} 件（重複なし）／そのうち元ネタに使った {sum(1 for p in cands if p in adopted)} 件")
    print("※ 候補ファイルは14日で消えるため、数えられるのは直近約2週間。1つの投稿が複数の語に数えられる")
    print()
    print("| 媒体 | 拾った語 | 候補になった数 | 元ネタに使った数 |")
    print("|---|---|---|---|")
    for (platform, kw), n in sorted(cand_n.items(), key=lambda x: (-used_n[x[0]], -x[1], x[0])):
        print(f"| {platform} | {kw} | {n} | {used_n[(platform, kw)]} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
