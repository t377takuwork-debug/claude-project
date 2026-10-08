"""Buffer API（公式）で、s4lv の X（@cfrms4lv）の予約を送る小さな道具。
元は UYAnote/.claude/hooks/buffer_api.py。s4lv の投稿ファイル（3_広報部/投稿文/posts_x.txt）の形を読めるようにした。

使い方（S4LVnote フォルダで実行する）:
  python .claude/hooks/buffer_api.py channels            # つながっているチャンネルの一覧（読み取りだけ）
  python .claude/hooks/buffer_api.py list <posts_x.txt> M/D
      その日の投稿の番号・日時・自己リプライの有無を出す（キーは要らない。何も送らない）
  python .claude/hooks/buffer_api.py send <posts_x.txt> M/D [番号 ...] [--draft|--go]
      その日の投稿（番号を省くと全部）を送る。何も付けないと「送る内容の確認」だけ（送らない）。
      --draft: Bufferの下書きに入れる / --go: 予約として入れる。日時は見出しの時刻を日本時間として扱う。
      番号は見出しの丸数字（①②…）か、その数字（1 2 …）。
キーは S4LVnote/.env.local の BUFFER_API_KEY から読む（UYAnote と同じ Buffer のキー）。画面には出さない。
送る先は、Bufferにつながっている X のチャンネルのうち、名前が CHANNEL_NAME のもの（毎回、名前で探す）。
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
CHANNEL_NAME = "cfrms4lv"
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"

YEAR_RE = re.compile(r"─+\s*(\d{4})-\d{2}-\d{2}")
HEADER_RE = re.compile(r"^【(.+)】\s*$")
SEP_RE = re.compile(r"^-{8,}\s*$")
REPLY_INLINE_RE = re.compile(r"^自己リプライ\d?（[^）]*）[:：]\s*(.*)$")


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
                 "User-Agent": "s4lvnote-buffer/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"http_error": e.code, "body": e.read().decode("utf-8", "replace")[:800]}


ORGS = "query { account { organizations { id name } } }"


def list_channels():
    """組織ごとに、チャンネルの一覧を返す。組織の中からチャンネルをたどる聞き方は、
    Bufferが「この情報を見る許可がない」と返すため、組織の番号を渡してチャンネルを聞く（2026-10-08）。"""
    res = gql(ORGS)
    orgs = ((res.get("data") or {}).get("account") or {}).get("organizations") or []
    if not orgs:
        sys.exit("Bufferの組織が取れません: " + json.dumps(res, ensure_ascii=False)[:300])
    out = []
    for org in orgs:
        q = 'query { channels(input: {organizationId: "%s"}) { id name service } }' % org["id"]
        r = gql(q)
        chs = (r.get("data") or {}).get("channels")
        if chs is None:
            sys.exit("チャンネルが取れません: " + json.dumps(r, ensure_ascii=False)[:300])
        out.append({"organization": org.get("name"), "channels": chs})
    return out

CREATE = """mutation($i: CreatePostInput!){ createPost(input:$i){
 ... on PostActionSuccess { post { id status dueAt } } ... on MutationError { message } } }"""


def find_channel():
    for org in list_channels():
        for ch in org["channels"]:
            if ch.get("service") == "twitter" and CHANNEL_NAME.lower() in (ch.get("name") or "").lower():
                return ch["id"]
    sys.exit(f"Bufferに、名前に「{CHANNEL_NAME}」を含む X のチャンネルが見つかりません。"
             f"`python .claude/hooks/buffer_api.py channels` で確かめてください。")


def parse(path):
    """posts_x.txt から、日時のある投稿を (番号, 'YYYY-MM-DD HH:MM', 本文, 自己リプライ or None) で返す。
    日付未定の投稿・時刻のない投稿は飛ばす。"""
    lines = open(path, encoding="utf-8").read().splitlines()
    year = datetime.date.today().year
    out = []
    i = 0
    while i < len(lines):
        y = YEAR_RE.search(lines[i])
        if y:
            year = int(y.group(1))
        h = HEADER_RE.match(lines[i])
        if not h:
            i += 1
            continue
        head = h.group(1)
        # 本文 = 見出しの次の区切り線から、次の区切り線まで
        j = i + 1
        while j < len(lines) and not SEP_RE.match(lines[j]) and not HEADER_RE.match(lines[j]):
            j += 1
        if j >= len(lines) or not SEP_RE.match(lines[j]):
            i = j
            continue
        k = j + 1
        body = []
        while k < len(lines) and not SEP_RE.match(lines[k]):
            body.append(lines[k])
            k += 1
        # 自己リプライ = 閉じの区切り線のあと、次の見出しまで（「▼自己リプライ」の行・区切り線・見出し行は除く）
        m = k + 1
        reply = []
        while m < len(lines) and not HEADER_RE.match(lines[m]) and not YEAR_RE.search(lines[m]):
            ln = lines[m]
            r = REPLY_INLINE_RE.match(ln.strip())
            if r:
                reply.append(r.group(1))
            elif not (ln.startswith("▼") or SEP_RE.match(ln) or ln.startswith("■")):
                reply.append(ln)
            m += 1
        i = m
        if "日付未定" in head:
            continue
        d = re.search(r"(\d{1,2})/(\d{1,2})", head)
        t = re.search(r"(\d{1,2}):(\d{2})", head)
        if not d or not t:
            continue
        num = next((CIRCLED.index(c) + 1 for c in head[:3] if c in CIRCLED), None)
        when = f"{year}-{int(d.group(1)):02d}-{int(d.group(2)):02d} {int(t.group(1)):02d}:{t.group(2)}"
        rep = "\n".join(reply).strip()
        out.append((num, when, "\n".join(body).strip(), rep or None))
    return out


def pick(path, md, nums):
    mm, dd = (int(x) for x in md.split("/"))
    rows = [p for p in parse(path) if p[1][5:10] == f"{mm:02d}-{dd:02d}"]
    if nums:
        rows = [p for p in rows if p[0] in nums]
    if not rows:
        sys.exit(f"{md} の、日時のある投稿が見つかりません（日付未定の投稿は送れません）")
    return rows


def send(path, md, nums, mode):
    rows = pick(path, md, nums)
    channel = find_channel() if mode != "check" else None
    for n, when, main, reply in rows:
        jst = datetime.datetime.strptime(when, "%Y-%m-%d %H:%M")
        due = (jst - datetime.timedelta(hours=9)).strftime("%Y-%m-%dT%H:%M:00.000Z")
        thread = [{"text": main}] + ([{"text": reply}] if reply else [])
        label = CIRCLED[n - 1] if n else "?"
        print(f"--- {label} {when}(日本時間) 自己リプライ:{'あり' if reply else 'なし'}")
        print(main + ("\n[自己リプライ]\n" + reply if reply else ""))
        if mode == "check":
            continue
        inp = {"channelId": channel, "text": main, "schedulingType": "automatic",
               "mode": "customScheduled", "dueAt": due, "needsApproval": False,
               "assets": [], "metadata": {"twitter": {"thread": thread}}}
        if mode == "draft":
            inp["saveToDraft"] = True
        print("→", json.dumps(gql(CREATE, {"i": inp}), ensure_ascii=False))


def parse_nums(args):
    out = set()
    for a in args:
        if a.isascii() and a.isdigit():
            out.add(int(a))
        else:
            out |= {CIRCLED.index(c) + 1 for c in a if c in CIRCLED}
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    a = sys.argv[1:]
    cmd = a[0] if a else ""
    if cmd == "channels":
        print(json.dumps(list_channels(), ensure_ascii=False, indent=1))
    elif cmd in ("list", "send") and len(a) >= 3:
        rest = [x for x in a[3:] if not x.startswith("--")]
        if cmd == "list":
            for n, when, main, reply in pick(a[1], a[2], parse_nums(rest)):
                print(f"{CIRCLED[n - 1] if n else '?'} {when} 自己リプライ:{'あり' if reply else 'なし'} 1行目: {main.splitlines()[0][:30]}")
        else:
            mode = "draft" if "--draft" in a else "go" if "--go" in a else "check"
            send(a[1], a[2], parse_nums(rest), mode)
    else:
        sys.exit(__doc__)
