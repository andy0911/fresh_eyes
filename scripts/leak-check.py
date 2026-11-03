#!/usr/bin/env python3
"""ペルソナ向けプロンプトに、非公開情報（目的・想定アウトカム・前回レビュー）の特徴語が
漏れていないかを機械的に点検する。

使い方:
  leak-check.py <prompt.md> <hidden.txt> [--allow 語,語,...]

hidden.txt には「ペルソナに渡してはいけない文章」（目的、想定アウトカム、期待する行動、
前回レポートの要約など）をそのまま入れる。prompt.md にその特徴語が現れたら一覧を出し、
終了コード 1 を返す。形態素解析を使わず、漢字連・カタカナ連・ラテン語の単純抽出で判定する。
偽陽性は --allow で除外できる（成果物の種別名などは既定で除外済み）。
"""
import re
import sys

DEFAULT_ALLOW = {
    # 成果物の種別・一般語（プロンプトに必ず出るもの）
    "デザイン", "記事", "アプリ", "サイト", "ウェブ", "論文", "スライド", "資料", "成果物",
    "ファイル", "レビュー", "ペルソナ", "体験", "回答", "形式", "日本語", "英語", "最低限",
    "アクセス", "手順", "時間", "制限", "以内", "以下", "以上", "場合", "こと", "もの", "ため",
    "自分", "言葉", "印象", "所感", "理解", "行動", "確信", "ポイント", "ネガティブ", "ポジティブ",
    "ログ", "見出し", "順番", "記録", "質問", "説明", "内容", "全体", "部分", "画面", "画像",
    "ページ", "リンク", "操作", "開始", "終了", "最初", "最後", "必要", "可能", "注意", "禁止",
    "推測", "専門", "用語", "読者", "利用者", "人物", "属性", "知識", "状態", "分野", "興味",
    "関心", "無垢", "専門家", "受信者", "想定", "著者", "作者", "目的", "意図",
    "http", "https", "html", "file", "path", "markdown", "json",
}

KANJI = re.compile(r"[一-鿿々]{2,}")
KATA = re.compile(r"[゠-ヿー]{3,}")
LATIN = re.compile(r"[A-Za-z][A-Za-z0-9_\-]{3,}")


def tokens(text: str) -> set[str]:
    out = set()
    for rx in (KANJI, KATA):
        for m in rx.findall(text):
            out.add(m)
            # 漢字連は部分語（2〜4文字窓）も見る。例: 「運動習慣化」→「運動習慣」「習慣化」
            if rx is KANJI and len(m) > 2:
                for n in (2, 3, 4):
                    for i in range(0, len(m) - n + 1):
                        out.add(m[i:i + n])
    for m in LATIN.findall(text):
        out.add(m.lower())
    return out


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    prompt_path, hidden_path = argv[1], argv[2]
    allow = set(DEFAULT_ALLOW)
    if "--allow" in argv:
        i = argv.index("--allow")
        if i + 1 < len(argv):
            allow |= {w.strip() for w in argv[i + 1].split(",") if w.strip()}
    prompt = open(prompt_path, encoding="utf-8").read()
    hidden = open(hidden_path, encoding="utf-8").read()
    hidden_tokens = {t for t in tokens(hidden) if t not in allow and t.lower() not in allow}
    prompt_tokens = tokens(prompt)
    leaks = sorted(t for t in hidden_tokens if t in prompt_tokens)
    # 2文字の漢字語だけの一致は弱い証拠なので、3文字以上かラテン語の一致を「強い漏れ」とする
    strong = [t for t in leaks if len(t) >= 3 or LATIN.fullmatch(t)]
    weak = [t for t in leaks if t not in strong]
    if strong:
        print("LEAK: 非公開情報の特徴語がプロンプトに含まれています:")
        for t in strong:
            print(f"  - {t}")
        if weak:
            print("参考（弱い一致）: " + ", ".join(weak))
        return 1
    if weak:
        print("OK（弱い一致のみ、確認推奨）: " + ", ".join(weak))
        return 0
    print("OK: 漏れは検出されませんでした")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
