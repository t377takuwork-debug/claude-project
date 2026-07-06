#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QA Gate — PostToolUseフック（Day 2: QA自動ゲート化）

Edit / Write されたファイルのパスに応じて機械検品ツールを自動実行し、
ERROR（QAツール終了コード非0）なら終了コード2でエージェントに差し戻す。
スキル本文の「qa_draft.pyを必ず実行せよ」に依存しない機械的な品質ゲート。

ルーティング（パスはリポジトリ内の実配置に準拠）:
  blogs/shira_note/draft_*.txt          -> blogs/shira_note/tools/qa_draft.py
  brands/**/posts_x.txt, posts_threads.txt -> brands/tools/qa_post.py
  **/articles/drafts/*.md               -> brands/tools/qa_article.py
                                            （--paid は自動判定不能のため付けない。
                                              有料記事は従来どおり手動で --paid 検品）

終了コード: 0 = 合格または対象外 / 2 = ERROR検出（stderrがエージェントへ返る）
フック登録は .claude/settings.json（execフォーム必須。シェル文字列型は
このマシンではstdinが届かない — git_guardrail.py の経緯と同じ）。
"""
import datetime
import json
import os
import subprocess
import sys
import threading

STDIN_TIMEOUT_SEC = 10
QA_TIMEOUT_SEC = 60
MAX_FEEDBACK_CHARS = 4000

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HOOKS_DIR))
LOG_PATH = os.path.join(HOOKS_DIR, "qa_gate.log")


def log(message):
    """発火確認用ログ（失敗しても本処理には影響させない）"""
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write("{} {}\n".format(
                datetime.datetime.now().isoformat(timespec="seconds"), message))
    except Exception:
        pass


def route(file_path):
    """検品対象なら (QAツール絶対パス, ラベル) を返す。対象外は None。"""
    norm = os.path.normcase(os.path.normpath(file_path))
    base = os.path.basename(norm)
    sep = os.sep

    if base.startswith("draft_") and base.endswith(".txt") \
            and os.path.normcase(os.path.join("blogs", "shira_note")) in norm:
        return (os.path.join(REPO_ROOT, "blogs", "shira_note", "tools", "qa_draft.py"),
                "qa_draft")
    if base in ("posts_x.txt", "posts_threads.txt") \
            and (sep + "brands" + sep) in (sep + norm + sep):
        return (os.path.join(REPO_ROOT, "brands", "tools", "qa_post.py"), "qa_post")
    if base.endswith(".md") \
            and (sep + os.path.join("articles", "drafts") + sep) in norm:
        return (os.path.join(REPO_ROOT, "brands", "tools", "qa_article.py"),
                "qa_article")
    return None


def main():
    try:
        if hasattr(sys.stdin, "reconfigure"):
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    box = {}

    def _read():
        try:
            box["data"] = sys.stdin.read()
        except Exception:
            pass

    reader = threading.Thread(target=_read, daemon=True)
    reader.start()
    reader.join(STDIN_TIMEOUT_SEC)
    if reader.is_alive():
        log("STDIN-TIMEOUT -> allow")
        os._exit(0)

    try:
        data = json.loads((box.get("data") or "").lstrip("\ufeff"))
    except Exception:
        log("PARSE-ERROR -> allow")
        return 0

    if data.get("tool_name") not in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        return 0

    tool_input = data.get("tool_input") or {}
    tool_response = data.get("tool_response") or {}
    file_path = tool_input.get("file_path") or tool_response.get("filePath") or ""
    if not file_path or not os.path.isfile(file_path):
        return 0

    target = route(file_path)
    if target is None:
        return 0
    qa_tool, label = target

    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        proc = subprocess.run(
            [sys.executable, qa_tool, file_path],
            capture_output=True, encoding="utf-8", errors="replace",
            timeout=QA_TIMEOUT_SEC, cwd=REPO_ROOT, env=env,
        )
    except Exception as exc:
        # QAツール自体が動かない場合は編集を止めない（フェイルオープン・ログで検知）
        log("GATE-ERROR {} {}: {}".format(label, file_path, exc))
        return 0

    if proc.returncode == 0:
        log("PASS  {} {}".format(label, file_path))
        return 0

    log("FAIL  {} {} (exit={})".format(label, file_path, proc.returncode))
    output = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    if len(output) > MAX_FEEDBACK_CHARS:
        output = output[:MAX_FEEDBACK_CHARS] + "\n…（出力が長いため省略）"
    sys.stderr.write(
        "[QA Gate] 機械検品で問題が検出されました（{} / 終了コード{}）。\n"
        "対象: {}\n"
        "ERROR 0件（qa_draftは新規WARN 0件も）になるまで修正してください。\n"
        "検品結果:\n{}\n".format(label, proc.returncode, file_path, output)
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
