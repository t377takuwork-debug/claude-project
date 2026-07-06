---
name: system-shira-research
description: shira_note専用ネタリサーチスキルの仕様・対象URL・フィルタルール
metadata: 
  node_type: memory
  type: project
  originSessionId: 3a9f8f90-65e8-4d61-8267-31be0cce2b25
---

`/shira-research` スキル（`blogs/shira_note/.claude/commands/shira-research.md`）で管理。

**Why:** 番組タイムテーブル記事・発売予約記事の2種に絞ったネタ収集を自動化するため。

## 収集対象URL（3件並行フェッチ）
| URL | 用途 |
|---|---|
| `https://news.ceek.jp/search.cgi?q=allintitle%3A%E8%A1%A8%E7%B4%99` | 雑誌表紙 |
| `https://news.ceek.jp/search.cgi?q=allintitle%3A%E7%99%BA%E5%A3%B2+%E6%B1%BA%E5%AE%9A` | 発売決定（CD/DVD/BD/写真集） |
| `https://news.ceek.jp/search.cgi?category_id=entertainment` | エンタメ全般（番組情報含む） |

## 時間フィルタ
- **5時間以内**のみ対象
- ceek.jpのタイムスタンプ: 当日=`HH:MM`、前日以前=`DD日 HH:MM`
- 現在時刻はフェッチ結果の最新タイムスタンプから推定

## フィルタルール（2種に限定）
**残す：**
- 音楽番組の出演者・タイムテーブル・歌唱曲情報（Mステ/CDTV/FNS/THE MUSIC DAY等）
- ライブレポート・CM/タイアップ曲の発表
- 音楽アーティストのCD/DVD/BD/雑誌/写真集の発売・予約（表紙登場記事も含む）

**除外：**
- 訃報・プライベート記事
- ドラマ・映画への出演情報
- ゲーム・アニメ・食品等の発売情報（音楽アーティストと無関係）

## 出力カテゴリ（3種）
1. 番組・タイムテーブル情報
2. CD / DVD / Blu-ray 発売・予約
3. 雑誌・写真集 発売・予約
