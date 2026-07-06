---
name: shira-utadeaetara
description: NHK夏の音楽祭 うたであえたら（新規番組）記事・リライト体制の整備状況
metadata: 
  node_type: memory
  type: project
  originSessionId: a7cd133b-76bc-4c38-8cc9-c5035ed456ef
---

2026-07-01、NHK新音楽特番『NHK夏の音楽祭 うたであえたら』（2026年8月15日放送、NHKホール）の新規タイムテーブル記事を作成した。

- ドラフトファイル：`draft_utadeaetara.txt`
- 記事URL：`https://shira-treat.com/utadeaetara-timetable/`
- 専用リライトコマンド：`/utadeaetara-rewrite`（`.claude/commands/utadeaetara-rewrite.md`）を新設し、`shira_note/CLAUDE.md`のコマンド一覧・ドラフト命名表に登録済み
- 全asideに`aria-label`を付与し、Grepマーカーによる部分編集に対応済み

**Why:** 作成時点（記事公開時）は司会1名（大森元貴／Mrs. GREEN APPLE、音楽番組初司会）のみ確定、出演者は完全未発表の段階だった。残り2名の司会者は7/1・7/2発表予定、出演者・観覧募集詳細は7/3以降順次判明の見込み。

**How to apply:** 今後この番組の続報（司会者追加・出演者発表・タイムテーブル確定・放送後の振り返り）が来たら、`/utadeaetara-rewrite`を起動してリライトする。他番組と異なり初回放送のため「過去のタイムテーブル」アーカイブ節が未整備で、放送後の初回対応時にSTAR/CDTVの構造を参考に新設する必要がある（[[shira-new-article-workflow]]参照）。
