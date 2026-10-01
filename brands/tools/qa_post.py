#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""qa_post.py — SNS投稿ドラフト機械検品ツール（brands共通）

完了条件: ERROR 0件（終了コード0）。WARNは参考情報（人間が判断する）。

使い方:
  python brands/tools/qa_post.py brands/mbticode/posts/posts_x.txt
  python brands/tools/qa_post.py <file> [--account mbticode|s4lv] [--platform x|threads]

アカウント・プラットフォームはファイルパスから自動判定する（--指定で上書き可）。
対応ファイル形式: 【ヘッダー】行 + `----`区切りの本文ブロック（posts_x.txt / posts_threads.txt 形式）。

ルールの出典（唯一の正。変更時は出典ファイルを先に更新し本スクリプトを追従させる）:
  - brands/mbticode/sns_post_cheatsheet.md          … 文体・記号・字数・型ルール
  - .claude/commands/quality-guardrail.md           … AIっぽさ禁止表現
  - brands/mbticode/rules/feedback_mbticode_reply_style.md … リプライ・引用RT文体
  - brands/s4lv/rules/feedback_s4lv_x_writing_style.md     … s4lv X投稿文体
  - brands/s4lv/rules/feedback_s4lv_threads_writing_style.md … s4lv Threads投稿文体（AI感禁止リスト・読点2つまで・締めの型の出典）
    （2026-09-07追加：sns-ai-reviewerで3巡かかった機械的指摘を先取り検知する
     kutouten-3 / closing-binary-q / closing-q-tail-repeat / opener-watashiwa を実装。
     すべてWARN・実ファイル40ブロックで現行文体への誤検知0を確認済み）
    （2026-09-07追加②：Threads運用プレイブック採用に伴い th-url（Threads本文・自己リプの
     外部URL＝フォロワー100まで誘導全廃・ERROR）と th-shitenai-opener /
     th-shitenai-opener-multi（1行目の「〜してないですか？」型指摘フック＝週1本まで・WARN）を実装。
     出典：feedback_s4lv_threads_writing_style.md「誘導リンクの扱い」「フック（1行目）」。
     旧・誘導リンク付き投稿済みブロックでth-urlが出るため新バッチ検品は --since を付ける）
    （2026-09-10追加：s4lv開示ワード（番組表・タイムテーブル・出演順・放送日・
     「毎年おなじ時期」「数字や日付の差し替え」等）の disclosure-tell を実装。
     Threadsバッチで審査2巡の原因になった開示漏れを生成時点で検知。WARN・高確度語のみ）
  - brands/CLAUDE.md 絶対遵守ルール3           … 断定的統計・性的描写・特定個人を傷つける表現の禁止
    （2026-07-26notekaigi Phase1で追加。正規表現の一次防御であり漏れは残る前提。
    完全な意味判定はPhase2のLLM二次判定で補う）
"""
import argparse
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HEADER_RE = re.compile(r"^【(.+?)】(.*)$")
SEP_RE = re.compile(r"^-{10,}\s*$")
DATE_RE = re.compile(r"(\d{1,2}/\d{1,2})")
MBTI_RE = re.compile(r"(?<![A-Za-z])([IE][NS][TF][JP])(?![A-Za-z])")
URL_RE = re.compile(r"https?://")
# 本文の閉じ`----`の後・次の見出しの前に置かれる「自己リプライ（〜）：」注記行の接頭辞。
# 投稿本体には含めない（実際にThreadsへ投稿するのはこの接頭辞を除いた本文のみ）。
REPLY_LABEL_RE = re.compile(r"^自己リプライ[^：]*：\s*")
# リスト型・続き型など、1本目の自己リプライ（列C＝続きの本文等）が既に使われている投稿向けの
# 2本目の自己リプライ（URL誘導専用・2026-09-29追加）。「自己リプライ2（〜）：」で始まる行から
# 次の見出しまでを reply2 として別途拾う（parse_posts参照）。
REPLY2_LABEL_RE = re.compile(r"^自己リプライ2[^：]*：\s*")
REPLY2_MARKER_RE = re.compile(r"^自己リプライ2[^：]*：")
# Threads API実測の投稿本文上限（超過分は投稿時に必ずエラーになる。目安200〜350字とは別軸のハード制約）。
THREADS_API_LIMIT = 500

# 1行目の恋愛文脈ワード（チェックリスト「1行目に恋愛文脈ワード」の近似判定・WARN専用）
LOVE_LEXICON = re.compile(
    r"好き|恋|付き合|彼氏|彼女|連絡|既読|別れ|尽く|甘え|冷め|重い|未練|デート"
    r"|LINE|返信|距離|片思い|相手|束縛|合わせ|素の自分|寂し|優しさ"
)

# brands/CLAUDE.md 絶対遵守ルール3（断定的統計・性的描写）の一次防御。
# 正規表現なので漏れは残る前提（2026-07-26notekaigi Phase1・LLM二次判定はPhase2で別途追加）。
CONTENT_POLICY_ERRORS = [
    ("teitei-toukei", r"\d+(\.\d+)?[割%％].{0,10}(見える|わかる|分かる|決まる|バレる)",
     "断定的統計の疑い（数字＋割合＋断定語尾・brands/CLAUDE.md絶対遵守ルール3）"),
    ("sexual-desc", r"セックス|性行為|エッチな|射精|オーガズム",
     "性的描写の疑い（brands/CLAUDE.md絶対遵守ルール3）"),
]
INDIVIDUAL_MENTION_RE = re.compile(r"@[A-Za-z0-9_]+")

# MBTICODEの文体系ERROR（記号・語尾・言い回し・回数制限）。2026-09-29、文体ルールを作り直すまでの間、
# 文体検品を止めるためERRORをWARNへ下げる（オーナー決定）。検知ロジック自体は残す
# （文体の再構築後にこの集合を空にすれば元のERRORに戻る）。
# ここに含めないERRORは維持する：字数・URL・ハッシュタグ・Threads/APIの上限・自己リプライ2の構造
# ・content-policy（断定的統計・性的描写。brands/CLAUDE.md絶対遵守ルール3）。
MBTICODE_STYLE_DOWNGRADE_CODES = {
    "symbol-quote", "symbol-dash", "dewa-nai", "sekkei-ng", "ai-desune", "ai-omoimasu",
    "ai-deshou", "ai-kanji", "ai-taisetsu", "ai-matome", "ai-yobousen", "ai-mashou",
    "demo-conj", "tsuzuki-meta", "ndesu-count", "kairo-count", "tech-words",
    "dayona", "mi-oboe", "sekkei-reply", "te-owari",
}


class Finding:
    def __init__(self, severity, label, code, message):
        self.severity = severity  # "ERROR" / "WARN"
        self.label = label        # 投稿の識別（ヘッダー冒頭）
        self.code = code
        self.message = message

    def line(self):
        return f"[{self.severity}] ({self.label}) {self.code}: {self.message}"


def parse_posts(text):
    """【ヘッダー】＋ ---- 区切りブロックを投稿リストに分解する。

    本文の閉じ`----`の後・次の見出しの前に「自己リプライ（〜）：」形式の行がある場合
    （posts_threads.txt の実ファイル形式）、その行を post["reply"] として別途保持する。
    """
    posts = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = HEADER_RE.match(lines[i])
        if m and "URL候補" not in m.group(1):
            header = m.group(1) + m.group(2)
            # 次の ---- から次の ---- までを本文とする
            j = i + 1
            while j < len(lines) and not SEP_RE.match(lines[j]):
                # 次のヘッダーが来たら本文なしとして打ち切り
                if HEADER_RE.match(lines[j]):
                    break
                j += 1
            if j < len(lines) and SEP_RE.match(lines[j]):
                k = j + 1
                body_lines = []
                while k < len(lines) and not SEP_RE.match(lines[k]):
                    body_lines.append(lines[k])
                    k += 1
                body = "\n".join(body_lines).strip()
                # 閉じ`----`が見つかった場合のみ、その後〜次の見出し直前までを自己リプライ候補として拾う
                reply = ""
                reply2 = ""
                end = k
                if k < len(lines) and SEP_RE.match(lines[k]):
                    m2 = k + 1
                    reply_lines = []
                    while m2 < len(lines) and not HEADER_RE.match(lines[m2]):
                        reply_lines.append(lines[m2])
                        m2 += 1
                    # 「自己リプライ2（〜）：」行があれば、そこでreply/reply2に分割する
                    # （URL誘導専用の2本目の自己リプライ・2026-09-29追加）
                    split_idx = next((idx for idx, ln in enumerate(reply_lines)
                                       if REPLY2_MARKER_RE.match(ln.strip())), None)
                    if split_idx is not None:
                        reply = "\n".join(reply_lines[:split_idx]).strip()
                        reply2 = "\n".join(reply_lines[split_idx:]).strip()
                    else:
                        reply = "\n".join(reply_lines).strip()
                    end = m2
                date_m = DATE_RE.search(header)
                posts.append({
                    "header": header,
                    "label": header[:26],
                    "date": date_m.group(1) if date_m else "",
                    "body": body,
                    "reply": reply,
                    "reply2": reply2,
                    # 「リプライ狙い」（s4lv Threadsの"締めで返信を誘う通常投稿"のラベル）や
                    # 「自己リプライ」は他者への返信/引用ポストではないので is_reply から除外する
                    # （2026-09-07：ヘッダー語の衝突で通常投稿が誤ってreply扱いされバッチ検査から
                    #  漏れる不具合を修正）。
                    # 2026-10-02：見出しの反響ラベル「会話・引用型」の「引用」で他者への返信と誤判定され、
                    # バッチ検査から外れていた不具合を修正（ラベル部分を除いて判定する）。
                    "is_reply": (("引用" in header.replace("会話・引用型", "")) or ("リプライ" in header))
                                and ("リプライ狙い" not in header)
                                and ("自己リプライ" not in header),
                })
                i = end
                continue
        i += 1
    return posts


def sentences(text):
    return [s for s in re.split(r"[。？！?!\n]+", text) if s.strip()]


def nonempty_lines(text):
    return [l for l in text.splitlines() if l.strip()]


def check_regex(findings, post, severity, code, pattern, message):
    if re.search(pattern, post["body"]):
        findings.append(Finding(severity, post["label"], code, message))


# 型D（DSKB）の締め定型（cheatsheet「4種の型」参照）はキャラクターの決め台詞として
# 意図的に採用された固定フレーズで、AIっぽい説教口調のヘッジとは別物のため
# ai-mashou（quality-guardrail「〜しましょう」禁止）の対象から個別に除外する
# （2026-07-26発見・矛盾を解消。cheatsheet側は変更しない）。
DSKB_CLOSING_PHRASE = "どれかひとつでも当てはまる人は、設計の話をしましょう。"


def check_ai_mashou(findings, post):
    body = post["body"].replace(DSKB_CLOSING_PHRASE, "")
    if re.search(r"しましょう|していきましょう", body):
        findings.append(Finding("ERROR", post["label"], "ai-mashou", "セミナー講師口調禁止（quality-guardrail）"))


# ---------------------------------------------------------------- mbticode

MBTICODE_MAIN_ERRORS = [
    ("symbol-quote", r"[\"“”]", "ダブルクォート禁止（cheatsheet禁止記号）"),
    ("symbol-dash", r"──|——", "ダッシュ記号禁止（cheatsheet禁止記号）"),
    ("dewa-nai", r"ではない|ではなく", "「ではない/ではなく」→「じゃない/じゃなくて」を使う"),
    ("sekkei-ng", r"設計があります|設計になってい|の話です。|設計が狂って",
     "「〜設計があります/〜になっている/〜の話です。」型は禁止（設計ワードルール・予告終止廃止）"),
    ("ai-desune", r"(?<!ん)ですね", "「〜ですね」相槌禁止（quality-guardrail）"),
    ("ai-omoimasu", r"と思います|と感じます", "「と思います/と感じます」禁止・観察として言い切る（quality-guardrail）"),
    ("ai-deshou", r"ではないでしょうか|でしょう。", "「でしょう」系の遠回し禁止（quality-guardrail）"),
    ("ai-kanji", r"という感じ", "「という感じ」の抽象化逃げ禁止（quality-guardrail）"),
    ("ai-taisetsu", r"ことが大切|が重要です|お勧めします|おすすめします",
     "「大切です/重要です/お勧め」禁止（quality-guardrail）"),
    ("ai-matome", r"以上のように|このように、|まとめると", "要約フレーズ禁止（quality-guardrail）"),
    ("ai-yobousen", r"個人差があります|一概には言えません", "責任回避の予防線禁止（quality-guardrail）"),
    ("demo-conj", r"(^|。)\s*でも[、ね]", "接続詞「でも」禁止→「けど」を使う（cheatsheet文体）"),
    ("tsuzuki-meta", r"続きに置いた|続きはリプ欄で|つづきます|自己リプライに続けます",
     "続き型の予告メタ発言禁止（2026-08-16notekaigi・本文は読点で文法的に途切れさせ、リプライが直接完成させる）"),
]

REPLY_ERRORS = [
    ("symbol-quote", r"[\"“”]", "ダブルクォート禁止"),
    ("symbol-dash", r"──|——", "ダッシュ記号禁止"),
    ("dewa-nai", r"ではない|ではなく", "「ではない/ではなく」→「じゃない/じゃなくて」"),
    ("dayona", r"だよな", "「〜だよな」禁止→「んですよね。」（reply_style）"),
    ("mi-oboe", r"身に覚えがあ", "「これ、身に覚えが〜」導入は禁止・本題から始める（reply_style）"),
    ("sekkei-reply", r"設計", "リプライ・引用では「設計」を使わない（reply_style）"),
]


# --- MBTICODE 文体・現実性の新検品（2026-09-30・オーナー指摘。すべてWARN。文体の再構築が固まったらERRORへ上げるか決める） ---
# 読点：1文に2つ以上でWARN／投稿全体で1文あたり0.5超でWARN（続き型の切れ目の末尾「、」は数えない）
# 現実性：実在しない・アプリで違う機能の描写（LINEに「入力中」表示はない等）
# 問いの置き場所：最後の文を問いで終えない（question-tail）。オーナーの手直し例（10/1 16:00）では、問いを独立した段落に置いても、直後に文が続けばOKだった
# 問い：「あなたは〜ですか？」「どっちですか？」のアンケート調は不自然（同意を求める「〜ませんか？」「〜ですよね？」型を使う）
UNREAL_FEATURE_RE = re.compile(r"入力中|オンライン(中|表示|状態)|最終ログイン|ログイン時間|既読(時間|の時刻|になった時刻)")
OPENING_BANNED_RE = re.compile(r"(人|ひと|方)(が|も|は)?(いる|います)|(こと|ときが|日が)(が|も)?ある|人を見かける|見かける|(い|あり|し|なり|感じ|ませ)ませんか|ないですか|ありませんか")
SURVEY_QUESTION_RE = re.compile(r"(あなた(は|が|の)|どっち|どちら|いくつ|何個|どれくらい).{0,30}(ですか|でしたか|ますか|ましたか)？|(どっち|どちら)(ですか|でしたか)？")


def check_mbticode_style_new(label, text, where="", opening=True):
    f = []
    suffix = f"（{where}）" if where else ""
    body = text.strip()
    sents = [x for x in re.split(r"[。？！?!\n]+", body) if x.strip()]
    if sents:
        counts = []
        for x in sents:
            x = x.strip()
            if x.endswith("、"):
                x = x[:-1]
            counts.append(x.count("、"))
        multi = [x for x, c in zip(sents, counts) if c >= 2]
        for x in multi[:3]:
            f.append(Finding("WARN", label, "comma-multi",
                             f"1文に読点2つ以上：「{x.strip()[:30]}…」→ 1文1つまで（消しても自然に読めるなら消す）{suffix}"))
        if len(multi) > 3:
            f.append(Finding("WARN", label, "comma-multi", f"ほかに読点2つ以上の文が{len(multi) - 3}文{suffix}"))
        density = sum(counts) / len(counts)
        if density > 0.5 and len(sents) >= 3:
            f.append(Finding("WARN", label, "comma-density",
                             f"読点が多い：1文あたり{density:.2f}個（目標0.5以下）{suffix}"))
    for m in UNREAL_FEATURE_RE.finditer(body):
        f.append(Finding("WARN", label, "reality-feature",
                         f"「{m.group(0)}」：LINEなどに存在しない・アプリで違う表示の疑い。確かでなければ書かず自分の動作で書く{suffix}"))
    # 問いの置き場所（2026-09-30 オーナー指示）：本文の最後を問いで終えない／問いだけの短い行を独立させない
    # （付け足しの問いは不自然。問いは前の文と同じ段落に埋め込み、直後に文が続く形にする）
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    if lines and lines[-1].endswith(("？", "?")) and not lines[-1].startswith(("・", "→")):
        f.append(Finding("WARN", label, "question-tail",
                         f"本文が問いで終わっている：「{lines[-1][-24:]}」→ 問いは途中に埋め込み、直後に文を続ける{suffix}"))
    # 冒頭の禁止形（2026-09-30 オーナー決定）：1行目を「〜な人がいる／〜ことがある／〜ありませんか」で書かない。
    # 自分の過去172本で、この形の1行目は上位20%に入る割合が13%（それ以外27%）だった。
    # 場面（〜のとき）＋何が分かるか、を1行目に置く。
    if opening and lines and OPENING_BANNED_RE.search(lines[0]):
        f.append(Finding("ERROR", label, "opening-observer",
                         f"1行目が禁止形（〜人がいる／〜ことがある／〜ありませんか 等）：「{lines[0][:30]}」"
                         f"→ 場面（〜のとき）＋何の話かが一目で分かる1行目に（style_0930.md 2.5）{suffix}"))
    for m in SURVEY_QUESTION_RE.finditer(body):
        f.append(Finding("WARN", label, "question-survey",
                         f"アンケート調の問い「{m.group(0)[:30]}」→ 流れの中の同意を求める形（〜ませんか？／〜ですよね？）へ{suffix}"))
    return f


def check_mbticode_post(post, platform):
    f = []
    body = post["body"]
    if post["is_reply"]:
        for code, pat, msg in REPLY_ERRORS:
            check_regex(f, post, "ERROR", code, pat, msg)
        for code, pat, msg in CONTENT_POLICY_ERRORS:
            check_regex(f, post, "ERROR", code, pat, msg)
        f.extend(check_mbticode_style_new(post["label"], body, "リプライ", opening=False))  # 2026-09-30：読点・問いのルールをリプライにも適用
        if INDIVIDUAL_MENTION_RE.search(body):
            f.append(Finding("WARN", post["label"], "individual-mention",
                             "@メンションあり・特定個人を傷つける表現になっていないか要確認（brands/CLAUDE.md絶対遵守ルール3）"))
        for line in nonempty_lines(body):
            if re.search(r"て。$", line.strip()):
                f.append(Finding("ERROR", post["label"], "te-owari",
                                 f"て形の文末禁止（「{line.strip()[-8:]}」）→「んですよね。」等で代替（reply_style）"))
        check_regex(f, post, "WARN", "boutou-hitei", r"はわかるんですけど|は正しいですが",
                    "冒頭の軟らかい否定の疑い（reply_style）")
        check_regex(f, post, "WARN", "omoimasu-reply", r"と思います",
                    "「と思います」は過去振り返り文脈（〜だったなと思います）のみ可（reply_style）")
        return f

    # 本文投稿
    for code, pat, msg in MBTICODE_MAIN_ERRORS:
        check_regex(f, post, "ERROR", code, pat, msg)
    check_ai_mashou(f, post)
    for code, pat, msg in CONTENT_POLICY_ERRORS:
        check_regex(f, post, "ERROR", code, pat, msg)
    if INDIVIDUAL_MENTION_RE.search(body):
        f.append(Finding("WARN", post["label"], "individual-mention",
                         "@メンションあり・特定個人を傷つける表現になっていないか要確認（brands/CLAUDE.md絶対遵守ルール3）"))

    f.extend(check_mbticode_style_new(post["label"], body))
    n_ndesu = len(re.findall(r"んです", body))
    if n_ndesu >= 2:
        f.append(Finding("ERROR", post["label"], "ndesu-count",
                         f"「〜んです/なんです」が{n_ndesu}回（1投稿1回まで・cheatsheet）"))
    if len(re.findall(r"回路", body)) >= 2:
        f.append(Finding("ERROR", post["label"], "kairo-count", "「回路」は1投稿1回まで（cheatsheet）"))
    for s in sentences(body):
        hits = sum(1 for w in ("処理", "コスト", "組み込まれ", "機能していない") if w in s)
        if hits >= 2:
            f.append(Finding("ERROR", post["label"], "tech-words",
                             f"技術語の連続（1文に2語以上）: 「{s[:24]}…」（cheatsheet差し替え辞書参照）"))
    if len(re.findall(r"だ。", body)) >= 3:
        f.append(Finding("WARN", post["label"], "da-tayou", "「〜だ。」多用の疑い（3回以上）"))
    if len(re.findall(r"かもしれません", body)) >= 2:
        f.append(Finding("WARN", post["label"], "kamo-tayou", "「かもしれません」多用（予防線・guardrail）"))
    # 抽象名詞「〜性」の連発（guardrail Step1）。「相性」はアカウントの中核語のため除外
    n_sei = len(re.findall(r"[一-龥]性", body)) - len(re.findall(r"相性", body))
    if n_sei >= 3:
        f.append(Finding("WARN", post["label"], "sei-renpatsu",
                         f"抽象名詞「〜性」が{n_sei}回（連発は内容が薄く見える・guardrail）"))

    lines = nonempty_lines(body)
    if lines and not LOVE_LEXICON.search(lines[0]):
        f.append(Finding("WARN", post["label"], "love-hook",
                         "1行目に恋愛文脈ワードが見つからない（辞書による近似判定・人間確認）"))

    if platform == "x":
        length = len(body.replace("\n", ""))
        if length > 140:
            f.append(Finding("ERROR", post["label"], "x-length", f"X本文{length}字（140字以内）"))
        if URL_RE.search(body):
            f.append(Finding("ERROR", post["label"], "x-url", "X本文にURL禁止（自己リプライに回す）"))
        if "#" in body:
            f.append(Finding("ERROR", post["label"], "x-hashtag", "ハッシュタグ禁止（cheatsheet基本設定）"))
        head2 = "".join(lines[:2])
        if MBTI_RE.search(head2):
            f.append(Finding("WARN", post["label"], "x-type-head",
                             "冒頭2行にMBTIタイプ名（タイプ名は核心フレーズの後に置く・X書き出しルール）"))
    elif platform == "threads":
        length = len(body.replace("\n", ""))
        if length > THREADS_API_LIMIT:
            f.append(Finding("ERROR", post["label"], "th-length-api-limit",
                             f"Threads本文{length}字（API上限{THREADS_API_LIMIT}字を超過・投稿時に必ず失敗する。"
                             f"型が原因で収まらない場合は圧縮せず続き型として自己リプライへ分割する）"))
        elif not (200 <= length <= 350):
            f.append(Finding("WARN", post["label"], "th-length",
                             f"Threads本文{length}字（目安200〜350字）"))
        reply = post.get("reply", "")
        if reply:
            reply_body = REPLY_LABEL_RE.sub("", reply, count=1).strip()
            for code, pat, msg in MBTICODE_MAIN_ERRORS:
                if re.search(pat, reply_body):
                    f.append(Finding("ERROR", post["label"], code, f"{msg}（自己リプライ）"))
            for code, pat, msg in CONTENT_POLICY_ERRORS:
                if re.search(pat, reply_body):
                    f.append(Finding("ERROR", post["label"], code, f"{msg}（自己リプライ）"))
            if not URL_RE.search(reply_body):
                f.extend(check_mbticode_style_new(post["label"], reply_body, "自己リプライ"))
            rlen = len(reply_body.replace("\n", ""))
            if rlen > THREADS_API_LIMIT:
                f.append(Finding("ERROR", post["label"], "th-reply-length-api-limit",
                                 f"自己リプライ{rlen}字（API上限{THREADS_API_LIMIT}字を超過・投稿時に必ず失敗する）"))
            elif not URL_RE.search(reply_body):
                # URL誘導リプライは1〜2行＋URLで完結（字数チェック対象外）
                if not (80 <= rlen <= 150):
                    f.append(Finding("WARN", post["label"], "th-reply-length",
                                     f"自己リプライ{rlen}字（コンテンツ系は80〜150字）"))
        # th-type-head（書き出しにタイプ名でWARN）は2026-09-30に廃止：1行目は「場面＋何が分かるか」を優先し、
        # タイプ名が1行目に入ってよい（オーナー承認。本文にタイプ名がある投稿は届きやすい傾向〈patterns.md J〉）
        # 続き型は本文の最後を読点で文法的に未完のまま終える（2026-08-16notekaigi）
        if "続き型" in post.get("header", "") and reply:
            tail_lines = nonempty_lines(body)
            if tail_lines and not tail_lines[-1].strip().endswith("、"):
                f.append(Finding("WARN", post["label"], "tsuzuki-not-fragment",
                                 "続き型は本文の最後を読点（、）で文法的に途切れさせ、"
                                 "自己リプライがそのまま完成させる形にする（2026-08-16notekaigi・続き型の本文の切り方）"))

        # 2本目の自己リプライ（URL誘導専用・2026-09-29追加）。1本目が既に本文の続き等で
        # 使われているリスト型・続き型向け。URL事後型の1本目リプライと同じ扱い
        # （字数は目安対象外・content-policy/禁止表現/API上限のみ機械チェック）。
        reply2 = post.get("reply2", "")
        if reply2:
            reply2_body = REPLY2_LABEL_RE.sub("", reply2, count=1).strip()
            for code, pat, msg in MBTICODE_MAIN_ERRORS:
                if re.search(pat, reply2_body):
                    f.append(Finding("ERROR", post["label"], code, f"{msg}（自己リプライ2・URL誘導）"))
            for code, pat, msg in CONTENT_POLICY_ERRORS:
                if re.search(pat, reply2_body):
                    f.append(Finding("ERROR", post["label"], code, f"{msg}（自己リプライ2・URL誘導）"))
            r2len = len(reply2_body.replace("\n", ""))
            if r2len > THREADS_API_LIMIT:
                f.append(Finding("ERROR", post["label"], "th-reply2-length-api-limit",
                                 f"自己リプライ2（URL誘導）{r2len}字（API上限{THREADS_API_LIMIT}字を超過・"
                                 f"投稿時に必ず失敗する）"))
            if not URL_RE.search(reply2_body):
                f.append(Finding("ERROR", post["label"], "th-reply2-no-url",
                                 "自己リプライ2はURL誘導専用のはずだがURLが見つからない（誤用の疑い）"))
    return f


def load_cta_templates():
    """cta_templates.md内の```で囲まれたCTA承認済み文言を全て抽出する（2026-08-16notekaigi追加）。"""
    path = Path(__file__).resolve().parent.parent / "mbticode" / "posts" / "cta_templates.md"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    return [t.strip() for t in re.findall(r"```\n(.+?)\n```", text, flags=re.S)]


def check_mbticode_file(posts, findings):
    """ファイル（バッチ）単位のチェック。"""
    all_body = "\n".join(p["body"] for p in posts)
    n = len(re.findall(r"心当たりある人の顔が浮かびませんか", all_body))
    if n >= 2:
        findings.append(Finding("WARN", "バッチ全体", "shime-tayou",
                                f"「心当たりある人の顔が〜」が{n}回（1バッチ1本まで）"))
    # 同日・同タイプ重複（quality-guardrail Step 2.5）
    seen = {}
    for p in posts:
        if p["is_reply"] or not p["date"]:
            continue
        for code in MBTI_RE.findall(p["header"]):
            key = (p["date"], code)
            seen.setdefault(key, 0)
            seen[key] += 1
    for (date, code), cnt in seen.items():
        if cnt >= 2:
            findings.append(Finding("WARN", "バッチ全体", "same-day-type",
                                    f"{date} に {code} が{cnt}本（同日同タイプ重複・guardrail Step2.5）"))
    # FW比率の集計（参考情報）
    fw = {"MBTI": 0, "ラブタイプ": 0, "DSKB": 0, "タイプなし": 0}
    for p in posts:
        if p["is_reply"]:
            continue
        h = p["header"]
        if "DSKB" in h:
            fw["DSKB"] += 1
        elif "ラブタイプ" in h:
            fw["ラブタイプ"] += 1
        elif "MBTI" in h:
            fw["MBTI"] += 1
        elif "なし" in h:
            fw["タイプなし"] += 1
    print("[INFO] FW内訳（本文投稿のみ・唯一の正はcheatsheet基本設定）: "
          + " / ".join(f"{k} {v}本" for k, v in fw.items()))

    # 書き出し恋愛文脈ワードの偏り検知（2026-07-29追加・「好きな人」固定化の再発防止）
    opener_words = {}
    for p in posts:
        if p["is_reply"] or not p["date"]:
            continue
        lines = nonempty_lines(p["body"])
        if not lines:
            continue
        m = LOVE_LEXICON.search(lines[0])
        if m:
            opener_words[m.group(0)] = opener_words.get(m.group(0), 0) + 1
    if opener_words:
        total = sum(opener_words.values())
        top_word, top_cnt = max(opener_words.items(), key=lambda kv: kv[1])
        if total >= 5 and top_cnt / total >= 0.5:
            findings.append(Finding("WARN", "バッチ全体", "opener-tayou",
                                    f"書き出し恋愛文脈ワード「{top_word}」が{top_cnt}/{total}本に偏り"
                                    "（50%以上・書き出し多様化ルール）"))

    # 書き出しフレーズの完全一致検知（2026-08-14追加）。
    # opener-tayouは単語単位・ファイル全体比率のみを見るため、7日保持分の古い投稿で薄まると
    # 新規バッチ内だけで「恋愛で、」等が集中していても閾値未満になり見逃す（実例：新規14本中10本が
    # 同一フレーズで開始、比率チェックでは無検知だった）。単語の一致有無に関わらず、1行目冒頭の
    # 同一フレーズ（読点まで、なければ先頭8文字）が絶対数で繰り返されていれば比率に関係なくWARNする。
    opener_phrases = {}
    for p in posts:
        if p["is_reply"] or not p["date"]:
            continue
        lines = nonempty_lines(p["body"])
        if not lines:
            continue
        first = lines[0].strip()
        m = re.match(r"^(.+?[、。])", first)
        phrase = m.group(1) if m else first[:8]
        if len(phrase) >= 3:
            opener_phrases.setdefault(phrase, []).append(p["label"])
    for phrase, labels in opener_phrases.items():
        if len(labels) >= 3:
            findings.append(Finding("WARN", "バッチ全体", "opener-phrase-repeat",
                                    f"書き出しフレーズ「{phrase}」が{len(labels)}本で完全一致"
                                    f"（ファイル全体比率とは無関係に絶対数3本以上で検知）: "
                                    + " / ".join(labels)))

    # タイプ名の締め方バリエーション偏り検知（2026-07-29追加）
    closing_pattern = re.compile(r"に近いタイプに出やすい(パターン|動き方)")
    type_posts = [p for p in posts if not p["is_reply"] and re.search(r"MBTI|ラブタイプ|DSKB", p["header"])]
    if len(type_posts) >= 5:
        hits = sum(1 for p in type_posts if closing_pattern.search(p["body"]))
        if hits / len(type_posts) >= 0.5:
            findings.append(Finding("WARN", "バッチ全体", "type-closing-tayou",
                                    f"タイプ名締め「〜に近いタイプに出やすい[パターン/動き方]」が"
                                    f"{hits}/{len(type_posts)}本に偏り（50%以上・締め方バリエーション表参照）"))

    # 結び文の文末パターン偏り検知（2026-07-30追加・「ことがある/だった/じゃなかった」量産の再発防止）
    CLOSING_SUFFIX_PATTERNS = [
        # 2026-09-21: 「こともある。」（「が」ではなく「も」）が同じ意味・同じ距離感の語尾なのに
        # 「ことが」限定の正規表現をすり抜けていた実例（未投稿キュー162行目）を受けて「こと(が|も)ある」に拡張。
        ("ことがある型", re.compile(r"こと(が|も)(あ|あっ)る[。！]?$")),
        ("だった/じゃなかった型", re.compile(r"(だった|じゃなかった)[。！]?$")),
        # 2026-08-16notekaigi追加：締め文の「〜だ。」は言い切り感が強く機械的に見えるとユーザー指摘。
        # 「んだ。」（んですよね系の柔らかい語尾に連なる契機・許容）は対象外にする。
        ("だ言い切り型", re.compile(r"(?<!ん)だ[。！]?$")),
        # 2026-08-16notekaigi追加（同日）：「だ。」と同じく「〜がある。/〜にある。」も言い切り感が
        # 強く機械的に見えるとユーザー指摘。「ことがある型」は既に別枠で判定済みのためそちらを優先。
        ("がある/にある型", re.compile(r"(が|に)ある[。！]?$")),
        ("気がする型", re.compile(r"気がする[。！]?$")),
        ("かもしれない型", re.compile(r"かもしれない[。！]?$")),
        ("らしい型", re.compile(r"らしい[。！]?$")),
        # 2026-08-14追加：「AなのかBなのか／〜のか、まだ答えが出ていない・整理できていない・
        # わからないままでいる」という自問未解決型の締め。ユーザー指摘で新規14本中4本の重複が発覚。
        ("まだ〜ない型", re.compile(r"まだ.{0,12}(ない|できていない)[。！]?$")),
        # 2026-09-21追加：「見えてくる。」「出てこなくなる。」等の「てくる」系語尾。ユーザー指摘で
        # 冒頭フック文にこの語尾が使われているのが判明し、追加登録した（下記opener-suffix-*参照）。
        ("てくる型", re.compile(r"(てくる|てこなくなる)[。！]?$")),
    ]
    closing_suffixes = {}
    closing_labels = {}
    for p in posts:
        if p["is_reply"] or not p["date"]:
            continue
        lines = nonempty_lines(p["body"])
        if not lines:
            continue
        last = lines[-1].strip()
        for label, pat in CLOSING_SUFFIX_PATTERNS:
            if pat.search(last):
                closing_suffixes[label] = closing_suffixes.get(label, 0) + 1
                closing_labels.setdefault(label, []).append(p["label"])
                break
    if closing_suffixes:
        total = sum(closing_suffixes.values())
        top_label, top_cnt = max(closing_suffixes.items(), key=lambda kv: kv[1])
        if total >= 5 and top_cnt / total >= 0.4:
            findings.append(Finding("WARN", "バッチ全体", "closing-suffix-tayou",
                                    f"結び文の文末「{top_label}」が{top_cnt}/{total}本に偏り"
                                    "（40%以上・結び文多様化ルール。2026-07-30notekaigi参照）"))
        # ファイル全体比率だと7日保持分の古い投稿で薄まり、新規バッチ内だけの偏りを見逃すため
        # （opener-phrase-repeatと同じ理由）、比率に関係なく絶対数3本以上でも別途WARNする。
        for label, cnt in closing_suffixes.items():
            if cnt >= 3:
                findings.append(Finding("WARN", "バッチ全体", "closing-suffix-repeat",
                                        f"結び文の文末「{label}」が絶対数{cnt}本で重複: "
                                        + " / ".join(closing_labels[label])))

    # 冒頭文の文末パターン偏り検知（2026-09-21追加）：上のCLOSING_SUFFIX_PATTERNSは元々
    # 締めの文（最終行）だけを見ており、同じ語尾を1行目（フック文）で使う抜け道が
    # 機械チェックの対象外だった（ユーザー指摘・実例：9/19-9/20投稿10本中5本が該当）。
    # 締めと同じ禁止語尾リストを1行目にもそのまま適用する。
    opener_suffixes = {}
    opener_suffix_labels = {}
    for p in posts:
        if p["is_reply"] or not p["date"]:
            continue
        lines = nonempty_lines(p["body"])
        if not lines:
            continue
        first = lines[0].strip()
        for label, pat in CLOSING_SUFFIX_PATTERNS:
            if pat.search(first):
                opener_suffixes[label] = opener_suffixes.get(label, 0) + 1
                opener_suffix_labels.setdefault(label, []).append(p["label"])
                break
    if opener_suffixes:
        total = sum(opener_suffixes.values())
        top_label, top_cnt = max(opener_suffixes.items(), key=lambda kv: kv[1])
        if total >= 5 and top_cnt / total >= 0.4:
            findings.append(Finding("WARN", "バッチ全体", "opener-suffix-tayou",
                                    f"冒頭文の文末「{top_label}」が{top_cnt}/{total}本に偏り"
                                    "（40%以上・結び文と同じ禁止語尾リストを1行目にも適用。2026-09-21追加）"))
        for label, cnt in opener_suffixes.items():
            if cnt >= 3:
                findings.append(Finding("WARN", "バッチ全体", "opener-suffix-repeat",
                                        f"冒頭文の文末「{label}」が絶対数{cnt}本で重複: "
                                        + " / ".join(opener_suffix_labels[label])))

    # 続き型の接続表現（読点直前フレーズ）の重複検知（2026-08-16notekaigi追加）
    CONNECTOR_TAIL_RE = re.compile(
        r"(としたら|てみたら|であって|があって|ていて|というと|けれど|けど|のに|ながら|ようで)、$"
    )
    connector_seen = {}
    connector_labels = {}
    for p in posts:
        if p["is_reply"] or not p["date"] or not p.get("reply"):
            continue
        if "続き型" not in p["header"]:
            continue
        lines = nonempty_lines(p["body"])
        if not lines:
            continue
        m = CONNECTOR_TAIL_RE.search(lines[-1].strip())
        if not m:
            continue
        word = m.group(1)
        connector_seen[word] = connector_seen.get(word, 0) + 1
        connector_labels.setdefault(word, []).append(p["label"])
    for word, cnt in connector_seen.items():
        if cnt >= 2:
            findings.append(Finding("WARN", "バッチ全体", "tsuzuki-connector-repeat",
                                    f"続き型の接続表現「〜{word}、」が{cnt}本で重複: "
                                    + " / ".join(connector_labels[word])))

    # URL事後型リプライがcta_templates.mdの承認済みパターンと一致しているか確認（2026-08-16notekaigi追加）
    cta_texts = load_cta_templates()
    if cta_texts:
        for p in posts:
            if p["is_reply"] or not p.get("reply"):
                continue
            if "URL事後型" not in p["header"]:
                continue
            # reply2がある投稿は、1本目（p["reply"]）がURL誘導ではなく続き型の本文等
            # （2026-09-29追加のリスト型向け2本目リプライ構成）なので、この突合対象から外す。
            # CTA突合はreply2側の専用ブロック（下）で行う。
            if p.get("reply2"):
                continue
            reply_body = REPLY_LABEL_RE.sub("", p["reply"], count=1).strip()
            reply_lines = [ln for ln in reply_body.split("\n") if not ln.strip().startswith("→")]
            reply_text = "\n".join(reply_lines).strip()
            if not any(reply_text in t or t in reply_text for t in cta_texts):
                findings.append(Finding("WARN", p["label"], "cta-template-mismatch",
                                        "自己リプライがcta_templates.mdの承認済みパターンと一致しない"
                                        "（新規パターンならテンプレート集へ正式追加したか確認）"))
        # 2本目の自己リプライ（URL誘導専用・2026-09-29追加）も同様にcta_templates.md突合する。
        # こちらは header の型ラベルに依存しない（reply2の存在自体がURL誘導の意図を示すため）。
        for p in posts:
            if p["is_reply"] or not p.get("reply2"):
                continue
            reply2_body = REPLY2_LABEL_RE.sub("", p["reply2"], count=1).strip()
            reply2_lines = [ln for ln in reply2_body.split("\n") if not ln.strip().startswith("→")]
            reply2_text = "\n".join(reply2_lines).strip()
            if not any(reply2_text in t or t in reply2_text for t in cta_texts):
                findings.append(Finding("WARN", p["label"], "cta-template-mismatch",
                                        "自己リプライ2（URL誘導）がcta_templates.mdの承認済みパターンと一致しない"
                                        "（新規パターンならテンプレート集へ正式追加したか確認）"))


# ---------------------------------------------------------------- s4lv

# AI感の禁止リスト（quality-guardrail.md表を移植・2026-08-23 s4lv Threads文体改訂で採用）
# 出典：brands/s4lv/rules/feedback_s4lv_threads_writing_style.md「AI感の禁止リスト」
S4LV_AI_TELL_ERRORS = [
    ("ai-desune", r"(?<!ん)ですね", "「〜ですね」相槌禁止（AI感・s4lv）"),
    ("ai-omoimasu", r"と思います|と感じます", "「と思います/と感じます」禁止・観察として言い切る（AI感・s4lv）"),
    ("ai-deshou", r"ではないでしょうか|でしょう。", "「でしょう」系の遠回し禁止（AI感・s4lv）"),
    ("ai-kanji", r"という感じ", "「という感じ」の抽象化逃げ禁止（AI感・s4lv）"),
    ("ai-taisetsu", r"ことが大切|が重要です|お勧めします|おすすめします",
     "「大切です/重要です/お勧め」禁止（AI感・s4lv）"),
    ("ai-matome", r"以上のように|このように、|まとめると", "要約フレーズ禁止（AI感・s4lv）"),
    ("ai-yobousen", r"個人差があります|一概には言えません", "責任回避の予防線禁止（AI感・s4lv）"),
]

# X専用のAI感禁止パターン（2026-09-06ユーザー指摘・具体例から追加）
# 出典：brands/s4lv/rules/feedback_s4lv_x_writing_style.md「絶対禁止事項」
S4LV_X_AI_TELL_ERRORS = [
    ("x-nda-ending", r"んだ。", "「〜んだ。」語尾禁止（AI感・s4lv X・2026-09-06ユーザー指摘）"),
]
# 「正直」自体は禁止語ではないが、「正直、〜ます/です。」の告白風ヘッジ構文はAI感が強いとの
# ユーザー指摘（2026-09-06）。誤検知の余地があるためERRORではなくWARN扱い。
S4LV_X_AI_TELL_WARNS = [
    ("x-shojiki-opener", r"正直[、,]?\s*(まだ)?.{0,15}(ます|です)。",
     "「正直、〜ます/です。」型の告白風ヘッジ構文（正直という語自体の禁止ではない・s4lv X・2026-09-06ユーザー指摘）"),
]

# 2026-10-02：問いの許可形（s4lv_voice.md「問いかけ」）。brands/s4lv/tools/recent_forms.py の QUESTION_FORMS と同じ分類
S4LV_Q_OK_RE = re.compile(r"(ってことありません|ありませんか|ませんか|じゃないですか|いませんか|ない|どうします)[？?]$")
S4LV_Q_FORMS = [
    ("ってことありません？", r"ってことありません？"),
    ("ありませんか？", r"ありませんか？"),
    ("ませんか？", r"ませんか？"),
    ("じゃないですか？", r"じゃないですか？"),
    ("〜ない？", r"ない？"),
    ("の人、いませんか？", r"いませんか？"),
]
# 締めの語尾の分類（recent_forms.py の ENDING_KINDS と同じ）
S4LV_ENDING_KINDS = [
    ("〜ました。", r"ました。$"), ("〜してます。", r"てます。$"), ("〜してる。", r"てる。$"),
    ("〜んですよ。", r"んですよ。$"), ("〜んだよね。", r"んだよね。$"), ("〜よね。", r"よね。$"),
    ("〜かな。", r"かな。$"), ("〜ます。", r"ます。$"), ("〜です。", r"です。$"),
    ("〜た。", r"た。$"), ("〜る。", r"る。$"), ("〜い。", r"い。$"),
]

# 1行目に説明なしで置くと読者を選別してしまう符丁（2026-09-04追加・WARN専用・広めの初期辞書）
# 出典：feedback_s4lv_threads_writing_style.md「専門用語・符丁の扱い」。誤検知が多ければ辞書を削る
S4LV_HOOK_JARGON = [
    "allintitle", "参入判定", "撤退判定", "共起語", "ファーストビュー", "一次情報",
    "ドメインパワー", "ドメイン評価", "被リンク", "インデックス", "クローズド案件",
    "サチコ", "サーチコンソール", "Search Console", "SERP", "カニバリ",
    "E-E-A-T", "YMYL", "サジェスト", "ロングテール", "ずらし",
]
# 死にやすい書き出し（2026-09-04追加・WARN専用・1行目のみ判定）
S4LV_DEAD_OPENERS = [
    "方法をまとめました", "まとめてみました", "学びをシェア", "知らないと損",
    "保存推奨", "拡散希望", "皆さんこんにちは", "みなさんこんにちは",
]


def check_s4lv_post(post, platform):
    f = []
    body = post["body"]
    if platform != "threads":
        # 2026-08-23: Threadsは文体改訂でこの禁止を機械チェック対象から外した
        # （feedback_s4lv_threads_writing_style.md参照）。Xは従来通り絶対禁止。
        check_regex(f, post, "ERROR", "meirei", r"しろ。|すべき",
                    "命令口調禁止（〜しろ/〜すべき・s4lv絶対禁止事項）")
    check_regex(f, post, "ERROR", "kougo-toi", r"と思う？",
                "問いかけの口語体禁止→「と思いますか？」（s4lv）")
    if platform == "x" and URL_RE.search(body):
        f.append(Finding("ERROR", post["label"], "x-url", "本文にURL禁止（URLはリプライ欄・s4lv）"))
    # Threads：フォロワー100までの期間は本文・自己リプライとも誘導リンク全廃（noteはプロフィール欄のみ）。
    # 出典：brands/s4lv/rules/feedback_s4lv_threads_writing_style.md「誘導リンクの扱い」／
    # sns_post_cheatsheet.md「ハード運用値」（2026-09-07 Threads運用プレイブックで決定）。
    if platform == "threads":
        _url_reply_raw = post.get("reply", "")
        _url_reply_body = REPLY_LABEL_RE.sub("", _url_reply_raw, count=1) if _url_reply_raw else ""
        if URL_RE.search(body) or URL_RE.search(_url_reply_body):
            f.append(Finding("ERROR", post["label"], "th-url",
                             "Threads本文・自己リプライにURL禁止（フォロワー100までは誘導リンク全廃・"
                             "noteはプロフィール欄のみ・2026-09-07プレイブック）"))
    # Threads 1行目の「〜してないですか？」型の指摘フック（週1本まで・連続禁止）。
    # 出典：feedback_s4lv_threads_writing_style.md「フック（1行目）」。1行目は指摘でなく
    # 自分の現場か具体事実で開く（2026-09-07プレイブック）。誤検知の余地があるためWARN。
    if platform == "threads" and not post["is_reply"]:
        _first = (nonempty_lines(body) or [""])[0].strip()
        if re.search(r"(てない|ていない|じゃない|ないん?)ですか[？?]$", _first):
            f.append(Finding("WARN", post["label"], "th-shitenai-opener",
                             "1行目が「〜してないですか？」型の指摘フック（週1本まで・連続禁止・"
                             "指摘でなく自分の現場か具体事実で開く・2026-09-07プレイブック）"))
    for code, pattern, message in S4LV_AI_TELL_ERRORS:
        check_regex(f, post, "ERROR", code, pattern, message)
    # X専用AI感チェック（2026-09-06追加）
    if platform == "x":
        for code, pattern, message in S4LV_X_AI_TELL_ERRORS:
            check_regex(f, post, "ERROR", code, pattern, message)
        for code, pattern, message in S4LV_X_AI_TELL_WARNS:
            check_regex(f, post, "WARN", code, pattern, message)
        last = (nonempty_lines(body) or [""])[-1].strip()
        # 2026-10-02：問いで終えてもよい（s4lv_voice.md「問いかけ」の形）。広い意見募集型だけWARN
        if (last.endswith("？") or last.endswith("?")) and not S4LV_Q_OK_RE.search(last):
            f.append(Finding("WARN", post["label"], "x-question-closing",
                             "文末が疑問符で、問いの形が引き出しにない（「どう思いますか？」のような広い意見募集型はAI的と指摘あり・"
                             "「〜ってことありません？」「〜ありませんか？」等の形にするか断言・観察で締める・2026-10-02改訂）"))
    # 1行目のフックチェック（2026-09-04追加・Threadsのみ・WARN）
    if platform == "threads" and not post["is_reply"]:
        first = (nonempty_lines(body) or [""])[0]
        hit = next((t for t in S4LV_HOOK_JARGON if t in first), None)
        if hit:
            f.append(Finding("WARN", post["label"], "hook-jargon",
                             f"1行目に符丁「{hit}」（説明なしで置かない・2行目以降で平易な言い換え＋実例に）"))
        dead = next((t for t in S4LV_DEAD_OPENERS if t in first), None)
        if dead:
            f.append(Finding("WARN", post["label"], "dead-opener",
                             f"1行目が死にやすい書き出し「{dead}」（予告・あいさつ・煽り定型）"))
    # 短文羅列のAI感（ヒューリスティック）
    run = 0
    for s in sentences(body):
        if len(s.strip()) <= 10:
            run += 1
            if run >= 4:
                f.append(Finding("WARN", post["label"], "tanbun-raretsu",
                                 "短文羅列の疑い（10字以下の文が4連続・s4lv禁止「〜があった。〜なかった。やめた。」型）"))
                break
        else:
            run = 0

    # 読点過多（1文に「、」3個以上）＝冗長・AI感（feedback_s4lv_threads_writing_style「句読点・記号」／
    # memory feedback_kutouten_kihon_rule_0903「読点は目安2つまで」）。2026-09-07追加。
    # 実測：現行文体(9/4以降)の全バッチで誤検知0。旧8/23バッチの冗長文のみ検出。本文＋自己リプライ両方。
    kt_texts = [("本文", body)]
    _reply_raw = post.get("reply", "")
    if _reply_raw:
        kt_texts.append(("自己リプライ", REPLY_LABEL_RE.sub("", _reply_raw, count=1)))
    for _tlabel, _ttext in kt_texts:
        for s in sentences(_ttext):
            # 2026-10-02：読点は1文に1つまで（s4lv_voice.md）。旧：3個以上でWARN（コード名 kutouten-3）
            if s.count("、") >= 2:
                f.append(Finding("WARN", post["label"], "kutouten-2",
                                 f"1文に読点2個以上（{_tlabel}・1文に1つまで・s4lv_voice.md）: 「{s.strip()[:40]}…」"))

    # 開示ワード（ブログ種別＝テレビ・エンタメ系の定期更新記事が特定される語）が本文・
    # 自己リプライに出ていないか（2026-09-10追加・WARN）。出典：sns_post_cheatsheet.md
    # 開示ルール／x_neta_daicho.md A1・A3「開示注意」。2026-09-10のThreadsバッチで
    # sns-ai-reviewer審査が2巡した原因（「数字や日付の差し替え」「番組表」）を生成時点で
    # 潰すのが目的。誤検知を避けるため高確度の語句・文脈つきパターンのみ。
    DISCLOSURE_TELLS = [
        "番組表", "タイムテーブル", "セットリスト", "セトリ", "出演順", "出演者順",
        "放送日", "放送予定", "毎年おなじ時期", "毎年同じ時期", "毎年書き直",
        "去年書いた記事", "去年の記事",
    ]
    # 「数字や日付を差し替え／更新」＝定期更新の表形式記事の示唆。単に「数字を1つ入れる」
    # 「日付は本文の1か所に」等の一般的な言及は拾わない。
    DISCLOSURE_RE = re.compile(r"数字[や、と]日付[をのは]?.{0,10}(差し替え|差替|置き換え|更新|直す|新しく)")
    _disc_texts = [("本文", body)]
    _disc_reply = post.get("reply", "")
    if _disc_reply:
        _disc_texts.append(("自己リプライ", REPLY_LABEL_RE.sub("", _disc_reply, count=1)))
    for _tlabel, _ttext in _disc_texts:
        hit = next((t for t in DISCLOSURE_TELLS if t in _ttext), None)
        if hit:
            f.append(Finding("WARN", post["label"], "disclosure-tell",
                             f"開示ワード「{hit}」（{_tlabel}・ブログ種別が特定される・一般語へ言い換え）"))
        if DISCLOSURE_RE.search(_ttext):
            f.append(Finding("WARN", post["label"], "disclosure-tell",
                             f"開示ワード「数字や日付＋差し替え/更新」（{_tlabel}・定期更新記事の示唆・"
                             "「古くなった記述を新しい情報に」等へ一般化）"))
    return f


def check_s4lv_file(posts, findings, platform=None):
    all_body = "\n".join(p["body"] for p in posts)
    if all_body.count("170万") >= 2:
        findings.append(Finding("WARN", "バッチ全体", "pv-nikai",
                                "「170万PV」言及が2回以上（1日の投稿群で1回まで・s4lv）"))
    if all_body.count("また別の機会") >= 2:
        findings.append(Finding("WARN", "バッチ全体", "jikai-yudo",
                                "次回誘導フレーズが2回以上（1日1回まで・s4lv）"))
    # 書き出しフレーズの反復検知（2026-09-04追加・mbticodeのopener-phrase-repeatと同型）
    # 1行目冒頭の同一フレーズ（読点/句点/？まで、なければ先頭8文字）が絶対数3本以上でWARN。
    opener_phrases = {}
    for p in posts:
        if p["is_reply"] or not p["date"]:
            continue
        lines = nonempty_lines(p["body"])
        if not lines:
            continue
        first = lines[0].strip()
        m = re.match(r"^(.+?[、。？?])", first)
        phrase = m.group(1) if m else first[:8]
        if len(phrase) >= 3:
            opener_phrases.setdefault(phrase, []).append(p["label"])
    for phrase, labels in opener_phrases.items():
        if len(labels) >= 3:
            findings.append(Finding("WARN", "バッチ全体", "s4lv-opener-repeat",
                                    f"書き出し「{phrase}」が{len(labels)}本で一致"
                                    "（テンプレ構文は同一バッチ2本まで）: " + " / ".join(labels)))

    # --- 2026-09-07追加：sns-ai-reviewerで3巡かかった「型の重複」指摘を機械化（Threadsバッチのみ）。
    # 実測（posts_threads.txt 40ブロック）で現行文体への誤検知が出ない閾値に調整済み。
    if platform == "threads":
        body_posts = [p for p in posts if not p["is_reply"] and p["date"]]

        # (a) 締めの二択問い「〜か、（…）〜か？」がバッチ内2本以上（別型にローテすべき）
        binary_q = re.compile(r"か、.{0,25}か[？?]\s*$")
        bq = [p["label"] for p in body_posts
              if (nonempty_lines(p["body"]) and binary_q.search(nonempty_lines(p["body"])[-1].strip()))]
        if len(bq) >= 2:
            findings.append(Finding("WARN", "バッチ全体", "closing-binary-q",
                                    f"締めの二択問い「〜か、〜か？」が{len(bq)}本（問いの型を散らす・"
                                    "件数/習慣yes-no等へローテ）: " + " / ".join(bq)))

        # (b) 問い締めの語尾（？直前5字）がバッチ内3本以上で一致
        qtails = {}
        for p in body_posts:
            lines = nonempty_lines(p["body"])
            if not lines:
                continue
            last = lines[-1].strip()
            if last.endswith("？") or last.endswith("?"):
                qtails.setdefault(last[:-1][-5:], []).append(p["label"])
        for tail, labels in qtails.items():
            if len(labels) >= 3:
                findings.append(Finding("WARN", "バッチ全体", "closing-q-tail-repeat",
                                        f"締めの問いの語尾「…{tail}？」が{len(labels)}本で一致"
                                        "（問いの型を散らす）: " + " / ".join(labels)))

        # (c) 本文の入り（1〜2文目）が「私は(いま)〜」宣言でバッチの4割以上かつ4本以上
        #     ＝「現象→私の対処→箇条書き」の同型構成の兆候
        wa = []
        for p in body_posts:
            ss = sentences(p["body"])[:2]
            if any(re.match(r"^(私|自分)は(いま)?", s.strip()) for s in ss):  # 2026-10-02：「自分は」も数える
                wa.append(p["label"])
        if len(wa) >= 4 and len(wa) / max(len(body_posts), 1) >= 0.4:
            findings.append(Finding("WARN", "バッチ全体", "opener-watashiwa",
                                    f"本文の入りが「私は〜している」型が{len(wa)}/{len(body_posts)}本"
                                    "（構成テンプレの固定化・型を2〜3種に散らす）: " + " / ".join(wa)))

        # (d) 「〜してないですか？」型の指摘フックがバッチ内2本以上（週1本まで・連続禁止）
        #     2026-09-07 Threads運用プレイブック。1行目は指摘でなく現場/具体事実で開く。
        _shitenai = re.compile(r"(てない|ていない|じゃない|ないん?)ですか[？?]$")
        st = [p["label"] for p in body_posts
              if nonempty_lines(p["body"]) and _shitenai.search(nonempty_lines(p["body"])[0].strip())]
        if len(st) >= 2:
            findings.append(Finding("WARN", "バッチ全体", "th-shitenai-opener-multi",
                                    f"「〜してないですか？」型フックが{len(st)}本（週1本まで・連続禁止・"
                                    "指摘でなく現場/具体事実で開く）: " + " / ".join(st)))

    # --- 2026-10-02：ばらつきの決まり（s4lv_voice.md）の機械化（X・Threads共通・WARN）。
    # 日付なし（テスト中）の投稿も対象にする。直近10本との比較は brands/s4lv/tools/recent_forms.py。
    vp = [p for p in posts if not p["is_reply"] and nonempty_lines(p["body"])]

    def _last_line(p):
        return nonempty_lines(p["body"])[-1].strip()

    def _end_kind(p):
        last = _last_line(p)
        return next((n for n, pat in S4LV_ENDING_KINDS if re.search(pat, last)), "")

    def _q_form(p):
        for ln in nonempty_lines(p["body"]):
            plain = re.sub(r"「[^」]*」", "", ln).strip()
            if plain.endswith("？") or plain.endswith("?"):
                return next((n for n, pat in S4LV_Q_FORMS if re.search(pat, ln)), "その他の問い")
        return ""

    kinds = [_end_kind(p) for p in vp]
    for i in range(len(vp) - 2):
        if kinds[i] and kinds[i] == kinds[i + 1] == kinds[i + 2]:
            findings.append(Finding("WARN", "バッチ全体", "ending-repeat",
                                    f"締めの語尾「{kinds[i]}」が3本続いている（語尾の引き出しを順番に使う・s4lv_voice.md）: "
                                    + " / ".join(p["label"] for p in vp[i:i + 3])))
            break
    qforms = [_q_form(p) for p in vp]
    if len(vp) >= 4 and sum(1 for q in qforms if q) / len(vp) > 0.5:
        findings.append(Finding("WARN", "バッチ全体", "question-ratio",
                                f"問いのある投稿が{sum(1 for q in qforms if q)}/{len(vp)}本（半分以下にする・s4lv_voice.md）"))
    tail5 = qforms[-5:]
    for q in set(q for q in tail5 if q):
        if tail5.count(q) >= 2:
            findings.append(Finding("WARN", "バッチ全体", "question-form-repeat",
                                    f"問いの形「{q}」が直近5本で{tail5.count(q)}回（同じ形は2回使わない・s4lv_voice.md）"))


# ---------------------------------------------------------------- main

def detect(path):
    p = path.replace("\\", "/").lower()
    account = "mbticode" if "mbticode" in p else ("s4lv" if "s4lv" in p else None)
    platform = "threads" if "threads" in p else ("x" if re.search(r"posts_x|_x\.", p) else None)
    return account, platform


def _month_day(s):
    """'M/D' or 'YYYY-MM-DD' -> (month, day)."""
    s = s.strip()
    parts = s.split("-") if "-" in s else s.split("/")
    return (int(parts[-2]), int(parts[-1]))


def filter_since(posts, since):
    """Keep only post blocks whose header date is on/after `since`.

    Post headers carry no year (just 'M/D'); the file never spans more than a few
    months, so a >6-month gap between the post month and the --since month is read
    as a year boundary. Lets `qa_post.py posts_threads.txt --since 2026-08-29`
    check just the new batch instead of drowning in WARNs from pre-rule old posts.
    """
    sm, sd = _month_day(since)
    out = []
    for p in posts:
        if not p["date"]:
            continue
        pm, pd = _month_day(p["date"])
        if sm - pm > 6:
            keep = True          # post is early next year
        elif pm - sm > 6:
            keep = False         # post is late previous year
        else:
            keep = (pm, pd) >= (sm, sd)
        if keep:
            out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--account", choices=["mbticode", "s4lv"])
    ap.add_argument("--platform", choices=["x", "threads"])
    ap.add_argument("--since", metavar="M/D|YYYY-MM-DD",
                    help="このヘッダー日付以降の投稿ブロックだけを検品する（旧投稿のWARN混入を避ける）")
    args = ap.parse_args()

    auto_acc, auto_pf = detect(args.file)
    account = args.account or auto_acc
    platform = args.platform or auto_pf
    if not account or not platform:
        print("[ERROR] account/platform をパスから判定できません。--account と --platform を指定してください。")
        sys.exit(2)

    with open(args.file, encoding="utf-8") as fh:
        text = fh.read()
    posts = parse_posts(text)
    if not posts:
        print("[ERROR] 投稿ブロック（【ヘッダー】＋----区切り）が見つかりません。")
        sys.exit(2)

    since_note = ""
    if args.since:
        posts = filter_since(posts, args.since)
        since_note = f" / since={args.since}"
        if not posts:
            print(f"[INFO] --since {args.since} 以降の投稿ブロックがありません。")
            sys.exit(0)

    print(f"=== qa_post: {args.file} / account={account} / platform={platform}{since_note} / {len(posts)}ブロック ===")
    findings = []
    for p in posts:
        if account == "mbticode":
            findings.extend(check_mbticode_post(p, platform))
        else:
            findings.extend(check_s4lv_post(p, platform))
    if account == "mbticode":
        check_mbticode_file(posts, findings)
    else:
        check_s4lv_file(posts, findings, platform)

    if account == "mbticode":
        downgraded = 0
        for x in findings:
            if x.severity == "ERROR" and x.code in MBTICODE_STYLE_DOWNGRADE_CODES:
                x.severity = "WARN"
                x.message += "（文体検品は保留中のためWARN扱い）"
                downgraded += 1
        if downgraded:
            print(f"[INFO] MBTICODE文体系ERROR {downgraded}件をWARNへ下げました（文体ルール再構築までの暫定運用）")

    errors = [x for x in findings if x.severity == "ERROR"]
    warns = [x for x in findings if x.severity == "WARN"]
    for x in errors + warns:
        print(x.line())
    print(f"=== 結果: ERROR {len(errors)}件 / WARN {len(warns)}件 ===")
    if errors:
        print("完了条件を満たしていません（ERROR 0件が必須）。該当箇所を修正して再実行してください。")
        sys.exit(1)
    print("完了条件クリア（ERROR 0件）。WARNは人間が判断してください。")
    sys.exit(0)


if __name__ == "__main__":
    main()
