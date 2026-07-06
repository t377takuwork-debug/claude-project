# /consolidate-memory — 週1メモリ精製（自動化Day 4運用）

`~/.claude/projects/C--Users-PC-User-claude-project/memory/` の重複・陳腐化メモリを統合し、MEMORY.mdを軽く正確に保つ。目安は週1回（前回実施日はメモリ `automation-day-plan` のDay 4欄を参照・実施後に必ず更新する）。

## 安全原則（どのモデルでも厳守）

1. **削除してよいのは次の2種だけ**
   - A: repo内に同名ファイルが存在し、機械検証（下記スクリプト）に合格したもの
   - B: 内容が現状と明確に矛盾する陳腐化メモリで、残すべき固有情報を統合先へ移し終えたもの
2. **削除前に必ず全対象をバックアップにコピー**（スクラッチパッド配下でよい）
3. **迷ったら削除しない。** 「保留」としてユーザーに列挙して判断を仰ぐ
4. 一度に大量削除する場合も、検証→バックアップ→削除→索引更新の順番を崩さない
5. `git reset` 等での復旧はできない（memory/はgit管理外）。だからこそ1〜3を飛ばさない

## 手順

### Step 1: 棚卸し
- memory/の全`.md`をGlobで列挙し、MEMORY.mdの行と突き合わせる
- 「索引に無いメモリ」「実体の無い索引行」を検出して修正対象に入れる

### Step 2: 分類
| 分類 | 判定 | 処置 |
|---|---|---|
| A: repo重複 | repoの `brands/*/rules/`・`blogs/shira_note/rules/`・`Junk314/junk_juice/rules/`・`docs/systems/`・`docs/rules/`・`.claude/commands/` に同名/同内容あり | 検証合格後に削除（repo側が唯一の正） |
| B: 陳腐化 | 日付・状態・参照先が現状と矛盾 | 固有情報を統合先へ移してから削除 |
| C: 統合可能 | 同テーマが複数ファイルに分散 | 1本へマージ・リンク`[[name]]`を張り替え |
| D: 維持 | 上記に該当しない | 何もしない |

### Step 3: A分類の機械検証（このスクリプトを流用する）

スクラッチパッドに保存して実行。**「repo側なし」「repo側が小さい」が1件でも出たら、その分は削除しない。**

```python
import os
MEM = r"C:\Users\PC_User\.claude\projects\C--Users-PC-User-claude-project\memory"
PAIRS = [  # (メモリファイル名, repo側フルパス) を分類Aの分だけ列挙
    # ("feedback_xxx.md", r"C:\Users\PC_User\claude project\brands\s4lv\rules\feedback_xxx.md"),
]
for name, repo_path in PAIRS:
    mem_path = os.path.join(MEM, name)
    if not os.path.isfile(repo_path):
        print(f"[repo側なし・削除禁止] {name}"); continue
    ms, rs = os.path.getsize(mem_path), os.path.getsize(repo_path)
    if rs < ms * 0.7:
        print(f"[repo側が小さい・削除禁止] {name}: memory={ms}B repo={rs}B"); continue
    print(f"[OK] {name}")
```

### Step 4: バックアップ→削除
- 削除対象全件をバックアップ用フォルダへ`copy`してから削除する
- 削除はPythonの`os.remove`か`Remove-Item`（**-Recurse禁止**・Guardrailにブロックされる）

### Step 5: 索引・リンクの整合
- MEMORY.mdを残存メモリと1対1になるよう更新（1メモリ=1行・内容は書かない）
- 残存メモリ内の`[[name]]`リンクが削除済みメモリを指していないかGrepで確認し、張り替える
- メモリ `automation-day-plan` のDay 4欄に実施日と結果を記録する

### Step 6: 報告（証拠つき）
- 「削除n本（A: n / B: n）・統合n本・保留n本・残存n本」＋保留リストと理由
- 検証スクリプトの出力とバックアップ先パスを添える

## 参考実績
- 第1回（2026-07-07・Fable 5）: 47本→6本。repo重複40本＋陳腐化1本を削除、40/40ペアの機械検証合格を確認してから実施
