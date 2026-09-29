#!/usr/bin/env python3
"""Build the analysis table for /mbticode-analysis from the Threads spreadsheet (read-only).

Usage:
  python export_analysis_table.py [--since YYYY-MM-DD] [--baseline-days 28] [--min-age-hours 48]
                                  [--max-diagnose 8] [--max-controls 3] [--out PATH]

  基礎分析（全期間を通す初回）：
  python export_analysis_table.py --since 2026-07-26 --baseline-days 400 --max-diagnose 14 --max-controls 5

Joins the 「Threads投稿キュー」 tab (本文・時刻・型・FW・自己リプライ) with the 「インサイト」 tab
(Views/Likes/Replies/Reposts/Quotes) on 投稿ID and writes a markdown file the analyst reads.

Design (2026-09-29, owner decisions + first dry-run findings):
  - 診断する期間 = --since（既定7日前）〜（今 − min-age-hours）。公開直後の投稿は数字が育っていないので除く
  - 基準線 = 直近 --baseline-days 日（既定28）の、公開から min-age-hours 以上経った全投稿
    （診断対象を選んだ結果に引っ張られないよう、診断期間より長い母集団から取る）
  - 判定はこのツールが計算する（診断役は計算しない）：
      Views区分＝基準線の上位20%／中間／下位50%
      反応区分＝強（Replies/Reposts/Quotes が1以上）／中（Likesが2以上・Viewsが中央値超・Likes率が基準線の上位20%）／弱
  - 診断対象 = 反応が強・中のもの（枠の半分）＋Views上位20%のもの（Viewsの大きい順）を、最大 --max-diagnose 本
  - 反響のなかった投稿は個別診断しない。型ごとの機械集計と、対照サンプル（同じ型でViewsが最も低い投稿を最大 --max-controls 本）だけ出す
  - 自己リプライの数字はシートに無いので出さない
"""
import argparse
import datetime
import json
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from google.oauth2 import service_account
from googleapiclient.discovery import build

TOOLS_DIR = Path(__file__).resolve().parent
CREDS_FILE = TOOLS_DIR / "sheets_service_account.local.json"
CONFIG_FILE = TOOLS_DIR / "sheets_config.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
MIN_BASELINE_POSTS = 12
FAMILIES = ["数字リスト型", "リスト型", "非対称理解型", "ミニマル観察型", "二つの温度型", "型C'", "型C",
            "型B", "型A", "型α", "命名"]


def num(s):
    try:
        return int(float(str(s).replace(",", "").strip()))
    except ValueError:
        return 0


def parse_dt(s):
    s = (s or "").strip().replace("/", "-")
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def col(r, i):
    return r[i] if len(r) > i else ""


def family(t):
    for f in FAMILIES:
        if f in t:
            return f
    return t.split("・")[0].split("／")[0][:10] or "不明"


def shape(t):
    return "続き型" if "続き型" in t else ("URL事後型" if "URL事後型" in t else "完結型")


def fw_group(fw):
    if "ラブタイプ" in fw:
        return "ラブタイプ"
    if "MBTI" in fw:
        return "MBTI"
    if "なし" in fw:
        return "タイプなし"
    return "その他"


def aggregate_lines(posts, keyfunc, chosen_ids, indent="  - "):
    grp = defaultdict(list)
    for p in posts:
        grp[keyfunc(p)].append(p)
    rows = []
    for k, ps in sorted(grp.items(), key=lambda kv: -len(kv[1])):
        vs = [x["views"] for x in ps]
        rows.append(f"{indent}{k}｜{len(ps)}本｜{statistics.median(vs):g}｜"
                    f"{sum(1 for x in ps if x['vlab'] == '上位20%')}本｜"
                    f"{sum(1 for x in ps if x['rlab'] in ('強', '中'))}本｜"
                    f"{sum(1 for x in ps if x['pid'] in chosen_ids)}本")
    return rows


def percentile(sorted_vals, p):
    """p in [0,1]; linear interpolation."""
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def quote(text):
    return [f"  > {ln}" if ln.strip() else "  >" for ln in (text.splitlines() or [""])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", help="診断する期間の開始日 YYYY-MM-DD（既定：7日前）")
    ap.add_argument("--baseline-days", type=int, default=28, help="基準線に使う期間（日・既定28）")
    ap.add_argument("--min-age-hours", type=float, default=48, help="公開からこの時間未満の投稿は除外（既定48）")
    ap.add_argument("--max-diagnose", type=int, default=8, help="診断対象の最大本数（既定8）")
    ap.add_argument("--exclude-ids-from", help="前回の表のパス。その表に載った投稿（診断対象・対照）を除いて、続きの投稿を診断する")
    ap.add_argument("--max-controls", type=int, default=3, help="対照サンプルの最大本数（既定3）")
    ap.add_argument("--out", help="出力先（既定 tools/output/analysis_table_YYYYMMDD.md）")
    args = ap.parse_args()

    now = datetime.datetime.now()
    since = parse_dt(args.since) if args.since else now - datetime.timedelta(days=7)
    if since is None:
        print("ERROR: --since は YYYY-MM-DD で指定してください。")
        sys.exit(2)
    cutoff = now - datetime.timedelta(hours=args.min_age_hours)
    base_start = now - datetime.timedelta(days=args.baseline_days)

    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    creds = service_account.Credentials.from_service_account_file(str(CREDS_FILE), scopes=SCOPES)
    sheets = build("sheets", "v4", credentials=creds).spreadsheets()
    q = sheets.values().get(spreadsheetId=config["spreadsheet_id"],
                            range=f"{config['queue_sheet_name']}!A2:K",
                            valueRenderOption="FORMATTED_VALUE").execute().get("values", [])
    ins = sheets.values().get(spreadsheetId=config["spreadsheet_id"],
                              range=f"{config['insights_sheet_name']}!A2:J",
                              valueRenderOption="FORMATTED_VALUE").execute().get("values", [])

    metrics = {}
    for r in ins:
        pid = col(r, 0).strip()
        if pid:
            metrics[pid] = {"views": num(col(r, 4)), "likes": num(col(r, 5)), "replies": num(col(r, 6)),
                            "reposts": num(col(r, 7)), "quotes": num(col(r, 8)), "captured": col(r, 9)}

    pool = []            # 基準線用（期間 baseline-days・成熟済み）
    skipped_young = 0
    for r in q:
        dt = parse_dt(col(r, 0))
        pid = col(r, 6).strip()
        if dt is None or not pid or col(r, 5).strip() != "投稿済み" or dt < min(base_start, since):
            continue
        if dt > cutoff:
            skipped_young += 1
            continue
        m = metrics.get(pid)
        if not m:
            continue
        pool.append({"dt": dt, "body": col(r, 1), "reply": col(r, 2), "url_reply": col(r, 9),
                     "type": col(r, 3), "fw": col(r, 4), "pid": pid, "fam": family(col(r, 3)),
                     "shape": shape(col(r, 3)), **m})

    base = [p for p in pool if p["dt"] >= base_start]
    window = [p for p in pool if p["dt"] >= since]
    if not window:
        print("診断する期間に投稿がありません（--since を見直してください）。")
        sys.exit(0)

    seen_before = set()
    if args.exclude_ids_from:
        seen_before = set(re.findall(r"ID (\d+)", Path(args.exclude_ids_from).read_text(encoding="utf-8")))

    views_sorted = sorted(p["views"] for p in base)
    rates_sorted = sorted(p["likes"] / p["views"] for p in base if p["views"] > 0)
    v80, v50 = percentile(views_sorted, 0.8), percentile(views_sorted, 0.5)
    r80 = percentile(rates_sorted, 0.8)
    med_v = statistics.median(views_sorted) if views_sorted else 0

    for p in pool:
        p["vlab"] = "上位20%" if p["views"] >= v80 else ("中間" if p["views"] > v50 else "下位50%")
        rate = p["likes"] / p["views"] if p["views"] else 0
        p["rate"] = rate
        if p["replies"] or p["reposts"] or p["quotes"]:
            p["rlab"] = "強"
        elif p["likes"] >= 2 and p["views"] > v50 and rate >= r80:   # 少数のいいねだけで「中」にならないよう下限を付ける
            p["rlab"] = "中"
        else:
            p["rlab"] = "弱"

    # 診断対象の選び方：枠の半分を「反応が強い・中」（強→中→Viewsの大きい順）、残りを「Viewsの大きい順」で埋める。
    # （反応順だけで埋めると、Viewsが最大級でも反応が弱い投稿が漏れるため）
    order = {"強": 0, "中": 1, "弱": 2}
    by_reaction = sorted([p for p in window if p["rlab"] in ("強", "中") and p["pid"] not in seen_before], key=lambda p: (order[p["rlab"]], -p["views"]))
    by_views = sorted([p for p in window if p["vlab"] == "上位20%" and p["pid"] not in seen_before], key=lambda p: -p["views"])
    half = (args.max_diagnose + 1) // 2
    chosen = by_reaction[:half]
    for p in by_views + by_reaction[half:]:
        if len(chosen) >= args.max_diagnose:
            break
        if p not in chosen:
            chosen.append(p)
    chosen_ids = {p["pid"] for p in chosen}
    chosen.sort(key=lambda p: p["dt"])
    rest = [p for p in window if p["pid"] not in chosen_ids]

    # 対照サンプル：診断対象の型（family）ごとに、同じ型で診断対象外かつViewsが最も低い投稿（最大3本）
    controls = []
    seen_fam = set()
    for p in chosen:
        if p["fam"] in seen_fam or len(controls) >= args.max_controls:
            continue
        seen_fam.add(p["fam"])
        same = [x for x in window if x["fam"] == p["fam"] and x["pid"] not in chosen_ids
                and x["pid"] not in seen_before]
        if same:
            controls.append((p, min(same, key=lambda x: x["views"])))

    out = Path(args.out) if args.out else TOOLS_DIR / "output" / f"analysis_table_{now:%Y%m%d}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    L = []
    L.append(f"# Threads分析用の表（{now:%Y-%m-%d %H:%M} 作成）")
    L.append("")
    L.append("## 基準線")
    L.append(f"- 基準線の母集団：直近{args.baseline_days}日の{len(base)}本"
             f"（公開から{args.min_age_hours:g}時間以上・テスト投稿除く。公開直後で除外 {skipped_young}本）")
    if len(base) < MIN_BASELINE_POSTS:
        L.append(f"- **注意：{MIN_BASELINE_POSTS}本未満のため、基準線は目安にならない（母数不足）**")
    L.append(f"- Views：中央値 {med_v:g}／上位20%の境目 {v80:g}／下位50%の境目 {v50:g}／最大 {max(views_sorted)}")
    L.append(f"- Likes率（Likes÷Views）の上位20%の境目：{r80 * 100:.2f}%")
    L.append("- 区分の意味：Views区分＝基準線内の順位（上位20%・中間・下位50%）。反応区分＝強（Replies/Reposts/Quotesが1以上）／"
             "中（Likesが2以上・Viewsが中央値超・Likes率が上位20%）／弱（それ以外）")
    L.append("- 取れていない数字：保存数・プロフィールクリック・リンククリック・フォロー増・自己リプライ側の数字（診断では触れない）")
    L.append("")
    L.append(f"## 診断する期間：{since:%Y-%m-%d} 以降（{len(window)}本のうち診断対象 {len(chosen)}本）")
    L.append("")
    for p in chosen:
        L.append(f"### {p['dt']:%m/%d %H:%M}｜{p['type']}／{p['fw']}｜ID {p['pid']}")
        L.append(f"- 数字：Views {p['views']}／Likes {p['likes']}（Likes率 {p['rate'] * 100:.2f}%）／Replies {p['replies']}／"
                 f"Reposts {p['reposts']}／Quotes {p['quotes']}（取得 {p['captured']}）")
        L.append(f"- 区分：Views＝{p['vlab']}／反応＝{p['rlab']}")
        L.append("- 本文：")
        L.append("")
        L.extend(quote(p["body"]))
        L.append("")
        if p["reply"].strip():
            L.append("- 自己リプライ：")
            L.append("")
            L.extend(quote(p["reply"]))
            L.append("")
        if p["url_reply"].strip():
            L.append("- URL自己リプライ：あり（記事誘導）")
            L.append("")
    L.append("## 診断しない投稿（機械集計だけ）")
    left_top = sum(1 for p in rest if p["vlab"] == "上位20%")
    left_react = sum(1 for p in rest if p["rlab"] in ("強", "中"))
    L.append(f"- {len(rest)}本。本文は載せない。内訳：反響が弱くViewsも上位でない投稿のほか、"
             f"**診断枠（最大{args.max_diagnose}本）に入らなかった上位20%の投稿 {left_top}本・反応が強・中の投稿 {left_react}本を含む**"
             f"（続きは --exclude-ids-from で診断できる）")
    hdr = "（｜本数｜Views中央値｜Views上位20%の本数｜反応が強・中の本数｜診断対象に入った本数）"
    L.append("- 診断期間の集計" + hdr)
    for name, fn in (("型", lambda x: x["fam"]), ("形", lambda x: x["shape"]),
                     ("タイプの扱い", lambda x: fw_group(x["fw"])), ("時間帯", lambda x: f"{x['dt'].hour:02d}時台")):
        L.append(f"  - ＜{name}別＞")
        L.extend(aggregate_lines(window, fn, chosen_ids, indent="    - "))
    if len(base) > len(window):
        L.append("- 基準線の期間全体の集計" + hdr)
        for name, fn in (("型", lambda x: x["fam"]), ("形", lambda x: x["shape"]),
                         ("タイプの扱い", lambda x: fw_group(x["fw"])), ("時間帯", lambda x: f"{x['dt'].hour:02d}時台")):
            L.append(f"  - ＜{name}別＞")
            L.extend(aggregate_lines(base, fn, chosen_ids, indent="    - "))
    L.append("")
    if controls:
        L.append("## 対照サンプル（診断対象と同じ型で、Viewsが最も低かった投稿）")
        L.append("診断対象との「同じ型なのに何が違うか」を見るための比較用（点数は付けなくてよい・違いだけを述べる）。")
        L.append("")
        for target, c in controls:
            L.append(f"### 対照：{c['dt']:%m/%d %H:%M}｜{c['type']}／{c['fw']}｜ID {c['pid']}（比較相手＝{target['dt']:%m/%d %H:%M}の投稿）")
            L.append(f"- 数字：Views {c['views']}／Likes {c['likes']}／Replies {c['replies']}／Reposts {c['reposts']}／"
                     f"Quotes {c['quotes']}｜区分：Views＝{c['vlab']}／反応＝{c['rlab']}")
            L.append("- 本文：")
            L.append("")
            L.extend(quote(c["body"]))
            L.append("")
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"[OK] {out}")
    print(f"基準線 {len(base)}本（Views中央値 {med_v:g}）／診断期間 {len(window)}本 → 診断 {len(chosen)}本・対照 {len(controls)}本")


if __name__ == "__main__":
    main()
