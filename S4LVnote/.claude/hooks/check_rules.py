#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_rules.py — s4lv の決まりのファイルに、食い違いの元が残っていないか調べる。

調べること:
  1. もう使わない言葉・旧いファイル名が残っていないか（RETIRED）
  2. 決まりが名前を挙げているファイルが実在するか

使い方:
  python .claude/hooks/check_rules.py

0件なら終了コード0。1件でもあれば一覧を出して終了コード1。
決まりを変えて、もう使わない言葉・ファイル名ができたら、RETIRED に1行足す
（手順は S4LVnote/CLAUDE.md「決まりを変える手順」）。
"""
import argparse
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# --- 調べるファイル（リポジトリの一番上からの場所） -------------------------
# s4lv の決まり・手順・審査・記録。言葉と、名前を挙げた先の両方を調べる
OWN_FILES = [
    "S4LVnote/CLAUDE.md",
    "S4LVnote/使い方.md",
    "S4LVnote/0_社長室/*.md",
    "S4LVnote/0_社長室/S4LV設定/*.md",
    "S4LVnote/1_企画部/社員.md",
    "S4LVnote/2_商品開発部/*.md",
    "S4LVnote/3_広報部/*.md",
    "S4LVnote/3_広報部/スレッズ道具/*.md",
    "S4LVnote/3_広報部/投稿文/*.txt",
    "S4LVnote/3_広報部/投稿文/archive/*.txt",
    "S4LVnote/.claude/agents/*.md",
    "S4LVnote/.claude/skills/*/SKILL.md",
]
# ほかのアカウントと共用のファイルと、材料の置き場。言葉だけ調べる
SHARED_FILES = [
    "journals/external_seeds.md",
    "journals/content_seeds.md",
    "brands/CLAUDE.md",
    "brands/sns_reply_guideline.md",
    "S4LVnote/.claude/hooks/*.py",
    "S4LVnote/3_広報部/スレッズ道具/*.py",
    "brands/reference/x_algorithm_2026.md",
    "brands/reference/threads_algorithm_2026.md",
    ".claude/commands/neta-research.md",
    ".claude/commands/reply.md",
    ".claude/commands/post-review.md",
    ".claude/commands/journal.md",
    ".claude/agents/post-writer.md",
    "journals/CLAUDE.md",
    "docs/business_inventory.md",
    "README.md",
]
# 調べないファイル（この道具自身）
SKIP_NAMES = {"check_rules.py"}
# Note記事の決まり。言葉だけ調べる（名前を挙げた先は調べない）
TERMS_ONLY_NAMES = {"project_s4lv_note_article_process.md", "note_article_checklist.md"}
# これから作る予定のファイル（まだ無くてよい）
ALLOW_MISSING = {"s4lv_learnings_archive.md"}

# --- もう使わない言葉・旧いファイル名 ----------------------------------------
# (説明, 正規表現, 範囲)  範囲: "all"＝全部のファイル／"own"＝s4lvのファイルだけ
RETIRED = [
    # 旧いファイル名
    ("旧いファイル名", r"feedback_s4lv_threads_writing_style", "all"),
    ("旧いファイル名", r"feedback_s4lv_x_writing_style", "all"),
    ("旧いファイル名", r"feedback_s4lv_x_post", "all"),
    ("旧いファイル名", r"sns_kutouten_kaigyo_rules", "all"),
    ("旧いファイル名", r"examples_x_posts", "all"),
    ("旧いファイル名", r"ai_work_log", "all"),
    ("旧いファイル名", r"project_s4lv_identity", "all"),
    ("旧いファイル名", r"s4lv_knowledge_inventory", "all"),
    ("旧いファイル名", r"s4lv_sns_consolidation_brief|s4lv_sns_common_rules_draft", "all"),
    ("旧いファイル名", r"s4lv/sns_post_cheatsheet", "all"),
    ("旧いファイル名", r"(?<!mbticode/)(?<!uya/)sns_post_cheatsheet", "own"),
    ("旧いファイル名", r"sync_neta_usage", "all"),
    ("旧い呼び名", r"s4lv-research", "all"),
    ("旧い入口(2026-10-11に消した)", r"/s4lv-post", "all"),
    ("旧い場所(2026-10-11に消した)", r"brands/s4lv/", "own"),
    ("旧い呼び名", r"s4lv_ai|s4lv_pro", "all"),
    ("旧い呼び名", r"チートシート", "own"),
    ("旧い呼び名", r"Step ?3\.5", "own"),
    # 旧文体の言葉
    ("旧文体の言葉", r"記憶のゆらぎ", "all"),
    ("旧文体の言葉", r"エグい比喩", "all"),
    ("旧文体の言葉", r"情景ワード", "all"),
    ("旧文体の言葉", r"僕ら", "all"),
    ("旧文体の言葉", r"ライブ感", "all"),
    ("旧文体の言葉", r"情緒サンドイッチ", "all"),
    ("旧文体の言葉", r"確定構造", "all"),
    ("旧文体の言葉", r"弱さの?開示\s*→", "all"),
    ("旧文体の言葉", r"ハッカー的ワクワク", "all"),
    ("旧文体の言葉", r"です/ます.{0,8}だ/である", "all"),
    ("旧文体の言葉", r"いいね・RP", "all"),
    ("旧文体の言葉", r"文体OS", "own"),
]

REF_RE = re.compile(r"`([^`\s]+\.(?:md|py|txt|json|gs|ps1))`")
REF_SKIP = ("*", "<", "{", "YYYY", "…", "◯", "XX", "MMDD", "日付")
IGNORE_DIRS = {".git", "node_modules", "__pycache__", "worktrees"}


def expand(repo, patterns):
    out = []
    for pat in patterns:
        for p in sorted(repo.glob(pat)):
            if p.is_file() and p.name not in SKIP_NAMES and p not in out:
                out.append(p)
    return out


def build_index(repo):
    """リポジトリ内の全ファイルを、/区切りの相対パスで集める。"""
    idx = []
    stack = [repo]
    while stack:
        d = stack.pop()
        try:
            entries = list(d.iterdir())
        except OSError:
            continue
        for e in entries:
            if e.is_dir():
                if e.name not in IGNORE_DIRS:
                    stack.append(e)
            else:
                idx.append(e.relative_to(repo).as_posix())
    return idx


def ref_exists(token, src, repo, index, names):
    tok = token.replace("\\", "/")
    if tok.startswith("./"):
        tok = tok[2:]
    if any(s in tok for s in REF_SKIP) or tok.rsplit("/", 1)[-1] in ALLOW_MISSING:
        return True
    if "/" not in tok:
        return tok in names
    bases = [src.parent, repo / "S4LVnote", repo]
    if any((b / tok).is_file() for b in bases):
        return True
    return any(i == tok or i.endswith("/" + tok) for i in index)


def main():
    ap = argparse.ArgumentParser(description="s4lv の決まりの検査")
    ap.add_argument("--repo", default=None, help="リポジトリの場所（ふつうは指定しない）")
    args = ap.parse_args()
    repo = Path(args.repo) if args.repo else Path(__file__).resolve().parents[3]

    own_all = expand(repo, OWN_FILES)
    own = [p for p in own_all if p.name not in TERMS_ONLY_NAMES]
    shared = [p for p in own_all if p.name in TERMS_ONLY_NAMES]
    shared += [p for p in expand(repo, SHARED_FILES) if p not in own_all]
    index = build_index(repo)
    names = {i.rsplit("/", 1)[-1] for i in index}

    term_hits, ref_hits = [], []
    for path, scope in [(p, "own") for p in own] + [(p, "shared") for p in shared]:
        rel = path.relative_to(repo).as_posix()
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for n, line in enumerate(lines, 1):
            for label, pat, rng in RETIRED:
                if rng == "own" and scope != "own":
                    continue
                m = re.search(pat, line)
                if m:
                    term_hits.append(f"  {rel}:{n}  {label}「{m.group(0)}」")
            if scope == "own":
                for m in REF_RE.finditer(line):
                    if not ref_exists(m.group(1), path, repo, index, names):
                        ref_hits.append(f"  {rel}:{n}  `{m.group(1)}`")

    print("=== s4lv 決まりの検査 ===")
    print(f"調べたファイル: {len(own) + len(shared)}本")
    print(f"[もう使わない言葉・旧いファイル名] {len(term_hits)}件")
    for h in term_hits:
        print(h)
    print(f"[名前を挙げた先が実在しない] {len(ref_hits)}件")
    for h in ref_hits:
        print(h)
    total = len(term_hits) + len(ref_hits)
    print(f"=== 結果: 合計 {total}件 ===")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
