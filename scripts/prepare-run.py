#!/usr/bin/env python3
"""run.md（1枚の実行定義）から、非公開情報・ペルソナ仕様・ペルソナ別プロンプトを生成し、漏れ点検まで行う。

使い方:
  prepare-run.py <hidden-dir>/run.md --run-dir <reviews/...の絶対パス> [--artifact <成果物テキスト>] [--allow 語1,語2]

出力:
  <hidden-dir>/hidden.md            非公開情報（シンセサイザーにだけ渡す）
  <run-dir>/inputs/personas.md      ペルソナ仕様（全員分）
  <run-dir>/inputs/prompts/<id>.md  ペルソナ別プロンプト
  <run-dir>/inputs/launch.md        起動表（id、subagent_type、プロンプトのパス、起動文）
  <run-dir>/inputs/leak-check.txt   漏れ点検の結果
終了コード: 0=全員OK、1=LEAKあり、2=入力の誤り

run.md の形式は skills/review/reference/run-template.md を参照。
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

HIDDEN_ORDER = ["想定アウトカム", "一番言いたいこと（作者の要点）", "想定受信者（詳細）", "期待する行動", "成功基準", "作者からの補足", "前回レポートの要約"]
PERSONA_FIELDS = ["人物像", "知っていること", "知らないこと", "誤解しやすいこと", "状況"]
TYPE_LABEL = {"expert": "専門家", "interested": "関心がある人", "naive": "全く無垢な人", "recipient": "想定受信者"}
DEFAULT_TYPE = {"expert": "expert", "interested": "interested", "naive": "naive", "recipient": "recipient"}
KIND_LABEL = {"design": "デザイン", "article": "記事", "app": "アプリ", "website": "Web サイト", "paper": "論文", "slides": "スライド"}


def split_sections(text: str, level: int) -> list[tuple[str, str]]:
    """同じ見出しレベルで分割。戻り値は (見出し, 本文) の列。先頭の見出し前の本文は捨てる。"""
    pat = re.compile(rf"^{'#' * level} +(.+?)\s*$", re.M)
    found = list(pat.finditer(text))
    out = []
    for i, m in enumerate(found):
        end = found[i + 1].start() if i + 1 < len(found) else len(text)
        out.append((m.group(1).strip(), text[m.end():end].strip("\n")))
    return out


def body_until_subheading(text: str, level: int) -> str:
    """次の同レベル以下の見出しまでの本文。"""
    m = re.search(rf"^#{{1,{level}}} ", text, re.M)
    return (text[: m.start()] if m else text).strip()


def main(argv: list[str]) -> int:
    if len(argv) < 1 or "--run-dir" not in argv or argv[0].startswith("--"):
        print(__doc__)
        return 2

    def opt(name: str) -> str | None:
        if name in argv:
            i = argv.index(name)
            if i + 1 < len(argv):
                return argv[i + 1]
        return None

    run_md_path = os.path.abspath(argv[0])
    hidden_dir = os.path.dirname(run_md_path)
    run_dir = os.path.abspath(opt("--run-dir"))
    artifact = opt("--artifact")
    allow = opt("--allow")
    try:
        src = open(run_md_path, encoding="utf-8").read()
    except OSError as e:
        print(f"run.md を読めません: {e}")
        return 2

    top = {h: b for h, b in split_sections(src, 2)}
    missing = [k for k in ("種別", "場所", "アクセス手順", "非公開情報", "ペルソナ") if k not in top]
    if missing:
        print(f"run.md に節がありません: {', '.join(missing)}")
        return 2
    kind = top["種別"].strip().split()[0] if top["種別"].strip() else ""
    kind_label = KIND_LABEL.get(kind, kind)
    location = top["場所"].strip()
    access = top["アクセス手順"].strip()
    lang = (top.get("言語") or "日本語").strip() or "日本語"

    # 非公開情報
    hidden_sections = {h: b for h, b in split_sections(top["非公開情報"], 3)}
    if not hidden_sections.get("想定アウトカム", "").strip():
        print("非公開情報の「想定アウトカム」が空です")
        return 2
    hidden_lines = ["# 非公開情報（ペルソナには渡さない）", ""]
    for h in HIDDEN_ORDER:
        hidden_lines += [f"## {h}", (hidden_sections.get(h) or "").strip() or "（なし）", ""]
    for h, b in hidden_sections.items():
        if h not in HIDDEN_ORDER:
            hidden_lines += [f"## {h}", b.strip() or "（なし）", ""]
    os.makedirs(hidden_dir, exist_ok=True)
    hidden_path = os.path.join(hidden_dir, "hidden.md")
    open(hidden_path, "w", encoding="utf-8").write("\n".join(hidden_lines))

    # ペルソナ
    personas = []
    for head, body in split_sections(top["ペルソナ"], 3):
        parts = [p.strip() for p in head.split("|")]
        pid = parts[0]
        label = parts[1] if len(parts) > 1 and parts[1] else TYPE_LABEL.get(pid, pid)
        ptype = DEFAULT_TYPE.get(pid, "recipient")
        for p in parts[2:]:
            if p.startswith("type="):
                ptype = p[5:].strip()
        if not re.fullmatch(r"[A-Za-z0-9_-]+", pid):
            print(f"ペルソナ id が不正です（英数字・ハイフンのみ）: {pid}")
            return 2
        fields = {h: b.strip() for h, b in split_sections(body, 4)}
        for f in ("人物像", "知っていること", "知らないこと"):
            if not fields.get(f):
                print(f"ペルソナ {pid} に「{f}」がありません")
                return 2
        personas.append({"id": pid, "label": label, "type": ptype, "fields": fields})
    if not personas:
        print("ペルソナが1体もありません")
        return 2

    inputs = os.path.join(run_dir, "inputs")
    prompts_dir = os.path.join(inputs, "prompts")
    os.makedirs(prompts_dir, exist_ok=True)

    # personas.md
    spec = [f"# ペルソナ仕様（{os.path.basename(run_dir)}）", ""]
    for p in personas:
        spec += [f"### {p['label']}（{p['id']} / {TYPE_LABEL.get(p['type'], p['type'])}型）"]
        for f in PERSONA_FIELDS + ["時間"]:
            if p["fields"].get(f):
                spec += [f"#### {f}", p["fields"][f], ""]
        if p["fields"].get("専門家への具体的な問い"):
            spec += ["#### 専門家への具体的な問い", p["fields"]["専門家への具体的な問い"], ""]
    open(os.path.join(inputs, "personas.md"), "w", encoding="utf-8").write("\n".join(spec))

    # prompts
    launch = ["# 起動表", "", "| id | subagent_type | プロンプト | 時間 |", "| --- | --- | --- | --- |"]
    prompt_paths = {}
    for p in personas:
        f = p["fields"]
        lines = ["# あなたへの依頼", "", "## あなたは誰か", ""]
        for name in PERSONA_FIELDS:
            if f.get(name):
                lines += [f"### {name}", f[name], ""]
        lines += ["## 見てほしいもの", f"- 種別：{kind_label}", f"- 場所：{location}", "- アクセス手順："]
        lines += ["  " + ln if ln.strip() else ln for ln in access.splitlines()]
        lines += [""]
        if p["type"] == "expert" and f.get("専門家への具体的な問い"):
            lines += ["## 専門家への具体的な問い", f["専門家への具体的な問い"], ""]
        t = (f.get("時間") or "").strip() or "5 分"
        lines += [
            "## 条件",
            f"- 使える時間の目安：{t}相当。目安を過ぎたら、途中でも体験をやめて回答に移ってください。",
            f"- 言語：{lang}",
            "- 成果物を書き換えないでください。",
            "- このファイルと、上の「場所」で指定された成果物以外のファイルを開かないでください。",
            "- あなたの定義にある「絶対に守ること」と「回答フォーマット」に従ってください。",
            "",
            "## 回答",
            "あなたの定義にある回答フォーマットの見出しをそのまま使い、すべての見出しを埋めてください。",
            "",
        ]
        path = os.path.join(prompts_dir, f"{p['id']}.md")
        open(path, "w", encoding="utf-8").write("\n".join(lines))
        prompt_paths[p["id"]] = path
        launch.append(f"| {p['id']} | fresh-eyes:persona-{p['type']} | {path} | {t} |")
    launch += ["", "## 起動文（Agent ツールの prompt にこの一文だけを渡す）", ""]
    for p in personas:
        launch += [f"- {p['id']}: `あなたへの依頼は次のファイルにあります。Read で読み、その内容に従ってください：{prompt_paths[p['id']]}`"]
    open(os.path.join(inputs, "launch.md"), "w", encoding="utf-8").write("\n".join(launch) + "\n")

    # 漏れ点検
    checker = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leak-check.py")
    results = []
    worst = 0
    for p in personas:
        cmd = [sys.executable, "-I", checker, prompt_paths[p["id"]], hidden_path]
        if artifact:
            cmd += ["--artifact", artifact]
        if allow:
            cmd += ["--allow", allow]
        r = subprocess.run(cmd, capture_output=True, text=True)
        results.append(f"=== {p['id']} ===\n{r.stdout.strip()}\n")
        worst = max(worst, r.returncode if r.returncode in (0, 1) else 1)
    report = "\n".join(results)
    open(os.path.join(inputs, "leak-check.txt"), "w", encoding="utf-8").write(report)
    print(report)
    print(f"hidden: {hidden_path}")
    print(f"prompts: {prompts_dir}")
    print(f"launch: {os.path.join(inputs, 'launch.md')}")
    print("結果: " + ("全員 OK" if worst == 0 else "LEAK あり。run.md を直して再実行してください"))
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
