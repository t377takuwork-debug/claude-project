#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""qa_article.py — Note記事ドラフト機械検品ツール（mbticode / s4lv / junk_juice 共通）

完了条件: ERROR 0件（終了コード0）。WARNは参考情報（人間が判断する）。

使い方:
  python brands/tools/qa_article.py "brands/mbticode/articles/drafts/○○.md"
  python brands/tools/qa_article.py <file> [--paid]   # 有料記事は --paid を付ける

チェック層:
  1. AI定型表現（どのアカウントの文体でも使わない語）… ERROR
  2. AIっぽさの兆候（要人間判断）… WARN
  3. 構造・保存先・文字数 … WARN / INFO

ルールの出典（変更時は出典を先に更新し本スクリプトを追従させる）:
  - .claude/commands/quality-guardrail.md（禁止表現の考え方）
  - brands/s4lv/rules/project_s4lv_note_article_process.md（AI臭さ除去3軸・——禁止・字数基準）
  - brands/writing/writing_core.md（PASONA導入・CTA具体化）
  - Junk314/junk_juice/rules/feedback_junk_paid_article.md（有料記事基準）
"""
import argparse
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# 層1: どの文体でも使わないAI定型表現（ERROR）
ERROR_PATTERNS = [
    ("ai-ikaga", r"いかがでしたか|いかがだったでしょうか", "「いかがでしたか」型の締め禁止（AI定型）"),
    ("ai-matome", r"以上のように|まとめると、", "要約フレーズ禁止（AI定型・guardrail）"),
    ("ai-dash", r"──|——", "ダッシュ記号禁止（s4lv AI臭さ除去3軸・全アカウント共通）"),
    ("ai-yobousen", r"個人差があります|一概には言えません", "責任回避の予防線禁止（guardrail）"),
]

# 層2: AIっぽさの兆候（WARN・人間判断）
WARN_PATTERNS = [
    ("ai-taisetsu", r"ことが大切です|ことが重要です", "「大切です/重要です」の抽象総括（guardrail系）"),
    ("ai-susume", r"をお勧めします|をおすすめします", "コンサル口調の疑い（guardrail系）"),
    ("ai-konoyouni", r"このように、", "説明の要約フレーズの疑い"),
    ("ai-ikagadeshou", r"いかがでしょうか", "問いかけの定型の疑い"),
]

# 層3: Note貼り付け時に崩れる記法（WARN・2026-07-09 s4lvトレンドブログ記事の実修正から追加）
NOTE_PASTE_WARN_PATTERNS = [
    ("note-list-dash", r"^- ", "Markdownリスト「- 」はNote貼り付けで崩れる可能性。テキストの「・」表記を推奨"),
    ("note-blank-quote", r"^>[ \t]*$", "引用ブロック内の空行「>」のみだとNote貼り付けで段落が潰れる可能性。全角スペースを挟んだ「>　」を推奨"),
    ("note-md-link", r"\[.+?\]\(https?://note\.com[^)]*\)", "note.comへのMarkdownリンク[text](url)はリンクカード化されない。裸URLを単独行に置くとカード化される"),
]


def sentences(text):
    return [s.strip() for s in re.split(r"[。！？!?]", text) if s.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--paid", action="store_true", help="有料記事として追加チェック")
    args = ap.parse_args()

    with open(args.file, encoding="utf-8") as fh:
        text = fh.read()

    errors, warns, infos = [], [], []

    # 層1・層2
    for code, pat, msg in ERROR_PATTERNS:
        for m in re.finditer(pat, text):
            line_no = text[:m.start()].count("\n") + 1
            errors.append(f"[ERROR] L{line_no} {code}: {msg}（「{m.group(0)}」）")
    for code, pat, msg in WARN_PATTERNS:
        for m in re.finditer(pat, text):
            line_no = text[:m.start()].count("\n") + 1
            warns.append(f"[WARN] L{line_no} {code}: {msg}（「{m.group(0)}」）")
    for code, pat, msg in NOTE_PASTE_WARN_PATTERNS:
        for m in re.finditer(pat, text, flags=re.M):
            line_no = text[:m.start()].count("\n") + 1
            warns.append(f"[WARN] L{line_no} {code}: {msg}")

    # 同一語尾の連続（4文連続で同じ末尾2字 → AI感の兆候）
    sents = sentences(re.sub(r"^#.*$", "", text, flags=re.M))
    run, prev = 1, None
    for s in sents:
        tail = s[-2:] if len(s) >= 2 else s
        if tail == prev:
            run += 1
            if run == 4:
                warns.append(f"[WARN] gobi-renzoku: 同一語尾「{tail}」が4文連続（語尾を3種類以上混在させる・s4lv AI臭さ除去）")
        else:
            run, prev = 1, tail

    # 構造チェック
    body = re.sub(r"^---.*?---\s*", "", text, flags=re.S)  # frontmatter除去
    char_count = len(re.sub(r"\s", "", body))
    infos.append(f"[INFO] 本文文字数（空白除く）: {char_count}字"
                 f"（s4lv無料記事基準は4,000字以上／980円帯は3,000〜5,000字）")
    if char_count > 2000 and not re.search(r"^#{2,3} ", text, flags=re.M):
        warns.append("[WARN] no-heading: 2,000字超で見出し（##）なし（スマホ縦読みでの離脱要因）")
    first45 = "\n".join(text.splitlines()[:45])  # 冒頭メタ情報（タイトル・タグ・構成）を考慮した窓
    if "？" not in first45 and "?" not in first45:
        warns.append("[WARN] no-question-intro: 記事冒頭に問いかけがない（PASONA導入Step.1「〇〇でお困りではないですか？」型の確認）")
    if not re.search(r"note\.com|http", text) and args.paid:
        warns.append("[WARN] no-cta-link: 有料記事にURL・CTAリンクが見当たらない（中間CTA最低2箇所・s4lvマネタイズ設計）")
    cta_like = len(re.findall(r"note\.com|有料記事", text))
    if char_count > 3000 and cta_like < 2:
        warns.append(f"[WARN] cta-count: CTA/有料記事への言及が{cta_like}箇所のみ（中間CTA最低2箇所・s4lvマネタイズ設計原則を下回っている可能性）")

    # 保存先チェック
    norm = args.file.replace("\\", "/")
    if "/articles/" not in norm:
        warns.append("[WARN] save-location: 保存先が articles/ 配下ではない（drafts保存ルール）")

    print(f"=== qa_article: {args.file}{'（有料）' if args.paid else ''} ===")
    for x in errors + warns + infos:
        print(x)
    print(f"=== 結果: ERROR {len(errors)}件 / WARN {len(warns)}件 ===")
    if errors:
        print("完了条件を満たしていません（ERROR 0件が必須）。")
        sys.exit(1)
    print("完了条件クリア（ERROR 0件）。WARNは人間が判断してください。")
    sys.exit(0)


if __name__ == "__main__":
    main()
