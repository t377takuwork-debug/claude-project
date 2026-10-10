"""Buffer API（公式）で、Xの予約を送る小さな道具。
使い方:
  python buffer_api.py channels            # つながっているチャンネルの一覧(読み取りだけ)
  python buffer_api.py metrics             # 送信済みの投稿ごとの数字(表示・いいね・コメント等。読み取りだけ)
  python buffer_api.py query "<GraphQL>"   # 任意の問い合わせ(調査用)
  python buffer_api.py send <提案.md> [N ...] [--draft|--go]
      提案ファイルのN本目(省略で全部)を送る。何も付けないと「送る内容の確認」だけ(送らない)。
      --draft: Bufferの下書きに入れる / --go: 予約として入れる。日時は「予約日時」をJSTとして扱う。
キーは UYAnote/.env.local の BUFFER_API_KEY から読む。画面には出さない。
"""
import json
import re
import datetime
import os
import sys
import urllib.request
import urllib.error

ENDPOINT = "https://api.buffer.com"
ENV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env.local")


def load_key():
    with open(ENV, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("BUFFER_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("BUFFER_API_KEY が .env.local にありません")


def gql(query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT, data=body, method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + load_key(),
                 "User-Agent": "uyanote-buffer/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"http_error": e.code, "body": e.read().decode("utf-8", "replace")[:800]}


CHANNEL_ID = "6ac697ec6a5c39ccb644f4c3"  # uyadott (twitter)

CREATE = """mutation($i: CreatePostInput!){ createPost(input:$i){
 ... on PostActionSuccess { post { id status dueAt } } ... on MutationError { message } } }"""


def parse(path):
    text = open(path, encoding="utf-8").read()
    out = []
    for m in re.finditer(r"^## (\d+)本目[^\n]*\n(.*?)(?=^## |\Z)", text, re.S | re.M):
        body = m.group(2)
        d = re.search(r"予約日時: (\d{4}-\d{2}-\d{2} \d{2}:\d{2})", body)
        blocks = re.findall(r"^(?:(自己返信[^\n]*)\n)?```\n(.*?)\n```", body, re.S | re.M)
        if not d or not blocks:
            continue
        main = [b for h, b in blocks if not h]
        reply = [b for h, b in blocks if h]
        if main:
            out.append((int(m.group(1)), d.group(1), main[0].strip(), [r.strip() for r in reply]))
    return out


def send(path, nums, mode):
    for n, when, main, replies in parse(path):
        if nums and n not in nums:
            continue
        jst = datetime.datetime.strptime(when, "%Y-%m-%d %H:%M")
        due = (jst - datetime.timedelta(hours=9)).strftime("%Y-%m-%dT%H:%M:00.000Z")
        thread = [{"text": main}] + [{"text": r} for r in replies]
        print(f"--- {n}本目 {when}(JST) " + (f"続きのポスト:{len(replies)}件" if replies else "自己返信:なし"))
        print(main + "".join("\n[%dつ目の続き]\n%s" % (k, r) for k, r in enumerate(replies, 2)))
        if mode == "check":
            continue
        inp = {"channelId": CHANNEL_ID, "text": main, "schedulingType": "automatic",
               "mode": "customScheduled", "dueAt": due, "needsApproval": False,
               "assets": [], "metadata": {"twitter": {"thread": thread}}}
        if mode == "draft":
            inp["saveToDraft"] = True
        print("→", json.dumps(gql(CREATE, {"i": inp}), ensure_ascii=False))


ORG_ID = "6ac696c03a800282e36bf892"

METRICS = """query($a: String){ posts(first: 50, after: $a, input:{organizationId:"%s"}) {
 pageInfo { hasNextPage endCursor }
 edges { node { id status sentAt channelId text metricsUpdatedAt metrics { name value } metadata { ... on TwitterPostMetadata { thread { text } } } } } } }""" % ORG_ID


def metrics():
    """送信済みの投稿ごとの数字を、1行ずつ出す(読み取りだけ)。"""
    after = None
    rows = []
    while True:
        d = gql(METRICS, {"a": after})
        if d.get("errors") or d.get("http_error"):
            sys.exit("取得できませんでした: " + json.dumps(d, ensure_ascii=False)[:300])
        p = d["data"]["posts"]
        rows += [e["node"] for e in p["edges"]]
        if not p["pageInfo"]["hasNextPage"]:
            break
        after = p["pageInfo"]["endCursor"]
    print("送信日時(JST)\t表示\tいいね\tコメント\t自己返信\t他の人の返信(推定)\tリポスト\tクリック\t数字の更新(JST)\t本文の冒頭")
    for n in sorted((r for r in rows if r["status"] == "sent" and r["sentAt"] and r["channelId"] == CHANNEL_ID), key=lambda r: r["sentAt"]):
        m = {x["name"]: x["value"] for x in n["metrics"]}
        t = lambda s: (datetime.datetime.strptime(s[:16], "%Y-%m-%dT%H:%M") + datetime.timedelta(hours=9)).strftime("%m-%d %H:%M")
        own = max(0, len((n.get("metadata") or {}).get("thread") or []) - 1)
        others = max(0, (m.get("Comments") or 0) - own)
        print("\t".join([t(n["sentAt"]), str(m.get("Impressions")), str(m.get("Reactions")), str(m.get("Comments")),
                         str(own), str(others), str(m.get("Reposts")), str(m.get("Clicks")), t(n["metricsUpdatedAt"]) if n["metricsUpdatedAt"] else "-",
                         n["text"][:20].replace("\n", " ")]))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "channels":
        q = "query { account { organizations { id name channels { id name service } } } }"
        print(json.dumps(gql(q), ensure_ascii=False, indent=1))
    elif cmd == "query":
        print(json.dumps(gql(sys.argv[2]), ensure_ascii=False, indent=1))
    elif cmd == "metrics":
        metrics()
    elif cmd == "send":
        a = sys.argv[2:]
        mode = "draft" if "--draft" in a else "go" if "--go" in a else "check"
        send(a[0], {int(x) for x in a[1:] if x.isdigit()}, mode)
    else:
        sys.exit(__doc__)
