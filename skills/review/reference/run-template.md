# run.md の書き方（1枚の実行定義）

オーケストレータは、非公開情報・ペルソナ仕様・プロンプトを別々に書かず、この形式の `run.md` を **1枚だけ** 書きます。`${CLAUDE_PLUGIN_ROOT}/scripts/prepare-run.py` がそれを読み、`hidden.md`、`inputs/personas.md`、`inputs/prompts/<id>.md`、`inputs/launch.md`、`inputs/leak-check.txt` を生成します。`run.md` は非公開情報を含むので、**プロジェクトの外**（`${CLAUDE_PLUGIN_DATA}/runs/<run>/run.md`）に置きます。

```markdown
# レビュー実行定義

## 種別
article

## 場所
/abs/path/reviews/20261103-1420-article/work/artifact.md

## アクセス手順
1. 次のファイルを開いて読んでください：/abs/path/reviews/20261103-1420-article/work/artifact.md
2. 普段、記事を読むときと同じように読んでください。全部読む必要はありません。

## 言語
日本語

## 非公開情報

### 想定アウトカム
（--goal）

### 一番言いたいこと（作者の要点）
（--message。なければ空）

### 想定受信者（詳細）
（--audience）

### 期待する行動
（--action）

### 成功基準
（--criteria）

### 作者からの補足
（あれば）

### 前回レポートの要約
（--prev があるときだけ。3〜5 行）

## ペルソナ

### expert | 専門家（技術文書の編集者）
#### 人物像
...
#### 知っていること
- ...
#### 知らないこと
- この文書の作者が誰か、どのような意図で書いたか
#### 誤解しやすいこと
- 特になし
#### 状況
...
#### 時間
20 分
#### 専門家への具体的な問い
1. ...

### interested | 関心がある人（...）
#### 人物像
#### 知っていること
#### 知らないこと
#### 誤解しやすいこと
#### 状況
#### 時間
8 分

### naive | 全く無垢な人
（同じ項目。時間は短く）

### recipient | 想定受信者（--audience の人物像）
（同じ項目。--goal --action --criteria の内容は書かない）

### extra-1 | 財務担当者 | type=expert
（--personas で追加されたペルソナ。type は expert か recipient）
```

規則：

- `### <id> | <表示名> [| type=<型>]`。id は英数字とハイフンのみ。`expert` `interested` `naive` `recipient` は型が自動で決まります
- `人物像` `知っていること` `知らないこと` は必須。`時間` を省くと 5 分相当になります
- 想定受信者の節に `--goal` `--action` `--criteria` の内容を書かないこと。無垢・関心層の「知らないこと」は成果物の表層から導くこと
- 「アクセス手順」はすべてのペルソナに共通です。開始地点だけを指定し、見る順序は誘導しません
- 実行後に `LEAK` が出たら、該当語を `run.md` から取り除いて再実行します
