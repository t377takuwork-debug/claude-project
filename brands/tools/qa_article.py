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
  4. フレームワーク用語の本文流入（感情トリガー等の制作側用語）… WARN
  5. 過去記事との言い回し重複（同アカウントの既存記事コーパスと照合）… WARN
  6. 同一記事内の重複（同じ文・言い直しが2回以上）… WARN

ルールの出典（変更時は出典を先に更新し本スクリプトを追従させる）:
  - .claude/commands/quality-guardrail.md（禁止表現の考え方）
  - brands/s4lv/rules/project_s4lv_note_article_process.md（AI臭さ除去3軸・——禁止・字数基準）
  - brands/writing/writing_core.md（PASONA導入・CTA具体化・AI臭さ除去の章＝層4〜6の出典）
  - Junk314/junk_juice/rules/feedback_junk_paid_article.md（有料記事基準）
"""
import argparse
import os
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
    ("number-setsu", r"\d+(\.\d+)?[%％]説", "「数字＋説」表現の疑い（2026-08-01、vivant新庄考察記事でユーザー指摘。論点を名付けた表現に置き換え推奨）"),
    ("gimonbun-kutouten", r"(ませんか|でしょうか|んですか|ますか|ですか)。", "疑問文は「か。」でなく「か？」を使う（2026-09-03、s4lvタイトル診断記事でユーザー指摘。writing_core.md 句読点ルール）"),
]

# 層3: Note貼り付け時に崩れる記法（WARN・2026-07-09 s4lvトレンドブログ記事の実修正から追加）
NOTE_PASTE_WARN_PATTERNS = [
    ("note-list-dash", r"^- ", "Markdownリスト「- 」はNote貼り付けで崩れる可能性。テキストの「・」表記を推奨"),
    ("note-blank-quote", r"^>[ \t]*$", "引用ブロック内の空行「>」のみだとNote貼り付けで段落が潰れる可能性。全角スペースを挟んだ「>　」を推奨"),
    ("note-md-link", r"\[.+?\]\(https?://note\.com[^)]*\)", "note.comへのMarkdownリンク[text](url)はリンクカード化されない。裸URLを単独行に置くとカード化される"),
    ("note-bold-bracket-open", r"\*\*[「『【]", "太字マーカー直後に開き括弧はNote貼り付けで太字が反映されない可能性（2026-08-01確認）。括弧を太字の外に出す"),
    ("note-bold-bracket-close", r"[」』】）]\*\*", "閉じ括弧の直後に太字マーカーはNote貼り付けで太字が反映されない可能性（2026-08-01確認）。括弧を太字の外に出す"),
    ("note-bold-percent", r"%\*\*", "「%」の直後に太字マーカーはNote貼り付けで太字が反映されない可能性（2026-08-01、新庄考察記事で確認）。`**95**%`のように%を太字の外に出す"),
]

# 層4: フレームワーク用語の本文流入（WARN・2026-09-03 ユーザー指摘）
# 記事を「作る側」の分析用語が読者向け本文に出ると、設計図が透けてAIっぽくなる。
# 平易な言葉に言い換える。対象は本文（ヘッダー除去後）のみ。
AI_JARGON_WARN = [
    ("ai-jargon-kanjo-trigger", r"感情トリガー", "「感情トリガー」は制作側の用語。『思わず反応してしまう言葉』等の平易な表現に言い換える"),
    ("ai-jargon-saigensei", r"再現性シグナル", "「再現性シグナル」は制作側の用語。『誰でも同じ手順で再現できると伝わる書き方』等に言い換える"),
    ("ai-jargon-benefit", r"ベネフィット", "「ベネフィット」→『読者にとっての得』『読むと何が変わるか』に言い換える"),
    ("ai-jargon-hook", r"フック(?!アップ)", "「フック」→『続きを読みたくなる仕掛け』に言い換える"),
    ("ai-jargon-persona", r"ペルソナ", "「ペルソナ」→『想定読者』『こういう人』に言い換える"),
    ("ai-jargon-pasona", r"PASONA|パソナの法則", "型の名前（PASONA等）を本文に出さない"),
    ("ai-jargon-cta", r"(?<![A-Za-z])CTA(?![A-Za-z])", "「CTA」→『行動の呼びかけ』または具体的な依頼文に言い換える"),
    ("ai-jargon-keni", r"権威性", "「権威性」→『信頼できる根拠』『実績』に言い換える"),
    ("ai-jargon-moura", r"網羅性", "「網羅性」→『抜けなく揃っている』に言い換える"),
    ("ai-jargon-sokuji", r"即時性", "「即時性」→『すぐに』『今日から』に言い換える"),
    ("ai-jargon-engage", r"エンゲージメント", "「エンゲージメント」→『反応』『いいねや保存』に言い換える"),
    ("ai-jargon-fw", r"フレームワーク|(?<![A-Za-z])FW(?![A-Za-z])", "「フレームワーク」「FW」→『考え方の型』『手順』に言い換える"),
]

# 層7: 文体・トーン（WARN・2026-09-04 writing_tone.md 1-1）。
# 4番目の要素は「このパス片を含むアカウントでは検知しない」（None=全アカウント）。
TONE_WARN_PATTERNS = [
    ("tone-omoimasu", r"と思います|と感じています|と思っています", "「〜と思います／感じています」は使わない。推量は「〜はず」「たぶん〜」（writing_tone 1-1）", None),
    ("tone-shimashou", r"しましょう|していきましょう", "「〜しましょう」のセミナー講師口調。呼びかけは「〜してみてください」まで（writing_tone 1-1）", None),
    ("tone-section", r"セクション", "「セクション」は本文で使わない→「ここ」「この記事」「〜欄」「〜一覧」（writing_tone 1-1）", None),
    ("tone-desune", r"ですね[。？]", "「〜ですね」の相槌語尾（writing_tone 1-1。vivantは可）", "/vivant/"),
]

# 層5-6用: 過去記事コーパスの所在（対象ファイルのパスから判定）
CORPUS_MAP = [
    ("/s4lv/", ["brands/s4lv/drafts"]),
    ("/mbticode/", ["brands/mbticode/articles/published", "brands/mbticode/articles/drafts"]),
    ("/junk_juice/", ["Junk314/junk_juice/articles/published", "Junk314/junk_juice/articles/drafts"]),
    ("/vivant/", ["vivant/articles/published", "vivant/articles/drafts"]),
]
SHINGLE_LEN = 20  # この文字数の連続一致を「同じ言い回し」とみなす（数字はマスクして比較）
_DIGIT_RE = re.compile(r"[0-9０-９]+")

# 層5で重複を報告しない「意図的に共通化している定型ブロック」（末尾の謝辞・更新履歴の断り書き・
# 有料記事の購入者保証・プロフィール署名など）。ここに載る語を含む文はコーパス一致してもスキップする。
# アカウント運用で新しい定型を足したらここに1行追加する。
CROSS_DUP_IGNORE = [
    "最後までお読みいただき",
    "追加料金なしで",
    "随時アップデート",
    "随時更新",
    "ご購入いただいた方",
    "本記事は", "免責", "情報は執筆時点",
    "恋愛の設計局",
    "この記事の内容は",
]


def sentences(text):
    return [s.strip() for s in re.split(r"[。！？!?]", text) if s.strip()]


def normalize_for_compare(s):
    """空白除去＋連続数字を0に潰す（「7曲」「12曲」の違いを同一視して言い回しの重複を拾う）。"""
    return _DIGIT_RE.sub("0", re.sub(r"\s+", "", s))


def strip_for_compare(text):
    """比較対象から外す行（見出し・引用・URL・箇条書き記号のみの行）を落とす。"""
    out = []
    for line in text.splitlines():
        st = line.strip()
        if not st or st.startswith("#") or st.startswith(">") or st.startswith("```"):
            continue
        if "http" in st or "note.com" in st:
            continue
        out.append(st.lstrip("-・*　 "))
    return "\n".join(out)


def load_corpus_files(target_file):
    """対象アカウントの既存記事ファイル一覧（対象ファイル自身は除く）。"""
    norm = target_file.replace("\\", "/")
    if not norm.startswith("/"):
        norm = "/" + norm  # 先頭ディレクトリ（vivant/ 等）も "/vivant/" で拾えるように
    tgt_abs = os.path.abspath(target_file)
    dirs = []
    for key, ds in CORPUS_MAP:
        if key in norm:
            dirs = ds
            break
    files = []
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".md") and os.path.abspath(os.path.join(d, fn)) != tgt_abs:
                files.append(os.path.join(d, fn))
    return files


def build_shingle_index(files):
    """コーパス全文の SHINGLE_LEN 文字シングル → 初出ファイル名 の辞書。"""
    idx = {}
    for p in files:
        try:
            with open(p, encoding="utf-8") as fh:
                t = normalize_for_compare(strip_for_compare(fh.read()))
        except OSError:
            continue
        name = os.path.basename(p)
        for i in range(len(t) - SHINGLE_LEN + 1):
            idx.setdefault(t[i:i + SHINGLE_LEN], name)
    return idx


def char_ngrams(s, n=4):
    return {s[i:i + n] for i in range(max(0, len(s) - n + 1))}


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

    # 読点過多チェック（1文に読点3つ以上 → 過剰読点の疑い。2026-09-03、s4lvタイトル診断記事でユーザー指摘。writing_core.md 句読点ルール）
    text_noheading = re.sub(r"^#.*$", "", text, flags=re.M)
    for m in re.finditer(r"[^。！？\n]*[。！？]", text_noheading):
        sent = m.group(0)
        if sent.count("、") >= 3:
            line_no = text_noheading[:m.start()].count("\n") + 1
            warns.append(f"[WARN] L{line_no} kutouten-kajou: 1文に読点{sent.count('、')}個（目安2つまで。読点を削るか文を分割する）（「{sent.strip()[:40]}...」）")

    # 構造チェック
    # ヘッダーは「作成日：〜Noteタグ：」の後に単独の「---」区切り行が1本のみ（前後ペア形式ではない）。
    # 旧・正規表現(^---.*?---)は先頭が"---"で始まる前提で壊れており、ヘッダーが本文に混入していた（2026-08-01修正）。
    fm_match = re.match(r"^.*?\n---[ \t]*\n", text, flags=re.S)
    body_start = fm_match.end() if fm_match else 0
    body = text[body_start:]
    char_count = len(re.sub(r"\s", "", body))
    infos.append(f"[INFO] 本文文字数（空白除く）: {char_count}字"
                 f"（s4lv無料記事基準は4,000字以上／980円帯は3,000〜5,000字）")
    if char_count > 2000 and not re.search(r"^#{2,3} ", text, flags=re.M):
        warns.append("[WARN] no-heading: 2,000字超で見出し（##）なし（スマホ縦読みでの離脱要因）")

    # H2直下のH3本数チェック（ルール：H3はH2内容が複数の独立サブトピックに分かれる場合のみ・2〜3本セットで使う。単独1本は禁止）
    headings = [(m.start(), len(m.group(1)), m.group(2)) for m in re.finditer(r"^(#{2,3}) (.+)$", text, flags=re.M)]
    cur_h2, h3_count = None, {}
    for pos, level, title in headings:
        line_no = text[:pos].count("\n") + 1
        if level == 2:
            cur_h2 = (line_no, title)
            h3_count[cur_h2] = 0
        elif level == 3 and cur_h2:
            h3_count[cur_h2] += 1
    for (line_no, title), count in h3_count.items():
        if count == 1:
            warns.append(f"[WARN] L{line_no} lone-h3: H2「{title}」直下のH3が1本のみ（ルールではH3は複数の独立サブトピックがある場合のみ・2〜3本セットで使う。単独H3は禁止）")
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

    # 層4: フレームワーク用語の本文流入（本文＝ヘッダー除去後のみ対象）
    for code, pat, msg in AI_JARGON_WARN:
        for m in re.finditer(pat, body):
            line_no = text[:body_start + m.start()].count("\n") + 1
            warns.append(f"[WARN] L{line_no} {code}: {msg}（「{m.group(0)}」）")

    # 層7: 文体・トーン（writing_tone.md 1-1。アカウント除外あり）
    norm_slash = norm if norm.startswith("/") else "/" + norm
    for code, pat, msg, skip in TONE_WARN_PATTERNS:
        if skip and skip in norm_slash:
            continue
        for m in re.finditer(pat, body):
            line_no = text[:body_start + m.start()].count("\n") + 1
            warns.append(f"[WARN] L{line_no} {code}: {msg}（「{m.group(0)}」）")

    # 層5: 過去記事との言い回し重複（同アカウントの既存記事コーパスと照合）
    corpus_files = load_corpus_files(args.file)
    if not corpus_files:
        infos.append("[INFO] cross-article-dup: 既存記事コーパスが見つからずスキップ（対象アカウントの articles/drafts・published に .md がない）")
    else:
        sh_idx = build_shingle_index(corpus_files)
        seen = set()
        for raw in sentences(strip_for_compare(body)):
            if any(ig in raw for ig in CROSS_DUP_IGNORE):
                continue
            ns = normalize_for_compare(raw)
            if len(ns) < SHINGLE_LEN:
                continue
            for i in range(len(ns) - SHINGLE_LEN + 1):
                src = sh_idx.get(ns[i:i + SHINGLE_LEN])
                if src:
                    key = (raw[:24], src)
                    if key not in seen:
                        seen.add(key)
                        warns.append(f"[WARN] cross-article-dup: 過去記事「{src}」と{SHINGLE_LEN}字以上一致する言い回し（「{raw.strip()[:45]}…」）。表現を作り直す")
                    break

    # 層6: 同一記事内の重複（同じ文・言い直しが2回以上）
    body_sents = [s.strip() for s in sentences(strip_for_compare(body)) if len(normalize_for_compare(s)) >= 12]
    norm_sents = [normalize_for_compare(s) for s in body_sents]
    counts = {}
    for n in norm_sents:
        counts[n] = counts.get(n, 0) + 1
    done = set()
    for orig, n in zip(body_sents, norm_sents):
        if counts[n] >= 2 and n not in done:
            done.add(n)
            warns.append(f"[WARN] intra-dup-exact: 同じ文が記事内で{counts[n]}回（「{orig[:45]}…」）。1回に減らすか言い換える")
    grams = [(char_ngrams(n), body_sents[i]) for i, n in enumerate(norm_sents) if 20 <= len(n) <= 200]
    near_done = set()
    for a in range(len(grams)):
        ga, oa = grams[a]
        if not ga or len(near_done) >= 10:
            continue
        for b in range(a + 1, len(grams)):
            gb, ob = grams[b]
            if not gb or normalize_for_compare(oa) == normalize_for_compare(ob):
                continue
            inter = len(ga & gb)
            if inter and inter / len(ga | gb) >= 0.70:
                pk = tuple(sorted((oa[:24], ob[:24])))
                if pk not in near_done:
                    near_done.add(pk)
                    warns.append(f"[WARN] intra-dup-near: 記事内で同じ内容を言い直している疑い（「{oa[:35]}…」 ≒ 「{ob[:35]}…」）")

    # vivant専用：冒頭注意書きのblockquote化チェック（2026-08-01追加。vivant-article.md「冒頭の注意書き」ルール準拠）
    if "/vivant/" in norm or norm.startswith("vivant/"):
        body_line_no = text[:body_start].count("\n") + 1
        first_line = ""
        for line in body.splitlines():
            if line.strip():
                first_line = line.strip()
                break
            body_line_no += 1
        if not (first_line.startswith(">") and "本記事は" in first_line):
            errors.append(f"[ERROR] L{body_line_no} vivant-intro-quote: 冒頭の注意書きが`>` blockquoteになっていない、または『本記事は』を含まない（vivant-article.md「冒頭の注意書き」ルール）")

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
