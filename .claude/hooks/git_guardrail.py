#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Git Guardrail — PreToolUseフック（第1層）

Claude が Bash / PowerShell ツールで破壊的コマンドを実行しようとしたとき、
実行前にブロックする。第2層は .claude/settings.json の permissions.deny。

判定ルールを追加・緩和する場合は RULES / check_special を編集する。
引用符内（コミットメッセージ等）は判定前に除去されるため、
「reset --hard について」のような文字列を含むメッセージは誤検知しない。

終了コード: 0 = 許可 / 2 = ブロック（stderr がエージェントへ返る）
"""
import datetime
import json
import os
import re
import sys

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guardrail.log")


def log(message):
    """発火確認用ログ（失敗しても本処理には影響させない）"""
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write("{} {}\n".format(
                datetime.datetime.now().isoformat(timespec="seconds"), message))
    except Exception:
        pass

# 再帰削除フラグ: -r, -rf, -fr, -R, -Recurse, --recursive, /s
# （-Force / -f 単独は含まない — 単一ファイル削除まで塞がないため）
RECURSIVE_FLAG = r"(?:^|\s)(?:/s\b|--recursive\b|-fr\b|-r(?:f|ec\w*)?\b)"

# (正規表現, フラグ, 説明)
RULES = [
    (r"\bgit\b.*\breset\b.*--hard", re.I,
     "git reset --hard（未コミットの変更が消える）"),
    (r"\bgit\b.*\bclean\b\s.*-\w*[fdxFDX]", 0,
     "git clean（未追跡ファイルが削除される）"),
    (r"\bgit\b.*\bpush\b.*(?:--force|\s-f\b)", re.I,
     "git push --force（リモート履歴を破壊する）"),
    (r"\bgit\b.*\bbranch\b.*\s-D\b", 0,
     "git branch -D（未マージブランチの強制削除）"),
    (r"\bgit\b(?=.*\bbranch\b)(?=.*--delete)(?=.*--force)", re.I,
     "git branch --delete --force"),
    (r"\bgit\b.*\bcheckout\b\s+(?:--(?:\s|$)|\.(?:\s|$))", re.I,
     "git checkout -- / git checkout .（作業ツリーの変更が消える）"),
    (r"\bgit\b.*\bstash\b.*\b(?:drop|clear)\b", re.I,
     "git stash drop/clear（退避した変更が消える）"),
    (r"\bdel\b\s.*/[fsq]\b", re.I,
     "del /f /s /q（一括削除）"),
]


def check_special(cmd):
    # git restore は --staged 単独（ステージ解除のみ）だけ許可
    if re.search(r"\bgit\b.*\brestore\b", cmd, re.I):
        staged = re.search(r"--staged\b|\s-S\b", cmd)
        worktree = re.search(r"--worktree\b|\s-W\b", cmd)
        if not staged or worktree:
            return "git restore（作業ツリーの変更が消える。--staged 単独のみ許可）"
    # 再帰削除（rm / Remove-Item / rmdir / rd + 再帰フラグ）
    if re.search(r"\b(?:rm|remove-item|rmdir|rd)\b", cmd, re.I) \
            and re.search(RECURSIVE_FLAG, cmd, re.I):
        return "再帰削除（rm -r / Remove-Item -Recurse 系）"
    return None


def main():
    try:
        if hasattr(sys.stdin, "reconfigure"):
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    try:
        data = json.load(sys.stdin)
    except Exception:
        log("PARSE-ERROR -> allow")
        return 0  # 入力が読めない場合はブロックしない（フェイルオープン）

    if data.get("tool_name") not in ("Bash", "PowerShell"):
        return 0

    raw = (data.get("tool_input") or {}).get("command") or ""
    if not raw:
        return 0

    # 引用符・ヒアストリング内を除去してから判定（コミットメッセージ等の誤検知防止）
    stripped = re.sub(r"@'[\s\S]*?'@|@\"[\s\S]*?\"@", ' "" ', raw)
    stripped = re.sub(r"\"[^\"]*\"|'[^']*'", ' "" ', stripped)
    cmd = " ".join(stripped.split())

    label = None
    for pattern, flags, desc in RULES:
        if re.search(pattern, cmd, flags):
            label = desc
            break
    if label is None:
        label = check_special(cmd)
    if label is None:
        log("ALLOW  {}: {}".format(data.get("tool_name"), raw[:120]))
        return 0
    log("BLOCK  {}: {} [{}]".format(data.get("tool_name"), raw[:120], label))

    sys.stderr.write(
        "[Git Guardrail] ブロックしました: {}\n"
        "コマンド: {}\n"
        "この操作は破壊的なため実行できません。どうしても必要な場合は、"
        "ユーザーに理由を説明し、ユーザー自身の判断・操作で実行してもらってください。\n".format(label, raw)
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
