#!/usr/bin/env python3
"""
Shira Notes ドラフト検品ツール（qa_draft.py）

過去に実際に発生したミス（メモリ蓄積分）を機械チェックする。
Usage:
  python tools/qa_draft.py draft_musicday.txt          # 1ファイル検品
  python tools/qa_draft.py --all                       # 全draft検品
  python tools/qa_draft.py draft_musicday.txt --fix    # スマートクォートを自動修正してから検品
  python tools/qa_draft.py --all --update-baseline     # 現在のWARNを「既知」として記録（要ユーザー承認）

チェック項目:
  [ERROR] スマートクォート混入（U+201C/U+201D/U+2018/U+2019）→ --fix で自動修正可
  [ERROR] 文字化け（U+FFFD）混入
  [ERROR] WPブロックコメントの開閉不一致（wp:paragraph / wp:html / wp:heading 等）
  [ERROR] ショートコードとテキストの同一<p>混在（[nopc][title]等は独立ブロック必須）
  [ERROR] JSON-LDのパースエラー
  [ERROR] JSON-LDの@id/urlが固定記事URL（NAV_FIXED_URLS）と不一致（スラッグ誤記検知）
  [ERROR] メタディスクリプションとJSON-LD descriptionの不一致
  [ERROR] 本文FAQ（Q/Aカード）とJSON-LD FAQPage.mainEntityの件数・文言不一致
  [ERROR] 楽天もしもAFリンクの属性仕様違反（rel/attributionsrc/referrerpolicy/daily-002/インプレッションピクセル）
  [WARN]  禁止ワード（彩る・飾る・幕を開ける・見せ場・筆頭に・フィナーレを飾る・締めくくる・編集部・集結）
  [WARN]  メタディスクリプション120字超
  [WARN]  <ul style= の使用（WPテーマCSSに上書きされるためdiv推奨）
  [WARN]  wp:imageブロックのalign指定とfigureのclassの不一致（手動修正時のズレ検知）
  [WARN]  ナビブロックにカテゴリURL残存（/category/musictv/ ※JSON-LD内は除外）
  [WARN]  ナビブロックの番組網羅漏れ・自己参照リンク（rewrite_common_rules.md 8章のURL一覧と照合）
  [WARN]  締め文（mokujimae直後）の主観形容詞（感動的・豪華・圧倒的 ※「な」なしの形も検出。
          class="shicho-memo" の視聴メモブロック内は対象外 — rewrite_common_rules.md 10章）
  [WARN]  同一文の記事内3回以上リピート（数字のみ違う文は同一視。表現ローテーション用 — 10章）
  [INFO]  本文中の日付分布（更新漏れ発見用）

WARNベースライン:
  tools/output/qa_baseline.json に「既知WARN」の指紋と件数を記録し、
  それを超えるWARNを【新規】として扱う（リライト完了条件は ERROR 0件 かつ 新規WARN 0件）。
  既知WARNを意図的に受け入れる場合のみ --update-baseline で更新する。

終了コード: ERROR または 新規WARN が1件以上あれば 1、なければ 0
"""

import argparse
import json
import os
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

DRAFT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "drafts"
)

SMART_QUOTES = {
    "“": '"', "”": '"',
    "‘": "'", "’": "'",
}

# 禁止ワード（feedback_shira_rewrite_banned_words 準拠）
BANNED_PATTERNS = [
    (r"幕を開け", "「続く」「登場する」「スタートする」等に言い換え"),
    (r"筆頭に、", "並列で事実を並べる"),
    (r"見せ場", "「集中する」「登場する予定」等の事実記述に"),
    (r"フィナーレを飾", "「ラストに登場します」「最後に登場します」等に（「担います」は使わない）"),
    (r"締めくくり|締めくくる|締めくくります", "「ラストに登場します」等の動作ベースに（「担います」は使わない）"),
    (r"彩り(?:ます)?[、。]|彩る|彩った|彩ります", "「担当する」「出演する」「登場する」等に"),
    (r"を飾る|を飾り(?:ます)?[、。]|を飾った", "「出演する」「初登場する」等に"),
    (r"編集部", "「筆者」「当サイト」に（一人運営のため組織を装わない・2026-07-16追加）"),
    (r"集結", "「出演する」「登場する」「顔ぶれが揃う」等に（2026-07-17追加）"),
]

# 締め文の主観形容詞（rewrite_common_rules.md 準拠・語幹マッチで「な」なしの形も検出）
SUBJECTIVE_ADJ = r"感動的|豪華|圧倒的"

# 既知WARNベースライン（これを超えるWARNは【新規】扱い → 終了コード1）
BASELINE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "output", "qa_baseline.json"
)

WP_BLOCK_TYPES = ["paragraph", "html", "heading", "list", "table", "image", "shortcode"]

NAV_FIXED_URLS = {
    "CDTV": "https://shira-treat.com/cdtv-timetable/",
    "STAR": "https://shira-treat.com/star-timetable/",
    "Mステ": "https://shira-treat.com/music-station-timetable/",
    "FNS歌謡祭": "https://shira-treat.com/fnskayousai-timetable/",
    "THE MUSIC DAY": "https://shira-treat.com/the-musicday-timetable/",
    "音楽の日": "https://shira-treat.com/ongakunohi-timetable/",
    "テレ東音楽祭": "https://shira-treat.com/teretoongakusai-timetable/",
    "うたであえたら": "https://shira-treat.com/utadeaetara-timetable/",
    "レコード大賞": "https://shira-treat.com/record-award-timetable/",
    "紅白歌合戦": "https://shira-treat.com/nhk-kouhaku-timetable/",
    "うたコン": "https://shira-treat.com/utacon-timetable/",
}

# ナビブロックの「自番組」判定用（この番組へのリンクはナビに出てはいけない＝自己参照バグ）
# アーカイブ系は本編と同じ番組として扱う。マッピングのないファイル（新番組・派生記事等）は
# 自己参照チェックをスキップし、欠落チェックのみ行う。
# 注意: アーカイブ記事（cdtv_archive/mste_archive）は本編と別の記事URL（例: cdtv-2026july）を
# 持つため、この「自番組」URLは記事自身の正規URLとイコールではない。JSON-LDの@id/url検証には
# 使わず、CANONICAL_URL_BY_FILENAME（下記）を使うこと。
NAV_SELF_URL_BY_FILENAME = {
    "draft_cdtv.txt": NAV_FIXED_URLS["CDTV"],
    "draft_cdtv_archive.txt": NAV_FIXED_URLS["CDTV"],
    "draft_mste.txt": NAV_FIXED_URLS["Mステ"],
    "draft_mste_archive.txt": NAV_FIXED_URLS["Mステ"],
    "draft_star.txt": NAV_FIXED_URLS["STAR"],
    "draft_fns.txt": NAV_FIXED_URLS["FNS歌謡祭"],
    "draft_musicday.txt": NAV_FIXED_URLS["THE MUSIC DAY"],
    "draft_ongakunohi.txt": NAV_FIXED_URLS["音楽の日"],
    "draft_teretou.txt": NAV_FIXED_URLS["テレ東音楽祭"],
    "draft_utadeaetara.txt": NAV_FIXED_URLS["うたであえたら"],
    "draft_utacon.txt": NAV_FIXED_URLS["うたコン"],
}

# JSON-LDの@id/urlが指すべき、この記事自身の正規URL。
# アーカイブ記事（本編と別URLを持つ）はマッピングを持たせず、チェック対象外とする。
CANONICAL_URL_BY_FILENAME = {
    "draft_cdtv.txt": NAV_FIXED_URLS["CDTV"],
    "draft_mste.txt": NAV_FIXED_URLS["Mステ"],
    "draft_star.txt": NAV_FIXED_URLS["STAR"],
    "draft_fns.txt": NAV_FIXED_URLS["FNS歌謡祭"],
    "draft_musicday.txt": NAV_FIXED_URLS["THE MUSIC DAY"],
    "draft_ongakunohi.txt": NAV_FIXED_URLS["音楽の日"],
    "draft_teretou.txt": NAV_FIXED_URLS["テレ東音楽祭"],
    "draft_utadeaetara.txt": NAV_FIXED_URLS["うたであえたら"],
    "draft_utacon.txt": NAV_FIXED_URLS["うたコン"],
}

# JSON-LDの@id/urlチェックから除外する、記事URLとは別に正当に存在する固定URL
# （著者プロフィールページ等）
JSONLD_URL_EXCLUDE_BASES = {
    "https://shira-treat.com/operator-information",
}

# ナビブロックの開始・終了マーカー（この区間内のhrefだけを対象にする。
# 本文中の文脈リンク（例: 「音楽の日のタイムテーブルはこちら」）を誤検知しないため）
NAV_BLOCK_START_RE = re.compile(r"他の音楽(?:番組|特番)もチェック")
NAV_BLOCK_END_MARKERS = ("出演者の作品を探す", "レコードを探す")


class Report:
    def __init__(self, filename: str):
        self.filename = filename
        self.errors: list[str] = []
        self.warns: list[str] = []
        self.infos: list[str] = []
        self.known_warns: list[str] = []
        self.new_warns: list[str] = []

    def error(self, msg: str):
        self.errors.append(msg)

    def warn(self, msg: str):
        self.warns.append(msg)

    def info(self, msg: str):
        self.infos.append(msg)

    def classify_warns(self, baseline_counts: dict):
        """ベースライン（指紋→件数）と照合し、既知/新規に振り分ける"""
        remaining = dict(baseline_counts)
        self.known_warns = []
        self.new_warns = []
        for w in self.warns:
            fp = warn_fingerprint(w)
            if remaining.get(fp, 0) > 0:
                remaining[fp] -= 1
                self.known_warns.append(w)
            else:
                self.new_warns.append(w)

    def print(self):
        print(f"\n{'='*70}")
        print(f"検品対象: {self.filename}")
        print(f"{'='*70}")
        if not self.errors and not self.warns:
            print("  [OK] ERROR/WARN なし")
        for e in self.errors:
            print(f"  [ERROR] {e}")
        for w in self.new_warns:
            print(f"  [WARN][新規] {w}")
        for w in self.known_warns:
            print(f"  [WARN][既知] {w}")
        if not self.known_warns and not self.new_warns:
            for w in self.warns:
                print(f"  [WARN]  {w}")
        for i in self.infos:
            print(f"  [INFO]  {i}")
        print(
            f"  --- ERROR: {len(self.errors)}件 / "
            f"WARN: {len(self.warns)}件（新規 {len(self.new_warns)}・既知 {len(self.known_warns)}） ---"
        )


def ctx(line: str, maxlen: int = 60) -> str:
    line = line.strip()
    return line[:maxlen] + ("…" if len(line) > maxlen else "")


def warn_fingerprint(msg: str) -> str:
    """WARNメッセージから行番号とコンテキスト部を除いた指紋を作る（行ズレ・前後編集に強い）"""
    fp = re.sub(r"^L\d+:\s*", "", msg)
    fp = fp.split(" → ")[0].strip()
    return fp


def load_baseline() -> dict:
    if os.path.exists(BASELINE_PATH):
        with open(BASELINE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_baseline(baseline: dict):
    os.makedirs(os.path.dirname(BASELINE_PATH), exist_ok=True)
    with open(BASELINE_PATH, "w", encoding="utf-8") as f:
        json.dump(baseline, f, ensure_ascii=False, indent=2)


def strip_jsonld_regions(text: str) -> tuple[str, list[tuple[int, int]]]:
    """JSON-LD scriptブロックの行範囲を返し、除外用に使う"""
    lines = text.split("\n")
    regions = []
    start = None
    for i, line in enumerate(lines):
        if 'application/ld+json' in line:
            start = i
        elif start is not None and "</script>" in line:
            regions.append((start, i))
            start = None
    return text, regions


def in_regions(lineno: int, regions: list[tuple[int, int]]) -> bool:
    return any(s <= lineno <= e for s, e in regions)


# ---------------------------------------------------------------------------
# 各チェック
# ---------------------------------------------------------------------------

def check_smart_quotes(lines: list[str], rep: Report):
    for i, line in enumerate(lines):
        for sq in SMART_QUOTES:
            if sq in line:
                rep.error(f"L{i+1}: スマートクォート U+{ord(sq):04X} 混入 → {ctx(line)}")


def check_mojibake(lines: list[str], rep: Report):
    for i, line in enumerate(lines):
        if "�" in line:
            rep.error(f"L{i+1}: 文字化け(U+FFFD)混入 → {ctx(line)}")


def check_banned_words(lines: list[str], regions, rep: Report):
    for i, line in enumerate(lines):
        if in_regions(i, regions):
            continue
        for pat, alt in BANNED_PATTERNS:
            m = re.search(pat, line)
            if m:
                rep.warn(f"L{i+1}: 禁止ワード「{m.group(0)}」（代替: {alt}） → {ctx(line)}")


def check_wp_blocks(text: str, rep: Report):
    for btype in WP_BLOCK_TYPES:
        opens = len(re.findall(rf"<!--\s*wp:{btype}(?:\s|-->)", text))
        closes = len(re.findall(rf"<!--\s*/wp:{btype}\s*-->", text))
        if opens != closes:
            rep.error(f"WPブロック開閉不一致: wp:{btype} 開始{opens} / 終了{closes}")


def check_shortcode_isolation(lines: list[str], rep: Report):
    """[nopc][xxx][/nopc] を含む<p>に他のテキストが混在していないか"""
    for i, line in enumerate(lines):
        m = re.search(r"<p>(.*?)</p>", line)
        if not m:
            continue
        inner = m.group(1)
        if "[nopc]" in inner:
            stripped = re.sub(r"\[/?nopc\]|\[/?[a-z]+\]", "", inner).strip()
            if stripped:
                rep.error(f"L{i+1}: ショートコードとテキストが同一<p>に混在 → {ctx(line)}")


def check_jsonld(text: str, rep: Report) -> list[str]:
    """JSON-LDをパースし、descriptionのリストを返す"""
    descriptions = []
    for m in re.finditer(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>', text, re.DOTALL
    ):
        raw = m.group(1)
        lineno = text[:m.start()].count("\n") + 1
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            rep.error(f"L{lineno}: JSON-LDパースエラー → {e}")
            continue

        def collect_desc(node):
            if isinstance(node, dict):
                for k, v in node.items():
                    if k == "description" and isinstance(v, str):
                        descriptions.append(v)
                    else:
                        collect_desc(v)
            elif isinstance(node, list):
                for item in node:
                    collect_desc(item)

        collect_desc(data)
    return descriptions


def check_jsonld_canonical_url(text: str, filename: str, rep: Report):
    """JSON-LD内の@id/urlが、この記事の固定URL（CANONICAL_URL_BY_FILENAME）と一致するか確認する
    （記事URLのスラッグ誤記・過去の一時URLの残存を検知。ホームURL・著者プロフィールURL・
    wp-content画像URL・アーカイブ記事（別URL体系のため対象外）は除外する）"""
    self_url = CANONICAL_URL_BY_FILENAME.get(filename)
    if not self_url:
        return  # マッピングのないファイル（アーカイブ記事・新番組・派生記事等）は対象外
    self_base = self_url.rstrip("/")

    for m in re.finditer(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>', text, re.DOTALL
    ):
        lineno = text[:m.start()].count("\n") + 1
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue

        mismatches = set()

        def walk(node):
            if isinstance(node, dict):
                for k, v in node.items():
                    if k in ("@id", "url") and isinstance(v, str):
                        if v.startswith("https://shira-treat.com/") and "/wp-content/" not in v:
                            base = v.split("#")[0].rstrip("/")
                            if (
                                base
                                and base != "https://shira-treat.com"
                                and base != self_base
                                and base not in JSONLD_URL_EXCLUDE_BASES
                            ):
                                mismatches.add(base)
                    else:
                        walk(v)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(data)
        if mismatches:
            rep.error(
                f"L{lineno}: JSON-LDの@id/urlが固定記事URL（{self_base}/）と不一致 → "
                f"{', '.join(sorted(mismatches))}"
            )


def check_meta_description(text: str, descriptions: list[str], rep: Report):
    m = re.search(r"メタディスクリプション（(\d+)字）：\s*\n(.+)", text)
    if not m:
        rep.warn("メタディスクリプション行が見つからない（フォーマット確認）")
        return
    declared_len = int(m.group(1))
    meta = m.group(2).strip()
    actual_len = len(meta)
    if actual_len > 120:
        rep.warn(f"メタディスクリプション {actual_len}字（120字超はGoogleで切れる）")
    if abs(actual_len - declared_len) > 2:
        rep.warn(f"メタの申告字数（{declared_len}字）と実字数（{actual_len}字）が不一致")
    if descriptions and meta not in descriptions:
        # 完全一致するdescriptionが1つもない場合はエラー（一字一句一致ルール）
        rep.error(
            f"メタディスクリプションとJSON-LD descriptionが不一致（一字一句一致ルール）\n"
            f"          メタ: {meta[:70]}…\n"
            f"          JSON-LD先頭: {descriptions[0][:70]}…"
        )


def extract_body_faq(text: str) -> list[tuple[str, str]]:
    """本文のFAQセクション（Q/Aカード）から質問・回答テキストを抽出する"""
    m = re.search(
        r"<h2>よくある質問[^<]*</h2>(.*?)(?:<!--\s*wp:heading\s*-->\s*\n<h2>|\Z)",
        text, re.DOTALL,
    )
    if not m:
        return []
    block = m.group(1)
    matches = re.finditer(r'<span[^>]*>(Q\d+|A)</span>.*?<p[^>]*>(.*?)</p>', block, re.DOTALL)
    pairs: list[tuple[str, str]] = []
    pending_q = None
    for m2 in matches:
        lbl, raw = m2.group(1), m2.group(2)
        txt = re.sub(r"<[^>]+>", "", raw)
        txt = re.sub(r"\s+", " ", txt).strip()
        if lbl.startswith("Q"):
            pending_q = txt
        elif lbl == "A" and pending_q is not None:
            pairs.append((pending_q, txt))
            pending_q = None
    return pairs


def extract_jsonld_faq(text: str) -> list[tuple[str, str]]:
    """JSON-LD FAQPage.mainEntityから質問・回答テキストを抽出する"""
    pairs: list[tuple[str, str]] = []

    def walk(node):
        if isinstance(node, dict):
            if node.get("@type") == "FAQPage":
                for q in node.get("mainEntity", []):
                    name = (q.get("name") or "").strip()
                    ans = ((q.get("acceptedAnswer") or {}).get("text") or "").strip()
                    pairs.append((name, ans))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    for m in re.finditer(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>', text, re.DOTALL
    ):
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        walk(data)
    return pairs


def check_faq_sync(text: str, rep: Report):
    body_faq = extract_body_faq(text)
    jsonld_faq = extract_jsonld_faq(text)
    if not body_faq:
        # 本文側のFAQマークアップがQ1/A形式のspan構造と異なるテンプレート
        # （例: STAR系の <div>Q1｜質問文</div> 形式）は抽出非対応のため判定をスキップする。
        return
    if len(body_faq) != len(jsonld_faq):
        rep.error(
            f"FAQ件数不一致: 本文{len(body_faq)}問 / JSON-LD FAQPage.mainEntity {len(jsonld_faq)}問"
            "（本文Q&AとJSON-LDを一字一句一致させること）"
        )
        return
    for idx, ((bq, ba), (jq, ja)) in enumerate(zip(body_faq, jsonld_faq), start=1):
        if bq != jq:
            rep.error(f"FAQ Q{idx} 質問文が本文とJSON-LDで不一致 → 本文:「{ctx(bq, 40)}」/ JSON-LD:「{ctx(jq, 40)}」")
        if ba != ja:
            rep.error(f"FAQ Q{idx} 回答文が本文とJSON-LDで不一致 → 本文:「{ctx(ba, 40)}」/ JSON-LD:「{ctx(ja, 40)}」")


def check_af_links(lines: list[str], text: str, rep: Report):
    has_moshimo_link = False
    for i, line in enumerate(lines):
        if "af.moshimo.com/af/c/click" not in line:
            continue
        has_moshimo_link = True
        # aタグ全体を近傍から取得（複数行対応のため周辺6行を連結）
        blob = "\n".join(lines[i:min(i+8, len(lines))])
        a_m = re.search(r"<a\s[^>]*af\.moshimo\.com[^>]*>", blob, re.DOTALL)
        tag = a_m.group(0) if a_m else line
        rel_m = re.search(r'rel="([^"]*)"', tag)
        if not rel_m:
            rep.error(f"L{i+1}: AFリンクに rel 属性なし（rel=\"nofollow\" 必須）")
        elif rel_m.group(1).strip() != "nofollow":
            rep.error(f'L{i+1}: AFリンク rel="{rel_m.group(1)}" → "nofollow" のみが正（sponsored/noopener等は付けない）')
        if "referrerpolicy=" not in tag:
            rep.error(f"L{i+1}: AFリンクに referrerpolicy がない（no-referrer-when-downgrade 必須）")
        if not re.search(r"attributionsrc(?!=)", tag):
            rep.error(f"L{i+1}: AFリンクに attributionsrc（値なしboolean属性）がない")
        if "books.rakuten.co.jp" in tag or "books.rakuten" in tag:
            if not re.search(r"daily(%2F|/)002", tag):
                rep.error(f"L{i+1}: 楽天ランキングURLが daily/002 でない（hourly/weeklyはNG）")
    if has_moshimo_link and "i.moshimo.com/af/i/impression" not in text:
        rep.error("AFリンクはあるがインプレッションピクセル（i.moshimo.com/af/i/impression）がない")


def check_ul_style(lines: list[str], rep: Report):
    for i, line in enumerate(lines):
        if re.search(r"<ul\s+style=", line):
            rep.warn(f"L{i+1}: <ul style= はWPテーマCSSに上書きされる → <div>に変換推奨")


def check_image_align(text: str, rep: Report):
    """wp:imageブロックのalign属性とfigureタグのclassが一致しているか確認する"""
    for m in re.finditer(
        r'<!--\s*wp:image\s*(\{.*?\})?\s*-->(.*?)<!--\s*/wp:image\s*-->', text, re.DOTALL
    ):
        attrs_raw = m.group(1) or "{}"
        block_body = m.group(2)
        lineno = text[:m.start()].count("\n") + 1
        align_match = re.search(r'"align"\s*:\s*"(\w+)"', attrs_raw)
        comment_align = align_match.group(1) if align_match else None
        fig_match = re.search(r'<figure[^>]*class="([^"]*)"', block_body)
        fig_classes = fig_match.group(1).split() if fig_match else []
        align_class = next((c for c in fig_classes if c.startswith("align")), None)
        if comment_align and f"align{comment_align}" not in fig_classes:
            rep.warn(
                f"L{lineno}: wp:imageのalign指定（{comment_align}）とfigureのclassが不一致"
                f"（align{comment_align}が付与されていない） → 画像修正後の見落とし注意"
            )
        elif not comment_align and align_class:
            rep.warn(
                f"L{lineno}: figureに{align_class}クラスがあるが、wp:imageブロックコメントにalign指定がない"
            )


def check_nav_completeness(lines: list[str], filename: str, rep: Report):
    """ナビブロック（他の音楽番組もチェック）が全番組を網羅し、自己参照リンクがないか確認する"""
    start = None
    for i, line in enumerate(lines):
        if NAV_BLOCK_START_RE.search(line):
            start = i
            break
    if start is None:
        return  # ナビブロックがないファイル（アーカイブ月次記事の一部等）は対象外

    end = min(start + 80, len(lines))
    for i in range(start + 1, end):
        if any(marker in lines[i] for marker in NAV_BLOCK_END_MARKERS):
            end = i
            break

    block = "\n".join(lines[start:end])
    found_urls = set(re.findall(r'href="(https://shira-treat\.com/[a-z0-9-]+-timetable/)"', block))

    self_url = NAV_SELF_URL_BY_FILENAME.get(filename)
    if self_url and self_url in found_urls:
        name = next(n for n, u in NAV_FIXED_URLS.items() if u == self_url)
        rep.warn(f"L{start+1}: ナビブロックに自番組（{name}）への自己参照リンクが混入 → 他番組のリンクに置き換え")

    expected = set(NAV_FIXED_URLS.values())
    if self_url:
        expected = expected - {self_url}
    missing = expected - found_urls
    if missing:
        missing_names = sorted(n for n, u in NAV_FIXED_URLS.items() if u in missing)
        rep.warn(f"L{start+1}: ナビブロックに未掲載の番組 → {'・'.join(missing_names)}（rewrite_common_rules.md 8章と照合）")


def check_nav_category_urls(lines: list[str], regions, rep: Report):
    for i, line in enumerate(lines):
        if in_regions(i, regions):
            continue  # JSON-LD内（BreadcrumbList）のカテゴリURLは正
        if "/category/musictv/" in line:
            rep.warn(f"L{i+1}: ナビ/本文にカテゴリURL残存 → 固定URL（例: /cdtv-timetable/）に更新 → {ctx(line)}")


def shicho_memo_line_indices(lines: list[str]) -> set:
    """class="shicho-memo"（視聴メモブロック）内の行番号集合。
    視聴メモは主観表現OKのため締め文チェックから除外する（rewrite_common_rules.md 10章）。
    仕様上ブロック内に子divは置かないため、最初の </div> でブロック終了とみなす。"""
    idx = set()
    inside = False
    for i, line in enumerate(lines):
        if "shicho-memo" in line:
            inside = True
        if inside:
            idx.add(i)
            if "</div>" in line:
                inside = False
    return idx


def check_closing_adjectives(lines: list[str], rep: Report):
    """mokujimae直後の締め文パラグラフに主観形容詞がないか（視聴メモブロック内は対象外）"""
    memo_idx = shicho_memo_line_indices(lines)
    for i, line in enumerate(lines):
        if "[mokujimae]" not in line:
            continue
        window = lines[i+1:min(i+12, len(lines))]
        for j, wline in enumerate(window):
            if (i + 1 + j) in memo_idx:
                continue
            m = re.search(SUBJECTIVE_ADJ, wline)
            if m and "<p>" in wline:
                rep.warn(f"L{i+2+j}: 締め文に主観形容詞「{m.group(0)}」→ 企画名の列挙のみでよい → {ctx(wline)}")


def check_repeated_sentences(text: str, rep: Report):
    """同一文の記事内3回以上リピートを検知（量産型シグナル対策・2026-07-16追加）。
    <p>本文のみ対象。数字・空白だけ違う文は同一とみなす。ナビ/AFリンク行は除外。"""
    body = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.S)
    counts = Counter()
    samples = {}
    for p in re.findall(r"<p[^>]*>(.*?)</p>", body, re.S):
        txt = re.sub(r"<[^>]+>", "", p)
        txt = re.sub(r"&[a-z]+;", " ", txt)
        txt = re.sub(r"\s+", " ", txt).strip()
        if "›" in txt or "Amazon" in txt or "楽天" in txt:
            continue
        for s in txt.split("。"):
            s = s.strip()
            if len(s) < 20:
                continue
            if s.startswith("[") or "[nopc]" in s:  # ショートコードは意図的な繰り返し
                continue
            key = re.sub(r"[0-9０-９\s]", "", s)
            counts[key] += 1
            samples.setdefault(key, s)
    for key, c in counts.items():
        if c >= 3:
            rep.warn(
                f"同一文が記事内に{c}回リピート"
                f" → 2箇所目以降は言い換えるか「前述のとおり」で参照（10章）"
                f" → {samples[key][:60]}…"
            )


def report_dates(lines: list[str], regions, rep: Report):
    """本文中の日付（M月D日）の分布を出す。少数派の日付は更新漏れの可能性"""
    date_hits: dict[str, list[int]] = {}
    for i, line in enumerate(lines):
        if in_regions(i, regions):
            continue
        for m in re.finditer(r"\d{1,2}月\d{1,2}日", line):
            date_hits.setdefault(m.group(0), []).append(i + 1)
    if not date_hits:
        return
    counts = Counter({d: len(v) for d, v in date_hits.items()})
    dominant, dom_n = counts.most_common(1)[0]
    summary = " / ".join(f"{d}×{n}" for d, n in counts.most_common())
    rep.info(f"日付分布: {summary}（過去一覧/アーカイブの日付は正常。最新回セクションに古い日付が残っていないかだけ確認）")
    # 「から放送」を含むリードパラグラフに支配的でない日付 → 更新漏れの典型パターン
    for i, line in enumerate(lines):
        if in_regions(i, regions) or "から放送" not in line:
            continue
        for m in re.finditer(r"\d{1,2}月\d{1,2}日", line):
            if m.group(0) != dominant and dom_n >= 3:
                rep.warn(f"L{i+1}: リード文の日付「{m.group(0)}」が最頻日付「{dominant}」と不一致 → 更新漏れの可能性 → {ctx(line)}")


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

def fix_smart_quotes(path: str) -> int:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    fixed = content
    n = 0
    for sq, rep_ch in SMART_QUOTES.items():
        n += fixed.count(sq)
        fixed = fixed.replace(sq, rep_ch)
    if n:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(fixed)
    return n


def run_qa(path: str) -> Report:
    rep = Report(os.path.basename(path))
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    lines = text.split("\n")
    _, regions = strip_jsonld_regions(text)

    check_smart_quotes(lines, rep)
    check_mojibake(lines, rep)
    check_wp_blocks(text, rep)
    check_shortcode_isolation(lines, rep)
    descriptions = check_jsonld(text, rep)
    check_jsonld_canonical_url(text, os.path.basename(path), rep)
    check_meta_description(text, descriptions, rep)
    check_faq_sync(text, rep)
    check_af_links(lines, text, rep)
    check_ul_style(lines, rep)
    check_image_align(text, rep)
    check_nav_category_urls(lines, regions, rep)
    check_nav_completeness(lines, os.path.basename(path), rep)
    check_closing_adjectives(lines, rep)
    check_repeated_sentences(text, rep)
    check_banned_words(lines, regions, rep)
    report_dates(lines, regions, rep)
    return rep


def main():
    parser = argparse.ArgumentParser(description="Shira Notes ドラフト検品")
    parser.add_argument("file", nargs="?", help="検品対象（例: draft_musicday.txt）")
    parser.add_argument("--all", action="store_true", help="全draftを検品")
    parser.add_argument("--fix", action="store_true", help="スマートクォートを自動修正してから検品")
    parser.add_argument(
        "--update-baseline", action="store_true",
        help="現在のWARNを既知としてqa_baseline.jsonに記録（意図的な受け入れ時のみ使用）"
    )
    args = parser.parse_args()

    if args.all:
        targets = sorted(
            os.path.join(DRAFT_DIR, f)
            for f in os.listdir(DRAFT_DIR)
            if f.startswith("draft_") and f.endswith(".txt")
        )
    elif args.file:
        p = args.file if os.path.isabs(args.file) else os.path.join(DRAFT_DIR, args.file)
        if not os.path.exists(p):
            print(f"[ERROR] ファイルが見つかりません: {p}")
            sys.exit(2)
        targets = [p]
    else:
        parser.print_help()
        sys.exit(2)

    baseline = load_baseline()
    total_errors = 0
    total_new_warns = 0
    for path in targets:
        if args.fix:
            n = fix_smart_quotes(path)
            if n:
                print(f"[FIX] {os.path.basename(path)}: スマートクォート {n}箇所を自動修正")
        rep = run_qa(path)
        key = os.path.basename(path)
        if args.update_baseline:
            counts = Counter(warn_fingerprint(w) for w in rep.warns)
            baseline[key] = dict(counts)
            rep.classify_warns(baseline.get(key, {}))
        else:
            rep.classify_warns(baseline.get(key, {}))
        rep.print()
        total_errors += len(rep.errors)
        total_new_warns += len(rep.new_warns)

    if args.update_baseline:
        save_baseline(baseline)
        print(f"\n[BASELINE] {len(targets)}ファイルの既知WARNを更新: {BASELINE_PATH}")

    print(f"\n{'#'*70}")
    print(f"# 検品完了: {len(targets)}ファイル / ERROR合計 {total_errors}件 / 新規WARN合計 {total_new_warns}件")
    print(f"{'#'*70}")
    sys.exit(1 if (total_errors or total_new_warns) else 0)


if __name__ == "__main__":
    main()
