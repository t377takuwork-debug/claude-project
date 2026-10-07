"""Buffer API（公式）で、Xの予約を送る小さな道具。
使い方:
  python buffer_api.py channels            # つながっているチャンネルの一覧(読み取りだけ)
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
            out.append((int(m.group(1)), d.group(1), main[0].strip(), reply[0].strip() if reply else None))
    return out


def send(path, nums, mode):
    for n, when, main, reply in parse(path):
        if nums and n not in nums:
            continue
        jst = datetime.datetime.strptime(when, "%Y-%m-%d %H:%M")
        due = (jst - datetime.timedelta(hours=9)).strftime("%Y-%m-%dT%H:%M:00.000Z")
        thread = [{"text": main}] + ([{"text": reply}] if reply else [])
        print(f"--- {n}本目 {when}(JST) 自己返信:{'あり' if reply else 'なし'}")
        print(main + ("\n[自己返信]\n" + reply if reply else ""))
        if mode == "check":
            continue
        inp = {"channelId": CHANNEL_ID, "text": main, "schedulingType": "automatic",
               "mode": "customScheduled", "dueAt": due, "needsApproval": False,
               "assets": [], "metadata": {"twitter": {"thread": thread}}}
        if mode == "draft":
            inp["saveToDraft"] = True
        print("→", json.dumps(gql(CREATE, {"i": inp}), ensure_ascii=False))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "channels":
        q = "query { account { organizations { id name channels { id name service } } } }"
        print(json.dumps(gql(q), ensure_ascii=False, indent=1))
    elif cmd == "query":
        print(json.dumps(gql(sys.argv[2]), ensure_ascii=False, indent=1))
    elif cmd == "send":
        a = sys.argv[2:]
        mode = "draft" if "--draft" in a else "go" if "--go" in a else "check"
        send(a[0], {int(x) for x in a[1:] if x.isdigit()}, mode)
    else:
        sys.exit(__doc__)
