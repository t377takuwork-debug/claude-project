#!/usr/bin/env python3
"""
generate_jsonld.py  JSON-LD 出演者データ生成ツール

【使い方】
  python tools/generate_jsonld.py              # 標準入力から読み込み（空行2連続 or Ctrl+Z で終了）
  python tools/generate_jsonld.py artists.txt  # テキストファイルから読み込み

【入力フォーマット（1行1アーティスト）】
  SixTONES             → 自動判定 → MusicGroup
  坂本冬美              → 自動判定 → Person
  NewJeans [G]         → [G] タグで強制グループ指定
  山下智久 [P]          → [P] タグで強制ソロ指定
  # コメント行は無視・空行は無視

【出力セクション】
  [1] mentions / performer 配列  （mste・cdtv 共通）
  [2] itemListElement 配列       （ItemList 用）
  [3] keywords 文字列            （CDTV 用）
  [4] numberOfItems カウント
"""

import io
import json
import sys
import re

# Windows cp932 環境でも UTF-8 で出力する
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── グループ判定ルール ──────────────────────────────────────────────────────
# 優先順：[G]/[P] タグ > キーワード > 末尾パターン > デフォルト（MusicGroup）

GROUP_KEYWORDS = [
    "&", "×",                        # コラボ・連名
    "グループ", "group", "バンド",    # 種別語
    "ボーイズ", "ガールズ", "BOYS", "GIRLS",
]

# 末尾がこれで終わるソロ名前パターン（姓名の苗字・名前の組み合わせ）
# ひらがな・カタカナ・漢字のみで構成され、スペースなし → Personの可能性が高い
SOLO_PATTERN = re.compile(r"^[぀-ゟ゠-ヿ一-鿿]{2,6}$")


def classify(name: str) -> str:
    """アーティスト名を MusicGroup / Person に分類する"""
    # キーワードチェック
    for kw in GROUP_KEYWORDS:
        if kw.lower() in name.lower():
            return "MusicGroup"
    # 純粋な日本語2〜6文字（苗字＋名前の典型パターン）→ Person
    if SOLO_PATTERN.match(name):
        return "Person"
    # 上記に当てはまらない場合はグループとみなす（Mステ/CDTVは多数派）
    return "MusicGroup"


def parse_artists(lines: list[str]) -> list[dict]:
    """入力行をパースして {name, type, uncertain} のリストを返す"""
    artists = []
    for raw in lines:
        line = raw.strip()
        line = line.lstrip("﻿")  # BOM 除去
        if not line or line.startswith("#"):
            continue

        uncertain = False

        # 明示タグの抽出
        if line.endswith("[G]"):
            artist_type = "MusicGroup"
            name = line[:-3].strip()
        elif line.endswith("[P]"):
            artist_type = "Person"
            name = line[:-3].strip()
        else:
            name = line
            artist_type = classify(name)
            # キーワードにも末尾パターンにも当てはまらなかった場合は要確認
            if not any(kw.lower() in name.lower() for kw in GROUP_KEYWORDS) \
                    and not SOLO_PATTERN.match(name):
                uncertain = True

        artists.append({"name": name, "type": artist_type, "uncertain": uncertain})
    return artists


def build_mentions(artists: list[dict]) -> str:
    """mentions / performer 用 JSON 配列を生成"""
    items = [{"@type": a["type"], "name": a["name"]} for a in artists]
    return json.dumps(items, ensure_ascii=False, indent=2)


def build_item_list(artists: list[dict]) -> str:
    """ItemList.itemListElement 用 JSON 配列を生成"""
    items = [
        {"@type": "ListItem", "position": i + 1, "name": a["name"]}
        for i, a in enumerate(artists)
    ]
    return json.dumps(items, ensure_ascii=False, indent=2)


def build_keywords(artists: list[dict]) -> str:
    """CDTV 用 keywords 文字列（カンマ区切り）を生成"""
    return ", ".join(f'"{a["name"]}"' for a in artists)


def read_input(source) -> list[str]:
    lines = []
    consecutive_blank = 0
    for line in source:
        if line.strip() == "":
            consecutive_blank += 1
            if consecutive_blank >= 2:
                break
        else:
            consecutive_blank = 0
            lines.append(line)
    return lines


def main():
    # 入力取得
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            lines = f.readlines()
    else:
        print("出演者を1行1名で入力してください（空行2連続で終了）:")
        print("  グループ → そのまま or [G] 付き")
        print("  ソロ     → [P] 付き推奨（例: 坂本冬美 [P]）")
        print("-" * 50)
        lines = read_input(sys.stdin)

    artists = parse_artists(lines)

    if not artists:
        print("[!]  アーティストが1件も読み込めませんでした。", file=sys.stderr)
        sys.exit(1)

    # 要確認アーティストを警告表示
    uncertain = [a for a in artists if a["uncertain"]]
    if uncertain:
        print("\n[!]  以下は自動判定（MusicGroup）— 要確認:", file=sys.stderr)
        for a in uncertain:
            print(f"   {a['name']} → {a['type']}", file=sys.stderr)

    # ── 出力 ──────────────────────────────────────────────────────────────
    sep = "─" * 60

    print(f"\n{sep}")
    print("[1] mentions / performer 配列（mste・cdtv 共通）")
    print(sep)
    print(build_mentions(artists))

    print(f"\n{sep}")
    print("[2] itemListElement 配列（ItemList 用）")
    print(sep)
    print(build_item_list(artists))

    print(f"\n{sep}")
    print("[3] keywords 文字列（CDTV 用）")
    print(sep)
    print(build_keywords(artists))

    print(f"\n{sep}")
    print("[4] numberOfItems")
    print(sep)
    print(len(artists))

    print(f"\n{sep}")
    print("[確認] 判定結果一覧")
    print(sep)
    for a in artists:
        flag = " [!] 要確認" if a["uncertain"] else ""
        print(f"  {a['type']:<12}  {a['name']}{flag}")


if __name__ == "__main__":
    main()
