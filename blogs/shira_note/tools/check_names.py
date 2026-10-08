"""出演者の反映漏れチェック（2026-10-08 オールスター感謝祭で、歴代優勝者9名が出演者一覧に入っていなかった反省から新設）

使い方:
  python tools/check_names.py draft_allstar.txt --names-file tools/output/allstar_names.txt
  python tools/check_names.py draft_allstar.txt 横浜流星 小栗旬 ...
  --aside '出演者一覧' で、一覧のasideを探す目印（aria-labelの一部）を指定できる（省略時は本文全体で確認）

資料①の「報道で名前が挙がった出演者・出場者」を1行1名（「名前（所属）」の括弧は無視）で書き出して渡す。
確認するもの:
  1. 出演者一覧（aside。--aside指定時）に名前があるか
  2. JSON-LD（mentions / performer / ItemList）に名前があるか
漏れがあれば終了コード1。
"""
import argparse, os, re, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def norm(n):
    return re.sub(r"[（(].*?[）)]", "", n).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("names", nargs="*")
    ap.add_argument("--names-file")
    ap.add_argument("--aside", help="出演者一覧asideのaria-labelの一部（例: 出演者一覧）")
    a = ap.parse_args()

    path = a.file if os.path.isabs(a.file) else os.path.join(BASE, "drafts", os.path.basename(a.file))
    text = open(path, encoding="utf-8").read()
    names = [norm(n) for n in a.names]
    if a.names_file:
        names += [norm(l) for l in open(a.names_file, encoding="utf-8").read().splitlines() if l.strip() and not l.startswith("#")]
    names = [n for n in dict.fromkeys(names) if n]
    if not names:
        print("名前が指定されていません")
        return 2

    jl_start = text.find("[jsonld]")
    jl_end = text.find("[/jsonld]")
    jsonld = text[jl_start:jl_end] if jl_start >= 0 and jl_end > jl_start else ""

    aside = ""
    if a.aside:
        m = re.search(r'aria-label="[^"]*' + re.escape(a.aside) + r'[^"]*"', text)
        if not m:
            print(f"[ERROR] aside（{a.aside}）が見つかりません")
            return 2
        s = text.rfind("<aside", 0, m.start())
        e = text.find("</aside>", m.end())
        aside = text[s:e]

    miss = 0
    for n in names:
        problems = []
        if a.aside and n not in aside:
            problems.append("出演者一覧に無い")
        if jsonld and f'"name": "{n}"' not in jsonld:
            problems.append("JSON-LDに無い")
        if not a.aside and n not in text:
            problems.append("本文に無い")
        if problems:
            miss += 1
            print(f"[漏れ] {n}: " + " / ".join(problems))
    print(f"--- 確認 {len(names)}名 / 漏れ {miss}名 ---")
    return 1 if miss else 0


if __name__ == "__main__":
    sys.exit(main())
