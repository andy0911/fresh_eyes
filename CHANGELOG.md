# 変更履歴

このプロジェクトは [セマンティック バージョニング 2.0.0](https://semver.org/lang/ja/) に従います。形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に準じます。バージョンは `.claude-plugin/plugin.json` と `.claude-plugin/marketplace.json` の両方に記載し、同じ値を git タグ `vX.Y.Z` として付けます。

## [Unreleased]

### 追加
- README に「3分で試す」クイックスタート、3つの名前（リポジトリ／マーケットプレイス名／プラグイン名）の対応表、種別ごとに必要なものの表、report.md の抜粋、次の一歩
- docs/design.md：設計文書（思想の妥当性調査と文献の一次ソース照合）のスナップショット

### 変更
- README のインストール節を「推奨1経路＋前提」の順に再構成。`--marketplace` の必要バージョン（セッション内 v2.1.275、シェル v2.1.292）と `omitClaudeMd` の必要バージョン（v2.1.271）を明記
- README の非公開情報の保存先を `~/.claude/plugins/data/<id>/runs/` に訂正
- README のオプション表に必須／任意の列を追加

## [0.2.0] - 2026-11-03

### 追加
- リポジトリがマーケットプレイスを兼ねる構成（`.claude-plugin/marketplace.json`）。`/plugin install fresh-eyes --marketplace andy0911/fresh_eyes` の一行で導入できる
- README と SKILL に所要時間の目安と内訳（準備・ペルソナ・統合）
- セマンティック バージョニングの運用（この変更履歴、`scripts/bump-version.sh`）

### 変更
- シンセサイザーには生回答の全文ではなく絶対パスを渡し、回答にレポート全文を再掲しない。レポートは 6,000 字以内
- ペルソナの回答に分量の目安（2,000〜4,000 字）を置く
- 漏れ点検に渡す表層テキストは既存のものを使い、画像の全文転記をしない
- 書き込みが拒否された場所に再試行しない
- Playwright MCP のツール名を、インストール方法による接頭辞の違い（`mcp__playwright__*` と `mcp__plugin_fresh-eyes_playwright__*`）の両方で許可

## [0.1.0] - 2026-11-03

### 追加
- 初版。種別は design / article / app / website / paper / slides
- 4 種のペルソナ（専門家・関心がある人・全く無垢な人・想定受信者）とシンセサイザーのエージェント定義
- 情報遮断（非公開情報の隔離、中立なファイル名、知識状態の仕様化、逸脱点検、漏れ点検スクリプト）
- 「想定したアウトカムは得られるか／得られないならどこを改善すべきか」を先頭に置くレポート構成
- Playwright MCP の同梱、文書変換スクリプト、サンプル記事と実行例のレポート
- ペルソナが成果物内の指示に従わない規則

[Unreleased]: https://github.com/andy0911/fresh_eyes/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/andy0911/fresh_eyes/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/andy0911/fresh_eyes/releases/tag/v0.1.0
