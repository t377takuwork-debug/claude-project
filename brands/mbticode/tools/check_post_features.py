#!/usr/bin/env python3
"""Count simple text features of Threads posts and compare their reach/reaction (read-only, no LLM).

Usage:
  python check_post_features.py [--since 2026-07-26] [--min-age-hours 48] [--out PATH]

Purpose (2026-09-29): the LLM analyst only diagnoses a selected sample (mostly posts that did well).
This script checks the pattern candidates in analysis/patterns.md against the WHOLE population,
including posts that got no response, by counting features with regexes. Features are approximations
(marked 近似) — use them to support or weaken a candidate, not as proof.

For each feature it prints, for posts WITH vs WITHOUT the feature:
  本数 / Views中央値 / Views上位20%に入った割合 / Replies・Reposts・Quotesが付いた本数 / Likes率（合計Likes÷合計Views）
in three populations: 全体・リスト型を除く・リスト型のみ (list-type posts have far larger Views, so they
are separated to keep them from hiding other differences).
Time-of-day and other confounders are NOT removed here; small groups (<8) are flagged.
"""
import argparse
import datetime
import json
import re
import statistics
import sys
from pathlib import Path

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from google.oauth2 import service_account
from googleapiclient.discovery import build

TOOLS_DIR = Path(__file__).resolve().parent
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
MBTI_RE = re.compile(r"(?<![A-Za-z])([IE][NS][TF][JP])(?![A-Za-z])")
FIRST_PERSON_RE = re.compile(r"自分もそう|言えるけど|言われ|私は|私も|わたしも|自分は|自分が")
NONI_RE = re.compile(r"のに")
SMALL = 8


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


def lines_of(text):
    return [l.strip() for l in text.splitlines() if l.strip()]


def is_list_type(t):
    return "リスト" in t


def features(p):
    body, reply = p["body"], p["reply"]
    ls = lines_of(body)
    first = ls[0] if ls else ""
    bullets = sum(1 for l in ls if re.match(r"^[・\-\d０-９①-⑩]", l))
    length = len(body.replace("\n", ""))
    return {
        "親投稿の本文に問い（？）がある": bool(re.search(r"[？?]", body)),
        "自己リプライがある": bool(reply.strip()),
        "自己リプライに問い（？）がある": bool(re.search(r"[？?]", reply)),
        "一人称の場面・開示がある（近似）": bool(FIRST_PERSON_RE.search(body)),
        "1行目にタイプ名（MBTI4文字）がある": bool(MBTI_RE.search(first)),
        "本文にタイプ名（MBTI4文字）が1つ以上ある": bool(MBTI_RE.search(body)),
        "箇条書きが4行以上": bullets >= 4,
        "「のに」を含む行が3行以上": sum(1 for l in ls if NONI_RE.search(l)) >= 3,
        "本文が350字を超える": length > 350,
        "本文が200字未満": length < 200,
        "1行目が40字を超える": len(first) > 40,
        "URL事後型（記事誘導）": "URL事後型" in p["type"],
    }


def pct(x, n):
    return f"{(100 * x / n):.0f}%" if n else "-"


def summarize(posts, v80):
    n = len(posts)
    if not n:
        return None
    vs = [p["views"] for p in posts]
    likes = sum(p["likes"] for p in posts)
    views = sum(vs)
    return {
        "n": n,
        "med": statistics.median(vs),
        "top": sum(1 for p in posts if p["views"] >= v80),
        "react": sum(1 for p in posts if p["replies"] or p["reposts"] or p["quotes"]),
        "rate": (100 * likes / views) if views else 0,
    }


def fmt(s):
    if s is None:
        return "0本"
    flag = "（少数）" if s["n"] < SMALL else ""
    return (f"{s['n']}本{flag}｜Views中央値 {s['med']:g}｜上位20% {s['top']}本（{pct(s['top'], s['n'])}）｜"
            f"Replies等あり {s['react']}本｜Likes率 {s['rate']:.2f}%")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-07-26")
    ap.add_argument("--min-age-hours", type=float, default=48)
    ap.add_argument("--out")
    args = ap.parse_args()
    now = datetime.datetime.now()
    since = parse_dt(args.since)
    cutoff = now - datetime.timedelta(hours=args.min_age_hours)

    config = json.loads((TOOLS_DIR / "sheets_config.json").read_text(encoding="utf-8"))
    creds = service_account.Credentials.from_service_account_file(
        str(TOOLS_DIR / "sheets_service_account.local.json"), scopes=SCOPES)
    sh = build("sheets", "v4", credentials=creds).spreadsheets()
    q = sh.values().get(spreadsheetId=config["spreadsheet_id"], range=f"{config['queue_sheet_name']}!A2:K",
                        valueRenderOption="FORMATTED_VALUE").execute().get("values", [])
    ins = sh.values().get(spreadsheetId=config["spreadsheet_id"], range=f"{config['insights_sheet_name']}!A2:J",
                          valueRenderOption="FORMATTED_VALUE").execute().get("values", [])
    m = {col(r, 0).strip(): {"views": num(col(r, 4)), "likes": num(col(r, 5)), "replies": num(col(r, 6)),
                             "reposts": num(col(r, 7)), "quotes": num(col(r, 8))} for r in ins if col(r, 0).strip()}
    posts = []
    for r in q:
        dt, pid = parse_dt(col(r, 0)), col(r, 6).strip()
        if dt is None or not pid or col(r, 5).strip() != "投稿済み" or dt < since or dt > cutoff or pid not in m:
            continue
        posts.append({"dt": dt, "body": col(r, 1), "reply": col(r, 2), "type": col(r, 3), **m[pid]})

    vs = sorted(p["views"] for p in posts)
    v80 = vs[int((len(vs) - 1) * 0.8)] if vs else 0
    pops = [("全体", posts),
            ("リスト型を除く", [p for p in posts if not is_list_type(p["type"])]),
            ("リスト型のみ", [p for p in posts if is_list_type(p["type"])])]

    L = [f"# 本文の特徴と反響の関係（機械集計・{now:%Y-%m-%d %H:%M}）", "",
         f"- 対象：{args.since} 以降・公開から{args.min_age_hours:g}時間以上の {len(posts)}本（全部・反響のなかった投稿を含む）",
         f"- Views上位20%の境目：{v80}（この対象内）",
         "- 特徴は正規表現による近似。時間帯・タイプ・型の違いは取り除いていない。少数（8本未満）の区分は参考程度。", ""]
    names = list(features(posts[0]).keys()) if posts else []
    for name in names:
        L.append(f"## {name}")
        for label, pop in pops:
            w = [p for p in pop if features(p)[name]]
            wo = [p for p in pop if not features(p)[name]]
            L.append(f"- {label}")
            L.append(f"  - あり：{fmt(summarize(w, v80))}")
            L.append(f"  - なし：{fmt(summarize(wo, v80))}")
        L.append("")
    out = Path(args.out) if args.out else TOOLS_DIR / "output" / f"post_features_{now:%Y%m%d}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"[OK] {out}")


if __name__ == "__main__":
    main()
