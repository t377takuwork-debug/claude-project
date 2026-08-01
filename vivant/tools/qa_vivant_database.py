#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""qa_vivant_database.py — vivant考察データベース 機械検品ツール

完了条件: ERROR 0件（終了コード0）。WARNは参考情報（人間が判断する）。

使い方:
  python vivant/tools/qa_vivant_database.py vivant_database_ep12.md
  python vivant/tools/qa_vivant_database.py vivant_database_ep12.md --prev vivant_database_ep11.md

  --prev を省略した場合、同じディレクトリ内の vivant_database_ep[N].md より話数の若い
  最新版を自動検出する（例: ep12.md なら ep11.md・ep10.md...のうち最大のもの）。

チェック内容（出典: vivant_database_ep11.md「5. データベース運用マニュアル」）:
  1. ファイル名が vivant_database_ep[N].md 形式か … ERROR
  2. ヘッダーに「最終更新」「カバー範囲」があるか … ERROR
  3. 「5. データベース運用マニュアル」セクションが旧版から一字一句変わっていないか … ERROR
     （5-0: マニュアルは削除・要約・改変禁止）
  4. ステータスタグが [確定]/[未解決]/[棄却] の3種のみか（未知のタグ・誤字を検出） … ERROR/WARN
     （5-2: 新しいステータスを発明しない）
  5. セクション1（確定している事実）に「箱舟」が混入していないか … ERROR
     （5-4: 「方舟」＝本編公式用語／「箱舟」＝ファン考察用語。混同禁止）
  6. 仮説項目（### 2-N 見出し）・キャラクター表の行数が旧版より減っていないか … ERROR
     （5-3: 過去の考察・文脈を削除しない。差分更新のみ許可）
  7. [確定]/[棄却] に変更された項目に根拠（「第◯話」等）が併記されているか … WARN
     （5-2: ステータス変更時は変更理由を1行併記）
  8. [未解決] 項目に「根拠」「反論・矛盾点」の両方があるか … WARN
     （5-1: 仮説は3要素で記録する）
  9. 話数が前バージョンの直後（N-1 → N）になっているか … WARN（情報として提示のみ）
"""
import argparse
import glob
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

FILENAME_RE = re.compile(r"vivant_database_ep(\d+)\.md$")
MANUAL_HEADING_RE = re.compile(r"^## 5\..*運用マニュアル.*$", re.M)
SECTION1_RANGE_RE = re.compile(r"^## 1\..*?(?=^## 2\.)", re.M | re.S)
STATUS_TOKEN_RE = re.compile(r"\[([^\]\n]{1,10})\]")
ALLOWED_STATUS = {"確定", "未解決", "棄却"}
# よくある「発明されがちな」代替ステータス（誤用をERRORで即検知）
INVENTED_STATUS_BLOCKLIST = {
    "保留", "濃厚", "検討中", "確認中", "仮確定", "有力", "濃厚候補", "調査中", "確定的",
}
HYPOTHESIS_HEADING_RE = re.compile(r"^### 2-\d+", re.M)
TABLE_ROW_RE = re.compile(r"^\|.+\|$", re.M)


def find_prev_file(new_path):
    m = FILENAME_RE.search(os.path.basename(new_path))
    if not m:
        return None
    n = int(m.group(1))
    d = os.path.dirname(new_path) or "."
    candidates = []
    for f in glob.glob(os.path.join(d, "vivant_database_ep*.md")):
        fm = FILENAME_RE.search(os.path.basename(f))
        if fm and int(fm.group(1)) < n:
            candidates.append((int(fm.group(1)), f))
    if not candidates:
        return None
    candidates.sort()
    return candidates[-1][1]  # 最大の話数（=直前バージョン）


def extract_manual_section(text):
    m = MANUAL_HEADING_RE.search(text)
    if not m:
        return None
    return text[m.start():].strip()


def extract_section1(text):
    m = SECTION1_RANGE_RE.search(text)
    return m.group(0) if m else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="検品対象の新バージョン（例: vivant_database_ep12.md）")
    ap.add_argument("--prev", help="比較対象の旧バージョン（省略時は自動検出）")
    args = ap.parse_args()

    errors, warns, infos = [], [], []

    if not os.path.exists(args.file):
        print(f"[ERROR] file-not-found: {args.file} が見つかりません")
        sys.exit(1)

    with open(args.file, encoding="utf-8") as fh:
        new_text = fh.read()

    # 1. ファイル名チェック
    if not FILENAME_RE.search(os.path.basename(args.file)):
        errors.append(f"[ERROR] filename: 「{args.file}」は vivant_database_ep[N].md 形式ではありません")

    # 2. ヘッダー必須項目
    head = "\n".join(new_text.splitlines()[:15])
    if "最終更新" not in head:
        errors.append("[ERROR] header-missing: ヘッダーに「最終更新」がありません")
    if "カバー範囲" not in head:
        errors.append("[ERROR] header-missing: ヘッダーに「カバー範囲」がありません")

    # 4. ステータストークンの妥当性
    # 運用マニュアル本文は禁止トークンを「悪い例」として説明のために使うため、スキャン対象から除外する
    manual_start_m = MANUAL_HEADING_RE.search(new_text)
    scannable_text = new_text[:manual_start_m.start()] if manual_start_m else new_text
    invalid_found = set()
    for m in STATUS_TOKEN_RE.finditer(scannable_text):
        token = m.group(1)
        if token in ALLOWED_STATUS:
            continue
        if token in INVENTED_STATUS_BLOCKLIST:
            line_no = new_text[:m.start()].count("\n") + 1
            errors.append(f"[ERROR] L{line_no} invented-status: 未定義のステータス「[{token}]」が使われています（許可は[確定]/[未解決]/[棄却]のみ）")
            invalid_found.add(token)

    # 5. 「箱舟」混入チェック（セクション1のみ）
    section1_text = extract_section1(new_text)
    if "箱舟" in section1_text:
        for m in re.finditer("箱舟", section1_text):
            errors.append("[ERROR] hakobune-in-facts: セクション1（確定している事実）に「箱舟」が混入しています（本編公式用語は「方舟」。「箱舟」はファン考察側の表記）")
            break  # 1件出せば十分

    prev_path = args.prev or find_prev_file(args.file)
    if prev_path and os.path.exists(prev_path):
        with open(prev_path, encoding="utf-8") as fh:
            prev_text = fh.read()

        # 3. 運用マニュアルの不変チェック
        new_manual = extract_manual_section(new_text)
        prev_manual = extract_manual_section(prev_text)
        if prev_manual is None:
            warns.append(f"[WARN] no-manual-in-prev: 旧版（{prev_path}）に運用マニュアルが見つかりません（初回移行時のみ許容）")
        elif new_manual is None:
            errors.append("[ERROR] manual-missing: 新版に「5. データベース運用マニュアル」セクションがありません")
        elif new_manual.strip() != prev_manual.strip():
            errors.append(f"[ERROR] manual-changed: 「5. データベース運用マニュアル」の内容が旧版（{prev_path}）から変更されています（削除・要約・改変は禁止）")

        # 6. 項目の非削減チェック
        prev_hyp = len(HYPOTHESIS_HEADING_RE.findall(prev_text))
        new_hyp = len(HYPOTHESIS_HEADING_RE.findall(new_text))
        if new_hyp < prev_hyp:
            errors.append(f"[ERROR] hypothesis-decreased: 仮説項目（### 2-N）が {prev_hyp}件 → {new_hyp}件 に減少しています（過去の考察は削除禁止）")
        else:
            infos.append(f"[INFO] 仮説項目数: {prev_hyp}件 → {new_hyp}件")

        prev_rows = len(TABLE_ROW_RE.findall(prev_text))
        new_rows = len(TABLE_ROW_RE.findall(new_text))
        if new_rows < prev_rows:
            errors.append(f"[ERROR] table-rows-decreased: 表の行数が {prev_rows}行 → {new_rows}行 に減少しています（キャラクター表等の削除禁止）")

        # 9. 話数連続性（情報のみ）
        pm = FILENAME_RE.search(os.path.basename(prev_path))
        nm = FILENAME_RE.search(os.path.basename(args.file))
        if pm and nm and int(nm.group(1)) != int(pm.group(1)) + 1:
            warns.append(f"[WARN] episode-gap: 話数が連続していません（旧版 第{pm.group(1)}話 → 新版 第{nm.group(1)}話）")

        # 7. ステータス変更の根拠併記チェック（[確定]/[棄却]の周辺に「第◯話」があるか）
        # 対象は本文（セクション1以降・マニュアル手前）のみ。かつ「旧版に存在しなかった＝今回変化した箇所」だけを見る
        # （旧版から変わらず持ち越された記述にまで根拠併記を要求すると誤検知が大量発生するため）
        content_start_m = re.search(r"^## 1\.", new_text, re.M)
        content_start = content_start_m.start() if content_start_m else 0
        content_end = manual_start_m.start() if manual_start_m else len(new_text)
        window_len = 80
        for status in ("確定", "棄却"):
            tag = f"[{status}]"
            search_from = content_start
            while True:
                pos = new_text.find(tag, search_from, content_end)
                if pos == -1:
                    break
                search_from = pos + 1
                window = new_text[pos:pos + window_len]
                if window in prev_text:
                    continue  # 旧版から変化なし（キャリーオーバー項目）
                if not re.search(r"第\d+話", window):
                    line_no = new_text[:pos].count("\n") + 1
                    warns.append(f"[WARN] L{line_no} no-rationale: 旧版になかった「[{status}]」の直後{window_len}字以内に「第◯話」の根拠記載が見当たりません")
    else:
        warns.append("[WARN] no-prev-file: 比較対象の旧バージョンが見つかりません（新規初版のため差分チェックをスキップ）")

    # 8. [未解決]項目の3要素チェック（### 2-N ブロック単位）
    blocks = list(re.finditer(r"^### (2-\d+)[^\n]*\n(.*?)(?=^### 2-\d+|\Z)", new_text, re.M | re.S))
    for m in blocks:
        label, body = m.group(1), m.group(2)
        if "[未解決]" not in m.group(0):
            continue
        missing = []
        if "根拠" not in body:
            missing.append("根拠")
        if "反論" not in body and "矛盾点" not in body:
            missing.append("反論・矛盾点")
        if missing:
            warns.append(f"[WARN] {label}: {'・'.join(missing)}の記載が見当たりません（仮説は3要素で記録するルール）")

    print(f"=== qa_vivant_database: {args.file} ===")
    if prev_path:
        print(f"（比較対象: {prev_path}）")
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
