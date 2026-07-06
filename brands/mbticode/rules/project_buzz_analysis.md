---
name: project-buzz-analysis
description: MBTICODEのX/Threadsバズ・パフォーマンス分析における役割分担（手動共有に確定・ブラウザ自動化は技術的制限により見送り）
metadata: 
  node_type: memory
  type: project
  originSessionId: e2a7a043-1fd5-487d-874b-f0dee6052410
---

MBTICODEのSNS投稿分析における役割分担は「ユーザーが数値を収集→Claudeが分析」。

2026-07-05に一度「claude-in-chromeでX/Threadsのアナリティクス画面を直接開いて取得する」方式への切り替えを試みたが、X（x.com）・Threads（threads.com）はどちらも常時バックグラウンド通信があるSPAで、ブラウザ拡張が「ページ読み込み完了」を検知できず取得不能だった（Chrome再起動後も再現）。note.comでは同様の待機で最終的に取得できたため、この2サイト特有の制限とみられる。

**Why:** 自動化を試みたのはKPI入力コストを下げるためだったが、技術的に安定して動かないため、ユーザーが数値（スクリーンショットまたはテキスト）を共有し、Claudeが受け取って分析する従来方式に確定した。

**How to apply:** 週次バズ分析や投稿パフォーマンス確認は、`kpi_weekly_template.md`にユーザーが数値を記入して渡す、またはスクリーンショットを貼ってもらう形で行う。ブラウザでの直接取得は提案しない（既知の制限として扱う）。将来的にX/Threads側の挙動が変わった場合や、他の取得手段が見つかった場合のみ再検討する。分析結果は[[project_mbticode_x_strategy_0609]]の分岐判断・KPIレビューに反映する。
