# プロジェクト全体ナビゲーター

Note/X/Threads運用のコンテンツ制作・SEO施策・ブランド構築を行うプロジェクト。

**全体索引は `README.md`、業務一覧と完了条件は `docs/business_inventory.md`、業務別手順書は `docs/sop/` を参照**（2026-07-06に全暗黙知をrepo内へ統合済み）。

---

## ディレクトリ構成と役割

```
claude project/
├── README.md       ← 全体索引（どのAIでも最初に読む）
├── .claude/commands/ ← 汎用スキル22本（唯一の正。過去版はgit履歴から復元）
├── docs/           ← 業務棚卸し表・SOP・会議システム定義・横断ルール
├── blogs/          ← ブログ記事制作・リライト環境
│   ├── shira_note/ ← 音楽番組タイムテーブル速報ブログ（メイン稼働・rules/に番組別チェックリスト）
│   └── seo/        ← SEO_guide.txt（全ブログ共通マスターガイド）
├── brands/         ← アカウント運用・ライティング原則（→ brands/CLAUDE.md を参照）
│   ├── writing/        ← ライティング原則4ファイル
│   ├── s4lv/
│   │   ├── profile.md  ← s4lv統一プロフィール（2026-07-08統一）
│   │   ├── rules/      ← 文体定義・Note記事プロセス等10本（旧Claude Codeメモリから統合）
│   │   └── shared/     ← s4lv共通プロフィール・実績データ
│   └── mbticode/       ← MBTI×ラブタイプ診断コンテンツ運用（rules/に文体・戦略12本）
└── Junk314/        ← クライアント管理アカウント（→ Junk314/junk_juice/CLAUDE.md を参照）
    └── junk_juice/ ← 60代推し活エッセイアカウント（rules/に品質基準3本）
```

---

## 作業開始ルール（全タスク共通）

1. **参照先の優先順位**：ルートの本ファイル → 各ディレクトリの `CLAUDE.md` → 個別ファイル
2. **捏造禁止**：コンテンツ生成時は必ず該当アカウントの `personal_data.md` を参照し、実体験に基づく内容のみ使用する
3. **参照先は1ファイル**：SEO判断は `blogs/seo/SEO_guide.txt` 、ライティング原則は `brands/writing/writing_core.md` を起点とする

---

## 行動規範（全モデル共通・Fable 5基準）

### 完了を機械的に判定する
着手前に「完了」を1行で定義する。
例：shira_noteリライトなら「/shira-qa ERROR 0件・新規WARN 0件」。Note記事なら「drafts/へ保存済み」。X投稿なら「/post-reviewチェック済み」。
書けない場合は、何が決まれば書けるかを質問してから進む。

### 複数解釈を勝手に選ばない
指示に2つ以上の読み方がある場合、黙って1つを選ばない。解釈の候補を列挙し、推奨を1つ添えて確認する。
ただし、どの解釈でも成果物が変わらない場合だけ、そのまま進めてよい。

### ついで改善を禁止する
依頼されていない変更を実装しない。「ついでに直した」は禁止。隣の改善点を見つけたら、実装せずに提案として列挙する。

### 「動いた」ではなく「検証した」を報告する
完了報告には検証の証拠（qa_draft.pyの結果・Grep確認結果・保存先パス等）を含める。
実行していないものを「できたはず」と書かない。スキップした検証は理由まで明記する。

### 同じエラーへの修正は2回まで
同じ問題への修正が2回失敗したら、3回目の変種を試さない。現状・試したこと・残る仮説を短く報告し、方針転換する。

### 完了前に初見のレビューを入れる
完了報告の前に、初めて読む人として自分の変更を見直す。壊れうる隣接箇所（同一draft内の重複記載・JSON-LD同期等）を1つ挙げて確認する。

### 確信度と進捗を3点で報告する
自信のない箇所には確信度（高・中・低）を付け、中・低なら確認してから進むべきかを聞く。
長い作業では、区切りごとに「完了したこと」「次にやること」「気になっていること」の3点だけ報告する。

### モデル切替時のeffort目安（タスク種類で切り替える）
- **定型作業＝`medium`**（機械QAの安全網があるもの）：shira_noteリライト（qa_gateフックが自動検品）／X・Threads投稿提案（qa_post＋/post-review）／Note記事本文生成（qa_article）
- **判断・環境系＝`high`**（Opus系は`xhigh`）：戦略会議（/notekaigi・/asp-kaigi等）／新規記事立ち上げ・タイトル/構成設計／/consolidate-memory／フック・タスクスケジューラ・settings.json等の環境変更
- mediumで見落とし（日付更新漏れ・JSON-LD同期等のQAチェック外項目）が続いた工程は、その工程だけhighへ上げる

---

## タスク別・最初に開くファイル

| やること | 最初に開くファイル |
|---|---|
| shira_note リライト | `blogs/shira_note/CLAUDE.md` |
| cf_room 記事新規作成（画像自動配置） | `/cf-article` スキルを起動 |
| cf_room リライト | `blogs/cf_room/CLAUDE.md` |
| vtuber_log 記事新規作成（画像自動配置） | `/vtuber-article` スキルを起動 |
| vtuber_log リライト | `blogs/vtuber_log/CLAUDE.md` |
| Note記事生成（s4lv/MBTICODE） | `brands/CLAUDE.md` |
| X・Threads投稿生成 | `brands/CLAUDE.md` |
| junk_juice Note記事（テーマ・タイトル） | `/junk-theme` スキルを起動 |
| junk_juice Note記事（構成・本文・保存） | `/junk-article` スキルを起動 |
| ASP記事設計 | `/asp-kaigi` スキルを起動 |
| 戦略・方針判断 | `/notekaigi` スキルを起動 |
