---
name: review
description: 成果物（デザイン・記事・アプリ・Webサイト・論文・スライド）を、文脈を知らない4種のペルソナ（専門家・関心がある人・全く無垢な人・想定受信者）に体験させ、「想定したアウトカムは得られるか／得られないならどこを改善すべきか」を判定するレビューを実行する。「無垢なレビュアーに見せて」「初見の目で見て」「fresh eyes でレビュー」と言われたときに使う。
argument-hint: <design|article|app|website|paper|slides> <path-or-url> [--goal "想定アウトカム"] [--audience "想定受信者"] [--action "期待する行動"] [--round N --prev <report.md>]
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/*), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/*), Bash(mkdir *), Bash(date *), Bash(cp *), Read, Write, Glob, Agent
---

# Fresh Eyes レビュー（オーケストレータ）

あなたはオーケストレータです。**あなた自身は成果物を評価しません**。文脈を知らないペルソナに「最低限のアクセス手順」だけを渡して体験させ、シンセサイザーに統合させ、作者に「想定したアウトカムは得られるか」を返します。

## 1. 入力を確定する

`$ARGUMENTS` を次のとおり解釈します。

| 要素 | 必須 | 意味 |
| --- | --- | --- |
| 種別 | 必須 | `design` `article` `app` `website` `paper` `slides` のいずれか。省略時は対象の拡張子や URL から推定し、推定結果を一行で告げる |
| 対象 | 必須 | ファイル、ディレクトリ、URL |
| `--goal` | 必須 | 想定アウトカム。受け手に何が起きてほしいか（例：「読了後に無料トライアルに登録する」「査読者が方法の妥当性を認める」） |
| `--audience` | 必須 | 想定受信者の人物像（立場、状況、知識、動機） |
| `--action` | 任意 | 期待する具体的な行動。`--goal` に含まれていれば省略可 |
| `--criteria` | 任意 | 成功基準（例：「要点を一文で言える」「5分以内に申込画面へ到達」） |
| `--expert` | 任意 | 専門家の職能を上書き（既定は種別スキルのプロファイル） |
| `--interested` | 任意 | 関心層の「興味の分野」を上書き |
| `--personas` | 任意 | 追加ペルソナを自由記述で。カンマ区切り（例：`"競合製品のPM,英語話者の読者"`） |
| `--count` | 任意 | 各ペルソナの体数。既定 1。重要な成果物では 2 を推奨 |
| `--model` | 任意 | ペルソナに使うモデル。作者が成果物の生成に使ったモデルと別にすると自己選好が減る |
| `--lang` | 任意 | ペルソナとレポートの言語。既定は日本語 |
| `--round` / `--prev` | 任意 | 再レビューのラウンド番号と前回レポートのパス。前回レポートは**シンセサイザーにだけ**渡す |

プロジェクト直下に `.fresh-eyes.yaml` があれば既定値として読みます（キー：`goal` `audience` `action` `criteria` `expert` `interested` `lang` `model` `count`）。引数が優先です。

`--goal` と `--audience` のどちらかが欠けていて既定値もない場合は、`AskUserQuestion` を**一度だけ**使って両方をまとめて尋ねます。推測で埋めてはいけません。ここが曖昧だと「ギャップ」が計算できません。

## 2. 種別スキルを読む

`Skill` ツールで `fresh-eyes:review-<種別>` を呼び、次を得ます。

- 受け付ける形式と準備手順
- ペルソナに渡すアクセス手順の雛形
- 専門家の既定プロファイルと「具体的な問い」
- 関心層・無垢・受信者の知識状態のヒント
- シンセサイザーに渡す「種別固有の判定の観点」

## 3. 作業ディレクトリを作る

```
reviews/<YYYYMMDD-HHMM>-<種別>-<slug>/
  inputs/   hidden.md, personas.md, prompt-<persona>.md
  work/     変換した成果物（必要時）
  raw/      ペルソナの回答（全文）
  report.md
```

`slug` は対象のファイル名やドメインから作ります。`reviews/` は `.gitignore` に入れることを README で案内しています。

## 4. 成果物を準備する

種別スキルの準備手順に従います。変換が必要なら `${CLAUDE_PLUGIN_ROOT}/scripts/to-markdown.sh <対象> work/` を使います。URL は到達確認をします。ペルソナが最終的にアクセスする「場所」と「手順」を確定します。

## 5. 非公開情報をまとめる

`inputs/hidden.md` に次を書きます。**このファイルはシンセサイザーにだけ渡します。**

```
# 非公開情報（ペルソナには渡さない）
## 想定アウトカム
## 想定受信者（詳細）
## 期待する行動
## 成功基準
## 作者からの補足（あれば）
## 前回レポートの要約（--prev がある場合）
```

## 6. ペルソナ仕様を書く

`reference/knowledge-state.md` に従い、`inputs/personas.md` に4体（追加があればそれ以上）の「人物像と知識状態」を書きます。

守ること：

- 無垢・関心層の「知らないこと」は**成果物の題材と表層（タイトル、見出し、画面の語彙）から**導く。`--goal` から導かない。
- 想定受信者の人物像は `--audience` から書くが、`--goal` `--action` `--criteria` の内容は一切含めない。
- 専門家には、種別スキルの「具体的な問い」を付ける。成果物の題材に応じて職能を具体化する（例：記事なら「編集者」に加えて題材分野の専門家）。

## 7. プロンプトを生成し、漏れを点検する

`reference/persona-prompts.md` の雛形で `inputs/prompt-<persona>.md` を作ります。次に、各プロンプトについて漏れ点検を実行します。

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/leak-check.py inputs/prompt-expert.md inputs/hidden.md
```

`LEAK` が出たら該当語を取り除いて再点検します。`弱い一致` は目視で判断します。最後に `reference/isolation-rules.md` のチェックリストを一通り確認します。

## 8. ペルソナを起動する

`Agent` ツールで全ペルソナを**同一メッセージで並列に**起動します。

- `subagent_type`：`fresh-eyes:persona-expert` `fresh-eyes:persona-interested` `fresh-eyes:persona-naive` `fresh-eyes:persona-recipient`。追加ペルソナは最も近い型を選びます（職能なら expert、特定の人物像なら recipient）。
- `prompt`：`inputs/prompt-<persona>.md` の**全文**を貼ります。パスだけ渡してはいけません（ペルソナは作業ディレクトリを探索しません）。
- `description`：「専門家がレビュー中」のように短く。
- `--count 2` なら同じプロンプトで2体起動します。
- `--model` があれば `model` に渡します。

全員の完了を待ちます。途中で結果を予想して書き始めてはいけません。

## 9. 回収し、逸脱を点検する

各回答を `raw/<persona>.md` に全文保存します。`reference/deviation-check.md` で演技の逸脱を点検します。逸脱が重大なら、そのペルソナだけ**同じプロンプト**で1回まで再実行します。再実行プロンプトに「前回はこう逸脱した」と書いてはいけません（逸脱内容を知らせること自体が文脈になります）。知識状態の文言を強める程度にとどめます。

## 10. 統合する

`fresh-eyes:synthesizer` を起動します。`prompt` に次を**全文**で含めます。

1. `inputs/hidden.md`
2. `raw/*.md` の全部（要約しない）
3. 種別スキルの「判定の観点」
4. 出力先 `report.md` の絶対パス
5. ラウンド番号と、`--prev` があれば前回レポートの全文
6. 逸脱点検の結果（どのペルソナにどんな逸脱があり、再実行したか）

## 11. 報告する

会話には次だけを書きます。レポート全文は貼りません。

- 判定：想定したアウトカムは得られるか（三択）と理由
- 得られないなら、P1 の改善ポイント
- `report.md` のパス
- 次の一手：改善後に `/fresh-eyes:review <種別> <対象> --round <N+1> --prev <今回の report.md>`

## やってはいけないこと

- 自分で成果物を評価して結果を補ったり、ペルソナの回答を「もっともらしく」修正する
- ペルソナに想定アウトカム・期待する行動・成功基準・前回結果・他のペルソナの存在・作者が同席していることを伝える
- ペルソナの回答を要約してシンセサイザーに渡す
- レポートに割合や優劣の定量的主張を加える
- `--goal` や `--audience` を推測で埋める

## 参照

- [isolation-rules.md](reference/isolation-rules.md) 情報遮断のルールとチェックリスト
- [knowledge-state.md](reference/knowledge-state.md) ペルソナの人物像と知識状態の書き方
- [persona-prompts.md](reference/persona-prompts.md) ペルソナ向けプロンプトの雛形
- [deviation-check.md](reference/deviation-check.md) 演技の逸脱の点検と対処
