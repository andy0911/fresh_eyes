#!/usr/bin/env python3
"""ペルソナ向けプロンプトに、非公開情報の特徴語が漏れていないかを機械的に点検する。

使い方:
  leak-check.py <prompt.md> <hidden.md> [--artifact <成果物テキスト>] [--allow 語,語,...]

点検対象（hidden.md の節）: 想定アウトカム / 期待する行動 / 成功基準 / 一番言いたいこと / 作者からの補足 / 前回レポートの要約
除外: 「想定受信者」の節（想定受信者ペルソナに渡す人物像を含む）。
見出しがあるのに上の節が一つも見つからない場合は、安全側に倒して全文を点検し、その旨を警告する。

判定の層:
  1. 特徴語の一致: 漢字連（2〜4文字窓）、カタカナ連、ラテン語（- _ で分割）、ひらがな連（5文字以上）
  2. 連続一致: 記号・空白を取り除いた上で、非公開文の7文字窓がプロンプトに現れる
  3. 指示文の一致: 「〜してください」「〜してみて」などの依頼表現を含む行に非公開語が一つでもあれば強い漏れ
--artifact で成果物本文を渡すと、成果物の表層に出る語は「あなたは誰か」節（人物像・知識状態）の中でだけ許容する。
アクセス手順や条件の節では許容しない（目的を構成する語がそのまま並ぶため）。

終了コード: 0 = 問題なし / 1 = 強い漏れあり / 2 = 使い方かファイルの誤り
この点検は安全網であり保証ではない。言い換え（特にひらがな化や同義語）は検出できないため、
isolation-rules.md のチェックリストによる目視点検を省略してはいけない。
"""
import re
import sys
import unicodedata

SECRET_HEADINGS = ("想定アウトカム", "期待する行動", "成功基準", "一番言いたいこと", "作者の要点", "作者からの補足", "前回")
PERSONA_HEADING = "あなたは誰か"
REQUEST_MARKERS = ("ください", "してみ", "しましょう", "してほしい", "せよ", "なさい", "すること", "please", "try to", "make sure")

DEFAULT_ALLOW = {
    "デザイン", "記事", "アプリ", "サイト", "ウェブ", "論文", "スライド", "資料", "成果物",
    "ファイル", "レビュー", "ペルソナ", "体験", "回答", "形式", "日本語", "英語", "最低限",
    "アクセス", "手順", "時間", "制限", "以内", "以下", "以上", "場合", "こと", "もの", "ため",
    "自分", "言葉", "印象", "所感", "理解", "行動", "確信", "ポイント", "ネガティブ", "ポジティブ",
    "ログ", "見出し", "順番", "記録", "質問", "説明", "内容", "全体", "部分", "画面", "画像",
    "ページ", "リンク", "操作", "開始", "終了", "最初", "最後", "必要", "可能", "注意", "禁止",
    "推測", "専門", "用語", "読者", "利用者", "人物", "属性", "知識", "状態", "分野", "興味",
    "関心", "無垢", "専門家", "受信者", "想定", "著者", "作者", "目的", "意図", "目安", "条件",
    "依頼", "種別", "場所", "定義", "絶対", "守る", "書き換え", "指定", "情報", "非公開",
    "スマホ", "スマートフォン", "パソコン", "タブレット", "端末", "ブラウザ", "iphone", "android", "ipad", "mac", "windows",
    "http", "https", "html", "file", "path", "markdown", "json", "app", "web", "url", "pdf", "png", "jpg", "md",
}
HIRA_STOP = {"ください", "ように", "について", "ところ", "ている", "という", "それぞれ", "あなた", "ではなく", "してください", "とおり", "ません", "ながら"}

KANJI = re.compile(r"[一-鿿々]{2,}")
KATA = re.compile(r"[ァ-ヺー]{3,}")
HIRA = re.compile(r"[ぁ-ゖ]{5,}")
LATIN = re.compile(r"[A-Za-z][A-Za-z0-9]{2,}")
PUNCT = re.compile(r"[\s　\-_‐-―・･/／、。，．,.:：;；!！?？「」『』（）()\[\]【】<>＜＞\"'”“’‘*#|`]+")


def normalize(text: str) -> str:
    t = unicodedata.normalize("NFKC", text)
    return PUNCT.sub(" ", t)


def compact(text: str) -> str:
    return re.sub(r"\s+", "", normalize(text))


def tokens(text: str) -> set[str]:
    t = normalize(text)
    out: set[str] = set()
    for m in KANJI.findall(t):
        out.add(m)
        if len(m) > 2:
            for n in (2, 3, 4):
                for i in range(0, len(m) - n + 1):
                    out.add(m[i:i + n])
    for m in KATA.findall(t):
        out.add(m)
    for m in HIRA.findall(t):
        if m not in HIRA_STOP:
            out.add(m)
    for m in LATIN.findall(t):
        out.add(m.lower())
    return out


def sections(md: str) -> list[tuple[int, str, str]]:
    """(見出しレベル, 見出し, 本文) の列。見出しより前の本文はレベル0・見出し空で返す。"""
    parts = re.split(r"^(#{1,6})\s+(.*)$", md, flags=re.M)
    out = []
    if parts and parts[0].strip():
        out.append((0, "", parts[0]))
    for i in range(1, len(parts) - 2, 3):
        out.append((len(parts[i]), parts[i + 1].strip(), parts[i + 2]))
    return out


def secret_text(hidden_md: str) -> tuple[str, str]:
    secs = sections(hidden_md)
    titled = [x for x in secs if x[1]]
    if not titled:
        return hidden_md, ""
    picked = [body for _, title, body in titled if any(h in title for h in SECRET_HEADINGS)]
    if not picked:
        return hidden_md, "警告: hidden.md に規定の見出し（想定アウトカム／期待する行動／成功基準／一番言いたいこと／作者からの補足／前回）が見つからないため、全文を点検対象にしました"
    return "\n".join(picked), ""


def split_prompt(prompt_md: str) -> tuple[str, str]:
    """「あなたは誰か」の見出しから、同じか上位のレベルの次の見出しまでを人物像の節とする。"""
    persona, rest = [], []
    in_persona, persona_level = False, 0
    for level, title, body in sections(prompt_md):
        if PERSONA_HEADING in title:
            in_persona, persona_level = True, level
        elif in_persona and level and level <= persona_level:
            in_persona = False
        (persona if in_persona else rest).append(body)
    return "\n".join(persona), "\n".join(rest)


def is_strong_token(t: str) -> bool:
    return len(t) >= 3 or bool(LATIN.fullmatch(t))


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2

    def opt(name: str) -> str | None:
        if name in argv:
            i = argv.index(name)
            if i + 1 < len(argv):
                return argv[i + 1]
        return None

    allow = set(DEFAULT_ALLOW)
    if opt("--allow"):
        allow |= {w.strip() for w in opt("--allow").split(",") if w.strip()}
    try:
        prompt = open(argv[1], encoding="utf-8").read()
        hidden_raw = open(argv[2], encoding="utf-8").read()
        artifact = open(opt("--artifact"), encoding="utf-8", errors="ignore").read() if opt("--artifact") else ""
    except OSError as e:
        print(f"ファイルを読めません: {e}")
        return 2

    secret, warning = secret_text(hidden_raw)
    hidden_tokens = {t for t in tokens(secret) if t not in allow and t.lower() not in allow}
    artifact_tokens = tokens(artifact) if artifact else set()
    persona_part, rest_part = split_prompt(prompt)
    persona_tokens, rest_tokens = tokens(persona_part), tokens(rest_part)

    strong: dict[str, str] = {}
    weak: set[str] = set()
    allowed_in_persona: set[str] = set()

    # 層1: 特徴語
    for t in sorted(hidden_tokens):
        if t in rest_tokens:
            if is_strong_token(t):
                strong[t] = "アクセス手順・条件の節"
            else:
                weak.add(t)
        elif t in persona_tokens:
            if t in artifact_tokens:
                allowed_in_persona.add(t)
            elif is_strong_token(t):
                strong[t] = "あなたは誰か（人物像）の節"
            else:
                weak.add(t)

    # 層2: 連続一致（7文字窓）。人物像の節では、成果物本文にも現れる並びは許容する
    c_secret = compact(secret)
    c_rest, c_persona, c_artifact = compact(rest_part), compact(persona_part), compact(artifact)
    seen = set()
    for i in range(0, max(0, len(c_secret) - 6)):
        w = c_secret[i:i + 7]
        if w in seen or re.fullmatch(r"[\u3041-\u3096]+", w):
            continue
        seen.add(w)
        if all(tok in allow for tok in tokens(w)):
            continue
        if w in c_rest:
            strong[w] = "7文字以上の連続一致（アクセス手順・条件の節）"
        elif w in c_persona and (not c_artifact or w not in c_artifact):
            strong[w] = "7文字以上の連続一致（人物像の節）"

    # 層3: 指示文に非公開語（行ごとに判定。人物像の節では成果物由来の語を除く）
    for part, exempt in ((rest_part, set()), (persona_part, artifact_tokens)):
        for raw in part.splitlines():
            line = normalize(raw)
            low = line.lower()
            if any(mk in low for mk in REQUEST_MARKERS):
                lt = tokens(line)
                for t in sorted(hidden_tokens):
                    if t in lt and t not in allow and t not in exempt:
                        strong[t] = "依頼表現を含む行"

    if warning:
        print(warning)
    if strong:
        print("LEAK: 非公開情報の特徴語がプロンプトに含まれています:")
        for t, where in strong.items():
            print(f"  - {t}（{where}）")
        if weak:
            print("参考（弱い一致）: " + ", ".join(sorted(weak)))
        if allowed_in_persona:
            print("成果物由来のため人物像の節では許容: " + ", ".join(sorted(allowed_in_persona)))
        return 1
    msg = "OK"
    if weak:
        msg += "（弱い一致のみ、確認推奨: " + ", ".join(sorted(weak)) + "）"
    if allowed_in_persona:
        msg += "　成果物由来のため人物像の節では許容: " + ", ".join(sorted(allowed_in_persona))
    if not weak and not allowed_in_persona:
        msg += ": 漏れは検出されませんでした"
    print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
