#!/usr/bin/env python3
# オーナーの「今日はここまで」「作業終わります」などの合図を拾い、作業の終わりの手順(owari)を呼ぶように、AIへ知らせる。
# UserPromptSubmit(オーナーが送信したとき)に動く。合図でなければ、何も出さずに終わる(作業を止めない)。
import sys, json, re

# 文のどこにあっても合図とみなす言い方
ANYWHERE = [
    "今日はここまで", "きょうはここまで", "本日はここまで", "今日は終わ", "今日はおわ", "今日は以上",
    "作業終わ", "作業おわ", "作業を終わ", "作業をおわ", "作業終了", "作業はここまで", "作業は以上",
]
# 短い発言(句読点を除いて15字以内)が、これで終わるときだけ合図とみなす言い方
SHORT_END = ["終わります", "おわります", "終わりです", "おわりです", "終了です", "終了します", "おしまい", "ここまでで", "ここまでです", "ここまで"]

def is_signal(text):
    t = re.sub(r"[\s、。,.!！・「」]", "", text or "")
    if not t or t.endswith(("?", "？", "か")):  # 質問は合図にしない
        return False
    if any(w in t for w in ANYWHERE):
        return True
    return len(t) <= 15 and t.endswith(tuple(SHORT_END))

def main():
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace") or "{}")
    except Exception:
        return
    if not is_signal(data.get("prompt", "")):
        return
    msg = ("オーナーが作業の終わりを伝えました。"
           "Skillツールで owari を呼び、`.claude/skills/owari/SKILL.md` の手順を1回だけ行ってください"
           "(今回のやり取りから意図・流れの改善・要らなくなった指示を拾って反映する。確認を取るのは、消す所だけ)。")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}}))

main()
