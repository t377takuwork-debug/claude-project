---
name: project-buzz-analysis
description: MBTICODEのX/Threadsバズ・パフォーマンス分析における役割分担（2026-09-22改訂・ブラウザ自動取得は解決済み）
metadata: 
  node_type: memory
  type: project
  originSessionId: e2a7a043-1fd5-487d-874b-f0dee6052410
---

MBTICODEのSNS投稿分析における役割分担は「ユーザーが数値を収集→Claudeが分析」（自分のアカウントのアナリティクス数値のみ・下記参照）。

2026-07-05に一度「claude-in-chromeでX/Threadsのアナリティクス画面を直接開いて取得する」方式への切り替えを試みたが、X（x.com）・Threads（threads.com）はどちらも常時バックグラウンド通信があるSPAで、`screenshot`・`get_page_text`・`read_page`・`computer`（scroll等）が「ページ読み込み完了」を検知できず取得不能だった（Chrome再起動後も再現）。

**2026-09-22訂正：この制限は解決済み**。`javascript_tool`（`document.body.innerText`や`document.querySelectorAll`をevalする方式）に切り替えれば、document_idle待ちをしないため即座に取得できる（`env_grok_chrome_automation`メモリ、2026-09-04/05にgrok.com調査で発見・確立。s4lvの`/s4lv-research`スキルで2026-09-22に他アカウントのX投稿反響取得に実運用済み）。**X上の他アカウントの投稿本文・反響数（いいね・ブックマーク等）の取得は、この方式で自動化してよい**。

**ただし自分のアカウント（MBTICODE）のアナリティクス画面（インプレッション詳細・フォロワー推移等の非公開ダッシュボード）は未検証**。こちらは引き続きユーザーが数値を共有する従来方式とする（検証済みなのは「他アカウントの公開投稿の閲覧・反響数取得」であり、ログイン専用の分析画面は別問題の可能性がある）。

**How to apply:** 他アカウントのバズ投稿分析（`/buzz-analysis`）は、`javascript_tool`方式での自動取得を選択肢に入れてよい（s4lvの`.claude/commands/s4lv-research.md`の「技術メモ」を手順の参考にする）。自分のアカウントの週次KPI・パフォーマンス確認は、引き続き`kpi_weekly_template.md`にユーザーが数値を記入して渡す、またはスクリーンショットを貼ってもらう形で行う。分析結果は[[project_mbticode_x_strategy_0609]]の分岐判断・KPIレビューに反映する。
