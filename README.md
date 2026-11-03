# Fresh Eyes

成果物を「文脈を知らないレビュアー」に見せるための Claude Code プラグインです。デザイン・記事・アプリ・Web サイト・論文・スライドを、作者の意図を知らされていない4種のペルソナ（専門家、関心がある人、全く無垢な人、想定受信者）がそれぞれ独立に体験し、その生の反応から **「想定したアウトカムは得られるか。得られないなら、どこを改善すべきか」** を判定します。

## なぜ必要か

作者は自分の成果物を初見の目で見られません。知っていることを知らない状態に戻せない「知識の呪い」は、デバイアスの指示でも消えないことが実証されています。専門家だけに見せても、専門家は初学者の躓きを逆に予測します。単独のレビュアーが見つける問題は全体の2〜5割で、異なる視点を割り当てた複数の独立したレビュアーを集約する方が検出率が上がります。

一方で LLM ペルソナには固有の弱点があります。「知らないふり」はプロンプトだけでは崩れる、同じペルソナを何度走らせても多様性が出ない、作者の意図を知ると迎合する、前回の評点を見るとアンカーされる。このプラグインは、それらに対して情報遮断・知識状態の仕様化・逸脱検知・独立集約で対処します。

LLM ペルソナは実在の受信者の代表ではありません。出力は **探索的な仮説の一覧** であり、「どこで迷うか、何が伝わらないか」を見つける用途に向きます。「何％が好むか」「A と B のどちらが良いか」の推定には使えません。

## インストール

このリポジトリはマーケットプレイスを兼ねています（`.claude-plugin/marketplace.json`）。Claude Code 内で次を実行します。

```
/plugin install fresh-eyes --marketplace andy0911/fresh_eyes
```

二段階で行う場合：

```
/plugin marketplace add andy0911/fresh_eyes
/plugin install fresh-eyes@fresh-eyes-marketplace
```

手元のクローンから入れる場合（ターミナル）：

```bash
claude plugin marketplace add /path/to/fresh-eyes
```

```bash
claude plugin install fresh-eyes@fresh-eyes-marketplace
```

インストールせずに一時的に試す：

```bash
claude --plugin-dir /path/to/fresh-eyes
```

更新は `/plugin marketplace update fresh-eyes-marketplace` のあと `/plugin update fresh-eyes@fresh-eyes-marketplace` です。

同梱の Playwright MCP は初回起動時に取得されます。`npx`（Node.js）が必要で、ブラウザ本体は事前に一度だけ次で導入します。

```bash
npx playwright install chromium
```

文書変換（スライド等）には `uvx`（uv）を使います。スライドの画像化には任意で LibreOffice と poppler（`pdftoppm`）を使います。

## 使い方

```
/fresh-eyes:review <種別> <対象> --goal "<想定アウトカム>" --audience "<想定受信者>"
```

| 種別 | 対象 |
| --- | --- |
| `design` | 画像ファイル、画像ディレクトリ、PDF |
| `article` | Markdown やテキストのファイル、公開 URL |
| `app` | Web アプリの URL、起動手順、録画やスクリーンショットのディレクトリ |
| `website` | URL |
| `paper` | PDF、Markdown、LaTeX、Word |
| `slides` | PPTX、PDF |

例：

```
/fresh-eyes:review article ./drafts/launch-post.md --goal "読了後に TestFlight のリンクを開く" --audience "30代の会社員。運動不足を気にしているが、フィットネスアプリは続いたことがない。通勤中にスマホで SNS を見ている"
```

```
/fresh-eyes:review slides ./deck.pptx --goal "部長が次四半期の予算を承認する" --audience "事業部長。この提案は初見。会議の3件目で、持ち時間は10分" --personas "財務担当者"
```

改善後の再レビュー：

```
/fresh-eyes:review article ./drafts/launch-post.md --round 2 --prev reviews/20261103-1200-article/report.md
```

2回目以降の `--goal` `--message` `--audience` は前回の非公開情報から復元されます。

主なオプション：

| オプション | 意味 |
| --- | --- |
| `--message` | 作者が一番伝えたいこと（一文）。理解度の採点に使う |
| `--action` | 期待する具体的な行動（goal に含まれていれば不要） |
| `--criteria` | 成功基準 |
| `--expert` | 専門家の職能を上書き |
| `--personas "A,B"` | ペルソナを追加 |
| `--count 2` | 各ペルソナを2体ずつ（重要な成果物で推奨） |
| `--model` | ペルソナのモデル。成果物の生成に使ったモデルと別にすると自己選好が減る |
| `--lang` | 言語（既定は日本語） |

プロジェクト直下の `.fresh-eyes.yaml` に既定値を置けます（`examples/.fresh-eyes.yaml.example`）。

## 出力

`reviews/<日時>-<種別>/report.md` に次の構成で保存されます（ディレクトリ名に成果物の名前を入れないのは、パスがペルソナに渡るためです）。

0. **判定：想定したアウトカムは得られるか**（得られる／条件付きで得られる／得られない）。各ペルソナが受け取った要点と作者の意図の一致表
1. **得られないなら、どこを改善すべきか**（P1〜P3 の優先順）
2. ペルソナ別の5項目（純粋な所感、理解度、目的の結果に対するギャップ、ネガティブ、ポジティブ）
3. 横断パターン（一致した指摘、分かれた指摘）
4. 残すべき強み
5. 次回のレビューで確認したいこと
6. 付録（演技の逸脱、前回との差分、実行情報）

ペルソナの生の回答は `raw/` に、ペルソナに渡したプロンプトは `inputs/` に残ります。想定アウトカムなどの非公開情報はプロジェクトの外（`~/.claude/plugins/data/fresh-eyes/runs/`）に置かれます。`reviews/` は `.gitignore` への追加を推奨します。

## 所要時間

4ペルソナは並列に走ります。1回のレビューは 12〜15 分が目安です。

| 工程 | 目安 | 備考 |
| --- | --- | --- |
| 準備 | 3〜4 分 | 成果物の変換、ペルソナ仕様とプロンプトの生成、漏れ点検 |
| ペルソナ | 4〜6 分 | 4体が並列。専門家が事実確認の検索をするぶん最も長い |
| 統合 | 4〜5 分 | シンセサイザーが生回答を読み、レポートを書く |

Web サイトと Web アプリはブラウザの都合でペルソナを順番に走らせるため、ペルソナの工程が約4倍になります。

## 情報遮断の仕組み

| ペルソナに渡す | ペルソナに渡さない |
| --- | --- |
| 自分の人物像と知識状態 | 想定アウトカム、期待する行動、成功基準 |
| 成果物の場所とアクセス手順 | 作者の意図、背景、作者が誰か |
| 時間の目安、言語 | 他のペルソナの存在と反応 |
| 専門家にだけ：具体的な問い | 前回の結果、「改訂版」という情報 |

- ペルソナは `omitClaudeMd: true` の白紙のサブエージェントとして起動され、ツールは閲覧系に限定されます（Playwright のツール名はインストール方法で `mcp__playwright__*` か `mcp__plugin_fresh-eyes_playwright__*` になるため、許可リストは両方を含みます）（Bash、Grep、Glob、任意コード実行、ファイル送出、任意 HTTP リクエストを持ちません。専門家だけ事実確認用の検索を持ちます）
- 成果物は中立なファイル名でコピーして渡し、非公開情報はプロジェクトの外に置きます。`.fresh-eyes.yaml` に `goal` を書く場合、それはプロジェクト直下の平文である点に留意してください
- Web サイトと Web アプリではブラウザがセッションに1つのため、ペルソナを1体ずつ順番に走らせ、間でブラウザを閉じます
- 起動前に `scripts/leak-check.py` が、プロンプトと非公開情報の特徴語の重なりを点検します
- 無垢・関心層は「知っていること／知らないこと／誤解しやすいこと」を列挙した知識状態で定義され、回答後に逸脱（専門用語の使用、自力解決）を点検します
- 統合は別エージェント（シンセサイザー）が行い、一致した指摘と分かれた指摘を平均化せずに並べ、定量的な主張をしません

## 同梱する MCP と、同梱しないコネクタ

同梱（同じ体験を再現するために必須なもの）：

| MCP | 用途 |
| --- | --- |
| Playwright MCP（`@playwright/mcp` 0.0.84、`--headless --isolated`） | Web サイトと Web アプリの閲覧・操作。ログイン状態を持ち込まない |

文書変換（PPTX、DOCX、PDF）は MCP ではなく同梱スクリプト `scripts/to-markdown.sh` が MarkItDown を `uvx` 経由で実行します。MCP として常駐させる必要がないためです。

同梱しない（環境にあれば任意で使う）：

- Figma、Google ドライブ、Notion などのコネクタ。デザインや文書の**取得**に使い、取得物をファイルとして `work/` に置いてからペルソナに渡します
- ネイティブアプリのシミュレータ操作 MCP。あればアプリ種別のアクセス手順を「操作できる」形に書き換えて使えます

## カスタマイズ

- 専門家の職能、関心層の分野：`--expert`、`--interested`、または `.fresh-eyes.yaml`
- ペルソナの追加：`--personas`。職能なら専門家型、人物像なら受信者型として起動されます
- 回答フォーマットの変更：`agents/persona-*.md`
- レポート構成の変更：`agents/synthesizer.md`
- 種別の追加：`skills/review-<種別>/SKILL.md` を既存のものに倣って作成

## 構成

```
fresh-eyes/
├── .claude-plugin/plugin.json
├── .mcp.json                      Playwright
├── skills/
│   ├── review/                    オーケストレータ（/fresh-eyes:review）
│   │   └── reference/             遮断ルール、知識状態の書き方、プロンプト雛形、逸脱点検
│   ├── review-design/             種別ごとの準備・アクセス手順・専門家プロファイル・判定観点
│   ├── review-article/
│   ├── review-app/
│   ├── review-website/
│   ├── review-paper/
│   └── review-slides/
├── agents/
│   ├── persona-expert.md
│   ├── persona-interested.md
│   ├── persona-naive.md
│   ├── persona-recipient.md
│   ├── persona-expert-cli.md       CLI・ローカル起動アプリの専門家（Bash あり）
│   └── synthesizer.md
├── scripts/
│   ├── leak-check.py              プロンプトへの非公開情報の漏れ点検
│   └── to-markdown.sh             文書の変換（Markdown、PDF、ページ画像）
└── examples/
```

## 制限と前提

- ペルソナの反応は LLM の出力であり、実在集団の反応分布を表しません。最終判断の前に、実際の受信者での確認を推奨します
- 無垢ペルソナの演技は完全ではありません。逸脱点検と再実行で軽減しますが、付録の逸脱記録を確認してください
- 同一モデルは自分の文体を好む傾向があります。成果物を LLM で書いた場合は `--model` で別のモデルを指定することを検討してください
- 1回のレビューで 5 体のサブエージェント（4 ペルソナ + シンセサイザー）が走ります。`--count 2` では 9 体です。ペルソナの回答は 1 体あたり 2,000〜4,000 字、レポートは 5,000〜8,000 字が目安です
- 非対話モード（`claude -p`）では、`reviews/` への書き込みが権限確認で止まり自動拒否されることがあります。対話モードで実行するか、設定で `reviews/` 配下への書き込みを許可してください
- レビュー対象の Web ページや文書に「レビュアーへの指示」が書かれていても、ペルソナはそれに従わないよう定義されていますが、信頼できない URL をレビューする際は Playwright MCP が `--isolated` で動くこと（ログイン状態を持ち込まない）を前提にしてください

## 根拠

設計の根拠となった文献（知識の呪い、ヒューリスティック評価の評価者数、LLM 評価者の迎合・アンカリング・自己選好、LLM ペルソナ模擬の限界、模擬学習者の能力の逆説など）は、付属の設計文書にまとめています。

## バージョニング

[セマンティック バージョニング](https://semver.org/lang/ja/) に従います。バージョンは `.claude-plugin/plugin.json` と `.claude-plugin/marketplace.json` に同じ値で記載し、git タグ `vX.Y.Z` を付けます。変更内容は `CHANGELOG.md` にあります。

| 上げる桁 | このプラグインでの意味 |
| --- | --- |
| MAJOR | 互換性のない変更。コマンドや必須オプションの変更、`report.md` の見出し構成や `--prev` で読む形式の変更、ペルソナの回答見出しの変更 |
| MINOR | 後方互換の機能追加。種別・オプション・ペルソナ型・MCP の追加、プロンプトや判定基準の実質的な変更 |
| PATCH | 後方互換の修正。文言の調整、スクリプトの不具合修正、ドキュメント |

1.0.0 より前（0.x）は、MINOR に互換性のない変更が含まれることがあります。リリースは次で行います（`CHANGELOG.md` の `[Unreleased]` に変更を書いてから）。

```bash
scripts/bump-version.sh minor
```

```bash
git push origin main --follow-tags
```

利用側の更新は `/plugin marketplace update fresh-eyes-marketplace` のあと `/plugin update fresh-eyes@fresh-eyes-marketplace` です。

## ライセンス

MIT
