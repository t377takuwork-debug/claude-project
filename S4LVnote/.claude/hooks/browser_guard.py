#!/usr/bin/env python3
# ブラウザ操作の暴走を機構で止めるガード(Claude Code の PreToolUse / UserPromptSubmit フック)
# 1) 150字を超える type を拒否  2) 1回の依頼の中でブラウザ操作が上限を超えたら拒否して停止を指示
# --reset を付けて呼ぶと回数をリセットする(ユーザーが新しく発言したとき)
# Mac / Windows 共通で動くように、入出力はUTF-8固定・回数ファイルはOSの一時フォルダに置く
import sys, json, os, re, tempfile

LIMIT = 120      # 1回の依頼あたりのブラウザ操作の上限(スケジュール実行で分析→執筆→販売まで通しても収まる回数)
TYPE_MAX = 150   # type で打てる最大文字数

def out_err(msg):
    try:
        sys.stderr.buffer.write((msg + "\n").encode("utf-8"))
        sys.stderr.flush()
    except Exception:
        pass

try:
    data = json.loads(sys.stdin.buffer.read().decode("utf-8", errors="replace"))
except Exception:
    sys.exit(0)

sid = re.sub(r"[^A-Za-z0-9_-]", "_", str(data.get("session_id", "default")))[:80] or "default"
path = os.path.join(tempfile.gettempdir(), f"claude_browser_guard_{sid}.count")

if "--reset" in sys.argv[1:]:
    try:
        os.remove(path)
    except Exception:
        pass
    sys.exit(0)

tool = str(data.get("tool_name", ""))
inp = data.get("tool_input", {})
raw = json.dumps(inp, ensure_ascii=False)

# ブラウザ系ツールか判定(ツール名に computer/browser を含む、または MCP ツールで入力に action/actions を含む)
tl = tool.lower()
is_browser = ("computer" in tl or "browser" in tl
              or (tl.startswith("mcp__") and ('"action"' in raw or '"actions"' in raw)))
if not is_browser:
    sys.exit(0)

# 1) 長文 type の拒否
def walk(o):
    if isinstance(o, dict):
        if o.get("action") == "type":
            yield str(o.get("text", ""))
        for v in o.values():
            yield from walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v)
for text in walk(inp):
    if len(text) > TYPE_MAX:
        out_err(f"ガード: {TYPE_MAX}字を超えるtype入力は禁止です。本文は 3_広報部/社員.md の販売AI手順3(JavaScript実行ツールで合成pasteイベントを1回)で入れてください。")
        sys.exit(2)

# 2) 回数上限
try:
    n = int(open(path, encoding="utf-8").read().strip()) if os.path.exists(path) else 0
except Exception:
    n = 0
n += 1
try:
    with open(path, "w", encoding="utf-8") as f:
        f.write(str(n))
except Exception:
    pass
if n > LIMIT:
    out_err(f"ガード: ブラウザ操作が{n}回に達しました。これ以上の操作は禁止です。今すぐ「[◯◯AI → あなた]」で現状を報告し、停止してください。")
    sys.exit(2)
sys.exit(0)
